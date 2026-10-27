---------------------------- MODULE CodeObjects ----------------------------
(***************************************************************************)
(* Code objects, as The Python Language Reference specifies them           *)
(* (reference/datamodel.html#code-objects, their special read-only         *)
(* attributes, and methods): a function's code carries its name, qualified *)
(* name, parameter counts, local names (parameters first), cell and free   *)
(* variables, the global and attribute names it uses (not free ones), its  *)
(* first line, and flags for *args (0x04), **kwargs (0x08), nesting        *)
(* (0x10), generators (0x20), coroutines (0x80), asynchronous generators   *)
(* (0x200), and a docstring (0x4000000, with the docstring first in        *)
(* co_consts); code objects are immutable, co_lines() ranges are           *)
(* consecutive from 0 to the end of co_code, co_positions() gives 4-tuples, *)
(* and replace() returns a changed copy.                                   *)
(*                                                                         *)
(* A program, after  v = 1  on line 1, defines f on line 2, or inside      *)
(*  def outer(): v = 1  on line 4 (then returns it), as                    *)
(*                                                                         *)
(*     [async] def f(SIG):                                                 *)
(*         "doc"                          (optionally)                     *)
(*         x = 1; g = lambda: x           (closure "cell")                 *)
(*         return|yield (len.__name__, v) (v only for closure "free")      *)
(*                                                                         *)
(* with SIG one of  ""  "a, /, b"  "a, *args"  "*, k, **kw"                *)
(* "a=1, *args, k, **kw", then reads one attribute of f.__code__ or does   *)
(* one operation on it. The outcome is the repr of the result (names       *)
(* sorted, flags masked to the bits above), or the exception.              *)
(***************************************************************************)
EXTENDS Naturals, Sequences, TLC

Sigs == {
    [text |-> "", argc |-> 0, posonly |-> 0, kwonly |-> 0, names |-> <<>>, varargs |-> FALSE, kwargs |-> FALSE],
    [text |-> "a, /, b", argc |-> 2, posonly |-> 1, kwonly |-> 0, names |-> <<"a", "b">>, varargs |-> FALSE, kwargs |-> FALSE],
    [text |-> "a, *args", argc |-> 1, posonly |-> 0, kwonly |-> 0, names |-> <<"a">>, varargs |-> TRUE, kwargs |-> FALSE],
    [text |-> "*, k, **kw", argc |-> 0, posonly |-> 0, kwonly |-> 1, names |-> <<"k">>, varargs |-> FALSE, kwargs |-> TRUE],
    [text |-> "a=1, *args, k, **kw", argc |-> 1, posonly |-> 0, kwonly |-> 1, names |-> <<"a", "k">>, varargs |-> TRUE,
     kwargs |-> TRUE]}
Kinds == {"def", "gen", "async", "asyncgen"}
Closures == {"none", "cell", "free"}
Reads == {"co_name", "co_qualname", "co_argcount", "co_posonlyargcount", "co_kwonlyargcount", "co_nlocals", "co_varnames",
          "co_cellvars", "co_freevars", "co_names", "co_flags", "co_firstlineno"}
Ops == {"doc", "replace", "copy", "setattr", "badkw", "lines", "positions"}
Programs == [sig : Sigs, kind : Kinds, doc : BOOLEAN, closure : Closures, nested : BOOLEAN, op : {"read"}, attr : Reads]
            \cup [sig : Sigs, kind : Kinds, doc : BOOLEAN, closure : Closures, nested : BOOLEAN, op : Ops]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

RECURSIVE Join(_)
Join(s) == CASE s = <<>> -> "" [] Len(s) = 1 -> "'" \o s[1] \o "'" [] OTHER -> "'" \o s[1] \o "', " \o Join(Tail(s))
Repr(s) == IF Len(s) = 1 THEN "(" \o Join(s) \o ",)" ELSE "(" \o Join(s) \o ")"

\* Parameters by name, then *args and **kw, then the locals that are not cells.
Varnames(p) == p.sig.names \o (IF p.sig.varargs THEN <<"args">> ELSE <<>>) \o (IF p.sig.kwargs THEN <<"kw">> ELSE <<>>)
               \o (IF p.closure = "cell" THEN <<"g">> ELSE <<>>)
\* Global and attribute names, sorted: v is a name only when it is not free.
Names(p) == <<"__name__", "len">> \o (IF p.closure = "free" /\ ~p.nested THEN <<"v">> ELSE <<>>)
Flags(p) == (IF p.sig.varargs THEN 4 ELSE 0) + (IF p.sig.kwargs THEN 8 ELSE 0) + (IF p.nested THEN 16 ELSE 0)
            + (CASE p.kind = "gen" -> 32 [] p.kind = "async" -> 128 [] p.kind = "asyncgen" -> 512 [] OTHER -> 0)
            + (IF p.doc THEN 67108864 ELSE 0)

Read(p, a) ==
    CASE a = "co_name" -> "'f'"
      [] a = "co_qualname" -> IF p.nested THEN "'outer.<locals>.f'" ELSE "'f'"
      [] a = "co_argcount" -> ToString(p.sig.argc)
      [] a = "co_posonlyargcount" -> ToString(p.sig.posonly)
      [] a = "co_kwonlyargcount" -> ToString(p.sig.kwonly)
      [] a = "co_nlocals" -> ToString(Len(Varnames(p)))
      [] a = "co_varnames" -> Repr(Varnames(p))
      [] a = "co_cellvars" -> IF p.closure = "cell" THEN "('x',)" ELSE "()"
      [] a = "co_freevars" -> IF p.closure = "free" /\ p.nested THEN "('v',)" ELSE "()"
      [] a = "co_names" -> Repr(Names(p))
      [] a = "co_flags" -> ToString(Flags(p))
      [] a = "co_firstlineno" -> IF p.nested THEN "4" ELSE "2"

Run(p) ==
    IF p.op = "read" THEN Read(p, p.attr)
    ELSE CASE p.op = "doc" -> IF p.doc THEN "'doc'" ELSE "no docstring"
           [] p.op = "replace" -> "z 9 f False"      \* replace(co_name="z", co_firstlineno=9): a changed copy
           [] p.op = "copy" -> "True"                \* replace() is equal, with an equal hash
           [] p.op = "setattr" -> "AttributeError"   \* immutable
           [] p.op = "badkw" -> "TypeError"
           [] p.op \in {"lines", "positions"} -> "ok"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* co_varnames starts with the parameter names.
ParamsFirst == Done => SubSeq(Varnames(program), 1, Len(program.sig.names)) = program.sig.names

\* A name is either free or global, never both.
FreeNotGlobal == Done => ~(program.closure = "free" /\ program.nested /\ \E i \in DOMAIN Names(program) : Names(program)[i] = "v")

\* The docstring flag is set exactly when co_consts starts with the docstring.
DocFlag == Done /\ program.op = "doc" => ((outcome = "'doc'") = (Flags(program) >= 67108864))
=============================================================================
