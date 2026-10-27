----------------------------- MODULE Operators -----------------------------
(***************************************************************************)
(* How a binary operator or comparison picks the special method that       *)
(* computes it, as The Python Language Reference specifies it              *)
(* (reference/datamodel.html#emulating-numeric-types and #object.__lt__),  *)
(* for x of class L and y of class R:                                      *)
(*                                                                         *)
(*     x + y    x += y    x == y    x != y    x < y                        *)
(*                                                                         *)
(* R is L itself, a subclass of L, or an unrelated class. Each class may   *)
(* define each special method the operator consults, as one returning a   *)
(* value or one returning NotImplemented; a method R does not define it    *)
(* inherits from L when R is L's subclass. A method returning a value      *)
(* returns "<class>.<name>:<self>", like "L.add:x". The outcome is the     *)
(* result, as a string, or the exception.                                  *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

Ops == {"+", "+=", "==", "!=", "<"}
Rels == {"same", "sub", "other"}
Kinds == {"none", "value", "NI"}
LMethods == {"add", "radd", "iadd", "eq", "ne", "lt", "gt"}
RMethods == {"radd", "eq", "ne", "gt"}

\* The methods each operator consults.
UsesL(op) == CASE op = "+" -> {"add", "radd"} [] op = "+=" -> {"add", "radd", "iadd"}
               [] op = "==" -> {"eq"} [] op = "!=" -> {"eq", "ne"} [] op = "<" -> {"lt", "gt"}
UsesR(op) == CASE op \in {"+", "+="} -> {"radd"} [] op = "==" -> {"eq"}
               [] op = "!=" -> {"eq", "ne"} [] op = "<" -> {"gt"}

Fill(f, all) == [m \in all |-> IF m \in DOMAIN f THEN f[m] ELSE "none"]
Programs == UNION {
    {[op |-> op, rel |-> rel, L |-> Fill(l, LMethods), R |-> Fill(r, RMethods)] :
        l \in [UsesL(op) -> Kinds], r \in [IF rel = "same" THEN {} ELSE UsesR(op) -> Kinds]}
    : op \in Ops, rel \in Rels}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"
NI == "NI"

\* Which class's method m an operand finds, if any: "L", "R", or "none".
Definer(p, who, m) ==
    CASE who = "x" \/ p.rel = "same" -> IF p.L[m] # "none" THEN "L" ELSE "none"
      [] p.rel = "other" -> IF p.R[m] # "none" THEN "R" ELSE "none"
      [] OTHER -> IF p.R[m] # "none" THEN "R" ELSE IF p.L[m] # "none" THEN "L" ELSE "none"

\* What calling who.m(other) returns: a value, or NI (also when there is no
\* such method, or only object's, which returns NotImplemented).
Call(p, who, m) ==
    LET d == Definer(p, who, m)
    IN  IF d = "none" \/ (IF d = "L" THEN p.L[m] ELSE p.R[m]) = "NI" THEN NI
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
    IN  First(calls, "TypeError")

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

\* A subclass's own reflected method is called before the left operand's.
SubclassFirst == Done /\ program.op = "+" /\ program.rel = "sub" /\ program.R.radd = "value" => outcome = "R.radd:y"

\* == and != never raise without a method that does; < does.
EqualityTotal == Done /\ program.op \in {"==", "!="} => outcome # "TypeError"

\* An in-place method returning a value is used as is.
InPlaceFirst == Done /\ program.op = "+=" /\ program.L.iadd = "value" => outcome = "L.iadd:x"
=============================================================================
