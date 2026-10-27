------------------------------ MODULE Objects ------------------------------
(***************************************************************************)
(* Objects, values and types, as The Python Language Reference specifies   *)
(* them (reference/datamodel.html#objects-values-and-types): every object  *)
(* has an identity, which never changes and which is and id() compare; a   *)
(* type, which never changes; and a value, which mutable objects can       *)
(* change. Each [] is a new, unique list; e = f = [] assigns the same      *)
(* object to both. An immutable container's value changes when a mutable   *)
(* object it holds changes, though its contents cannot.                    *)
(*                                                                         *)
(* A program starts with  a = []; b = []; a0 = a; t = (a,)  and runs up to *)
(* four of                                                                 *)
(*                                                                         *)
(*     new a     a = []            push a    a.append(1)                   *)
(*     new b     b = []            push b    b.append(1)                   *)
(*     alias     b = a             wrap      t = (a,)                      *)
(*     retype    a.__class__ = tuple   (TypeError; nothing changes)         *)
(*                                                                         *)
(* The outcome is  (a is b, id(a) == id(b), a == b, len(a), len(b),        *)
(* a is a0, len(t[0]), t[0] is a, type(a) is list).                        *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Ops == {"new a", "new b", "alias", "push a", "push b", "wrap", "retype"}
Programs == UNION {[1..n -> Ops] : n \in 0..4}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<>>

(***************************************************************************)
(* The heap: lists numbered from 1, each with its length. a, b, a0, and    *)
(* the tuple's item name lists.                                            *)
(***************************************************************************)
Start == [heap |-> <<0, 0>>, a |-> 1, b |-> 2, a0 |-> 1, t |-> 1]
New(s) == Append(s.heap, 0)
Push(s, x) == [s.heap EXCEPT ![x] = @ + 1]
Step(s, op) ==
    CASE op = "new a" -> [s EXCEPT !.heap = New(s), !.a = Len(s.heap) + 1]
      [] op = "new b" -> [s EXCEPT !.heap = New(s), !.b = Len(s.heap) + 1]
      [] op = "alias" -> [s EXCEPT !.b = s.a]
      [] op = "push a" -> [s EXCEPT !.heap = Push(s, s.a)]
      [] op = "push b" -> [s EXCEPT !.heap = Push(s, s.b)]
      [] op = "wrap" -> [s EXCEPT !.t = s.a]
      [] op = "retype" -> s
RECURSIVE Steps(_, _)
Steps(s, p) == IF p = <<>> THEN s ELSE Steps(Step(s, Head(p)), Tail(p))

Run(p) ==
    LET s == Steps(Start, p)
    IN  <<s.a = s.b, s.a = s.b, s.heap[s.a] = s.heap[s.b], s.heap[s.a], s.heap[s.b],
          s.a = s.a0, s.heap[s.t], s.t = s.a, TRUE>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* is and id() agree.
IdIs == Done => outcome[1] = outcome[2]

\* The same object has the same value.
SameValue == Done /\ outcome[1] => outcome[3]

\* A type never changes.
TypeFixed == Done => outcome[9]
=============================================================================
