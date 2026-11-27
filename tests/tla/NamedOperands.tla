---------------------------- MODULE NamedOperands ---------------------------
(***************************************************************************)
(* Which error a statement whose expression is a name followed by another  *)
(* expression reports, as PLS-315 13.13 states it: a conditional without   *)
(* else after the name, after a further name, or after a not; one assigned *)
(* or after a comma; an attribute or a number before it, which read        *)
(* nothing further; a call with a bare star after a name, an error inside  *)
(* the first operand read; a conditional followed by a colon; and inside   *)
(* parentheses two adjacent expressions, the second one as much as parses, *)
(* None before a string, or a name before a string, which is no missing    *)
(* comma; and a print followed by as much of a call as parses. The outcome *)
(* is the message and its column.                                          *)
(***************************************************************************)
EXTENDS Naturals

Programs == {"cond", "chain", "not", "assigned", "comma", "attribute", "number", "call", "colon", "bracketed",
             "prefix", "keyword_string", "name_string", "print_prefix"}

VARIABLES program, outcome
vars == <<program, outcome>>

Else == "expected 'else' after 'if' expression"
Reported(p) == CASE p \in {"cond", "not"} -> <<Else, 3>>
                 [] p = "chain" -> <<Else, 5>>
                 [] p = "comma" -> <<Else, 6>>
                 [] p = "assigned" -> <<Else, 7>>
                 [] p = "attribute" -> <<"invalid syntax", 5>>
                 [] p \in {"number", "call", "colon"} -> <<"invalid syntax", 3>>
                 [] p \in {"bracketed", "keyword_string"} -> <<"invalid syntax. Perhaps you forgot a comma?", 2>>
                 [] p = "prefix" -> <<"invalid syntax. Perhaps you forgot a comma?", 3>>
                 [] p = "name_string" -> <<"invalid syntax", 4>>
                 [] p = "print_prefix" -> <<"Missing parentheses in call to 'print'. Did you mean print(...)?", 1>>

Init == program \in Programs /\ outcome = <<"pending", 0>>
Execute == outcome[1] = "pending" /\ outcome' = Reported(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome[1] # "pending"

\* Only expressions read after a name that no "(" follows, outside brackets,
\* report a conditional's missing else.
AfterName == Done /\ outcome[1] = Else => program \in {"cond", "chain", "not", "assigned", "comma"}

\* A string after a name is no second expression.
NameBeforeString == Done /\ program = "name_string" => outcome[1] = "invalid syntax"
=============================================================================
