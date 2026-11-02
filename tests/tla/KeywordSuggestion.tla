-------------------------- MODULE KeywordSuggestion --------------------------
(***************************************************************************)
(* The suggestion of a keyword argument that names no parameter            *)
(* (PLS-315 7.4.5), for every call                                         *)
(*                                                                         *)
(*     def f(c1=None, c2=None): ...       # zero to two parameters         *)
(*     f(name=1)                          # name any spelling, even ''   *)
(*                                                                         *)
(* whose names are spelled with a, b and B. The outcome is the binding, or *)
(* the TypeError and the parameter it suggests. The limits on candidate   *)
(* count and on name length are left to the spec tests.                   *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Letters == {"a", "b", "B"}
Words == {<<x>> : x \in Letters} \cup {<<x, y>> : x, y \in Letters}
Lists == {<<>>} \cup {<<w>> : w \in Words} \cup {<<v, w>> : v, w \in Words}
Programs == [params : {l \in Lists : Len(l) < 2 \/ l[1] # l[2]}, name : Words \cup {<<>>}]

VARIABLES program, outcome
vars == <<program, outcome>>

None == "-"
Pending == <<"pending", None>>

Min(x, y) == IF x < y THEN x ELSE y
Lower(x) == IF x = "B" THEN "b" ELSE x
Front(s) == SubSeq(s, 1, Len(s) - 1)
Last(s) == s[Len(s)]
\* Replacing a byte costs 2, or 1 when only its ASCII case differs;
\* inserting or deleting one costs 2.
Cost(x, y) == IF x = y THEN 0 ELSE IF Lower(x) = Lower(y) THEN 1 ELSE 2
RECURSIVE Distance(_, _)
Distance(s, t) ==
    CASE Len(s) = 0 -> 2 * Len(t)
      [] Len(t) = 0 -> 2 * Len(s)
      [] OTHER -> Min(Min(Distance(Front(s), t) + 2, Distance(s, Front(t)) + 2),
                      Distance(Front(s), Front(t)) + Cost(Last(s), Last(t)))
Third(s, t) == ((Len(s) + Len(t) + 3) * 2) \div 6
Far == 1000

\* KeywordSuggestion: the first candidate closest to the name, within a
\* third of their characters.
RECURSIVE Pick(_, _, _, _)
Pick(name, rest, best, cost) ==
    IF rest = <<>> THEN best
    ELSE LET c == Head(rest)
             limit == Min(Third(name, c), cost - 1)
             d == Distance(name, c)
         IN  IF c # name /\ d <= limit THEN Pick(name, Tail(rest), c, d)
             ELSE Pick(name, Tail(rest), best, cost)

Call(p) ==
    IF \E i \in 1..Len(p.params) : p.params[i] = p.name THEN <<"bound", None>>
    ELSE <<"TypeError", Pick(p.name, p.params, None, Far)>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Call(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Suggested == outcome[1] = "TypeError" /\ outcome[2] # None
Candidate == Suggested => \E i \in 1..Len(program.params) : program.params[i] = outcome[2]
WithinThird == Suggested => Distance(program.name, outcome[2]) <= Third(program.name, outcome[2])
\* No parameter within its own third is strictly closer than the suggestion,
\* and with none suggested, none is within its third at all.
Closest == outcome[1] = "TypeError" =>
    \A i \in 1..Len(program.params) :
        LET c == program.params[i] IN
        Distance(program.name, c) <= Third(program.name, c) =>
            outcome[2] # None /\ Distance(program.name, outcome[2]) <= Distance(program.name, c)
=============================================================================
