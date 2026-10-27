---------------------------- MODULE MatchGuards ----------------------------
(***************************************************************************)
(* Guards, value patterns, and group patterns of the match statement, as   *)
(* The Python Language Reference specifies them                            *)
(* (reference/compound_stmts.html#guards, #value-patterns, and #group-     *)
(* patterns, with #the-match-statement and #irrefutable-case-blocks): the  *)
(* subject is evaluated once; case blocks are tried in order, and a        *)
(* pattern that succeeds binds its names before its guard is evaluated, so *)
(* a failed guard leaves them bound and moves on to the next case; a guard *)
(* is evaluated only after its pattern succeeds; a value pattern looks up  *)
(* its dotted name each time it is tried and compares the subject with ==; *)
(* a parenthesized pattern is the pattern itself; and an irrefutable case  *)
(* block (a capture or wildcard without a guard) may only be the last.     *)
(*                                                                         *)
(* A program matches a subject t(x), x being 1, 2, or 3, against up to two *)
(* case blocks, each with the pattern 1, the capture n, the value pattern  *)
(* C.two (2, logged when looked up), or the group (1 | 2), and no guard or *)
(* a guard that is logged and true or false. A case's suite logs it. The   *)
(* outcome is n (None unless bound) or the exception, and the log.         *)
(***************************************************************************)
EXTENDS Naturals, Sequences, TLC

Patterns == {"one", "capture", "value", "group"}
Guards == {"none", "yes", "no"}
Blocks == [pattern : Patterns, guard : Guards]
Programs == [subject : 1..3, cases : UNION {[1..n -> Blocks] : n \in 1..2}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

R(n) == ToString(n)

Matches(pattern, x) == CASE pattern = "one" -> x = 1
                          [] pattern = "capture" -> TRUE
                          [] pattern = "value" -> x = 2
                          [] pattern = "group" -> x \in {1, 2}

\* Case blocks k.. with n bound so far: the final n and the log.
RECURSIVE Try(_, _, _)
Try(p, k, n) ==
    IF k > Len(p.cases) THEN <<n, <<>>>>
    ELSE LET b == p.cases[k]  x == p.subject
             lookup == IF b.pattern = "value" THEN <<"C.two">> ELSE <<>>
             bound == IF b.pattern = "capture" THEN R(x) ELSE n
             guard == IF b.guard = "none" THEN <<>> ELSE <<"guard " \o R(k)>>
         IN  IF ~Matches(b.pattern, x) THEN LET rest == Try(p, k + 1, n) IN <<rest[1], lookup \o rest[2]>>
             ELSE IF b.guard = "no" THEN LET rest == Try(p, k + 1, bound) IN <<rest[1], lookup \o guard \o rest[2]>>
             ELSE <<bound, lookup \o guard \o <<"case " \o R(k)>>>>

\* An irrefutable case block before the last is a syntax error.
Unreachable(p) == {k \in 1..(Len(p.cases) - 1) : p.cases[k].pattern = "capture" /\ p.cases[k].guard = "none"}

Run(p) ==
    IF Unreachable(p) # {} THEN <<"SyntaxError: name capture 'n' makes remaining patterns unreachable", <<>>>>
    ELSE LET r == Try(p, 1, "None") IN <<r[1], <<"subject">> \o r[2]>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
Ran == Done /\ Len(outcome[2]) > 0

\* The subject is evaluated once, first, and at most one suite runs.
SubjectOnce == Ran => outcome[2][1] = "subject" /\ \A i \in 2..Len(outcome[2]) : outcome[2][i] # "subject"
OneSuite == Ran => Len(SelectSeq(outcome[2], LAMBDA e : e \in {"case 1", "case 2"})) <= 1
=============================================================================
