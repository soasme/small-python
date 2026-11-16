--------------------------- MODULE KeywordHashes ----------------------------
(***************************************************************************)
(* How often keyword names are hashed and compared when ** merges dicts    *)
(* whose keys are instances of a str subclass with a logging __hash__ and  *)
(* __eq__, as PLS-315 13.2.3, 13.3.4, 26.1.1 and 26.2 specify it: a dict's *)
(* keys keep their stored hashes through DictMerge, so merging calls       *)
(* __eq__ only on a key equal in hash to one already merged; a call's      *)
(* duplicate raises TypeError there, a display's keeps the first key with  *)
(* the later value. A function's **kw, dict() and frozendict() then set    *)
(* each keyword by DictSetItem, hashing its name once; a subclass's        *)
(* construction, dict.update and a display merge without hashing. A       *)
(* function with a parameter z first compares each name with z by its     *)
(* __eq__, then hashes it into **kw.                                       *)
(*                                                                         *)
(* A program is a target, a call of a function taking only **kw, or z=None *)
(* and **kw, dict(), a                                                     *)
(* dict subclass, dict.update, frozendict(), a frozendict subclass or a    *)
(* dict display, given a=0 first or not, then one or two ** dicts of one   *)
(* key each, a or b. The outcome is the result's items in order with the   *)
(* log, or TypeError with the log.                                         *)
(***************************************************************************)
EXTENDS Integers, Sequences, FiniteSets

Targets == {"call", "parameter call", "dict", "dict subclass", "update", "frozendict", "frozendict subclass", "display"}
Keys == UNION {[1..n -> {"a", "b"}] : n \in 1..2}
Programs == [target : Targets, explicit : BOOLEAN, keys : Keys]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", <<>>, <<>>>>

\* Merge the ** dicts in order: a key spelled as one merged before calls
\* __eq__ once; a call refuses it, a display replaces the value.
RECURSIVE Merge(_, _, _, _)
Merge(items, log, keys, i) ==
    IF i > Len(keys) THEN <<"ok", items, log>>
    ELSE LET k == keys[i]
             at == {j \in DOMAIN items : items[j][1] = k}
         IN  IF at = {} THEN Merge(Append(items, <<k, i>>), log, keys, i + 1)
             ELSE IF program.target = "display"
                  THEN Merge([items EXCEPT ![CHOOSE j \in at : TRUE][2] = i], Append(log, "eq"), keys, i + 1)
                  ELSE <<"TypeError", <<>>, Append(log, "eq")>>

\* Each merged name of the str subclass, not the exact str a, hashed once.
Hashes(items, explicit) == [j \in 1..(Len(items) - IF explicit THEN 1 ELSE 0) |-> "hash"]

\* Each such name compared with the parameter z, then hashed into **kw.
Binds(items, explicit) == [j \in 1..(2 * (Len(items) - IF explicit THEN 1 ELSE 0)) |-> IF j % 2 = 1 THEN "eq" ELSE "hash"]

Run(p) ==
    LET merged == Merge(IF p.explicit THEN <<<<"a", 0>>>> ELSE <<>>, <<>>, p.keys, 1)
    IN  IF merged[1] # "ok" \/ p.target \notin {"call", "parameter call", "dict", "frozendict"} THEN merged
        ELSE IF p.target = "parameter call" THEN <<"ok", merged[2], merged[3] \o Binds(merged[2], p.explicit)>>
        ELSE <<"ok", merged[2], merged[3] \o Hashes(merged[2], p.explicit)>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* No name is hashed more than once, nor compared without a duplicate.
OnceEach == Done => Len(SelectSeq(outcome[3], LAMBDA e : e = "hash")) <= Len(program.keys)
Duplicates == Done /\ program.target \notin {"display", "parameter call"} /\ outcome[1] = "ok" => outcome[3] \in {<<>>, <<"hash">>, <<"hash", "hash">>}
=============================================================================
