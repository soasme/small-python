----------------------------- MODULE Tracebacks -----------------------------
(***************************************************************************)
(* Traceback objects, as The Python Language Reference specifies them      *)
(* (reference/datamodel.html#traceback-objects): as the search for a       *)
(* handler unwinds the stack, each level puts a traceback in front of the  *)
(* current one, so tb_next leads towards where the exception occurred;     *)
(* tb_lineno is where the exception passed through a level, which differs  *)
(* from the frame's line after a finally clause or handler ran; tb_frame,  *)
(* tb_lineno, and tb_lasti are read-only and tb_next is writable (not into *)
(* a loop); tracebacks can be made by calling the traceback type, which    *)
(* checks its arguments; with_traceback() sets the traceback that a raise  *)
(* then extends.                                                           *)
(*                                                                         *)
(* A program defines                                                       *)
(*                                                                         *)
(*  1  def b():                        8  def h():                         *)
(*  2      raise KeyError              9      try:                         *)
(*  3  def a():                       10          CALL                     *)
(*  4      try:                       11      except Exception as e:       *)
(*  5          b()                    12          return e                 *)
(*  6      VIA                                                             *)
(*  7          BODY                                                        *)
(*                                                                         *)
(* where CALL raises KeyError itself (depth 0), calls b() (1), or calls    *)
(* a() (2), and a's try has VIA/BODY "finally: pass", "except KeyError:    *)
(* raise", "except KeyError as x: raise ValueError from x", or none (if    *)
(* True:/if False: pass). It walks the traceback of h()'s exception (and   *)
(* its cause), giving each level's function, tb_lineno, and f_lineno; or,  *)
(* with t the traceback of h() at depth 0 or 1, does an explicit operation.*)
(***************************************************************************)
EXTENDS Naturals, Sequences

Vias == {"none", "finally", "reraise", "from"}
Explicit == {"construct", "link", "badnext", "badframe", "badlasti", "loop", "self", "setnext", "setlineno", "setframe",
             "setlasti", "with", "fresh"}
Programs == [via : {"none"}, depth : {0, 1}, op : {"chain"}] \cup [via : Vias, depth : {2}, op : {"chain"}]
            \cup [via : {"none"}, depth : {1}, op : Explicit]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Level(name, tbline, fline) == [name |-> name, tbline |-> tbline, fline |-> fline]
\* The levels from h outwards to where the exception occurred.
Chain(p) ==
    CASE p.depth = 0 -> <<Level("h", "10", "12")>>
      [] p.depth = 1 -> <<Level("h", "10", "12"), Level("b", "2", "2")>>
      [] p.via = "none" -> <<Level("h", "10", "12"), Level("a", "5", "5"), Level("b", "2", "2")>>
      \* The handler or finally clause ran on, so the frame's line is 7.
      [] p.via \in {"finally", "reraise"} -> <<Level("h", "10", "12"), Level("a", "5", "7"), Level("b", "2", "2")>>
      [] p.via = "from" -> <<Level("h", "10", "12"), Level("a", "7", "7")>>
Cause(p) == IF p.via = "from" /\ p.depth = 2 THEN <<Level("a", "5", "7"), Level("b", "2", "2")>> ELSE <<>>

RECURSIVE Render(_)
Render(s) == IF s = <<>> THEN "" ELSE " " \o s[1].name \o ":" \o s[1].tbline \o "/" \o s[1].fline \o Render(Tail(s))

Run(p) ==
    CASE p.op = "chain" -> (IF p.via = "from" /\ p.depth = 2 THEN "ValueError" ELSE "KeyError") \o Render(Chain(p))
                           \o (IF Cause(p) = <<>> THEN "" ELSE " cause" \o Render(Cause(p)))
      [] p.op = "construct" -> "5 None 0"         \* TracebackType(None, frame, 0, 5)
      [] p.op = "link" -> "True"                  \* the first argument becomes tb_next
      [] p.op \in {"badnext", "badframe", "badlasti"} -> "TypeError"
      [] p.op \in {"loop", "self"} -> "ValueError"
      [] p.op = "setnext" -> "1"                  \* t.tb_next = None leaves one level
      [] p.op \in {"setlineno", "setframe", "setlasti"} -> "AttributeError"
      [] p.op = "with" -> "3 True"                \* the new raise's level, then t's two
      [] p.op = "fresh" -> "None"                 \* an exception never raised has none

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The traceback starts at the handler's level and has one level per frame unwound.
OuterFirst == Done /\ program.op = "chain" =>
    Chain(program)[1].name = "h" /\ (program.via = "from" \/ Len(Chain(program)) = program.depth + 1)
=============================================================================
