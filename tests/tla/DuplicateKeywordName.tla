------------------------ MODULE DuplicateKeywordName ------------------------
(***************************************************************************)
(* How a call's duplicate keyword names its callee, as PLS-315 13.3.4      *)
(* specifies FunctionStr, for every call                                   *)
(*                                                                         *)
(*     f( **{"a": 1}, **{"a": 2})     # or f( **{"a": 1}, a=2)             *)
(*                                                                         *)
(* of a callable instance whose Python __getattribute__, which may loop,   *)
(* gives its __qualname__ (a str), raises AttributeError, or raises        *)
(* another error, and gives its __module__ (a str, None or "builtins"),    *)
(* raises AttributeError or another error; one without __qualname__ is     *)
(* named by its Python __str__, which returns a str or not. The outcome    *)
(* is the name in the TypeError and the attributes read, in order.         *)
(***************************************************************************)
EXTENDS Sequences

Qualnames == {"str", "absent", "error"}
Modules == {"str", "none", "builtins", "absent", "error"}
Programs == [merge : {"double", "keyword"}, qualname : Qualnames, module : Modules, text : {"str", "other"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", <<>>>>

\* Without __qualname__ the name is str(f), "function" when that fails;
\* with it, "Q()" behind the module unless it is absent, None or builtins.
\* Any other error makes the name "function".
Name(p) ==
    CASE p.qualname = "error" -> <<"function", <<"__qualname__">>>>
      [] p.qualname = "absent" -> <<IF p.text = "str" THEN "text" ELSE "function", <<"__qualname__", "__str__">>>>
      [] p.module = "error" -> <<"function", <<"__qualname__", "__module__">>>>
      [] p.module = "str" -> <<"mod.Q()", <<"__qualname__", "__module__">>>>
      [] OTHER -> <<"Q()", <<"__qualname__", "__module__">>>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Name(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
\* The merge's shape does not change the name.
SameName == outcome # Pending =>
            outcome = Name([program EXCEPT !.merge = IF program.merge = "double" THEN "keyword" ELSE "double"])
\* __module__ is read only after a __qualname__ was found.
ModuleAfterQualname == outcome # Pending /\ Len(outcome[2]) = 2 /\ outcome[2][2] = "__module__" => program.qualname = "str"
=============================================================================
