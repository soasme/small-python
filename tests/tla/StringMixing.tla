---------------------------- MODULE StringMixing ----------------------------
(***************************************************************************)
(* Which adjacent literals PLS-315 12.5.4 lets one concatenation mix, and  *)
(* where the error is: two or three literals, each a string, a bytes       *)
(* literal or a t-string. The first literal differing from the one before  *)
(* it ends the check: a t-string next to a literal of another kind is an   *)
(* error over the two, a bytes mix one at the token after the literals     *)
(* before the first t-string. The outcome is the message and the literals  *)
(* the error spans, the number one past the last for the token after them, *)
(* or "ok".                                                                *)
(***************************************************************************)
EXTENDS Naturals

Kinds == {"str", "bytes", "t"}
Programs == [first : Kinds, second : Kinds, third : Kinds \cup {"none"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Kind(p, i) == CASE i = 1 -> p.first [] i = 2 -> p.second [] i = 3 -> p.third
Count(p) == IF p.third = "none" THEN 2 ELSE 3
\* Whether literal i and the one before it differ in being of kind k.
Differ(p, i, k) == (Kind(p, i) = k) # (Kind(p, i - 1) = k)
Mixed(p, i) == Differ(p, i, "t") \/ Differ(p, i, "bytes")
\* The number of literals before the first t-string.
Run(p) == IF p.first = "t" THEN 0 ELSE IF p.second = "t" THEN 1 ELSE IF p.third = "t" THEN 2 ELSE Count(p)

T == "cannot mix t-string literals with string or bytes literals"
B == "cannot mix bytes and nonbytes literals"
Reported(p) == LET i == IF Mixed(p, 2) THEN 2 ELSE IF Count(p) = 3 /\ Mixed(p, 3) THEN 3 ELSE 0 IN
               IF i = 0 THEN <<"ok", 0, 0>>
               ELSE IF Differ(p, i, "t") THEN <<T, i - 1, i>>
               ELSE <<B, Run(p) + 1, Run(p) + 1>>

Init == program \in Programs /\ outcome = <<"pending", 0, 0>>
Execute == outcome[1] = "pending" /\ outcome' = Reported(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome[1] # "pending"

\* A concatenation is an error exactly when two adjacent literals differ in kind.
OkUnmixed == Done => ((outcome[1] = "ok") = (\A i \in 2..Count(program) : ~Mixed(program, i)))

\* A t-string error spans two adjacent literals.
PairOnly == Done /\ outcome[1] = T => outcome[3] = outcome[2] + 1

\* A bytes error comes after literals that are no t-strings.
BytesBeforeT == Done /\ outcome[1] = B => \A i \in 1..(outcome[2] - 1) : Kind(program, i) # "t"
=============================================================================
