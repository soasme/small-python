------------------------------- MODULE Frames -------------------------------
(***************************************************************************)
(* Frame objects, as The Python Language Reference specifies them          *)
(* (reference/datamodel.html#frame-objects, their special read-only and    *)
(* writable attributes, and clear()): a frame's code, caller (f_back,      *)
(* None for a generator's frame), locals, globals, builtins, instruction   *)
(* index, owning generator (None once it finishes or for a function), and  *)
(* line; f_trace, f_trace_lines, and f_trace_opcodes can be set (the       *)
(* latter two only to bools), f_lineno only by a trace function, the rest  *)
(* not at all; clear() drops the locals (of a generator's frame, once the  *)
(* generator finishes), finalizes a generator that has not started, and    *)
(* raises RuntimeError for an executing or suspended frame.                *)
(*                                                                         *)
(* A program defines                                                       *)
(*                                                                         *)
(*  1  def caller(): return work(1)    10  def gen(a):                     *)
(*  3  def work(a):                    11      b = a + 1                   *)
(*  4      b = a + 1                   12      yield b                     *)
(*  6      (raise and catch KeyError)  13      yield b                     *)
(*  8      fr = the traceback's frame                                      *)
(*  9      return ACT(fr)                                                  *)
(*                                                                         *)
(* and takes the frame of work while it runs ("running", ACT doing the     *)
(* operation) or after it returns ("finished"), or gen(1).gi_frame before  *)
(* next ("gennew"), after one next ("gensusp"), or after exhaustion        *)
(* ("gendone"), then reads an attribute or does an operation. The outcome  *)
(* is the result or the exception.                                         *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Sources == {"running", "finished", "gennew", "gensusp", "gendone"}
Ops == {"f_code", "f_back", "f_locals", "f_globals", "f_builtins", "f_lasti", "f_generator", "f_lineno", "f_trace",
        "settrace", "setlines", "setbadlines", "setlineno", "setcode", "clear"}
Programs == [source : Sources, op : Ops]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Generator(s) == s \in {"gennew", "gensusp", "gendone"}

Locals(s) == CASE s \in {"running", "finished"} -> "['a', 'b', 'fr']" [] s = "gennew" -> "['a']" [] OTHER -> "['a', 'b']"
Line(s) == CASE s \in {"running", "finished"} -> "9" [] s = "gennew" -> "10" [] s = "gensusp" -> "12" [] OTHER -> "13"

Run(p) ==
    LET s == p.source IN
    CASE p.op = "f_code" -> IF Generator(s) THEN "gen" ELSE "work"
      [] p.op = "f_back" -> IF Generator(s) THEN "None" ELSE "caller"
      [] p.op = "f_locals" -> Locals(s)
      [] p.op = "f_globals" -> "the module's"
      [] p.op = "f_builtins" -> "has len"
      [] p.op = "f_lasti" -> "int"
      [] p.op = "f_generator" -> IF s \in {"gennew", "gensusp"} THEN "gen" ELSE "None"
      [] p.op = "f_lineno" -> Line(s)
      [] p.op = "f_trace" -> "None"
      [] p.op = "settrace" -> "len"
      [] p.op = "setlines" -> "False"
      [] p.op = "setbadlines" -> "TypeError"
      [] p.op = "setlineno" -> "ValueError"
      [] p.op = "setcode" -> "AttributeError"
      [] p.op = "clear" -> CASE s \in {"running", "gensusp"} -> "RuntimeError"
                             \* A generator that has not started is finalized; its frame stays its own.
                             [] s = "gennew" -> "{'a': 1} None"
                             [] s = "gendone" -> "{} None"
                             [] OTHER -> "{}"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* An executing or suspended frame cannot be cleared.
ClearRefused == Done /\ program.op = "clear" /\ program.source \in {"running", "gensusp"} => outcome = "RuntimeError"

\* A generator's frame has no caller while it is not running.
GeneratorUnlinked == Done /\ program.op = "f_back" /\ Generator(program.source) => outcome = "None"
=============================================================================
