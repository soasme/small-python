---------------------------- MODULE CompileModes ----------------------------
(***************************************************************************)
(* Structure of a program and its top-level components, as The Python      *)
(* Language Reference specifies them (reference/executionmodel.html#       *)
(* structure-of-a-program, reference/toplevel_components.html, and         *)
(* reference/simple_stmts.html#expression-statements): file input ("exec") *)
(* is any sequence of statements and evaluates to None; expression input   *)
(* ("eval") is one expression, possibly followed by blank lines, and       *)
(* yields its value; interactive input ("single") is one statement, which  *)
(* may be a simple statement list or a compound statement, and passes the  *)
(* value of each expression statement to sys.displayhook, which shows      *)
(* anything but None and binds it to builtins._; anything else is a        *)
(* SyntaxError (an unexpected indent an IndentationError), and an unknown  *)
(* mode is a ValueError.                                                   *)
(*                                                                         *)
(* A program compiles SOURCE in MODE and runs it with a fresh namespace,   *)
(* recording the values passed to sys.displayhook. SOURCE is "1 + 1",      *)
(* "x = 1", "x = 1; 2", "x = 1\ny = 2", an if statement whose body is the  *)
(* expressions 3 and 4, "None", "", " 1", "1\n\n", or the starred list     *)
(* "*[1], 2", which only eval input, a list of plain expressions           *)
(* (PLS-315 17.6.3), rejects; MODE is exec, eval, single, or bad. The      *)
(* outcome is the result, then the displayed values,                       *)
(* or the exception.                                                       *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Sources == {"expr", "assign", "list", "lines", "compound", "none", "empty", "indented", "trailing", "starred"}
Programs == [source : Sources, mode : {"exec", "eval", "single", "bad"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Exec(s) == "None []"

Eval(s) == CASE s \in {"expr", "trailing"} -> "2 []"
             [] s = "none" -> "None []"
             [] OTHER -> "SyntaxError"

Single(s) == CASE s = "expr" -> "None [2]"
               [] s = "list" -> "None [2]"
               [] s = "compound" -> "None [3, 4]"
               [] s = "none" -> "None [None]"
               [] s = "trailing" -> "None [2]"
               [] s = "assign" -> "None []"
               [] s = "starred" -> "None [(1, 2)]"
               [] OTHER -> "SyntaxError"                      \* two statements, nothing, or an indent

Run(p) == CASE p.mode = "bad" -> "ValueError"
            [] p.source = "indented" -> "IndentationError"         \* a SyntaxError in every mode
            [] p.mode = "exec" -> Exec(p.source)
            [] p.mode = "eval" -> Eval(p.source)
            [] p.mode = "single" -> Single(p.source)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Only interactive input displays values.
OnlySingleDisplays == Done /\ program.mode # "single" => outcome \in {"None []", "2 []", "SyntaxError", "IndentationError", "ValueError"}
=============================================================================
