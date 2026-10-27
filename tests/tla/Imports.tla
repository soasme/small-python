------------------------------ MODULE Imports ------------------------------
(***************************************************************************)
(* The import system, as The Python Language Reference specifies it        *)
(* (reference/import.html and reference/simple_stmts.html#the-import-      *)
(* statement, with the module attributes of reference/datamodel.html#      *)
(* import-related-attributes-on-module-objects): importing a submodule     *)
(* first imports its parents, runs each module once, caches it in          *)
(* sys.modules before running it (so a cycle sees a partial module) and    *)
(* removes it again if running it fails, and binds the submodule as an     *)
(* attribute of its parent; `import a.b` binds a, `import a.b as c` binds  *)
(* the submodule, and `from a import b` falls back to importing a.b; a     *)
(* None in sys.modules halts the import with ModuleNotFoundError, and any  *)
(* other cached object is the result; a regular package has an __init__    *)
(* and a __path__, a namespace package (a directory without __init__) a    *)
(* __path__ but no file; __package__ names the package for relative        *)
(* imports, which may not go beyond the top-level package nor be used      *)
(* outside a package; `from a import *` honors __all__; and a missing      *)
(* module, submodule, or name raises ModuleNotFoundError or ImportError.   *)
(*                                                                         *)
(* A program clears the fixture modules from sys.modules and runs one of   *)
(* the statements of CASES over the package pkg (an __init__ with          *)
(* __all__ = ["pub"], submodule sub, subpackage inner whose __init__       *)
(* imports `..sub` and `.leaf`, a leaf importing `..sub`, a module broken  *)
(* that raises ValueError, and a module beyond that imports from `...`),   *)
(* the namespace package nspkg, a module plain using `from . import x`,    *)
(* and the modules cycle_a and cycle_b importing each other. Every module  *)
(* logs its name when it runs. The outcome is the program's result (or     *)
(* the exception and its message, without the file name) and the log.      *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Cases == {"import_sub", "binds", "import_as", "from_submodule", "from_missing", "from_star", "relative",
          "broken", "beyond", "no_parent", "namespace", "twice", "none_cached", "replaced", "cycle",
          "attributes", "plain_attributes", "missing_module", "missing_sub", "from_inner_missing"}
Programs == [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Run(p) ==
    CASE p.case = "import_sub" -> "'sub' ['pkg', 'sub']"
      [] p.case = "binds" -> "['pkg'] ['pkg', 'sub']"                       \* import pkg.sub binds pkg only
      [] p.case = "import_as" -> "'pkg.sub' ['pkg', 'sub']"
      [] p.case = "from_submodule" -> "'sub' ['pkg', 'sub']"
      [] p.case = "from_missing" -> "ImportError: cannot import name 'missing' from 'pkg' ['pkg']"
      [] p.case = "from_star" -> "['pub'] ['pkg']"
      [] p.case = "relative" -> "('sub', 'pkg.sub') ['pkg', 'inner', 'sub', 'leaf']"
      [] p.case = "broken" -> "(False, True, False) ['pkg', 'broken']"       \* uncached, unbound
      [] p.case = "beyond" -> "ImportError: attempted relative import beyond top-level package ['pkg', 'beyond']"
      [] p.case = "no_parent" -> "ImportError: attempted relative import with no known parent package ['plain']"
      [] p.case = "namespace" -> "(None, True, 'nspkg') ['nsmod']"
      [] p.case = "twice" -> "'twice' ['pkg', 'sub']"
      [] p.case = "none_cached" -> "ModuleNotFoundError: import of pkg halted; None in sys.modules []"
      [] p.case = "replaced" -> "5 []"
      [] p.case = "cycle" -> "'partial' ['cycle_a', 'cycle_b']"
      [] p.case = "attributes" -> "('pkg', 'pkg', 'pkg', True, False) ['pkg', 'sub']"
      [] p.case = "plain_attributes" -> "('', False) ['cycle_b', 'cycle_a']"
      [] p.case = "missing_module" -> "ModuleNotFoundError: No module named 'nosuchmodule' []"
      [] p.case = "missing_sub" -> "ModuleNotFoundError: No module named 'pkg.nosuch' ['pkg']"
      [] p.case = "from_inner_missing" -> "ImportError: cannot import name 'nothing' from 'pkg.inner' ['pkg', 'inner', 'sub', 'leaf']"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Every log is one of these run orders, in which no module runs twice.
Logs == {"['pkg', 'sub']", "['pkg']", "['pkg', 'inner', 'sub', 'leaf']", "['pkg', 'broken']", "['pkg', 'beyond']",
         "['plain']", "['nsmod']", "[]", "['cycle_a', 'cycle_b']", "['cycle_b', 'cycle_a']"}
OnceEach == Done => \E log \in Logs : \E i \in 1..Len(outcome) : SubSeq(outcome, i, Len(outcome)) = log
=============================================================================
