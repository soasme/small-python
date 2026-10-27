------------------------------- MODULE Truth -------------------------------
(***************************************************************************)
(* Truth value testing and the Boolean operations, as The Python Language  *)
(* Reference and the built-in types chapter specify them                   *)
(* (reference/expressions.html#boolean-operations,                         *)
(* library/stdtypes.html#truth-value-testing, #boolean-operations-and-or-  *)
(* not, and #boolean-type-bool, with                                       *)
(* reference/datamodel.html#object.__bool__): an object is true unless its *)
(* type's __bool__ returns False or, lacking __bool__, its __len__ returns *)
(* zero; __bool__ must return a bool and is preferred to __len__, a        *)
(* __bool__ of None makes the object unusable as a boolean, and __len__    *)
(* must return an index that is not negative and fits a Py_ssize_t; the    *)
(* built-in constants and empty containers and zero numbers are false; not *)
(* yields a bool, while x and y and x or y test only x and yield x itself  *)
(* or y, never testing y.                                                  *)
(*                                                                         *)
(* A program applies OP (bool, not, and, or) to instances of classes of    *)
(* KIND (the right one only for and and or), each logging its __bool__ or  *)
(* __len__ call, or calls bool() on one of the built-in VALUES. A class    *)
(* has no method (plain), a __bool__ returning True, False, or 1, or None  *)
(* as __bool__, a __len__ returning 0, 3, -1, "3", 2**64, or an object     *)
(* with __index__ returning 2, or __bool__ returning False with __len__    *)
(* returning 3. The outcome is the result ("left" or "right" for and and   *)
(* or) or the exception, and the log.                                      *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Kinds == {"plain", "bool_true", "bool_false", "bool_int", "bool_none", "len_zero", "len_three", "len_negative",
          "len_str", "len_big", "len_index", "both"}
Values == {"0", "0.0", "-0.0", "0j", "''", "b''", "[]", "()", "{}", "set()", "frozenset()", "range(0)", "range(1, 1)",
           "None", "...", "NotImplemented", "float('nan')", "' '", "[0]", "frozendict()", "bytearray()",
           "memoryview(b'')", "type", "object()", "1e-300 * 1e-300"}
Programs == [op : {"bool", "not"}, left : Kinds, right : {"plain"}]
            \cup [op : {"and", "or"}, left : Kinds, right : Kinds]
            \cup [value : Values]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

\* The truth of an instance of kind k, or the exception, and its calls.
Truth(k, side) ==
    LET called(m) == <<side \o "." \o m>>
    IN  CASE k = "plain" -> <<"true", <<>>>>
          [] k = "bool_true" -> <<"true", called("bool")>>
          [] k = "bool_false" -> <<"false", called("bool")>>
          [] k = "both" -> <<"false", called("bool")>>                        \* __len__ is not called
          [] k = "bool_int" -> <<"TypeError: bool_int.__bool__() must return a bool, not int", called("bool")>>
          [] k = "bool_none" -> <<"TypeError: 'bool_none' cannot be interpreted as a boolean", <<>>>>
          [] k = "len_zero" -> <<"false", called("len")>>
          [] k = "len_three" -> <<"true", called("len")>>
          [] k = "len_index" -> <<"true", called("len")>>
          [] k = "len_negative" -> <<"ValueError: __len__() should return >= 0", called("len")>>
          [] k = "len_str" -> <<"TypeError: 'str' object cannot be interpreted as an integer", called("len")>>
          [] k = "len_big" -> <<"OverflowError: cannot fit 'int' into an index-sized integer", called("len")>>

Show(b) == IF b = "true" THEN "True" ELSE "False"
Not(b) == IF b = "true" THEN "false" ELSE "true"

False == {"0", "0.0", "-0.0", "0j", "''", "b''", "[]", "()", "{}", "set()", "frozenset()", "range(0)", "range(1, 1)",
          "None", "frozendict()", "bytearray()", "memoryview(b'')", "1e-300 * 1e-300"}

Run(p) ==
    IF "value" \in DOMAIN p THEN
        <<CASE p.value = "NotImplemented" -> "TypeError: NotImplemented should not be used in a boolean context"
            [] p.value \in False -> "False"
            [] OTHER -> "True", <<>>>>
    ELSE LET t == Truth(p.left, "L")
         IN  IF t[1] \notin {"true", "false"} THEN t
             ELSE CASE p.op = "bool" -> <<Show(t[1]), t[2]>>
                    [] p.op = "not" -> <<Show(Not(t[1])), t[2]>>
                    [] p.op = "and" -> <<IF t[1] = "true" THEN "right" ELSE "left", t[2]>>
                    [] p.op = "or" -> <<IF t[1] = "true" THEN "left" ELSE "right", t[2]>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* and and or never test the truth of their right operand.
ShortCircuit == Done /\ "op" \in DOMAIN program => \A i \in DOMAIN outcome[2] : outcome[2][i] \in {"L.bool", "L.len"}

\* At most one of __bool__ and __len__ is called.
OneCall == Done => Len(outcome[2]) <= 1
=============================================================================
