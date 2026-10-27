------------------------------- MODULE SeqOps -------------------------------
(***************************************************************************)
(* Sequence operations that do not mutate, as The Python Language          *)
(* Reference specifies them (reference/datamodel.html#sequences and        *)
(* #immutable-sequences, library/stdtypes.html#common-sequence-operations  *)
(* and #tuples): len and the indexes 0..n-1, negative indexes counted from *)
(* the end and IndexError beyond; slices with defaults, clamping, and a    *)
(* step (not zero) of the same type; an item of a str is a str of length   *)
(* one, of bytes an int; in, count, index; concatenation of the same type  *)
(* only; repetition, empty for counts below one; immutable sequences are  *)
(* hashable (given hashable items) and mutable ones are not.               *)
(*                                                                         *)
(* A program is a sequence of up to three items, each 1 or 2, as a str     *)
(* ("a", "b"), tuple, bytes, list, or bytearray, and one of                *)
(*                                                                         *)
(*     s[i]  for i in -4..3        s[start:stop:step]                      *)
(*     x in s  s.count(x)  s.index(x)  for x 1 (present or not) or 3        *)
(*     s + <2> (same type)  s + [2] (a list)   s * n  for n in -1..2       *)
(*     hash(s)                                                             *)
(*                                                                         *)
(* The outcome is the result as <<kind, type, items>>, or the exception.   *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Types == {"str", "tuple", "bytes", "list", "bytearray"}
Items == UNION {[1..n -> {1, 2}] : n \in 0..3}
None == 99   \* a missing start, stop, or step
Steps == {None, 1, 2, -1, -2, 0}
Op == {[op |-> "index", i |-> i] : i \in -4..3}
      \cup {[op |-> "slice", start |-> a, stop |-> b, step |-> c] : a \in {None, -4, -1, 0, 2, 4}, b \in {None, -4, -1, 0, 2, 4}, c \in Steps}
      \cup {[op |-> o, x |-> x] : o \in {"in", "count", "find"}, x \in {1, 3}}
      \cup {[op |-> o] : o \in {"concat", "concat list", "hash"}}
      \cup {[op |-> "repeat", n |-> n] : n \in -1..2}
Programs == {[type |-> t, items |-> s] @@ o : t \in Types, s \in Items, o \in Op}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", "", <<>>>>
Error(name) == <<name, "", <<>>>>

\* PySlice_AdjustIndices: the slice's indexes into a sequence of length n.
Clamp(v, n, step, default) ==
    IF v = None THEN default
    ELSE LET w == IF v < 0 THEN v + n ELSE v
         IN  CASE w < 0 -> IF step < 0 THEN -1 ELSE 0
               [] w >= n -> IF step < 0 THEN n - 1 ELSE n
               [] OTHER -> w
RECURSIVE Walk(_, _, _)
Walk(i, stop, step) ==
    IF (step > 0 /\ i < stop) \/ (step < 0 /\ i > stop) THEN <<i>> \o Walk(i + step, stop, step) ELSE <<>>
Indexes(n, p) ==
    LET step == IF p.step = None THEN 1 ELSE p.step
        start == Clamp(p.start, n, step, IF step < 0 THEN n - 1 ELSE 0)
        stop == Clamp(p.stop, n, step, IF step < 0 THEN -1 ELSE n)
    IN  Walk(start, stop, step)

RECURSIVE Count(_, _)
Count(s, x) == IF s = <<>> THEN 0 ELSE (IF Head(s) = x THEN 1 ELSE 0) + Count(Tail(s), x)
RECURSIVE Repeat(_, _)
Repeat(s, n) == IF n <= 0 THEN <<>> ELSE s \o Repeat(s, n - 1)
First(s, x) == CHOOSE k \in DOMAIN s : s[k] = x /\ \A j \in 1..(k - 1) : s[j] # x

Run(p) ==
    LET s == p.items  n == Len(s)  t == p.type
        Result(items) == <<"seq", t, items>>
    IN  CASE p.op = "index" -> LET k == IF p.i < 0 THEN p.i + n ELSE p.i
                               IN  IF k < 0 \/ k >= n THEN Error("IndexError")
                                   ELSE <<"item", IF t = "str" THEN "str" ELSE "int", <<s[k + 1]>>>>
          [] p.op = "slice" -> IF p.step = 0 THEN Error("ValueError")
                               ELSE LET ks == Indexes(n, p) IN Result([j \in DOMAIN ks |-> s[ks[j] + 1]])
          [] p.op = "in" -> <<"bool", "", <<IF Count(s, p.x) > 0 THEN 1 ELSE 0>>>>
          [] p.op = "count" -> <<"int", "", <<Count(s, p.x)>>>>
          [] p.op = "find" -> IF Count(s, p.x) = 0 THEN Error("ValueError") ELSE <<"int", "", <<First(s, p.x) - 1>>>>
          [] p.op = "concat" -> Result(Append(s, 2))
          [] p.op = "concat list" -> IF t = "list" THEN Result(Append(s, 2)) ELSE Error("TypeError")
          [] p.op = "repeat" -> Result(Repeat(s, p.n))
          [] p.op = "hash" -> IF t \in {"list", "bytearray"} THEN Error("TypeError") ELSE <<"hashable", "", <<>>>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A slice is a sequence of the same type, never longer.
SliceType == Done /\ program.op = "slice" /\ outcome[1] = "seq" =>
    outcome[2] = program.type /\ Len(outcome[3]) <= Len(program.items)

\* s[i] for i in range(len(s)) are the items, as is the full slice.
FullSlice == Done /\ program.op = "slice" /\ program.start = None /\ program.stop = None /\ program.step = None =>
    outcome[3] = program.items

\* A negative step reverses: s[::-1] is s backwards.
Reverse == Done /\ program.op = "slice" /\ program.start = None /\ program.stop = None /\ program.step = -1 =>
    outcome[3] = [k \in DOMAIN program.items |-> program.items[Len(program.items) - k + 1]]
=============================================================================
