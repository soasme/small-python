------------------------------- MODULE Ranges -------------------------------
(***************************************************************************)
(* Ranges, as the Built-in Types chapter specifies them                    *)
(* (library/stdtypes.html#ranges): range(stop) and range(start, stop,      *)
(* step) take integers or __index__ objects, step defaulting to 1 and      *)
(* start to 0, a zero step raising ValueError; r[i] = start + step * i for *)
(* i >= 0 while r[i] is short of stop in the step's direction; negative    *)
(* indices count from the end; slicing yields the range of the selected    *)
(* items; membership and index follow the items; ranges are equal and hash *)
(* alike when their sequences are, whatever their attributes; len beyond   *)
(* sys.maxsize raises OverflowError; and ranges support the common         *)
(* sequence operations except concatenation, repetition, and ordering, and *)
(* are immutable with read-only start, stop, and step.                     *)
(*                                                                         *)
(* A program builds range(start, stop, step) for start and stop among -3,  *)
(* -1, 0, 2, and 4 and every step from -2 to 2, and reports its items,     *)
(* length, first and last items (or IndexError), r[::-1], r[1:], whether 2 *)
(* is in it, and 2's index; or runs one of the sources of CASES in a fresh *)
(* namespace. The outcome is the repr of that tuple or of the case's       *)
(* result, or the exception and its message.                               *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Vs == {-3, -1, 0, 2, 4}

R(n) == ToString(n)
RECURSIVE Join(_)
Join(s) == IF s = <<>> THEN "" ELSE IF Len(s) = 1 THEN Head(s) ELSE Head(s) \o ", " \o Join(Tail(s))
Repr(a, b, s) == "range(" \o R(a) \o ", " \o R(b) \o (IF s = 1 THEN "" ELSE ", " \o R(s)) \o ")"

\* The number of i >= 0 with start + step * i short of stop.
Length(a, b, s) == IF s > 0 THEN (IF b > a THEN (b - a - 1) \div s + 1 ELSE 0)
                   ELSE (IF a > b THEN (a - b - 1) \div (-s) + 1 ELSE 0)
Items(a, b, s) == [i \in 1..Length(a, b, s) |-> a + s * (i - 1)]
At(items, i) == IF items = <<>> THEN "'IndexError'" ELSE R(items[i])

Describe(a, b, s) ==
    LET items == Items(a, b, s)  n == Len(items)
        found == {i \in 1..n : items[i] = 2}
    IN  "(" \o "[" \o Join([i \in 1..n |-> R(items[i])]) \o "], " \o R(n) \o ", " \o At(items, 1) \o ", "
        \o At(items, n) \o ", "
        \* r[::-1] steps back from the last item to just before the first;
        \* r[1:] starts at the second item, or at stop's position when empty.
        \o Repr(a + (n - 1) * s, a - s, -s) \o ", "
        \o Repr(a + (IF n > 0 THEN 1 ELSE 0) * s, a + n * s, s) \o ", "
        \o (IF found = {} THEN "False, 'missing'" ELSE "True, " \o R((CHOOSE i \in found : TRUE) - 1)) \o ")"


Cases == {"one_arg", "index_args", "float_arg", "str_arg", "no_args", "four_args", "keyword", "step_zero", "huge_len",
          "huge_ok", "attrs_kept", "equal_sequences", "equal_list", "hash_equal", "ordering", "concat",
          "repeat", "contains_float", "contains_bool", "contains_other", "index_missing", "count",
          "doc_example", "slice_step", "index_bad_type", "index_too_big", "immutable", "attr_readonly",
          "bool", "reversed_type", "subclass", "iter_type", "repr_step", "negative_index_out",
          "len_bool_index"}
Programs == [start : Vs, stop : Vs, step : -2..2]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Generated(p) == IF p.step = 0 THEN "ValueError: range() arg 3 must not be zero" ELSE Describe(p.start, p.stop, p.step)

Case(c) ==
    CASE c = "one_arg" -> "(range(0, 3), 0, 3, 1)"
      [] c = "index_args" -> "[1, 4]"
      [] c = "float_arg" -> "TypeError: 'float' object cannot be interpreted as an integer"
      [] c = "str_arg" -> "TypeError: 'str' object cannot be interpreted as an integer"
      [] c = "no_args" -> "TypeError: range expected at least 1 argument, got 0"
      [] c = "four_args" -> "TypeError: range expected at most 3 arguments, got 4"
      [] c = "keyword" -> "TypeError: range() takes no keyword arguments"
      [] c = "step_zero" -> "ValueError: range() arg 3 must not be zero"
      [] c = "huge_len" -> "OverflowError: Python int too large to convert to C ssize_t"
      [] c = "huge_ok" -> "(27670116110564327421, False, 3)"
      [] c = "attrs_kept" -> "(2, 1, 3, True)"
      [] c = "equal_sequences" -> "(True, False, False)"
      [] c = "equal_list" -> "False"
      [] c = "hash_equal" -> "True"
      [] c = "ordering" -> "TypeError: '<' not supported between instances of 'range' and 'range'"
      [] c = "concat" -> "TypeError: unsupported operand type(s) for +: 'range' and 'range'"
      [] c = "repeat" -> "TypeError: unsupported operand type(s) for *: 'range' and 'int'"
      [] c = "contains_float" -> "(True, False)"
      [] c = "contains_bool" -> "True"
      [] c = "contains_other" -> "False"
      [] c = "index_missing" -> "ValueError: range.index(x): x not in range"
      [] c = "count" -> "(1, 1, 0)"
      [] c = "doc_example" -> "(range(0, 20, 2), False, True, 5, 10, range(0, 10, 2), 18)"
      [] c = "slice_step" -> "(range(0, 10, 3), range(8, 1, -2), range(10, 10))"
      [] c = "index_bad_type" -> "TypeError: range indices must be integers or slices, not str"
      [] c = "index_too_big" -> "IndexError: range object index out of range"
      [] c = "immutable" -> "TypeError: 'range' object does not support item assignment"
      [] c = "attr_readonly" -> "AttributeError: readonly attribute"
      [] c = "bool" -> "(False, True)"
      [] c = "reversed_type" -> "('range_iterator', [9, 5, 1])"
      [] c = "subclass" -> "TypeError: type 'range' is not an acceptable base type"
      [] c = "iter_type" -> "'range_iterator'"
      [] c = "repr_step" -> "('range(1, 2)', 'range(1, 2, 3)')"
      [] c = "negative_index_out" -> "IndexError: range object index out of range"
      [] c = "len_bool_index" -> "(range(0, 1), 0)"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* Every item lies on the step's side of start and short of stop.
Bounded == Done /\ "step" \in DOMAIN program /\ program.step # 0 =>
    \A i \in 1..Len(Items(program.start, program.stop, program.step)) :
        LET x == Items(program.start, program.stop, program.step)[i]
        IN  IF program.step > 0 THEN program.start <= x /\ x < program.stop
            ELSE program.stop < x /\ x <= program.start
=============================================================================
