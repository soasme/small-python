-------------------------------- MODULE MRO --------------------------------
(***************************************************************************)
(* The method resolution order of classes, as Python specifies it          *)
(* (reference/datamodel.html, and "The Python 2.3 Method Resolution        *)
(* Order", which defines the C3 linearization it still uses), for every    *)
(* program of four class statements:                                      *)
(*                                                                         *)
(*     class A: pass                                                       *)
(*     class B(<bases>): pass      # each up to two bases, from the        *)
(*     class C(<bases>): pass      # classes before it and object (O)      *)
(*     class D(<bases>): pass                                              *)
(*                                                                         *)
(* A class without bases has object as its base. The outcome is the MRO   *)
(* of each class created, and the exception that stopped the program, if  *)
(* any: a base listed twice, or bases no linearization can order.         *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

Classes == <<"A", "B", "C", "D">>
Bases(set) == UNION {[1..n -> set] : n \in 0..2}
Programs == [B : Bases({"O", "A"}), C : Bases({"O", "A", "B"}), D : Bases({"O", "A", "B", "C"})]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", <<>>>>
Range(s) == {s[i] : i \in DOMAIN s}

\* C3's merge: repeatedly take the first head, in list order, that is in
\* no list's tail. Stuck, it ends with "!".
RECURSIVE Merge(_)
Merge(ls) ==
    LET ne == SelectSeq(ls, LAMBDA l : l # <<>>)
        good == {i \in 1..Len(ne) : \A j \in 1..Len(ne) : Head(ne[i]) \notin Range(Tail(ne[j]))}
    IN  IF ne = <<>> THEN <<>>
        ELSE IF good = {} THEN <<"!">>
        ELSE LET h == Head(ne[CHOOSE i \in good : \A j \in good : i <= j])
             IN  <<h>> \o Merge([j \in 1..Len(ne) |-> IF Head(ne[j]) = h THEN Tail(ne[j]) ELSE ne[j]])

BasesOf(p, c) == IF c = "A" THEN <<"O">> ELSE IF p[c] = <<>> THEN <<"O">> ELSE p[c]

\* The MROs of the first k classes, each from those before it.
RECURSIVE MROs(_, _)
MROs(p, k) ==
    IF k = 0 THEN <<>>
    ELSE LET before == MROs(p, k - 1)
             L(b) == IF b = "O" THEN <<"O">> ELSE before[CHOOSE i \in 1..(k - 1) : Classes[i] = b]
             bases == BasesOf(p, Classes[k])
         IN  before \o <<<<Classes[k]>> \o Merge([i \in 1..Len(bases) |-> L(bases[i])] \o <<bases>>)>>

\* The classes a program creates before the first that fails.
Created(p) ==
    LET bad(k) == LET b == BasesOf(p, Classes[k])
                  IN  Cardinality(Range(b)) < Len(b) \/ "!" \in Range(MROs(p, k)[k])
        failing == {k \in 1..4 : bad(k)}
    IN  IF failing = {} THEN 4 ELSE (CHOOSE k \in failing : \A j \in failing : k <= j) - 1

Run(p) == <<IF Created(p) = 4 THEN "ok" ELSE "TypeError", MROs(p, Created(p))>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
(* What the linearization guarantees.                                      *)

Done == outcome # Pending
MRO(k) == outcome[2][k]
Index(s, x) == CHOOSE i \in DOMAIN s : s[i] = x

\* A class comes first, object last, and nothing twice.
Ends == Done => \A k \in DOMAIN outcome[2] :
    Head(MRO(k)) = Classes[k] /\ MRO(k)[Len(MRO(k))] = "O" /\ Cardinality(Range(MRO(k))) = Len(MRO(k))

\* Local precedence: the bases appear in the order they are listed.
LocalPrecedence == Done => \A k \in DOMAIN outcome[2] :
    LET b == BasesOf(program, Classes[k])
    IN  \A i, j \in 1..Len(b) : i < j => Index(MRO(k), b[i]) < Index(MRO(k), b[j])

\* Monotonicity: every base's MRO keeps its order in the class's MRO.
Monotonic == Done => \A k \in DOMAIN outcome[2] :
    \A b \in Range(BasesOf(program, Classes[k])) \ {"O"} :
        LET m == MRO(CHOOSE i \in 1..4 : Classes[i] = b)
        IN  \A i, j \in 1..Len(m) : i < j => Index(MRO(k), m[i]) < Index(MRO(k), m[j])
=============================================================================
