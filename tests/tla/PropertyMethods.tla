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
(* property class with the property first, or bound and called later, or   *)
(* runs the statement c.x = 1 or del c.x, which gives None as they do. The *)
(* outcome is what the call returns, or the exception, and the function's  *)
(* calls. For op doc, the property is made of a getter whose __doc__ is a  *)
(* Python property returning "documented", raising LookupError, or raising *)
(* AttributeError (absent), read once: the property's __doc__ is that      *)
(* docstring, the error, or None. For op get, the getter is an instance   *)
(* whose Python __call__ returns "got" or raises LookupError, or absent,   *)
(* read by c.x or __get__ as the method's how says: the value, the error,  *)
(* or an AttributeError naming the getter, after its calls.                *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [op : {"set", "delete", "doc", "get"}, maker : {"property", "subclass"}, function : {"returns", "raises", "absent"},
             how : {"method", "class", "bound", "statement"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Call(p) == CASE p.op = "set" -> "set(c, 1)" [] p.op = "delete" -> "delete(c)" [] p.op = "get" -> "get(c)" [] OTHER -> "doc"

Run(p) == CASE p.op = "doc" -> (CASE p.function = "absent" -> "None doc"
                                 [] p.function = "raises" -> "LookupError doc"
                                 [] OTHER -> "'documented' doc")
            [] p.op = "get" -> (CASE p.function = "absent" -> "AttributeError getter"
                                 [] p.function = "raises" -> "LookupError get(c)"
                                 [] OTHER -> "'got' get(c)")
            [] p.function = "absent" -> IF p.op = "set" THEN "AttributeError setter" ELSE "AttributeError deleter"
            [] p.function = "raises" -> "LookupError " \o Call(p)
            [] OTHER -> "None " \o Call(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The function's own result never comes back.
ReturnsNone == Done /\ program.op \notin {"doc", "get"} /\ program.function = "returns" => outcome = "None " \o Call(program)
=============================================================================
