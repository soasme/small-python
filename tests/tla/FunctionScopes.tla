-------------------------- MODULE FunctionScopes --------------------------
(* PLS-315 14.9, 16.1, 27.2, 27.4, 27.5: a nested definition's body
 * belongs to that function, whereas its defaults execute in the outer
 * function. A yield in an unreachable branch, or an assertion removed
 * by optimization, still makes a generator. *)
EXTENDS Naturals

Programs == [asynchronous : BOOLEAN, ownYield : BOOLEAN,
             nestedYield : BOOLEAN, defaultYield : BOOLEAN,
             valuedReturn : BOOLEAN, optimized : BOOLEAN]
Kind(p) ==
    LET generator == p.ownYield \/ p.defaultYield
    IN IF p.asynchronous /\ generator /\ p.valuedReturn THEN "SyntaxError"
       ELSE IF p.asynchronous /\ generator THEN "async_generator"
       ELSE IF p.asynchronous THEN "coroutine"
       ELSE IF generator THEN "generator"
       ELSE "plain"

VARIABLES program, outcome
vars == <<program, outcome>>
Init == program \in Programs /\ outcome = "pending"
Compile == outcome = "pending" /\ outcome' = Kind(program) /\ UNCHANGED program
Spec == Init /\ [][Compile]_vars
LexicalScope == outcome = "pending" \/ outcome = Kind(program)
=============================================================================
