------------------------- MODULE AssignmentMeant -------------------------
(***************************************************************************)
(* Which error an assignment with a target that cannot be assigned gets,   *)
(* as PLS-315 14.2 states it. The statement begins with a call, a genexp,  *)
(* a genexp in redundant parentheses, or a tuple of a name and a call; or  *)
(* it is a name assigned a genexp and a name, assigned 1 in turn. A name,  *)
(* '=' and an operand that no '=' follows is "Maybe you meant '==' or      *)
(* ':='"; else a beginning that is no list, tuple or genexp, then '=' and  *)
(* an operand that no '=' follows, is "here. Maybe you meant '=='"; else   *)
(* the first invalid part is the error.                                    *)
(***************************************************************************)
EXTENDS Naturals

Targets == {"call", "genexp", "grouped genexp", "tuple", "chained"}

VARIABLES program, outcome
vars == <<program, outcome>>

Reported(t) == CASE t = "call" -> "cannot assign to function call here. Maybe you meant '==' instead of '='?"
                 [] t = "genexp" -> "cannot assign to generator expression"
                 [] t = "grouped genexp" -> "cannot assign to generator expression here. Maybe you meant '==' instead of '='?"
                 [] t = "tuple" -> "cannot assign to function call"
                 [] t = "chained" -> "invalid syntax. Maybe you meant '==' or ':=' instead of '='?"

Init == program \in Targets /\ outcome = "pending"
Execute == outcome = "pending" /\ outcome' = Reported(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # "pending"

\* A beginning that is a tuple or genexp itself gets no suggestion.
NoSuggestion == Done /\ program \in {"genexp", "tuple"} => outcome \in {"cannot assign to generator expression", "cannot assign to function call"}

\* A name's suggestion precedes the generator target's own error.
NameFirst == Done /\ program = "chained" => outcome = "invalid syntax. Maybe you meant '==' or ':=' instead of '='?"
=============================================================================
