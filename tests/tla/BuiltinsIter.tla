---------------------------- MODULE BuiltinsIter ----------------------------
(***************************************************************************)
(* The iteration and sorting built-in functions, as The Python Standard    *)
(* Library specifies them (library/functions.html and howto/sorting.html): *)
(* iter() of an iterable or the sequence protocol, or of a callable and a  *)
(* sentinel; next() with a default; reversed() through __reversed__ or the *)
(* sequence protocol; enumerate() from start; zip() stopping at the        *)
(* shortest input, consuming inputs left to right, and with strict=True    *)
(* naming the first input of a different length; map() over several        *)
(* iterables, also strict, or of a class, each instance made, then its     *)
(* __init__ called; filter() with a function, a builtin calling each      *)
(* instance's Python method as it reaches it, or None; all() and           *)
(* any() stopping at the first deciding item; len() requiring a non-       *)
(* negative index-sized __len__; and sorted() and list.sort(), stable with *)
(* key and reverse (equal items keeping their order even reversed), a key  *)
(* that is a class, a bound method, a callable instance or a builtin      *)
(* calling each item's Python method once in item order, using only <,     *)
(* tuples ordered by their first items not equal by __eq__, and refusing a *)
(* list modified during the sort.                                          *)
(*                                                                         *)
(* A program takes a list l of up to four items among 1, 2, and 3 and      *)
(* reports one of OPS: the original positions of l's items as sorted()     *)
(* orders them by value, ascending or with reverse=True; reversed(l);      *)
(* enumerate(l, 1); zip(l, l[:2], strict=True); filter() dropping the 2s;  *)
(* the products of neighbors by map(); any() for a 3 and all() below 3,    *)
(* each with the count of items left in its iterator; iter() of a callable *)
(* taking the next item, with sentinel 2; or the first position of the     *)
(* maximum by max(key=, default=-1); or runs one of the sources of CASES   *)
(* in a fresh namespace, among them a callable iterator its own callable   *)
(* exhausts, and the sequence and callable iterators' __reduce__ and       *)
(* __setstate__ state. The outcome is the repr of the result, or the       *)
(* exception and its message.                                              *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

VARIABLES program, outcome
vars == <<program, outcome>>

Ops == {"sorted", "sorted_rev", "reversed", "enumerate", "zip_strict", "filter", "map", "any_all", "iter_sentinel",
        "max_key"}
Lists == UNION {[1..n -> {1, 2, 3}] : n \in 0..4}

R(n) == ToString(n)
B(b) == IF b THEN "True" ELSE "False"
RECURSIVE Join(_)
Join(s) == IF s = <<>> THEN "" ELSE IF Len(s) = 1 THEN Head(s) ELSE Head(s) \o ", " \o Join(Tail(s))
List(s) == "[" \o Join(s) \o "]"
Ints(s) == List([i \in DOMAIN s |-> R(s[i])])
Pair(a, b) == "(" \o R(a) \o ", " \o R(b) \o ")"

Positions(l) == [i \in 1..Len(l) |-> i]
\* A stable sort by value: the positions holding each value, in order.
Group(l, v) == SelectSeq(Positions(l), LAMBDA i : l[i] = v)
SortedBy(l, order) == Group(l, order[1]) \o Group(l, order[2]) \o Group(l, order[3])
Zero(s) == [i \in DOMAIN s |-> s[i] - 1]

\* The number of items an iterator over l still holds once the first item
\* satisfying the test has been consumed, or 0 when none does.
Rest(l, hits) == IF hits = <<>> THEN 0 ELSE Len(l) - hits[1]


Cases == {"iter_sequence_protocol", "filter_nested_generator", "enumerate_start_first", "reversed_hook", "reversed_len", "reversed_subclass", "reversed_bad", "reversed_dict", "next_default", "next_python", "next_called", "next_retry", "star_called", "adapt_python", "adapt_iter", "adapt_iter_strict", "next_stop",
          "next_non_iterator", "iter_sentinel_noncallable", "iter_two_args_kw", "zip_strict_first_shorter",
          "zip_strict_third", "zip_strict_mixed", "adapter_zip_generator", "zip_shortest", "zip_consumes", "zip_consumes_order", "map_strict",
          "map_shortest", "map_none", "map_bound", "map_class_unpack", "map_generator", "map_repr", "map_metaclass", "callable_generator", "iterator_subclass", "iterator_subclass_next", "adapter_subclass_iter", "adapter_subclass_init", "map_convert", "map_convert_bad", "map_class", "map_class_bad", "map_class_new", "callable_calls", "callable_sentinel_eq", "zip_sentinel_eq", "zip_callable", "zip_native_generator", "filter_generator", "starred_calls", "map_hash_tuple", "map_adapted", "map_index", "map_index_bad", "callable_bound", "sorted_sources", "sorted_later_calls", "filter_none", "filter_truth", "filter_builtin", "filter_next", "filter_adapted", "filter_next_truth",
          "filter_truth_bad", "enumerate_kw", "enumerate_bad_start", "all_any_empty",
          "all_returns_bool", "sorted_key_none", "sorted_unknown_keyword", "sorted_positional_key", "sorted_mixed",
          "sorted_returns_new", "list_sort_none", "sort_stability_doc", "sort_reverse_stable",
          "sort_mutated", "sort_key_error", "sort_key_callables", "sort_builtin_keys", "builtin_key_iterators", "key_sources", "consume_getitem", "sort_lt_only", "sort_tuple_ties", "sort_list_ties", "sort_tuple_lt_only", "sort_gt_reflected", "sort_lt_declined", "min_reflected_truth", "sort_truth", "sort_reverse_truth", "max_key_truth", "len_negative", "len_big",
          "len_float", "len_unsized", "sum_iter", "aiter_sync", "slice_builtin", "range_iter_type",
          "iter_sentinel_reentrant", "iter_sentinel_reduce", "iter_sequence_state", "range_state_index"}
Programs == [op : Ops, l : Lists]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    LET l == p.l  n == Len(l) IN
    CASE p.op = "sorted" -> Ints(Zero(SortedBy(l, <<1, 2, 3>>)))
      [] p.op = "sorted_rev" -> Ints(Zero(SortedBy(l, <<3, 2, 1>>)))
      [] p.op = "reversed" -> Ints([i \in 1..n |-> l[n + 1 - i]])
      [] p.op = "enumerate" -> List([i \in 1..n |-> Pair(i, l[i])])
      [] p.op = "zip_strict" -> IF n > 2 THEN "ValueError: zip() argument 2 is shorter than argument 1"
                                ELSE List([i \in 1..n |-> Pair(l[i], l[i])])
      [] p.op = "filter" -> Ints(SelectSeq(l, LAMBDA x : x # 2))
      [] p.op = "map" -> Ints([i \in 1..(n - 1) |-> l[i] * l[i + 1]])
      [] p.op = "any_all" ->
            LET threes == SelectSeq(Positions(l), LAMBDA i : l[i] = 3) IN
            "(" \o B(threes # <<>>) \o ", " \o R(Rest(l, threes)) \o ", " \o B(threes = <<>>) \o ", "
            \o R(Rest(l, threes)) \o ")"
      [] p.op = "iter_sentinel" ->
            LET twos == SelectSeq(Positions(l), LAMBDA i : l[i] = 2) IN
            Ints(IF twos = <<>> THEN l ELSE SubSeq(l, 1, twos[1] - 1))
      [] p.op = "max_key" ->
            IF n = 0 THEN "-1"
            ELSE R(CHOOSE i \in 0..(n - 1) : (\A j \in 1..n : l[j] <= l[i + 1]) /\ \A j \in 1..i : l[j] < l[i + 1])

Case(c) ==
    CASE c = "iter_sequence_protocol" -> "([0, 10, 20], [20, 10, 0], True)"
      \* enumerate() converts its start, by position or keyword, before it calls iter() of the iterable.
      [] c = "enumerate_start_first" -> "([(3, 'a'), (4, 'b')], [(3, 'a'), (4, 'b')], ['index', 'iter', 'index', 'iter'])"
      \* A filter inside another adapter tests each item of its generator as the generator yields it.
      [] c = "filter_nested_generator" -> "([(1, 'a'), (3, 'b')], [(0, 1), (1, 2), (2, 3)], (1, 1), [1, ('odd', 1), 2, ('odd', 2), 3, ('odd', 3), 0, ('odd', 0), 1, 2, 3, 0, 1, 1, ('odd', 1)])"
      [] c = "reversed_hook" -> "['r', 'e', 'v']"
      \* reversed() of a sequence calls its Python __len__, which must give a
      \* length and must exist
      [] c = "reversed_len" -> "([2, 1, 0], [-1, 'neg', 'nolen', 3])"
      \* A reversed subclass's call reverses by the sequence's Python
      \* __len__, and gives a Python __reversed__'s result as it is.
      [] c = "reversed_subclass" -> "('R', 1, 0, 'list_iterator', ['len', 'rev'])"
      [] c = "reversed_bad" -> "TypeError: 'set' object is not reversible"
      [] c = "reversed_dict" -> "[3, 1]"
      [] c = "next_default" -> "(1, 'end', None)"
      \* a class's Python __next__, and its StopIteration giving the default
      [] c = "next_python" -> "(0, 'end', None)"
      \* next() of a sequence's iterator calls its __getitem__, and of a map or
      \* filter its function, a StopIteration from it giving the default
      [] c = "next_called" -> "(0, 'end', 4, 'stop', 3)"
      \* a sequence iterator tries an index again after its __getitem__ raised
      [] c = "next_retry" -> "[0, 1]"
      \* a starred iterator over a sequence, reversed one or map in a display
      \* calls __getitem__, __len__ for each length hint, or the function
      [] c = "star_called" -> "([0, 1], (2,), (1, 0), 3)"
      \* enumerate, zip and map take an instance's items from its Python __next__,
      \* a zip ending at the first StopIteration
      [] c = "adapt_python" -> "([(0, 1), (1, 0)], [('a', 2), ('b', 1)], [0], 'end')"
      \* creating zip, map, enumerate and filter calls each instance's Python
      \* __iter__ in order, an error stopping the iterables after it
      [] c = "adapt_iter" -> "([(1, 2, 3)], [4], [(0, 5)], [6], [(1,), (), (1,), (3,), (4,), (5,), (0, 6)])"
      \* and so does one given strict, a bool or an int, then checking lengths
      [] c = "adapt_iter_strict" -> "('zip() argument 2 is longer than argument 1', [5], [(1,), (2, 3), (4,), (5,)])"
      [] c = "next_stop" -> "StopIteration: "
      [] c = "next_non_iterator" -> "TypeError: 'list' object is not an iterator"
      [] c = "iter_sentinel_noncallable" -> "TypeError: iter(v, w): v must be callable"
      [] c = "iter_two_args_kw" -> "TypeError: iter() takes no keyword arguments"
      [] c = "zip_strict_first_shorter" -> "ValueError: zip() argument 2 is longer than argument 1"
      [] c = "zip_strict_third" -> "ValueError: zip() argument 3 is shorter than arguments 1-2"
      \* a strict zip of instances and generators takes each item in turn, then
      \* asks each later one, an instance or a generator, for one more
      [] c = "zip_strict_mixed" -> "([(5, 0, 0)], [('it', 1), ('gen', 5), ('it', 0), ('gen', 6), 'zip() argument 2 is longer than argument 1', ('gen', 5), ('it', 1), ('it', 1), ('it', 0), ('it', 0)])"
      \* enumerate and filter of a zip mixing an instance and a generator take
      \* each item in order, the generator's reaching the zip first
      [] c = "adapter_zip_generator" -> "([(0, (1, 5)), (1, (0, 6))], [(0, 0)], [('it', 2), ('gen', 5), ('it', 1), ('gen', 6), ('it', 0), ('it', 1), ('gen', 0), ('it', 0)])"
      [] c = "zip_shortest" -> "([('a', 0), ('b', 1)], [], [('a',)])"
      [] c = "zip_consumes" -> "[2, 3]"
      [] c = "zip_consumes_order" -> "[1, 2, 3]"
      [] c = "map_strict" -> "ValueError: map() argument 2 is shorter than argument 1"
      [] c = "map_shortest" -> "[2, 9]"
      [] c = "map_none" -> "TypeError: 'NoneType' object is not callable"
      \* a bound method or callable instance is called with its self first
      [] c = "map_bound" -> "([3, 5], [12])"
      \* unpacking takes a map's class calls one at a time, one more for the check
      [] c = "map_class_unpack" -> "('ValueError', [1, 2, 3])"
      \* next() and a generator's own send and close resume each generator,
      \* close running its cleanup
      [] c = "map_generator" -> "([0, 0], ['a', 'b'], [None], [('a', 0), ('b', 0), 'fin'])"
      \* repr() and ascii() of containers call each item's Python __repr__
      [] c = "map_repr" -> "(['[r]', '(r,)'], ['[r]'], 3)"
      \* dir() and len() of classes call their metaclass's Python methods
      [] c = "map_metaclass" -> "([['a', 'b']], [1], 2)"
      \* iter() of a generator's __next__ resumes it until the sentinel
      [] c = "callable_generator" -> "([1, 2], (1, 'end'))"
      \* An enumerate or zip subclass keeping __iter__ and __next__ gives its builtin's items.
      [] c = "iterator_subclass" -> "([(0, 1), (1, 2)], ((1, 'a'),), (0, 1), 'end')"
      \* next() of one, its super().__next__() and the builtin's own __next__ resume its generator.
      [] c = "iterator_subclass_next" -> "((0, 1), (0, 2), (1, 3), 'end')"
      \* Calling such a subclass calls its iterables' Python __iter__, its instance carrying the iterator.
      [] c = "adapter_subclass_iter" -> "('E', [(1, 0), (2, 1)], [(0, 0)], 3)"
      \* So does one defining __init__, called after them with the call's
      \* arguments, enumerate's named, zip's strict taken by its truth.
      [] c = "adapter_subclass_init" -> "([(2, 0), (3, 1)], [(0, 0)], [2, 'init', 1, 2, 'init'])"
      \* map() of str, repr or format calls each item's method as it takes it
      [] c = "map_convert" -> "(['k1', 'k2'], ['K1', '7'], 'k1,k2', ['F'], ['s1', 's2', 'r1', 's1', 's2', 'f'])"
      [] c = "map_convert_bad" -> "TypeError: W.__str__() must return a str, not int"
      \* map() of a class makes each instance, then calls its Python __init__
      \* with the items, as it takes them; __init__ returns None.
      [] c = "map_class" -> "([(1, 'a'), (2, 'b')], [1, ('t', 1), 2, ('t', 2)])"
      [] c = "map_class_bad" -> "TypeError: __init__() should return None, not 'int'"
      \* so does one with a Python __new__, called with the class first: an
      \* instance of the class is initialized, another result is the item.
      [] c = "map_class_new" -> "(['z', 2, 3], [('n', 0), ('n', 2), ('i', 2), ('n', 3), ('i', 3)])"
      \* a builtin called with starred arguments calls each item's method in turn
      [] c = "starred_calls" -> "(True, 's', 'f', [0, 1, 'str', 'format'])"
      \* iter(f, sentinel) of a Python f calls it for each item, ending at the sentinel
      \* zip and enumerate of iter(f, sentinel) call a Python f for each item, after a str's
      [] c = "zip_callable" -> "([('x', 1), ('y', 2)], [(0, 1), (1, 2)], [1, 2, 3, 1, 2, 3])"
      \* a filter's Python function tests each item its generator yields before the next
      [] c = "filter_generator" -> "([1, 3], [0, 0, 1, -1, 2, -2, 3, -3])"
      [] c = "zip_native_generator" -> "([('a', 0), ('b', 1)], {120: 0}, 'c', [0, 1, 0, 0])"
      [] c = "callable_calls" -> "([1, 2], 3, [1, 2], 1, [1, 2, 3, 1, 2, 3, 1, 2, 3, 1])"
      \* A bound method's and a callable instance's calls, until the sentinel.
      [] c = "callable_bound" -> "([1, 2], [1, 2, 3], 1)"
      [] c = "callable_sentinel_eq" -> "([1, 2], [0], [(3, 1), (3, 2), (3, 3), (1, 0), (1, 1)])"
      [] c = "zip_sentinel_eq" -> "([(1, 'a'), (2, 'b')], [(0, 4)], [(3, 1), (3, 2), (3, 3), (5, 4), (5, 5)])"
      \* map() of hash hashes a tuple's items in order, nested tuples first
      [] c = "map_hash_tuple" -> "(True, [1, 3, 4])"
      [] c = "map_adapted" -> "([('a', '1'), ('b', '2')], [(0, '3')], [1, 2, 3])"
      \* A builtin's, a builtin type's or a builtin method's index arguments
      \* convert by their __index__ for each item, in order.
      [] c = "map_index" -> "([2.2, 3.38], [4], ['a  '], ['c'], [1, 2, 3, 3, -1])"
      [] c = "map_index_bad" -> "LookupError: x"
      [] c = "sorted_sources" -> "([1, 2, 3], [3, 1], [2, 4], True)"
      \* A sort whose first comparison is of plain values, and one of nested
      \* tuples, call the later pairs' Python __eq__ and __lt__.
      [] c = "sorted_later_calls" -> "([0, 1, 1], [1, 1], ['=1', '<1', '=1', '<1', '=1', '=1', '<1'])"
      [] c = "consume_getitem" -> "([0, 1, 2], 3, [0, 1, 2], [0, 1, 2], (0, 1, 2), [2, 1, 0])"
      [] c = "filter_none" -> "[1, 'a']"
      \* filter() of None or bool takes each item's truth by __bool__ or __len__
      [] c = "filter_truth" -> "([1, 3], [1], ['b1', 'b0', 'l3', 'b0', 'b1'])"
      [] c = "filter_truth_bad" -> "TypeError: Bad.__bool__() must return a bool, not int"
      [] c = "enumerate_kw" -> "([(-1, 'a'), (0, 'b')], [(0, 'a')])"
      [] c = "enumerate_bad_start" -> "TypeError: 'float' object cannot be interpreted as an integer"
      [] c = "all_any_empty" -> "(True, False, False, True)"
      [] c = "all_returns_bool" -> "(True, True)"
      [] c = "sorted_key_none" -> "(['a', 'b', 'c'], [3, 2, 1])"
      \* sorted() takes the items before sort refuses an unknown keyword
      [] c = "sorted_unknown_keyword" -> "('TypeError', [3, 1])"
      [] c = "sorted_positional_key" -> "TypeError: sorted expected 1 argument, got 2"
      [] c = "sorted_mixed" -> "TypeError: '<' not supported between instances of 'str' and 'int'"
      [] c = "sorted_returns_new" -> "([3, 1], [1, 3], False)"
      [] c = "list_sort_none" -> "(None, [1, 2])"
      [] c = "sort_stability_doc" -> "[('blue', 1), ('blue', 2), ('red', 1), ('red', 2)]"
      [] c = "sort_reverse_stable" -> "[(1, 'a'), (1, 'c'), (0, 'b')]"
      [] c = "sort_mutated" -> "ValueError: list modified during sort"
      [] c = "sort_key_error" -> "ZeroDivisionError: division by zero"
      [] c = "sort_key_callables" -> "([3, 2, 1], [2, 4, 1, 3], 1)"
      [] c = "filter_builtin" -> "([1, 'a', 2], [('len', 1), ('len', 0), ('len', 2)])"
      \* filter() of an iterator instance takes each item by its Python
      \* __next__ before testing it, whatever its function.
      [] c = "filter_next" -> "([1, 2], [1], [-3], 2, 11)"
      \* filter of a __getitem__ iterator, iter(f, sentinel) or a map takes each item by its call.
      [] c = "filter_adapted" -> "([1, 1], [1, 2], [1], 8)"
      \* next() of a filter by truth or a builtin calls the items' Python methods until one is kept.
      [] c = "filter_next_truth" -> "(2, 3, 'end', 4)"
      [] c = "sort_builtin_keys" -> "([k0, 'a', k2], k3, k4, [k1, k2, k3], [3, 1, 2, 2, 0, 4, 5])"
      [] c = "builtin_key_iterators" -> "([k1, k2, k3], k3, [k1, k2], [k4, k5], [3, 1, 2, 3, 1, 2, 1, 2, 5, 4])"
      [] c = "key_sources" -> "([1, 0], 0, 'd', [0, 1, 'k0', 'k1', 0, 'k0', 1, 'k1'])"
      [] c = "sort_lt_only" -> "[1, 2, 3]"
      [] c = "sort_tuple_ties" -> "([0, 1, 2], True)"
      [] c = "sort_list_ties" -> "([0, 1, 2], True, True)"
      [] c = "sort_tuple_lt_only" -> "([0, 1, 2], [2, 1, 0], True)"
      [] c = "sort_gt_reflected" -> "[1, 2]"
      [] c = "sort_lt_declined" -> "([1, 2, 3], [0, 1], 'KeyError')"
      \* min() and max() call the best's reflected method after an item's
      \* NotImplemented, and a result's __bool__, in order
      [] c = "min_reflected_truth" -> "(1, 3, ['lt', 'gt', 'bool', 'gt', 'bool'])"
      \* a sort orders a pair by the truth of its __lt__ or __eq__ result
      [] c = "sort_truth" -> "([1, 2], [(1, 1), (1, 2)], ['lt', 'bool', 'eq', 'bool'])"
      \* a sort takes reverse's truth, by its __bool__ or __len__, before its
      \* key calls, while list.sort's list still holds its items
      [] c = "sort_reverse_truth" -> "([3, 1], [1, 3], [('bool', 2), ('key', 1), ('key', 3), 'len'])"
      \* max() by a key calls the best key's reflected method first when the key
      \* has only object's, then the result's __bool__
      [] c = "max_key_truth" -> "(3, ['lt', 'bool', 'lt', 'bool'])"
      [] c = "len_negative" -> "ValueError: __len__() should return >= 0"
      [] c = "len_big" -> "OverflowError: cannot fit 'int' into an index-sized integer"
      [] c = "len_float" -> "TypeError: 'float' object cannot be interpreted as an integer"
      [] c = "len_unsized" -> "TypeError: object of type 'int' has no len()"
      [] c = "sum_iter" -> "14"
      [] c = "aiter_sync" -> "TypeError: 'list' object is not an async iterable"
      [] c = "slice_builtin" -> "([1, 3], (0, 3, 1), 'slice(1, 2, None)')"
      [] c = "range_iter_type" -> "'range_iterator'"
      [] c = "iter_sentinel_reentrant" -> "([], 2, ((),))"
      [] c = "iter_sentinel_reduce" -> "(<class 'int'>, 1)"
      [] c = "iter_sequence_state" -> "(1, 0, [3], ((),))"
      \* A range iterator's state converts by its Python __index__ once
      [] c = "range_state_index" -> "([3, 4], ['i'])"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
IsOp == Done /\ "op" \in DOMAIN program

\* Sorting permutes the positions, orders the values, and keeps equal
\* values in their original order, ascending or reversed.
Stable == IsOp =>
    \A order \in {<<1, 2, 3>>, <<3, 2, 1>>} :
        LET l == program.l  s == SortedBy(l, order)  rank(v) == CHOOSE k \in 1..3 : order[k] = v IN
        /\ Len(s) = Len(l)
        /\ {s[i] : i \in DOMAIN s} = DOMAIN l
        /\ \A i, j \in DOMAIN s : i < j => rank(l[s[i]]) < rank(l[s[j]]) \/ (l[s[i]] = l[s[j]] /\ s[i] < s[j])
=============================================================================
