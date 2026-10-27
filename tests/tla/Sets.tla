-------------------------------- MODULE Sets --------------------------------
(***************************************************************************)
(* Set types, as The Python Language Reference specifies them              *)
(* (reference/datamodel.html#set-types, library/stdtypes.html#set-types-   *)
(* set-frozenset): unordered collections of unique hashable objects, where *)
(* numbers equal as numbers (1, 1.0, True) are one element; union,         *)
(* intersection, difference, symmetric difference, and the subset and      *)
(* superset comparisons, whose results take the type of the left operand;  *)
(* set is mutable (add, discard, remove, and the augmented operators) and  *)
(* unhashable, frozenset immutable and hashable.                           *)
(*                                                                         *)
(* A program is either                                                     *)
(*   - two sets a and b of elements from {0, 1, 2}, each a set or a        *)
(*     frozenset, and one of  a | b, a & b, a - b, a ^ b, a <= b, a < b,   *)
(*     a >= b, a > b, a == b, a.isdisjoint(b), a |= b, a &= b, a -= b,     *)
(*     a ^= b, a.add(2), a.discard(2), a.remove(2), hash(a), a.add([]); or *)
(*   - set(<items>) of up to three of 1, 1.0, True, 2.                     *)
(*                                                                         *)
(* The outcome is a's type and elements afterwards (or the result's, for   *)
(* an operator), the bool, or the exception.                               *)
(***************************************************************************)
EXTENDS Integers, Sequences, FiniteSets

Kinds == {"set", "frozenset"}
Elements == SUBSET {0, 1, 2}
Binary == {"|", "&", "-", "^", "<=", "<", ">=", ">", "==", "isdisjoint"}
Mutate == {"|=", "&=", "-=", "^=", "add", "discard", "remove", "hash", "add list"}
Numbers == {"1", "1.0", "True", "2"}
Programs == [ka : Kinds, a : Elements, op : Binary \cup Mutate, kb : Kinds, b : Elements]
            \cup [op : {"build"}, items : UNION {[1..n -> Numbers] : n \in 0..3}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", "", {}>>
Error(name) == <<name, "", {}>>
Bool(b) == <<"bool", IF b THEN "True" ELSE "False", {}>>

Combine(op, a, b) == CASE op \in {"|", "|="} -> a \cup b [] op \in {"&", "&="} -> a \cap b
                       [] op \in {"-", "-="} -> a \ b [] op \in {"^", "^="} -> (a \ b) \cup (b \ a)

\* The numbers that set() keeps: the first of each equal value, as spelled.
RECURSIVE Keep(_, _)
Keep(s, seen) ==
    IF s = <<>> THEN {}
    ELSE LET v == IF Head(s) = "2" THEN 2 ELSE 1
         IN  (IF v \in seen THEN {} ELSE {Head(s)}) \cup Keep(Tail(s), seen \cup {v})

Run(p) ==
    IF p.op = "build" THEN <<"set", "", Keep(p.items, {})>>
    ELSE LET a == p.a  b == p.b
         IN  CASE p.op \in {"|", "&", "-", "^"} -> <<p.ka, "", Combine(p.op, a, b)>>
               [] p.op = "<=" -> Bool(a \subseteq b)
               [] p.op = "<" -> Bool(a \subseteq b /\ a # b)
               [] p.op = ">=" -> Bool(b \subseteq a)
               [] p.op = ">" -> Bool(b \subseteq a /\ a # b)
               [] p.op = "==" -> Bool(a = b)
               [] p.op = "isdisjoint" -> Bool(a \cap b = {})
               \* A set is changed in place; a frozenset name is rebound to a new one.
               [] p.op \in {"|=", "&=", "-=", "^="} -> <<p.ka, "", Combine(p.op, a, b)>>
               [] p.ka = "frozenset" /\ p.op \in {"add", "discard", "remove", "add list"} -> Error("AttributeError")
               [] p.op = "add" -> <<"set", "", a \cup {2}>>
               [] p.op = "discard" -> <<"set", "", a \ {2}>>
               [] p.op = "remove" -> IF 2 \in a THEN <<"set", "", a \ {2}>> ELSE Error("KeyError")
               [] p.op = "add list" -> Error("TypeError")                \* unhashable
               [] p.op = "hash" -> IF p.ka = "set" THEN Error("TypeError") ELSE <<"hashable", "", {}>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* a <= b and a >= b together are a == b.
Antisymmetric == Done /\ program.op = "<=" /\ outcome = Bool(TRUE) /\ Run([program EXCEPT !.op = ">="]) = Bool(TRUE)
                 => Run([program EXCEPT !.op = "=="]) = Bool(TRUE)

\* Numbers equal as numbers are one element.
Unique == Done /\ program.op = "build" => Cardinality(outcome[3]) <= 2
=============================================================================
