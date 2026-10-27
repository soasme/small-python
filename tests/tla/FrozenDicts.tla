---------------------------- MODULE FrozenDicts ----------------------------
(***************************************************************************)
(* Frozen dictionaries, new in 3.15, as The Python Language Reference      *)
(* specifies them (reference/datamodel.html#frozen-dictionaries,           *)
(* library/stdtypes.html#frozen-dictionaries): frozendict(iterable or      *)
(* mapping, **kwargs) keeps insertion order with later keys replacing      *)
(* earlier values; it compares equal to a dict with the same items; | of a *)
(* frozendict and a dict takes the left operand's type; |= makes a new     *)
(* frozendict; it has no methods that mutate and refuses item assignment   *)
(* and deletion; it is hashable when its values are; it is not a dict.     *)
(*                                                                         *)
(* A program is either                                                     *)
(*   - frozendict(<pairs>, **<keywords>), pairs up to two of a, b with     *)
(*     values 1, 2 (or no positional argument), keywords up to two of a, c *)
(*     with values 3, 4; or                                                *)
(*   - x and y, each a dict or frozendict with up to two items of a, b,    *)
(*     and one of  x | y, x == y, x |= y (with x aliased as z), hash(x),   *)
(*     hash of x with a list value, x[k] = 1, del x[k], x.pop(k),          *)
(*     x.update(), x.setdefault(k), x.clear(), x.popitem(), x.copy() is x, *)
(*     isinstance(x, dict).                                                *)
(*                                                                         *)
(* The outcome is the result's type and items in order, or the exception.  *)
(***************************************************************************)
EXTENDS Integers, Sequences, FiniteSets

Pairs(keys, values) == UNION {[1..n -> keys \X values] : n \in 0..2}
Distinct(s) == \A i, j \in DOMAIN s : i # j => s[i][1] # s[j][1]
Mappings == {s \in Pairs({"a", "b"}, {1, 2}) : Distinct(s)}
Kinds == {"dict", "frozendict"}
Ops == {"|", "==", "|=", "hash", "hash list", "setitem", "delitem", "pop", "update", "setdefault", "clear",
        "popitem", "copy", "isdict"}
Programs == [op : {"build"}, positional : {<<"none", <<>>>>} \cup {<<"pairs", s>> : s \in Pairs({"a", "b"}, {1, 2})},
             keywords : {s \in Pairs({"a", "c"}, {3, 4}) : Distinct(s)}]
            \cup [op : Ops, kx : Kinds, x : Mappings, ky : Kinds, y : Mappings]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", "", <<>>>>
Error(name) == <<name, "", <<>>>>
Bool(b) == <<"bool", IF b THEN "True" ELSE "False", <<>>>>

\* Insert or replace each pair in order: a replaced key keeps its place.
RECURSIVE Update(_, _)
Update(d, s) ==
    IF s = <<>> THEN d
    ELSE LET k == Head(s)[1]
             at == {i \in DOMAIN d : d[i][1] = k}
         IN  Update(IF at = {} THEN Append(d, Head(s)) ELSE [d EXCEPT ![CHOOSE i \in at : TRUE] = Head(s)], Tail(s))
Items(d) == {d[i] : i \in DOMAIN d}

Run(p) ==
    IF p.op = "build" THEN <<"frozendict", "", Update(Update(<<>>, p.positional[2]), p.keywords)>>
    ELSE LET x == p.x  y == p.y  frozen == p.kx = "frozendict"
         IN  CASE p.op = "|" -> <<p.kx, "", Update(x, y)>>
               [] p.op = "==" -> Bool(Items(x) = Items(y))
               \* x |= y: a dict changes in place (z, an alias, sees it); a
               \* frozendict is replaced (z keeps its items).
               [] p.op = "|=" -> <<p.kx, IF frozen THEN "kept" ELSE "same", Update(x, y)>>
               [] p.op = "hash" -> IF frozen THEN <<"hashable", "", <<>>>> ELSE Error("TypeError")
               [] p.op = "hash list" -> Error("TypeError")
               [] ~frozen /\ p.op \in {"setitem", "delitem", "pop", "update", "setdefault", "clear", "popitem"} -> <<"mutable", "", <<>>>>
               [] p.op \in {"setitem", "delitem"} -> Error("TypeError")
               [] p.op \in {"pop", "update", "setdefault", "clear", "popitem"} -> Error("AttributeError")
               [] p.op = "copy" -> Bool(frozen)                  \* a frozendict's copy is itself
               [] p.op = "isdict" -> Bool(~frozen)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Keys are unique.
UniqueKeys == Done /\ outcome[1] \in Kinds => Distinct(outcome[3])

\* Equality ignores the types: a dict equals the frozendict of its items.
EqualAcross == Done /\ program.op = "==" => outcome = Run([program EXCEPT !.kx = "dict", !.ky = "dict"])
=============================================================================
