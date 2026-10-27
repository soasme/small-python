---------------------------- MODULE TypeAliases ----------------------------
(***************************************************************************)
(* The type statement, as The Python Language Reference specifies it       *)
(* (reference/simple_stmts.html#the-type-statement and                     *)
(* reference/executionmodel.html#lazy-evaluation): `type A = V` binds A to *)
(* a TypeAliasType whose __value__ is evaluated lazily, when first read    *)
(* (once), so V may name something bound later, including the alias        *)
(* itself, and an unbound name raises NameError only then; the alias       *)
(* knows its __name__, __module__, and __type_params__; only a generic     *)
(* alias can be subscripted; and its attributes other than __module__ are  *)
(* read-only.                                                              *)
(*                                                                         *)
(* A program runs `type A = V` (or `type A[K] = V` when generic) where V   *)
(* names int, a name bound after the statement, a name never bound, or A   *)
(* itself inside list[...]; the evaluating V logs; then reads __value__    *)
(* once or twice, __name__, __module__, or __type_params__, subscripts A   *)
(* with str, takes type(A).__name__, or assigns __value__. The outcome is  *)
(* the result and how many times V was evaluated, or the exception.        *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Values == {"int", "later", "never", "self"}
Queries == {"value", "value2", "name", "module", "params", "subscript", "type", "set"}
Programs == [value : Values, generic : BOOLEAN, query : Queries]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Value(p) == CASE p.value = "never" -> "NameError"
              [] p.value = "self" -> "list[A] 1"
              [] OTHER -> "int 1"                             \* evaluated once, however often read

Run(p) == CASE p.query \in {"value", "value2"} -> Value(p)
            [] p.query = "name" -> "A 0"
            [] p.query = "module" -> "__main__ 0"
            [] p.query = "params" -> IF p.generic THEN "(K,) 0" ELSE "() 0"
            [] p.query = "subscript" -> IF p.generic THEN "A[str] 0" ELSE "TypeError"
            [] p.query = "type" -> "TypeAliasType 0"
            [] p.query = "set" -> "AttributeError"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Only reading __value__ evaluates it.
LazyValue == Done /\ program.query \notin {"value", "value2"} => outcome \in {"TypeError", "AttributeError"} \/
    \E s \in {"A", "__main__", "(K,)", "()", "A[str]", "TypeAliasType"} : outcome = s \o " 0"
=============================================================================
