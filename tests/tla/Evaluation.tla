---------------------------- MODULE Evaluation ----------------------------
(***************************************************************************)
(* Evaluation order, as The Python Language Reference specifies it         *)
(* (reference/expressions.html#evaluation-order, #boolean-operations,      *)
(* #comparisons, and reference/simple_stmts.html#assignment-statements),   *)
(* for each of these forms, with t(k) logging "tk" and returning v_k, and  *)
(* c a container logging "get", "set", "attr" (for c.f), and "call":       *)
(*                                                                         *)
(*     and      t(1) and t(2)                                              *)
(*     or       t(1) or t(2)                                               *)
(*     chain    t(1) < t(2) < t(3)                                         *)
(*     cond     t(2) if t(1) else t(3)                                     *)
(*     arith    t(1) - t(2) * t(3)                                         *)
(*     call     c.f(t(1), k=t(2), *[t(3)])                                 *)
(*     dict     {t(1): t(2), t(3): 0}                                      *)
(*     dictcomp {t(1): t(2) for _ in [0]}                                  *)
(*     assign   c[t(1)] = t(2)                                             *)
(*     multi    c[t(1)] = c[t(2)] = t(3)                                   *)
(*     augment  c[t(1)] += t(2)                                            *)
(*     unpack   c[t(1)], c[t(2)] = t(3), t(3)                              *)
(*                                                                         *)
(* for v_k in 0..2. The outcome is the log and the value, as a string      *)
(* ("-" for a statement).                                                  *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Forms == {"and", "or", "chain", "cond", "arith", "call", "dict", "dictcomp",
          "assign", "multi", "augment", "unpack"}
Programs == [form : Forms, v : [1..3 -> 0..2]]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<<<>>, "pending">>
T(k) == "t" \o ToString(k)
Str(n) == ToString(n)
Bool(b) == IF b THEN "True" ELSE "False"

Evaluate(p) ==
    LET v == p.v
    IN  CASE p.form = "and" -> IF v[1] = 0 THEN <<<<T(1)>>, Str(v[1])>> ELSE <<<<T(1), T(2)>>, Str(v[2])>>
          [] p.form = "or" -> IF v[1] # 0 THEN <<<<T(1)>>, Str(v[1])>> ELSE <<<<T(1), T(2)>>, Str(v[2])>>
          \* t(2) is evaluated once; t(3) only if the first comparison holds.
          [] p.form = "chain" -> IF v[1] < v[2] THEN <<<<T(1), T(2), T(3)>>, Bool(v[2] < v[3])>>
                                 ELSE <<<<T(1), T(2)>>, "False">>
          [] p.form = "cond" -> IF v[1] # 0 THEN <<<<T(1), T(2)>>, Str(v[2])>> ELSE <<<<T(1), T(3)>>, Str(v[3])>>
          \* Operands left to right, whatever the precedence.
          [] p.form = "arith" -> <<<<T(1), T(2), T(3)>>, Str(v[1] - v[2] * v[3])>>
          \* The callee before its arguments, the arguments in source order,
          \* except that *args are processed before keyword arguments.
          [] p.form = "call" -> <<<<"attr", T(1), T(3), T(2), "call">>, "-">>
          [] p.form = "dict" -> <<<<T(1), T(2), T(3)>>, "-">>
          \* A key before its value.
          [] p.form = "dictcomp" -> <<<<T(1), T(2)>>, "-">>
          \* The right-hand side first, then targets left to right, each
          \* target's subexpressions before it is assigned.
          [] p.form = "assign" -> <<<<T(2), T(1), "set">>, "-">>
          [] p.form = "multi" -> <<<<T(3), T(1), "set", T(2), "set">>, "-">>
          \* An augmented target is evaluated once, before the right side.
          [] p.form = "augment" -> <<<<T(1), "get", T(2), "set">>, "-">>
          [] p.form = "unpack" -> <<<<T(3), T(3), T(1), "set", T(2), "set">>, "-">>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Evaluate(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
Log == outcome[1]
Index(s, x) == CHOOSE i \in DOMAIN s : s[i] = x
Logged(x) == \E i \in DOMAIN Log : Log[i] = x

\* Each operand of an expression is evaluated at most once, left to right.
LeftToRight == Done /\ program.form \in {"and", "or", "chain", "cond", "arith", "dict", "dictcomp"} =>
    LET operands == {i \in DOMAIN Log : Log[i] \in {T(1), T(2), T(3)}}
        k(i) == CHOOSE n \in 1..3 : Log[i] = T(n)
    IN  \A i, j \in operands : i < j => k(i) < k(j)

\* "f(k=t(2), *[t(3)])" unpacks t(3) first.
StarBeforeKeywords == Done /\ program.form = "call" => Index(Log, T(3)) < Index(Log, T(2))

\* An assignment evaluates its whole right-hand side before any target.
RightFirst == Done /\ program.form \in {"assign", "multi", "unpack"} =>
    Index(Log, "set") > Index(Log, T(IF program.form = "assign" THEN 2 ELSE 3))

\* Short-circuiting skips the right operand exactly when the left decides.
ShortCircuit == Done /\ program.form \in {"and", "or"} =>
    (Logged(T(2)) <=> (IF program.form = "and" THEN program.v[1] # 0 ELSE program.v[1] = 0))
=============================================================================
