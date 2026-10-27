----------------------------- MODULE Precedence -----------------------------
(***************************************************************************)
(* Operator precedence and associativity, as The Python Language Reference *)
(* specifies them (reference/expressions.html#operator-precedence and the  *)
(* expression grammar of reference/grammar.html): from lowest to highest   *)
(* binding, lambda and assignment expressions, conditional expressions,    *)
(* or, and, not, comparisons (chained, with membership and identity        *)
(* tests), |, ^, &, shifts, + and -, the multiplicative operators *, @, /, *)
(* //, and %, the unary operators -, +, and ~, the power operator, await,  *)
(* and primaries (subscriptions, slicings, calls, and attribute            *)
(* references); every binary operator groups from left to right except **  *)
(* which groups from right to left, and ** binds tighter than a unary      *)
(* operator on its left but looser than one on its right.                  *)
(*                                                                         *)
(* A program evaluates a OP1 b OP2 c, -a OP b (or +a, ~a), or a OP -b for  *)
(* symbolic operands whose operator methods return the parenthesized form  *)
(* of the operation they perform; or it runs one of the CASES. The        *)
(* outcome is the parenthesized form, or the result's repr or the          *)
(* exception.                                                              *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Binary == {"**", "*", "@", "/", "//", "%", "+", "-", "<<", ">>", "&", "^", "|"}
Unary == {"-", "+", "~"}
Cases == {"not_eq", "not_in", "or_and", "and_or", "not_or", "not_and", "cmp_chain_bitor", "cmp_chain_mixed",
          "bitand_cmp", "cond_or", "cond_nested", "cond_lambda", "lambda_lowest", "walrus_lowest",
          "await_power", "unary_power_right", "neg_power", "double_neg", "not_not", "power_attr",
          "call_before_unary", "subscript_before_power", "star_in_call", "comparison_not_associative",
          "is_not_vs_not", "in_not_in", "tuple_comma_lowest", "yield_lowest",
          "string_concat_before_ops", "unary_not_bitwise", "invert_bool", "starred_precedence"}
Programs == [left : Binary, right : Binary] \cup [unary : Unary, binary : Binary, position : {"prefix", "operand"}]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* Binding strength; the unary operators sit between ** and *.
Level(o) == CASE o = "**" -> 7
              [] o \in {"*", "@", "/", "//", "%"} -> 5
              [] o \in {"+", "-"} -> 4
              [] o \in {"<<", ">>"} -> 3
              [] o = "&" -> 2
              [] o = "^" -> 1
              [] o = "|" -> 0
UnaryLevel == 6

Paren(x, o, y) == "(" \o x \o " " \o o \o " " \o y \o ")"

\* a o1 b o2 c groups left unless o2 binds tighter, or both are **.
Group(o1, o2) ==
    IF Level(o1) > Level(o2) \/ (Level(o1) = Level(o2) /\ o1 # "**")
    THEN Paren(Paren("a", o1, "b"), o2, "c")
    ELSE Paren("a", o1, Paren("b", o2, "c"))

\* u a o b: the unary operator takes a alone unless o binds tighter (only
\* **); a o u b: the unary operator always takes b.
UnaryGroup(u, o, position) ==
    IF position = "operand" THEN Paren("a", o, "(" \o u \o "b)")
    ELSE IF Level(o) > UnaryLevel THEN "(" \o u \o Paren("a", o, "b") \o ")"
    ELSE Paren("(" \o u \o "a)", o, "b")

Case(c) ==
    CASE c = "not_eq" -> "True"
      [] c = "not_in" -> "False"
      [] c = "or_and" -> "1"
      [] c = "and_or" -> "2"
      [] c = "not_or" -> "True"
      [] c = "not_and" -> "False"
      [] c = "cmp_chain_bitor" -> "True"
      [] c = "cmp_chain_mixed" -> "True"
      [] c = "bitand_cmp" -> "True"
      [] c = "cond_or" -> "5"
      [] c = "cond_nested" -> "3"
      [] c = "cond_lambda" -> "0"
      [] c = "lambda_lowest" -> "2"
      [] c = "walrus_lowest" -> "7"
      [] c = "await_power" -> "4"
      [] c = "unary_power_right" -> "0.5"
      [] c = "neg_power" -> "-4"
      [] c = "double_neg" -> "2"
      [] c = "not_not" -> "True"
      [] c = "power_attr" -> "2"
      [] c = "call_before_unary" -> "-3"
      [] c = "subscript_before_power" -> "4"
      [] c = "star_in_call" -> "2"
      [] c = "comparison_not_associative" -> "True"
      [] c = "is_not_vs_not" -> "(True, False)"
      [] c = "in_not_in" -> "True"
      [] c = "tuple_comma_lowest" -> "(1, 3)"
      [] c = "yield_lowest" -> "(1, 2)"
      [] c = "string_concat_before_ops" -> "'abab'"
      [] c = "unary_not_bitwise" -> "False"
      [] c = "invert_bool" -> "-2"
      [] c = "starred_precedence" -> "SyntaxError: invalid syntax"

Run(p) == CASE "left" \in DOMAIN p -> Group(p.left, p.right)
             [] "unary" \in DOMAIN p -> UnaryGroup(p.unary, p.binary, p.position)
             [] OTHER -> Case(p.case)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Operators of one level group left, except **.
LeftAssociative == Done /\ "left" \in DOMAIN program /\ program.left = program.right =>
    (outcome = Paren(Paren("a", program.left, "b"), program.right, "c")) <=> program.left # "**"
=============================================================================
