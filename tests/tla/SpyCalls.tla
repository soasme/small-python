------------------------------ MODULE SpyCalls ------------------------------
(***************************************************************************)
(* The call stack of a context, as spy.c's call_enter, unit_enter,        *)
(* call_leave, call_function and run_machine keep it. A function whose    *)
(* body is on the machine runs as a call on the context's stack: a call   *)
(* it makes of such a function, of exec() or eval() on source, of a       *)
(* module of source an import statement runs (import_step), or of a       *)
(* Python special method a step waits for (a key's __hash__, __index__,   *)
(* __instancecheck__, a generator's close, a dead instance's __del__, a   *)
(* class statement's metaclass __new__),                                  *)
(* pushes another call there, and the same run_machine goes on (a         *)
(* machine call); a call that C makes (a host call, a special method      *)
(* the machine does not take, a trace function) enters a new run_machine, *)
(* one level of C nesting.                                                *)
(* The call stack's storage is kept for reuse, Keep entries of it once     *)
(* the outermost call has returned.                                       *)
(*                                                                         *)
(* Leaving a call pops it, then leave_frame may run a trace function,     *)
(* whose own calls reuse the storage just popped; the environment and     *)
(* function released afterwards are those read before leave_frame.       *)
(*                                                                         *)
(* TLC checks that after every step:                                      *)
(*                                                                         *)
(*  - C nesting is the number of host calls in progress: a machine call   *)
(*    uses none, so a recursion of machine calls is bounded by the        *)
(*    recursion limit alone.                                               *)
(*  - The frames never exceed the recursion limit; a call past it raises  *)
(*    RecursionError and enters nothing.                                  *)
(*  - Each call's environment is released once, by its own leaving.       *)
(*  - Once no call runs, at most Keep entries of storage are kept.        *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS Limit,    \* the recursion limit
          Keep,     \* storage entries kept after the outermost call
          Envs      \* environments, one per call made

VARIABLES calls,    \* calls in progress, innermost last: [env, host]
          slots,    \* slots[i]: the env stored in storage entry i, or "free"
          nesting,  \* run_machine invocations in progress (C nesting)
          leaving,  \* <<the call popped whose leave_frame is running>>, or <<>>
          used,     \* environments ever entered
          released, \* released[e]: times environment e was released
          error     \* the last call raised RecursionError

vars == <<calls, slots, nesting, leaving, used, released, error>>

Init == /\ calls = <<>> /\ slots = <<>> /\ nesting = 0 /\ leaving = <<>>
        /\ used = {} /\ released = [e \in Envs |-> 0] /\ error = FALSE

Hosts == Cardinality({i \in 1..Len(calls) : calls[i].host})

\* Store env in the storage entry for call number n, growing it when needed.
Store(n, e) == IF n <= Len(slots) THEN [slots EXCEPT ![n] = e] ELSE Append(slots, e)

\* A call of a machine function: from C (host) or from the innermost call.
Enter(e, host) ==
    /\ e \notin used /\ leaving = <<>>
    /\ host \/ calls # <<>>
    /\ IF Len(calls) >= Limit
       THEN /\ error' = TRUE
            /\ UNCHANGED <<calls, slots, nesting, used, released>>
       ELSE /\ calls' = Append(calls, [env |-> e, host |-> host])
            /\ slots' = Store(Len(calls) + 1, e)
            /\ nesting' = IF host THEN nesting + 1 ELSE nesting
            /\ used' = used \cup {e}
            /\ error' = FALSE
            /\ UNCHANGED released
    /\ UNCHANGED leaving

\* call_leave pops the innermost call, reading its env first.
Pop == /\ leaving = <<>> /\ calls # <<>>
       /\ leaving' = <<calls[Len(calls)]>>
       /\ calls' = SubSeq(calls, 1, Len(calls) - 1)
       /\ UNCHANGED <<slots, nesting, used, released, error>>

\* A trace function in leave_frame enters and leaves a call of its own,
\* reusing the storage entry just popped.
Trace(e) == /\ leaving # <<>> /\ e \notin used /\ Len(calls) < Limit
            /\ slots' = Store(Len(calls) + 1, e)
            /\ used' = used \cup {e}
            /\ released' = [released EXCEPT ![e] = @ + 1]
            /\ UNCHANGED <<calls, nesting, leaving, error>>

\* call_leave releases the env it read; a host call's run_machine returns,
\* and after the outermost call the storage past Keep is freed.
Release == /\ leaving # <<>>
           /\ released' = [released EXCEPT ![leaving[1].env] = @ + 1]
           /\ nesting' = IF leaving[1].host THEN nesting - 1 ELSE nesting
           /\ slots' = IF calls = <<>> /\ Len(slots) > Keep THEN SubSeq(slots, 1, Keep) ELSE slots
           /\ leaving' = <<>>
           /\ UNCHANGED <<calls, used, error>>

Next == \/ Pop \/ Release
        \/ \E e \in Envs : Enter(e, TRUE) \/ Enter(e, FALSE) \/ Trace(e)

Spec == Init /\ [][Next]_vars

TypeOK == /\ Len(calls) <= Limit /\ nesting \in Nat
          /\ released \in [Envs -> Nat]

\* C nesting grows only with host calls; machine calls use none.
NestingIsHostCalls == nesting = Hosts + (IF leaving # <<>> /\ leaving[1].host THEN 1 ELSE 0)
\* The frames stay within the recursion limit.
WithinLimit == Len(calls) <= Limit
\* Each environment is released at most once, and only after it was used;
\* one still running is not released.
ReleasedOnce == \A e \in Envs : /\ released[e] <= 1
                                /\ released[e] = 1 => e \in used
                                /\ \A i \in 1..Len(calls) : calls[i].env = e => released[e] = 0
\* With nothing running, at most Keep storage entries are kept.
StorageTrimmed == (calls = <<>> /\ leaving = <<>>) => Len(slots) <= Keep
=============================================================================
