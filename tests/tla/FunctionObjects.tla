-------------------------- MODULE FunctionObjects --------------------------
(***************************************************************************)
(* User-defined function objects, as The Python Language Reference         *)
(* specifies them (reference/datamodel.html#user-defined-functions and its *)
(* special read-only and writable attributes): __globals__, __builtins__,  *)
(* and __closure__ (with its cells) are read-only; __doc__, __name__,      *)
(* __qualname__, __module__, __defaults__, __kwdefaults__, __code__,       *)
(* __dict__, __annotations__, and __type_params__ are writable, most of    *)
(* them checking the type of the value, and a call uses the new defaults   *)
(* or code; any other attribute is stored in __dict__.                     *)
(*                                                                         *)
(* A program defines f, in module m, with parameters                       *)
(*                                                                         *)
(*     plain  (x)     default  (x=1)     kwonly  ( *, x=1)                 *)
(*     both   (x=1, *, y=2)   generic  [T](x)                              *)
(*                                                                         *)
(* at module level, in a class C, or nested in a function g (where it      *)
(* refers to g's local v = 5), with or without a docstring and a -> int    *)
(* annotation; f returns its parameters' values. It then reads one         *)
(* attribute, or writes one and reads it back (or calls f()).              *)
(*                                                                         *)
(* The outcome is the repr of what is read or returned, or the exception.  *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Params == {"plain", "default", "kwonly", "both", "generic"}
Places == {"module", "class", "nested"}
Reads == {"__defaults__", "__kwdefaults__", "__closure__", "__doc__", "__name__", "__qualname__", "__module__",
          "__annotations__", "__annotate__", "__type_params__", "__dict__", "__globals__", "__builtins__", "call"}
Writes == {"__name__ = 'g'", "__name__ = 1", "__qualname__ = 'q'", "__qualname__ = 1", "__defaults__ = (2,)",
           "__defaults__ = 1", "__defaults__ = None", "__kwdefaults__ = {'x': 3}", "__kwdefaults__ = 1",
           "__doc__ = 1", "__module__ = 1", "__closure__ = None", "__globals__ = {}", "__builtins__ = {}",
           "__code__ = (lambda: 9).__code__", "__dict__ = 1", "__dict__ = {'y': 1}", "__annotations__ = 1",
           "__annotations__ = {'a': 1}", "__type_params__ = 1", "x = 1"}
Programs == [params : Params, place : Places, doc : BOOLEAN, annotated : BOOLEAN, op : {"read"}, attr : Reads]
            \cup [params : Params, place : Places, doc : BOOLEAN, annotated : BOOLEAN, op : {"write"}, attr : Writes]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Defaults(p) == CASE p.params \in {"default", "both"} -> "(1,)" [] OTHER -> "None"
Kwdefaults(p) == CASE p.params = "kwonly" -> "{'x': 1}" [] p.params = "both" -> "{'y': 2}" [] OTHER -> "None"
Qualname(p) == CASE p.place = "module" -> "f" [] p.place = "class" -> "C.f" [] OTHER -> "g.<locals>.f"
Annotations(p) == IF p.annotated THEN "{'return': <class 'int'>}" ELSE "{}"
\* f() with the given defaults: what it returns, or TypeError for a
\* missing argument.
Call(p, defaults, kwdefaults) ==
    CASE p.params \in {"plain", "generic"} -> IF defaults = "(2,)" THEN "2" ELSE "TypeError"
      [] p.params = "default" -> CASE defaults = "(2,)" -> "2" [] defaults = "(1,)" -> "1" [] OTHER -> "TypeError"
      [] p.params = "kwonly" -> CASE kwdefaults = "{'x': 3}" -> "3" [] kwdefaults = "{'x': 1}" -> "1" [] OTHER -> "TypeError"
      [] p.params = "both" -> LET x == CASE defaults = "(2,)" -> "2" [] defaults = "(1,)" -> "1" [] OTHER -> "missing"
                                  y == CASE kwdefaults = "{'y': 2}" -> "2" [] OTHER -> "missing"
                              IN  IF x = "missing" \/ y = "missing" THEN "TypeError" ELSE "(" \o x \o ", " \o y \o ")"

Read(p, attr) ==
    CASE attr = "__defaults__" -> Defaults(p)
      [] attr = "__kwdefaults__" -> Kwdefaults(p)
      [] attr = "__closure__" -> IF p.place = "nested" THEN "cells 5" ELSE "None"
      [] attr = "__doc__" -> IF p.doc THEN "'doc'" ELSE "None"
      [] attr = "__name__" -> "'f'"
      [] attr = "__qualname__" -> "'" \o Qualname(p) \o "'"
      [] attr = "__module__" -> "'m'"
      [] attr = "__annotations__" -> Annotations(p)
      [] attr = "__annotate__" -> IF p.annotated THEN "function" ELSE "None"
      [] attr = "__type_params__" -> IF p.params = "generic" THEN "(T,)" ELSE "()"
      [] attr = "__dict__" -> "{}"
      [] attr = "__globals__" -> "the module's globals"
      [] attr = "__builtins__" -> "dict"
      [] attr = "call" -> Call(p, Defaults(p), Kwdefaults(p))

Write(p, w) ==
    CASE w = "__name__ = 'g'" -> "'g'"
      [] w = "__qualname__ = 'q'" -> "'q'"
      [] w \in {"__name__ = 1", "__qualname__ = 1", "__defaults__ = 1", "__kwdefaults__ = 1", "__dict__ = 1",
                "__annotations__ = 1", "__type_params__ = 1"} -> "TypeError"
      [] w = "__defaults__ = (2,)" -> Call(p, "(2,)", Kwdefaults(p))
      [] w = "__defaults__ = None" -> Call(p, "None", Kwdefaults(p))
      [] w = "__kwdefaults__ = {'x': 3}" -> Call(p, Defaults(p), "{'x': 3}")
      [] w = "__doc__ = 1" -> "1"                                  \* not checked
      [] w = "__module__ = 1" -> "1"                               \* not checked
      [] w \in {"__closure__ = None", "__globals__ = {}", "__builtins__ = {}"} -> "AttributeError"
      \* The new code must have as many free variables as f has cells.
      [] w = "__code__ = (lambda: 9).__code__" -> IF p.place = "nested" THEN "ValueError" ELSE "9"
      [] w = "__dict__ = {'y': 1}" -> "1"
      [] w = "__annotations__ = {'a': 1}" -> "{'a': 1}"
      [] w = "x = 1" -> "{'x': 1}"

Run(p) == IF p.op = "read" THEN Read(p, p.attr) ELSE Write(p, p.attr)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Writing __defaults__ back changes nothing.
DefaultsRoundTrip == Done /\ program.op = "read" /\ program.attr = "call" /\ program.params = "default" =>
    outcome = Call(program, Defaults(program), Kwdefaults(program))

\* Read-only attributes cannot be written.
ReadOnly == Done /\ program.op = "write" /\ program.attr \in {"__closure__ = None", "__globals__ = {}", "__builtins__ = {}"}
            => outcome = "AttributeError"
=============================================================================
