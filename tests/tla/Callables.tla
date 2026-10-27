------------------------------ MODULE Callables ------------------------------
(***************************************************************************)
(* Classes and class instances as callables, as The Python Language        *)
(* Reference specifies them (reference/datamodel.html#classes, #class-     *)
(* instances, and #object.__new__, #object.__init__, #object.__call__):    *)
(* calling a class passes the arguments to __new__ and, when it returns an *)
(* instance of the class, to __init__, which must return None; extra       *)
(* arguments are an error unless __new__ or __init__ is overridden; an     *)
(* instance is callable when its class defines __call__ (looked up on the  *)
(* type, so one set on the instance does not count).                       *)
(*                                                                         *)
(* A program defines class C with                                          *)
(*                                                                         *)
(*     new   none | self (super().__new__(cls)) | other (returns 5)        *)
(*     init  none | records (self.args = args) | returns (returns 1)       *)
(*     call  none | class (def __call__(self, *a): return a)               *)
(*                | instance (c.__call__ = a function, after creation)     *)
(*                                                                         *)
(* where __new__ and __init__ take *args, then evaluates C(), C(1), or     *)
(* C()(2). The outcome is the result (its type, and args if recorded), or  *)
(* the exception.                                                          *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [new : {"none", "self", "other"}, init : {"none", "records", "returns"},
             call : {"none", "class", "instance"}, op : {"C()", "C(1)", "C()(2)"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* Creating the object: what C(args) gives.
Create(p, args) ==
    CASE args = "(1,)" /\ p.new = "none" /\ p.init = "none" -> "TypeError"      \* C() takes no arguments
      [] p.new = "other" -> "int 5"                                              \* __init__ is not called
      [] p.init = "returns" -> "TypeError"                                       \* __init__ should return None
      [] p.init = "records" -> "C args=" \o args
      [] OTHER -> "C"

Run(p) ==
    CASE p.op = "C()" -> Create(p, "()")
      [] p.op = "C(1)" -> Create(p, "(1,)")
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
=============================================================================
