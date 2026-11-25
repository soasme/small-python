---------------------------- MODULE LazyImports ----------------------------
(***************************************************************************)
(* Lazy imports, as The Python Language Reference specifies them (PEP 810, *)
(* reference/simple_stmts.html#lazy-imports and #lazy-modules-compat): a   *)
(* lazy import binds each name to a lazy_import placeholder without        *)
(* running or caching any module, so a missing or broken module raises     *)
(* only when used; the first use of the name in the global namespace       *)
(* reifies it, importing the module (for `lazy import a.b` only a, b being *)
(* imported when first looked up as an attribute, as sys.lazy_modules      *)
(* records) and rebinding the name; `lazy import a.b as c` binds a.b and   *)
(* `lazy from a import b` the attribute; lazy imports are allowed only at  *)
(* module level and outside try statements, never with * or __future__;    *)
(* and a module-level __lazy_modules__ makes the regular imports of the    *)
(* modules it lists (by absolute name, the module after `from` for a from  *)
(* import) lazy, except inside try statements, functions, and classes,     *)
(* read before each module through the __getitem__ of globals that are a   *)
(* dict subclass's instance.                                               *)
(*                                                                         *)
(* A program clears the fixture modules (those of Imports) from sys.modules*)
(* and sys.lazy_modules and runs one of the statements of CASES. The       *)
(* outcome is the program's result (or the exception and its message,      *)
(* without the file name) and the log of the modules that ran; for         *)
(* compat_getitem, in globals whose Python __getitem__ answers ['pkg',     *)
(* 'nosuchmod'] for __lazy_modules__, the result and how often it did.     *)
(* A __lazy_import__ in the builtins other than the original is called     *)
(* instead, at the statement; without one the statement raises.            *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Cases == {"unused", "used", "from_unused", "from_used", "placeholder", "from_placeholder", "missing_unused",
          "missing_used", "broken", "as", "not_cached", "in_function_use", "registry", "submodule",
          "in_function", "in_try", "in_class", "star", "future",
          "compat", "compat_used", "compat_other", "compat_from", "compat_try", "compat_function",
          "compat_getitem", "compat_hook", "attribute_hook", "hook_used", "hook_dotted", "method_read",
          "lazy_hook", "lazy_hook_missing", "policy"}
Programs == [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Run(p) ==
    CASE p.case = "unused" -> "'unused' []"
      [] p.case = "used" -> "'sub' ['pkg', 'sub']"
      [] p.case = "from_unused" -> "'unused' []"
      [] p.case = "from_used" -> "'sub' ['pkg', 'sub']"
      [] p.case = "placeholder" -> "'lazy_import' []"
      [] p.case = "from_placeholder" -> "'lazy_import' []"
      [] p.case = "missing_unused" -> "'unused' []"
      [] p.case = "missing_used" -> "ModuleNotFoundError: No module named 'nosuchmod' []"
      [] p.case = "broken" -> "['pkg'] ['pkg', 'broken']"                  \* reifying pkg leaves broken
      [] p.case = "as" -> "'sub' ['pkg', 'sub']"
      [] p.case = "not_cached" -> "False []"
      [] p.case = "in_function_use" -> "1 ['pkg']"
      [] p.case = "registry" -> "['pkg.inner.leaf'] []"
      [] p.case = "submodule" -> "'sub' ['pkg', 'inner', 'sub', 'leaf']"
      [] p.case = "in_function" -> "SyntaxError: lazy import not allowed inside functions []"
      [] p.case = "in_try" -> "SyntaxError: lazy import not allowed inside try/except blocks []"
      [] p.case = "in_class" -> "SyntaxError: lazy import not allowed inside classes []"
      [] p.case = "star" -> "SyntaxError: lazy from ... import * is not allowed []"
      [] p.case = "future" -> "SyntaxError: lazy from __future__ import is not allowed []"
      [] p.case = "compat" -> "'lazy_import' []"
      [] p.case = "compat_used" -> "1 ['pkg']"
      [] p.case = "compat_other" -> "'module' ['pkg']"
      [] p.case = "compat_from" -> "'lazy_import' []"
      [] p.case = "compat_try" -> "'module' ['pkg']"
      [] p.case = "compat_function" -> "'module' ['pkg']"
      [] p.case = "compat_getitem" -> "('lazy_import', 2) []"           \* read once per module
      \* a module's attribute bound lazily reifies when getattr() or str.format reads it
      [] p.case = "attribute_hook" -> "('sub', '1', ['pkg', 'pkg']) ['pkg', 'sub']"
      \* a Python __import__ hook imports an unlisted module; a listed one stays lazy
      [] p.case = "compat_hook" -> "(['other'], 'given', 'lazy_import') []"
      \* a Python __import__ hook reifies each name once, its modules run then
      [] p.case = "hook_used" -> "(1, 'sub', ['pkg', 'pkg']) ['pkg', 'sub']"
      \* such a hook is given a dotted lazy import's whole name, so the submodule runs too
      [] p.case = "hook_dotted" -> "([('pkg.sub', None)], ['pkg', 'sub']) ['pkg', 'sub']"
      \* a lazily named submodule read for a call is imported first, then called
      [] p.case = "method_read" -> "(\"'module' object is not callable\", 'sub') ['pkg', 'sub']"
      \* a Python __lazy_import__ is called at the statement with __import__'s arguments,
      \* its result bound as __import__'s is, and no module runs
      [] p.case = "lazy_hook" -> "([('pkg', None, 0), ('pkg', ('sub',), 0)], True, 'r-sub') []"
      [] p.case = "lazy_hook_missing" -> "ImportError: __lazy_import__ not found []"
      \* a Python __contains__ of __lazy_modules__ names each import lazy, then the host's
      \* policy is asked, its verdict's Python __bool__ making each eager, in order
      [] p.case = "policy" -> "([('in', 'pkg'), ('policy', 'pkg', None), 'bool', ('in', 'pkg'), ('policy', 'pkg', ('sub',)), 'bool'], 'module', 'module') ['pkg', 'sub']"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A program that never uses a lazy name runs no module.
Unused == {"unused", "from_unused", "placeholder", "from_placeholder", "missing_unused", "not_cached", "registry",
           "compat", "compat_from", "compat_getitem", "lazy_hook", "lazy_hook_missing"}
NothingRuns == Done /\ program.case \in Unused => SubSeq(outcome, Len(outcome) - 1, Len(outcome)) = "[]"
=============================================================================
