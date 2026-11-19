---------------------------- MODULE PropertyMethods ----------------------------
(***************************************************************************)
(* property's __set__ and __delete__ called as methods, as PLS-315 20.5.1  *)
(* specifies them: each calls fset(instance, value) or fdel(instance) and  *)
(* returns None, whatever the function returned; an exception it raises    *)
(* propagates; without the function, an AttributeError names the setter    *)
(* or deleter.                                                             *)
(*                                                                         *)
(* A program, for op set (C.x.__set__(c, 1)) or delete (C.x.__delete__(c)),*)
(* holds x = property(get, fset, fdel) on class C, made by property or a   *)
(* subclass of it, its function returning "ignored", raising LookupError,  *)
(* or absent (None), and calls the method from the property, from the      *)
(* property class with the property first, or bound and called later. The  *)
(* outcome is what the call returns, or the exception, and the function's  *)
(* calls.                                                                  *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [op : {"set", "delete"}, maker : {"property", "subclass"}, function : {"returns", "raises", "absent"},
             how : {"method", "class", "bound"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Call(p) == IF p.op = "set" THEN "set(c, 1)" ELSE "delete(c)"

Run(p) == CASE p.function = "absent" -> IF p.op = "set" THEN "AttributeError setter" ELSE "AttributeError deleter"
            [] p.function = "raises" -> "LookupError " \o Call(p)
            [] OTHER -> "None " \o Call(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The function's own result never comes back.
ReturnsNone == Done /\ program.function = "returns" => outcome = "None " \o Call(program)
=============================================================================
