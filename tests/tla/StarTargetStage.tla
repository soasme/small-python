------------------------- MODULE StarTargetStage -------------------------
(***************************************************************************)
(* Which error a module reports when an assignment's starred-target error  *)
(* (PLS-315 14.2) meets others, as 14.2 orders them: a target that cannot  *)
(* be assigned, a parse error, first, then an error of Clause 8, then the  *)
(* compiler's errors in source order, an assignment's value before its     *)
(* targets. A module is                                                    *)
(*                                                                         *)
(*     [return]                                                            *)
(*     <target> = <1 or (yield)>                                           *)
(*     [return]                                                            *)
(*     [a function whose global declaration follows an assignment]         *)
(*                                                                         *)
(* whose target is a name, a starred name alone, two starred names in a    *)
(* tuple, or a starred call. The outcome names the error reported, or      *)
(* "ok".                                                                   *)
(***************************************************************************)
EXTENDS Naturals

Programs == [target : {"name", "alone", "two", "call"}, other : {"none", "scope", "before", "after", "value"}]

VARIABLES program, outcome
vars == <<program, outcome>>

\* The target's own error, the compiler's, or none.
Starred(p) == CASE p.target = "alone" -> "alone" [] p.target = "two" -> "two" [] OTHER -> "none"

Reported(p) == CASE p.target = "call" -> "call"
                 [] p.other = "scope" -> "scope"
                 [] p.other \in {"before", "value"} -> IF p.other = "before" THEN "return" ELSE "yield"
                 [] Starred(p) # "none" -> Starred(p)
                 [] p.other = "after" -> "return"
                 [] OTHER -> "ok"

Init == program \in Programs /\ outcome = "pending"
Execute == outcome = "pending" /\ outcome' = Reported(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # "pending"

\* A target that cannot be assigned comes first, then an error of Clause 8.
ParserFirst == Done /\ program.target = "call" => outcome = "call"

\* A starred-target error follows the compiler's earlier errors and the value's.
StarredInOrder == Done /\ Starred(program) # "none" /\ program.other \in {"none", "after"} => outcome = Starred(program)
=============================================================================
