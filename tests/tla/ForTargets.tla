---------------------------- MODULE ForTargets ----------------------------
(***************************************************************************)
(* A for target's error, as PLS-315 15.3 and 13.2.6 state it, in a for     *)
(* statement or a list comprehension's for clause. A target that is not    *)
(* star_targets before 'in' is read again as star_expressions, which take  *)
(* in the 'in': a lambda or a conditional expression is then the invalid   *)
(* part; a call is, as the left operand of a comparison begun by 'in'; a   *)
(* comparison begun by another operator has no invalid part, and the error *)
(* is invalid syntax. A comprehension first reports operands of a bitwise  *)
(* or, separated by commas, that 'in' does not follow, so a name and a     *)
(* lambda, a conditional expression or a comparison are "'in' expected"    *)
(* there. The outcome is the error's message.                              *)
(***************************************************************************)
EXTENDS Naturals

Targets == {"lambda", "conditional", "call", "comparison", "name and lambda"}
Places == {"statement", "comprehension"}

VARIABLES program, outcome
vars == <<program, outcome>>

Message(p) ==
    CASE p.target = "call" -> "cannot assign to function call"
      [] p.place = "comprehension" /\ p.target # "lambda" -> "'in' expected after for-loop variables"
      [] p.target = "comparison" -> "invalid syntax"
      [] p.target \in {"lambda", "name and lambda"} -> "cannot assign to lambda"
      [] p.target = "conditional" -> "cannot assign to conditional expression"

Init == program \in [target : Targets, place : Places] /\ outcome = "pending"
Execute == outcome = "pending" /\ outcome' = Message(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # "pending"

\* A target whose star_expressions reading has an invalid part is the
\* same error in both places, unless the comprehension's operands come first.
SamePart == Done /\ program.target \in {"lambda", "call"} =>
                outcome = Message([program EXCEPT !.place = IF program.place = "statement" THEN "comprehension" ELSE "statement"])

\* Only a comprehension reports "'in' expected".
InExpected == Done /\ outcome = "'in' expected after for-loop variables" => program.place = "comprehension"
=============================================================================
