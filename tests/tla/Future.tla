------------------------------ MODULE Future ------------------------------
(***************************************************************************)
(* Future statements, as The Python Language Reference specifies them      *)
(* (reference/simple_stmts.html#future, with reference/                    *)
(* compound_stmts.html#annotations and the compile() built-in): a future   *)
(* statement may follow only the module docstring, comments, blank lines,  *)
(* and other future statements, and only at module level; it names known   *)
(* features (annotations, which stores every annotation as the source      *)
(* string of its expression, normalized, instead of evaluating it, and the *)
(* historical features, which change nothing), possibly parenthesized or   *)
(* renamed, and anything else is a SyntaxError (braces: "not a chance");   *)
(* code compiled by exec() and compile() in such a module inherits the     *)
(* feature unless dont_inherit is true, and the annotations flag turns it  *)
(* on; and the runtime import of the __future__ module is an ordinary,     *)
(* host-supplied import, so a relative one resolves its package as any     *)
(* import does.                                                            *)
(*                                                                         *)
(* A program compiles and runs one of the sources of CASES. The outcome is *)
(* the program's result, or the exception and its message, without the     *)
(* location.                                                               *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Cases == {"stringized", "eager_without", "class", "module", "unparse", "local_not", "unknown", "braces", "late",
          "docstring", "two_docstrings", "after_future", "parenthesized", "as_name", "historical",
          "barry", "in_function", "star", "inherit", "dont_inherit", "flag", "after_import", "relative",
          "lambda_default", "annotate", "nested_class", "generic"}
Programs == [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Run(p) ==
    CASE p.case = "stringized" -> "{'x': 'undefined', 'a': 'int', 'k': \"'q'\", 'return': 'None'}"
      [] p.case = "eager_without" -> "NameError: name 'undefined' is not defined"
      [] p.case = "class" -> "{'x': 'undefined', 'y': 'int'}"
      [] p.case = "module" -> "{'x': 'undefined'}"
      [] p.case = "unparse" -> "{'a': \"'a' + b\", 'b': 'dict[str, int]', 'c': 'x if y else z', 'd': '(1, 2)', 'e': '[1, *x]', 'f': '{1: 2, **d}', 'g': 'lambda q: q', 'h': 'a.b.c', 'i': '-x ** 2', 'k': \"f'{x!r:>{w}}'\", 'l': 'a or b and not c', 'm': 'x[1:2, ::3]', 'n': '...', 'o': '10000000000.0', 'p': '16'}"
      [] p.case = "local_not" -> "1"
      [] p.case = "unknown" -> "SyntaxError: future feature nosuch is not defined"
      [] p.case = "braces" -> "SyntaxError: not a chance"
      [] p.case = "late" -> "SyntaxError: from __future__ imports must occur at the beginning of the file"
      [] p.case = "docstring" -> "'ok'"
      [] p.case = "two_docstrings" -> "SyntaxError: from __future__ imports must occur at the beginning of the file"
      [] p.case = "after_future" -> "'ok'"
      [] p.case = "parenthesized" -> "'ok'"
      [] p.case = "as_name" -> "'ok'"
      [] p.case = "historical" -> "'ok'"
      [] p.case = "barry" -> "True"
      [] p.case = "in_function" -> "SyntaxError: from __future__ imports must occur at the beginning of the file"
      [] p.case = "star" -> "SyntaxError: future feature * is not defined"
      [] p.case = "inherit" -> "{'x': 'undefined'}"
      [] p.case = "dont_inherit" -> "'NameError'"
      [] p.case = "flag" -> "{'x': 'undefined'}"
      [] p.case = "after_import" -> "SyntaxError: from __future__ imports must occur at the beginning of the file"
      [] p.case = "relative" -> "KeyError: \"'__name__' not in globals\""
      [] p.case = "lambda_default" -> "({'x': 'int'}, (3,))"
      [] p.case = "annotate" -> "True"
      [] p.case = "nested_class" -> "{'x': 'undefined'}"
      [] p.case = "generic" -> "{'x': 'T', 'return': 'list[T]'}"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A future statement anywhere but the top of a module is rejected.
Misplaced == {"late", "two_docstrings", "in_function", "after_import"}
OnlyAtTop == Done /\ program.case \in Misplaced =>
    outcome = "SyntaxError: from __future__ imports must occur at the beginning of the file"
=============================================================================
