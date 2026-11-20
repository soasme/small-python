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
(* KeyError("k"), 1, (GeneratorExit, 1, 2), whose third argument is no     *)
(* traceback, as is (KeyError, None, 2)'s, (KeyError("k"), 1), an instance *)
(* given a value, (Made, 3), Made's Python __init__ making the exception, or *)
(* Exit, a GeneratorExit class whose Python __init__ notes whether the     *)
(* delegate is closed yet, or (Exit, (4, 5)), made of those arguments,     *)
(* or GeneratorExit itself, made with no Python code. it is a generator   *)
(* suspended at a yield, or in a yield from of                             *)
(* one (a chain, both closed before Exit is made), a generator closed      *)
(* before the throw (ended), which checks and raises as one at a yield     *)
(* does, an iterator whose throw                                           *)
(* returns "thrown" and whose close returns, one whose Python __getattr__  *)
(* gives those methods (asked), or one whose __getattr__ raises            *)
(* ZeroDivisionError (broken), or one with neither; or a generator that    *)
(* yields on GeneratorExit (stubborn), or an iterator whose throw returns  *)
(* "thrown" and whose close raises ValueError (failing): a close that      *)
(* fails raises its error at the yield from instead. A throw's failed      *)
(* lookup leaves g suspended; a close's is unraisable, as if absent. The   *)
(* outcome is the throw()'s result or exception, and whether g is still    *)
(* suspended.                                                              *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [delegate : {"generator", "chain", "ended", "throws", "asked", "broken", "bare", "stubborn", "failing"},
             args : {"instance", "invalid", "exit", "made", "exit_made", "exit_value", "exit_class", "instance_value", "traceback"},
             handles : BOOLEAN]

\* The arguments every generator refuses before calling any class.
Refused == {"invalid", "instance_value", "traceback"}
Exits == {"exit", "exit_made", "exit_value", "exit_class"}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == [result |-> "pending", suspended |-> TRUE]

\* The exception the delegate raises at the yield from, or "" for none.
Raised(p) ==
    CASE p.delegate = "stubborn" /\ p.args \in Exits -> "RuntimeError"
      [] p.delegate = "failing" /\ p.args \in Exits -> "ValueError"
      [] p.args \in Exits -> ""
      [] p.delegate \in {"throws", "asked", "failing"} -> ""
      [] p.delegate \in {"bare", "broken"} /\ p.args \in Refused -> ""
      [] p.args = "instance" -> "KeyError"
      [] p.args = "made" -> "Made"
      [] OTHER -> "TypeError"

Run(p) ==
    LET e == Raised(p)
    IN CASE p.delegate = "broken" /\ p.args \in {"instance", "made"} \cup Refused ->
                \* Looking up throw failed before g resumed.
                [result |-> "ZeroDivisionError", suspended |-> TRUE]
         [] e # "" /\ p.handles -> [result |-> "'caught " \o e \o "'", suspended |-> TRUE]
         [] e # "" -> [result |-> e, suspended |-> FALSE]
         \* A GeneratorExit class is made once the delegate closed, and ends g.
         [] p.args = "exit_made" -> [result |-> "Exit after close", suspended |-> FALSE]
         [] p.args = "exit_value" -> [result |-> "Exit (4, 5) after close", suspended |-> FALSE]
         [] p.args = "exit_class" -> [result |-> "GeneratorExit after close", suspended |-> FALSE]
         \* The iterator's throw took the arguments as given.
         [] p.delegate \in {"throws", "asked", "failing"} /\ p.args \notin Exits -> [result |-> "'thrown'", suspended |-> TRUE]
         \* The delegator's own check failed: it did not resume.
         [] OTHER -> [result |-> "TypeError", suspended |-> TRUE]

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A TypeError the delegator raises itself never ends it.
OwnCheckSuspends == Done /\ program.args = "exit" /\ program.delegate \notin {"stubborn", "failing"} => outcome.suspended
=============================================================================
