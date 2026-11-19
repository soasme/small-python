--------------------------- MODULE WeakCallbacks ---------------------------
(***************************************************************************)
(* The callbacks of host weak references when their target dies, as       *)
(* PLS-315 9.7 and Annex B specify them: the target's __del__ runs first, *)
(* then the callback of each reference, given the reference, already      *)
(* dead, before the statement after the one that dropped the target; a    *)
(* callback that drops another target has that target's callback run     *)
(* after it; and an exception a callback raises is reported, not         *)
(* propagated.                                                            *)
(*                                                                         *)
(* A program drops an object, with or without a __del__ logging "del",    *)
(* with one weak reference whose callback logs "callback", then, when     *)
(* chains, drops a second object, whose callback logs "second", and, when *)
(* fails, raises. When cyclic, the first object, which has no __del__,  *)
(* refers to itself, and a collection the program asks for reclaims it,  *)
(* the callbacks running before it returns. Each runs in a function or   *)
(* in a suspended generator.                                              *)
(* The outcome is the log, ending with "after".                           *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == {p \in [finalizer : BOOLEAN, chains : BOOLEAN, fails : BOOLEAN, cyclic : BOOLEAN, place : {"function", "generator"}] :
                ~(p.cyclic /\ p.finalizer)}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

Run(p) == (IF p.finalizer THEN <<"del">> ELSE <<>>) \o <<"callback">> \o
          (IF p.chains THEN <<"second">> ELSE <<>>) \o <<"after">>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Every callback runs before the next statement, whether or not it raised.
CallbacksFirst == Done => outcome[Len(outcome)] = "after"
=============================================================================
