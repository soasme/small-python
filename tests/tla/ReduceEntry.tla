------------------------------ MODULE ReduceEntry ------------------------------
(***************************************************************************)
(* The builtins lookup of an intrinsic iterator's __reduce__, as PLS-315   *)
(* 27.1.1 specifies it: the entry, iter or reversed, is found by key       *)
(* equality as LoadGlobal (9.3.2) finds a name. A program replaces the     *)
(* builtins entry by a key of the same hash whose __eq__ first runs an     *)
(* effect on the iterator it, then answers                                 *)
(*                                                                         *)
(*     name      whether the other key equals the entry's name             *)
(*     one       the int 1, true                                           *)
(*     declined  NotImplemented: str's reflected __eq__ declines too       *)
(*     raise     raises LookupError                                        *)
(*                                                                         *)
(* where it iterates over [1, 2] (a list), {1: 2, 3: 4} (a dict) or        *)
(* range(0, 4) (a range), or is reversed([1, 2]); the effect is none, next *)
(* (advance it once) or drain (exhaust it). The outcome is what            *)
(* it.__reduce__() returns, the iterator written by the items it would     *)
(* still give and its index, or the exception.                             *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Kinds == {"list", "dict", "range", "reversed"}
Effects == {"none", "next", "drain"}
Answers == {"name", "one", "declined", "raise"}
Programs == [kind : Kinds, effect : Effects, answer : Answers]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* How many items the effect takes from it.
Taken(e) == CASE e = "none" -> 0 [] e = "next" -> 1 [] e = "drain" -> 2

\* The dict iterator's items, and the range iterator's range, are read
\* before the lookup; the list and reverse iterators' state after it.
Reduced(p) ==
    CASE p.kind = "dict" -> "(iter, ([1, 3],))"
      [] p.kind = "range" -> "(iter, (range(0, 4),), None)"
      [] p.kind = "list" -> IF Taken(p.effect) = 2 THEN "(iter, ([],))"
                            ELSE IF Taken(p.effect) = 1 THEN "(iter, ([1, 2],), 1)" ELSE "(iter, ([1, 2],), 0)"
      [] p.kind = "reversed" -> IF Taken(p.effect) = 2 THEN "(reversed, ([],))"
                                ELSE IF Taken(p.effect) = 1 THEN "(reversed, ([1, 2],), 0)" ELSE "(reversed, ([1, 2],), 1)"

Run(p) == CASE p.answer = "raise" -> "LookupError"
            [] p.answer = "declined" -> "AttributeError"
            [] OTHER -> Reduced(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* What the dict and range iterators read first is not changed by __eq__.
ReadFirst == Done /\ program.kind \in {"dict", "range"} /\ program.answer \in {"name", "one"} =>
    outcome = Reduced([program EXCEPT !.effect = "none"])

\* A key that is not equal leaves the entry absent.
DeclinedIsAbsent == Done /\ program.answer = "declined" => outcome = "AttributeError"
=============================================================================
