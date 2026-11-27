------------------------- MODULE AnnotatedTargets -------------------------
(***************************************************************************)
(* Where an annotated assignment's target error is located, as PLS-315     *)
(* 14.4 states it, for statements  <target>: int  and  <target>:  whose    *)
(* target begins at column 1: a name; an unparenthesized tuple whose first *)
(* item is a name, a parenthesized name, a parenthesized tuple or a        *)
(* starred name; a parenthesized tuple; a list; a starred name alone; or a *)
(* call. A tuple is located at itself when parenthesized, else at its      *)
(* first item, that item's own parentheses excluded; a starred target      *)
(* alone is invalid syntax at the colon. Without an annotation every       *)
(* statement is invalid syntax: a name's after the colon, any other at it. *)
(* The outcome is the message, column and end column, or "ok".             *)
(***************************************************************************)
EXTENDS Naturals

Targets == {"a", "a, b", "(a), b", "(a, b), c", "*a, b", "(a, b)", "[a, b]", "*a", "f()"}
Programs == [target : Targets, annotation : {"int", "none"}]

\* The column of the colon after target t.
Colon(t) == CASE t = "a" -> 2 [] t = "*a" -> 3 [] t = "f()" -> 4 [] t = "a, b" -> 5
                [] t = "*a, b" -> 6 [] t \in {"(a), b", "(a, b)", "[a, b]"} -> 7 [] t = "(a, b), c" -> 10

VARIABLES program, outcome
vars == <<program, outcome>>

Tuple == "only single target (not tuple) can be annotated"
Located(t) == CASE t = "a" -> <<"ok", 0, 0>>
                [] t = "a, b" -> <<Tuple, 1, 2>>
                [] t = "(a), b" -> <<Tuple, 2, 3>>
                [] t = "(a, b), c" -> <<Tuple, 1, 7>>
                [] t = "*a, b" -> <<Tuple, 1, 3>>
                [] t = "(a, b)" -> <<Tuple, 1, 7>>
                [] t = "[a, b]" -> <<"only single target (not list) can be annotated", 1, 7>>
                [] t = "*a" -> <<"invalid syntax", 3, 4>>
                [] t = "f()" -> <<"illegal target for annotation", 1, 4>>
Reported(p) == IF p.annotation = "int" THEN Located(p.target)
               ELSE IF p.target = "a" THEN <<"invalid syntax", 3, 4>>
               ELSE <<"invalid syntax", Colon(p.target), Colon(p.target) + 1>>

Init == program \in Programs /\ outcome = <<"pending", 0, 0>>
Execute == outcome[1] = "pending" /\ outcome' = Reported(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome[1] # "pending"

\* An error lies within the target or at the colon after it, and is never empty.
WithinStatement == Done /\ outcome[1] # "ok" => 1 <= outcome[2] /\ outcome[2] < outcome[3]

\* An unparenthesized tuple's error ends before its first comma.
FirstItem == Done /\ program.annotation = "int" /\ program.target \in {"a, b", "(a), b", "(a, b), c", "*a, b"} => outcome[3] <= 8

\* A statement without an annotation is invalid syntax at or after its colon.
AnnotationNeeded == Done /\ program.annotation = "none" => outcome[1] = "invalid syntax" /\ outcome[2] >= Colon(program.target)
=============================================================================
