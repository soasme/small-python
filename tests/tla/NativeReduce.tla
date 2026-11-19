---------------------------- MODULE NativeReduce ----------------------------
(***************************************************************************)
(* A bytearray's and a set's reduction, as PLS-315 24.2 and 26.3.2 specify *)
(* them, of an instance of                                                 *)
(*                                                                         *)
(*     class C(kind):          kind: bytearray, set, or frozenset          *)
(*         def __getstate__(self): return "S"          when getstate       *)
(*                                     raise ValueError      when raises   *)
(*                                                                         *)
(* made as C(b"a") or C([1]), with o.x = 1 when attr. A bytearray's        *)
(* __reduce_ex__(protocol) and a set's __reduce__() are called as a method *)
(* of o, through kind, or by map() of kind's method over [o].              *)
(*                                                                         *)
(* The outcome is (Type(o), args, state) as repr() shows it, the class     *)
(* written C, or ValueError, and the log of __getstate__ calls: the state  *)
(* is ? Call(? GetAttribute(o, "__getstate__"), « »), object's default the *)
(* instance dict or None (20.1.4).                                         *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Kinds == {"bytearray", "set", "frozenset"}
Programs == {p \in [kind : Kinds, getstate : {"none", "python", "raises"}, attr : BOOLEAN,
                    via : {"method", "type", "map"}, protocol : {0, 3}] :
             p.kind # "bytearray" => p.protocol = 0}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<>>

Args(p) == CASE p.kind # "bytearray" -> "([1],)"
             [] p.protocol < 3 -> "('a', 'latin-1')"
             [] OTHER -> "(b'a',)"

State(p) == CASE p.getstate = "python" -> "'S'"
              [] p.attr -> "{'x': 1}"
              [] OTHER -> "None"

Run(p) == <<IF p.getstate = "raises" THEN "ValueError" ELSE "(C, " \o Args(p) \o ", " \o State(p) \o ")",
            IF p.getstate = "none" THEN <<>> ELSE <<"getstate">>>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A Python __getstate__ is called exactly once, its error the outcome's.
GetstateOnce == Done => (Len(outcome[2]) = 1 <=> program.getstate # "none")
RaisesOnly == Done => (outcome[1] = "ValueError" <=> program.getstate = "raises")

\* How the method is reached changes nothing.
SameEveryWay == Done => \A q \in Programs :
    (q.kind = program.kind /\ q.getstate = program.getstate /\ q.attr = program.attr /\ q.protocol = program.protocol)
        => Run(q) = outcome
=============================================================================
