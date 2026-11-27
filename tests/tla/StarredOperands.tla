-------------------------- MODULE StarredOperands --------------------------
(***************************************************************************)
(* What a starred item's operand may be, as PLS-315 14.7 and 13.15 state   *)
(* it. A del statement's starred item after a name or a call: a name,      *)
(* which parses and cannot be deleted, or a lambda, which does not parse,  *)
(* so the call before it is the error, or else the star. A parenthesized   *)
(* starred item alone: a name, a lambda, an or of names or a yield, which  *)
(* fails at its first token. The outcome is the error's message.           *)
(***************************************************************************)
EXTENDS Naturals

Programs == [part : {"del"}, before : {"name", "call"}, operand : {"name", "lambda"}]
            \cup [part : {"group"}, operand : {"name", "lambda", "or", "yield"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Reported(p) ==
    CASE p.part = "del" /\ p.before = "call" -> "cannot delete function call"
      [] p.part = "del" /\ p.operand = "name" -> "cannot delete starred"
      [] p.part = "del" -> "invalid syntax"
      [] p.part = "group" /\ p.operand = "yield" -> "Invalid star expression"
      [] p.part = "group" -> "cannot use starred expression here"

Init == program \in Programs /\ outcome = "pending"
Execute == outcome = "pending" /\ outcome' = Reported(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # "pending"

\* Items before a del's starred item are checked before it.
BeforeFirst == Done /\ program.part = "del" /\ program.before = "call" => outcome = "cannot delete function call"

\* A parenthesized starred item that parses is the parser's error over it.
GroupError == Done /\ program.part = "group" /\ program.operand # "yield" => outcome = "cannot use starred expression here"
=============================================================================
