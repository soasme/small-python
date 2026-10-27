-------------------------- MODULE BuiltinsCompile ---------------------------
(***************************************************************************)
(* The compilation built-in functions, as The Python Standard Library      *)
(* specifies them (library/functions.html): compile() in exec, eval, or    *)
(* single mode with flags, dont_inherit, and optimize; eval() of an        *)
(* expression string, bytes, or code object, and exec() of statements or a *)
(* code object (with a closure for free variables), both in the caller's   *)
(* namespaces by default or in a globals dict (gaining __builtins__) and   *)
(* any locals mapping; names load from the locals, then the globals, then  *)
(* the builtins, a function made there seeing only the globals and         *)
(* builtins, store and delete in the locals, and global statements reach   *)
(* the globals; globals() is the module namespace and locals() a snapshot  *)
(* in a function; and __import__() with level and its errors.              *)
(*                                                                         *)
(* A program runs one of OPS with exec() in a globals dict g and a locals  *)
(* dict l (or with g alone): r = x; x = 5 then r = x; global x, x = 5,     *)
(* then r = x; del x; or r = f() for f returning x. Before it, x is 2 in   *)
(* l, 1 in g, or 3 in g's __builtins__, in any combination. The program    *)
(* reports r (or the NameError), and x in g and in l afterwards; or runs   *)
(* one of the sources of CASES in a fresh namespace. The outcome is the    *)
(* repr of that tuple or of the case's result, or the exception and its    *)
(* message.                                                                *)
(***************************************************************************)
EXTENDS Sequences

VARIABLES program, outcome
vars == <<program, outcome>>

Ops == {"lookup", "store", "global_store", "delete", "function"}
Missing == "\"NameError: name 'x' is not defined\""
Opt(b, v) == IF b THEN v ELSE "None"
Show(r, g, l) == "(" \o r \o ", " \o g \o ", " \o l \o ")"


Cases == {"eval_expression_only", "eval_code_object", "exec_returns_none", "eval_strips", "eval_bytes",
          "eval_bad_type", "eval_globals_type", "eval_locals_mapping", "eval_locals_keyword",
          "exec_closure", "exec_closure_mismatch", "builtins_injected", "compile_modes", "compile_bad_mode",
          "compile_single_multi", "compile_eval_statement", "compile_filename", "compile_null",
          "compile_dont_inherit", "compile_bad_flags", "compile_optimize", "compile_optimize0",
          "compile_syntax_error", "single_prints_repr", "globals_is_namespace", "locals_snapshot",
          "locals_write_ignored", "locals_module_is_globals", "import_builtin", "import_missing",
          "import_level_bad", "import_empty", "import_relative_no_package", "eval_nested_scope",
          "eval_free_var_missing"}
Programs == {p \in [op : Ops, inl : BOOLEAN, ing : BOOLEAN, inb : BOOLEAN, same : BOOLEAN] : ~(p.same /\ p.inl)}
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    LET local == ~p.same /\ p.inl
        g == Opt(p.ing, "1")  l == IF p.same THEN "None" ELSE Opt(p.inl, "2")
        \* Loading looks in the locals, the globals, then the builtins.
        load == IF local THEN "2" ELSE IF p.ing THEN "1" ELSE IF p.inb THEN "3" ELSE Missing
    IN
    CASE p.op = "lookup" -> Show(load, g, l)
      [] p.op = "store" -> IF p.same THEN Show("5", "5", "None") ELSE Show("5", g, "5")
      [] p.op = "global_store" -> Show("5", "5", l)
      \* Deleting looks only in the locals (the globals when they are the same).
      [] p.op = "delete" -> IF p.same THEN (IF p.ing THEN Show("'deleted'", "None", "None") ELSE Show(Missing, "None", "None"))
                            ELSE IF p.inl THEN Show("'deleted'", g, "None") ELSE Show(Missing, g, "None")
      \* A function's free name skips the exec locals.
      [] p.op = "function" -> Show(IF p.ing THEN "1" ELSE IF p.inb THEN "3" ELSE Missing, g, l)

Case(c) ==
    CASE c = "eval_expression_only" -> "SyntaxError: invalid syntax"
      [] c = "eval_code_object" -> "(3, None)"
      [] c = "exec_returns_none" -> "None"
      [] c = "eval_strips" -> "2"
      [] c = "eval_bytes" -> "6"
      [] c = "eval_bad_type" -> "TypeError: eval() arg 1 must be a string, bytes or code object"
      [] c = "eval_globals_type" -> "TypeError: globals must be a real dict or a frozendict; try eval(expr, {}, mapping)"
      [] c = "eval_locals_mapping" -> "'abab'"
      [] c = "eval_locals_keyword" -> "7"
      [] c = "exec_closure" -> "None"
      [] c = "exec_closure_mismatch" -> "TypeError: code object requires a closure of exactly length 1"
      [] c = "builtins_injected" -> "(True, True)"
      [] c = "compile_modes" -> "['code', 'code', 'code']"
      [] c = "compile_bad_mode" -> "ValueError: compile() mode must be 'exec', 'eval' or 'single'"
      [] c = "compile_single_multi" -> "SyntaxError: multiple statements found while compiling a single statement"
      [] c = "compile_eval_statement" -> "SyntaxError: invalid syntax"
      [] c = "compile_filename" -> "'file.py'"
      [] c = "compile_null" -> "SyntaxError: source code string cannot contain null bytes"
      [] c = "compile_dont_inherit" -> "'code'"
      [] c = "compile_bad_flags" -> "ValueError: compile(): unrecognised flags"
      [] c = "compile_optimize" -> "'skipped'"
      [] c = "compile_optimize0" -> "AssertionError: 1"
      [] c = "compile_syntax_error" -> "('f.py', 1, 'SyntaxError')"
      [] c = "single_prints_repr" -> "'single'"
      [] c = "globals_is_namespace" -> "'ok'"
      [] c = "locals_snapshot" -> "(1, 2)"
      [] c = "locals_write_ignored" -> "1"
      [] c = "locals_module_is_globals" -> "True"
      [] c = "import_builtin" -> "'sys'"
      [] c = "import_missing" -> "ModuleNotFoundError: No module named 'nosuchmodule_xyz'"
      [] c = "import_level_bad" -> "ValueError: level must be >= 0"
      [] c = "import_empty" -> "ValueError: Empty module name"
      [] c = "import_relative_no_package" -> "KeyError: \"'__name__' not in globals\""
      [] c = "eval_nested_scope" -> "'local'"
      [] c = "eval_free_var_missing" -> "NameError: name 'y' is not defined"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* A store without a global statement never touches separate globals.
LocalStores == Done /\ "op" \in DOMAIN program /\ program.op = "store" /\ ~program.same =>
    outcome = Show("5", Opt(program.ing, "1"), "5")
=============================================================================
