--------------------------- MODULE InstanceChecks ---------------------------
(***************************************************************************)
(* Customizing instance and subclass checks, as The Python Language        *)
(* Reference specifies it (reference/datamodel.html#customizing-instance-  *)
(* and-subclass-checks): isinstance() and issubclass() look up             *)
(* __instancecheck__ and __subclasscheck__ on the type of the class, so    *)
(* the methods take effect when a metaclass defines them and not when the  *)
(* class itself does; their results are converted to bool; an object       *)
(* whose type is exactly the class is its instance without the hook; a     *)
(* tuple of classes checks each, a nested tuple's before the items after  *)
(* it; a result's truth is its __bool__ or __len__; a second argument     *)
(* that is an instance                                                    *)
(* is checked by its class's hooks; and one that is neither a class nor a  *)
(* tuple of classes, without hooks, raises TypeError.                      *)
(*                                                                         *)
(* A program defines class C, under a metaclass whose hooks return 1,      *)
(* return 0, return an object whose __bool__ returns True or whose        *)
(* __len__ returns 0, or raise ValueError, or with the hooks defined on C *)
(* itself,                                                                 *)
(* or with none, and class D(C); then calls isinstance(x, CLS) for x a C,  *)
(* a D, or 1, or issubclass(X, CLS) for X C, D, or int, where CLS is C,    *)
(* (str, C), (C, int), ((str, (C,)),), 5, or C(). The outcome is the      *)
(* result or the                                                           *)
(* exception; a tuple's items are checked in order until one is true.     *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Hooks == {"true", "false", "truthy", "empty", "raise", "onclass", "none"}
Subjects == {"C", "D", "int"}
Programs == [check : {"isinstance", "issubclass"}, hook : Hooks, subject : Subjects, cls : {"C", "tuple", "pair", "nested", "five", "instance"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Default(p) == IF p.subject \in {"C", "D"} THEN "True" ELSE "False"

Check(p) ==
    CASE p.check = "isinstance" /\ p.subject = "C" -> "True"   \* exactly the class: no hook
      [] p.hook \in {"true", "truthy"} -> "True"
      [] p.hook \in {"false", "empty"} -> "False"
      [] p.hook = "raise" -> "ValueError"
      [] OTHER -> Default(p)

\* (C, int): int decides once C's check is false.
Pair(p) == IF Check(p) = "False" /\ p.subject = "int" THEN "True" ELSE Check(p)

\* An instance's class's hooks check against it; a metaclass's are not its class's.
Run(p) == CASE p.cls = "five" -> "TypeError"
            [] p.cls = "instance" -> IF p.hook = "onclass" THEN "True" ELSE "TypeError"
            [] p.cls = "pair" -> Pair(p)
            [] OTHER -> Check(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Hooks defined on the class itself change nothing.
ClassHooksIgnored == Done /\ program.hook = "onclass" /\ program.cls \in {"C", "tuple", "nested"} => outcome = Default(program)

\* A nested tuple checks as the flat one of its items.
NestedFlat == Done /\ program.cls = "nested" => outcome = Run([program EXCEPT !.cls = "tuple"])

\* Every result is a bool or an exception.
Bools == Done => outcome \in {"True", "False", "ValueError", "TypeError"}
=============================================================================
