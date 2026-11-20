---------------------------- MODULE ClassGetitem ----------------------------
(***************************************************************************)
(* Emulating generic types, as The Python Language Reference specifies it  *)
(* (reference/datamodel.html#emulating-generic-types): subscripting a      *)
(* class calls its metaclass's __getitem__ if there is one, else the       *)
(* class's __class_getitem__, which is a class method even when not        *)
(* decorated; subscripting an instance calls __getitem__ and never         *)
(* __class_getitem__; with neither, subscription raises TypeError; and     *)
(* builtin containers such as list and dict return a generic alias.        *)
(*                                                                         *)
(* A program defines class C with __class_getitem__ absent, a plain        *)
(* function, or a classmethod, each returning ("cg", cls.__name__, key);   *)
(* with or without __getitem__ returning "item"; under a metaclass with or *)
(* without __getitem__ returning "meta"; and subscripts C[int] or C()[int].*)
(* A builtin program takes repr(list[int]), repr(dict[str, int]),          *)
(* repr(tuple[int, ...]), or repr(type[int]). The outcome is the result    *)
(* or the exception.                                                       *)
(*                                                                         *)
(* A read program has C's __class_getitem__ read as any attribute is: a   *)
(* metaclass __getattribute__ or __getattr__ giving a function of the key, *)
(* a metaclass attribute that is a classmethod, a plain function or a      *)
(* staticmethod stored on C after creation (called with the key alone), a *)
(* __getattribute__ raising AttributeError (C not subscriptable) or        *)
(* KeyError, which propagates.                                             *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [part : {"user"}, cg : {"none", "plain", "classmethod"}, item : BOOLEAN, meta : BOOLEAN,
             subject : {"class", "instance"}]
            \cup [part : {"builtin"}, name : {"list", "dict", "tuple", "type"}]
            \cup [part : {"read"}, read : {"getattribute", "getattr", "meta_attribute", "stored", "static", "missing", "raising"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

User(p) ==
    IF p.subject = "class"
    THEN CASE p.meta -> "meta"
           [] p.cg # "none" -> "cg C int"                     \* bound to C either way
           [] OTHER -> "TypeError"
    ELSE IF p.item THEN "item" ELSE "TypeError"

Builtin(p) == CASE p.name = "list" -> "list[int]"
                [] p.name = "dict" -> "dict[str, int]"
                [] p.name = "tuple" -> "tuple[int, ...]"
                [] p.name = "type" -> "type[int]"

Read(p) == CASE p.read = "missing" -> "TypeError"
             [] p.read = "raising" -> "KeyError"
             [] p.read = "meta_attribute" -> "cg Meta int"   \* bound to the metaclass
             [] OTHER -> "key int"

Run(p) == CASE p.part = "user" -> User(p) [] p.part = "read" -> Read(p) [] OTHER -> Builtin(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Instances never reach __class_getitem__.
InstancesUseGetitem == Done /\ program.part = "user" /\ program.subject = "instance" => outcome \in {"item", "TypeError"}
=============================================================================
