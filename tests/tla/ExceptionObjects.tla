-------------------------- MODULE ExceptionObjects --------------------------
(***************************************************************************)
(* Exception objects, as The Python Standard Library specifies them        *)
(* (library/exceptions.html#base-classes and #inheriting-from-built-in-    *)
(* exceptions): BaseException.__new__ stores the positional arguments as   *)
(* args (so a subclass __init__ that skips super() keeps them), refusing   *)
(* keywords unless __init__ takes them; str() is '' without arguments,     *)
(* str() of the one argument (repr() for KeyError), or str() of args, and  *)
(* repr() is the class name with the arguments' reprs; args assignment     *)
(* takes any iterable; with_traceback() sets __traceback__ and returns the *)
(* exception; add_note() appends a str to __notes__, which it creates and  *)
(* which must stay a list; __cause__ and __context__ take exceptions or    *)
(* None, setting __cause__ sets __suppress_context__; instances have a     *)
(* __dict__ kept by __reduce__ and __setstate__, compare by identity, and  *)
(* hash; and SystemExit.code and StopIteration.value follow the arguments. *)
(*                                                                         *)
(* A program builds Exception, KeyError, or a plain subclass Sub of        *)
(* Exception from zero to two arguments among 'a', 1, and None, and        *)
(* reports str(), repr(), or args of it; or runs one of the sources of     *)
(* CASES in a fresh namespace. The outcome is the repr of the result, or   *)
(* the exception and its message.                                          *)
(***************************************************************************)
EXTENDS Integers, Sequences

VARIABLES program, outcome
vars == <<program, outcome>>

Args == UNION {[1..n -> {"s", "i", "n"}] : n \in 0..2}
Repr(v) == CASE v = "s" -> "'a'" [] v = "i" -> "1" [] v = "n" -> "None"
Str(v) == CASE v = "s" -> "a" [] v = "i" -> "1" [] v = "n" -> "None"
RECURSIVE Join(_)
Join(s) == IF s = <<>> THEN "" ELSE IF Len(s) = 1 THEN Head(s) ELSE Head(s) \o ", " \o Join(Tail(s))
Reprs(a) == [i \in DOMAIN a |-> Repr(a[i])]
Tuple(a) == "(" \o Join(Reprs(a)) \o (IF Len(a) = 1 THEN ",)" ELSE ")")

\* The repr of a str holding no backslash or newline: in ' unless it holds
\* ' and no ".
HasChar(t, c) == \E i \in 1..Len(t) : SubSeq(t, i, i) = c
PyRepr(t) == IF HasChar(t, "'") /\ ~HasChar(t, "\"") THEN "\"" \o t \o "\"" ELSE "'" \o t \o "'"

\* str(): nothing, the sole argument (its repr for KeyError), or args.
Text(cls, a) == CASE Len(a) = 0 -> ""
                  [] Len(a) = 1 /\ cls = "KeyError" -> Repr(a[1])
                  [] Len(a) = 1 -> Str(a[1])
                  [] OTHER -> Tuple(a)


Cases == {"args_set_by_new", "args_assign_tuple", "args_assign_bad", "with_traceback_self", "traceback_bad",
          "with_traceback_bad", "add_note", "add_note_bad", "notes_absent", "notes_replaced_bad",
          "context_defaults", "cause_assign_bad", "context_assign_bad", "cause_sets_suppress", "custom_str",
          "kwargs_refused", "kwargs_subclass_init", "reduce", "reduce_dict", "setstate", "setstate_bad",
          "exception_dict", "inherit_init_args", "base_new_args", "str_of_class_instance",
          "repr_trailing_comma", "equality_identity", "hashable", "systemexit_code", "stopiteration_value",
          "keyerror_str_tuple"}
Programs == [op : {"str", "repr", "args"}, cls : {"Exception", "KeyError", "Sub"}, args : Args]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    CASE p.op = "str" -> PyRepr(Text(p.cls, p.args))
      [] p.op = "repr" -> PyRepr(p.cls \o "(" \o Join(Reprs(p.args)) \o ")")
      [] p.op = "args" -> Tuple(p.args)

Case(c) ==
    CASE c = "args_set_by_new" -> "((5,), 5, '5')"
      [] c = "args_assign_tuple" -> "((1, 2), 'tuple')"
      [] c = "args_assign_bad" -> "TypeError: 'int' object is not iterable"
      [] c = "with_traceback_self" -> "(True, None)"
      [] c = "traceback_bad" -> "TypeError: __traceback__ must be a traceback or None"
      [] c = "with_traceback_bad" -> "TypeError: __traceback__ must be a traceback or None"
      [] c = "add_note" -> "(['one', 'two'], 'v')"
      [] c = "add_note_bad" -> "TypeError: add_note() argument must be str, not int"
      [] c = "notes_absent" -> "False"
      [] c = "notes_replaced_bad" -> "TypeError: Cannot add note: __notes__ is not a list"
      [] c = "context_defaults" -> "(None, None, False)"
      [] c = "cause_assign_bad" -> "TypeError: exception cause must be None or derive from BaseException"
      [] c = "context_assign_bad" -> "TypeError: exception context must be None or derive from BaseException"
      [] c = "cause_sets_suppress" -> "True"
      [] c = "custom_str" -> "('custom', 'MyStr(1)', (1,))"
      [] c = "kwargs_refused" -> "TypeError: Exception() takes no keyword arguments"
      [] c = "kwargs_subclass_init" -> "(3,)"
      [] c = "reduce" -> "(True, (1, 2))"
      [] c = "reduce_dict" -> "{'extra': 2}"
      [] c = "setstate" -> "1"
      [] c = "setstate_bad" -> "TypeError: state is not a dictionary"
      [] c = "exception_dict" -> "{'anything': 1}"
      [] c = "inherit_init_args" -> "(\"'k'\", ('k', 2))"
      [] c = "base_new_args" -> "(1, 2)"
      [] c = "str_of_class_instance" -> "'inner'"
      [] c = "repr_trailing_comma" -> "('ValueError((1,))', 'ValueError(1)')"
      [] c = "equality_identity" -> "(False, True)"
      [] c = "hashable" -> "True"
      [] c = "systemexit_code" -> "(None, 1, (1, 2))"
      [] c = "stopiteration_value" -> "(None, 1)"
      [] c = "keyerror_str_tuple" -> "('(1, 2)', '()')"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* With several arguments, str() is the same for every class.
SharedStr == Done /\ "cls" \in DOMAIN program /\ Len(program.args) > 1 =>
    \A c \in {"Exception", "KeyError", "Sub"} : Text(c, program.args) = Text(program.cls, program.args)
=============================================================================
