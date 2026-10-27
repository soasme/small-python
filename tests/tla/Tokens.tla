------------------------------- MODULE Tokens -------------------------------
(***************************************************************************)
(* Tokens, as The Python Language Reference specifies them                 *)
(* (reference/lexical_analysis.html#other-tokens, #operators-and-          *)
(* delimiters, #whitespace-between-tokens): the longest string that forms  *)
(* a token is read at each point; whitespace between tokens separates     *)
(* them and is otherwise ignored; augmented assignment operators are       *)
(* delimiters, not operators.                                              *)
(*                                                                         *)
(* A program is  r = <source>  run with a = 2 and b = 1, where the source  *)
(* is up to five characters from  a b * < = -  and space. These spell      *)
(* names, *, **, <, <<, <=, =, ==, -, and the delimiters *=, **=, <<=, -=, *)
(* which here are syntax errors, so the outcome shows how the characters   *)
(* split into tokens. It is r's type and repr, or the exception.           *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Chars == {"a", "b", "*", "<", "=", "-", " "}
Programs == UNION {[1..n -> Chars] : n \in 0..5}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", "">>
Error(name) == <<name, "">>
At(s, i) == IF i >= 1 /\ i <= Len(s) THEN s[i] ELSE "EOF"
Letter(c) == c \in {"a", "b"}

(***************************************************************************)
(* Tokens, as <<kind, name, characters>>: the longest operator or         *)
(* delimiter, or a name (a run of letters).                                *)
(***************************************************************************)
RECURSIVE Name(_, _)
Name(s, i) == IF Letter(At(s, i)) THEN s[i] \o Name(s, i + 1) ELSE ""
RECURSIVE Lex(_, _)
Lex(s, i) ==
    LET Op(text) == <<<<text, "", SubSeq(s, i, i + Len(text) - 1)>>>> \o Lex(s, i + Len(text))
        c == At(s, i)  d == At(s, i + 1)  e == At(s, i + 2)
    IN  CASE i > Len(s) -> <<>>
          [] c = " " -> Lex(s, i + 1)
          [] Letter(c) -> LET n == Name(s, i) IN <<<<"name", n, SubSeq(s, i, i + Len(n) - 1)>>>> \o Lex(s, i + Len(n))
          [] c = "*" /\ d = "*" /\ e = "=" -> Op("**=")
          [] c = "*" /\ d = "*" -> Op("**")
          [] c = "<" /\ d = "<" /\ e = "=" -> Op("<<=")
          [] c = "<" /\ d = "<" -> Op("<<")
          [] c \in {"*", "<", "=", "-"} /\ d = "=" -> Op(c \o "=")  \* *=, <=, ==, -=
          [] OTHER -> Op(c)
Kind(t, i) == IF i >= 1 /\ i <= Len(t) THEN t[i][1] ELSE "EOF"

(***************************************************************************)
(* Values, as <<kind, n>>: <<"int", n>>, <<"bool", 0 or 1>>, <<"float", d>> *)
(* for 1/d (from a negative power), or an exception once evaluating fails. *)
(* Parsing returns <<ok, next position, value>>; operands are evaluated    *)
(* left to right, so the left one's exception wins.                        *)
(***************************************************************************)
Failed(v) == v[1] \notin {"int", "bool", "float"}
Then(x, y, F(_, _)) == IF Failed(x) THEN x ELSE IF Failed(y) THEN y ELSE F(x, y)
Num(n) == <<"int", n>>
Pow(x, y) == IF y[2] >= 0 THEN Num(x[2] ^ y[2]) ELSE <<"float", x[2] ^ (-y[2])>>
Shift(x, y) == IF y[2] < 0 THEN <<"ValueError", 0>> ELSE Num(x[2] * 2 ^ y[2])
Less(op, x, y) == CASE op = "<" -> x[2] < y[2] [] op = "<=" -> x[2] <= y[2] [] op = "==" -> x[2] = y[2]

RECURSIVE Factor(_, _), Power(_, _), Term(_, _, _), Sum(_, _, _), Shifts(_, _, _), Chain(_, _, _, _)
Power(t, i) ==
    IF Kind(t, i) # "name" THEN <<FALSE, 0, Num(0)>>
    ELSE LET v == CASE t[i][2] = "a" -> Num(2) [] t[i][2] = "b" -> Num(1) [] OTHER -> <<"NameError", 0>>
         IN  IF Kind(t, i + 1) # "**" THEN <<TRUE, i + 1, v>>
             ELSE LET f == Factor(t, i + 2) IN <<f[1], f[2], Then(v, f[3], Pow)>>
Factor(t, i) ==
    IF Kind(t, i) = "-" THEN LET f == Factor(t, i + 1) IN <<f[1], f[2], IF Failed(f[3]) THEN f[3] ELSE Num(-f[3][2])>>
    ELSE Power(t, i)
\* Left-associative levels: the operand at i, then more of op and operands.
Term(t, i, v) == IF Kind(t, i) # "*" THEN <<TRUE, i, v>>
                 ELSE LET f == Factor(t, i + 1) IN IF ~f[1] THEN f ELSE Term(t, f[2], Then(v, f[3], LAMBDA x, y : Num(x[2] * y[2])))
Product(t, i) == LET f == Factor(t, i) IN IF ~f[1] THEN f ELSE Term(t, f[2], f[3])
Sum(t, i, v) == IF Kind(t, i) # "-" THEN <<TRUE, i, v>>
                ELSE LET f == Product(t, i + 1) IN IF ~f[1] THEN f ELSE Sum(t, f[2], Then(v, f[3], LAMBDA x, y : Num(x[2] - y[2])))
Difference(t, i) == LET f == Product(t, i) IN IF ~f[1] THEN f ELSE Sum(t, f[2], f[3])
Shifts(t, i, v) == IF Kind(t, i) # "<<" THEN <<TRUE, i, v>>
                   ELSE LET f == Difference(t, i + 1) IN IF ~f[1] THEN f ELSE Shifts(t, f[2], Then(v, f[3], Shift))
Shifted(t, i) == LET f == Difference(t, i) IN IF ~f[1] THEN f ELSE Shifts(t, f[2], f[3])
\* A chain a < b <= c: the result so far (once false, the rest is not
\* evaluated) and the previous operand.
Chain(t, i, result, prev) ==
    IF Kind(t, i) \notin {"<", "<=", "=="} THEN <<TRUE, i, result>>
    ELSE LET f == Shifted(t, i + 1)
             next == CASE result = <<"bool", 0>> \/ Failed(result) -> result
                       [] Failed(f[3]) -> f[3]
                       [] OTHER -> <<"bool", IF Less(t[i][1], prev, f[3]) THEN 1 ELSE 0>>
         IN  IF ~f[1] THEN f ELSE Chain(t, f[2], next, f[3])
Comparison(t, i) ==
    LET f == Shifted(t, i)
    IN  IF ~f[1] \/ Kind(t, f[2]) \notin {"<", "<=", "=="} THEN f
        ELSE LET c == Chain(t, f[2], <<"bool", 1>>, f[3])
             IN  <<c[1], c[2], IF Failed(f[3]) THEN f[3] ELSE c[3]>>

\* r = target = ... = expression: each target is a name.
RECURSIVE Targets(_, _)
Targets(t, i) ==
    IF Kind(t, i) = "name" /\ Kind(t, i + 1) = "=" THEN Targets(t, i + 2) ELSE i
Repr(v) == CASE v[1] = "int" -> <<"int", ToString(v[2])>>
             [] v[1] = "bool" -> <<"bool", IF v[2] = 1 THEN "True" ELSE "False">>
             [] v[1] = "float" -> <<"float", CASE v[2] = 1 -> "1.0" [] v[2] = 2 -> "0.5" [] v[2] = 4 -> "0.25">>
             [] OTHER -> Error(v[1])
Run(s) ==
    LET t == Lex(s, 1)
        e == Comparison(t, Targets(t, 1))
    IN  IF ~e[1] \/ e[2] # Len(t) + 1 THEN Error("SyntaxError") ELSE Repr(e[3])

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Whitespace before or after the tokens changes nothing.
Surrounding == Done /\ Len(program) < 5 =>
    Run(<<" ">> \o program) = outcome /\ Run(Append(program, " ")) = outcome

\* Spaces between tokens change nothing, as long as they split no token.
Spaced == Done =>
    LET t == Lex(program, 1)
        RECURSIVE Spell(_)
        Spell(k) == IF k > Len(t) THEN <<>>
                    ELSE <<" ">> \o t[k][3] \o Spell(k + 1)
    IN  Run(Spell(1)) = outcome
=============================================================================
