---------------------------- MODULE Conditionals ----------------------------
(***************************************************************************)
(* The if and while statements, as The Python Language Reference specifies *)
(* them (reference/compound_stmts.html#the-if-statement, #the-while-       *)
(* statement, and the compound statement grammar, with                     *)
(* reference/simple_stmts.html#the-break-statement and #the-continue-      *)
(* statement and reference/expressions.html#conditional-expressions): if   *)
(* evaluates its conditions one at a time until one is true and runs that  *)
(* suite, or the else suite when none is; while evaluates its condition    *)
(* before every iteration, runs its suite while it is true and its else    *)
(* suite when it becomes false, break ends the loop without the else suite *)
(* and continue goes back to the condition; break and continue apply to    *)
(* the innermost loop of their function and are syntax errors elsewhere;   *)
(* and a conditional expression evaluates only the chosen branch.          *)
(*                                                                         *)
(* A program runs an if statement whose conditions t(c1), t(c2), ... are   *)
(* CONDITIONS, with or without an else, or a while loop whose condition    *)
(* t(i < N) is true N times, whose suite counts i and breaks when i is     *)
(* BREAK and continues when i is CONTINUE (0 for never), with or without   *)
(* an else; or it runs one of the CASES. Conditions and suites are logged. *)
(* The outcome is the result's repr or the exception, and the log.         *)
(***************************************************************************)
EXTENDS Naturals, Sequences, TLC

Cases == {"break_outside", "continue_outside", "break_in_function_in_loop", "continue_in_finally", "break_in_finally",
          "nested_break", "elif_after_else", "if_walrus", "while_walrus", "if_bool_error", "while_cond_each_time",
          "if_empty_body", "while_else_after_break_in_nested", "if_expression_value", "conditional_expr_lazy",
          "conditional_expr_precedence", "conditional_expr_lambda"}
Programs == [conditions : UNION {[1..n -> BOOLEAN] : n \in 1..3}, else : BOOLEAN]
            \cup [n : 0..3, break : 0..3, continue : 0..3, else : BOOLEAN]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

R(n) == ToString(n)
Show(b) == IF b THEN "True" ELSE "False"

\* The conditions from the k-th on: each logged until one is true.
RECURSIVE Branch(_, _)
Branch(p, k) ==
    IF k > Len(p.conditions) THEN (IF p.else THEN <<"else">> ELSE <<>>)
    ELSE IF p.conditions[k] THEN <<"True", "branch " \o R(k)>>
    ELSE <<"False">> \o Branch(p, k + 1)

\* The loop after i iterations.
RECURSIVE Loop(_, _)
Loop(p, i) ==
    IF i >= p.n THEN <<"False">> \o (IF p.else THEN <<"else">> ELSE <<>>)
    ELSE CASE i + 1 = p.break -> <<"True", "break">>
           [] i + 1 = p.continue -> <<"True", "continue">> \o Loop(p, i + 1)
           [] OTHER -> <<"True", "body " \o R(i + 1)>> \o Loop(p, i + 1)

Case(c) ==
    CASE c = "break_outside" -> "SyntaxError: 'break' outside loop"
      [] c = "continue_outside" -> "SyntaxError: 'continue' not properly in loop"
      [] c = "break_in_function_in_loop" -> "SyntaxError: 'break' outside loop"
      [] c = "continue_in_finally" -> "2"
      [] c = "break_in_finally" -> "'swallowed'"                          \* break discards the exception
      [] c = "nested_break" -> "[0, 1]"                                   \* only the innermost loop
      [] c = "elif_after_else" -> "SyntaxError: 'elif' block follows an 'else' block"
      [] c = "if_walrus" -> "5"
      [] c = "while_walrus" -> "[1, 2]"
      [] c = "if_bool_error" -> "ValueError: no"
      [] c = "while_cond_each_time" -> "3"
      [] c = "if_empty_body" -> "IndentationError: expected an indented block after 'if' statement on line 5"        \* after the replay's prelude
      [] c = "while_else_after_break_in_nested" -> "'else ran'"
      [] c = "if_expression_value" -> "['b', 'a']"
      [] c = "conditional_expr_lazy" -> "(2, ['f'])"                      \* only the chosen branch
      [] c = "conditional_expr_precedence" -> "3"
      [] c = "conditional_expr_lambda" -> "2"

Run(p) == CASE "conditions" \in DOMAIN p -> <<"None", Branch(p, 1)>>
             [] "n" \in DOMAIN p -> <<"None", Loop(p, 0)>>
             [] OTHER -> <<Case(p.case), <<>>>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* At most one suite of an if statement runs.
OneBranch == Done /\ "conditions" \in DOMAIN program =>
    Len(SelectSeq(outcome[2], LAMBDA e : e \notin {"True", "False"})) <= 1

\* A loop's else suite runs exactly when its condition ended it.
ElseUnlessBroken == Done /\ "n" \in DOMAIN program /\ program.else =>
    (\E i \in DOMAIN outcome[2] : outcome[2][i] = "else") <=> ~(\E i \in DOMAIN outcome[2] : outcome[2][i] = "break")
=============================================================================
