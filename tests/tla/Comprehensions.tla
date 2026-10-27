--------------------------- MODULE Comprehensions ---------------------------
(***************************************************************************)
(* Comprehensions and generator expressions, as The Python Language        *)
(* Reference specifies them (reference/expressions.html#comprehensions and *)
(* #generator-expressions): the clauses nest from left to right, each for  *)
(* clause binding its target for every item of its iterable, evaluated     *)
(* afresh for every binding of the clauses before it, and each if clause   *)
(* skipping what follows when false; the element is evaluated for each     *)
(* surviving binding and a starred (or, in a dict, double-starred) element *)
(* contributes every item of its iterable (PEP 798); only the first        *)
(* iterable is evaluated in the enclosing scope, eagerly even for a        *)
(* generator expression, whose remaining evaluation waits until it is      *)
(* iterated; the comprehension has its own scope, so its targets do not    *)
(* leak, a class body's names are visible only in the first iterable, and  *)
(* an assignment expression binds in the enclosing function or module; and *)
(* yield, an unparenthesized second argument, and dict unpacking outside a *)
(* dict comprehension are syntax errors.                                   *)
(*                                                                         *)
(* A program is either a comprehension of KIND (list, set, dict, or gen,   *)
(* which the program turns into a list) with up to three CLAUSES, the      *)
(* first a for clause, and a plain or starred element, or one of the       *)
(* CASES. For clause k iterates over [10^(k-1), 2 * 10^(k-1)]; an if       *)
(* clause tests whether the sum s of the bound values is odd; the element  *)
(* is s, or s: -s in a dict, or *(s, -s), or **{s: -s} in a dict.          *)
(* Iterables, tested sums, and elements are logged as they are evaluated,  *)
(* and then the program logs 'created' once the comprehension is created.  *)
(* The outcome is "ok", the result, and the log, or the exception and the  *)
(* log.                                                                    *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Clauses == {<<"for">> \o c : c \in UNION {[1..n -> {"for", "if"}] : n \in 0..2}}
Cases == {"no_leak", "class_scope", "class_scope_inner", "class_first_iterable", "walrus_binds", "walrus_iter_var",
          "walrus_iterable", "walrus_class", "yield_in", "await_outside", "async_for_outside", "gen_sole_arg",
          "gen_not_sole", "gen_first_error", "gen_inner_error", "comp_error_type", "star_list", "dstar_dict",
          "star_gen", "dstar_list", "star_dict_key", "star_dict_bad", "dstar_bad", "star_target_in_comp",
          "nested_scope", "late_binding", "gen_close", "gen_send_none", "gen_name", "frame_name",
          "unparenthesized_tuple", "if_else_elem", "if_without_else", "lambda_in_if", "iter_var_global"}
Programs == [kind : {"list", "set", "dict", "gen"}, clauses : Clauses, element : {"plain", "star"}]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

R(n) == ToString(n)
Step(k) == 10 ^ (k - 1)
Iterable(k) == "[" \o R(Step(k)) \o ", " \o R(2 * Step(k)) \o "]"

\* The elements (or key-value pairs) of the element at sum s, and its log.
Element(p, s) ==
    CASE p.kind = "dict" /\ p.element = "plain" -> <<<<<<R(s), R(-s)>>>>, <<R(s), R(-s)>>>>
      [] p.kind = "dict" -> <<<<<<R(s), R(-s)>>>>, <<"{" \o R(s) \o ": " \o R(-s) \o "}">>>>
      [] p.element = "plain" -> <<<<R(s)>>, <<R(s)>>>>
      [] OTHER -> <<<<R(s), R(-s)>>, <<"(" \o R(s) \o ", " \o R(-s) \o ")">>>>

\* The elements and the log of clauses k.. with the bound values summing to s.
RECURSIVE Eval(_, _, _)
Eval(p, k, s) ==
    IF k > Len(p.clauses) THEN Element(p, s)
    ELSE IF p.clauses[k] = "if" THEN
        IF s % 2 = 1 THEN LET rest == Eval(p, k + 1, s) IN <<rest[1], <<R(s)>> \o rest[2]>>
        ELSE <<<<>>, <<R(s)>>>>
    ELSE LET a == Eval(p, k + 1, s + Step(k))  b == Eval(p, k + 1, s + 2 * Step(k))
         IN  <<a[1] \o b[1], <<Iterable(k)>> \o a[2] \o b[2]>>

\* The first iterable is evaluated at once; a generator runs the rest later.
Comprehension(p) ==
    LET a == Eval(p, 2, 1)  b == Eval(p, 2, 2)  items == a[1] \o b[1]  rest == a[2] \o b[2]
        result == IF p.kind = "set" THEN {items[i] : i \in DOMAIN items} ELSE items
    IN  <<"ok", result, IF p.kind = "gen" THEN <<Iterable(1), "'created'">> \o rest
                        ELSE <<Iterable(1)>> \o rest \o <<"'created'">>>>

Syntax(m) == <<"SyntaxError: " \o m, <<>>, <<>>>>
Case(c) ==
    CASE c = "no_leak" -> <<"ok", "'outer'", <<>>>>
      [] c = "class_scope" -> <<"NameError: name 'a' is not defined", <<>>, <<>>>>
      [] c = "class_scope_inner" -> <<"ok", "\"name 'a' is not defined\"", <<>>>>
      [] c = "class_first_iterable" -> <<"ok", "[1, 2]", <<>>>>
      [] c = "walrus_binds" -> <<"ok", "([0, 1, 2], 2)", <<>>>>
      [] c = "walrus_iter_var" -> Syntax("assignment expression cannot rebind comprehension iteration variable 'x'")
      [] c = "walrus_iterable" -> Syntax("assignment expression cannot be used in a comprehension iterable expression")
      [] c = "walrus_class" -> Syntax("assignment expression within a comprehension cannot be used in a class body")
      [] c = "yield_in" -> Syntax("'yield' inside list comprehension")
      [] c = "await_outside" -> Syntax("asynchronous comprehension outside of an asynchronous function")
      [] c = "async_for_outside" -> Syntax("asynchronous comprehension outside of an asynchronous function")
      [] c = "gen_sole_arg" -> <<"ok", "3", <<"0", "1", "2">>>>
      [] c = "gen_not_sole" -> Syntax("Generator expression must be parenthesized")
      [] c = "gen_first_error" -> <<"TypeError: 'int' object is not iterable", <<>>, <<>>>>
      [] c = "gen_inner_error" -> <<"TypeError: 'int' object is not iterable", <<>>, <<"'created'">>>>
      [] c = "comp_error_type" -> <<"TypeError: 'int' object is not iterable", <<>>, <<>>>>
      [] c = "star_list" -> <<"ok", "[1, 2, 3]", <<"[1, 2]", "[3]">>>>
      [] c = "dstar_dict" -> <<"ok", "{1: 5, 3: 4}", <<"{1: 2}", "{3: 4, 1: 5}">>>>
      [] c = "star_gen" -> <<"ok", "[1, 2, 3]", <<>>>>
      [] c = "dstar_list" -> Syntax("cannot use dict unpacking in list comprehension")
      [] c = "star_dict_key" -> Syntax("cannot use a starred expression in a dictionary key")
      [] c = "star_dict_bad" -> <<"TypeError: 'int' object is not iterable", <<>>, <<>>>>
      [] c = "dstar_bad" -> <<"TypeError: 'int' object is not a mapping", <<>>, <<>>>>
      [] c = "star_target_in_comp" -> <<"ok", "[[2, 3]]", <<>>>>
      [] c = "nested_scope" -> <<"ok", "[10, 11]", <<>>>>
      [] c = "late_binding" -> <<"ok", "[2, 2, 2]", <<>>>>               \* closures share the target's cell
      [] c = "gen_close" -> <<"ok", "[]", <<"0">>>>
      [] c = "gen_send_none" -> <<"ok", "(0, 1)", <<>>>>
      [] c = "gen_name" -> <<"ok", "('<genexpr>', '<genexpr>')", <<>>>>
      [] c = "frame_name" -> <<"ok", "['<module>']", <<>>>>              \* inlined (PEP 709)
      [] c = "unparenthesized_tuple" -> Syntax("did you forget parentheses around the comprehension target?")
      [] c = "if_else_elem" -> <<"ok", "[0, 1, -2, 3]", <<>>>>
      [] c = "if_without_else" -> Syntax("invalid syntax")
      [] c = "lambda_in_if" -> <<"ok", "[1, 3]", <<>>>>
      [] c = "iter_var_global" -> <<"ok", "([0, 1], 'g')", <<>>>>

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Comprehension(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
IsComprehension == Done /\ "clauses" \in DOMAIN program

\* Nothing but the first iterable is evaluated before a generator expression
\* is created; every other comprehension is done by then.
FirstIterableEager == IsComprehension =>
    IF program.kind = "gen" THEN outcome[3][2] = "'created'"
    ELSE outcome[3][Len(outcome[3])] = "'created'"

\* Clause k's iterable is evaluated once per binding of the for clauses
\* before it that passes the if clauses between them.
IterableCounts == IsComprehension /\ program.clauses = <<"for", "for">> =>
    Len(SelectSeq(outcome[3], LAMBDA e : e = Iterable(2))) = 2
=============================================================================
