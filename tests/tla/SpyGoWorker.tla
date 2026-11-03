--------------------------- MODULE SpyGoWorker -----------------------------
(***************************************************************************)
(* The parent side of the worker protocol (docs/packaging/protocol.md) in *)
(* the Go module's worker package, as worker.go implements it, against a  *)
(* worker that follows the protocol. TLC checks that after every step:    *)
(*                                                                         *)
(*  - The parent never sends a handle the worker has released, nor        *)
(*    releases one twice (either makes the worker exit with status 3),   *)
(*    and releases one only after its Object became unreachable.          *)
(*  - The turns form one stack (6): the parent sends a request only while *)
(*    it holds the turn, and each reply answers the innermost request.   *)
(*  - No wait hangs (TLC's deadlock check): the worker answers, its exit  *)
(*    ends the wait, or the timeout does, which loses the worker; then   *)
(*    every frame unwinds, including host functions that ignore the      *)
(*    error.                                                              *)
(*                                                                         *)
(* The implementation, step by step:                                     *)
(*                                                                         *)
(*  - run and serve send the RELEASE notice of the queued ids first        *)
(*    (notice), then encode their message and send it; ids in the message *)
(*    are reachable through its fields until it is encoded, so their      *)
(*    release can only come in a later notice.                            *)
(*  - shared.release, the cleanup, queues the id under the mutex unless   *)
(*    the runtime ended.                                                  *)
(*  - The reader goroutine hands each message from the worker to the      *)
(*    parent, and the end of its output once the worker exits.            *)
(*  - A timeout or the worker's end loses it (lose, then end); serve      *)
(*    returns lost after a host function returns. end sets rt.to to nil, *)
(*    so a later send would block.                                        *)
(*  - Close closes the worker's input and waits for one message or a      *)
(*    second, then ends the worker. It fails with ErrInvalid while a host *)
(*    function runs, as eval and exec do.                                 *)
(***************************************************************************)
EXTENDS Naturals, Sequences

CONSTANTS Handles,  \* handle ids the worker may send; 0 is none
          Depth     \* the most frames the parent may have at once

None == {}

VARIABLES wk,       \* the worker's table: "none" (not sent), "live", "released"
          held,     \* the program still uses the handle's Object
          gc,       \* its Object: "none" (not made), "reachable", "found", "done"
          queue,    \* shared.released: ids the cleanup queued
          to,       \* messages to the worker, in order
          from,     \* messages from the worker the reader has not handed over
          reading,  \* the reader thread runs
          pstack,   \* the parent's frames: "R" a request awaiting its reply,
                    \* "H" a host function running, "C" Close waiting
          wstack,   \* the worker's: "W" handling a request, "N" awaiting a reply
          alive,    \* the worker process runs
          timed,    \* a timeout is set
          closed, ended, lost,
          bad       \* ghost: the worker saw the parent break the protocol

vars == <<wk, held, gc, queue, to, from, reading, pstack, wstack, alive, timed, closed, ended, lost, bad>>

Init == /\ wk = [h \in Handles |-> "none"] /\ held = [h \in Handles |-> FALSE]
        /\ gc = [h \in Handles |-> "none"] /\ queue = {}
        /\ to = <<>> /\ from = <<>> /\ reading = TRUE /\ pstack = <<>> /\ wstack = <<>>
        /\ alive = TRUE /\ timed \in BOOLEAN /\ closed = FALSE /\ ended = FALSE /\ lost = FALSE
        /\ bad = FALSE

Top(s) == IF s = <<>> THEN "" ELSE s[Len(s)]
Pop(s) == SubSeq(s, 1, Len(s) - 1)
Msg(k, ids) == [k |-> k, ids |-> ids]
Carried(m) == IF m = 0 THEN None ELSE {m}
HeldSet == {h \in Handles : held[h]}

\* The program runs: at the top level or in a host function.
Program == Top(pstack) \in {"", "H"}

\* notice, then send: blocks once ended, as rt.to is nil; the writer
\* discards what it is given once the worker is gone.
Send(m) == /\ ~ended
           /\ to' = IF ~alive THEN to
                    ELSE IF queue = {} THEN Append(to, m) ELSE to \o <<Msg("release", queue), m>>
           /\ queue' = {}

\* run: a request carrying handles the program holds.
Request(ids) == /\ Program /\ ~closed /\ ~lost /\ Len(pstack) < Depth /\ ids \subseteq HeldSet
                /\ Send(Msg("req", ids)) /\ pstack' = Append(pstack, "R")
                /\ UNCHANGED <<wk, held, gc, from, reading, wstack, alive, timed, closed, ended, lost, bad>>

\* end: kills the worker and stops the reader; nothing more is sent.
End == /\ ended' = TRUE /\ queue' = {} /\ to' = <<>> /\ alive' = FALSE /\ reading' = FALSE
\* lose (a timeout or the worker's END), then the waiting request throws.
Lose == /\ End /\ lost' = TRUE /\ pstack' = Pop(pstack)

\* receive, while a request awaits its reply: the worker's reply or nested
\* request, whose handles the program now holds, or END.
Arrive(m) == /\ held' = [h \in Handles |-> held[h] \/ h \in m.ids]
             /\ gc' = [h \in Handles |-> IF h \in m.ids THEN "reachable" ELSE gc[h]]
Receive == /\ Top(pstack) = "R" /\ reading /\ from # <<>> /\ from' = Tail(from)
           /\ LET m == Head(from) IN
              CASE m.k = "result" -> /\ Arrive(m) /\ pstack' = Pop(pstack)
                                     /\ UNCHANGED <<reading, alive, ended, lost, queue, to>>
                [] m.k = "host"   -> /\ Arrive(m) /\ pstack' = Append(pstack, "H")
                                     /\ UNCHANGED <<reading, alive, ended, lost, queue, to>>
                [] OTHER          -> /\ Lose /\ UNCHANGED <<held, gc>>
           /\ UNCHANGED <<wk, wstack, timed, closed, bad>>

Timeout == /\ Top(pstack) = "R" /\ timed /\ ~lost
           /\ Lose /\ UNCHANGED <<wk, held, gc, from, wstack, timed, closed, bad>>

\* Once lost, every request below throws in turn.
Unwind == /\ Top(pstack) = "R" /\ lost /\ pstack' = Pop(pstack)
          /\ UNCHANGED <<wk, held, gc, queue, to, from, reading, wstack, alive, timed, closed, ended, lost, bad>>

\* The host function returns, maybe a handle the program holds; serve
\* rethrows lost, or sends the reply.
HostReturn(ids) == /\ Top(pstack) = "H" /\ ids \subseteq HeldSet /\ pstack' = Pop(pstack)
                   /\ IF lost THEN UNCHANGED <<queue, to>> ELSE Send(Msg("reply", ids))
                   /\ UNCHANGED <<wk, held, gc, from, reading, wstack, alive, timed, closed, ended, lost, bad>>

\* Close: refused in a host function; ends a lost worker at once.
Close == /\ pstack = <<>> /\ ~closed /\ closed' = TRUE
         /\ IF lost THEN /\ UNCHANGED <<queue, to, pstack>>
            ELSE /\ Send(Msg("close", None)) /\ pstack' = Append(pstack, "C")
         /\ UNCHANGED <<wk, held, gc, from, reading, wstack, alive, timed, ended, lost, bad>>
Discard == /\ Top(pstack) = "C" /\ reading /\ from # <<>> /\ from' = Tail(from)
           /\ End /\ pstack' = Pop(pstack)
           /\ UNCHANGED <<wk, held, gc, wstack, timed, closed, lost, bad>>
CloseTimeout == /\ Top(pstack) = "C" /\ End /\ pstack' = Pop(pstack)
                /\ UNCHANGED <<wk, held, gc, from, wstack, timed, closed, lost, bad>>

Forget(h) == /\ Program /\ held[h] /\ held' = [held EXCEPT ![h] = FALSE]
             /\ UNCHANGED <<wk, gc, queue, to, from, reading, pstack, wstack, alive, timed, closed, ended, lost, bad>>
Collect(h) == /\ gc[h] = "reachable" /\ ~held[h] /\ gc' = [gc EXCEPT ![h] = "found"]
              /\ UNCHANGED <<wk, held, queue, to, from, reading, pstack, wstack, alive, timed, closed, ended, lost, bad>>
\* shared.release, under the mutex.
Drop(h) == /\ gc[h] = "found" /\ gc' = [gc EXCEPT ![h] = "done"]
           /\ queue' = IF ended THEN queue ELSE queue \cup {h}
           /\ UNCHANGED <<wk, held, to, from, reading, pstack, wstack, alive, timed, closed, ended, lost, bad>>

\* The worker reads the next message; an unknown or released id, or a
\* message out of turn, is the parent's bug.
Known(ids) == \A h \in ids : wk[h] = "live"
WorkerRead == /\ alive /\ to # <<>> /\ to' = Tail(to)
              /\ LET m == Head(to) IN
                 CASE m.k = "release" -> /\ bad' = (bad \/ ~Known(m.ids))
                                         /\ wk' = [h \in Handles |-> IF h \in m.ids THEN "released" ELSE wk[h]]
                                         /\ UNCHANGED <<wstack, alive, from>>
                   [] m.k = "req"     -> /\ bad' = (bad \/ ~Known(m.ids) \/ Top(wstack) = "W")
                                         /\ wstack' = Append(wstack, "W") /\ UNCHANGED <<wk, alive, from>>
                   [] m.k = "reply"   -> /\ bad' = (bad \/ ~Known(m.ids) \/ Top(wstack) # "N")
                                         /\ wstack' = Pop(wstack) /\ UNCHANGED <<wk, alive, from>>
                   [] OTHER           -> /\ alive' = FALSE /\ from' = Append(from, Msg("end", None))
                                         /\ UNCHANGED <<wk, wstack, bad>>
              /\ UNCHANGED <<held, gc, queue, reading, pstack, timed, closed, ended, lost>>

\* The worker answers the innermost request, or makes a nested one, maybe
\* carrying a new handle; the worker's output ends when it exits.
WorkerSend(k, m) == /\ alive /\ Top(wstack) = "W" /\ IF m = 0 THEN TRUE ELSE wk[m] = "none"
                    /\ wk' = IF m = 0 THEN wk ELSE [wk EXCEPT ![m] = "live"]
                    /\ from' = Append(from, Msg(k, Carried(m)))
                    /\ wstack' = IF k = "result" THEN Pop(wstack) ELSE Append(wstack, "N")
                    /\ UNCHANGED <<held, gc, queue, to, reading, pstack, alive, timed, closed, ended, lost, bad>>

\* What is left when the program is done: nothing waits.
Done == /\ pstack = <<>> /\ (closed \/ lost) /\ UNCHANGED vars

Next == \/ Receive \/ Timeout \/ Unwind \/ Close \/ Discard \/ CloseTimeout \/ WorkerRead \/ Done
        \/ \E ids \in SUBSET Handles : Request(ids) \/ HostReturn(ids)
        \/ \E h \in Handles : Forget(h) \/ Collect(h) \/ Drop(h)
        \/ \E k \in {"result", "host"}, m \in Handles \cup {0} : WorkerSend(k, m)

Spec == Init /\ [][Next]_vars

TypeOK == /\ wk \in [Handles -> {"none", "live", "released"}] /\ held \in [Handles -> BOOLEAN]
          /\ gc \in [Handles -> {"none", "reachable", "found", "done"}] /\ queue \subseteq Handles
          /\ Len(pstack) <= Depth + 1 /\ closed \in BOOLEAN /\ lost \in BOOLEAN

\* The worker never exits with status 3 for the parent's sake.
ParentFollowsProtocol == ~bad
\* What the program can still use is in the worker's table.
HeldLive == \A h \in Handles : held[h] /\ ~ended => wk[h] = "live"
\* A released handle's Object was unreachable.
ReleasedUnreachable == \A h \in Handles : wk[h] = "released" => gc[h] = "done"
=============================================================================
