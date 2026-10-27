----------------------------- MODULE Unpacking -----------------------------
(***************************************************************************)
(* Assignment to a target list, as The Python Language Reference specifies *)
(* it (reference/simple_stmts.html#assignment-statements), for every      *)
(* target list of up to three targets, each a name, a starred name, or a  *)
(* parenthesized pair of names, and every tuple of up to four items, each *)
(* an int, a pair, or a triple:                                            *)
(*                                                                         *)
(*     t1, *s, (u3, v3), = (1, (2, 12), (3, 13, 23))                       *)
(*                                                                         *)
(* Item k is k, (k, k + 10), or (k, k + 10, k + 20); the outcome is what   *)
(* each name is bound to, in order, or the exception.                      *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets, TLC

Targets == {"name", "star", "pair"}
Items == {"int", "pair", "triple"}
Programs == (UNION {[1..n -> Targets] : n \in 1..3}) \X (UNION {[1..n -> Items] : n \in 0..4})

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", <<>>>>
Fail(name) == <<name, <<>>>>

\* Item k's parts, as the tokens the replay writes for values: an int n is
\* "i<n>"; a pair or triple starting with k is "t<k>" or "u<k>".
Token(kind, k) == CASE kind = "int" -> "i" \o ToString(k)
                    [] kind = "pair" -> "t" \o ToString(k)
                    [] kind = "triple" -> "u" \o ToString(k)

Stars(t) == {i \in DOMAIN t : t[i] = "star"}

Assign(p) ==
    LET t == p[1]  v == p[2]  n == Len(t)  m == Len(v)
        star == IF Stars(t) = {} THEN 0 ELSE CHOOSE i \in Stars(t) : TRUE
        \* The item index each target takes (a starred target takes a run).
        first(i) == IF star = 0 \/ i <= star THEN i ELSE i + (m - n)
        nested == {i \in 1..n : t[i] = "pair" /\ v[first(i)] # "pair"}
        firstNested == CHOOSE i \in nested : \A j \in nested : i <= j
        binding(i) ==
            CASE t[i] = "name" -> <<<<Token(v[first(i)], first(i))>>>>
              [] t[i] = "star" -> <<[j \in 1..(m - n + 1) |-> Token(v[star + j - 1], star + j - 1)]>>
              [] t[i] = "pair" -> <<<<Token("int", first(i))>>, <<Token("int", first(i) + 10)>>>>
        RECURSIVE All(_)
        All(i) == IF i > n THEN <<>> ELSE binding(i) \o All(i + 1)
    IN  CASE Cardinality(Stars(t)) > 1 -> Fail("syntax")            \* multiple starred expressions
          [] star = 0 /\ m # n -> Fail("ValueError")                  \* too many or not enough values
          [] star # 0 /\ m < n - 1 -> Fail("ValueError")              \* not enough values
          \* Targets are assigned left to right; the first nested target
          \* whose item is no pair fails: an int cannot be unpacked, a
          \* triple has too many values.
          [] nested # {} -> Fail(IF v[first(firstNested)] = "int" THEN "TypeError" ELSE "ValueError")
          [] OTHER -> <<"ok", All(1)>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Assign(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
Bound == Done /\ outcome[1] = "ok"

\* Without a starred target, a successful assignment takes every item once;
\* a starred target takes exactly the items the others leave.
EveryItemOnce == Bound =>
    LET t == program[1]  sizes == [i \in DOMAIN outcome[2] |-> Len(outcome[2][i])]
        RECURSIVE Sum(_)
        Sum(i) == IF i = 0 THEN 0 ELSE sizes[i] + Sum(i - 1)
        pairs == Cardinality({i \in DOMAIN t : t[i] = "pair"})
    IN  Sum(Len(sizes)) = Len(program[2]) + pairs

\* The starred target always receives a list, possibly empty.
StarAlwaysBound == Bound /\ Stars(program[1]) # {} => Len(outcome[2]) >= Len(program[1])
=============================================================================
