------------------------- MODULE YieldFromIterator -------------------------
(***************************************************************************)
(* yield from delegating to an iterator that is not a generator, as        *)
(* PLS-315 13.16.3 specifies it: send() of a value other than None calls   *)
(* its send method, throw() its throw method, and close() its close        *)
(* method before GeneratorExit ends the delegator. A missing method makes  *)
(* send fail and throw raise the exception in the delegator; for close, an *)
(* error getting the method (other than AttributeError) is unraisable, so  *)
(* the delegator still closes, while an error from calling it propagates; *)
(* for throw, such an error propagates before the delegator resumes, which *)
(* stays suspended.                                                        *)
(*                                                                         *)
(* A program runs                                                          *)
(*                                                                         *)
(*     def g():                                                            *)
(*         yield from it                                                   *)
(*                                                                         *)
(* after one next(), then one step: close(), throw(KeyError), or send(1).  *)
(* Each of it's send, throw and close is defined (send and throw return 7, *)
(* close returns None), raises ValueError when called, is missing, or is   *)
(* broken: looking it up raises ZeroDivisionError. The outcome is the      *)
(* step's result or exception, the methods it called, and whether g        *)
(* finished.                                                               *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Kinds == {"defined", "raises", "missing", "broken"}
Programs == [kind : Kinds, step : {"close", "throw", "send"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == [result |-> "pending", called |-> "", finished |-> FALSE]

Method(step) == CASE step = "close" -> "close" [] step = "throw" -> "throw" [] OTHER -> "send"

Run(p) ==
    LET m == Method(p.step)
        called == IF p.kind \in {"defined", "raises"} THEN m ELSE ""
    IN CASE p.kind = "defined" /\ p.step = "close" -> [result |-> "None", called |-> called, finished |-> TRUE]
         [] p.kind = "defined" -> [result |-> "7", called |-> called, finished |-> FALSE]
         \* The method's own exception propagates, and ends the delegator.
         [] p.kind = "raises" -> [result |-> "ValueError", called |-> called, finished |-> TRUE]
         \* An unraisable lookup error: close() completes as if there were no close.
         [] p.step = "close" -> [result |-> "None", called |-> called, finished |-> TRUE]
         [] p.kind = "broken" -> [result |-> "ZeroDivisionError", called |-> called, finished |-> p.step = "send"]
         \* No throw: the exception is raised in the delegator.
         [] p.step = "throw" -> [result |-> "KeyError", called |-> called, finished |-> TRUE]
         [] OTHER -> [result |-> "AttributeError", called |-> called, finished |-> TRUE]

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* close() closes the delegator unless the subiterator's close itself raises.
CloseCloses == Done /\ program.step = "close" /\ program.kind # "raises" =>
    outcome.result = "None" /\ outcome.finished
=============================================================================
