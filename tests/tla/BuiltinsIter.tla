---------------------------- MODULE BuiltinsIter ----------------------------
(***************************************************************************)
(* The iteration and sorting built-in functions, as The Python Standard    *)
(* Library specifies them (library/functions.html and howto/sorting.html): *)
(* iter() of an iterable or the sequence protocol, or of a callable and a  *)
(* sentinel; next() with a default; reversed() through __reversed__ or the *)
(* sequence protocol; enumerate() from start; zip() stopping at the        *)
(* shortest input, consuming inputs left to right, and with strict=True    *)
(* naming the first input of a different length; map() over several        *)
(* iterables, also strict; filter() with a function or None; all() and     *)
(* any() stopping at the first deciding item; len() requiring a non-       *)
(* negative index-sized __len__; and sorted() and list.sort(), stable with *)
(* key and reverse (equal items keeping their order even reversed), using  *)
(* only <, and refusing a list modified during the sort.                   *)
(*                                                                         *)
(* A program takes a list l of up to four items among 1, 2, and 3 and      *)
(* reports one of OPS: the original positions of l's items as sorted()     *)
(* orders them by value, ascending or with reverse=True; reversed(l);      *)
(* enumerate(l, 1); zip(l, l[:2], strict=True); filter() dropping the 2s;  *)
(* the products of neighbors by map(); any() for a 3 and all() below 3,    *)
(* each with the count of items left in its iterator; iter() of a callable *)
(* taking the next item, with sentinel 2; or the first position of the     *)
(* maximum by max(key=, default=-1); or runs one of the sources of CASES   *)
(* in a fresh namespace. The outcome is the repr of the result, or the     *)
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


Cases == {"iter_sequence_protocol", "reversed_hook", "reversed_bad", "reversed_dict", "next_default", "next_stop",
          "next_non_iterator", "iter_sentinel_noncallable", "iter_two_args_kw", "zip_strict_first_shorter",
          "zip_strict_third", "zip_shortest", "zip_consumes", "zip_consumes_order", "map_strict",
          "map_shortest", "map_none", "filter_none", "enumerate_kw", "enumerate_bad_start", "all_any_empty",
          "all_returns_bool", "sorted_key_none", "sorted_positional_key", "sorted_mixed",
          "sorted_returns_new", "list_sort_none", "sort_stability_doc", "sort_reverse_stable",
          "sort_mutated", "sort_key_error", "sort_lt_only", "sort_gt_reflected", "len_negative", "len_big",
          "len_float", "len_unsized", "sum_iter", "aiter_sync", "slice_builtin", "range_iter_type"}
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
      [] c = "reversed_hook" -> "['r', 'e', 'v']"
      [] c = "reversed_bad" -> "TypeError: 'set' object is not reversible"
      [] c = "reversed_dict" -> "[3, 1]"
      [] c = "next_default" -> "(1, 'end', None)"
      [] c = "next_stop" -> "StopIteration: "
      [] c = "next_non_iterator" -> "TypeError: 'list' object is not an iterator"
      [] c = "iter_sentinel_noncallable" -> "TypeError: iter(v, w): v must be callable"
      [] c = "iter_two_args_kw" -> "TypeError: iter() takes no keyword arguments"
      [] c = "zip_strict_first_shorter" -> "ValueError: zip() argument 2 is longer than argument 1"
      [] c = "zip_strict_third" -> "ValueError: zip() argument 3 is shorter than arguments 1-2"
      [] c = "zip_shortest" -> "([('a', 0), ('b', 1)], [], [('a',)])"
      [] c = "zip_consumes" -> "[2, 3]"
      [] c = "zip_consumes_order" -> "[1, 2, 3]"
      [] c = "map_strict" -> "ValueError: map() argument 2 is shorter than argument 1"
      [] c = "map_shortest" -> "[2, 9]"
      [] c = "map_none" -> "TypeError: 'NoneType' object is not callable"
      [] c = "filter_none" -> "[1, 'a']"
      [] c = "enumerate_kw" -> "([(-1, 'a'), (0, 'b')], [(0, 'a')])"
      [] c = "enumerate_bad_start" -> "TypeError: 'float' object cannot be interpreted as an integer"
      [] c = "all_any_empty" -> "(True, False, False, True)"
      [] c = "all_returns_bool" -> "(True, True)"
      [] c = "sorted_key_none" -> "(['a', 'b', 'c'], [3, 2, 1])"
      [] c = "sorted_positional_key" -> "TypeError: sorted expected 1 argument, got 2"
      [] c = "sorted_mixed" -> "TypeError: '<' not supported between instances of 'str' and 'int'"
      [] c = "sorted_returns_new" -> "([3, 1], [1, 3], False)"
      [] c = "list_sort_none" -> "(None, [1, 2])"
      [] c = "sort_stability_doc" -> "[('blue', 1), ('blue', 2), ('red', 1), ('red', 2)]"
      [] c = "sort_reverse_stable" -> "[(1, 'a'), (1, 'c'), (0, 'b')]"
      [] c = "sort_mutated" -> "ValueError: list modified during sort"
      [] c = "sort_key_error" -> "ZeroDivisionError: division by zero"
      [] c = "sort_lt_only" -> "[1, 2, 3]"
      [] c = "sort_gt_reflected" -> "[1, 2]"
      [] c = "len_negative" -> "ValueError: __len__() should return >= 0"
      [] c = "len_big" -> "OverflowError: cannot fit 'int' into an index-sized integer"
      [] c = "len_float" -> "TypeError: 'float' object cannot be interpreted as an integer"
      [] c = "len_unsized" -> "TypeError: object of type 'int' has no len()"
      [] c = "sum_iter" -> "14"
      [] c = "aiter_sync" -> "TypeError: 'list' object is not an async iterable"
      [] c = "slice_builtin" -> "([1, 3], (0, 3, 1), 'slice(1, 2, None)')"
      [] c = "range_iter_type" -> "'range_iterator'"

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
