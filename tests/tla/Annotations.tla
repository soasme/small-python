---------------------------- MODULE Annotations ----------------------------
(***************************************************************************)
(* Annotations, as The Python Language Reference specifies them            *)
(* (reference/compound_stmts.html#annotations, reference/datamodel.html#   *)
(* annotations, reference/executionmodel.html#annotation-scopes, and       *)
(* reference/simple_stmts.html#annotated-assignment-statements):           *)
(* annotations of functions and classes are evaluated lazily, in an        *)
(* annotation scope, by the object's __annotate__ function when            *)
(* __annotations__ is first read (and the result is kept); __annotate__    *)
(* takes a format, supports VALUE (1), and raises NotImplementedError for  *)
(* FORWARDREF (3); a name that is still unbound raises NameError then, not *)
(* at definition; string annotations stay strings; annotations of local    *)
(* variables are never evaluated, and an annotation without a value binds  *)
(* nothing; class-scope names and enclosing locals are visible to the      *)
(* annotation scope; and __annotations__ and __annotate__ replace each     *)
(* other when assigned, while __annotate__ must be callable or None and    *)
(* cannot be deleted.                                                      *)
(*                                                                         *)
(* An evaluation program annotates a function parameter x, or a class      *)
(* attribute x with or without a value, or a local x with or without a     *)
(* value, by ANN: a name T bound after the definition, a name never bound, *)
(* or the string "T"; then reads __annotations__, calls __annotate__(1) or *)
(* __annotate__(3), reads the class attribute, or returns the local. A     *)
(* lazy program counts the evaluations after 0, 1, or 2 reads. A scope     *)
(* program annotates with a class-body name or an enclosing function's     *)
(* local. A replacement program assigns a function's or class's            *)
(* __annotations__ or __annotate__ (a function, or 5) or deletes           *)
(* __annotate__. The outcome is the annotations, value, or exception.      *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Anns == {"later", "never", "string"}
Programs == [part : {"function"}, ann : Anns, op : {"annotations", "format1", "format3"}]
            \cup [part : {"class"}, ann : Anns, value : BOOLEAN, op : {"annotations", "attr"}]
            \cup [part : {"local"}, ann : Anns, value : BOOLEAN]
            \cup [part : {"lazy"}, reads : 0..2]
            \cup [part : {"scope"}, where : {"class", "closure"}]
            \cup [part : {"replace"}, target : {"function", "class"}, op : {"annotations", "annotate", "bad", "delete"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* The annotations dict, rendered as name=value.
Evaluate(ann) == CASE ann = "later" -> "x=str" [] ann = "never" -> "NameError" [] ann = "string" -> "x='T'"

Run(p) ==
    CASE p.part = "function" -> IF p.op = "format3" THEN "NotImplementedError" ELSE Evaluate(p.ann)
      [] p.part = "class" -> IF p.op = "attr" THEN (IF p.value THEN "1" ELSE "AttributeError") ELSE Evaluate(p.ann)
      [] p.part = "local" -> IF p.value THEN "1" ELSE "UnboundLocalError"
      [] p.part = "lazy" -> IF p.reads = 0 THEN "0" ELSE "1"
      [] p.part = "scope" -> IF p.where = "class" THEN "x=int" ELSE "x=float"
      [] p.part = "replace" -> CASE p.op = "annotations" -> "None"          \* __annotate__ is dropped
                                 [] p.op = "annotate" -> "w=2"              \* the new function answers
                                 [] OTHER -> "TypeError"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Defining never evaluates an annotation, so it never fails for one.
DefinitionNeverFails == Done /\ program.part \in {"local", "class"} /\ (program.part = "local" \/ program.op = "attr") =>
    outcome # "NameError"

\* Annotations are evaluated at most once.
AtMostOnce == Done /\ program.part = "lazy" => outcome \in {"0", "1"}
=============================================================================
