--------------------------- MODULE DynamicScopes ---------------------------
(***************************************************************************)
(* Interaction with dynamic features, as The Python Language Reference     *)
(* specifies it (reference/executionmodel.html#interaction-with-dynamic-   *)
(* features, with the locals() and exec() semantics of PEP 667): eval()    *)
(* and exec() run in the caller's globals and a snapshot of its locals     *)
(* unless given mappings (the locals mapping is searched first); names     *)
(* are resolved in the code being run, so a variable of an enclosing       *)
(* function is visible to eval() only if the calling function itself       *)
(* refers to it; exec() cannot rebind or add a function's local variables, *)
(* and a function's locals() is an independent snapshot, while a frame's   *)
(* f_locals writes through; and a class body's eval() sees the names       *)
(* bound so far in the body.                                               *)
(*                                                                         *)
(* A program runs one of these in a function with local x = 1 (or in a     *)
(* class body with a = 1): exec("x = 2") then x; exec("y = 3") then        *)
(* locals().get("y"); exec("y = 3", globals(), ns) then ns; eval("x + 1"); *)
(* an inner function's eval("x") with and without its own reference to x;  *)
(* d = locals(), d["x"] = 5, then x and locals()["x"]; l = locals(),       *)
(* x = 2, then l["x"]; sys._getframe().f_locals["x"] = 10 then x;          *)
(* eval("q", {"q": 2}, {"q": 3}); or the class body's eval("a + 1"). The   *)
(* outcome is the result or the exception.                                 *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Cases == {"exec_rebind", "exec_new", "exec_mapping", "eval_local", "eval_free", "eval_free_referenced",
          "locals_write", "locals_snapshot", "frame_locals", "eval_mappings", "class_eval"}
Programs == [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Run(p) == CASE p.case = "exec_rebind" -> "1"                   \* the snapshot changes, not x
            [] p.case = "exec_new" -> "None"
            [] p.case = "exec_mapping" -> "{'y': 3}"
            [] p.case = "eval_local" -> "2"
            [] p.case = "eval_free" -> "NameError"            \* x is not a free variable of the caller
            [] p.case = "eval_free_referenced" -> "1"
            [] p.case = "locals_write" -> "(1, 1)"
            [] p.case = "locals_snapshot" -> "1"
            [] p.case = "frame_locals" -> "10"                 \* f_locals writes through
            [] p.case = "eval_mappings" -> "3"
            [] p.case = "class_eval" -> "2"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Only a frame's f_locals changes a local variable from outside the code.
LocalsProtected == Done /\ program.case \in {"exec_rebind", "locals_write", "locals_snapshot"} =>
    outcome \in {"1", "(1, 1)"}
=============================================================================
