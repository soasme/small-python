-------------------------- MODULE StarredOperands --------------------------
(***************************************************************************)
(* What a starred item's operand may be, as PLS-315 14.7, 13.15, 13.2.6    *)
(* and 13.3.2 state it. A del statement's starred item after a name or a   *)
(* call: a name, which parses and cannot be deleted, or a lambda, which    *)
(* does not parse, so the call before it is the error, or else the star. A *)
(* parenthesized starred item alone: a name, a lambda, an or of names or a *)
(* yield, which fails at its first token. A generator expression's or list *)
(* comprehension's starred element, an or of names, and a not of a name    *)
(* starred in a list, a call or a subscript, where only a call or a        *)
(* subscript takes it, or compared or added, where only an arithmetic      *)
(* operator has its own error. The outcome is the error's message, or      *)
(* "ok".                                                                   *)
(***************************************************************************)
EXTENDS Naturals

Programs == [part : {"del"}, before : {"name", "call"}, operand : {"name", "lambda"}]
            \cup [part : {"group"}, operand : {"name", "lambda", "or", "yield"}]
            \cup [part : {"element"}, display : {"generator", "list"}]
            \cup [part : {"not"}, place : {"list", "call", "comparison", "sum", "subscript"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Reported(p) ==
    CASE p.part = "del" /\ p.before = "call" -> "cannot delete function call"
      [] p.part = "del" /\ p.operand = "name" -> "cannot delete starred"
      [] p.part = "del" -> "invalid syntax"
      [] p.part = "group" /\ p.operand = "yield" -> "Invalid star expression"
      [] p.part = "group" -> "cannot use starred expression here"
      [] p.part = "element" /\ p.display = "generator" -> "ok"
      [] p.part = "element" -> "invalid syntax"
      [] p.part = "not" /\ p.place \in {"list", "comparison"} -> "invalid syntax"
      [] p.part = "not" /\ p.place = "sum" -> "'not' after an operator must be parenthesized"
      [] p.part = "not" -> "ok"

Init == program \in Programs /\ outcome = "pending"
Execute == outcome = "pending" /\ outcome' = Reported(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # "pending"

\* Items before a del's starred item are checked before it.
BeforeFirst == Done /\ program.part = "del" /\ program.before = "call" => outcome = "cannot delete function call"

\* Only a generator expression's element a call's argument and a subscript's item take an
\* expression that is no bitwise or.
ExpressionOnly == Done /\ outcome = "ok" => (program.part = "element" /\ program.display = "generator")
                                          \/ (program.part = "not" /\ program.place \in {"call", "subscript"})
=============================================================================
