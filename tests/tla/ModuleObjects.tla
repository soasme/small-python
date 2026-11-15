---------------------------- MODULE ModuleObjects ----------------------------
(***************************************************************************)
(* Module objects, as The Python Language Reference specifies them         *)
(* (reference/datamodel.html#modules, its import-related and other         *)
(* writable attributes, and #module-dictionaries): attribute assignment    *)
(* and deletion update the module's namespace dictionary, which is         *)
(* read-only as __dict__ and not a global inside the module; a module made *)
(* by the module type has __name__, __doc__ (or None), and None for        *)
(* __package__, __loader__, and __spec__, no __file__ or __path__, and     *)
(* __annotations__ ({} or those of its body) with __annotate__ None; a     *)
(* read finds the namespace's entry, then the module type's attributes,    *)
(* such as object's methods, then calls the namespace's __getattr__.       *)
(*                                                                         *)
(* A program makes m = ModuleType("m"), or ModuleType("m", "doc"), then    *)
(* reads one attribute, or does one of                                     *)
(*                                                                         *)
(*     set       m.x = 1; m.__dict__["x"]                                  *)
(*     dictset   m.__dict__["y"] = 2; m.y                                  *)
(*     del       m.x = 1; del m.x; hasattr(m, "x")                         *)
(*     delmiss   del m.nope           getmiss   m.nope                     *)
(*     setdict   m.__dict__ = {}      global    __dict__ inside m          *)
(*     annotate  run "a: int = 1" in m; m.__annotations__                  *)
(*     rename    m.__name__ = "r"; m.__name__                              *)
(*     getattr   m.__getattr__ = lambda n: n * 2 (a Python function);      *)
(*               m.ab, hasattr(m, "zz"), m.__eq__(m), "ab" in m.__dict__   *)
(*     typefirst m.__getattr__ answers "GA"; m.__repr__, m.__init__ types  *)
(*                                                                         *)
(* The outcome is the repr of the result, or the exception.                *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Reads == {"__name__", "__doc__", "__package__", "__loader__", "__spec__", "__file__", "__path__", "__annotations__",
          "__annotate__"}
Programs == [doc : BOOLEAN, op : {"read"}, attr : Reads]
            \cup [doc : BOOLEAN, op : {"set", "dictset", "del", "delmiss", "getmiss", "setdict", "global", "annotate", "rename",
                                              "getattr", "typefirst"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Read(p, a) == CASE a = "__name__" -> "'m'"
                [] a = "__doc__" -> IF p.doc THEN "'doc'" ELSE "None"
                [] a \in {"__package__", "__loader__", "__spec__", "__annotate__"} -> "None"
                [] a \in {"__file__", "__path__"} -> "AttributeError"
                [] a = "__annotations__" -> "{}"

Run(p) == CASE p.op = "read" -> Read(p, p.attr)
             [] p.op = "set" -> "1"                     \* m.x = 1 is m.__dict__["x"] = 1
             [] p.op = "dictset" -> "2"
             [] p.op = "del" -> "False"
             [] p.op \in {"delmiss", "getmiss", "setdict"} -> "AttributeError"
             [] p.op = "global" -> "NameError"
             [] p.op = "annotate" -> "{'a': <class 'int'>}"
             [] p.op = "rename" -> "'r'"
             [] p.op = "getattr" -> "('abab', True, True, False)"
             [] p.op = "typefirst" -> "('method-wrapper', 'method-wrapper')"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The namespace dictionary and the attributes are one.
OneNamespace == Done /\ program.op \in {"set", "dictset"} => outcome # "AttributeError"
\* The type's attributes come before the namespace's __getattr__.
TypeBeforeFallback == Done /\ program.op = "typefirst" => outcome # "('GA', 'GA')"
=============================================================================
