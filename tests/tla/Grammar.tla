------------------------------- MODULE Grammar ------------------------------
(***************************************************************************)
(* Compound statements and the complete grammar, as The Python Language    *)
(* Reference specifies them (reference/compound_stmts.html#compound-       *)
(* statements and reference/grammar.html): a compound statement's clause   *)
(* has a header ending in a colon and a suite that is either one or more   *)
(* semicolon-separated simple statements on the header's line, an optional *)
(* semicolon ending them, all executed or none since the semicolon binds   *)
(* tighter than the colon, or an indented block of statements on the       *)
(* following lines, which alone may contain compound statements; a header  *)
(* without a suite is an IndentationError naming the statement, and a      *)
(* dedent to no enclosing level is one too; and the full grammar accepts   *)
(* and rejects each production, the rejections with the messages of its    *)
(* invalid_ rules.                                                         *)
(*                                                                         *)
(* A program is either a compound statement of KIND (if over a true or a   *)
(* false condition, while over a condition true once, for over one item,   *)
(* with, try followed by a finally clause, def followed by a call, and     *)
(* class) whose first suite has FORM, its statements logging 1 and 2, or   *)
(* one of the SNIPPETS, which the program only compiles. The outcome is    *)
(* the log, or the exception and its message, without the location; or,    *)
(* for a snippet, "compiled".                                              *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Kinds == {"if_true", "if_false", "while", "for", "with", "try", "def", "class"}
Forms == {"inline1", "inline2", "trailing", "block", "block2", "nested", "missing", "block_semis", "dedent_mismatch",
          "block_then_inline"}
Snippets == {"soft_keywords_as_names", "match_soft", "return_star", "assign_star_tuple", "assign_star_alone",
             "del_targets", "call_dstar_then_star", "call_kw_then_pos", "call_genexpr_unparenthesized",
             "call_keyword_repeated", "decorator_expression", "lambda_bare_star", "lambda_kwonly",
             "def_slash_first", "def_params_full", "def_duplicate_param", "def_default_order",
             "slice_tuple", "subscript_star", "with_parenthesized", "except_star", "except_mixed",
             "except_unparenthesized", "except_unparenthesized_as", "try_alone", "walrus_if",
             "walrus_unparenthesized_stmt", "unpack_targets", "two_starred_targets", "fstring_debug",
             "tstring", "type_stmt", "class_type_params", "annotated_single", "annotated_tuple",
             "assign_literal", "assign_call", "conditional_without_else", "print_statement",
             "missing_comma", "else_alone", "return_outside", "break_outside", "continue_outside",
             "await_outside", "yield_outside", "nonlocal_module", "global_after_use", "chained_conditional",
             "comprehension_ifs", "dict_unpack_display", "async_constructs", "yield_from_expr",
             "lazy_import", "lazy_in_function", "lazy_star", "star_in_index_assign",
             "keyword_as_identifier", "dotted_import_as", "relative_import_star", "import_star_function",
             "pass_semicolons", "double_semicolon", "backslash_continuation", "implicit_continuation",
             "decorated_class", "async_lambda", "star_expression_for", "assert_message", "raise_from",
             "default_after_star", "kwargs_then_param"}
Programs == [kind : Kinds, form : Forms] \cup [snippet : Snippets]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* What the header names in the error for a missing block.
Statement(k) == CASE k = "def" -> "function definition"
                  [] k = "class" -> "class definition"
                  [] k = "if_true" \/ k = "if_false" -> "'if' statement"
                  [] OTHER -> "'" \o k \o "' statement"

\* The statements a suite runs: a one-line suite only of simple statements.
Body(f) == CASE f \in {"inline1", "trailing", "block"} -> "1"
             [] OTHER -> "1, 2"

\* The log of running the statement once its suite parsed.
Wrap(k, body) == CASE k = "if_false" -> "[]"
                   [] k = "with" -> "['enter', " \o body \o ", 'exit']"
                   [] k = "try" -> "[" \o body \o ", 9]"
                   [] OTHER -> "[" \o body \o "]"

Suite(k, f) ==
    CASE f = "nested" -> "SyntaxError: invalid syntax"
      [] f = "missing" -> "IndentationError: expected an indented block after " \o Statement(k) \o " on line 1"
      [] f = "dedent_mismatch" -> "IndentationError: unindent does not match any outer indentation level"
      [] OTHER -> Wrap(k, Body(f))

Snippet(s) ==
    CASE s = "soft_keywords_as_names" -> "'compiled'"
      [] s = "match_soft" -> "'compiled'"
      [] s = "return_star" -> "'compiled'"
      [] s = "assign_star_tuple" -> "'compiled'"
      [] s = "assign_star_alone" -> "SyntaxError: can't use starred expression here"
      [] s = "del_targets" -> "'compiled'"
      [] s = "call_dstar_then_star" -> "SyntaxError: iterable argument unpacking follows keyword argument unpacking"
      [] s = "call_kw_then_pos" -> "SyntaxError: positional argument follows keyword argument"
      [] s = "call_genexpr_unparenthesized" -> "SyntaxError: Generator expression must be parenthesized"
      [] s = "call_keyword_repeated" -> "SyntaxError: keyword argument repeated: a"
      [] s = "decorator_expression" -> "'compiled'"
      [] s = "lambda_bare_star" -> "SyntaxError: named parameters must follow bare *"
      [] s = "lambda_kwonly" -> "'compiled'"
      [] s = "def_slash_first" -> "SyntaxError: at least one parameter must precede /"
      [] s = "def_params_full" -> "'compiled'"
      [] s = "def_duplicate_param" -> "SyntaxError: duplicate parameter 'a' in function definition"
      [] s = "def_default_order" -> "SyntaxError: parameter without a default follows parameter with a default"
      [] s = "slice_tuple" -> "'compiled'"
      [] s = "subscript_star" -> "'compiled'"
      [] s = "with_parenthesized" -> "'compiled'"
      [] s = "except_star" -> "'compiled'"
      [] s = "except_mixed" -> "SyntaxError: cannot have both 'except' and 'except*' on the same 'try'"
      [] s = "except_unparenthesized" -> "'compiled'"
      [] s = "except_unparenthesized_as" -> "SyntaxError: multiple exception types must be parenthesized when using 'as'"
      [] s = "try_alone" -> "SyntaxError: expected 'except' or 'finally' block"
      [] s = "walrus_if" -> "'compiled'"
      [] s = "walrus_unparenthesized_stmt" -> "SyntaxError: invalid syntax"
      [] s = "unpack_targets" -> "'compiled'"
      [] s = "two_starred_targets" -> "SyntaxError: multiple starred expressions in assignment"
      [] s = "fstring_debug" -> "'compiled'"
      [] s = "tstring" -> "'compiled'"
      [] s = "type_stmt" -> "'compiled'"
      [] s = "class_type_params" -> "'compiled'"
      [] s = "annotated_single" -> "'compiled'"
      [] s = "annotated_tuple" -> "SyntaxError: only single target (not tuple) can be annotated"
      [] s = "assign_literal" -> "SyntaxError: cannot assign to literal here. Maybe you meant '==' instead of '='?"
      [] s = "assign_call" -> "SyntaxError: cannot assign to function call here. Maybe you meant '==' instead of '='?"
      [] s = "conditional_without_else" -> "SyntaxError: expected 'else' after 'if' expression"
      [] s = "print_statement" -> "SyntaxError: Missing parentheses in call to 'print'. Did you mean print(...)?"
      [] s = "missing_comma" -> "SyntaxError: invalid syntax"
      [] s = "else_alone" -> "SyntaxError: invalid syntax"
      [] s = "return_outside" -> "SyntaxError: 'return' outside function"
      [] s = "break_outside" -> "SyntaxError: 'break' outside loop"
      [] s = "continue_outside" -> "SyntaxError: 'continue' not properly in loop"
      [] s = "await_outside" -> "SyntaxError: 'await' outside function"
      [] s = "yield_outside" -> "SyntaxError: 'yield' outside function"
      [] s = "nonlocal_module" -> "SyntaxError: nonlocal declaration not allowed at module level"
      [] s = "global_after_use" -> "SyntaxError: name 'x' is assigned to before global declaration"
      [] s = "chained_conditional" -> "'compiled'"
      [] s = "comprehension_ifs" -> "'compiled'"
      [] s = "dict_unpack_display" -> "'compiled'"
      [] s = "async_constructs" -> "'compiled'"
      [] s = "yield_from_expr" -> "'compiled'"
      [] s = "lazy_import" -> "'compiled'"
      [] s = "lazy_in_function" -> "SyntaxError: lazy import not allowed inside functions"
      [] s = "lazy_star" -> "SyntaxError: lazy from ... import * is not allowed"
      [] s = "star_in_index_assign" -> "'compiled'"
      [] s = "keyword_as_identifier" -> "SyntaxError: invalid syntax"
      [] s = "dotted_import_as" -> "'compiled'"
      [] s = "relative_import_star" -> "'compiled'"
      [] s = "import_star_function" -> "SyntaxError: import * only allowed at module level"
      [] s = "pass_semicolons" -> "'compiled'"
      [] s = "double_semicolon" -> "SyntaxError: invalid syntax"
      [] s = "backslash_continuation" -> "'compiled'"
      [] s = "implicit_continuation" -> "'compiled'"
      [] s = "decorated_class" -> "'compiled'"
      [] s = "async_lambda" -> "SyntaxError: invalid syntax"
      [] s = "star_expression_for" -> "'compiled'"
      [] s = "assert_message" -> "'compiled'"
      [] s = "raise_from" -> "'compiled'"
      [] s = "default_after_star" -> "'compiled'"
      [] s = "kwargs_then_param" -> "SyntaxError: parameters cannot follow var-keyword parameter"

Run(p) == IF "kind" \in DOMAIN p THEN Suite(p.kind, p.form) ELSE Snippet(p.snippet)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Either all or none of a one-line suite's statements run.
AllOrNone == Done /\ "kind" \in DOMAIN program /\ program.form = "inline2" =>
    outcome \in {"[]", "[1, 2]", "['enter', 1, 2, 'exit']", "[1, 2, 9]"}
=============================================================================
