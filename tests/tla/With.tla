-------------------------------- MODULE With --------------------------------
(***************************************************************************)
(* The with statement and context managers, as The Python Language         *)
(* Reference specifies them (reference/compound_stmts.html#the-with-       *)
(* statement and reference/datamodel.html#with-statement-context-          *)
(* managers): __enter__ and __exit__ are both looked up before __enter__   *)
(* is called, and a manager lacking either raises TypeError; if __enter__  *)
(* raises, __exit__ is not called; otherwise __exit__ is called however    *)
(* the body ends, with the exception's type, value, and traceback or with  *)
(* three Nones; a true result suppresses the exception, while the result   *)
(* is ignored after a normal exit or a return; an exception from __exit__  *)
(* replaces the body's; and several managers nest, so a later __enter__    *)
(* that raises reaches the earlier managers' __exit__.                     *)
(*                                                                         *)
(* A single program runs `with M(): BODY` in a function, where M's         *)
(* __enter__ succeeds, raises ValueError, or is missing; its __exit__      *)
(* returns False, returns True, raises RuntimeError, or is missing; and    *)
(* BODY completes, raises KeyError, or returns. A nested program runs      *)
(* `with M(), N(): pass` where N's __enter__ raises ValueError and M's     *)
(* __exit__ returns False or True. Every method logs a word; the outcome   *)
(* is the log followed by "done", "returned", or the exception's name.     *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [part : {"single"}, enter : {"ok", "raise", "missing"}, exit : {"false", "true", "raise", "missing"},
             body : {"normal", "raise", "return"}]
            \cup [part : {"nested"}, exit : {"false", "true"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Single(p) ==
    IF p.enter = "missing" \/ p.exit = "missing" THEN "TypeError"
    ELSE IF p.enter = "raise" THEN "enter ValueError"
    ELSE LET raised == p.body = "raise"
             start == "enter body exit:" \o (IF raised THEN "KeyError" ELSE "None") \o " "
             final == CASE p.exit = "raise" -> "RuntimeError"
                        [] raised /\ p.exit = "true" -> "done"
                        [] raised -> "KeyError"
                        [] p.body = "return" -> "returned"
                        [] OTHER -> "done"
         IN start \o final

Nested(p) == "enterM enterN exitM:ValueError " \o (IF p.exit = "true" THEN "done" ELSE "ValueError")

Run(p) == IF p.part = "single" THEN Single(p) ELSE Nested(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* __exit__ runs exactly when __enter__ returned.
ExitAfterEnter == Done /\ program.part = "single" /\ program.enter = "ok" /\ program.exit # "missing" =>
    outcome # "TypeError" /\ outcome # "enter ValueError"
=============================================================================
