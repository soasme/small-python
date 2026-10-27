-------------------------- MODULE MethodDescriptors --------------------------
(***************************************************************************)
(* Static method and class method objects, as The Python Language          *)
(* Reference specifies them (reference/datamodel.html#static-method-       *)
(* objects and #class-method-objects): a static method object wraps any    *)
(* object, which retrieval from a class or instance returns untransformed, *)
(* and is itself callable; a class method object wraps any object, which   *)
(* retrieval binds to the class (the instance's class, or the subclass it  *)
(* was retrieved through), and is not callable itself; both expose the     *)
(* wrapped object as __func__ and __wrapped__ and copy its name.           *)
(*                                                                         *)
(* A program defines  def f( *a): return a,  then                          *)
(*                                                                         *)
(*     class C: x = WRAP(TARGET)        class D(C): pass                   *)
(*                                                                         *)
(* with WRAP staticmethod or classmethod and TARGET f, abs, or 5, and      *)
(* takes C.x, C().x, D.x, D().x, or the wrapper itself (C.__dict__["x"]);  *)
(* it gives the type of what it took or calls it with -1, or (for the      *)
(* wrapper) reads __func__, __wrapped__, or __name__. The outcome is the   *)
(* result (classes by name) or the exception.                              *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Wraps == {"static", "class"}
Targets == {"f", "abs", "5"}
Accesses == {"C", "C()", "D", "D()", "raw"}
Programs == [wrap : Wraps, target : Targets, access : Accesses, op : {"type", "call"}]
            \cup [wrap : Wraps, target : Targets, access : {"raw"}, op : {"func", "wrapped", "name"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* The class retrieval binds a class method to.
Owner(a) == IF a \in {"C", "C()"} THEN "C" ELSE "D"

\* What the target does when called with these arguments.
Call(t, args) == CASE t = "f" -> "(" \o args \o (IF args = "-1" THEN ",)" ELSE ")")
                   [] t = "abs" /\ args = "-1" -> "1"
                   [] OTHER -> "TypeError"            \* abs(C, -1), or calling 5

Run(p) ==
    LET t == p.target IN
    CASE p.op = "func" \/ p.op = "wrapped" -> "the target"
      [] p.op = "name" -> IF t = "5" THEN "AttributeError" ELSE "'" \o t \o "'"
      [] p.access = "raw" -> IF p.op = "type" THEN (IF p.wrap = "static" THEN "staticmethod" ELSE "classmethod")
                             ELSE IF p.wrap = "static" THEN Call(t, "-1") ELSE "TypeError"     \* not callable
      [] p.wrap = "static" -> IF p.op = "type" THEN (CASE t = "f" -> "function" [] t = "abs" -> "builtin_function_or_method"
                                                         [] OTHER -> "int")
                              ELSE Call(t, "-1")
      [] OTHER -> IF p.op = "type" THEN "method" ELSE Call(t, Owner(p.access) \o ", -1")

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Retrieval never transforms what a static method wraps: calling it is calling the target.
StaticUntransformed == Done /\ program.wrap = "static" /\ program.op = "call" => outcome = Call(program.target, "-1")

\* A class method is always bound, so its target gets the class first.
ClassBound == Done /\ program.wrap = "class" /\ program.access # "raw" /\ program.op = "type" => outcome = "method"
=============================================================================
