---------------------------- MODULE SpecialLookup ----------------------------
(***************************************************************************)
(* Special method lookup, as The Python Language Reference specifies it    *)
(* (reference/datamodel.html#special-method-lookup, and #custom-classes'   *)
(* special methods): implicit invocations look a special method up on the  *)
(* object's type, never its instance dictionary, and bypass                *)
(* __getattribute__; one defined on a metaclass applies to its classes,    *)
(* not their instances; replacing or deleting it on the class takes effect *)
(* at once. Explicit lookup through the instance is ordinary attribute     *)
(* access.                                                                 *)
(*                                                                         *)
(* A program, for M one of __len__, __iter__, __bool__, __call__, __neg__, *)
(* with an implementation giving 5 (iter([5]) and False for __iter__ and   *)
(* __bool__), defines M                                                    *)
(*                                                                         *)
(*     instance   on c = C() only: c.M = lambda: ...                       *)
(*     class      on C             base       on B, with class C(B)        *)
(*     replaced   on C, then C.M = an implementation giving 6 (or True)    *)
(*     deleted    on C, then del C.M                                       *)
(*     metaclass  on Meta, with class C(metaclass=Meta)                    *)
(*                                                                         *)
(* where C may also define __getattribute__ recording the names it looks   *)
(* up, then invokes M implicitly on c (len(c), list(iter(c)), bool(c),     *)
(* c(), -c) or on C, or explicitly as c.M(). The outcome is the result (a  *)
(* list for iterators), or the exception, and whether __getattribute__     *)
(* saw M.                                                                  *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Methods == {"__len__", "__iter__", "__bool__", "__call__", "__neg__"}
Wheres == {"instance", "class", "base", "replaced", "deleted", "metaclass"}
Programs == [method : Methods, where : Wheres, getattribute : BOOLEAN, op : {"implicit", "onclass", "explicit"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* The result of an implementation giving 5 (or 6).
Gives(m, six) == CASE m = "__iter__" -> IF six THEN "[6]" ELSE "[5]"
                   [] m = "__bool__" -> IF six THEN "True" ELSE "False"
                   [] OTHER -> IF six THEN "6" ELSE "5"

\* An implicit invocation on an object whose type does not define M.
Missing(m, onclass) == CASE m = "__bool__" -> "True"                 \* everything is true by default
                         [] m = "__call__" /\ onclass -> "a C"       \* calling a class makes an instance
                         [] OTHER -> "TypeError"

\* Where the object's type has M: the class (or its base) for c, the metaclass for C.
Implicit(p, onclass) ==
    LET found == IF onclass THEN p.where = "metaclass" ELSE p.where \in {"class", "base", "replaced"}
    IN  IF found THEN Gives(p.method, p.where = "replaced") ELSE Missing(p.method, onclass)

\* c.M through ordinary attribute access: instance dict, then the class.
Explicit(p) == IF p.where \in {"deleted", "metaclass"} THEN "AttributeError" ELSE Gives(p.method, p.where = "replaced")

Run(p) ==
    CASE p.op = "implicit" -> Implicit(p, FALSE) \o " seen=False"
      [] p.op = "onclass" -> Implicit(p, TRUE) \o " seen=False"
      \* A metaclass __call__ giving 5 makes c the int 5, which has no __getattribute__ of C's.
      [] p.op = "explicit" -> Explicit(p) \o " seen=" \o
                              (IF p.getattribute /\ ~(p.where = "metaclass" /\ p.method = "__call__") THEN "True" ELSE "False")

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* An instance attribute never serves an implicit invocation.
InstanceIgnored == Done /\ program.op = "implicit" /\ program.where = "instance" =>
    outcome = Missing(program.method, FALSE) \o " seen=False"
=============================================================================
