---------------------------- MODULE MatchLookups ----------------------------
(***************************************************************************)
(* The order of a mapping or class pattern's lookups (PLS-315 15.6.4,      *)
(* 15.6.5): a mapping pattern evaluates every key, then calls the          *)
(* subject's get for each key in order, and a class pattern reads every    *)
(* attribute in order, before any sub-pattern is matched; the first        *)
(* missing key or attribute fails the pattern with no further lookup, and  *)
(* the first sub-pattern that fails ends the matching.                     *)
(*                                                                         *)
(* A program matches {K.a: S.a, K.b: S.b} against a dict subclass, which   *)
(* also holds the keys 'c' and 'd' so that its length never fails it,     *)
(* whose get logs "get a" and "get b", the keys logging "key a" and        *)
(* "key b", or P(S.a, S.b) against an instance of P, __match_args__        *)
(* ('a', 'b'), whose properties log "attr a" and "attr b". Each entry is   *)
(* present or missing, and its value matches its sub-pattern or not: S.a   *)
(* and S.b are values whose __eq__ logs "sub a" and "sub b". The outcome   *)
(* is whether the case matched, and the log.                               *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Entries == [present : BOOLEAN, matches : BOOLEAN]
Programs == [kind : {"mapping", "class"}, entries : [1..2 -> Entries]]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

Name(i) == IF i = 1 THEN "a" ELSE "b"
Read(p, i) == IF p.kind = "mapping" THEN "get " \o Name(i) ELSE "attr " \o Name(i)
Keys(p) == IF p.kind = "mapping" THEN <<"key a", "key b">> ELSE <<>>

\* Lookups stop at the first missing entry, sub-patterns at the first failure.
Lookups(p) == IF p.entries[1].present THEN <<Read(p, 1), Read(p, 2)>> ELSE <<Read(p, 1)>>
Found(p) == p.entries[1].present /\ p.entries[2].present
Subs(p) == IF p.entries[1].matches THEN <<"sub a", "sub b">> ELSE <<"sub a">>
Matched(p) == Found(p) /\ p.entries[1].matches /\ p.entries[2].matches

Run(p) == <<IF Matched(p) THEN "hit" ELSE "miss", Keys(p) \o Lookups(p) \o (IF Found(p) THEN Subs(p) ELSE <<>>)>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
Log == outcome[2]
IsSub(e) == e \in {"sub a", "sub b"}

\* No lookup follows a sub-pattern's match.
LookupsFirst == Done => \A i, j \in 1..Len(Log) : i < j /\ IsSub(Log[i]) => IsSub(Log[j])
\* Every key is evaluated before the first get.
KeysFirst == Done /\ program.kind = "mapping" => Log[1] = "key a" /\ Log[2] = "key b"
\* A case that matched made every lookup.
AllRead == Done /\ outcome[1] = "hit" => Len(Log) = Len(Keys(program)) + 4
=============================================================================
