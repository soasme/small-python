------------------------------ MODULE Generics ------------------------------
(***************************************************************************)
(* Type parameter lists, as The Python Language Reference specifies them   *)
(* (reference/compound_stmts.html#type-parameter-lists and                 *)
(* reference/executionmodel.html#annotation-scopes): T, *Ts, and **P make  *)
(* a TypeVar, a TypeVarTuple, and a ParamSpec, each inferring its          *)
(* variance; a bound, constraints, or default is evaluated lazily, when    *)
(* first read, so a name still unbound raises NameError then; the          *)
(* parameters are visible in the annotations, body, and methods of the     *)
(* definition, through an annotation scope in which a class body's own     *)
(* names come first, but not outside it; a duplicate parameter or a        *)
(* parameter without a default after one with a default is a syntax        *)
(* error; and a generic class gets Generic as a base and can be            *)
(* subscripted.                                                            *)
(*                                                                         *)
(* A parameter program defines a function, class, or type alias with one   *)
(* parameter: T, T: int, T: (str, bytes), T = int, *T, or **T; and reads   *)
(* its type, __bound__, __constraints__, __default__, or                   *)
(* __infer_variance__. A lazy program declares T: X, T: (X, X), or T = X   *)
(* with X bound after the definition or never, and reads the attribute.    *)
(* A visibility program reads T from an annotation, the body, a method,    *)
(* a class annotation after the body binds T = 5, or outside the           *)
(* definition. A syntax program compiles a duplicate, misordered, or valid *)
(* list. A class program reads a generic class's __bases__ or              *)
(* __orig_bases__ or subscripts it with int. The outcome is the result or  *)
(* the exception.                                                          *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Params == {"plain", "bound", "constraints", "default", "tuple", "spec"}
Programs == [part : {"param"}, kind : {"function", "class", "alias"}, param : Params,
             query : {"type", "bound", "constraints", "default", "infer"}]
            \cup [part : {"lazy"}, what : {"bound", "constraints", "default"}, defined : BOOLEAN]
            \cup [part : {"visible"}, where : {"annotation", "body", "method", "shadow", "outside"}]
            \cup [part : {"syntax"}, case : {"duplicate", "order", "ok"}]
            \cup [part : {"class"}, query : {"bases", "orig", "subscript"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

TypeOf(param) == CASE param = "tuple" -> "TypeVarTuple" [] param = "spec" -> "ParamSpec" [] OTHER -> "TypeVar"

Param(p) ==
    CASE p.query = "type" -> TypeOf(p.param)
      [] p.query = "bound" -> IF p.param = "bound" THEN "int" ELSE "None"
      [] p.query = "constraints" -> CASE p.param = "constraints" -> "(str, bytes)"
                                      [] TypeOf(p.param) = "TypeVar" -> "()"
                                      [] OTHER -> "AttributeError"
      [] p.query = "default" -> IF p.param = "default" THEN "int" ELSE "NoDefault"
      [] p.query = "infer" -> "True"

Lazy(p) == IF ~p.defined THEN "NameError" ELSE CASE p.what = "constraints" -> "(int, int)" [] OTHER -> "int"

Visible(p) == CASE p.where = "shadow" -> "5" [] p.where = "outside" -> "NameError" [] OTHER -> "T"

Class(p) == CASE p.query = "bases" -> "(Generic,)" [] p.query = "orig" -> "(Generic[T],)" [] p.query = "subscript" -> "C[int]"

Run(p) == CASE p.part = "param" -> Param(p)
            [] p.part = "lazy" -> Lazy(p)
            [] p.part = "visible" -> Visible(p)
            [] p.part = "syntax" -> IF p.case = "ok" THEN "ok" ELSE "SyntaxError"
            [] p.part = "class" -> Class(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The kind of definition never changes what a parameter is.
KindIndependent == Done /\ program.part = "param" => outcome = Param([program EXCEPT !.kind = "function"])
=============================================================================
