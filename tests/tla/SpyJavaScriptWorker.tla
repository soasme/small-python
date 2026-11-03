------------------------ MODULE SpyJavaScriptWorker ------------------------
(***************************************************************************)
(* The parent side of the worker protocol (docs/packaging/protocol.md) in *)
(* the small-python package for JavaScript, as index.js implements it,    *)
(* against a worker that follows the protocol. TLC checks that after     *)
(* every step:                                                            *)
(*                                                                         *)
(*  - The parent never sends a handle the worker has released, nor        *)
(*    releases one twice (either makes the worker exit with status 3),   *)
(*    and releases one only after its PyObject was released or collected.*)
(*  - The turns form one stack (6): the parent sends a request only while *)
(*    it holds the turn, and each reply answers the innermost request.   *)
(*  - No operation waits forever (TLC's deadlock check): the worker       *)
(*    answers, the timeout loses the worker, or close ends it; then every *)
(*    waiting write and read settles, including host functions that      *)
(*    catch the error.                                                    *)
(*                                                                         *)
(* The implementation, step by step:                                     *)
(*                                                                         *)
(*  - Operations are asynchronous. Each callback level runs one at a time *)
(*    (_run), and close may be called while one of the top level waits.  *)
(*  - _request encodes its message and _send takes the release queue in  *)
(*    the same synchronous run, so no PyObject can be collected or        *)
(*    released in between; a released PyObject cannot be encoded.        *)
(*  - _write puts the bytes in the worker's inbox as it takes them, and   *)
(*    waits while the inbox is full; _next then waits for a reply. Both   *)
(*    waits end once the runtime is lost or closed.                       *)
(*  - release() and the FinalizationRegistry's callback queue the id      *)
(*    unless the runtime is lost or closed.                               *)
(*  - The timer loses the worker (_lose, then _end) outside host           *)
(*    callbacks; _serve rethrows lost after a host function returns.      *)
(*  - close is refused while a host function runs; otherwise it ends the  *)
(*    worker and rejects the waiting read.                                *)
(***************************************************************************)
EXTENDS Naturals, Sequences

CONSTANTS Handles,  \* handle ids the worker may send; 0 is none
          Depth     \* the most frames the parent may have at once

None == {}

VARIABLES wk,       \* the worker's table: "none" (not sent), "live", "released"
          held,     \* the program may still use the handle's PyObject
          gc,       \* its PyObject: "none" (not made), "live", "unreachable", "done"
          queue,    \* _released: ids to send with the next message
          outbox,   \* messages _write is putting in the inbox, in order
          to,       \* messages in the worker's inbox, in order
          from,     \* messages from the worker not yet read
          pstack,   \* the parent's frames, innermost last: "S" writing a request,
                    \* "N" about to wait for its reply, "R" waiting for it,
                    \* "H" a host function running, "T" writing its reply
          waiter,   \* _next's waiter is set
          wstack,   \* the worker's: "W" handling a request, "N" awaiting a reply
          alive,    \* the worker runs
          timed,    \* a timeout is set
          closed, lost,
          bad       \* ghost: the worker saw the parent break the protocol

vars == <<wk, held, gc, queue, outbox, to, from, pstack, waiter, wstack, alive, timed, closed, lost, bad>>

Init == /\ wk = [h \in Handles |-> "none"] /\ held = [h \in Handles |-> FALSE]
        /\ gc = [h \in Handles |-> "none"] /\ queue = {} /\ outbox = <<>>
        /\ to = <<>> /\ from = <<>> /\ pstack = <<>> /\ waiter = FALSE /\ wstack = <<>>
        /\ alive = TRUE /\ timed \in BOOLEAN /\ closed = FALSE /\ lost = FALSE /\ bad = FALSE

Top(s) == IF s = <<>> THEN "" ELSE s[Len(s)]
Pop(s) == SubSeq(s, 1, Len(s) - 1)
Msg(k, ids) == [k |-> k, ids |-> ids]
Carried(m) == IF m = 0 THEN None ELSE {m}
HeldSet == {h \in Handles : held[h]}
Over == lost \/ closed
InCallback == \E i \in 1..Len(pstack) : pstack[i] = "H"

\* The program runs: at the top level, or in a host function, its level.
Program == Top(pstack) \in {"", "H"}

\* _send: the notice of what was queued, then the message, to _write.
Send(m) == /\ outbox' = outbox \o (IF queue = {} THEN <<m>> ELSE <<Msg("release", queue), m>>)
           /\ queue' = {}

Request(ids) == /\ Program /\ ~Over /\ Len(pstack) < Depth /\ ids \subseteq HeldSet
                /\ Send(Msg("req", ids)) /\ pstack' = Append(pstack, "S")
                /\ UNCHANGED <<wk, held, gc, to, from, waiter, wstack, alive, timed, closed, lost, bad>>

\* The worker takes the next message from the inbox's writer.
Take == /\ alive /\ outbox # <<>> /\ to' = Append(to, Head(outbox)) /\ outbox' = Tail(outbox)
        /\ UNCHANGED <<wk, held, gc, queue, from, pstack, waiter, wstack, alive, timed, closed, lost, bad>>

\* _write returns once all is in the inbox, or throws once lost or closed.
Written == /\ Top(pstack) \in {"S", "T"} /\ outbox = <<>> /\ ~Over
           /\ pstack' = IF Top(pstack) = "S" THEN Append(Pop(pstack), "N") ELSE Pop(pstack)
           /\ UNCHANGED <<wk, held, gc, queue, outbox, to, from, waiter, wstack, alive, timed, closed, lost, bad>>
\* _next: waits, or rejects once lost or closed.
Wait == /\ Top(pstack) = "N" /\ ~Over /\ pstack' = Append(Pop(pstack), "R") /\ waiter' = TRUE
        /\ UNCHANGED <<wk, held, gc, queue, outbox, to, from, wstack, alive, timed, closed, lost, bad>>
\* Every wait settles with the error once lost or closed.
Unwind == /\ Top(pstack) \in {"S", "T", "N", "R"} /\ Over /\ pstack' = Pop(pstack) /\ waiter' = FALSE
          /\ UNCHANGED <<wk, held, gc, queue, outbox, to, from, wstack, alive, timed, closed, lost, bad>>

\* _feed resolves the waiter: a reply, or a nested request.
Arrive(m) == /\ held' = [h \in Handles |-> held[h] \/ h \in m.ids]
             /\ gc' = [h \in Handles |-> IF h \in m.ids THEN "live" ELSE gc[h]]
Receive == /\ Top(pstack) = "R" /\ waiter /\ ~Over /\ from # <<>> /\ from' = Tail(from) /\ waiter' = FALSE
           /\ LET m == Head(from) IN
              /\ Arrive(m)
              \* After a nested request _awaitReply calls _next again.
              /\ pstack' = IF m.k = "result" THEN Pop(pstack) ELSE Append(Append(Pop(pstack), "N"), "H")
           /\ UNCHANGED <<wk, queue, outbox, to, wstack, alive, timed, closed, lost, bad>>

\* _end: terminates the worker; the inbox and the messages from it are gone.
End == /\ alive' = FALSE /\ queue' = {} /\ to' = <<>> /\ from' = <<>>
\* The timer, outside host callbacks.
Timeout == /\ Top(pstack) \in {"S", "T", "N", "R"} /\ timed /\ ~Over /\ lost' = TRUE /\ End
           /\ UNCHANGED <<wk, held, gc, outbox, pstack, waiter, wstack, timed, closed, bad>>

\* The host function returns, maybe a handle the program holds; _serve
\* rethrows lost, or writes the reply.
HostReturn(ids) == /\ Top(pstack) = "H" /\ ids \subseteq HeldSet
                   /\ IF lost THEN /\ pstack' = Pop(pstack) /\ UNCHANGED <<queue, outbox>>
                      ELSE /\ Send(Msg("reply", ids)) /\ pstack' = Append(Pop(pstack), "T")
                   /\ UNCHANGED <<wk, held, gc, to, from, waiter, wstack, alive, timed, closed, lost, bad>>

\* close: refused while a host function runs, even one awaiting; otherwise
\* it may come while a top-level operation waits.
Close == /\ ~InCallback /\ ~closed /\ closed' = TRUE /\ waiter' = FALSE
         /\ IF lost THEN UNCHANGED <<alive, queue, to, from>> ELSE End
         /\ UNCHANGED <<wk, held, gc, outbox, pstack, wstack, timed, lost, bad>>

\* release(), or the program dropping its last reference.
Forget(h) == /\ held[h] /\ held' = [held EXCEPT ![h] = FALSE] /\ gc' = [gc EXCEPT ![h] = "unreachable"]
             /\ UNCHANGED <<wk, queue, outbox, to, from, pstack, waiter, wstack, alive, timed, closed, lost, bad>>
\* _release, from release() at once or from the registry's callback later.
Drop(h) == /\ gc[h] = "unreachable" /\ gc' = [gc EXCEPT ![h] = "done"]
           /\ queue' = IF Over THEN queue ELSE queue \cup {h}
           /\ UNCHANGED <<wk, held, outbox, to, from, pstack, waiter, wstack, alive, timed, closed, lost, bad>>

Known(ids) == \A h \in ids : wk[h] = "live"
WorkerRead == /\ alive /\ to # <<>> /\ to' = Tail(to)
              /\ LET m == Head(to) IN
                 CASE m.k = "release" -> /\ bad' = (bad \/ ~Known(m.ids))
                                         /\ wk' = [h \in Handles |-> IF h \in m.ids THEN "released" ELSE wk[h]]
                                         /\ UNCHANGED wstack
                   [] m.k = "req"     -> /\ bad' = (bad \/ ~Known(m.ids) \/ Top(wstack) = "W")
                                         /\ wstack' = Append(wstack, "W") /\ UNCHANGED wk
                   [] OTHER           -> /\ bad' = (bad \/ ~Known(m.ids) \/ Top(wstack) # "N")
                                         /\ wstack' = Pop(wstack) /\ UNCHANGED wk
              /\ UNCHANGED <<held, gc, queue, outbox, from, pstack, waiter, alive, timed, closed, lost>>

WorkerSend(k, m) == /\ alive /\ Top(wstack) = "W" /\ IF m = 0 THEN TRUE ELSE wk[m] = "none"
                    /\ wk' = IF m = 0 THEN wk ELSE [wk EXCEPT ![m] = "live"]
                    /\ from' = Append(from, Msg(k, Carried(m)))
                    /\ wstack' = IF k = "result" THEN Pop(wstack) ELSE Append(wstack, "N")
                    /\ UNCHANGED <<held, gc, queue, outbox, to, pstack, waiter, alive, timed, closed, lost, bad>>

Done == /\ pstack = <<>> /\ Over /\ UNCHANGED vars

Next == \/ Take \/ Written \/ Wait \/ Unwind \/ Receive \/ Timeout \/ Close \/ WorkerRead \/ Done
        \/ \E ids \in SUBSET Handles : Request(ids) \/ HostReturn(ids)
        \/ \E h \in Handles : Forget(h) \/ Drop(h)
        \/ \E k \in {"result", "host"}, m \in Handles \cup {0} : WorkerSend(k, m)

Spec == Init /\ [][Next]_vars

TypeOK == /\ wk \in [Handles -> {"none", "live", "released"}] /\ held \in [Handles -> BOOLEAN]
          /\ gc \in [Handles -> {"none", "live", "unreachable", "done"}] /\ queue \subseteq Handles
          /\ Len(pstack) <= Depth + 2 /\ closed \in BOOLEAN /\ lost \in BOOLEAN

ParentFollowsProtocol == ~bad
HeldLive == \A h \in Handles : held[h] /\ ~Over => wk[h] = "live"
ReleasedDropped == \A h \in Handles : wk[h] = "released" => gc[h] = "done"
=============================================================================
