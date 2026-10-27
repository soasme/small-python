---------------------------- MODULE ClassObjects ----------------------------
(***************************************************************************)
(* Custom classes and class instances, as The Python Language Reference    *)
(* specifies them (reference/datamodel.html#custom-classes and #class-     *)
(* instances, with their special attributes): a class's name, qualified    *)
(* name, module, read-only namespace view, bases (Generic added for type   *)
(* parameters), layout base, documentation (not inherited), annotations,   *)
(* type parameters, static attributes, first line, and MRO;                *)
(* __subclasses__; class attribute assignment changes the class's own      *)
(* dictionary, never a base's, and instance assignment the instance's.     *)
(*                                                                         *)
(* A program, in module m, defines  class A: w = 0  and  class B: pass  on *)
(* lines 1 and 2, then class C on line 3 (or nested in def f on line 3,    *)
(* so on line 4) with bases from                                           *)
(*                                                                         *)
(*     (none)   A   A, B   A, int   int                                    *)
(*                                                                         *)
(* optionally a docstring, an annotation x: int, and a type parameter T;   *)
(* its method m assigns self.b and self.a. It reads one attribute of C, or *)
(* does one of: C.__dict__["x"] = 1; D(C).__doc__; A.__subclasses__();    *)
(* C.w = 1 then A.w; c.w = 5 then C.w; c.z = 1 then c.__dict__;            *)
(* c.__class__.                                                            *)
(*                                                                         *)
(* The outcome is the result, classes by name, or the exception.           *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Bases == {<<>>, <<"A">>, <<"A", "B">>, <<"A", "int">>, <<"int">>}
Reads == {"__name__", "__qualname__", "__module__", "__dict__", "__bases__", "__base__", "__doc__", "__annotations__",
          "__annotate__", "__type_params__", "__static_attributes__", "__firstlineno__", "__mro__"}
Ops == {"dictwrite", "subdoc", "subclasses", "classset", "instanceset", "instancedict", "class"}
Programs == [bases : Bases, doc : BOOLEAN, ann : BOOLEAN, generic : BOOLEAN, nested : BOOLEAN, op : {"read"}, attr : Reads]
            \cup [bases : Bases, doc : BOOLEAN, ann : BOOLEAN, generic : BOOLEAN, nested : BOOLEAN, op : Ops]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

RECURSIVE Join(_)
Join(s) == CASE s = <<>> -> "" [] Len(s) = 1 -> s[1] [] OTHER -> s[1] \o ", " \o Join(Tail(s))
Tuple(s) == IF Len(s) = 1 THEN "(" \o s[1] \o ",)" ELSE "(" \o Join(s) \o ")"

\* The bases as written, with Generic after them for a type parameter.
AllBases(p) == LET b == IF p.generic THEN p.bases \o <<"Generic">> ELSE p.bases IN IF b = <<>> THEN <<"object">> ELSE b
\* The base with the instance layout: int, if it is a base, else the first.
Base(p) == IF \E i \in DOMAIN p.bases : p.bases[i] = "int" THEN "int" ELSE AllBases(p)[1]
Mro(p) == <<"C">> \o (IF p.bases = <<>> /\ ~p.generic THEN <<>> ELSE AllBases(p)) \o <<"object">>

Read(p, a) ==
    CASE a = "__name__" -> "'C'"
      [] a = "__qualname__" -> IF p.nested THEN "'f.<locals>.C'" ELSE "'C'"
      [] a = "__module__" -> "'m'"
      [] a = "__dict__" -> "mappingproxy"
      [] a = "__bases__" -> Tuple(AllBases(p))
      [] a = "__base__" -> Base(p)
      [] a = "__doc__" -> IF p.doc THEN "'doc'" ELSE "None"
      [] a = "__annotations__" -> IF p.ann THEN "{'x': int}" ELSE "{}"
      [] a = "__annotate__" -> IF p.ann THEN "function" ELSE "None"
      [] a = "__type_params__" -> IF p.generic THEN "(T,)" ELSE "()"
      [] a = "__static_attributes__" -> "('a', 'b')"
      [] a = "__firstlineno__" -> IF p.nested THEN "4" ELSE "3"
      [] a = "__mro__" -> Tuple(Mro(p))

HasA(p) == \E i \in DOMAIN p.bases : p.bases[i] = "A"
Run(p) ==
    IF p.op = "read" THEN Read(p, p.attr)
    ELSE CASE p.op = "dictwrite" -> "TypeError"                   \* a read-only view
           [] p.op = "subdoc" -> "None"                            \* not inherited
           [] p.op = "subclasses" -> IF HasA(p) THEN "[C]" ELSE "[]"
           [] p.op = "classset" -> "0"                          \* A.w is untouched
           [] p.op = "instanceset" -> IF HasA(p) THEN "0" ELSE "AttributeError"
           [] p.op = "instancedict" -> "{'z': 1}"
           [] p.op = "class" -> "C"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The layout base is one of the bases.
BaseIsBase == Done /\ program.op = "read" /\ program.attr = "__base__" =>
    \E i \in DOMAIN AllBases(program) : AllBases(program)[i] = outcome
=============================================================================
