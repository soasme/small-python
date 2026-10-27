---------------------------- MODULE FunctionDefs ----------------------------
(***************************************************************************)
(* Function definitions, lambdas, and assignment expressions, as The       *)
(* Python Language Reference specifies them                                *)
(* (reference/compound_stmts.html#function-definitions,                    *)
(* reference/expressions.html#lambda and #assignment-expressions, with     *)
(* reference/compound_stmts.html#class-definitions): a def statement       *)
(* evaluates its decorator expressions from top to bottom, then its        *)
(* positional and keyword-only default values from left to right, once,    *)
(* creates the function, and applies the decorators from the bottom up,    *)
(* binding the result to the name; a class definition likewise evaluates   *)
(* its decorators, then its bases and keywords, runs its body, and applies *)
(* the decorators; a lambda evaluates its defaults and makes an anonymous  *)
(* function of one expression; the parameter list allows defaults only in  *)
(* a suffix of the positional parameters, at most one / before *, and a    *)
(* var-keyword parameter only last; and an assignment expression binds a   *)
(* name (never an attribute, subscript, or keyword) in the enclosing       *)
(* function or module, also from a comprehension, and must be              *)
(* parenthesized where an assignment statement could be meant.             *)
(*                                                                         *)
(* A program defines KIND (a def, a lambda, or a class) with DECORATORS    *)
(* decorators, POSITIONAL and KEYWORD defaults (for a class, POSITIONAL    *)
(* bases and KEYWORD set to its metaclass), each expression logged when    *)
(* evaluated and each decorator when applied, the class body logging       *)
(* itself; or it runs one of the CASES. The outcome is "ok" (or the        *)
(* result's repr, or the exception) and the log.                           *)
(***************************************************************************)
EXTENDS Naturals, Sequences, TLC

Cases == {"mutable_default", "default_once", "default_order_error", "kwonly_no_default_ok", "duplicate_param",
          "duplicate_kw_param", "bare_star_end", "slash_first", "slash_after_star", "two_slashes",
          "two_stars", "kwargs_not_last", "star_default", "return_default", "docstring",
          "no_docstring_expr", "nested_qualname", "method_qualname", "generator_detect",
          "return_in_class", "return_outside", "yield_outside", "def_is_assignment", "decorator_expr",
          "decorator_arbitrary", "lambda_basic", "lambda_name", "lambda_statement", "lambda_annotation",
          "lambda_yield", "lambda_late_binding", "lambda_default_capture", "lambda_star_args",
          "lambda_posonly", "lambda_in_default", "lambda_cond", "walrus_scope", "walrus_statement",
          "walrus_attr", "walrus_subscript", "walrus_paren_ok", "walrus_in_call", "walrus_kwarg",
          "walrus_default", "walrus_lambda", "walrus_precedence", "walrus_unparenthesized_tuple",
          "walrus_in_fstring", "walrus_comprehension_class", "walrus_nonlocal", "walrus_global_in_comp",
          "walrus_rebind_iter_nested", "walrus_keyword_name"}
Programs == [kind : {"def"}, decorators : 0..3, positional : 0..2, keyword : 0..2]
            \cup [kind : {"lambda"}, decorators : {0}, positional : 0..2, keyword : 0..2]
            \cup [kind : {"class"}, decorators : 0..3, positional : 0..2, keyword : 0..1]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

R(n) == ToString(n)
Gen(n, F(_)) == [i \in 1..n |-> F(i)]
Reverse(s) == [i \in DOMAIN s |-> s[Len(s) - i + 1]]

\* Default i of a function is i (keyword-only default j is 10 + j); class
\* base i is a fresh class Bi, and the keyword is metaclass=type.
Definition(p) ==
    LET evaluated == Gen(p.decorators, LAMBDA i : "eval d" \o R(i))
        applied == Reverse(Gen(p.decorators, LAMBDA i : "apply d" \o R(i)))
        positional == Gen(p.positional, LAMBDA i : IF p.kind = "class" THEN "B" \o R(i) ELSE R(i))
        keyword == Gen(p.keyword, LAMBDA j : IF p.kind = "class" THEN "type" ELSE R(10 + j))
        body == IF p.kind = "class" THEN <<"body">> ELSE <<>>
    IN  <<"ok", evaluated \o positional \o keyword \o body \o applied>>

Case(c) ==
    CASE c = "mutable_default" -> "[1, 1]"
      [] c = "default_once" -> "(1, 1, 1)"
      [] c = "default_order_error" -> "SyntaxError: parameter without a default follows parameter with a default"
      [] c = "kwonly_no_default_ok" -> "(0, 1)"
      [] c = "duplicate_param" -> "SyntaxError: duplicate parameter 'a' in function definition"
      [] c = "duplicate_kw_param" -> "SyntaxError: duplicate parameter 'a' in function definition"
      [] c = "bare_star_end" -> "SyntaxError: named parameters must follow bare *"
      [] c = "slash_first" -> "SyntaxError: at least one parameter must precede /"
      [] c = "slash_after_star" -> "SyntaxError: / must be ahead of *"
      [] c = "two_slashes" -> "SyntaxError: / may appear only once"
      [] c = "two_stars" -> "SyntaxError: * may appear only once"
      [] c = "kwargs_not_last" -> "SyntaxError: parameters cannot follow var-keyword parameter"
      [] c = "star_default" -> "SyntaxError: var-positional parameter cannot have default value"
      [] c = "return_default" -> "None"
      [] c = "docstring" -> "('doc', 'f', 'f')"
      [] c = "no_docstring_expr" -> "None"
      [] c = "nested_qualname" -> "'f.<locals>.g'"
      [] c = "method_qualname" -> "'C.m'"
      [] c = "generator_detect" -> "'generator'"
      [] c = "return_in_class" -> "SyntaxError: 'return' outside function"
      [] c = "return_outside" -> "SyntaxError: 'return' outside function"
      [] c = "yield_outside" -> "SyntaxError: 'yield' outside function"
      [] c = "def_is_assignment" -> "(1, 2)"
      [] c = "decorator_expr" -> "['f']"
      [] c = "decorator_arbitrary" -> "'wrapped'"
      [] c = "lambda_basic" -> "3"
      [] c = "lambda_name" -> "('<lambda>', '<lambda>')"
      [] c = "lambda_statement" -> "SyntaxError: cannot assign to lambda"
      [] c = "lambda_annotation" -> "SyntaxError: invalid syntax"
      [] c = "lambda_yield" -> "'generator'"
      [] c = "lambda_late_binding" -> "[2, 2, 2]"
      [] c = "lambda_default_capture" -> "[0, 1, 2]"
      [] c = "lambda_star_args" -> "((1,), {'b': 2})"
      [] c = "lambda_posonly" -> "(1, 2)"
      [] c = "lambda_in_default" -> "5"
      [] c = "lambda_cond" -> "2"
      [] c = "walrus_scope" -> "3"
      [] c = "walrus_statement" -> "SyntaxError: invalid syntax"
      [] c = "walrus_attr" -> "SyntaxError: cannot use assignment expressions with attribute"
      [] c = "walrus_subscript" -> "SyntaxError: cannot use assignment expressions with subscript"
      [] c = "walrus_paren_ok" -> "1"
      [] c = "walrus_in_call" -> "(5, 5)"
      [] c = "walrus_kwarg" -> "SyntaxError: invalid syntax"
      [] c = "walrus_default" -> "(4, 4)"
      [] c = "walrus_lambda" -> "7"
      [] c = "walrus_precedence" -> "(3, 3)"
      [] c = "walrus_unparenthesized_tuple" -> "(1, 2)"
      [] c = "walrus_in_fstring" -> "'33'"
      [] c = "walrus_comprehension_class" -> "SyntaxError: assignment expression within a comprehension cannot be used in a class body"
      [] c = "walrus_nonlocal" -> "9"
      [] c = "walrus_global_in_comp" -> "1"
      [] c = "walrus_rebind_iter_nested" -> "SyntaxError: assignment expression cannot rebind comprehension iteration variable 'i'"
      [] c = "walrus_keyword_name" -> "SyntaxError: cannot use assignment expressions with True"

Run(p) == IF "case" \in DOMAIN p THEN <<Case(p.case), <<>>>> ELSE Definition(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
IsDefinition == Done /\ "kind" \in DOMAIN program

\* Every decorator is evaluated before any is applied, and applied once.
DecoratorsBracket == IsDefinition =>
    \A i, j \in DOMAIN outcome[2] :
        (outcome[2][i] \in {"apply d" \o R(k) : k \in 1..3} /\ outcome[2][j] \in {"eval d" \o R(k) : k \in 1..3}) => j < i
=============================================================================
