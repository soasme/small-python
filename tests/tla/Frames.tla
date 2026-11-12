------------------------------- MODULE Frames -------------------------------
(***************************************************************************)
(* Frame objects, as The Python Language Reference specifies them          *)
(* (reference/datamodel.html#frame-objects, their special read-only and    *)
(* writable attributes, and clear()): a frame's code, caller (f_back,      *)
(* None for a generator's frame), locals, globals, builtins, instruction   *)
(* index, owning generator (None once it finishes or for a function), and  *)
(* line, which with its code's name ends its repr; f_trace, f_trace_lines, *)
(* and f_trace_opcodes can be set (the latter two only to bools), f_lineno *)
(* only by a trace function, the rest not at all, and f_lineno,          *)
(* f_trace_lines and f_trace_opcodes not deleted; f_locals hashes its keys *)
(* first, takes a key equal to a variable's name for that variable, and    *)
(* reverses to a list; clear() drops the locals                            *)
(* (of a generator's frame, once the generator finishes), finalizes a      *)
(* generator that has not started, and raises RuntimeError for an          *)
(* executing or suspended frame.                                           *)
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
(* next ("gennew"), after one next ("gensusp"), after exhaustion          *)
(* ("gendone"), or after one next and dropping the generator, which closes *)
(* it while the frame lives on ("gendropped"), also once its local b holds *)
(* the generator itself, which a collection then closes ("genself"), then  *)
(* reads an attribute or does an operation. The outcome is the result or   *)
(* the exception.                                                          *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Sources == {"running", "finished", "gennew", "gensusp", "gendone", "gendropped", "genself"}
Ops == {"f_code", "repr", "f_back", "f_locals", "f_globals", "f_builtins", "f_lasti", "f_generator", "f_lineno", "f_trace",
        "settrace", "setlines", "setbadlines", "setlineno", "setcode", "clear",
        "dellineno", "dellines", "delopcodes", "impostor", "unhashable", "reversed"}
Programs == [source : Sources, op : Ops]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Generator(s) == s \in {"gennew", "gensusp", "gendone", "gendropped", "genself"}

Locals(s) == CASE s \in {"running", "finished"} -> "['a', 'b', 'fr']" [] s = "gennew" -> "['a']" [] OTHER -> "['a', 'b']"
Line(s) == CASE s \in {"running", "finished"} -> "9" [] s = "gennew" -> "10" [] s \in {"gensusp", "gendropped", "genself"} -> "12" [] OTHER -> "13"

Run(p) ==
    LET s == p.source IN
    CASE p.op = "f_code" -> IF Generator(s) THEN "gen" ELSE "work"
      [] p.op = "repr" -> IF Generator(s) THEN "line " \o Line(s) \o ", code gen>" ELSE "line " \o Line(s) \o ", code work>"
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
      [] p.op \in {"dellineno", "delopcodes"} -> "AttributeError"
      [] p.op = "dellines" -> "TypeError"
      \* An object equal to "b", with its hash, writes the variable b.
      [] p.op = "impostor" -> "5"
      [] p.op = "unhashable" -> "TypeError"
      [] p.op = "reversed" -> "list"
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

\* A locals proxy hashes every key before it looks for the variable.
KeysHashed == Done /\ program.op = "unhashable" => outcome = "TypeError"

\* A frame that outlives its generator names no generator.
OutlivesGenerator == Done /\ program.op = "f_generator" /\ program.source \in {"gendropped", "genself"} => outcome = "None"
=============================================================================
