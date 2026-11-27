------------------------- MODULE WithStarTargets -------------------------
(***************************************************************************)
(* The error of a with item's starred target, as PLS-315 15.5 states it,   *)
(* for statements  with a as *<operand>: pass  whose star is at column 11: *)
(* a name, an attribute, a list of names or a call's attribute, which are  *)
(* targets; a call and a number, primaries that are not; a sum of names,   *)
(* whose longest primary is its first name; and a negation, an await and a *)
(* lambda, which begin no primary. The outcome is the message, column and  *)
(* end column; the compiler's starred-target error is kept without either. *)
(***************************************************************************)
EXTENDS Naturals

Operands == {"a", "a.b", "[a, b]", "f()", "1", "f().x", "a + b", "-a", "await a", "lambda: 0"}

VARIABLES program, outcome
vars == <<program, outcome>>

Starred == <<"starred assignment target must be in a list or tuple", 0, 0>>
Invalid(at, end) == <<"invalid syntax", at, end>>
Reported(o) == CASE o \in {"a", "a.b", "[a, b]", "f().x"} -> Starred
                 [] o = "f()" -> Invalid(15, 16)
                 [] o = "1" -> Invalid(13, 14)
                 [] o = "a + b" -> Invalid(14, 15)
                 [] o = "-a" -> Invalid(12, 13)
                 [] o = "await a" -> Invalid(12, 17)
                 [] o = "lambda: 0" -> Invalid(12, 18)

Init == program \in Operands /\ outcome = <<"pending", 0, 0>>
Execute == outcome[1] = "pending" /\ outcome' = Reported(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome[1] # "pending"

\* An invalid syntax lies on one token at or after the operand's first.
OneToken == Done /\ outcome[1] = "invalid syntax" => 12 <= outcome[2] /\ outcome[2] < outcome[3]

\* What cannot begin a primary is reported at the operand's first token.
NoPrimary == Done /\ program \in {"-a", "await a", "lambda: 0"} => outcome[2] = 12
=============================================================================
