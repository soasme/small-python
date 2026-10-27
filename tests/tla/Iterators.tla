----------------------------- MODULE Iterators ------------------------------
(***************************************************************************)
(* Iterator types, as the Built-in Types chapter specifies them            *)
(* (library/stdtypes.html#iterator-types and #generator-types, with iter() *)
(* and next() of library/functions.html): an iterable's __iter__ returns   *)
(* an iterator, whose own __iter__ returns itself and whose __next__       *)
(* returns the next item or raises StopIteration, and keeps raising it     *)
(* once it has; iter() and for reject a non-iterable, an __iter__ of None, *)
(* and an __iter__ that returns something without __next__, and fall back  *)
(* to the sequence protocol, which stops at IndexError or StopIteration;   *)
(* iter(callable, sentinel) calls until a result equals the sentinel;      *)
(* next() returns a default instead of raising; a generator implements the *)
(* protocol, its StopIteration becoming RuntimeError; and dicts and sets   *)
(* refuse to change size during iteration.                                 *)
(*                                                                         *)
(* A program takes an iterator of KIND over n items (10, 20, or a kind's   *)
(* own items), checks that iter() of it is itself, calls next n + 2 times, *)
(* logging each item or 'stop', and then, for a kind over a growable       *)
(* source, appends to the source and calls next once more; or runs one of  *)
(* the sources of CASES in a fresh namespace. The outcome is the log, or   *)
(* the repr of the case's result or its exception and message.             *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Kinds == {"list", "tuple", "str", "bytes", "bytearray", "dict", "dict_values", "dict_items", "set", "frozenset",
          "range", "reversed", "enumerate", "zip", "map", "filter", "generator", "callable_iterator",
          "sequence_protocol", "custom_iterator", "genexpr", "memoryview"}
Growable == {"list", "bytearray", "reversed", "sequence_protocol"}

R(n) == ToString(n)

\* The i-th item of an iterator of kind k over n items.
Item(k, n, i) ==
    CASE k = "str" -> IF i = 1 THEN "'a'" ELSE "'b'"
      [] k = "dict_values" -> R(10 * i + 1)
      [] k = "dict_items" -> "(" \o R(10 * i) \o ", " \o R(10 * i + 1) \o ")"
      [] k = "reversed" -> R(10 * (n + 1 - i))
      [] k = "enumerate" -> "(" \o R(i - 1) \o ", " \o R(10 * i) \o ")"
      [] k = "zip" -> "(" \o R(10 * i) \o ", " \o R(10 * i) \o ")"
      [] k = "map" -> "'" \o R(10 * i) \o "'"
      [] OTHER -> R(10 * i)

RECURSIVE Join(_)
Join(s) == IF s = <<>> THEN "" ELSE IF Len(s) = 1 THEN Head(s) ELSE Head(s) \o ", " \o Join(Tail(s))

\* Exhaustion is permanent: every later next, even after the source grows,
\* raises StopIteration.
Log(k, n) == <<"True">> \o [i \in 1..n |-> Item(k, n, i)] \o <<"'stop'", "'stop'">>
             \o (IF k \in Growable THEN <<"'stop'">> ELSE <<>>)


Cases == {"iter_returns_non_iterator", "for_returns_non_iterator", "no_next", "iter_none", "for_iter_none",
          "not_iterable", "for_not_iterable", "next_not_iterator", "next_default",
          "next_default_exhausted_twice", "generator_stopiteration", "for_stops_at_first",
          "broken_iterator_revives", "iter_prefers_dunder_iter", "sequence_index_error",
          "sequence_stop_iteration", "sequence_lookup_error", "callable_not_callable",
          "callable_sentinel_equality", "iter_of_iterator_is_self", "for_calls_iter_once",
          "list_iterator_mutation", "dict_changed_size", "set_changed_size", "dict_keys_replaced_ok",
          "iterator_type_names", "length_hint", "next_dunder_direct", "zip_strict", "map_multi",
          "enumerate_start", "reversed_not_sequence", "reversed_dunder"}
Programs == [kind : Kinds, n : 0..2]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Generated(p) == "[" \o Join(Log(p.kind, p.n)) \o "]"

Case(c) ==
    CASE c = "iter_returns_non_iterator" -> "TypeError: NonIter.__iter__() must return an iterator, not int"
      [] c = "for_returns_non_iterator" -> "TypeError: NonIter.__iter__() must return an iterator, not int"
      [] c = "no_next" -> "TypeError: NoNext.__iter__() must return an iterator, not NoNext"
      [] c = "iter_none" -> "TypeError: 'IterNone' object is not iterable"
      [] c = "for_iter_none" -> "TypeError: 'IterNone' object is not iterable"
      [] c = "not_iterable" -> "TypeError: 'Plain' object is not iterable"
      [] c = "for_not_iterable" -> "TypeError: 'int' object is not iterable"
      [] c = "next_not_iterator" -> "TypeError: 'list' object is not an iterator"
      [] c = "next_default" -> "'default'"
      [] c = "next_default_exhausted_twice" -> "(1, 'd', 'd')"
      [] c = "generator_stopiteration" -> "RuntimeError: generator raised StopIteration"
      [] c = "for_stops_at_first" -> "[1]"
      [] c = "broken_iterator_revives" -> "([1], 3)"
      [] c = "iter_prefers_dunder_iter" -> "[1, 2]"
      [] c = "sequence_index_error" -> "[0, 1]"
      [] c = "sequence_stop_iteration" -> "[0]"
      [] c = "sequence_lookup_error" -> "KeyError: 0"
      [] c = "callable_not_callable" -> "TypeError: iter(v, w): v must be callable"
      [] c = "callable_sentinel_equality" -> "[1]"
      [] c = "iter_of_iterator_is_self" -> "True"
      [] c = "for_calls_iter_once" -> "1"
      [] c = "list_iterator_mutation" -> "[1, 3]"
      [] c = "dict_changed_size" -> "RuntimeError: dictionary changed size during iteration"
      [] c = "set_changed_size" -> "RuntimeError: Set changed size during iteration"
      [] c = "dict_keys_replaced_ok" -> "{1: 0, 2: 0}"
      [] c = "iterator_type_names" -> "['bytearray_iterator', 'bytes_iterator', 'dict_keyiterator', 'list_iterator', 'range_iterator', 'set_iterator', 'str_ascii_iterator', 'tuple_iterator']"
      [] c = "length_hint" -> "2"
      [] c = "next_dunder_direct" -> "('a', 'b')"
      [] c = "zip_strict" -> "ValueError: zip() argument 2 is shorter than argument 1"
      [] c = "map_multi" -> "[8, 9]"
      [] c = "enumerate_start" -> "[(5, 'a'), (6, 'b')]"
      [] c = "reversed_not_sequence" -> "TypeError: 'set' object is not reversible"
      [] c = "reversed_dunder" -> "['z', 'y']"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* After the items, an iterator only ever raises StopIteration.
StaysExhausted == Done /\ "kind" \in DOMAIN program =>
    LET log == Log(program.kind, program.n)
    IN  \A i \in program.n + 2..Len(log) : log[i] = "'stop'"
=============================================================================
