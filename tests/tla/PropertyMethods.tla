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
(* AttributeError (absent), read once as the property is made, by a call, *)
(* or for how method or bound by list() or next() of a map of the maker:   *)
(* the property's __doc__ is that                                          *)
(* docstring, the error, or None. For op get, the getter is an instance   *)
(* whose Python __call__ returns "got" or raises LookupError, or absent,   *)
(* read by c.x or __get__ as the method's how says: the value, the error,  *)
(* or an AttributeError naming the getter, after its calls. For op named,  *)
(* a property added to C after its creation, with no setter or deleter,    *)
(* has a getter instance whose __name__ is a Python property returning     *)
(* "nm", raising LookupError, or raising AttributeError (absent): c.x = 1  *)
(* (statement), setattr (method), del c.x (class) or delattr (bound) raise *)
(* the AttributeError quoting that name, or none ("-"), or the error. Op   *)
(* callnamed calls the property's methods instead: x.__set__(c, 1)         *)
(* (statement), type(x).__set__(x, c, 1) (method), type(x).__delete__(x,  *)
(* c) (class), or x.__delete__ bound first, then called (bound).           *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [op : {"set", "delete", "doc", "get", "named", "callnamed"}, maker : {"property", "subclass"}, function : {"returns", "raises", "absent"},
             how : {"method", "class", "bound", "statement"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Call(p) == CASE p.op = "set" -> "set(c, 1)" [] p.op = "delete" -> "delete(c)" [] p.op = "get" -> "get(c)" [] OTHER -> "doc"

Accessor(p) == IF p.how \in {"method", "statement"} THEN "setter" ELSE "deleter"

Run(p) == CASE p.op = "doc" -> (CASE p.function = "absent" -> "None doc"
                                 [] p.function = "raises" -> "LookupError doc"
                                 [] OTHER -> "'documented' doc")
            [] p.op = "get" -> (CASE p.function = "absent" -> "AttributeError getter"
                                 [] p.function = "raises" -> "LookupError get(c)"
                                 [] OTHER -> "'got' get(c)")
            [] p.op \in {"named", "callnamed"} -> (CASE p.function = "raises" -> "LookupError name"
                                   [] p.function = "absent" -> "AttributeError - " \o Accessor(p) \o " name"
                                   [] OTHER -> "AttributeError 'nm' " \o Accessor(p) \o " name")
            [] p.function = "absent" -> IF p.op = "set" THEN "AttributeError setter" ELSE "AttributeError deleter"
            [] p.function = "raises" -> "LookupError " \o Call(p)
            [] OTHER -> "None " \o Call(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The function's own result never comes back.
ReturnsNone == Done /\ program.op \notin {"doc", "get", "named", "callnamed"} /\ program.function = "returns" => outcome = "None " \o Call(program)
=============================================================================
