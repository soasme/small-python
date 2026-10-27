---------------------------- MODULE DictMethods -----------------------------
(***************************************************************************)
(* Dictionaries and dictionary views, as the Built-in Types chapter        *)
(* specifies them (library/stdtypes.html#mapping-types-dict and            *)
(* #dictionary-view-objects): dict() builds from a mapping (or any object  *)
(* with keys()), an iterable of pairs, and keywords, later keys winning;   *)
(* keys must be hashable, and equal keys (1, 1.0, True) are one key        *)
(* keeping its first spelling; a dict remembers insertion order, which     *)
(* reassignment keeps and deletion forgets; d | other and update() (and    *)
(* |=, which also takes pairs) keep the left operand's order, give the     *)
(* right operand's values, and append its new keys in its order; equality  *)
(* ignores order and dicts are unordered and unhashable; get, setdefault,  *)
(* pop, popitem (last in, first out), fromkeys, copy (shallow), clear,     *)
(* reversed(), and __missing__ in subclasses behave as documented, a       *)
(* missing key raising KeyError; and keys(), values(), and items() are     *)
(* live views, keys and items set-like (their operators accept any         *)
(* iterable and return sets) with a mapping attribute, values not.         *)
(*                                                                         *)
(* A program builds dicts d1 and d2 from two maps of at most two entries   *)
(* over keys 1, 2, 3 and values 10, 20 and applies one of OPS: d1 | d2,    *)
(* d1.update(d2), d1 |= d2 (and whether d1 is the same object), d1 == d2,  *)
(* the sorted results of the view operators &, |, -, ^ on keys and &, - on *)
(* items, d1.keys() <= d2.keys(), isdisjoint, or the values and reversed   *)
(* items of views taken before d1.update(d2); or runs one of the sources   *)
(* of CASES in a fresh namespace. The outcome is the repr of that result   *)
(* or of the case's result, or the exception and its message.              *)
(***************************************************************************)
EXTENDS Integers, Sequences, FiniteSets, TLC

VARIABLES program, outcome
vars == <<program, outcome>>

KS == {1, 2, 3}
VS == {10, 20}
Maps == {<<>>} \cup {<<<<k, v>>>> : k \in KS, v \in VS}
        \cup {<<<<k1, v1>>, <<k2, v2>>>> : <<k1, k2>> \in {q \in KS \X KS : q[1] # q[2]}, v1 \in VS, v2 \in VS}
Ops == {"merge", "update", "ior", "equal", "keys_and", "keys_or", "keys_sub", "keys_xor", "items_and",
        "items_sub", "keys_le", "keys_disjoint", "values_list", "reversed_items"}

R(n) == ToString(n)
B(b) == IF b THEN "True" ELSE "False"
RECURSIVE Join(_)
Join(s) == IF s = <<>> THEN "" ELSE IF Len(s) = 1 THEN Head(s) ELSE Head(s) \o ", " \o Join(Tail(s))
List(s) == "[" \o Join(s) \o "]"

Keys(m) == {m[i][1] : i \in DOMAIN m}
Items(m) == {m[i] : i \in DOMAIN m}
Get(m, k) == m[CHOOSE i \in DOMAIN m : m[i][1] = k][2]
Item(e) == "(" \o R(e[1]) \o ", " \o R(e[2]) \o ")"
Show(m) == "{" \o Join([i \in DOMAIN m |-> R(m[i][1]) \o ": " \o R(m[i][2])]) \o "}"

\* The left map's keys in its order with the right map's values, then the
\* right map's new keys in its order.
Merge(a, b) == [i \in DOMAIN a |-> IF a[i][1] \in Keys(b) THEN <<a[i][1], Get(b, a[i][1])>> ELSE a[i]]
               \o SelectSeq(b, LAMBDA e : e[1] \notin Keys(a))

\* Sets are shown sorted, as the program sorts them.
SortedKeys(S) == List([i \in 1..Len(SelectSeq(<<1, 2, 3>>, LAMBDA k : k \in S)) |->
                       R(SelectSeq(<<1, 2, 3>>, LAMBDA k : k \in S)[i])])
AllItems == [i \in 1..6 |-> <<(i - 1) \div 2 + 1, IF (i - 1) % 2 = 0 THEN 10 ELSE 20>>]
SortedItems(S) == LET s == SelectSeq(AllItems, LAMBDA e : e \in S) IN List([i \in DOMAIN s |-> Item(s[i])])
Reverse(s) == [i \in DOMAIN s |-> s[Len(s) + 1 - i]]


Cases == {"ctor_forms", "ctor_equal", "ctor_bad_item", "ctor_bad_element", "ctor_two_positional", "fromkeys",
          "fromkeys_shared", "missing_hook", "keyerror", "keyerror_tuple", "unhashable_key", "get_default",
          "pop_default", "pop_missing", "popitem_lifo", "popitem_empty", "setdefault", "update_forms",
          "update_bad", "update_too_many", "or_non_dict", "ior_iterable", "copy_shallow", "clear",
          "len_iter_reversed", "order_reinsert", "equality_ignores_order", "no_ordering", "unhashable_dict",
          "view_live", "view_mapping", "view_contains", "view_set_ops_iterable", "view_set_ops_return_set",
          "values_no_set_ops", "values_equality", "items_unhashable_value", "items_set_op_unhashable",
          "view_changed_size", "view_reversed_type", "view_repr", "view_hash", "view_comparisons",
          "view_isdisjoint", "repr_recursive", "iter_type_names", "dict_subclass_or",
          "keys_order_after_pop", "float_int_key", "nan_key"}
Programs == [op : Ops, a : Maps, b : Maps]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    LET a == p.a  b == p.b  m == Merge(a, b) IN
    CASE p.op \in {"merge", "update"} -> Show(m)
      [] p.op = "ior" -> "(" \o Show(m) \o ", True)"
      [] p.op = "equal" -> B(Items(a) = Items(b))
      [] p.op = "keys_and" -> SortedKeys(Keys(a) \cap Keys(b))
      [] p.op = "keys_or" -> SortedKeys(Keys(a) \cup Keys(b))
      [] p.op = "keys_sub" -> SortedKeys(Keys(a) \ Keys(b))
      [] p.op = "keys_xor" -> SortedKeys((Keys(a) \ Keys(b)) \cup (Keys(b) \ Keys(a)))
      [] p.op = "items_and" -> SortedItems(Items(a) \cap Items(b))
      [] p.op = "items_sub" -> SortedItems(Items(a) \ Items(b))
      [] p.op = "keys_le" -> B(Keys(a) \subseteq Keys(b))
      [] p.op = "keys_disjoint" -> B(Keys(a) \cap Keys(b) = {})
      \* Views see the update made after they were taken.
      [] p.op = "values_list" -> List([i \in DOMAIN m |-> R(m[i][2])])
      [] p.op = "reversed_items" -> List([i \in DOMAIN m |-> Item(Reverse(m)[i])])

Case(c) ==
    CASE c = "ctor_forms" -> "[{'one': 1, 'two': 2}, {'one': 1, 'two': 2}, {'one': 1, 'two': 2}, {'two': 2, 'one': 1}, {'one': 1, 'two': 2}, {'a': 'A', 'b': 'B'}]"
      [] c = "ctor_equal" -> "True"
      [] c = "ctor_bad_item" -> "ValueError: dictionary update sequence element #0 has length 3; 2 is required"
      [] c = "ctor_bad_element" -> "TypeError: object is not iterable"
      [] c = "ctor_two_positional" -> "TypeError: dict expected at most 1 argument, got 2"
      [] c = "fromkeys" -> "({'a': None, 'b': None}, {1: 0, 2: 0}, 'Missing')"
      [] c = "fromkeys_shared" -> "{'a': [1], 'b': [1]}"
      [] c = "missing_hook" -> "(1, 'zzzz', False, None)"
      [] c = "keyerror" -> "KeyError: 'k'"
      [] c = "keyerror_tuple" -> "KeyError: (1,)"
      [] c = "unhashable_key" -> "TypeError: cannot use 'list' as a dict key (unhashable type: 'list')"
      [] c = "get_default" -> "(None, 'd', 0)"
      [] c = "pop_default" -> "(2, 'd', {})"
      [] c = "pop_missing" -> "KeyError: 1"
      [] c = "popitem_lifo" -> "((3, 3), (2, 2), {1: 1})"
      [] c = "popitem_empty" -> "KeyError: 'popitem(): dictionary is empty'"
      [] c = "setdefault" -> "(None, 1, 1, {'a': None, 'b': 1})"
      [] c = "update_forms" -> "{'a': 'A', 'b': 'B', 'c': 3}"
      [] c = "update_bad" -> "TypeError: 'int' object is not iterable"
      [] c = "update_too_many" -> "TypeError: update expected at most 1 argument, got 2"
      [] c = "or_non_dict" -> "TypeError: unsupported operand type(s) for |: 'dict' and 'list'"
      [] c = "ior_iterable" -> "{'a': 1}"
      [] c = "copy_shallow" -> "({'k': [1]}, {'k': [1], 'n': 1})"
      [] c = "clear" -> "{}"
      [] c = "len_iter_reversed" -> "(4, ['one', 'two', 'three', 'four'], ['four', 'three', 'two', 'one'], [4, 3, 2, 1])"
      [] c = "order_reinsert" -> "{'one': 42, 'two': None}"
      [] c = "equality_ignores_order" -> "(True, False)"
      [] c = "no_ordering" -> "TypeError: '<' not supported between instances of 'dict' and 'dict'"
      [] c = "unhashable_dict" -> "TypeError: unhashable type: 'dict'"
      [] c = "view_live" -> "(['a', 'b'], [1, 2], [('a', 1), ('b', 2)], 2)"
      [] c = "view_mapping" -> "(True, 'mappingproxy', 1)"
      [] c = "view_contains" -> "(True, True, True, False)"
      [] c = "view_set_ops_iterable" -> "(['a'], ['a', 'b', 'x', 'y'], ['b'], ['b'])"
      [] c = "view_set_ops_return_set" -> "'set'"
      [] c = "values_no_set_ops" -> "TypeError: unsupported operand type(s) for &: 'dict_values' and 'set'"
      [] c = "values_equality" -> "(False, True, True)"
      [] c = "items_unhashable_value" -> "True"
      [] c = "items_set_op_unhashable" -> "TypeError: unhashable type: 'list'"
      [] c = "view_changed_size" -> "RuntimeError: dictionary changed size during iteration"
      [] c = "view_reversed_type" -> "'dict_reversekeyiterator'"
      [] c = "view_repr" -> "(\"dict_keys(['a'])\", 'dict_values([1])', \"dict_items([('a', 1)])\")"
      [] c = "view_hash" -> "TypeError: unhashable type: 'dict_keys'"
      [] c = "view_comparisons" -> "(True, True, True, False)"
      [] c = "view_isdisjoint" -> "(True, False)"
      [] c = "repr_recursive" -> "\"{'self': {...}}\""
      [] c = "iter_type_names" -> "['dict_keyiterator', 'dict_keyiterator', 'dict_valueiterator', 'dict_itemiterator']"
      [] c = "dict_subclass_or" -> "'dict'"
      [] c = "keys_order_after_pop" -> "['b', 'c', 'a']"
      [] c = "float_int_key" -> "({1: 'bool'}, 'int')"
      [] c = "nan_key" -> "(1, False)"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
IsOp == Done /\ "op" \in DOMAIN program

\* A merge holds each key of either map once, the right map's value winning,
\* with the left map's keys first in their order.
MergeLaw == IsOp =>
    LET a == program.a  b == program.b  m == Merge(a, b) IN
    /\ Keys(m) = Keys(a) \cup Keys(b)
    /\ Len(m) = Cardinality(Keys(m))
    /\ \A k \in Keys(b) : Get(m, k) = Get(b, k)
    /\ \A i \in DOMAIN a : m[i][1] = a[i][1]

\* Equal dicts have equal keys views; keys views compare as sets.
EqualKeys == IsOp /\ program.op = "equal" /\ outcome = "True" => Keys(program.a) = Keys(program.b)
=============================================================================
