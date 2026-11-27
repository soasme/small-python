------------------------- MODULE FutureErrorStage -------------------------
(***************************************************************************)
(* Which error a module reports when a future statement's error (PLS-315   *)
(* 14.13) meets an error of Clause 8. A module is                          *)
(*                                                                         *)
(*     <first line>                                                        *)
(*     [a function whose global declaration follows an assignment]         *)
(*     [from __future__ import annotations]                                *)
(*     [the function again]                                                *)
(*                                                                         *)
(* whose first line is a future statement naming an undefined feature, a   *)
(* future statement after an assignment on that line, or an assignment;    *)
(* the future statement on its own line follows only the last. The scope   *)
(* error is in the middle, at the end, or absent. The outcome names the    *)
(* error reported, or "ok".                                                *)
(***************************************************************************)
EXTENDS Naturals

Programs == [future : {"none", "undefined", "sameline", "laterline"}, scope : {"none", "middle", "end"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Reported(p) == CASE p.future = "undefined" -> "feature"
                 [] p.future = "sameline" -> "misplaced"
                 [] p.future = "laterline" /\ p.scope = "middle" -> "scope"
                 [] p.future = "laterline" -> "misplaced"
                 [] p.scope # "none" -> "scope"
                 [] OTHER -> "ok"

Init == program \in Programs /\ outcome = "pending"
Execute == outcome = "pending" /\ outcome' = Reported(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # "pending"

\* The future pass's errors come before every error of Clause 8.
FuturePassFirst == Done /\ program.future \in {"undefined", "sameline"} => outcome # "scope"

\* A future statement on a later line is one of Clause 8's, in source order.
LaterInOrder == Done /\ program.future = "laterline" =>
                    outcome = IF program.scope = "middle" THEN "scope" ELSE "misplaced"
=============================================================================
