-------------------------- MODULE BuiltinsObjects ---------------------------
(***************************************************************************)
(* The object built-in functions, as The Python Standard Library specifies *)
(* them (library/functions.html): isinstance() and issubclass() against a  *)
(* class, a tuple of them (nested tuples included), or a union, through    *)
(* __instancecheck__ and __subclasscheck__, with their errors; getattr()   *)
(* with a default, hasattr() (false only on AttributeError), setattr(),    *)
(* and delattr(), which reach the instance dict and not class attributes   *)
(* or __getattr__, refusing objects without a __dict__ and read-only       *)
(* attributes; vars(), dir() (sorted, or __dir__ listed), callable(),      *)
(* id(), hash() (truncating big __hash__ results, refusing non-int ones    *)
(* and classes that set __eq__ alone), object(), and type() with one or    *)
(* three arguments.                                                        *)
(*                                                                         *)
(* A program takes an instance o of class A (with class attribute x), of   *)
(* B(A) (setting y in __init__), of C (whose __getattr__ supplies names    *)
(* starting with m), or the int 1, and reports isinstance(o, info) or      *)
(* issubclass(type(o), info) for info among A, B, (A, C), B | C, int,      *)
(* object, (), bool, and ((B,), (int,)); or getattr(o, name, 'd'),         *)
(* hasattr(o, name), hasattr(o, name) after delattr(o, name), or           *)
(* (getattr(o, name), name in vars(o)) after setattr(o, name, 5), for name *)
(* among x, y, m, and real; or runs one of the sources of CASES in a fresh *)
(* namespace. The outcome is the repr of the result, or the exception and  *)
(* its message.                                                            *)
(***************************************************************************)
EXTENDS Sequences

VARIABLES program, outcome
vars == <<program, outcome>>

Objs == {"a", "b", "c", "one"}
Names == {"x", "y", "m", "real"}
B(b) == IF b THEN "True" ELSE "False"

Type == [a |-> "A", b |-> "B", c |-> "C", one |-> "int"]
\* Each class with its bases, to object.
Ancestors == [A |-> {"A", "object"}, B |-> {"B", "A", "object"}, C |-> {"C", "object"}, int |-> {"int", "object"}]
\* The classes each info names, tuples and unions flattened.
Infos == [A |-> {"A"}, B |-> {"B"}, AC |-> {"A", "C"}, BorC |-> {"B", "C"}, int |-> {"int"}, object |-> {"object"},
          empty |-> {}, bool |-> {"bool"}, nested |-> {"B", "int"}]

\* Where each attribute lives: the class, the instance dict, __getattr__.
Has(o, n) == CASE n = "x" -> o \in {"a", "b"}
              [] n = "y" -> o = "b"
              [] n = "m" -> o = "c"
              [] n = "real" -> o = "one"
InDict(o, n) == o = "b" /\ n = "y"
Value(n) == CASE n = "x" -> "1" [] n = "y" -> "2" [] n = "m" -> "'dyn:m'" [] n = "real" -> "1"

NoDict(n) == IF n = "real" THEN "AttributeError: attribute 'real' of 'int' objects is not writable"
             ELSE "AttributeError: 'int' object has no attribute '" \o n \o "' and no __dict__ for setting new attributes"


Cases == {"getattr_nonstr", "getattr_missing", "setattr_nonstr", "hasattr_propagates", "hasattr_attributeerror",
          "slots_setattr", "slots_vars", "vars_no_arg", "vars_module", "dir_sorted", "dir_hook",
          "dir_hook_bad", "callable_forms", "id_identity", "hash_big", "hash_bad", "hash_eq_only",
          "hash_numeric", "type_one_arg", "type_three_args", "type_two_args", "type_bad_bases",
          "type_bad_dict", "type_bad_name", "type_qualname_kw", "isinstance_hook", "isinstance_bad",
          "issubclass_bad_first", "issubclass_bad_second", "object_no_attrs", "object_args",
          "object_dir_has", "delattr_class", "setattr_builtin_type", "getattr_type_default",
          "super_zero_arg", "globals_identity", "memoryview_builtin", "repr_builtin"}
