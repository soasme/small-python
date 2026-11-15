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
(*     a >= b, a > b, a == b, a.isdisjoint(b), a <= b <= a, a |= b,        *)
(*     a &= b, a -= b, a ^= b, a.add(2), a.discard(2), a.remove(2),        *)
(*     hash(a), a.add([]), the methods union, intersection, difference,    *)
(*     symmetric_difference, issubset and issuperset of b, and update,     *)
(*     intersection_update, difference_update and                          *)
(*     symmetric_difference_update of b, which change a set in place and   *)
(*     return None,                                                        *)
(*     where with eq each element is an object hashing as its value whose  *)
(*     Python __eq__ compares values, which changes no outcome; or         *)
(*   - set(<items>) of up to three of 1, 1.0, True, 2; or                  *)
(*   - set(src), frozenset(src), {*src}, {0}.update(src), S(src),          *)
(*     F(src), set.__init__({0}, src), which empties the set first, or     *)
(*     SI(src) of SI a set subclass whose Python __init__ calls            *)
(*     super().__init__(src), or SN(src) of SN one whose Python            *)
(*     __new__ returns super().__new__(cls), its __init__ set's, of S      *)
(*     and F a set's and a frozenset's subclasses of no methods, of a      *)
(*     list or a generator of two objects whose Python __hash__ (which     *)
(*     loops) logs "h" and its value, the second's returning, raising      *)
(*     TypeError or raising ValueError, or both of value 1, the second     *)
(*     found equal by the first's Python __eq__ (which loops), logging     *)
(*     "e" and its value; a generator logs "y" and the value before        *)
(*     each item; with tuple, each object is the first item of a pair      *)
(*     (object, 0); or                                                     *)
(*   - set(src), frozenset(src), {*src}, set().union(src), an empty set's  *)
(*     update(src) or |= src, S(src) or F(src), of a set src of three      *)
(*     objects of one hash                                                 *)
(*     whose Python __eq__ logs "e": merged into an empty set, the         *)
(*     distinct elements are compared with none (Annex D); or              *)
(*   - {K(1)}'s or S({K(1)})'s union, update, difference, intersection,    *)
(*     isdisjoint, issuperset, issubset, symmetric_difference or           *)
(*     symmetric_difference_update of a list, its iterator or a generator  *)
(*     of K(1) and K(2), called alone or as another call's argument: each  *)
(*     item is hashed and compared with the set's K(1) before the next is  *)
(*     taken; intersection, isdisjoint and issubset stop at the first,     *)
(*     which decides; the symmetric ones make a set of the items,          *)
(*     comparing none, then toggle K(1), comparing it once; a subclass's   *)
(*     methods make a set, its updates change it.                          *)
(*                                                                         *)
(* The outcome is a's type and elements afterwards (or the result's, for   *)
(* an operator), the bool, or the exception; for the hashed builds, the    *)
(* log of calls, each item hashed before the next is taken, and a          *)
(* TypeError of __hash__ named as a set element's.                         *)
(***************************************************************************)
EXTENDS Integers, Sequences, FiniteSets

Kinds == {"set", "frozenset"}
Elements == SUBSET {0, 1, 2}
Methods == {"union", "intersection", "difference", "symmetric_difference"}
Updates == {"update", "intersection_update", "difference_update", "symmetric_difference_update"}
Binary == {"|", "&", "-", "^", "<=", "<", ">=", ">", "==", "isdisjoint", "<= <=", "issubset", "issuperset"} \cup Methods
Mutate == {"|=", "&=", "-=", "^=", "add", "discard", "remove", "hash", "add list"} \cup Updates
Numbers == {"1", "1.0", "True", "2"}
Programs == [ka : Kinds, a : Elements, op : Binary \cup Mutate, kb : Kinds, b : Elements, eq : BOOLEAN]
            \cup [op : {"build"}, items : UNION {[1..n -> Numbers] : n \in 0..3}]
            \cup [op : {"hashed"}, form : {"set", "frozenset", "star", "update", "S", "F", "init", "SI", "SN"}, source : {"list", "generator"},
                  fails : {"no", "TypeError", "ValueError", "equal"}, tuple : BOOLEAN]
            \cup [op : {"merge"}, form : {"set", "frozenset", "star", "union", "update", "|=", "S", "F"}]
            \cup [op : {"iterable"}, method : {"union", "difference", "intersection", "isdisjoint", "issuperset", "issubset",
                                              "symmetric_difference", "symmetric_difference_update", "update"},
                  source : {"list", "generator", "iterator"}, kind : {"set", "S"}, form : {"statement", "argument"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", "", {}>>
Error(name) == <<name, "", {}>>
Bool(b) == <<"bool", IF b THEN "True" ELSE "False", {}>>

Combine(op, a, b) == CASE op \in {"|", "|=", "union", "update"} -> a \cup b
                       [] op \in {"&", "&=", "intersection", "intersection_update"} -> a \cap b
                       [] op \in {"-", "-=", "difference", "difference_update"} -> a \ b
                       [] op \in {"^", "^=", "symmetric_difference", "symmetric_difference_update"} -> (a \ b) \cup (b \ a)

\* The numbers that set() keeps: the first of each equal value, as spelled.
RECURSIVE Keep(_, _)
Keep(s, seen) ==
    IF s = <<>> THEN {}
    ELSE LET v == IF Head(s) = "2" THEN 2 ELSE 1
         IN  (IF v \in seen THEN {} ELSE {Head(s)}) \cup Keep(Tail(s), seen \cup {v})

\* The type a build makes: a subclass's when it calls one.
Built(form) == IF form \in {"frozenset", "S", "F", "SI", "SN"} THEN form ELSE "set"

\* A list's items exist before the set hashes them; a generator gives each
\* as the set takes it.
RunHashed(p) ==
    <<CASE p.fails = "TypeError" -> "TypeError: cannot use '" \o (IF p.tuple THEN "tuple" ELSE "K") \o "' as a set element (t)"
        [] p.fails = "ValueError" -> "ValueError"
        [] OTHER -> Built(p.form),
      CASE p.fails = "equal" -> IF p.source = "list" THEN "h1 h1 e1" ELSE "y1 h1 y1 h1 e1"
        [] p.source = "list" -> "h1 h2"
        [] OTHER -> "y1 h1 y2 h2",
      CASE p.fails \notin {"no", "equal"} -> {}
        [] p.fails = "equal" -> IF p.form = "update" THEN {0, 1} ELSE {1}
        [] p.form = "update" -> {0, 1, 2}
        [] OTHER -> {1, 2}>>

\* The items an iterable method takes, each hashed and compared with K(1)
\* in turn: a generator gives each as it is taken. The symmetric methods
\* hash both items into a set, then look K(1) up in it, or its K(1) up in
\* the set, and drop it.
RunIterable(p) ==
    LET y(v) == IF p.source = "generator" THEN "y" \o v \o " " ELSE ""   \* a list's iterator logs none
        first == y("1") \o "h1 e1"
        both == y("1") \o "h1 " \o y("2") \o "h2"
        log == CASE p.method \in {"intersection", "isdisjoint", "issubset"} -> first
                 [] p.method \in {"symmetric_difference", "symmetric_difference_update"} -> both \o " e1"
                 [] OTHER -> first \o " " \o y("2") \o "h2"
        made == IF p.method \in {"update", "symmetric_difference_update"} THEN p.kind ELSE "set"
    IN  CASE p.method \in {"union", "update"} -> <<made, log, {1, 2}>>
          [] p.method = "difference" -> <<made, log, {}>>
          [] p.method = "intersection" -> <<made, log, {1}>>
          [] p.method \in {"symmetric_difference", "symmetric_difference_update"} -> <<made, log, {2}>>
          [] OTHER -> <<"bool", log, {}>>

Run(p) ==
    IF p.op = "build" THEN <<"set", "", Keep(p.items, {})>>
    ELSE IF p.op = "iterable" THEN RunIterable(p)
    ELSE IF p.op = "hashed" THEN RunHashed(p)
    ELSE IF p.op = "merge" THEN <<Built(p.form), "", {0, 1, 2}>>
    ELSE LET a == p.a  b == p.b
         IN  CASE p.op \in {"|", "&", "-", "^"} \cup Methods -> <<p.ka, "", Combine(p.op, a, b)>>
               [] p.op \in {"<=", "issubset"} -> Bool(a \subseteq b)
               [] p.op = "<" -> Bool(a \subseteq b /\ a # b)
               [] p.op \in {">=", "issuperset"} -> Bool(b \subseteq a)
               [] p.op = ">" -> Bool(b \subseteq a /\ a # b)
               [] p.op = "==" -> Bool(a = b)
               [] p.op = "isdisjoint" -> Bool(a \cap b = {})
               [] p.op = "<= <=" -> Bool(a = b)                         \* a chain's links
               \* A set is changed in place; a frozenset name is rebound to a new one.
               [] p.op \in {"|=", "&=", "-=", "^="} -> <<p.ka, "", Combine(p.op, a, b)>>
               [] p.ka = "frozenset" /\ p.op \in {"add", "discard", "remove", "add list"} \cup Updates -> Error("AttributeError")
               [] p.op \in Updates -> <<"set", "", Combine(p.op, a, b)>>
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

\* A method called as another call's argument behaves as one called alone.
FormFree == Done /\ program.op = "iterable" => outcome = Run([program EXCEPT !.form = "statement"])

\* intersection, isdisjoint and issubset take no item past the one that decides.
Decided == Done /\ program.op = "iterable" /\ program.method \in {"intersection", "isdisjoint", "issubset"} =>
           outcome[2] \in {"h1 e1", "y1 h1 e1"}

\* Numbers equal as numbers are one element.
Unique == Done /\ program.op = "build" => Cardinality(outcome[3]) <= 2
=============================================================================
