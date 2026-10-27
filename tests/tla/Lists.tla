------------------------------- MODULE Lists -------------------------------
(***************************************************************************)
(* Mutable sequences, as The Python Language Reference specifies them      *)
(* (reference/datamodel.html#mutable-sequences, library/stdtypes.html#     *)
(* mutable-sequence-types and #lists): item and slice assignment and del,  *)
(* where a slice with a step other than 1 must be replaced by as many      *)
(* items as it selects (a bytearray's takes none as del); += and *= (a    *)
(* count below one clears); and the                                        *)
(* methods append, clear, copy, extend, insert (its index clamped to the   *)
(* sequence), pop, remove, and reverse.                                    *)
(*                                                                         *)
(* A program is a list or bytearray of up to three items, each 1 or 2, and *)
(* one of                                                                  *)
(*                                                                         *)
(*     s[i] = 7, del s[i]                    i in -4..3                    *)
(*     s[start:stop:step] = t, del s[...]    t: up to two of 7, 8          *)
(*     s += t   s *= n   s.append(7)   s.clear()   s.copy()   s.extend(t)  *)
(*     s.insert(i, 7)   s.pop()   s.pop(i)   s.remove(x)   s.reverse()     *)
(*                                                                         *)
(* The outcome is what the operation returns and s's items afterwards, or  *)
(* the exception.                                                          *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Types == {"list", "bytearray"}
Items == UNION {[1..n -> {1, 2}] : n \in 0..3}
Values == UNION {[1..n -> {7, 8}] : n \in 0..2}
None == 99   \* a missing start, stop, step, or index
Bounds == {None, -1, 0, 2, 4}
Op == {[op |-> o, i |-> i] : o \in {"set", "del", "insert"}, i \in -4..3}
      \cup {[op |-> "pop", i |-> i] : i \in {None, -4, -1, 0, 2, 3}}
      \cup {[op |-> "setslice", start |-> a, stop |-> b, step |-> c, t |-> t] :
              a \in Bounds, b \in Bounds, c \in {None, 1, 2, -1}, t \in Values}
      \cup {[op |-> "delslice", start |-> a, stop |-> b, step |-> c] : a \in Bounds, b \in Bounds, c \in {None, 1, 2, -1}}
      \cup {[op |-> o, t |-> t] : o \in {"iadd", "extend"}, t \in Values}
      \cup {[op |-> "imul", n |-> n] : n \in -1..2}
      \cup {[op |-> "remove", x |-> x] : x \in {1, 3}}
      \cup {[op |-> o] : o \in {"append", "clear", "copy", "reverse"}}
Programs == {[type |-> t, items |-> s] @@ o : t \in Types, s \in Items, o \in Op}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", 0, <<>>>>
Error(name) == <<name, 0, <<>>>>
Done(items) == <<"None", 0, items>>

Clamp(v, n, step, default) ==
    IF v = None THEN default
    ELSE LET w == IF v < 0 THEN v + n ELSE v
         IN  CASE w < 0 -> IF step < 0 THEN -1 ELSE 0
               [] w >= n -> IF step < 0 THEN n - 1 ELSE n
               [] OTHER -> w
RECURSIVE Walk(_, _, _)
Walk(i, stop, step) ==
    IF (step > 0 /\ i < stop) \/ (step < 0 /\ i > stop) THEN <<i>> \o Walk(i + step, stop, step) ELSE <<>>
Step(p) == IF p.step = None THEN 1 ELSE p.step
Start(n, p) == Clamp(p.start, n, Step(p), IF Step(p) < 0 THEN n - 1 ELSE 0)
Stop(n, p) == Clamp(p.stop, n, Step(p), IF Step(p) < 0 THEN -1 ELSE n)

\* s without the items at the (0-based) indexes in ks.
Without(s, ks) == LET keep == {k \in DOMAIN s : k - 1 \notin {ks[j] : j \in DOMAIN ks}}
                      RECURSIVE F(_)
                      F(k) == IF k > Len(s) THEN <<>> ELSE (IF k \in keep THEN <<s[k]>> ELSE <<>>) \o F(k + 1)
                  IN  F(1)
\* s[a:b] replaced by t, for 0 <= a <= n.
Splice(s, a, b, t) == SubSeq(s, 1, a) \o t \o SubSeq(s, (IF b < a THEN a ELSE b) + 1, Len(s))
RECURSIVE Repeat(_, _)
Repeat(s, n) == IF n <= 0 THEN <<>> ELSE s \o Repeat(s, n - 1)
First(s, x) == CHOOSE k \in DOMAIN s : s[k] = x /\ \A j \in 1..(k - 1) : s[j] # x

Run(p) ==
    LET s == p.items  n == Len(s)
        Index(i) == IF i < 0 THEN i + n ELSE i
    IN  CASE p.op = "set" -> IF Index(p.i) < 0 \/ Index(p.i) >= n THEN Error("IndexError") ELSE Done([s EXCEPT ![Index(p.i) + 1] = 7])
          [] p.op = "del" -> IF Index(p.i) < 0 \/ Index(p.i) >= n THEN Error("IndexError") ELSE Done(Without(s, <<Index(p.i)>>))
          [] p.op = "setslice" /\ Step(p) = 1 -> Done(Splice(s, Start(n, p), Stop(n, p), p.t))
          [] p.op = "setslice" /\ p.type = "bytearray" /\ p.t = <<>> -> Done(Without(s, Walk(Start(n, p), Stop(n, p), Step(p))))
          [] p.op = "setslice" ->
                LET ks == Walk(Start(n, p), Stop(n, p), Step(p))
                IN  IF Len(ks) # Len(p.t) THEN Error("ValueError")
                    ELSE Done([k \in DOMAIN s |-> IF \E j \in DOMAIN ks : ks[j] = k - 1
                                                   THEN p.t[CHOOSE j \in DOMAIN ks : ks[j] = k - 1] ELSE s[k]])
          [] p.op = "delslice" /\ Step(p) = 1 -> Done(Splice(s, Start(n, p), Stop(n, p), <<>>))
          [] p.op = "delslice" -> Done(Without(s, Walk(Start(n, p), Stop(n, p), Step(p))))
          [] p.op \in {"iadd", "extend"} -> Done(s \o p.t)
          [] p.op = "imul" -> Done(Repeat(s, p.n))
          [] p.op = "append" -> Done(Append(s, 7))
          [] p.op = "clear" -> Done(<<>>)
          [] p.op = "copy" -> <<"copy", 0, s>>                       \* a new sequence with the same items
          [] p.op = "reverse" -> Done([k \in DOMAIN s |-> s[n - k + 1]])
          [] p.op = "insert" -> LET i == IF Index(p.i) < 0 THEN 0 ELSE IF Index(p.i) > n THEN n ELSE Index(p.i)
                                IN  Done(Splice(s, i, i, <<7>>))
          [] p.op = "pop" -> LET i == IF p.i = None THEN n - 1 ELSE Index(p.i)
                             IN  IF n = 0 \/ i < 0 \/ i >= n THEN Error("IndexError") ELSE <<"item", s[i + 1], Without(s, <<i>>)>>
          [] p.op = "remove" -> IF \A k \in DOMAIN s : s[k] # p.x THEN Error("ValueError")
                                ELSE Done(Without(s, <<First(s, p.x) - 1>>))

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Finished == outcome # Pending

\* del s[i:j] is s[i:j] = [].
DelIsEmptyAssignment == Finished /\ program.op = "delslice" /\ program.step \in {None, 1} =>
    outcome = Run([type |-> program.type, items |-> program.items, op |-> "setslice", start |-> program.start,
                   stop |-> program.stop, step |-> program.step, t |-> <<>>])

\* append(x) is s[len(s):len(s)] = [x].
AppendIsSlice == Finished /\ program.op = "append" =>
    outcome = Run([type |-> program.type, items |-> program.items, op |-> "setslice", start |-> Len(program.items),
                   stop |-> Len(program.items), step |-> None, t |-> <<7>>])
=============================================================================
