--------------------------- MODULE KeywordHashes ----------------------------
(***************************************************************************)
(* How often keyword names are hashed and compared when ** merges dicts    *)
(* whose keys are instances of a str subclass with a logging __hash__ and  *)
(* __eq__, as PLS-315 13.2.3, 13.3.4, 26.1.1 and 26.2 specify it: a dict's *)
(* keys keep their stored hashes through DictMerge, so merging calls       *)
(* __eq__ only on a key equal in hash to one already merged, in the order  *)
(* they were merged; a call's duplicate raises TypeError there, a          *)
(* display's keeps the first key with the later value. A call's merge     *)
(* looks a key up twice, to refuse it and then to insert it, a display's  *)
(* once. A function's **kw, dict() and frozendict() then set each keyword *)
(* by DictSetItem, hashing its name once and comparing it with each       *)
(* earlier name equal in hash; a subclass's construction, dict.update and *)
(* a display merge without hashing. A function with a parameter z first   *)
(* compares each name with z by its __eq__.                                *)
(*                                                                         *)
(* A program is a target, a call of a function taking only **kw, or z=None *)
(* and **kw, dict(), a dict subclass, dict.update, frozendict(), a         *)
(* frozendict subclass or a dict display, given one or two ** dicts of one *)
(* key each, a, b, or A, whose hash is a's, and a=0 first, last or not at  *)
(* all; a=0 last merges as a ** of it does. The outcome is the result's    *)
(* items in order with the log, or TypeError with the log.                 *)
(***************************************************************************)
EXTENDS Integers, Sequences, FiniteSets

Targets == {"call", "parameter call", "dict", "dict subclass", "update", "frozendict", "frozendict subclass", "display"}
Keys == UNION {[1..n -> {"a", "b", "A"}] : n \in 1..2}
Programs == [target : Targets, explicit : {"none", "first", "last"}, keys : Keys]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", <<>>, <<>>>>

Fold(k) == IF k = "A" THEN "a" ELSE k
Eqs(n) == [j \in 1..n |-> "eq"]
\* The positions of items, in order, whose names are equal in hash to k.
Collides(items, k) == SelectSeq([j \in DOMAIN items |-> j], LAMBDA j : Fold(items[j][1]) = Fold(k))

\* Merge the ** dicts in order: a key is compared with each merged one
\* equal in hash, up to one spelled as it is; a call refuses that one, a
\* display replaces its value. A key equal to none is compared with them
\* again as a call inserts it.
RECURSIVE Merge(_, _, _, _)
Merge(items, log, keys, i) ==
    IF i > Len(keys) THEN <<"ok", items, log>>
    ELSE LET k == keys[i]
             at == Collides(items, k)
             same == {n \in DOMAIN at : items[at[n]][1] = k}
         IN  IF same = {}
             THEN Merge(Append(items, <<k, i>>), log \o Eqs((IF program.target = "display" THEN 1 ELSE 2) * Len(at)), keys, i + 1)
             ELSE LET n == CHOOSE n \in same : TRUE
                  IN  IF program.target = "display"
                      THEN Merge([items EXCEPT ![at[n]][2] = i], log \o Eqs(n), keys, i + 1)
                      ELSE <<"TypeError", <<>>, log \o Eqs(n)>>

\* Each merged name, compared with each earlier one equal in hash as it is
\* stored; one of the str subclass, not the exact str a of value 0, is
\* first compared with z when the function has it, and hashed.
RECURSIVE Stores(_, _, _)
Stores(items, binds, j) ==
    IF j > Len(items) THEN <<>>
    ELSE (IF items[j][2] = 0 THEN <<>> ELSE (IF binds THEN <<"eq">> ELSE <<>>) \o <<"hash">>)
         \o Eqs(Len(Collides(SubSeq(items, 1, j - 1), items[j][1]))) \o Stores(items, binds, j + 1)

Run(p) ==
    LET keys == IF p.explicit = "last" THEN Append(p.keys, "a") ELSE p.keys
        given == Merge(IF p.explicit = "first" THEN <<<<"a", 0>>>> ELSE <<>>, <<>>, keys, 1)
        \* a=0 last, merged at Len(keys), has value 0.
        merged == IF p.explicit = "last" /\ given[1] = "ok"
                  THEN <<"ok", [j \in DOMAIN given[2] |-> IF given[2][j][2] = Len(keys) THEN <<given[2][j][1], 0>> ELSE given[2][j]], given[3]>>
                  ELSE given
    IN  IF merged[1] # "ok" \/ p.target \notin {"call", "parameter call", "dict", "frozendict"} THEN merged
        ELSE <<"ok", merged[2], merged[3] \o Stores(merged[2], p.target = "parameter call", 1)>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* No name is hashed more than once, nor compared without one equal in hash.
OnceEach == Done => Len(SelectSeq(outcome[3], LAMBDA e : e = "hash")) <= Len(program.keys)
Duplicates == (Done /\ program.target \notin {"display", "parameter call"} /\ outcome[1] = "ok" /\ program.explicit # "last" /\
               \A j \in DOMAIN program.keys : program.keys[j] # "A") =>
              outcome[3] \in {<<>>, <<"hash">>, <<"hash", "hash">>}
=============================================================================
