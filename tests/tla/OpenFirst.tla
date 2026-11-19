------------------------------- MODULE OpenFirst -------------------------------
(***************************************************************************)
(* The first open() of a program, as PLS-315 19.3.28 and the host hook     *)
(* HostOpen (Annex B) specify it, does what any later one does: a program  *)
(* writes "x" to a file in the mounted directory, then makes two calls,    *)
(* each giving the file and mode positionally, by keyword, or a mode it    *)
(* rejects, or an unknown keyword. The outcome of each is the text read,   *)
(* or the exception; neither depends on which came first.                  *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Calls == {"positional", "keywords", "mode", "unknown"}
Programs == [first : Calls, second : Calls]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Result(call) == CASE call \in {"positional", "keywords"} -> "x"
                  [] call = "mode" -> "ValueError"
                  [] call = "unknown" -> "TypeError"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ UNCHANGED program /\ outcome' = Result(program.first) \o " / " \o Result(program.second)
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
\* Keywords open the file as positional arguments do.
KeywordsAsPositional == outcome # Pending /\ program.first = "keywords" => outcome = Result("positional") \o " / " \o Result(program.second)
=============================================================================
