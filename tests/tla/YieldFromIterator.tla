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
(* stays suspended. next() calls its __next__, whose StopIteration ends    *)
(* the yield from with the exception's value, also when a loop resumes g   *)
(* through an outer generator's yield from; a throw into that outer        *)
(* generator reaches the iterator as a throw into g does.                  *)
(*                                                                         *)
(* A program runs                                                          *)
(*                                                                         *)
(*     def g():                                                            *)
(*         return (yield from it)                                          *)
(*                                                                         *)
(* after one next(), then one step: close(), throw(KeyError()) or         *)
(* throw(KeyError), the class made at a delegator's raise but given as    *)
(* it is to it's throw (called "throwC"), send(1),                         *)
(* next(), list() of an outer generator, yield ("ret", (yield from g)), or *)
(* throw(KeyError()) into one, return (yield from g), started instead of   *)
(* g, list() of g itself, or dropping g's last reference, which closes    *)
(* it, its finally clause showing it finished, an error unraisable. g's    *)
(* body may first run a yield statement, which one                         *)
(* more next() passes.                                                     *)
(* where it's __next__ returns 1, then raises StopIteration(8).            *)
(* Each of it's send, throw and close is defined (send and throw return 7, *)
(* close returns None), so held by it as its own attributes, taking no     *)
(* self ("own"), raises ValueError when called, is missing, or is broken:  *)
(* looking it up raises ZeroDivisionError. Or it is a map whose            *)
(* Python function acts as that __next__, and has none of the three        *)
(* methods, or a builtin list iterator of the one item 1, which ends with  *)
(* StopIteration(None) and has no methods. The outcome is the              *)
(* step's result or exception, the methods it called, and whether g        *)
(* finished.                                                               *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Kinds == {"defined", "own", "raises", "missing", "broken", "map", "builtin"}
Programs == [kind : Kinds, step : {"close", "throw", "throwclass", "send", "next", "loop", "nested", "consume", "drop"}, first : BOOLEAN]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == [result |-> "pending", called |-> "", finished |-> FALSE]

Method(step) == CASE step \in {"close", "drop"} -> "close" [] step = "throwclass" -> "throwC" [] step \in {"throw", "nested"} -> "throw" [] step \in {"next", "loop", "consume"} -> "next" [] OTHER -> "send"

Run(p) ==
    LET m == Method(p.step)
        called == IF p.kind = "builtin" THEN "" ELSE IF p.kind \in {"defined", "own", "raises"} \/ m = "next" THEN m ELSE ""
    IN CASE p.kind = "builtin" /\ p.step = "next" -> [result |-> "StopIteration None", called |-> called, finished |-> TRUE]
         [] p.kind = "builtin" /\ p.step = "loop" -> [result |-> "[('ret', None)]", called |-> called, finished |-> TRUE]
         [] p.step = "next" -> [result |-> "StopIteration 8", called |-> called, finished |-> TRUE]
         [] p.step = "loop" -> [result |-> "[('ret', 8)]", called |-> called, finished |-> TRUE]
         [] p.step = "consume" -> [result |-> "[]", called |-> called, finished |-> TRUE]
         \* The close a dropped g gets reports its errors as unraisable.
         [] p.step = "drop" -> [result |-> "dropped", called |-> called, finished |-> TRUE]
         [] p.kind \in {"defined", "own"} /\ p.step = "close" -> [result |-> "None", called |-> called, finished |-> TRUE]
         [] p.kind \in {"defined", "own"} -> [result |-> "7", called |-> called, finished |-> FALSE]
         \* The method's own exception propagates, and ends the delegator.
         [] p.kind = "raises" -> [result |-> "ValueError", called |-> called, finished |-> TRUE]
         \* An unraisable lookup error: close() completes as if there were no close.
         [] p.step = "close" -> [result |-> "None", called |-> called, finished |-> TRUE]
         [] p.kind = "broken" -> [result |-> "ZeroDivisionError", called |-> called, finished |-> p.step = "send"]
         \* No throw: the exception is raised in the delegator.
         [] p.step \in {"throw", "throwclass", "nested"} -> [result |-> "KeyError", called |-> called, finished |-> TRUE]
         [] OTHER -> [result |-> "AttributeError", called |-> called, finished |-> TRUE]

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* close() closes the delegator unless the subiterator's close itself raises.
CloseCloses == Done /\ program.step = "close" /\ program.kind # "raises" =>
    outcome.result = "None" /\ outcome.finished

\* A loop or consumer resuming g in its yield from takes the iterator's
\* items, whether or not a yield statement came first.
ConsumeEnds == Done /\ program.step = "consume" => outcome.result = "[]" /\ outcome.finished

\* A dropped g is closed, its iterator's close called when it has one.
DropCloses == Done /\ program.step = "drop" =>
    outcome.finished /\ (outcome.called = "close" <=> program.kind \in {"defined", "own", "raises"})

\* A thrown class reaches the iterator's throw as given, not made.
ThrowClassRaw == Done /\ program.step = "throwclass" /\ program.kind \in {"defined", "own", "raises"} => outcome.called = "throwC"
=============================================================================
