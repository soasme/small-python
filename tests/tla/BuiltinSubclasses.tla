-------------------------- MODULE BuiltinSubclasses --------------------------
(***************************************************************************)
(* Built-in classes' __new__, as The Python Language Reference specifies   *)
(* it (reference/datamodel.html#object.__new__) and the Built-in Types      *)
(* chapter the classes (library/stdtypes.html): a subclass of int, str,    *)
(* bytes, tuple or frozenset whose __new__ is its base's builds the value  *)
(* the base's own call of the arguments would, each conversion method      *)
(* running once, and holds it; its __init__ receives the original          *)
(* arguments. bytearray's __new__ makes an empty array, which its __init__ *)
(* fills as bytearray() would.                                             *)
(*                                                                         *)
(* A program defines class C of base T, and x whose class defines          *)
(*                                                                         *)
(*     kind   index (__index__ returning 2) | iter (__iter__ giving 3, 1)  *)
(*            | raise (__index__ and __iter__ raising KeyError)            *)
(*                                                                         *)
(* and __repr__ (returning 'X', raising KeyError for raise), each logging  *)
(* its name; then evaluates C(x), C(x) for a C whose __init__ logs init    *)
(* when given x, C(x) for a C whose __new__ returns super().__new__ of the *)
(* class and its arguments, C(x) for a C whose metaclass's __call__        *)
(* returns super().__call__ of its arguments, or list(map(C, [x]))[0]. The *)
(* outcome is the result's class and value (a list of its items, sorted    *)
(* for a frozenset, or the repr of an int or str), or the exception, and   *)
(* the calls logged.                                                       *)
(***************************************************************************)
EXTENDS Sequences

Programs == [base : {"int", "str", "bytes", "tuple", "frozenset", "bytearray"}, kind : {"index", "iter", "raise"},
             how : {"call", "init", "new", "meta", "map"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* The method of x that T(x) calls, or "" when none applies: str() the
\* __repr__, int() the __index__, tuple() and frozenset() the __iter__,
\* bytes() and bytearray() the __index__ before iterating.
Calls(b, k) == CASE b = "str" -> "repr"
                 [] b = "int" -> IF k = "iter" THEN "" ELSE "index"
                 [] b \in {"tuple", "frozenset"} -> IF k = "index" THEN "" ELSE "iter"
                 [] OTHER -> IF k = "iter" THEN "iter" ELSE "index"
\* What T(x) gives, or the exception.
Value(b, k) == CASE k = "raise" -> "KeyError"
                 [] Calls(b, k) = "" -> "TypeError"
                 [] b = "int" -> "2"
                 [] b = "str" -> "'X'"
                 [] k = "index" -> "[0, 0]"
                 [] b = "frozenset" -> "[1, 3]"
                 [] OTHER -> "[3, 1]"
Failed(v) == v \in {"KeyError", "TypeError"}
Log(p) == Calls(p.base, p.kind) \o (IF p.how = "init" /\ ~Failed(Value(p.base, p.kind)) THEN ",init" ELSE "")

Run(p) ==
    \* bytearray's own __init__, which a Python one replaces, fills it.
    IF p.how = "init" /\ p.base = "bytearray" THEN "C [];init"
    ELSE LET v == Value(p.base, p.kind) IN (IF Failed(v) THEN v ELSE "C " \o v) \o ";" \o Log(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The base's __new__, called by the class, its metaclass's super().__call__
\* or map(), or by a Python __new__, builds the value the same way.
SameBuild == Done /\ program.how \in {"new", "meta", "map"} => outcome = Run([program EXCEPT !.how = "call"])
\* A Python __init__ runs only on a built instance.
InitBuilt == Done /\ program.how = "init" /\ program.base # "bytearray" =>
             (outcome = Run([program EXCEPT !.how = "call"]) \o ",init" <=> ~Failed(Value(program.base, program.kind)))
=============================================================================