Programs == [op : {"isinstance", "issubclass"}, obj : Objs, arg : DOMAIN Infos]
            \cup [op : {"getattr", "hasattr", "delattr", "setattr"}, obj : Objs, arg : Names]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    LET o == p.obj  n == p.arg IN
    CASE p.op \in {"isinstance", "issubclass"} -> B(Ancestors[Type[o]] \cap Infos[n] # {})
      [] p.op = "getattr" -> IF Has(o, n) THEN Value(n) ELSE "'d'"
      [] p.op = "hasattr" -> B(Has(o, n))
      [] o = "one" -> NoDict(n)
      [] p.op = "delattr" -> IF InDict(o, n) THEN "False" ELSE "AttributeError: '" \o Type[o] \o "' object has no attribute '" \o n \o "'"
      [] p.op = "setattr" -> "(5, True)"

Case(c) ==
    CASE c = "getattr_nonstr" -> "TypeError: attribute name must be string, not 'int'"
      [] c = "getattr_missing" -> "AttributeError: 'int' object has no attribute 'nope'"
      [] c = "setattr_nonstr" -> "TypeError: attribute name must be string, not 'int'"
      [] c = "hasattr_propagates" -> "ValueError: inner"
      [] c = "hasattr_attributeerror" -> "False"
      [] c = "slots_setattr" -> "AttributeError: 'P' object has no attribute 't' and no __dict__ for setting new attributes"
      [] c = "slots_vars" -> "TypeError: vars() argument must have __dict__ attribute"
      [] c = "vars_no_arg" -> "{'a': 1}"
      [] c = "vars_module" -> "'mappingproxy'"
      [] c = "dir_sorted" -> "['a', 'b']"
      [] c = "dir_hook" -> "['a', 'z']"
      [] c = "dir_hook_bad" -> "TypeError: 'int' object is not iterable"
      [] c = "callable_forms" -> "(True, True, False, True, False)"
      [] c = "id_identity" -> "(True, True, 'int')"
      [] c = "hash_big" -> "True"
      [] c = "hash_bad" -> "TypeError: __hash__ method should return an integer"
      [] c = "hash_eq_only" -> "TypeError: unhashable type: 'Eq'"
      [] c = "hash_numeric" -> "(True, -2, -2)"
      [] c = "type_one_arg" -> "(<class 'int'>, <class 'type'>, 'P')"
      [] c = "type_three_args" -> "('T', (<class '__main__.P'>,), 1, 'm')"
      [] c = "type_two_args" -> "TypeError: type() takes 1 or 3 arguments"
      [] c = "type_bad_bases" -> "TypeError: type.__new__() argument 2 must be tuple, not int"
      [] c = "type_bad_dict" -> "TypeError: type.__new__() argument 3 must be dict or frozendict, not list"
      [] c = "type_bad_name" -> "TypeError: type.__new__() argument 1 must be str, not int"
      [] c = "type_qualname_kw" -> "'Q.T'"
      [] c = "isinstance_hook" -> "(True, False, True, False)"
      [] c = "isinstance_bad" -> "TypeError: isinstance() arg 2 must be a type, a tuple of types, or a union"
      [] c = "issubclass_bad_first" -> "TypeError: issubclass() arg 1 must be a class"
      [] c = "issubclass_bad_second" -> "TypeError: issubclass() arg 2 must be a class, a tuple of classes, or a union"
      [] c = "object_no_attrs" -> "AttributeError: 'object' object has no attribute 'x' and no __dict__ for setting new attributes"
      [] c = "object_args" -> "TypeError: object() takes no arguments"
      [] c = "object_dir_has" -> "(False, True)"
      [] c = "delattr_class" -> "False"
      [] c = "setattr_builtin_type" -> "TypeError: cannot set 'k' attribute of immutable type 'int'"
      [] c = "getattr_type_default" -> "None"
      [] c = "super_zero_arg" -> "'S1>S0'"
      [] c = "globals_identity" -> "True"
      [] c = "memoryview_builtin" -> "98"
      [] c = "repr_builtin" -> "(True, '<built-in function len>', 'None')"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* An instance of a class is an instance of every base, and of no class
\* outside its ancestry.
Ancestry == Done /\ "op" \in DOMAIN program /\ program.op = "isinstance" =>
    ((outcome = "True") <=> \E k \in Infos[program.arg] : k \in Ancestors[Type[program.obj]])
=============================================================================
