----------------------------- MODULE AsyncWith -----------------------------
(***************************************************************************)
(* The async with statement, as The Python Language Reference specifies it *)
(* (reference/compound_stmts.html#the-async-with-statement and reference/  *)
(* datamodel.html#asynchronous-context-managers): it awaits __aenter__()   *)
(* before the body and __aexit__() after it, however the body ends, with   *)
(* the exception or three Nones; values the awaited methods pass out reach *)
(* the coroutine's driver; a true result suppresses the exception, an      *)
(* exception from __aexit__ replaces the body's, and if __aenter__ raises  *)
(* __aexit__ is not called; a manager without __aenter__ or __aexit__      *)
(* raises TypeError (suggesting `with` for an ordinary context manager, as *)
(* `with` suggests `async with` for an asynchronous one); and an           *)
(* __aenter__ that returns something not awaitable raises TypeError.       *)
(*                                                                         *)
(* A program drives a coroutine running `async with M(): BODY`, where M's  *)
(* awaited methods each pass out "tick" and log their names; __aenter__    *)
(* succeeds or raises ValueError; __aexit__ returns False, returns True,   *)
(* or raises RuntimeError; and BODY completes or raises KeyError. A        *)
(* protocol program uses an ordinary context manager with async with, an   *)
(* asynchronous one with with, a manager without __aexit__, or one whose   *)
(* __aenter__ returns 5. The outcome is the log, the number of values      *)
(* passed out, and "done" or the exception.                                *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [part : {"manager"}, enter : {"ok", "raise"}, exit : {"false", "true", "raise"}, body : {"normal", "raise"}]
            \cup [part : {"protocol"}, case : {"sync", "async", "noaexit", "badaenter"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Manager(p) ==
    IF p.enter = "raise" THEN "aenter 1 ValueError"
    ELSE LET raised == p.body = "raise"
             final == CASE p.exit = "raise" -> "RuntimeError"
                        [] raised /\ p.exit = "false" -> "KeyError"
                        [] OTHER -> "done"
         IN "aenter body aexit:" \o (IF raised THEN "KeyError" ELSE "None") \o " 2 " \o final

Run(p) == IF p.part = "manager" THEN Manager(p)
          ELSE CASE p.case = "sync" -> "0 TypeError: use with"
                 [] p.case = "async" -> "0 TypeError: use async with"
                 [] OTHER -> "0 TypeError"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* __aexit__ is awaited exactly when __aenter__ returned.
ExitAfterEnter == Done /\ program.part = "manager" => (program.enter = "ok" <=> outcome # "aenter 1 ValueError")
=============================================================================
