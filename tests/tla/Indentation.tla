---------------------------- MODULE Indentation ----------------------------
(***************************************************************************)
(* Indentation, as The Python Language Reference specifies it              *)
(* (reference/lexical_analysis.html#indentation): the stack of indentation *)
(* levels that turns leading whitespace into INDENT and DEDENT tokens,     *)
(* tabs advancing to the next multiple of eight, TabError when the meaning *)
(* depends on the tab size, IndentationError for a dedent to no level on   *)
(* the stack, an unexpected indent, or a missing block, blank lines that   *)
(* do not count, and the DEDENTs at the end marker.                        *)
(*                                                                         *)
(* A program is up to four lines, each indented by nothing, a space, or a  *)
(* tab, and each                                                           *)
(*                                                                         *)
(*     s   log.append(<line number>)                                       *)
(*     t   if 1:                                                           *)
(*     f   if 0:                                                           *)
(*     b   nothing (a blank line)                                          *)
(*                                                                         *)
(* The outcome is the log the program leaves, or the error's class.        *)
(***************************************************************************)
EXTENDS Integers, Sequences, FiniteSets

Indents == {"", " ", "\t"}
Kinds == {"s", "t", "f", "b"}
Programs == UNION {[1..n -> Indents \X Kinds] : n \in 1..4}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", <<>>>>

\* A line's column with tabs to the next multiple of 8, and with tabs as
\* one column (the "alternate" column the tokenizer compares too).
Col(indent) == CASE indent = "" -> 0 [] indent = " " -> 1 [] indent = "\t" -> 8
AltCol(indent) == IF indent = "" THEN 0 ELSE 1

\* Runs the lines from line i with the indentation stack (pairs of column
\* and alternate column), whether the previous line opened a block, and
\* the stack of whether each enclosing block runs.
RECURSIVE Run(_, _, _, _, _, _)
Run(p, i, stack, opened, runs, log) ==
    IF i > Len(p) THEN
        IF opened THEN <<"IndentationError", <<>>>> ELSE <<"ok", log>>     \* a block ended at the end marker
    ELSE IF p[i][2] = "b" THEN Run(p, i + 1, stack, opened, runs, log)
    ELSE
        LET col == Col(p[i][1])  alt == AltCol(p[i][1])
            top == stack[Len(stack)]
            \* Dedent: pop the levels above this column.
            kept == LET n == CHOOSE n \in 1..Len(stack) : stack[n][1] <= col /\ (n = Len(stack) \/ stack[n + 1][1] > col)
                    IN  SubSeq(stack, 1, n)
            kind == p[i][2]
            \* The statement's effect, then the rest.
            Next(st, rs) ==
                IF kind = "s" THEN Run(p, i + 1, st, FALSE, rs, IF \A k \in DOMAIN rs : rs[k] THEN Append(log, i) ELSE log)
                ELSE Run(p, i + 1, st, TRUE, Append(rs, kind = "t"), log)
        IN  CASE col = top[1] /\ alt # top[2] -> <<"TabError", <<>>>>
              [] col = top[1] /\ opened -> <<"IndentationError", <<>>>>               \* expected an indented block
              [] col = top[1] -> Next(stack, runs)
              [] col > top[1] /\ alt <= top[2] -> <<"TabError", <<>>>>
              [] col > top[1] /\ ~opened -> <<"IndentationError", <<>>>>              \* unexpected indent
              [] col > top[1] -> Next(Append(stack, <<col, alt>>), runs)
              [] kept[Len(kept)][1] # col -> <<"IndentationError", <<>>>>             \* unindent matches no level
              [] kept[Len(kept)][2] # alt -> <<"TabError", <<>>>>
              [] opened -> <<"IndentationError", <<>>>>
              [] OTHER -> Next(kept, SubSeq(runs, 1, Len(runs) - (Len(stack) - Len(kept))))

Execute == outcome = Pending /\ outcome' = Run(program, 1, <<<<0, 0>>>>, FALSE, <<>>, <<>>) /\ UNCHANGED program
Init == program \in Programs /\ outcome = Pending
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Blank lines never change the outcome.
BlankLinesIgnored == Done =>
    LET kept == SelectSeq(program, LAMBDA l : l[2] # "b")
        renumber == [k \in DOMAIN outcome[2] |-> Cardinality({j \in 1..outcome[2][k] : program[j][2] # "b"})]
    IN  kept # <<>> /\ outcome[1] = "ok" =>
        LET r == Run(kept, 1, <<<<0, 0>>>>, FALSE, <<>>, <<>>) IN r[1] = "ok" /\ r[2] = renumber

\* Without tabs there is never a TabError.
TabsOnly == Done /\ (\A k \in DOMAIN program : program[k][1] # "\t") => outcome[1] # "TabError"

\* Statements run in order: the log is increasing.
InOrder == Done => \A a, b \in DOMAIN outcome[2] : a < b => outcome[2][a] < outcome[2][b]
=============================================================================
