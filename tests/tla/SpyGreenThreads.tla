-------------------------- MODULE SpyGreenThreads --------------------------
(***************************************************************************)
(* The scheduler docs/greenthread.md proposes; nothing of it is in spy.c   *)
(* yet. Threads of one context take turns on one C stack:                  *)
(*                                                                         *)
(*  - A thread whose frames are all on the heap is parked: switching away  *)
(*    from it leaves nothing on the C stack, and it resumes above whatever *)
(*    the stack holds.                                                     *)
(*  - A thread is pinned while C code (a native that called Python, a sort *)
(*    key, __eq__ called by a dict) is between its frames. Its C frames    *)
(*    stay on the stack, in `stack`, bottom to top. A pinned thread is     *)
(*    never preempted; when it waits, other threads run above it, and it   *)
(*    resumes only from the top, by a C return.                            *)
(*  - A lock passes from its releaser straight to one waiter.              *)
(*  - A host wait (spy_wait) ends when the host settles it, at any time.   *)
(*  - When no thread can run and no host wait is outstanding, the wait on  *)
(*    top of the stack (or Main's, on an empty stack) raises RuntimeError: *)
(*    "deadlock" when no thread is ready, "buried" when every ready thread *)
(*    is pinned under another thread's C frames.                           *)
(*  - The outermost call returns once Main has finished and no C frames    *)
(*    of another thread remain; parked threads stay for the next call.     *)
(*                                                                         *)
(* TLC checks that a running pinned thread is always on top, so its C      *)
(* returns land in its own frames; that no waiter sits on a free lock; and *)
(* that a thread lies under another only because it waited while pinned;  *)
(* and (deadlock checking) that the scheduler never stops unreturned.      *)
(* Budget bounds each thread's acquires, pins, yields and host calls.      *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets, TLC

CONSTANTS Threads, Main, Locks, MaxPin, Budget
ASSUME Main \in Threads

None == "none"
Host == "host"

VARIABLES state, pin, stack, owner, wait, current, used, raised, sunk
vars == <<state, pin, stack, owner, wait, current, used, raised, sunk>>

Range(s) == {s[i] : i \in DOMAIN s}
Top == stack[Len(stack)]
OnTop(t) == stack # <<>> /\ Top = t

TypeOK ==
    /\ state \in [Threads -> {"ready", "running", "waiting", "done"}]
    /\ pin \in [Threads -> 0..MaxPin]
    /\ stack \in Seq(Threads)
    /\ owner \in [Locks -> Threads \cup {None}]
    /\ wait \in [Threads -> Locks \cup {Host, None}]
    /\ current \in Threads \cup {None}
    /\ used \in [Threads -> 0..Budget]
    /\ raised \in {"none", "deadlock", "buried"}
    /\ sunk \in [Threads -> BOOLEAN]

Init ==
    /\ state = [t \in Threads |-> IF t = Main THEN "running" ELSE "ready"]
    /\ pin = [t \in Threads |-> 0]
    /\ stack = <<>>
    /\ owner = [l \in Locks |-> None]
    /\ wait = [t \in Threads |-> None]
    /\ current = Main
    /\ used = [t \in Threads |-> 0]
    /\ raised = "none"
    /\ sunk = [t \in Threads |-> FALSE]

Running(t) == current = t
Spend(t) == used[t] < Budget /\ used' = [used EXCEPT ![t] = @ + 1]
\* The running thread stops: it waits or yields, and the scheduler chooses.
\* sunk records that a pinned thread left the top by waiting.
Leave(t, s, w) ==
    /\ state' = [state EXCEPT ![t] = s]
    /\ wait' = [wait EXCEPT ![t] = w]
    /\ current' = None
    /\ sunk' = [sunk EXCEPT ![t] = s = "waiting" /\ pin[t] > 0]

Acquire(t, l) ==
    /\ Running(t) /\ owner[l] # t /\ Spend(t)
    /\ IF owner[l] = None
       THEN owner' = [owner EXCEPT ![l] = t] /\ UNCHANGED <<state, wait, current, sunk>>
       ELSE Leave(t, "waiting", l) /\ UNCHANGED owner
    /\ UNCHANGED <<pin, stack, raised>>

Release(t, l) ==
    /\ Running(t) /\ owner[l] = t
    /\ LET waiters == {u \in Threads : state[u] = "waiting" /\ wait[u] = l} IN
       IF waiters = {}
       THEN owner' = [owner EXCEPT ![l] = None] /\ UNCHANGED <<state, wait>>
       ELSE \E u \in waiters :
              /\ owner' = [owner EXCEPT ![l] = u]
              /\ state' = [state EXCEPT ![u] = "ready"]
              /\ wait' = [wait EXCEPT ![u] = None]
    /\ UNCHANGED <<pin, stack, current, used, raised, sunk>>

\* C code calls Python: the first such frame puts t on the C stack.
Pin(t) ==
    /\ Running(t) /\ pin[t] < MaxPin /\ Spend(t)
    /\ pin' = [pin EXCEPT ![t] = @ + 1]
    /\ stack' = IF pin[t] = 0 THEN Append(stack, t) ELSE stack
    /\ UNCHANGED <<state, owner, wait, current, raised, sunk>>

\* That C code returns; its last frame leaves the top of the C stack.
Unpin(t) ==
    /\ Running(t) /\ pin[t] > 0
    /\ pin' = [pin EXCEPT ![t] = @ - 1]
    /\ stack' = IF pin[t] = 1 THEN SubSeq(stack, 1, Len(stack) - 1) ELSE stack
    /\ UNCHANGED <<state, owner, wait, current, used, raised, sunk>>

\* Preemption at a call or loop pass, only while parked frames are all t has.
Yield(t) ==
    /\ Running(t) /\ pin[t] = 0 /\ Spend(t)
    /\ Leave(t, "ready", None)
    /\ UNCHANGED <<pin, stack, owner, raised>>

HostWait(t) ==
    /\ Running(t) /\ Spend(t)
    /\ Leave(t, "waiting", Host)
    /\ UNCHANGED <<pin, stack, owner, raised>>

\* A thread ends, keeping any lock it still holds.
End(t) ==
    /\ Running(t) /\ pin[t] = 0
    /\ Leave(t, "done", None)
    /\ UNCHANGED <<pin, stack, owner, used, raised>>

Settle(t) ==
    /\ state[t] = "waiting" /\ wait[t] = Host
    /\ state' = [state EXCEPT ![t] = "ready"]
    /\ wait' = [wait EXCEPT ![t] = None]
    /\ UNCHANGED <<pin, stack, owner, current, used, raised, sunk>>

\* Threads the scheduler may run: parked ones, called above the stack, and
\* the top of the stack, returned to.
Candidates == {u \in Threads : state[u] = "ready" /\ (pin[u] = 0 \/ OnTop(u))}
Returning == current = None /\ state[Main] = "done" /\ stack = <<>>
HostPending == \E u \in Threads : wait[u] = Host

Run(u) ==
    /\ current = None /\ ~Returning /\ u \in Candidates
    /\ state' = [state EXCEPT ![u] = "running"]
    /\ current' = u
    /\ UNCHANGED <<pin, stack, owner, wait, used, raised, sunk>>

Raise ==
    /\ current = None /\ ~Returning /\ Candidates = {} /\ ~HostPending
    /\ LET victim == IF stack = <<>> THEN Main ELSE Top
           kind == IF \E u \in Threads : state[u] = "ready" THEN "buried" ELSE "deadlock" IN
       /\ Assert(state[victim] = "waiting", "the raising wait is not waiting")
       /\ Assert(kind = "deadlock" \/ \A u \in Threads : state[u] = "ready" => pin[u] > 0 /\ ~OnTop(u),
                 "a ready thread was reported buried but could run")
       /\ state' = [state EXCEPT ![victim] = "running"]
       /\ wait' = [wait EXCEPT ![victim] = None]
       /\ current' = victim
       /\ raised' = kind
    /\ UNCHANGED <<pin, stack, owner, used, sunk>>

Next ==
    \/ \E t \in Threads, l \in Locks : Acquire(t, l) \/ Release(t, l)
    \/ \E t \in Threads : Pin(t) \/ Unpin(t) \/ Yield(t) \/ HostWait(t) \/ End(t) \/ Settle(t) \/ Run(t)
    \/ Raise
    \/ Returning /\ UNCHANGED vars

Spec == Init /\ [][Next]_vars

\* A pinned thread is on the C stack once, and nothing else is.
PinnedOnStack == \A t \in Threads : pin[t] > 0 <=> t \in Range(stack)
StackDistinct == Len(stack) = Cardinality(Range(stack))
\* Its C frames are the stack's top whenever it runs, so its returns are its own.
RunningOnTop == current # None /\ pin[current] > 0 => OnTop(current)
OneRunning == \A t \in Threads : state[t] = "running" <=> current = t
Waiting == \A t \in Threads : state[t] = "waiting" <=> wait[t] # None
\* A lock someone waits for is held by another thread: no wakeup is lost.
NoLostWakeup == \A t \in Threads : wait[t] \in Locks => owner[wait[t]] \notin {None, t}
\* A thread lies under another's C frames only because it waited while
\* pinned: a program that never blocks inside a C callback is never buried.
BuriedByWaiting == \A i \in 1..Len(stack) - 1 : sunk[stack[i]]
=============================================================================
