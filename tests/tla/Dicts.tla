------------------------------- MODULE Dicts -------------------------------
(***************************************************************************)
(* A dict as a sequence of entries in insertion order, as the Library      *)
(* Reference's mapping types section specifies it ("Dictionaries preserve  *)
(* insertion order. Note that updating a key does not affect the order.    *)
(* Keys added after deletion are inserted at the end."), driven by:        *)
(*                                                                         *)
(*     d[k] = v       d.pop(k)       d.popitem()       d.setdefault(k, v)  *)
(*     del d[k]       d.get(k)       k in d            list(d.items())     *)
(*                                                                         *)
(* over keys 'a', 'b', 'c' and values 1 and 2. Every step's `result` is    *)
(* what it returned (as a string) or raised; `entries` is the dict.        *)
(***************************************************************************)
EXTENDS Naturals, Sequences, TLC

Keys == {"a", "b", "c"}
Vals == {1, 2}

VARIABLES entries, op, result
vars == <<entries, op, result>>

KeysOf(d) == {d[i][1] : i \in DOMAIN d}
Pos(d, k) == CHOOSE i \in DOMAIN d : d[i][1] = k
Value(d, k) == d[Pos(d, k)][2]
Without(d, k) == SelectSeq(d, LAMBDA e : e[1] # k)

RECURSIVE Show(_)
Show(d) == IF d = <<>> THEN "" ELSE d[1][1] \o "=" \o ToString(d[1][2]) \o (IF Len(d) > 1 THEN "," ELSE "") \o Show(Tail(d))

Init == entries = <<>> /\ op = <<"init", "", 0>> /\ result = "-"

\* d[k] = v: a new key goes last; an existing one keeps its place.
SetItem(k, v) ==
    /\ op' = <<"set", k, v>> /\ result' = "None"
    /\ entries' = IF k \in KeysOf(entries) THEN [entries EXCEPT ![Pos(entries, k)] = <<k, v>>]
                  ELSE Append(entries, <<k, v>>)

\* del d[k] and d.pop(k) remove the entry; a missing key is a KeyError.
Delete(k, name) ==
    /\ op' = <<name, k, 0>>
    /\ IF k \in KeysOf(entries)
       THEN entries' = Without(entries, k)
            /\ result' = IF name = "del" THEN "None" ELSE ToString(Value(entries, k))
       ELSE result' = "KeyError" /\ UNCHANGED entries

\* d.popitem() removes the last entry (LIFO).
PopItem ==
    /\ op' = <<"popitem", "", 0>>
    /\ IF entries = <<>> THEN result' = "KeyError" /\ UNCHANGED entries
       ELSE LET e == entries[Len(entries)]
            IN  result' = e[1] \o "=" \o ToString(e[2]) /\ entries' = SubSeq(entries, 1, Len(entries) - 1)

SetDefault(k, v) ==
    /\ op' = <<"setdefault", k, v>>
    /\ IF k \in KeysOf(entries) THEN result' = ToString(Value(entries, k)) /\ UNCHANGED entries
       ELSE result' = ToString(v) /\ entries' = Append(entries, <<k, v>>)

\* Steps that only read.
Read(name, k) ==
    /\ op' = <<name, k, 0>>
    /\ result' = CASE name = "get" -> IF k \in KeysOf(entries) THEN ToString(Value(entries, k)) ELSE "None"
                   [] name = "in" -> IF k \in KeysOf(entries) THEN "True" ELSE "False"
                   [] name = "items" -> Show(entries)
    /\ UNCHANGED entries

Next == \/ \E k \in Keys, v \in Vals : SetItem(k, v) \/ SetDefault(k, v)
        \/ \E k \in Keys : Delete(k, "del") \/ Delete(k, "pop") \/ Read("get", k) \/ Read("in", k)
        \/ PopItem \/ Read("items", "")
Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
\* No key appears twice.
UniqueKeys == \A i, j \in DOMAIN entries : i # j => entries[i][1] # entries[j][1]

\* Updating a key does not move it.
UpdateKeepsOrder == [][(\E k \in Keys, v \in Vals : op' = <<"set", k, v>> /\ k \in KeysOf(entries))
                       => [i \in DOMAIN entries' |-> entries'[i][1]] = [i \in DOMAIN entries |-> entries[i][1]]]_vars

\* A key added after deletion goes at the end.
ReinsertLast == [][(op'[1] \in {"set", "setdefault"} /\ op'[2] \notin KeysOf(entries))
                   => entries'[Len(entries')][1] = op'[2]]_vars
=============================================================================
