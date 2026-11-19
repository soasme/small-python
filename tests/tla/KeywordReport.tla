------------------------------ MODULE KeywordReport ------------------------------
(***************************************************************************)
(* A built-in's report of keywords naming none of its keyword parameters   *)
(* (PLS-315 7.4.4), for every call                                         *)
(*                                                                         *)
(*     sorted([], **{k1: 1, k2: 1})      # one or two keywords             *)
(*                                                                         *)
(* whose keys are str subclass instances with a Python __eq__, compared by *)
(* p == key with the names key and reverse in turn. Each __eq__ is true    *)
(* for no name, for key, for reverse, or raises. The outcome is the error  *)
(* and the number of __eq__ calls made.                                    *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Answers == {"none", "key", "reverse", "raise"}
Programs == {<<a>> : a \in Answers} \cup {<<a, b>> : a, b \in Answers}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", 0>>

\* The calls one key's comparisons make, and whether it matched a name.
Calls(a) == CASE a = "key" -> 1 [] a = "reverse" -> 2 [] a = "none" -> 2 [] a = "raise" -> 1

RECURSIVE Report(_, _, _)
Report(keys, i, calls) ==
    IF i > Len(keys) THEN <<"invalid", calls>>
    ELSE LET a == keys[i] IN
         CASE a = "raise" -> <<"LookupError", calls + 1>>
           [] a = "none" -> <<"unexpected " \o (IF i = 1 THEN "k1" ELSE "k2"), calls + 2>>
           [] OTHER -> Report(keys, i + 1, calls + Calls(a))

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Report(program, 1, 0) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
\* Every keyword equal to a name makes the keywords invalid.
AllEqualInvalid == outcome # Pending /\ (\A i \in 1..Len(program) : program[i] \in {"key", "reverse"}) =>
                   outcome[1] = "invalid"
\* No key's __eq__ is called more often than there are names.
Bounded == outcome # Pending => outcome[2] <= 2 * Len(program)
=============================================================================
