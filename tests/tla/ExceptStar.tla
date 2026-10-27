---------------------------- MODULE ExceptStar ----------------------------
(***************************************************************************)
(* except* clauses and exception groups, as The Python Language Reference  *)
(* (reference/compound_stmts.html#except-star) and PEP 654 specify them,   *)
(* for every statement of this shape:                                      *)
(*                                                                         *)
(*     try:                                                                *)
(*         raise <exception>                                               *)
(*     except* <type 1> as eg:     # one or two clauses                    *)
(*         log.append((1, leaves(eg)))                                     *)
(*         <action 1>              # pass, raise, or raise RuntimeError()  *)
(*     except* <type 2> as eg: ...                                         *)
(*                                                                         *)
(* The exception is a ValueError (V), a TypeError (T), a KeyError (K), or  *)
(* a group of them, possibly nested; the types are ValueError, TypeError,  *)
(* LookupError, and Exception. leaves() lists an exception's leaves in     *)
(* name order, a RuntimeError being R. The outcome is the log and what     *)
(* the statement raised: nothing, a single exception, or a group, with     *)
(* its leaves.                                                             *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

Raised == {"V", "T", "K", "EG(V,T)", "EG(V,EG(K))", "EG(T,K)"}
Types == {"ValueError", "TypeError", "LookupError", "Exception"}
Actions == {"pass", "raise", "new"}
Clauses == [type : Types, action : Actions]
Programs == Raised \X (UNION {[1..n -> Clauses] : n \in 1..2})

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<<<>>, "pending", "">>

LeavesOf(r) == CASE r = "EG(V,T)" -> {"V", "T"} [] r = "EG(V,EG(K))" -> {"V", "K"}
                 [] r = "EG(T,K)" -> {"T", "K"} [] OTHER -> {r}
IsGroup(r) == Cardinality(LeavesOf(r)) > 1
Matches(type, leaf) == CASE type = "ValueError" -> leaf = "V" [] type = "TypeError" -> leaf = "T"
                         [] type = "LookupError" -> leaf = "K" [] type = "Exception" -> TRUE

RECURSIVE Rs(_)
Rs(n) == IF n = 0 THEN "" ELSE "R" \o Rs(n - 1)
Name(set, n) == (IF "K" \in set THEN "K" ELSE "") \o Rs(n) \o (IF "T" \in set THEN "T" ELSE "")
                \o (IF "V" \in set THEN "V" ELSE "")

Run(p) ==
    LET r == p[1]  cs == p[2]  n == Len(cs)
        \* Each clause takes the leaves of what is left that match its type.
        RECURSIVE Left(_)
        Left(k) == IF k = 0 THEN LeavesOf(r) ELSE {l \in Left(k - 1) : ~Matches(cs[k].type, l)}
        Taken(k) == {l \in Left(k - 1) : Matches(cs[k].type, l)}
        ran == {k \in 1..n : Taken(k) # {}}
        log == [j \in 1..Cardinality(ran) |->
                   LET k == CHOOSE k \in ran : Cardinality({m \in ran : m < k}) = j - 1
                   IN  <<k, Name(Taken(k), 0)>>]
        \* What the clauses raise: new RuntimeErrors, and the parts they
        \* re-raise, which with the unhandled rest keep the original's shape.
        new == Cardinality({k \in ran : cs[k].action = "new"})
        kept == Left(n) \cup UNION {Taken(k) : k \in {m \in ran : cs[m].action = "raise"}}
        items == new + (IF kept = {} THEN 0 ELSE 1)
    IN  <<log,
          CASE ~IsGroup(r) /\ ran = {} -> "single"              \* nothing matched: re-raised as it was
            \* A single exception matched by a clause was wrapped in a group:
            \* that clause's raise re-raises the group, or what it raised.
            [] ~IsGroup(r) -> (CASE kept # {} -> "group" [] new = 1 -> "single" [] OTHER -> "none")
            [] items = 0 -> "none"
            [] items = 1 /\ new = 1 -> "single"
            [] OTHER -> "group",
          Name(kept, new)>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Each leaf is handled by at most one clause, the first that matches it.
AtMostOnce == Done => \A i, j \in DOMAIN outcome[1] : i < j => outcome[1][i][1] < outcome[1][j][1]

\* A clause for Exception after the others leaves nothing unhandled: only
\* what clauses raise escapes.
CatchAll == Done /\ program[2][Len(program[2])].type = "Exception" /\ (\A k \in DOMAIN program[2] : program[2][k].action = "pass")
            => outcome[2] = "none"

\* A single exception no clause matches propagates unchanged.
Unmatched == Done /\ outcome[1] = <<>> => outcome[2] = (IF IsGroup(program[1]) THEN "group" ELSE "single")
                                          /\ outcome[3] = Name(LeavesOf(program[1]), 0)
=============================================================================
