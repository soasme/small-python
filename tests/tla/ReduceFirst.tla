------------------------------ MODULE ReduceFirst ------------------------------
(***************************************************************************)
(* The first object reduction of a program, as PLS-315 20.1.3 specifies  *)
(* it, gives what any later one gives: a program makes two reductions,     *)
(* each __reduce_ex__(2), __reduce__() or __getstate__() of an instance    *)
(* whose Python __getstate__ returns its state or raises LookupError. The  *)
(* outcome of each is the reconstructor's name and the state, or the       *)
(* error; neither depends on which came first.                             *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Calls == {"reduce_ex", "reduce", "getstate"}
Programs == [first : Calls, second : Calls, fails : BOOLEAN]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Result(call, fails) == IF fails THEN "LookupError"
                       ELSE CASE call = "reduce_ex" -> "__newobj__ state"
                              [] call = "reduce" -> "_reconstructor state"
                              [] call = "getstate" -> "state"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ UNCHANGED program /\
           outcome' = Result(program.first, program.fails) \o " / " \o Result(program.second, program.fails)
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
\* The same reduction gives the same outcome first and second.
FirstAsLater == outcome # Pending /\ program.first = program.second =>
                outcome = Result(program.first, program.fails) \o " / " \o Result(program.first, program.fails)
=============================================================================
