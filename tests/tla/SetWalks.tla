------------------------------ MODULE SetWalks ------------------------------
(***************************************************************************)
(* Which entries the set operations of two sets compare, as PLS-315 26.3.2 *)
(* states it: each lookup compares the searched set's entries with the key *)
(* until one is equal, the entry's __eq__ called; | adds each entry of the *)
(* right set to the left's copy, which an empty left set copies, comparing *)
(* none; & looks the entries of the smaller set, the right when as large,  *)
(* up in the other and adds each found to the result after looking it up   *)
(* there; - looks the left's entries up in the right and adds each missing *)
(* one likewise; ^ discards the left's entries from the right's copy or    *)
(* adds a missing one after another lookup; -= and difference_update       *)
(* discard the right's entries from the set, ^= discards them or adds      *)
(* them; the comparisons look the subset side's entries up in the other,   *)
(* isdisjoint the smaller's, the right's when as large, until one decides. *)
(*                                                                         *)
(* A program takes a set or frozenset a and a set b of at most two of the  *)
(* values 1, 2, 3, each element an object of one hash whose Python __eq__  *)
(* logs its side and value, and applies an operator, an augmented          *)
(* assignment, or a method; an operator's special method called by name    *)
(* gives the operator's outcome. The outcome is the result's values, a's   *)
(* after an update, or the bool, then the log.                             *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

Values == <<"1", "2", "3">>
Small == {s \in SUBSET {1, 2, 3} : Cardinality(s) <= 2}
Operators == {"|", "&", "-", "^", "<=", "<", ">=", ">", "==", "|=", "&=", "-=", "^="}
Methods == {"union", "intersection", "difference", "symmetric_difference", "issubset", "issuperset", "isdisjoint"}
Updates == {"update", "intersection_update", "difference_update", "symmetric_difference_update"}
Programs == [ka : {"set", "frozenset"}, a : Small, op : Operators \cup Methods, b : Small]
            \cup [ka : {"set"}, a : Small, op : Updates, b : Small]

\* A set built in the order of the values: its elements <<side, value>>.
Build(side, s) == LET RECURSIVE From(_) From(i) == IF i > 3 THEN <<>>
                                                   ELSE (IF i \in s THEN <<<<side, Values[i]>>>> ELSE <<>>) \o From(i + 1)
                  IN From(1)
Tag(e) == e[1] \o e[2]

\* The lookup of key k in S: the tags of the entries compared, and the index found or 0.
RECURSIVE Probe(_, _, _)
Probe(S, k, i) == IF i > Len(S) THEN [log |-> <<>>, at |-> 0]
                  ELSE IF S[i][2] = k[2] THEN [log |-> <<Tag(S[i])>>, at |-> i]
                  ELSE LET r == Probe(S, k, i + 1) IN [log |-> <<Tag(S[i])>> \o r.log, at |-> r.at]
Lookup(S, k) == Probe(S, k, 1)
Without(S, i) == SubSeq(S, 1, i - 1) \o SubSeq(S, i + 1, Len(S))

\* A walk of W's entries from i into result R, searching R itself to add,
\* discard or toggle, else T.
RECURSIVE Walk(_, _, _, _, _, _)
Walk(kind, W, i, R, T, log) ==
    IF i > Len(W) THEN [r |-> R, log |-> log, bool |-> "True"]
    ELSE LET w == W[i]
             S == IF kind \in {"add", "discard", "toggle"} THEN R ELSE T
             f == Lookup(S, w)
             again == Lookup(R, w)
         IN CASE kind = "add" -> Walk(kind, W, i + 1, IF f.at = 0 THEN Append(R, w) ELSE R, T, log \o f.log)
              [] kind = "keep" \/ kind = "miss" ->
                   IF (f.at # 0) = (kind = "keep")
                   THEN Walk(kind, W, i + 1, IF again.at = 0 THEN Append(R, w) ELSE R, T, log \o f.log \o again.log)
                   ELSE Walk(kind, W, i + 1, R, T, log \o f.log)
              [] kind = "discard" -> Walk(kind, W, i + 1, IF f.at = 0 THEN R ELSE Without(R, f.at), T, log \o f.log)
              [] kind = "toggle" -> IF f.at # 0 THEN Walk(kind, W, i + 1, Without(R, f.at), T, log \o f.log)
                                    ELSE Walk(kind, W, i + 1, Append(R, w), T, log \o f.log \o f.log)
              [] kind = "subset" -> IF f.at = 0 THEN [r |-> R, log |-> log \o f.log, bool |-> "False"]
                                    ELSE Walk(kind, W, i + 1, R, T, log \o f.log)
              [] kind = "disjoint" -> IF f.at # 0 THEN [r |-> R, log |-> log \o f.log, bool |-> "False"]
                                      ELSE Walk(kind, W, i + 1, R, T, log \o f.log)

Smaller(A, B) == IF Len(B) > Len(A) THEN A ELSE B
Other(A, B) == IF Len(B) > Len(A) THEN B ELSE A
\* A union into an empty set copies the other, comparing none (Annex D).
Union(A, B) == IF A = <<>> THEN [r |-> B, log |-> <<>>, bool |-> "True"] ELSE Walk("add", B, 1, A, <<>>, <<>>)
Inter(A, B) == Walk("keep", Smaller(A, B), 1, <<>>, Other(A, B), <<>>)
Diff(A, B) == IF Len(A) \div 4 > Len(B) THEN Walk("discard", B, 1, A, <<>>, <<>>) ELSE Walk("miss", A, 1, <<>>, B, <<>>)
Discard(A, B) == Walk("discard", B, 1, A, <<>>, <<>>)
Toggle(A, B) == Walk("toggle", B, 1, A, <<>>, <<>>)
Subset(A, B) == IF Len(A) > Len(B) THEN [r |-> <<>>, log |-> <<>>, bool |-> "False"] ELSE Walk("subset", A, 1, <<>>, B, <<>>)
False == [r |-> <<>>, log |-> <<>>, bool |-> "False"]

\* What a program gives; a frozenset's augmented assignment is its operator.
Apply(p) ==
    LET A == Build("a", p.a)  B == Build("b", p.b)
        op == IF p.ka = "frozenset" /\ p.op \in {"|=", "&=", "-=", "^="} THEN SubSeq(p.op, 1, 1) ELSE p.op
    IN CASE op \in {"|", "|=", "union", "update"} -> Union(A, B)
         [] op \in {"&", "&=", "intersection", "intersection_update"} -> Inter(A, B)
         [] op \in {"-", "difference"} -> Diff(A, B)
         [] op \in {"-=", "difference_update"} -> Discard(A, B)
         [] op \in {"^", "symmetric_difference"} -> Toggle(B, A)
         [] op \in {"^=", "symmetric_difference_update"} -> Toggle(A, B)
         [] op \in {"<=", "issubset"} -> Subset(A, B)
         [] op \in {">=", "issuperset"} -> Subset(B, A)
         [] op = "<" -> IF Len(A) >= Len(B) THEN False ELSE Subset(A, B)
         [] op = ">" -> IF Len(A) <= Len(B) THEN False ELSE Subset(B, A)
         [] op = "==" -> IF Len(A) # Len(B) THEN False ELSE Subset(A, B)
         [] op = "isdisjoint" -> Walk("disjoint", Smaller(A, B), 1, <<>>, Other(A, B), <<>>)

Compares == {"<=", "<", ">=", ">", "==", "issubset", "issuperset", "isdisjoint"}
RECURSIVE Join(_)
Join(s) == IF s = <<>> THEN "" ELSE " " \o Head(s) \o Join(Tail(s))
Shown(S) == LET RECURSIVE From(_) From(i) == IF i > 3 THEN ""
                                             ELSE (IF \E j \in 1..Len(S) : S[j][2] = Values[i] THEN Values[i] ELSE "") \o From(i + 1)
            IN "{" \o From(1) \o "}"
Show(p) == LET w == Apply(p) IN (IF p.op \in Compares THEN w.bool ELSE Shown(w.r)) \o Join(w.log)

VARIABLES program, outcome
vars == <<program, outcome>>

Init == program \in Programs /\ outcome = "pending"
Execute == outcome = "pending" /\ outcome' = Show(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # "pending"

\* An entry is compared at most twice per walked entry: a union compares each of the result's once.
Bounded == Done => Len(Apply(program).log) <= 2 * (Cardinality(program.a) + 1) * (Cardinality(program.b) + 1)

\* Disjoint sets intersect in nothing.
Disjoint == Done /\ program.op = "&" /\ program.a \cap program.b = {} => Apply(program).r = <<>>
=============================================================================
