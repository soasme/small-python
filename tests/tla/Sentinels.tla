------------------------------ MODULE Sentinels -----------------------------
(***************************************************************************)
(* Sentinel objects, as the 3.15 edition requires them (SLP-315 20.8,     *)
(* and the sentinel() built-in of library/functions.html#sentinel):        *)
(* sentinel(name, /, *, repr=None) checks that name is a str and repr a    *)
(* str or None and returns a new object, unique, truthy, hashable, equal   *)
(* only to itself, and unordered; its representation, and so its str() and *)
(* format(), is repr if given and name otherwise; __name__ is read-only    *)
(* and __module__, the name of the creating code's module, is writable and *)
(* deletable; copies and deep copies are the object itself and it reduces  *)
(* to its name; it supports | in type expressions; and sentinel is a       *)
(* builtin type that cannot be subclassed and whose instances take no      *)
(* other attributes.                                                       *)
(*                                                                         *)
(* A program runs one of the sources of CASES in a fresh namespace. The    *)
(* outcome is the repr of its result, or the exception and its message.    *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Cases == {"repr_default", "repr_custom", "str_form", "name_attr", "module_attr", "module_writable", "truthy",
          "unique", "equal_self", "not_equal_other", "hashable", "name_not_str", "repr_not_str",
          "repr_positional", "no_args", "no_subclass", "type_name", "type_is_sentinel", "union",
          "union_left", "annotation", "is_compare", "nonidentifier_name", "name_readonly", "new_attr",
          "ordering", "builtin", "repr_none", "repr_str_form", "unknown_keyword", "too_many",
          "keyword_too_many", "name_keyword", "module_any", "module_delete", "module_delete_twice",
          "name_delete", "module_global", "module_function", "reduce", "copy_self", "union_repr",
          "type_module"}
Programs == [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Run(p) ==
    CASE p.case = "repr_default" -> "'MISSING'"
      [] p.case = "repr_custom" -> "'<MISSING>'"
      [] p.case = "str_form" -> "'MISSING'"
      [] p.case = "name_attr" -> "'MISSING'"
      [] p.case = "module_attr" -> "None"
      [] p.case = "module_writable" -> "'elsewhere'"
      [] p.case = "truthy" -> "True"
      [] p.case = "unique" -> "False"
      [] p.case = "equal_self" -> "(True, False)"
      [] p.case = "not_equal_other" -> "False"
      [] p.case = "hashable" -> "1"
      [] p.case = "name_not_str" -> "TypeError: sentinel() argument 1 must be str, not int"
      [] p.case = "repr_not_str" -> "TypeError: sentinel() argument 'repr' must be str or None, not int"
      [] p.case = "repr_positional" -> "TypeError: sentinel() takes exactly 1 positional argument (2 given)"
      [] p.case = "no_args" -> "TypeError: sentinel() takes exactly 1 positional argument (0 given)"
      [] p.case = "no_subclass" -> "TypeError: type 'sentinel' is not an acceptable base type"
      [] p.case = "type_name" -> "'sentinel'"
      [] p.case = "type_is_sentinel" -> "True"
      [] p.case = "union" -> "'int | M'"
      [] p.case = "union_left" -> "'M | None'"
      [] p.case = "annotation" -> "(True, True)"
      [] p.case = "is_compare" -> "True"
      [] p.case = "nonidentifier_name" -> "'not an identifier'"
      [] p.case = "name_readonly" -> "AttributeError: readonly attribute"
      [] p.case = "new_attr" -> "AttributeError: 'sentinel' object has no attribute 'other' and no __dict__ for setting new attributes"
      [] p.case = "ordering" -> "TypeError: '<' not supported between instances of 'sentinel' and 'sentinel'"
      [] p.case = "builtin" -> "True"
      [] p.case = "repr_none" -> "'X'"
      [] p.case = "repr_str_form" -> "('<r>', '<r>', 'X')"
      [] p.case = "unknown_keyword" -> "TypeError: sentinel() got an unexpected keyword argument 'foo'"
      [] p.case = "too_many" -> "TypeError: sentinel() takes at most 2 arguments (3 given)"
      [] p.case = "keyword_too_many" -> "TypeError: sentinel() takes at most 2 arguments (3 given)"
      [] p.case = "name_keyword" -> "TypeError: sentinel() takes exactly 1 positional argument (0 given)"
      [] p.case = "module_any" -> "3"
      [] p.case = "module_delete" -> "False"
      [] p.case = "module_delete_twice" -> "AttributeError: __module__"
      [] p.case = "name_delete" -> "AttributeError: readonly attribute"
      [] p.case = "module_global" -> "'mymod'"
      [] p.case = "module_function" -> "'fmod'"
      [] p.case = "reduce" -> "'X'"
      [] p.case = "copy_self" -> "(True, True)"
      [] p.case = "union_repr" -> "'<r> | int'"
      [] p.case = "type_module" -> "('builtins', 'sentinel')"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Two sentinels of one name are distinct, and each equals only itself.
Unique == Done /\ program.case \in {"unique", "not_equal_other"} => outcome = "False"

\* A bad call is a TypeError, never a sentinel.
BadCalls == {"name_not_str", "repr_not_str", "repr_positional", "no_args", "unknown_keyword", "too_many",
             "keyword_too_many", "name_keyword", "no_subclass"}
CallsChecked == Done /\ program.case \in BadCalls => SubSeq(outcome, 1, 10) = "TypeError:"
=============================================================================
