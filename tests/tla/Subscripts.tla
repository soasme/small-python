----------------------------- MODULE Subscripts -----------------------------
(***************************************************************************)
(* Subscriptions, as The Python Language Reference specifies them          *)
(* (reference/expressions.html#subscriptions-and-slicings, its comma-      *)
(* separated and starred subscriptions and formal grammar, with            *)
(* reference/simple_stmts.html#assignment-statements and #the-del-         *)
(* statement and reference/datamodel.html#emulating-container-types): the  *)
(* primary is evaluated, then the subscript, which is one expression, a    *)
(* slice (a slice object), or a comma-separated list of them, possibly     *)
(* starred, making a tuple of the items with each starred iterable         *)
(* unpacked; the result is the primary's __getitem__ (__class_getitem__    *)
(* for a class) called with that key, an assignment evaluates its value    *)
(* first and calls __setitem__, and del calls __delitem__; a missing       *)
(* method raises TypeError, and the built-in sequences take indices (ints  *)
(* or objects with __index__, negative ones counting from the end, that    *)
(* fit a Py_ssize_t) and mappings keys, raising IndexError or KeyError for *)
(* missing ones and calling a dict subclass's __missing__.                 *)
(*                                                                         *)
(* A program performs ACTION (get, set, or del) on r[FORM] for an object r *)
(* whose __getitem__, __setitem__, and __delitem__ log their key, with a   *)
(* FORM such as 1, 1, 2, *t([1, 2]), 1:2, or ..., 1, where t logs a value; *)
(* or it runs one of the CASES. The outcome is the result's repr or the    *)
(* exception, and the log.                                                 *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Forms == {"one", "pair", "trailing", "empty", "star", "mixed_star", "star_empty", "slice", "slice_item", "full_slice",
          "colon", "step", "ellipsis", "walrus", "star_slice"}
Cases == {"aug_order", "not_subscriptable", "not_subscriptable_none", "no_setitem", "no_delitem", "no_delitem_key",
          "tuple_assign", "str_del", "int_del", "type_del", "type_getitem", "type_not_subscriptable", "list_neg",
          "list_out", "list_neg_out", "list_str_index", "list_float_index", "list_index_dunder", "list_big_index",
          "tuple_out", "str_out", "dict_missing", "dict_tuple_key", "dict_unhashable", "dict_missing_hook",
          "range_index", "range_out", "bytes_index", "getitem_none", "list_set_out", "list_del_out",
          "seq_getitem_iter", "generator_subscript", "star_in_slice", "star_bare_index", "nested_star"}
Programs == [form : Forms, action : {"get", "set", "del"}] \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

\* The key a form makes, and what evaluating it logs.
Key(f) ==
    CASE f = "one" -> <<"1", <<>>>>
      [] f = "pair" -> <<"(1, 2)", <<>>>>
      [] f = "trailing" -> <<"(1,)", <<>>>>                               \* r[1,]
      [] f = "empty" -> <<"()", <<>>>>                                    \* r[()]
      [] f = "star" -> <<"(1, 2)", <<"[1, 2]">>>>                         \* r[*t([1, 2])]
      [] f = "mixed_star" -> <<"(1, 2, 3)", <<"[2]">>>>                   \* r[1, *t([2]), 3]
      [] f = "star_empty" -> <<"()", <<"[]">>>>                           \* r[*t([])]
      [] f = "slice" -> <<"slice(1, 2, None)", <<>>>>
      [] f = "slice_item" -> <<"(slice(1, 2, None), 3)", <<>>>>
      [] f = "full_slice" -> <<"slice(None, None, None)", <<>>>>          \* r[::]
      [] f = "colon" -> <<"slice(None, None, None)", <<>>>>               \* r[:]
      [] f = "step" -> <<"slice(1, 2, 3)", <<>>>>
      [] f = "ellipsis" -> <<"(Ellipsis, 1)", <<>>>>
      [] f = "walrus" -> <<"1", <<>>>>                                    \* r[a := 1]
      [] f = "star_slice" -> <<"(1, slice(1, 2, None))", <<"[1]">>>>      \* r[*t([1]), 1:2]

Subscript(p) ==
    LET k == Key(p.form)
    IN  CASE p.action = "get" -> <<k[1], <<"r">> \o k[2] \o <<"get " \o k[1]>>>>
          [] p.action = "set" -> <<"None", <<"'v'", "r">> \o k[2] \o <<"set " \o k[1] \o " 'v'">>>>
          [] p.action = "del" -> <<"None", <<"r">> \o k[2] \o <<"del " \o k[1]>>>>

Case(c) ==
    CASE c = "aug_order" -> <<"None", <<"a", "0", "get", "5", "set 6">>>>  \* get before the value, set after
      [] c = "not_subscriptable" -> <<"TypeError: 'int' object is not subscriptable", <<>>>>
      [] c = "not_subscriptable_none" -> <<"TypeError: 'NoneType' object is not subscriptable", <<>>>>
      [] c = "no_setitem" -> <<"TypeError: 'G' object does not support item assignment", <<>>>>
      [] c = "no_delitem" -> <<"TypeError: 'G' object doesn't support item deletion", <<>>>>
      [] c = "no_delitem_key" -> <<"TypeError: 'G' object does not support item deletion", <<>>>>
      [] c = "tuple_assign" -> <<"TypeError: 'tuple' object does not support item assignment", <<>>>>
      [] c = "str_del" -> <<"TypeError: 'str' object doesn't support item deletion", <<>>>>
      [] c = "int_del" -> <<"TypeError: 'int' object does not support item deletion", <<>>>>
      [] c = "type_del" -> <<"TypeError: 'type' object does not support item deletion", <<>>>>
      [] c = "type_getitem" -> <<"('cg', (<class 'int'>, <class 'str'>))", <<>>>>
      [] c = "type_not_subscriptable" -> <<"TypeError: type 'G' is not subscriptable", <<>>>>
      [] c = "list_neg" -> <<"(3, 'a', 2)", <<>>>>
      [] c \in {"list_out", "list_neg_out"} -> <<"IndexError: list index out of range", <<>>>>
      [] c = "list_str_index" -> <<"TypeError: list indices must be integers or slices, not str", <<>>>>
      [] c = "list_float_index" -> <<"TypeError: list indices must be integers or slices, not float", <<>>>>
      [] c = "list_index_dunder" -> <<"6", <<>>>>
      [] c = "list_big_index" -> <<"IndexError: cannot fit 'int' into an index-sized integer", <<>>>>
      [] c = "tuple_out" -> <<"IndexError: tuple index out of range", <<>>>>
      [] c = "str_out" -> <<"IndexError: string index out of range", <<>>>>
      [] c = "dict_missing" -> <<"KeyError: 'k'", <<>>>>
      [] c = "dict_tuple_key" -> <<"'x'", <<>>>>
      [] c = "dict_unhashable" -> <<"TypeError: cannot use 'list' as a dict key", <<>>>>
      [] c = "dict_missing_hook" -> <<"('missing', 'k')", <<>>>>
      [] c = "range_index" -> <<"(9, 6, range(2, 5))", <<>>>>
      [] c = "range_out" -> <<"IndexError: range object index out of range", <<>>>>
      [] c = "bytes_index" -> <<"(97, 98)", <<>>>>
      [] c = "getitem_none" -> <<"TypeError: 'NoneType' object is not callable", <<>>>>
      [] c \in {"list_set_out", "list_del_out"} -> <<"IndexError: list assignment index out of range", <<>>>>
      [] c = "seq_getitem_iter" -> <<"[0, 1, 2]", <<>>>>
      [] c = "generator_subscript" -> <<"SyntaxError: invalid syntax", <<>>>>
      [] c = "star_in_slice" -> <<"SyntaxError: invalid syntax", <<>>>>
      [] c = "star_bare_index" -> <<"SyntaxError: Invalid star expression", <<>>>>
      [] c = "nested_star" -> <<"(1, 2)", <<"(1,)", "(2,)", "get (1, 2)">>>>

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Subscript(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
IsSubscript == Done /\ "form" \in DOMAIN program

\* The container method is called exactly once, last, after the subscript.
MethodLast == IsSubscript =>
    LET methods == {"get", "set", "del"}
    IN  \A i \in 1..(Len(outcome[2]) - 1) : outcome[2][i] \notin {m \o " " \o Key(program.form)[1] : m \in methods}

\* An assignment evaluates its value before the container and the key.
ValueFirst == IsSubscript /\ program.action = "set" => outcome[2][1] = "'v'"
=============================================================================
