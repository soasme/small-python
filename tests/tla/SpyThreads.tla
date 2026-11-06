----------------------------- MODULE SpyThreads -----------------------------
(***************************************************************************)
(* Virtual threads of stdlib/_thread.py (docs/threads.md): every thread     *)
(* runs on the host's system thread, and switches only where it blocks.    *)
(* Names are the module's.                                                 *)
(*                                                                         *)
(*  - _start queues a thread; nothing runs it until a thread blocks.       *)
(*  - _wait: a thread that blocks, for the lock or for another thread to   *)
(*    end, goes on when that holds; else it runs the first queued thread   *)
(*    on top of itself; with none queued, a timed wait times out and a     *)
(*    wait for ever raises. Either way the thread runs on.                 *)
(*  - A thread under another resumes only when the one above it ends, and  *)
(*    _current is then its ident again.                                    *)
(*  - The host's call returns when the main thread ends; queued threads    *)
(*    are left unstarted.                                                  *)
(*                                                                         *)
(* TLC checks that only the thread on top runs and that _current names it; *)
(* that a wait ends only when what it waits for holds or nothing is left   *)
(* to run; that the lock goes only to the thread that took it; and, by     *)
(* deadlock checking and Termination, that the host's call always returns. *)
(***************************************************************************)
EXTENDS Naturals, Sequences

CONSTANTS Workers, Budget
Main == "main"
Threads == {Main} \cup Workers
None == "none"
Lock == "lock"

\* pc: "unborn", "queued", "run", "wait" (in _wait), "done".
VARIABLES pc, stack, queue, holder, want, current, used
vars == <<pc, stack, queue, holder, want, current, used>>

TypeOK ==
    /\ pc \in [Threads -> {"unborn", "queued", "run", "wait", "done"}]
    /\ stack \in Seq(Threads) /\ queue \in Seq(Workers)
    /\ holder \in Threads \cup {None}
    /\ want \in [Threads -> {None, Lock} \cup Workers]
    /\ current \in Threads
    /\ used \in [Threads -> 0..Budget]

Init ==
    /\ pc = [t \in Threads |-> IF t = Main THEN "run" ELSE "unborn"]
    /\ stack = <<Main>> /\ queue = <<>> /\ holder = None
    /\ want = [t \in Threads |-> None] /\ current = Main
    /\ used = [t \in Threads |-> 0]

Top == stack[Len(stack)]
Running(t) == stack # <<>> /\ t = Top /\ pc[t] = "run"
Spend(t) == used[t] < Budget /\ used' = [used EXCEPT ![t] = @ + 1]
Ready(t) == \/ want[t] = Lock /\ holder = None
            \/ want[t] \in Workers /\ pc[want[t]] = "done"

\* lock.acquire: a free lock is taken at once; a held one makes it wait.
Acquire(t) ==
    /\ Running(t) /\ Spend(t)
    /\ IF holder = None
       THEN holder' = t /\ UNCHANGED <<pc, want>>
       ELSE pc' = [pc EXCEPT ![t] = "wait"] /\ want' = [want EXCEPT ![t] = Lock] /\ UNCHANGED holder
    /\ UNCHANGED <<stack, queue, current>>
\* lock.release, by any thread.
Release(t) ==
    /\ Running(t) /\ holder # None /\ Spend(t)
    /\ holder' = None
    /\ UNCHANGED <<pc, stack, queue, want, current>>
Start(t, w) ==
    /\ Running(t) /\ pc[w] = "unborn" /\ Spend(t)
    /\ pc' = [pc EXCEPT ![w] = "queued"] /\ queue' = Append(queue, w)
    /\ UNCHANGED <<stack, holder, want, current>>
\* _ThreadHandle.join of a started thread.
Join(t, w) ==
    /\ Running(t) /\ w # t /\ pc[w] # "unborn" /\ Spend(t)
    /\ IF pc[w] = "done"
       THEN UNCHANGED <<pc, want>>
       ELSE pc' = [pc EXCEPT ![t] = "wait"] /\ want' = [want EXCEPT ![t] = w]
    /\ UNCHANGED <<stack, queue, holder, current>>

\* One pass of _wait's loop for the thread on top.
Wait(t) ==
    /\ stack # <<>> /\ t = Top /\ pc[t] = "wait"
    /\ IF Ready(t)
       THEN /\ pc' = [pc EXCEPT ![t] = "run"] /\ want' = [want EXCEPT ![t] = None]
            /\ holder' = IF want[t] = Lock THEN t ELSE holder
            /\ UNCHANGED <<stack, queue, current>>
       ELSE IF queue # <<>>
       THEN /\ pc' = [pc EXCEPT ![Head(queue)] = "run"]
            /\ stack' = Append(stack, Head(queue)) /\ queue' = Tail(queue)
            /\ current' = Head(queue)
            /\ UNCHANGED <<holder, want>>
       \* Timed out or raised: the thread runs on without what it waited for.
       ELSE /\ pc' = [pc EXCEPT ![t] = "run"] /\ want' = [want EXCEPT ![t] = None]
            /\ UNCHANGED <<stack, queue, holder, current>>
    /\ UNCHANGED used

\* A started thread ends; the one below it resumes in _wait as itself.
End(t) ==
    /\ t \in Workers /\ Running(t)
    /\ pc' = [pc EXCEPT ![t] = "done"] /\ stack' = SubSeq(stack, 1, Len(stack) - 1)
    /\ current' = stack[Len(stack) - 1]
    /\ UNCHANGED <<queue, holder, want, used>>
\* The host's call returns once the main thread is alone and ends.
Return ==
    /\ Running(Main)
    /\ pc' = [pc EXCEPT ![Main] = "done"] /\ stack' = <<>>
    /\ UNCHANGED <<queue, holder, want, current, used>>

Next ==
    \/ \E t \in Threads : Acquire(t) \/ Release(t) \/ Wait(t) \/ End(t)
    \/ \E t \in Threads, w \in Workers : Start(t, w) \/ Join(t, w)
    \/ Return
    \/ pc[Main] = "done" /\ UNCHANGED vars

Spec == Init /\ [][Next]_vars /\ WF_vars(Next)

\* Every thread below the top waits in _wait; those on the stack are the
\* started threads that have not ended.
OnlyTopRuns ==
    /\ \A i \in 1..Len(stack) - 1 : pc[stack[i]] = "wait"
    /\ \A t \in Threads : pc[t] \in {"run", "wait"} <=> \E i \in 1..Len(stack) : stack[i] = t
CurrentIsTop == stack # <<>> => current = Top
\* A queued thread has not started, and is queued once.
Queued == \A i \in 1..Len(queue) : pc[queue[i]] = "queued" /\ \A j \in 1..Len(queue) : i # j => queue[i] # queue[j]
\* A wait ends only when what it waits for holds or nothing is left to run;
\* a lock wait that holds takes the lock.
WaitsHonest ==
    [][\A t \in Threads : pc[t] = "wait" /\ pc'[t] = "run" =>
         \/ Ready(t) /\ (want[t] = Lock => holder' = t)
         \/ queue = <<>> /\ holder' = holder]_vars
Termination == <>(pc[Main] = "done")
==============================================================================
