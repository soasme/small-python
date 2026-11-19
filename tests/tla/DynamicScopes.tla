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
(* bound so far in the body. A locals mapping's own __getitem__ loads     *)
(* exec()'s names, a KeyError falling back to the globals; past its        *)
(* locals, a module or class body reads globals that are a dict subclass   *)
(* by their storage, while a function calls their __getitem__.             *)
(*                                                                         *)
(* A program runs one of these in a function with local x = 1 (or in a     *)
(* class body with a = 1): exec("x = 2") then x; exec("y = 3") then        *)
(* locals().get("y"); exec("y = 3", globals(), ns) then ns; eval("x + 1"); *)
(* an inner function's eval("x") with and without its own reference to x;  *)
(* d = locals(), d["x"] = 5, then x and locals()["x"]; l = locals(),       *)
(* x = 2, then l["x"]; sys._getframe().f_locals["x"] = 10 then x;          *)
(* eval("q", {"q": 2}, {"q": 3}); the class body's eval("a + 1"); or      *)
(* exec("r = q", {"q": 2}, m) then m["r"] for m a mapping whose Python     *)
(* __getitem__ has q = 3, has no q, or raises LookupError; or exec("for i  *)
(* in (1, 2): pass\nfor i in (x for x in (3,)): pass\nk = j = 0\ndel k,    *)
(* j", {}, m) for m a mapping whose Python __setitem__ and __delitem__ log *)
(* each binding, in order; or exec("r = (q, z, len('ab'))\nclass C:\n    *)
(* w = q\ns = C.w\ndef f(): return q\nt = f()", g) for g a dict subclass  *)
(* with q = 2 and z = 4 whose __getitem__ logs each key and raises         *)
(* KeyError for z, then r, s, t and the log. The outcome is the result or  *)
(* the exception.                                                          *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Cases == {"exec_rebind", "exec_new", "exec_mapping", "eval_local", "eval_free", "eval_free_referenced",
          "locals_write", "locals_snapshot", "frame_locals", "eval_mappings", "class_eval", "exec_custom_hit",
          "exec_custom_miss", "exec_custom_error", "exec_custom_loop", "exec_globals_storage"}
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
            [] p.case = "exec_custom_hit" -> "3"
            [] p.case = "exec_custom_miss" -> "2"            \* the KeyError falls back to the globals
            [] p.case = "exec_custom_error" -> "LookupError"
            [] p.case = "exec_custom_loop" ->
                 "[('set', 'i', 1), ('set', 'i', 2), ('set', 'i', 3), ('set', 'k', 0), ('set', 'j', 0), ('del', 'k'), ('del', 'j')]"
            \* The module body's misses (z, len) and the class body read the storage.
            [] p.case = "exec_globals_storage" -> "((2, 4, 2), 2, 2, ['q', 'z', 'len', 'C', 'f', 'q'])"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Only a frame's f_locals changes a local variable from outside the code.
LocalsProtected == Done /\ program.case \in {"exec_rebind", "locals_write", "locals_snapshot"} =>
    outcome \in {"1", "(1, 1)"}

\* A locals mapping is searched before the globals, by its own __getitem__.
LocalsFirst == Done /\ program.case \in {"eval_mappings", "exec_custom_hit"} => outcome = "3"

\* A body's lookup past its locals never calls the globals' __getitem__ again.
StorageAfterLocals == Done /\ program.case = "exec_globals_storage" => outcome = Run(program)
=============================================================================
