----------------------------- MODULE Singletons -----------------------------
(***************************************************************************)
(* None, NotImplemented, and Ellipsis, as The Python Language Reference    *)
(* specifies them (reference/datamodel.html#none, #notimplemented,         *)
(* #ellipsis): each type has a single value and a single object with it,   *)
(* reached through the built-in name (and ... for Ellipsis) and through    *)
(* the type, which cannot be subclassed. None is false, Ellipsis is true,  *)
(* and NotImplemented in a boolean context raises TypeError. A function    *)
(* that returns nothing returns None.                                      *)
(*                                                                         *)
(* A program is an operation on two expressions from                       *)
(*                                                                         *)
(*     None  type(None)()  f()  [].append(1)  NotImplemented               *)
(*     type(NotImplemented)()  1 .__add__('')  ...  Ellipsis  type(...)()  *)
(*                                                                         *)
(* (f is a function without a return statement):                          *)
(*                                                                         *)
(*     is      x is y                                                      *)
(*     bool    bool(x)                                                     *)
(*     not     not x                                                       *)
(*     repr    repr(x)                                                     *)
(*     sub     class C(type(x)): pass                                      *)
(*     attr    x.a = 1                                                     *)
(*                                                                         *)
(* The outcome is the result's repr, or the exception.                     *)
(***************************************************************************)
EXTENDS Naturals

Sources == {"None", "type(None)()", "f()", "[].append(1)", "NotImplemented", "type(NotImplemented)()",
            "1 .__add__('')", "...", "Ellipsis", "type(...)()"}
Programs == [op : {"is"}, x : Sources, y : Sources] \cup [op : {"bool", "not", "repr", "sub", "attr"}, x : Sources]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* The object an expression evaluates to.
Value(e) == CASE e \in {"None", "type(None)()", "f()", "[].append(1)"} -> "None"
              [] e \in {"NotImplemented", "type(NotImplemented)()", "1 .__add__('')"} -> "NotImplemented"
              [] OTHER -> "Ellipsis"

Truth(v) == CASE v = "None" -> "False" [] v = "Ellipsis" -> "True" [] OTHER -> "TypeError"
Run(p) ==
    LET v == Value(p.x)
    IN  CASE p.op = "is" -> IF v = Value(p.y) THEN "True" ELSE "False"
          [] p.op = "bool" -> Truth(v)
          [] p.op = "not" -> CASE Truth(v) = "True" -> "False" [] Truth(v) = "False" -> "True" [] OTHER -> "TypeError"
          [] p.op = "repr" -> v
          [] p.op = "sub" -> "TypeError"                \* not an acceptable base type
          [] p.op = "attr" -> "AttributeError"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* There is a single object of each type: equal reprs mean the same object.
Single == Done /\ program.op = "is" => (outcome = "True") = (Run([op |-> "repr", x |-> program.x]) = Run([op |-> "repr", x |-> program.y]))
=============================================================================
