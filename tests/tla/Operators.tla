----------------------------- MODULE Operators -----------------------------
(***************************************************************************)
(* How a binary operator or comparison picks the special method that       *)
(* computes it, as The Python Language Reference specifies it              *)
(* (reference/datamodel.html#emulating-numeric-types and #object.__lt__),  *)
(* for x of class L and y of class R:                                      *)
(*                                                                         *)
(*     x + y    x += y    x == y    x != y    x < y                        *)
(*                                                                         *)
(* R is L itself, a subclass of L, or an unrelated class. Each class       *)
(* may define each special method the operator consults, as one            *)
(* returning a value or one returning NotImplemented; a method R does      *)
(* not define it inherits from L when R is L's subclass. A method          *)
(* returning a value returns "<class>.<name>:<self>", like "L.add:x".      *)
(* The outcome is the result, as a string, or the exception. L and R       *)
(* are classes of x and y, or metaclasses of the classes x and y           *)
(* (holder "class"), whose type defines none of the methods; the           *)
(* outcome is the same for both. For x + y, L and R may also subclass      *)
(* int or str (holders "int" and "str"), y may be an exact int or str      *)
(* (relation "exact"), and a method a class does not define is the         *)
(* builtin's, int's __add__ and __radd__ giving 3 for 1 and 2. str's       *)
(* __add__, "ab" for "a" and "b", answers x's turn only when L defines     *)
(* __radd__; otherwise its concatenation, a sequence's, comes after        *)
(* both operands' methods, unless L defines __add__. x may instead be      *)
(* the exact str "a" with y of an unrelated plain class R (relation        *)
(* "left"): a sequence has no method of +, so only y's __radd__            *)
(* answers before its concatenation raises TypeError. Or x may be of L     *)
(* subclassing str with y of an unrelated plain class R (relation          *)
(* "plain"): str's __add__ is the concatenation and raises TypeError for   *)
(* y rather than returning NotImplemented, so once L defines __radd__ y's  *)
(* __radd__ is never reached. Or x may be of a plain class L with y of R  *)
(* subclassing str (relation "right"): with no __add__ answering, y's      *)
(* __radd__ is the last call, str's __add__ never consulted.               *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

Ops == {"+", "+=", "==", "!=", "<"}
Rels == {"same", "sub", "other"}
Builtins == {"int", "str"}
Kinds == {"none", "value", "NI"}
LMethods == {"add", "radd", "iadd", "eq", "ne", "lt", "gt"}
RMethods == {"radd", "eq", "ne", "gt"}

\* The methods each operator consults.
UsesL(op) == CASE op = "+" -> {"add", "radd"} [] op = "+=" -> {"add", "radd", "iadd"}
               [] op = "==" -> {"eq"} [] op = "!=" -> {"eq", "ne"} [] op = "<" -> {"lt", "gt"}
UsesR(op) == CASE op \in {"+", "+="} -> {"radd"} [] op = "==" -> {"eq"}
               [] op = "!=" -> {"eq", "ne"} [] op = "<" -> {"gt"}

Fill(f, all) == [m \in all |-> IF m \in DOMAIN f THEN f[m] ELSE "none"]
Holders == {"instance", "class"}
Programs == (UNION {
    {[op |-> op, rel |-> rel, holder |-> h, L |-> Fill(l, LMethods), R |-> Fill(r, RMethods)] :
        l \in [UsesL(op) -> Kinds], r \in [IF rel = "same" THEN {} ELSE UsesR(op) -> Kinds], h \in Holders}
    : op \in Ops, rel \in Rels})
    \cup (UNION {
    {[op |-> "+", rel |-> rel, holder |-> h, L |-> Fill(l, LMethods), R |-> Fill(r, RMethods)] :
        l \in [UsesL("+") -> Kinds], r \in [IF rel \in {"same", "exact"} THEN {} ELSE UsesR("+") -> Kinds], h \in Builtins}
    : rel \in Rels \cup {"exact"}})
    \cup {[op |-> "+", rel |-> "left", holder |-> "str", L |-> Fill(l, LMethods), R |-> Fill(r, RMethods)] :
           l \in [{} -> Kinds], r \in [UsesR("+") -> Kinds]}
    \cup {[op |-> "+", rel |-> rel, holder |-> "str", L |-> Fill(l, LMethods), R |-> Fill(r, RMethods)] :
           l \in [UsesL("+") -> Kinds], r \in [UsesR("+") -> Kinds], rel \in {"plain", "right"}}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"
NI == "NI"

\* The builtin's own method m, "B", else "none": int's __add__ and __radd__;
\* str's __add__ only once L has a number slot, by defining __radd__.
Builtin(p, m) == IF (p.holder = "int" /\ m \in {"add", "radd"}) \/ (p.holder = "str" /\ m = "add" /\ p.L.radd # "none")
                 THEN "B" ELSE "none"

\* Which class's method m an operand finds, if any: "L", "R", "B" (the
\* builtin's), or "none".
Definer(p, who, m) ==
    CASE who = "y" /\ p.rel = "exact" -> Builtin(p, m)
      [] who = "y" /\ p.rel = "plain" -> IF p.R[m] # "none" THEN "R" ELSE "none"
      [] p.rel = "right" -> IF (IF who = "x" THEN p.L[m] ELSE p.R[m]) # "none" THEN (IF who = "x" THEN "L" ELSE "R") ELSE "none"
      [] (who = "x" /\ p.rel # "right") \/ p.rel = "same" -> IF p.L[m] # "none" THEN "L" ELSE Builtin(p, m)
      [] p.rel = "other" -> IF p.R[m] # "none" THEN "R" ELSE Builtin(p, m)
      [] OTHER -> IF p.R[m] # "none" THEN "R" ELSE IF p.L[m] # "none" THEN "L" ELSE Builtin(p, m)

\* What calling who.m(other) returns: a value, or NI (also when there is no
\* such method, or only object's, which returns NotImplemented); str's
\* __add__ raises TypeError for a y that is no str.
Call(p, who, m) ==
    LET d == Definer(p, who, m)
    IN  IF d = "B" THEN (IF p.holder = "int" THEN "3" ELSE IF p.rel = "plain" THEN "TypeError" ELSE "ab")
        ELSE IF d = "none" \/ (IF d = "L" THEN p.L[m] ELSE p.R[m]) = "NI" THEN NI
        ELSE d \o "." \o m \o ":" \o who

\* object.__ne__ inverts what __eq__ returns (every value here is true).
CallNe(p, who) ==
    IF Definer(p, who, "ne") # "none" THEN Call(p, who, "ne")
    ELSE IF Call(p, who, "eq") = NI THEN NI ELSE "False"

\* The first result of a sequence of calls that is not NotImplemented.
RECURSIVE First(_, _)
First(calls, otherwise) ==
    IF calls = <<>> THEN otherwise
    ELSE IF Head(calls) # NI THEN Head(calls) ELSE First(Tail(calls), otherwise)

\* x + y: y.__radd__ goes first when R is a subclass of L defining its own;
\* otherwise it goes after x.__add__, and only for different types.
Add(p) ==
    LET first == p.rel = "sub" /\ p.R.radd # "none"
        calls == IF first THEN <<Call(p, "y", "radd"), Call(p, "x", "add")>>
                 ELSE <<Call(p, "x", "add")>> \o (IF p.rel = "same" THEN <<>> ELSE <<Call(p, "y", "radd")>>)
    IN  First(calls, IF p.holder = "str" /\ p.L.add = "none" /\ p.rel \notin {"left", "plain", "right"} THEN "ab" ELSE "TypeError")

\* A comparison tries the reflected method of y first when R is a proper
\* subclass of L, otherwise after x's; then falls back to identity.
Compare(p, mine, theirs, otherwise) ==
    IF p.rel = "sub" THEN First(<<theirs, mine>>, otherwise) ELSE First(<<mine, theirs>>, otherwise)

Run(p) ==
    CASE p.op = "+" -> Add(p)
      [] p.op = "+=" -> IF Call(p, "x", "iadd") # NI THEN Call(p, "x", "iadd") ELSE Add(p)
      [] p.op = "==" -> Compare(p, Call(p, "x", "eq"), Call(p, "y", "eq"), "False")
      [] p.op = "!=" -> Compare(p, CallNe(p, "x"), CallNe(p, "y"), "True")
      [] p.op = "<" -> Compare(p, Call(p, "x", "lt"), Call(p, "y", "gt"), "TypeError")

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
(* What the reference states about every dispatch.                         *)

Done == outcome # Pending

\* "The reflected methods are only called if the operands are of
\* different types" (for arithmetic, not comparisons).
ReflectedOnlyDifferent == Done /\ program.op \in {"+", "+="} /\ program.rel = "same" => outcome # "L.radd:y"

\* An int subclass's operand without the method computes int's result in
\* that method's place.
BuiltinInPlace == Done /\ program.op = "+" /\ program.holder = "int" /\ program.L.add = "none" /\
    ~(program.rel = "sub" /\ program.R.radd = "value") => outcome = "3"

\* A subclass's own reflected method is called before the left operand's.
SubclassFirst == Done /\ program.op = "+" /\ program.rel = "sub" /\ program.R.radd = "value" => outcome = "R.radd:y"

\* == and != never raise without a method that does; < does.
EqualityTotal == Done /\ program.op \in {"==", "!="} => outcome # "TypeError"

\* A str subclass defining __radd__ has str's concatenation as its __add__,
\* which raises for a y that is no str before y's __radd__ is tried.
ConcatenationRaises == Done /\ program.rel = "plain" /\ program.L.add = "none" /\ program.L.radd # "none" =>
    outcome = "TypeError"

\* A plain left operand without __add__ leaves the right one's __radd__ last.
ReflectedLast == Done /\ program.rel = "right" /\ program.L.add # "value" /\ program.R.radd = "value" => outcome = "R.radd:y"

\* An in-place method returning a value is used as is.
InPlaceFirst == Done /\ program.op = "+=" /\ program.L.iadd = "value" => outcome = "L.iadd:x"
=============================================================================
