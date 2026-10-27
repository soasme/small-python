----------------------------- MODULE Descriptors -----------------------------
(***************************************************************************)
(* Descriptors, as The Python Language Reference specifies them            *)
(* (reference/datamodel.html#implementing-descriptors and #descriptor-     *)
(* invocation): an object with any of __get__, __set__, and __delete__ in  *)
(* a class dictionary is a descriptor; one with __set__ or __delete__ is a *)
(* data descriptor, which takes precedence over the instance dictionary,   *)
(* while a non-data descriptor's __get__ runs only when the instance       *)
(* dictionary lacks the name, and a descriptor without __get__ is returned *)
(* itself. Instance binding calls __get__(a, type(a)), class binding       *)
(* __get__(None, A), super binding __get__(a, A) for the class after A;    *)
(* assignment and deletion call __set__ and __delete__ (an AttributeError  *)
(* when a data descriptor lacks the one needed) or change the instance     *)
(* dictionary; assigning through the class replaces the descriptor.        *)
(*                                                                         *)
(* A program defines a descriptor class D with the methods in METHODS,     *)
(* each recording its arguments, then                                      *)
(*                                                                         *)
(*     class B: x = D()          class A(B): pass  (or x = 999, for super) *)
(*     a = A()                   and, if dict, a.__dict__["x"] = "inst"    *)
(*                                                                         *)
(* and does a.x, A.x, super(A, a).x, B.__dict__["x"].__get__(a),           *)
(* a.x = 1, del a.x, or A.x = 1. The outcome is the result (a descriptor   *)
(* call as get(instance, owner), set(instance, value), or delete(instance);*)
(* the descriptor itself as D) or the exception, then a's dictionary after *)
(* an assignment or deletion (A.__dict__["x"] after A.x = 1).              *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Names == {"get", "set", "delete"}
Ops == {"get", "classget", "superget", "direct", "set", "del", "classset"}
Programs == [methods : SUBSET Names, dict : BOOLEAN, op : Ops]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Data(p) == "set" \in p.methods \/ "delete" \in p.methods
Has(p, m) == m \in p.methods
Dict(p) == IF p.dict THEN "{'x': 'inst'}" ELSE "{}"

Get(p) == CASE Data(p) /\ Has(p, "get") -> "get(a, A)"                 \* a data descriptor wins
            [] p.dict -> "'inst'"                                      \* then the instance dictionary
            [] Has(p, "get") -> "get(a, A)"
            [] OTHER -> "D"                                            \* no __get__: the descriptor itself

Run(p) ==
    CASE p.op = "get" -> Get(p)
      [] p.op = "classget" -> IF Has(p, "get") THEN "get(None, A)" ELSE "D"
      [] p.op = "superget" -> IF Has(p, "get") THEN "get(a, A)" ELSE "D"
      [] p.op = "direct" -> IF Has(p, "get") THEN "get(a, None)" ELSE "AttributeError"
      [] p.op = "set" -> CASE Has(p, "set") -> "set(a, 1) " \o Dict(p)
                           [] Data(p) -> "AttributeError " \o Dict(p)       \* __delete__ only: no __set__
                           [] OTHER -> "None {'x': 1}"
      [] p.op = "del" -> CASE Has(p, "delete") -> "delete(a) " \o Dict(p)
                           [] Data(p) -> "AttributeError " \o Dict(p)       \* __set__ only: no __delete__
                           [] p.dict -> "None {}"
                           [] OTHER -> "AttributeError {}"
      [] p.op = "classset" -> "None 1"                                 \* the class dictionary changes

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A data descriptor with __get__ overrides the instance dictionary.
DataOverrides == Done /\ program.op = "get" /\ Data(program) /\ Has(program, "get") => outcome = "get(a, A)"

\* The instance dictionary overrides a non-data descriptor.
InstanceOverrides == Done /\ program.op = "get" /\ ~Data(program) /\ program.dict => outcome = "'inst'"
=============================================================================
