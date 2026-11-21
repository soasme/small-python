---------------------------- MODULE SuperBinding ----------------------------
(***************************************************************************)
(* Binding an unbound super object of a subclass of super, as 20.3.2       *)
(* specifies it after The Python Library Reference                         *)
(* (library/functions.html#super) and CPython's super_descr_get: a super   *)
(* object is a non-data descriptor, and a read through an instance binds   *)
(* an unbound one of a subclass S by calling S with its __thisclass__ and  *)
(* the instance; a read through the class gives it unchanged.              *)
(*                                                                         *)
(*     class S(super): __init__ records, then calls super().__init__      *)
(*     class B: x = S(B)          class A(B): pass         a = A()         *)
(*                                                                         *)
(* S's __init__, which loops, records its arguments, and when raises is   *)
(* set raises AttributeError for the binding call; B may have a           *)
(* __getattr__, which loops and returns 'fallback'; a's dictionary may    *)
(* hold x. The program reads a.x, getattr(a, "x"), getattr(a, "x",       *)
(* "dflt"), hasattr(a, "x"), object.__getattribute__(a, "x") or A.x. The  *)
(* outcome is the value, S(B, a) for the bound S, D for the unbound one,  *)
(* or the AttributeError, which names x unless object.__getattribute__   *)
(* was called.                                                             *)
(***************************************************************************)
EXTENDS Naturals

Ops == {"get", "getattr", "getattrd", "hasattr", "objget", "classget"}
Programs == [op : Ops, dict : BOOLEAN, raises : BOOLEAN, fallback : BOOLEAN]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* The instance dictionary wins over a non-data descriptor; else the
\* binding call, whose AttributeError __getattr__ answers, except for
\* object.__getattribute__, which calls no __getattr__.
Read(p) == CASE p.dict -> "'inst'"
             [] ~p.raises -> "S(B, a)"
             [] p.fallback /\ p.op # "objget" -> "'fallback'"
             [] p.op = "objget" -> "AttributeError"
             [] OTHER -> "AttributeError x"

Run(p) == CASE p.op = "classget" -> "D"
            [] p.op = "getattrd" -> IF Read(p) = "AttributeError x" THEN "'dflt'" ELSE Read(p)
            [] p.op = "hasattr" -> IF Read(p) = "AttributeError x" THEN "False" ELSE "True"
            [] OTHER -> Read(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A read through the class never calls S.
ClassUnbound == Done /\ program.op = "classget" => outcome = "D"

\* A read through the instance binds S unless the dictionary answers.
InstanceBinds == Done /\ program.op = "get" /\ ~program.dict /\ ~program.raises => outcome = "S(B, a)"
=============================================================================
