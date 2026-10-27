-------------------------- MODULE TypeAnnotations ---------------------------
(***************************************************************************)
(* Type annotation types, as the Built-in Types chapter specifies them     *)
(* (library/stdtypes.html#types-genericalias and #types-union):            *)
(* subscripting a standard generic class gives a GenericAlias whose        *)
(* __origin__ is the class, __args__ the arguments as a tuple, and         *)
(* __parameters__ the type parameters among them; the alias is callable as *)
(* its origin, forwards other attributes to it, compares and hashes by     *)
(* origin and arguments, can be a base class, can be substituted for its   *)
(* parameters (too many arguments, or none to substitute, raise            *)
(* TypeError), unpacks a tuple alias with *, and refuses isinstance() and  *)
(* issubclass(); __class_getitem__ serves a class's own subscription; X |  *)
(* Y on types (or None) gives a Union whose arguments are flattened, with  *)
(* duplicates dropped and None as NoneType, a single remaining type        *)
(* standing for itself; unions compare and hash ignoring order, support    *)
(* isinstance() and issubclass() unless an argument is a parameterized     *)
(* generic, cannot be called or subclassed, and | with a non-type is a     *)
(* TypeError.                                                              *)
(*                                                                         *)
(* A program evaluates T1 | T2 or T1 | T2 | T3 for terms among int, str,   *)
(* None, and bool, and reports the result's repr, the names of its         *)
(* __args__ (or - when the result is a single type), and whether 1, '',    *)
(* None, and True are instances of it; or runs one of the sources of CASES *)
(* in a fresh namespace. The outcome is the repr of that tuple or of the   *)
(* case's result, or the exception and its message.                        *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

VARIABLES program, outcome
vars == <<program, outcome>>

Terms == {"int", "str", "None", "bool"}
Seqs == [1..2 -> Terms] \cup [1..3 -> Terms]

RECURSIVE JoinWith(_, _)
JoinWith(s, sep) == IF s = <<>> THEN "" ELSE IF Len(s) = 1 THEN Head(s) ELSE Head(s) \o sep \o JoinWith(Tail(s), sep)
Join(s) == JoinWith(s, ", ")
Q(s) == "'" \o s \o "'"
B(b) == IF b THEN "True" ELSE "False"
Contains(s, x) == \E i \in DOMAIN s : s[i] = x

\* None stands for its type.
Type(t) == IF t = "None" THEN "NoneType" ELSE t
\* The arguments of a, then those of b not among them.
Merge(a, b) == a \o SelectSeq(b, LAMBDA x : ~Contains(a, x))

\* The types left after folding terms 1..k from the left, or <<>> when
\* None | None was evaluated.
RECURSIVE Fold(_, _)
Fold(s, k) ==
    IF k = 1 THEN <<Type(s[1])>>
    ELSE IF k = 2 /\ s[1] = "None" /\ s[2] = "None" THEN <<>>
    ELSE LET left == Fold(s, k - 1) IN IF left = <<>> THEN <<>> ELSE Merge(left, <<Type(s[k])>>)

Args(s) == Fold(s, Len(s))
Shown(t) == IF t = "NoneType" THEN "None" ELSE t
Instance(v, args) == CASE v = "1" -> Contains(args, "int")
                       [] v = "''" -> Contains(args, "str")
                       [] v = "None" -> Contains(args, "NoneType")
                       [] v = "True" -> Contains(args, "int") \/ Contains(args, "bool")


Cases == {"list_int", "dict_args", "tuple_ellipsis", "call_origin", "no_runtime_check", "isinstance_fails",
          "issubclass_fails", "eq", "unpacked", "unpack_non_tuple", "type_of_origin", "getattr_forward",
          "dir_like", "class_getitem", "subclass_alias", "nested_param", "too_many_args", "not_generic",
          "subscript_int", "union_or", "union_dedup", "union_none", "union_isinstance",
          "union_generic_isinstance", "union_nested", "union_bad", "union_bad_left", "union_hash",
          "union_generic_alias", "union_param", "union_getitem_noparams", "union_origin", "union_subclass",
          "union_eq_order", "union_call", "ga_instancecheck_inner", "ga_repr_nested",
          "ga_repr_callable_like", "ga_star_star", "ga_args_tuple_single", "ga_args_list_param",
          "ga_mro_entries", "ga_setattr", "ga_copy_attr_ok"}
Programs == [terms : Seqs]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    LET args == Args(p.terms) IN
    IF args = <<>> THEN "TypeError: unsupported operand type(s) for |: 'NoneType' and 'NoneType'"
    ELSE "(" \o (IF Len(args) = 1 THEN "\"<class " \o Q(args[1]) \o ">\", '-'"
                  ELSE Q(JoinWith([i \in DOMAIN args |-> Shown(args[i])], " | "))
                       \o ", [" \o Join([i \in DOMAIN args |-> Q(args[i])]) \o "]")
         \o ", [" \o Join([i \in 1..4 |-> B(Instance(<<"1", "''", "None", "True">>[i], args))]) \o "])"

Case(c) ==
    CASE c = "list_int" -> "('list[int]', True, (<class 'int'>,), (), 'GenericAlias')"
      [] c = "dict_args" -> "('dict[str, list[int]]', (<class 'str'>, list[int]))"
      [] c = "tuple_ellipsis" -> "('tuple[int, ...]', (), 'tuple[()]')"
      [] c = "call_origin" -> "['a', 'b']"
      [] c = "no_runtime_check" -> "[1, 2]"
      [] c = "isinstance_fails" -> "TypeError: isinstance() argument 2 cannot be a parameterized generic"
      [] c = "issubclass_fails" -> "TypeError: issubclass() argument 2 cannot be a parameterized generic"
      [] c = "eq" -> "(True, False, False, True)"
      [] c = "unpacked" -> "('*tuple[int]', True, False, 'tuple[*tuple[int, ...]]')"
      [] c = "unpack_non_tuple" -> "[*list[int]]"
      [] c = "type_of_origin" -> "(True, 'type[int]')"
      [] c = "getattr_forward" -> "(True, 'list', 'list', 'builtins')"
      [] c = "dir_like" -> "True"
      [] c = "class_getitem" -> "('cgi', <class 'int'>)"
      [] c = "subclass_alias" -> "(True, True)"
      [] c = "nested_param" -> "((T,), 'list[int]', 'dict[str, int]')"
      [] c = "too_many_args" -> "TypeError: Too many arguments for list[T]; actual 2, expected 1"
      [] c = "not_generic" -> "TypeError: list[int] is not a generic class"
      [] c = "subscript_int" -> "TypeError: type 'int' is not subscriptable"
      [] c = "union_or" -> "('int | str', 'Union', (<class 'int'>, <class 'str'>))"
      [] c = "union_dedup" -> "(\"<class 'int'>\", True, 'int | str', True)"
      [] c = "union_none" -> "('int | None', 'None | int', (<class 'int'>, <class 'NoneType'>))"
      [] c = "union_isinstance" -> "(True, False, True, True)"
      [] c = "union_generic_isinstance" -> "TypeError: isinstance() argument 2 cannot be a parameterized generic"
      [] c = "union_nested" -> "('int | str | float', (<class 'int'>, <class 'str'>, <class 'float'>))"
      [] c = "union_bad" -> "TypeError: unsupported operand type(s) for |: 'type' and 'int'"
      [] c = "union_bad_left" -> "TypeError: unsupported operand type(s) for |: 'int' and 'type'"
      [] c = "union_hash" -> "(True, 1)"
      [] c = "union_generic_alias" -> "'list[int] | None'"
      [] c = "union_param" -> "((T,), 'list[int] | None')"
      [] c = "union_getitem_noparams" -> "TypeError: int | str is not a generic class"
      [] c = "union_origin" -> "<class 'typing.Union'>"
      [] c = "union_subclass" -> "TypeError: Cannot subclass int | str"
      [] c = "union_eq_order" -> "True"
      [] c = "union_call" -> "TypeError: 'typing.Union' object is not callable"
      [] c = "ga_instancecheck_inner" -> "False"
      [] c = "ga_repr_nested" -> "'list[list[dict[str, ...]]]'"
      [] c = "ga_repr_callable_like" -> "'dict[int, ...]'"
      [] c = "ga_star_star" -> "'tuple[*tuple[int, str]]'"
      [] c = "ga_args_tuple_single" -> "(<class 'int'>,)"
      [] c = "ga_args_list_param" -> "'list[[int, str]]'"
      [] c = "ga_mro_entries" -> "((<class 'list'>,), True)"
      [] c = "ga_setattr" -> "AttributeError: 'types.GenericAlias' object has no attribute 'x' and no __dict__ for setting new attributes"
      [] c = "ga_copy_attr_ok" -> "'GenericAlias'"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
IsUnion == Done /\ "terms" \in DOMAIN program /\ Args(program.terms) # <<>>

\* A union holds each term's type once, in order of first appearance.
Flattened == IsUnion =>
    LET args == Args(program.terms) IN
    /\ \A i, j \in DOMAIN args : i < j => args[i] # args[j]
    /\ {args[i] : i \in DOMAIN args} = {Type(program.terms[i]) : i \in DOMAIN program.terms}
    /\ args[1] = Type(program.terms[1])
=============================================================================
