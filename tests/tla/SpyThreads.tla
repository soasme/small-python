----------------------------- MODULE SpyThreads -----------------------------
(***************************************************************************)
(* The host-facing contract of stdlib/_thread.c: Python threads, each on a *)
(* system thread, take turns at one context through spy_thread_swap and    *)
(* spy_set_switch (docs/threads.md). Names are the C file's.               *)
(*                                                                         *)
(*  - take_turn draws the next ticket and waits until serving reaches it,  *)
(*    then swaps its state in; give_turn swaps it out and serves the next  *)
(*    ticket. The host's thread starts with ticket 0 and its state in.     *)
(*  - A lock that is taken makes the caller give its turn, wait until the  *)
(*    lock is free, take it, then take a turn again.                       *)
(*  - switch_turn gives the turn and takes it again when another ticket    *)
(*    waits; the switch is set while a started thread lives.               *)
(*  - A started thread that ends swaps its state out and frees it, then    *)
(*    serves the next ticket and leaves.                                   *)
(*  - The host frees the context only from outside the engine. The module  *)
(*    closes: every waiting thread leaves without touching the context,    *)
(*    and the module's memory goes once no system thread remains.          *)
(*                                                                         *)
(* TLC checks that one thread at a time uses the context, holding the turn *)
(* and its own state in it; that the host holds the turn whenever it is    *)
(* outside the engine; that the switch is set exactly while a started      *)
(* thread lives; that nothing touches the module after it is freed; and,   *)
(* by deadlock checking, that a program whose threads release what they    *)
(* take always runs on until the context is freed.                         *)
(***************************************************************************)
EXTENDS Naturals, FiniteSets

CONSTANTS Workers, Calls, Budget
Host == "host"
Threads == {Host} \cup Workers
Blank == "blank"
None == "none"

\* pc: the host is "out" of the engine or "in" a call; a started thread is
\* "unborn", "born" (created, wants a first turn), "run" (using the context),
\* "gone". Either may be "turn" (wants a turn), "queued" (holds a ticket),
\* or "lock" (waits for the lock without a turn). The host's last states are
\* "freeing" and "freed".
VARIABLES pc, ticket, next, serving, ctx, slot, holder, closing, systems, live, switch, freed, calls, used
vars == <<pc, ticket, next, serving, ctx, slot, holder, closing, systems, live, switch, freed, calls, used>>

Using == {"in", "run"}

TypeOK ==
    /\ pc \in [Threads -> {"out", "in", "unborn", "born", "run", "gone", "turn", "queued", "lock", "freeing", "freed"}]
    /\ ticket \in [Threads -> Nat] /\ next \in Nat /\ serving \in Nat
    /\ ctx \in Threads \cup {Blank}
    /\ slot \in [Threads -> Threads \cup {Blank, None}]
    /\ holder \in Threads \cup {None}
    /\ closing \in BOOLEAN /\ systems \in Nat /\ live \in Nat /\ switch \in BOOLEAN /\ freed \in BOOLEAN
    /\ calls \in 0..Calls /\ used \in [Threads -> 0..Budget]

Init ==
    /\ pc = [t \in Threads |-> IF t = Host THEN "out" ELSE "unborn"]
    /\ ticket = [t \in Threads |-> 0] /\ next = 1 /\ serving = 0
    /\ ctx = Host
    /\ slot = [t \in Threads |-> IF t = Host THEN Blank ELSE None]
    /\ holder = None
    /\ closing = FALSE /\ systems = 0 /\ live = 0 /\ switch = FALSE /\ freed = FALSE
    /\ calls = 0 /\ used = [t \in Threads |-> 0]

Running(t) == pc[t] \in Using
Spend(t) == used[t] < Budget /\ used' = [used EXCEPT ![t] = @ + 1]
\* spy_thread_swap: the context's state and the thread's slot change places.
Swap(t) == ctx' = slot[t] /\ slot' = [slot EXCEPT ![t] = ctx]
Resume(t) == IF t = Host THEN "in" ELSE "run"

Enter ==
    /\ pc[Host] = "out" /\ calls < Calls
    /\ pc' = [pc EXCEPT ![Host] = "in"] /\ calls' = calls + 1
    /\ UNCHANGED <<ticket, next, serving, ctx, slot, holder, closing, systems, live, switch, freed, used>>
Return ==
    /\ pc[Host] = "in" /\ holder # Host
    /\ pc' = [pc EXCEPT ![Host] = "out"]
    /\ UNCHANGED <<ticket, next, serving, ctx, slot, holder, closing, systems, live, switch, freed, calls, used>>

\* _spawn: a new state and system thread; the first live one sets the switch.
Spawn(t, w) ==
    /\ Running(t) /\ pc[w] = "unborn"
    /\ pc' = [pc EXCEPT ![w] = "born"] /\ slot' = [slot EXCEPT ![w] = w]
    /\ systems' = systems + 1 /\ live' = live + 1 /\ switch' = TRUE
    /\ UNCHANGED <<ticket, next, serving, ctx, holder, closing, freed, calls, used>>

\* take_turn, first half: draw a ticket, or leave when closing.
Draw(t) ==
    /\ pc[t] \in {"born", "turn"}
    /\ IF closing
       THEN pc' = [pc EXCEPT ![t] = "gone"] /\ systems' = systems - 1 /\ UNCHANGED <<ticket, next>>
       ELSE pc' = [pc EXCEPT ![t] = "queued"] /\ ticket' = [ticket EXCEPT ![t] = next] /\ next' = next + 1
            /\ UNCHANGED systems
    /\ UNCHANGED <<serving, ctx, slot, holder, closing, live, switch, freed, calls, used>>
\* take_turn, second half: served, swap the state in; or leave when closing.
Served(t) ==
    /\ pc[t] = "queued" /\ (serving = ticket[t] \/ closing)
    /\ IF closing
       THEN pc' = [pc EXCEPT ![t] = "gone"] /\ systems' = systems - 1 /\ UNCHANGED <<ctx, slot>>
       ELSE pc' = [pc EXCEPT ![t] = Resume(t)] /\ Swap(t) /\ UNCHANGED systems
    /\ UNCHANGED <<ticket, next, serving, holder, closing, live, switch, freed, calls, used>>

\* give_turn, then wait as s.
Give(t, s) == pc' = [pc EXCEPT ![t] = s] /\ Swap(t) /\ serving' = serving + 1

Acquire(t) ==
    /\ Running(t) /\ holder # t /\ Spend(t)
    /\ IF holder = None
       THEN holder' = t /\ UNCHANGED <<pc, ctx, slot, serving>>
       ELSE Give(t, "lock") /\ UNCHANGED holder
    /\ UNCHANGED <<ticket, next, closing, systems, live, switch, freed, calls>>
\* The lock wait's loop: leave when closing, or take a free lock.
Woken(t) ==
    /\ pc[t] = "lock" /\ (holder = None \/ closing)
    /\ IF closing
       THEN pc' = [pc EXCEPT ![t] = "gone"] /\ systems' = systems - 1 /\ UNCHANGED holder
       ELSE pc' = [pc EXCEPT ![t] = "turn"] /\ holder' = t /\ UNCHANGED systems
    /\ UNCHANGED <<ticket, next, serving, ctx, slot, closing, live, switch, freed, calls, used>>
Release(t) ==
    /\ Running(t) /\ holder = t
    /\ holder' = None
    /\ UNCHANGED <<pc, ticket, next, serving, ctx, slot, closing, systems, live, switch, freed, calls, used>>

\* switch_turn: called only while set, it yields when another ticket waits.
Switch(t) ==
    /\ Running(t) /\ switch /\ next - serving > 1 /\ Spend(t)
    /\ Give(t, "turn")
    /\ UNCHANGED <<ticket, next, holder, closing, systems, live, switch, freed, calls>>

\* thread_main's end: the last live thread clears the switch; the state is
\* swapped out and freed, and the next ticket served.
End(w) ==
    /\ w \in Workers /\ pc[w] = "run" /\ holder # w
    /\ pc' = [pc EXCEPT ![w] = "gone"]
    /\ ctx' = slot[w] /\ slot' = [slot EXCEPT ![w] = None]
    /\ serving' = serving + 1 /\ systems' = systems - 1
    /\ live' = live - 1 /\ switch' = (live - 1 > 0)
    /\ UNCHANGED <<ticket, next, holder, closing, freed, calls, used>>

\* spy_context_free from outside the engine: the module closes, waits for
\* the system threads, and frees its memory.
Free ==
    /\ pc[Host] = "out" /\ ~closing
    /\ pc' = [pc EXCEPT ![Host] = "freeing"] /\ closing' = TRUE
    /\ UNCHANGED <<ticket, next, serving, ctx, slot, holder, systems, live, switch, freed, calls, used>>
Freed ==
    /\ pc[Host] = "freeing" /\ systems = 0
    /\ pc' = [pc EXCEPT ![Host] = "freed"] /\ freed' = TRUE
    /\ UNCHANGED <<ticket, next, serving, ctx, slot, holder, closing, systems, live, switch, calls, used>>

Next ==
    \/ Enter \/ Return \/ Free \/ Freed
    \/ \E t \in Threads : Draw(t) \/ Served(t) \/ Acquire(t) \/ Woken(t) \/ Release(t) \/ Switch(t)
    \/ \E t \in Threads, w \in Workers : Spawn(t, w)
    \/ \E w \in Workers : End(w)
    \/ pc[Host] = "freed" /\ UNCHANGED vars

Spec == Init /\ [][Next]_vars

\* One thread uses the context at a time, holding the turn, with its own
\* state in the context.
Exclusive == Cardinality({t \in Threads : Running(t)}) <= 1
OwnState == \A t \in Threads : Running(t) => ctx = t /\ ticket[t] = serving
\* Outside the engine the host holds the turn, with its state in.
HostHolds == pc[Host] = "out" => ctx = Host /\ ticket[Host] = serving /\ \A w \in Workers : pc[w] # "run"
SwitchSet == switch <=> live > 0
\* A thread's state is in one place: the context or its own slot.
OneState == \A t \in Threads : pc[t] \notin {"unborn", "gone"} => (ctx = t) # (slot[t] = t)
\* After the module is freed no system thread of it remains.
NoUseAfterFree == freed => systems = 0 /\ \A w \in Workers : pc[w] \in {"unborn", "gone"}
==============================================================================
