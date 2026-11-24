---------------------------- MODULE ContainerRepr ----------------------------
(***************************************************************************)
(* The representation of a container, as PLS-315 25.1.2 specifies a        *)
(* list's (a tuple's, dict's and set's alike): the reprs of its items in   *)
(* order, each by its type's __repr__, of                                  *)
(*                                                                         *)
(*     class C:                                                            *)
(*         def __repr__(self): return "c"                     function     *)
(*         __repr__ = staticmethod(lambda: "s")               static       *)
(*         __repr__ = staticmethod(lambda: 1 // 0)            raises       *)
(*                                                         (none: object's)*)
(*                                                                         *)
(* in [C(), 1], (C(), 1), {1: C()} or {C()}, or when sub in an instance   *)
(* of class Sub(list) (tuple, dict, set) holding the same, whose repr a    *)
(* set's subclass's names Sub, nested in a list when nested, shown by      *)
(* repr(), str(), an f-string, str.format, %, ascii(), repr() through a    *)
(* starred call, or format() with an empty spec; each __repr__             *)
(* loops and logs its call. The outcome is the text, the default repr      *)
(* written <C>, or ZeroDivisionError, and the number of calls.             *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [repr : {"function", "static", "raises", "none"}, container : {"list", "tuple", "dict", "set"},
             sub : BOOLEAN, nested : BOOLEAN, via : {"repr", "str", "fstring", "format", "percent", "ascii", "starred", "format_empty"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<>>

Item(p) == CASE p.repr = "function" -> "c" [] p.repr = "static" -> "s" [] OTHER -> "<C>"

Shown(p) == LET i == Item(p)
                t == CASE p.container = "list" -> "[" \o i \o ", 1]"
                       [] p.container = "tuple" -> "(" \o i \o ", 1)"
                       [] p.container = "dict" -> "{1: " \o i \o "}"
                       [] p.sub -> "Sub({" \o i \o "})"
                       [] OTHER -> "{" \o i \o "}"
            IN  IF p.nested THEN "[" \o t \o "]" ELSE t

Run(p) == <<IF p.repr = "raises" THEN "ZeroDivisionError" ELSE Shown(p), IF p.repr = "none" THEN 0 ELSE 1>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Each item's __repr__ runs once, every way of showing the container alike.
CalledOnce == Done => outcome[2] = (IF program.repr = "none" THEN 0 ELSE 1)
SameEveryWay == Done => \A q \in Programs :
    (q.repr = program.repr /\ q.container = program.container /\ q.sub = program.sub /\ q.nested = program.nested) => Run(q) = outcome
=============================================================================
