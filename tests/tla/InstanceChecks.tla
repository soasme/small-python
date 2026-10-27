--------------------------- MODULE InstanceChecks ---------------------------
(***************************************************************************)
(* Customizing instance and subclass checks, as The Python Language        *)
(* Reference specifies it (reference/datamodel.html#customizing-instance-  *)
(* and-subclass-checks): isinstance() and issubclass() look up             *)
(* __instancecheck__ and __subclasscheck__ on the type of the class, so    *)
(* the methods take effect when a metaclass defines them and not when the  *)
(* class itself does; their results are converted to bool; an object       *)
(* whose type is exactly the class is its instance without the hook; a     *)
(* tuple of classes checks each; and a second argument that is neither a   *)
(* class nor a tuple of classes raises TypeError.                          *)
(*                                                                         *)
(* A program defines class C, under a metaclass whose hooks return 1,      *)
(* return 0, or raise ValueError, or with the hooks defined on C itself,   *)
(* or with none, and class D(C); then calls isinstance(x, CLS) for x a C,  *)
(* a D, or 1, or issubclass(X, CLS) for X C, D, or int, where CLS is C,    *)
(* (str, C), or 5. The outcome is the result or the exception.             *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Hooks == {"true", "false", "raise", "onclass", "none"}
Subjects == {"C", "D", "int"}
Programs == [check : {"isinstance", "issubclass"}, hook : Hooks, subject : Subjects, cls : {"C", "tuple", "five"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Default(p) == IF p.subject \in {"C", "D"} THEN "True" ELSE "False"

Check(p) ==
    CASE p.check = "isinstance" /\ p.subject = "C" -> "True"   \* exactly the class: no hook
      [] p.hook = "true" -> "True"
      [] p.hook = "false" -> "False"
      [] p.hook = "raise" -> "ValueError"
      [] OTHER -> Default(p)

Run(p) == IF p.cls = "five" THEN "TypeError" ELSE Check(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Hooks defined on the class itself change nothing.
ClassHooksIgnored == Done /\ program.hook = "onclass" /\ program.cls # "five" => outcome = Default(program)

\* Every result is a bool or an exception.
Bools == Done => outcome \in {"True", "False", "ValueError", "TypeError"}
=============================================================================
