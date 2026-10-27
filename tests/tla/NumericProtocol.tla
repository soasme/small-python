-------------------------- MODULE NumericProtocol --------------------------
(***************************************************************************)
(* Emulating numeric types, as The Python Language Reference specifies it  *)
(* (reference/datamodel.html#emulating-numeric-types): x + y calls         *)
(* x.__add__(y), then y.__radd__(x) when the operands' types differ, but   *)
(* first when y's type is a subclass of x's that provides a different      *)
(* __radd__; NotImplemented passes on, and when every method declines the  *)
(* operation raises TypeError; x += y tries __iadd__ first and falls back  *)
(* to x + y; __index__ supplies integers to subscripts, range(), and       *)
(* int() (which prefers __int__) and must return an int.                   *)
(*                                                                         *)
(* A binary program defines class A with __add__ and __radd__, S(A) with   *)
(* or without its own __radd__, and O with __radd__, each absent,          *)
(* returning its name like "A.add" (an inherited method keeps the name of  *)
(* its class), or returning NotImplemented, and evaluates A() + R() for R  *)
(* A, S, or O. An in-place program defines A's __iadd__ and __add__ the    *)
(* same way and evaluates x += A() for x = A(). An index program defines   *)
(* __index__ (absent, returning 3, or returning 3.0) with or without       *)
(* __int__ returning 7 and evaluates [10, 20, 30, 40][x], len(range(x)),   *)
(* or int(x). The outcome is the result or the exception.                  *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Kinds == {"none", "value", "notimpl"}
Programs == [part : {"binary"}, add : Kinds, radd : Kinds, s : Kinds, o : Kinds, right : {"A", "S", "O"}]
            \cup [part : {"inplace"}, iadd : Kinds, add : Kinds]
            \cup [part : {"index"}, index : {"none", "int", "float"}, int : BOOLEAN, use : {"subscript", "range", "int"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"
NI == "NotImplemented"

\* Calling a method of kind k named n: its result, or NotImplemented if absent or declining.
Call(k, n) == IF k = "value" THEN n ELSE NI

\* The __radd__ that R finds, as <<kind, name>>.
RAdd(p, R) == CASE R = "A" -> <<p.radd, "A.radd">>
                [] R = "S" -> IF p.s # "none" THEN <<p.s, "S.radd">> ELSE <<p.radd, "A.radd">>
                [] R = "O" -> <<p.o, "O.radd">>

Binary(p) ==
    LET r == RAdd(p, p.right)
        priority == p.right = "S" /\ p.s # "none"             \* S overrides __radd__
        first == IF priority THEN Call(r[1], r[2]) ELSE NI
        second == Call(p.add, "A.add")
        third == IF p.right # "A" /\ ~priority THEN Call(r[1], r[2]) ELSE NI
    IN  CASE first # NI -> first [] second # NI -> second [] third # NI -> third [] OTHER -> "TypeError"

InPlace(p) == CASE p.iadd = "value" -> "A.iadd"
                [] p.add = "value" -> "A.add"
                [] OTHER -> "TypeError"

Index(p) == CASE p.use = "int" /\ p.int -> "7"
              [] p.index = "int" -> CASE p.use = "subscript" -> "40" [] OTHER -> "3"
              [] OTHER -> "TypeError"

Run(p) == CASE p.part = "binary" -> Binary(p)
            [] p.part = "inplace" -> InPlace(p)
            [] p.part = "index" -> Index(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Operands of the same type never reach the reflected method.
SameTypeNoReflection == Done /\ program.part = "binary" /\ program.right = "A" => outcome \in {"A.add", "TypeError"}

\* __int__ never stands in for __index__.
IntIsNotIndex == Done /\ program.part = "index" /\ program.use # "int" /\ program.index # "int" => outcome = "TypeError"
=============================================================================
