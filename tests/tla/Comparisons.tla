---------------------------- MODULE Comparisons ----------------------------
(***************************************************************************)
(* Comparisons, as The Python Language Reference and the built-in types    *)
(* chapter specify them (reference/expressions.html#comparisons, #value-   *)
(* comparisons, #membership-test-operations, and #is-not,                  *)
(* library/stdtypes.html#comparisons, with                                 *)
(* reference/datamodel.html#object.__lt__): x op y calls x's rich          *)
(* comparison method and, if it returns NotImplemented, y's reflected one  *)
(* (__lt__ and __gt__, __le__ and __ge__, __eq__ and __ne__ themselves),   *)
(* trying y's first when y's type is a proper subclass of x's; object's    *)
(* __eq__ is identity, its __ne__ inverts __eq__, and when both sides      *)
(* decline, == and != fall back to identity while an ordering raises       *)
(* TypeError; a method's result is returned as is; chains evaluate each    *)
(* operand once and stop at the first false link; built-in sequences       *)
(* compare lexicographically and only with their own type, mappings and    *)
(* sets by contents (sets ordering by subset), NaN is unequal to itself    *)
(* while containers test identity first, and ints and floats compare       *)
(* exactly; is compares identity; in uses __contains__ (its result made a  *)
(* bool), then iteration, then __getitem__ with indices from 0, and        *)
(* strings, bytes, and dicts and sets have their own rules.                *)
(*                                                                         *)
(* A program evaluates x OP y for an instance x of class A and y of class  *)
(* B, B either unrelated to A or a subclass of it (RELATION), where A and  *)
(* B have KIND: no comparison methods, all six returning their call's      *)
(* description ("A.__lt__(L)" when A's __lt__ is called on the left        *)
(* operand), all six returning NotImplemented, or only __eq__; or it runs  *)
(* one of the CASES. Calls and operands are logged. The outcome is the     *)
(* result's repr or the exception, and the log.                            *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Ops == {"==", "!=", "<", "<=", ">", ">="}
Kinds == {"none", "value", "notimpl", "eq_only"}
Cases == {"chain_once", "chain_short", "chain_mixed", "chain_value", "chain_value_false", "is_ident", "is_none", "nan",
          "nan_distinct", "seq_lex", "seq_type_err", "seq_elem_err", "str_int_eq", "order_err", "order_err_none",
          "dict_eq", "dict_order", "set_order", "range_eq", "int_float", "complex_order", "complex_eq", "bool_int",
          "in_list", "in_str_type", "in_bytes_type", "in_identity", "contains_nonbool", "contains_falsy",
          "contains_iter", "contains_getitem", "contains_none", "contains_is_none", "contains_raises",
          "in_dict_unhashable", "in_set_unhashable", "in_set_of_set", "not_in_precedence", "eq_returns_value",
          "hash_none_eq", "list_identity_shortcut"}
Programs == [op : Ops, left : Kinds, right : Kinds, relation : {"unrelated", "sub"}] \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

Method == [o \in Ops |-> CASE o = "==" -> "__eq__" [] o = "!=" -> "__ne__" [] o = "<" -> "__lt__"
                           [] o = "<=" -> "__le__" [] o = ">" -> "__gt__" [] o = ">=" -> "__ge__"]
Reflected == [o \in Ops |-> CASE o = "<" -> ">" [] o = ">" -> "<" [] o = "<=" -> ">=" [] o = ">=" -> "<="
                              [] OTHER -> o]

Defines(kind, m) == kind \in {"value", "notimpl"} \/ (kind = "eq_only" /\ m = "__eq__")

\* The class whose method m an instance of cls finds first: B, then A when B
\* subclasses A; "object" when neither defines it.
Owner(p, cls, m) ==
    IF cls = "B" /\ Defines(p.right, m) THEN "B"
    ELSE IF cls = "A" /\ Defines(p.left, m) THEN "A"
    ELSE IF cls = "B" /\ p.relation = "sub" /\ Defines(p.left, m) THEN "A"
    ELSE "object"
KindOf(p, cls) == IF cls = "A" THEN p.left ELSE p.right

\* Calling method m on the instance of cls on side: the result ("NI" for
\* NotImplemented) and the log. object's __ne__ inverts __eq__.
Call(p, cls, side, m) ==
    LET owner == Owner(p, cls, m)  entry == owner \o "." \o m \o "(" \o side \o ")"
    IN  IF owner # "object" THEN
            <<IF KindOf(p, owner) = "notimpl" THEN "NI" ELSE "'" \o entry \o "'", <<entry>>>>
        ELSE IF m = "__ne__" /\ Owner(p, cls, "__eq__") # "object" THEN
            LET eqOwner == Owner(p, cls, "__eq__")  eq == eqOwner \o ".__eq__(" \o side \o ")"
            IN  <<IF KindOf(p, eqOwner) = "notimpl" THEN "NI" ELSE "False", <<eq>>>>
        ELSE <<"NI", <<>>>>

Compare(p) ==
    LET forward == <<"A", "L", Method[p.op]>>  reflected == <<"B", "R", Method[Reflected[p.op]]>>
        first == IF p.relation = "sub" THEN reflected ELSE forward
        second == IF p.relation = "sub" THEN forward ELSE reflected
        r1 == Call(p, first[1], first[2], first[3])
        r2 == Call(p, second[1], second[2], second[3])
        fallback == CASE p.op = "==" -> "False"
                      [] p.op = "!=" -> "True"
                      [] OTHER -> "TypeError: '" \o p.op \o "' not supported between instances of 'A' and 'B'"
    IN  IF r1[1] # "NI" THEN r1
        ELSE IF r2[1] # "NI" THEN <<r2[1], r1[2] \o r2[2]>>
        ELSE <<fallback, r1[2] \o r2[2]>>

Unsupported(op, a, b) == "TypeError: '" \o op \o "' not supported between instances of '" \o a \o "' and '" \o b \o "'"
Case(c) ==
    CASE c = "chain_once" -> <<"True", <<"1", "2", "3">>>>                \* each operand once
      [] c = "chain_short" -> <<"False", <<"3", "2">>>>                   \* stops at the first false link
      [] c = "chain_mixed" -> <<"True", <<>>>>
      [] c = "chain_value" -> <<"True", <<>>>>
      [] c = "chain_value_false" -> <<"''", <<"1">>>>                     \* a false link is the result
      [] c = "is_ident" -> <<"(True, False, True, True)", <<>>>>
      [] c = "is_none" -> <<"(True, True)", <<>>>>
      [] c = "nan" -> <<"(False, True, False, True, True, True)", <<>>>>   \* identity before equality
      [] c = "nan_distinct" -> <<"False", <<>>>>
      [] c = "seq_lex" -> <<"(True, True, True, False, True, True)", <<>>>>
      [] c = "seq_type_err" -> <<Unsupported("<", "list", "tuple"), <<>>>>
      [] c = "seq_elem_err" -> <<Unsupported("<", "str", "int"), <<>>>>
      [] c = "str_int_eq" -> <<"(False, True)", <<>>>>
      [] c = "order_err" -> <<Unsupported("<", "int", "str"), <<>>>>
      [] c = "order_err_none" -> <<Unsupported("<", "NoneType", "NoneType"), <<>>>>
      [] c = "dict_eq" -> <<"(True, False)", <<>>>>
      [] c = "dict_order" -> <<Unsupported("<", "dict", "dict"), <<>>>>
      [] c = "set_order" -> <<"(True, True, False, False, True)", <<>>>>
      [] c = "range_eq" -> <<"(True, True, False)", <<>>>>
      [] c = "int_float" -> <<"(True, False, True, True, True)", <<>>>>  \* exact, not rounded
      [] c = "complex_order" -> <<Unsupported("<", "complex", "complex"), <<>>>>
      [] c = "complex_eq" -> <<"(True, True)", <<>>>>
      [] c = "bool_int" -> <<"(True, True, 2)", <<>>>>
      [] c = "in_list" -> <<"(True, True, True, True, True, True, False)", <<>>>>
      [] c = "in_str_type" -> <<"TypeError: 'in <string>' requires string as left operand, not int", <<>>>>
      [] c = "in_bytes_type" -> <<"TypeError: a bytes-like object is required, not 'str'", <<>>>>
      [] c = "in_identity" -> <<"(True, False)", <<>>>>
      [] c = "contains_nonbool" -> <<"(True, False)", <<"'yes'", "'yes'">>>>
      [] c = "contains_falsy" -> <<"False", <<>>>>
      [] c = "contains_iter" -> <<"True", <<"1", "2">>>>                  \* stops at the first match
      [] c = "contains_getitem" -> <<"(True, False)", <<"0", "10", "20", "0", "10", "20", "30">>>>
      [] c = "contains_none" -> <<"TypeError: argument of type 'C' is not a container or iterable", <<>>>>
      [] c = "contains_is_none" -> <<"TypeError: 'C' object is not a container", <<>>>>
      [] c = "contains_raises" -> <<"KeyError: 'k'", <<>>>>
      [] c = "in_dict_unhashable" -> <<"TypeError: cannot use 'list' as a dict key", <<>>>>
      [] c = "in_set_unhashable" -> <<"TypeError: cannot use 'list' as a set element", <<>>>>
      [] c = "in_set_of_set" -> <<"True", <<>>>>                          \* a set is looked up as a frozenset
      [] c = "not_in_precedence" -> <<"False", <<>>>>
      [] c = "eq_returns_value" -> <<"('x', False, 'x')", <<>>>>
      [] c = "hash_none_eq" -> <<"None", <<>>>>                           \* defining __eq__ clears __hash__
      [] c = "list_identity_shortcut" -> <<"(True, True)", <<"'eq'">>>>

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Compare(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
IsCompare == Done /\ "op" \in DOMAIN program

\* At most two comparison methods run, and only == and != never raise.
AtMostTwo == IsCompare => Len(outcome[2]) <= 2
Results == {"'" \o c \o "." \o Method[o] \o "(" \o side \o ")'" : c \in {"A", "B"}, o \in Ops, side \in {"L", "R"}}
EqualityTotal == IsCompare /\ program.op \in {"==", "!="} => outcome[1] \in {"True", "False"} \cup Results
=============================================================================
