------------------------------ MODULE Callables ------------------------------
(***************************************************************************)
(* Classes and class instances as callables, as The Python Language        *)
(* Reference specifies them (reference/datamodel.html#classes, #class-     *)
(* instances, and #object.__new__, #object.__init__, #object.__call__):    *)
(* calling a class passes the arguments to __new__ and, when it returns an *)
(* instance of the class, to __init__, which must return None; extra       *)
(* arguments are an error unless __new__ or __init__ is overridden; an     *)
(* instance is callable when its class defines __call__ (looked up on the  *)
(* type, so one set on the instance does not count); a metaclass's         *)
(* __call__ replaces all of creation, and its super().__call__, or         *)
(* type.__call__ given the class, is the creation itself.                  *)
(*                                                                         *)
(* A program defines class C, of base object, list or Exception, with      *)
(*                                                                         *)
(*     new   none | self (super().__new__(cls)) | other (returns 5)        *)
(*           | classmethod (one doing the same, the class bound first)     *)
(*           | descriptor (an instance whose Python __get__ gives one)     *)
(*     init  none | records (self.args = args) | returns (returns 1)       *)
(*           | descriptor (an instance whose Python __get__ gives a        *)
(*             function recording them so)                                 *)
(*     call  none | class (def __call__(self, *a): return a)               *)
(*                | instance (c.__call__ = a function, after creation)     *)
(*                | meta (a metaclass's def __call__(cls, *a): return a)   *)
(*                | super (a metaclass's __call__ returning                *)
(*                         super().__call__ of its arguments)              *)
(*                | unbound (one returning type.__call__(cls, *a, **k))    *)
(*                                                                         *)
(* where __new__ and __init__ take *args and **kw (recording args and the  *)
(* keyword items), then evaluates C(), C(1), C(k=1), or C()(2). The        *)
(* outcome is the result (its type, and args if recorded or an             *)
(* exception's), or the exception. A builtin base's __new__ makes the      *)
(* instance: list's then initializes from an iterable, and                 *)
(* BaseException's keeps the arguments as args.                            *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [base : {"object", "list", "Exception"}, new : {"none", "self", "other", "classmethod", "descriptor"},
             init : {"none", "records", "returns", "descriptor"}, call : {"none", "class", "instance", "meta", "super", "unbound"},
             op : {"C()", "C(1)", "C(k=1)", "C()(2)"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* Creating the object: what C(args) gives.
Create(p, args) ==
    CASE p.new = "other" -> "int 5"                                              \* __init__ is not called
      [] p.init = "returns" -> "TypeError"                                       \* __init__ should return None
      \* BaseException's __init__ takes no keywords, nor list's unless __new__ is overridden.
      [] args = "(('k', 1),)" /\ p.init = "none" /\ (p.new = "none" \/ p.base = "Exception") -> "TypeError"
      [] p.init \in {"records", "descriptor"} \/ p.base = "Exception" -> "C args=" \o args
      [] args = "(1,)" /\ (p.new = "none" \/ p.base = "list") -> "TypeError"    \* C() takes no arguments; list(1)
      [] OTHER -> "C"

Run(p) ==
    CASE p.call = "meta" -> CASE p.op = "C()" -> "tuple ()" [] p.op = "C(1)" -> "tuple (1,)"
                                 [] OTHER -> "TypeError"                         \* no keywords; a tuple is not callable
      [] p.op = "C()" -> Create(p, "()")
      [] p.op = "C(1)" -> Create(p, "(1,)")
      [] p.op = "C(k=1)" -> Create(p, "(('k', 1),)")
      [] Create(p, "()") \in {"TypeError", "int 5"} -> "TypeError"               \* an int is not callable
      [] p.call = "class" -> "(2,)"
      [] OTHER -> "TypeError"                                                    \* 'C' object is not callable

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A __call__ on the instance never makes it callable.
TypeLookup == Done /\ program.op = "C()(2)" /\ program.call = "instance" => outcome = "TypeError"
\* A metaclass's super().__call__ creates the instance as a plain call does.
SuperCreates == Done /\ program.call = "super" => outcome = Run([program EXCEPT !.call = "none"])
\* So does type.__call__ called unbound with the class.
UnboundCreates == Done /\ program.call = "unbound" => outcome = Run([program EXCEPT !.call = "none"])
=============================================================================
