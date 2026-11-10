----------------------- MODULE DelegateThrowArguments -----------------------
(***************************************************************************)
(* throw() into a generator suspended in a yield from, as PLS-315 13.16.3  *)
(* and 27.2.2 specify it: the arguments pass on as given. A generator      *)
(* delegate checks them where the throw raises, an iterator's throw takes  *)
(* them unchecked, and a delegate with no throw, or a GeneratorExit        *)
(* closing the delegate, has the delegator check them. An exception from   *)
(* the delegate raises at the yield from, where the delegator may handle   *)
(* it; one from the delegator's own check leaves it suspended.             *)
(*                                                                         *)
(* A program runs                                                          *)
(*                                                                         *)
(*     def g():                                                            *)
(*         yield from it                                                   *)
(*                                                                         *)
(* or the same yield from inside try: ... except Exception as e: yield     *)
(* "caught " + type(e).__name__, after one next(), then throw()s           *)
(* KeyError("k"), 1, or (GeneratorExit, 1, 2), whose third argument is no  *)
(* traceback. it is a generator suspended at a yield, an iterator whose    *)
(* throw returns "thrown" and whose close returns, or one with neither.    *)
(* The outcome is the throw()'s result or exception, and whether g is      *)
(* still suspended.                                                        *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [delegate : {"generator", "throws", "bare"},
             args : {"instance", "invalid", "exit"}, handles : BOOLEAN]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == [result |-> "pending", suspended |-> TRUE]

\* The exception the delegate raises at the yield from, or "" for none.
Raised(p) ==
    CASE p.args = "exit" -> ""
      [] p.delegate = "throws" -> ""
      [] p.delegate = "bare" /\ p.args = "invalid" -> ""
      [] p.args = "instance" -> "KeyError"
      [] OTHER -> "TypeError"

Run(p) ==
    LET e == Raised(p)
    IN CASE e # "" /\ p.handles -> [result |-> "'caught " \o e \o "'", suspended |-> TRUE]
         [] e # "" -> [result |-> e, suspended |-> FALSE]
         \* The iterator's throw took the arguments as given.
         [] p.delegate = "throws" /\ p.args # "exit" -> [result |-> "'thrown'", suspended |-> TRUE]
         \* The delegator's own check failed: it did not resume.
         [] OTHER -> [result |-> "TypeError", suspended |-> TRUE]

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A TypeError the delegator raises itself never ends it.
OwnCheckSuspends == Done /\ program.args = "exit" => outcome.suspended
=============================================================================
