------------------------- MODULE BasicCustomization -------------------------
(***************************************************************************)
(* Basic customization, as The Python Language Reference specifies it      *)
(* (reference/datamodel.html#basic-customization): rich comparisons try    *)
(* the reflected method of a right operand whose type is a subclass of the *)
(* left's first, then the left's method, then the right's reflected one;   *)
(* NotImplemented passes to the next, and when all decline, == and != fall *)
(* back to identity while ordering raises TypeError; __ne__ by default     *)
(* inverts __eq__; a class that defines __eq__ without __hash__ is         *)
(* unhashable; truth comes from __bool__ (which must return a bool), else  *)
(* __len__ (which must not be negative), else is true; str() falls back to *)
(* __repr__, and format(x, "") is str(x).                                  *)
(*                                                                         *)
(* A comparison program defines class A with __eq__ and __lt__, class      *)
(* S(A) with __eq__ and __gt__, and class O with __eq__ and __gt__, each   *)
(* pair absent ("none"), returning its name like "A.lt" ("value"), or      *)
(* returning NotImplemented, then evaluates A() OP X() for X in A, S, O    *)
(* and OP in ==, !=, <, >. A hash program defines __eq__ or not and        *)
(* __hash__ (absent, returning 5, or None) and hashes an instance. A truth *)
(* program defines __bool__ (absent, True, False, or returning 1) and      *)
(* __len__ (absent, 0, 2, or -1) and takes bool(). A text program defines  *)
(* __repr__ ("r") and __str__ ("s") or not and takes str(), repr(), or     *)
(* format(x, ""). The outcome is the result (a default repr as "<default>")*)
(* or the exception.                                                       *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Kinds == {"none", "value", "notimpl"}
Classes == {"A", "S", "O"}
CompareOps == {"==", "!=", "<", ">"}
Programs == [part : {"compare"}, a : Kinds, s : Kinds, o : Kinds, right : Classes, op : CompareOps]
            \cup [part : {"hash"}, eq : BOOLEAN, hash : {"none", "five", "None"}]
            \cup [part : {"truth"}, bool : {"none", "True", "False", "one"}, len : {"none", "0", "2", "-1"}]
            \cup [part : {"text"}, repr : BOOLEAN, str : BOOLEAN, op : {"str", "repr", "format"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"
NI == "NotImplemented"

\* The class defining method m (eq, lt, gt) that C finds, and its kind; "object" if none does.
Defines(p, C, m) == CASE C = "A" -> m \in {"eq", "lt"} /\ p.a # "none"
                      [] C = "S" -> m \in {"eq", "gt"} /\ p.s # "none"
                      [] C = "O" -> m \in {"eq", "gt"} /\ p.o # "none"
Kind(p, C) == CASE C = "A" -> p.a [] C = "S" -> p.s [] C = "O" -> p.o
Owner(p, C, m) == IF Defines(p, C, m) THEN C ELSE IF C = "S" /\ Defines(p, "A", m) THEN "A" ELSE "object"

\* Calling the method m that class C finds, on two distinct objects.
Call(p, C, m) ==
    LET o == Owner(p, C, m) IN
    IF m = "ne"
    THEN LET eq == IF Owner(p, C, "eq") = "object" THEN NI
                   ELSE IF Kind(p, Owner(p, C, "eq")) = "notimpl" THEN NI ELSE "a str"
         IN IF eq = NI THEN NI ELSE "False"                   \* not "X.eq", which is true
    ELSE IF o = "object" \/ Kind(p, o) = "notimpl" THEN NI    \* object's methods decline for distinct objects
    ELSE o \o "." \o m

Direct(op) == CASE op = "==" -> "eq" [] op = "!=" -> "ne" [] op = "<" -> "lt" [] op = ">" -> "gt"
Reflected(op) == CASE op = "==" -> "eq" [] op = "!=" -> "ne" [] op = "<" -> "gt" [] op = ">" -> "lt"

Compare(p) ==
    LET sub == p.right = "S"                                  \* a proper subclass of A
        first == IF sub THEN Call(p, "S", Reflected(p.op)) ELSE NI
        second == Call(p, "A", Direct(p.op))
        third == IF sub THEN NI ELSE Call(p, p.right, Reflected(p.op))
    IN  CASE first # NI -> first
          [] second # NI -> second
          [] third # NI -> third
          [] p.op = "==" -> "False"                           \* identity, and they are distinct
          [] p.op = "!=" -> "True"
          [] OTHER -> "TypeError"

Hash(p) == CASE p.hash = "five" -> "5"
             [] p.hash = "None" \/ p.eq -> "TypeError"        \* __eq__ alone sets __hash__ to None
             [] OTHER -> "an int"

Truth(p) == CASE p.bool = "one" -> "TypeError"                \* __bool__ must return a bool
              [] p.bool # "none" -> p.bool
              [] p.len = "-1" -> "ValueError"
              [] p.len = "0" -> "False"
              [] OTHER -> "True"

Text(p) == CASE p.op = "repr" -> IF p.repr THEN "'r'" ELSE "<default>"
             [] p.str -> "'s'"
             [] p.repr -> "'r'"
             [] OTHER -> "<default>"

Run(p) == CASE p.part = "compare" -> Compare(p)
            [] p.part = "hash" -> Hash(p)
            [] p.part = "truth" -> Truth(p)
            [] p.part = "text" -> Text(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Equality never raises for want of methods.
EqualityTotal == Done /\ program.part = "compare" /\ program.op \in {"==", "!="} => outcome # "TypeError"

\* A subclass's reflected method wins over the base's direct one.
SubclassFirst == Done /\ program.part = "compare" /\ program.right = "S" /\ program.op \in {"<", "=="} /\
    program.s = "value" => outcome \in {"S.gt", "S.eq"}
=============================================================================
