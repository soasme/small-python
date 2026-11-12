------------------------------ MODULE SpyCalls ------------------------------
(***************************************************************************)
(* The call stack of a context, as spy.c's call_enter, unit_enter,        *)
(* call_leave, call_function and run_machine keep it. A function whose    *)
(* body is on the machine runs as a call on the context's stack: a call   *)
(* it makes of such a function, of exec() or eval() on source, of a       *)
(* module of source an import statement runs (import_step), or of a       *)
(* Python special method a step waits for (a key's __hash__, __index__,   *)
(* __instancecheck__, a generator's close, a dead instance's __del__, a   *)
(* class statement's metaclass __new__, a new class's __set_name__ and    *)
(* __init_subclass__, an attribute store's or deletion's Python hook, an  *)
(* item's __repr__ in a list's or tuple's repr), pushes another call      *)
(* there, and the same run_machine goes on (a machine call), as it        *)
(* resumes a generator a loop or a yield from takes items from; a call    *)
(* that C makes (a host call, a special method the machine does not take, *)
(* a trace function) enters a new run_machine, one level of C nesting.    *)
(* The call stack's storage is kept for reuse, Keep entries of it once     *)
(* the outermost call has returned.                                       *)
(*                                                                         *)
(* C code that a step calls may call Python on through callk, as Lua's   *)
(* lua_callk: the call is a machine call carrying the continuation's      *)
(* context (CALL_K); when it returns, the continuation runs on the        *)
(* caller's machine and either finishes, releasing its context (its      *)
(* value pushed, or the consumer under way going on), or calls again     *)
(* with it (c->k_fn), which the step enters before anything else.        *)
(* A call refused at the recursion limit releases the context unrun.      *)
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
(*  - A continuation's context is released once, never while a call or  *)
(*    a pending callk holds it, and every one is released once no call   *)
(*    runs: continuations add no C nesting and leak nothing.              *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS Limit,    \* the recursion limit
          Keep,     \* storage entries kept after the outermost call
          Envs,     \* environments, one per call made
          Ks        \* continuation contexts, one per callk begun

VARIABLES calls,    \* calls in progress, innermost last: [env, host]
          slots,    \* slots[i]: the env stored in storage entry i, or "free"
          nesting,  \* run_machine invocations in progress (C nesting)
          leaving,  \* <<the call popped whose leave_frame is running>>, or <<>>
          used,     \* environments ever entered
          released, \* released[e]: times environment e was released
          error,    \* the last call raised RecursionError
          kused,    \* continuation contexts ever begun
          kreleased, \* kreleased[k]: times context k was released
          pending   \* the context of a callk a continuation left (c->k_fn), or "none"

vars == <<calls, slots, nesting, leaving, used, released, error, kused, kreleased, pending>>
kvars == <<kused, kreleased, pending>>

Init == /\ calls = <<>> /\ slots = <<>> /\ nesting = 0 /\ leaving = <<>>
        /\ used = {} /\ released = [e \in Envs |-> 0] /\ error = FALSE
        /\ kused = {} /\ kreleased = [k \in Ks |-> 0] /\ pending = "none"

Hosts == Cardinality({i \in 1..Len(calls) : calls[i].host})

\* Store env in the storage entry for call number n, growing it when needed.
Store(n, e) == IF n <= Len(slots) THEN [slots EXCEPT ![n] = e] ELSE Append(slots, e)

\* A call of a machine function: from C (host) or from the innermost call,
\* carrying continuation context k ("none" for a plain call).
Call(e, host, k) ==
    /\ e \notin used /\ leaving = <<>>
    /\ host \/ calls # <<>>
    /\ IF Len(calls) >= Limit
       THEN /\ error' = TRUE
            /\ kreleased' = IF k = "none" THEN kreleased ELSE [kreleased EXCEPT ![k] = @ + 1]
            /\ UNCHANGED <<calls, slots, nesting, used, released>>
       ELSE /\ calls' = Append(calls, [env |-> e, host |-> host, k |-> k])
            /\ slots' = Store(Len(calls) + 1, e)
            /\ nesting' = IF host THEN nesting + 1 ELSE nesting
            /\ used' = used \cup {e}
            /\ error' = FALSE
            /\ UNCHANGED <<released, kreleased>>
    /\ UNCHANGED leaving

Enter(e, host) == pending = "none" /\ Call(e, host, "none") /\ UNCHANGED <<kused, pending>>

\* A step's C code begins callk with a new context, from the innermost call.
EnterK(e, k) == pending = "none" /\ k \notin kused /\ Call(e, FALSE, k)
                /\ kused' = kused \cup {k} /\ UNCHANGED pending

\* The step enters the call a continuation left, before anything else.
Again(e) == pending # "none" /\ Call(e, FALSE, pending) /\ pending' = "none" /\ UNCHANGED kused

\* call_leave pops the innermost call, reading its env first.
Pop == /\ leaving = <<>> /\ calls # <<>> /\ pending = "none"
       /\ leaving' = <<calls[Len(calls)]>>
       /\ calls' = SubSeq(calls, 1, Len(calls) - 1)
       /\ UNCHANGED <<slots, nesting, used, released, error, kvars>>

\* A trace function in leave_frame enters and leaves a call of its own,
\* reusing the storage entry just popped.
Trace(e) == /\ leaving # <<>> /\ e \notin used /\ Len(calls) < Limit
            /\ slots' = Store(Len(calls) + 1, e)
            /\ used' = used \cup {e}
            /\ released' = [released EXCEPT ![e] = @ + 1]
            /\ UNCHANGED <<calls, nesting, leaving, error, kvars>>

\* call_leave releases the env it read; a host call's run_machine returns,
\* and after the outermost call the storage past Keep is freed. A CALL_K's
\* continuation then runs on its caller: it finishes, releasing its
\* context, or (again) leaves another call with it.
Release(again) ==
    /\ leaving # <<>>
    /\ again => leaving[1].k # "none"
    /\ released' = [released EXCEPT ![leaving[1].env] = @ + 1]
    /\ nesting' = IF leaving[1].host THEN nesting - 1 ELSE nesting
    /\ slots' = IF calls = <<>> /\ Len(slots) > Keep THEN SubSeq(slots, 1, Keep) ELSE slots
    /\ leaving' = <<>>
    /\ kreleased' = IF leaving[1].k = "none" \/ again THEN kreleased ELSE [kreleased EXCEPT ![leaving[1].k] = @ + 1]
    /\ pending' = IF again THEN leaving[1].k ELSE pending
    /\ UNCHANGED <<calls, used, error, kused>>

Next == \/ Pop \/ Release(FALSE) \/ Release(TRUE)
        \/ \E e \in Envs : Enter(e, TRUE) \/ Enter(e, FALSE) \/ Trace(e) \/ Again(e) \/ \E k \in Ks : EnterK(e, k)

Spec == Init /\ [][Next]_vars

TypeOK == /\ Len(calls) <= Limit /\ nesting \in Nat
          /\ released \in [Envs -> Nat] /\ kreleased \in [Ks -> Nat]

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
\* A continuation's context is released once, not while a call or a pending
\* callk holds it, and none is left once no call runs.
Held(k) == pending = k \/ (leaving # <<>> /\ leaving[1].k = k) \/ \E i \in 1..Len(calls) : calls[i].k = k
ContextReleasedOnce == \A k \in Ks : /\ kreleased[k] <= 1
                                     /\ kreleased[k] = 1 => k \in kused /\ ~Held(k)
NoContextLeft == (calls = <<>> /\ leaving = <<>> /\ pending = "none") => \A k \in kused : kreleased[k] = 1
=============================================================================
