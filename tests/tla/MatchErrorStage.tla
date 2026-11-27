-------------------------- MODULE MatchErrorStage --------------------------
(***************************************************************************)
(* Which error a program reports when a case pattern's early error         *)
(* (PLS-315 15.6.1) meets others, as 15.6.1 orders them: an error of       *)
(* Clause 8 anywhere comes first; the pattern errors follow it with the    *)
(* other errors found after Clause 8's, in source order, a case's pattern  *)
(* before its guard and block. A program is a module holding               *)
(*                                                                         *)
(*     match v:                                                            *)
(*         case <pattern> [if (yield)]:                                    *)
(*             <pass or return 1>                                          *)
(*         case 2: pass                                                    *)
(*                                                                         *)
(* whose pattern is [a], [a, a] (a repeated name), {1: a, 1: b} (a         *)
(* repeated key) or x (an irrefutable capture, allowed only when guarded); *)
(* with a function whose global declaration follows an assignment, a       *)
(* Clause 8 error, before or after the match, or none; and with a module   *)
(* level return before the match, a yield in the guard, a return in the    *)
(* case's block, or none. The outcome names the error reported, or "ok".   *)
(***************************************************************************)
EXTENDS Naturals

Programs == [pattern : {"ok", "names", "keys", "capture"}, scope : {"none", "before", "after"},
             compile : {"none", "earlier", "guard", "body"}]

VARIABLES program, outcome
vars == <<program, outcome>>

\* The case pattern's own error: a capture is irrefutable, which a guard allows.
PatternError(p) == CASE p.pattern = "names" -> "names" [] p.pattern = "keys" -> "keys"
                     [] p.pattern = "capture" /\ p.compile # "guard" -> "capture"
                     [] OTHER -> "none"

Reported(p) == CASE p.scope # "none" -> "scope"
                 [] p.compile = "earlier" -> "return"
                 [] PatternError(p) # "none" -> PatternError(p)
                 [] p.compile = "guard" -> "yield"
                 [] p.compile = "body" -> "return"
                 [] OTHER -> "ok"

Init == program \in Programs /\ outcome = "pending"
Execute == outcome = "pending" /\ outcome' = Reported(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # "pending"

\* An error of Clause 8, before or after the match, comes first.
ScopeFirst == Done /\ program.scope # "none" => outcome = "scope"

\* Without one, a case's pattern error comes before its guard's and block's.
PatternBeforeItsCase == Done /\ program.scope = "none" /\ program.compile \in {"guard", "body"} /\ PatternError(program) # "none" =>
                            outcome = PatternError(program)

\* An error of the compiler earlier in the source comes before the pattern's.
EarlierFirst == Done /\ program.scope = "none" /\ program.compile = "earlier" => outcome = "return"
=============================================================================
