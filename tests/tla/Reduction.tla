------------------------------ MODULE Reduction ------------------------------
(***************************************************************************)
(* The reduction protocol, as PLS-315 20.1.4 specifies it: what            *)
(* object.__reduce_ex__(protocol) returns for an instance of               *)
(*                                                                         *)
(*     class C(base):          base: object, int, list, or dict            *)
(*         __slots__ = ("s",)            when slots (not for int)          *)
(*         def __getstate__(self): return "S"          when getstate       *)
(*         def __getnewargs__(self): return (7,)       when newargs = args *)
(*         def __getnewargs_ex__(self): return (7,), {}             ex     *)
(*         def __getnewargs_ex__(self): return (7,), {"k": 1}       exkw   *)
(*                                                                         *)
(* made as C(), C(5), C([1]) or C(a=1), with o.s = 2 (slots) or o.x = 1    *)
(* when attr. Below protocol 2, CommonReduce names %Reconstructor% with    *)
(* ReduceBase(o) and its view of o; from protocol 2, ReduceNew names       *)
(* %NewObj% or %NewObjEx% with the new arguments, the state, and the list  *)
(* and dict items.                                                         *)
(*                                                                         *)
(* The outcome is five strings: the function (NewObj, NewObjEx,            *)
(* Reconstructor, or TypeError), then the remaining items as repr() shows  *)
(* them, the class written C, a base class by its name, an iterator by the *)
(* list of what it yields, and "absent" past the end of a shorter tuple.   *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Bases == {"object", "int", "list", "dict"}
Programs == {p \in [base : Bases, slots : BOOLEAN, attr : BOOLEAN, getstate : BOOLEAN,
                    newargs : {"none", "args", "ex", "exkw"}, protocol : {0, 1, 2, 4}] :
             ~(p.base = "int" /\ p.slots)}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<>>

\* Call(base, o): the instance as its first built-in base sees it.
BaseView(b) == CASE b = "object" -> "None" [] b = "int" -> "5" [] b = "list" -> "[1]" [] b = "dict" -> "{'a': 1}"

\* The instance namespace, None when empty (DefaultState step 2).
Namespace(p) == IF p.attr /\ ~p.slots THEN "{'x': 1}" ELSE "None"

\* CommonReduce: a class with true __slots__ and object.__getstate__ fails.
Common(p) ==
    IF p.slots /\ ~p.getstate THEN <<"TypeError", "absent", "absent", "absent", "absent">>
    ELSE LET d == IF p.getstate THEN "'S'" ELSE IF p.attr /\ ~p.slots THEN "{'x': 1}" ELSE "absent"
         IN  <<"Reconstructor", "(C, " \o p.base \o ", " \o BaseView(p.base) \o ")", d, "absent", "absent">>

\* ReduceNew: __getnewargs_ex__ first, then __getnewargs__ (int has one).
New(p) ==
    LET fargs == CASE p.newargs \in {"args", "ex"} -> "(C, 7)"
                   [] p.newargs = "exkw" -> "(C, (7,), {'k': 1})"
                   [] p.base = "int" -> "(C, 5)"
                   [] OTHER -> "(C,)"
        slots == p.slots /\ p.attr
        state == CASE p.getstate -> "'S'"
                   [] slots -> "(" \o Namespace(p) \o ", {'s': 2})"
                   [] OTHER -> Namespace(p)
    IN  <<IF p.newargs = "exkw" THEN "NewObjEx" ELSE "NewObj", fargs, state,
          IF p.base = "list" THEN "[1]" ELSE "None",
          IF p.base = "dict" THEN "[('a', 1)]" ELSE "None">>

Run(p) == IF p.protocol >= 2 THEN New(p) ELSE Common(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* %NewObj% and %NewObjEx% exactly from protocol 2.
NewFromTwo == Done => (outcome[1] \in {"NewObj", "NewObjEx"} <=> program.protocol >= 2)

\* Only slots without a __getstate__ of their own fail, and only below 2.
FailsOnlyForSlots == Done /\ outcome[1] = "TypeError" =>
    program.slots /\ ~program.getstate /\ program.protocol < 2

\* Keyword arguments to __new__ need %NewObjEx%.
KeywordsNeedEx == Done /\ outcome[1] = "NewObjEx" => program.newargs = "exkw"

\* The list and dict items come only from list and dict instances.
ItemsFromContainers == Done =>
    /\ (outcome[4] \notin {"None", "absent"} => program.base = "list")
    /\ (outcome[5] \notin {"None", "absent"} => program.base = "dict")
=============================================================================
