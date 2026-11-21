--------------------------- MODULE ClassCreation ---------------------------
(***************************************************************************)
(* The steps of creating a class, as The Python Language Reference         *)
(* specifies them (reference/datamodel.html#customizing-class-creation     *)
(* and reference/compound_stmts.html#class-definitions), for              *)
(*                                                                         *)
(*     @deco                       # optional                              *)
(*     class C(B, metaclass=Meta, flag=1):   # Meta and flag optional      *)
(*         a = D()                 # 0, 1, or 2 attributes whose class     *)
(*         b = S()                 #   defines __set_name__, S's a         *)
(*                                 #   staticmethod of (owner, name)       *)
(*                                                                         *)
(* where B may define __init_subclass__(cls, **kw), or be given by an      *)
(* object, made by a call logging "base", whose __mro_entries__, which     *)
(* its Python __getattribute__ reads, returns (B,), and Meta (a subclass   *)
(* of type) defines __new__ and __init__, and possibly __prepare__, read   *)
(* by a descriptor's Python __get__ logging "prepare_get", each            *)
(* passing flag on to type.__new__ but not to type.__init__, or            *)
(* __init__ alone, type.__new__ then receiving flag itself, or mro         *)
(* alone, returning type.mro's order and called after any __new__,         *)
(* before the other hooks. Every hook logs its name; the class body        *)
(* logs "body" when it calls, else "add" by an operator's Python method    *)
(* (a type() call's body function only assigns), and may begin with        *)
(* an annotated assignment; C may take a type parameter, class             *)
(* C[T](...), which adds the base Generic[T]; and the statement's          *)
(* __build_class__ may be a Python function calling the builtin one.       *)
(* None of these changes an outcome. The outcome is the log and whether    *)
(* the statement raised.                                                   *)
(* The class may instead be a call, C = deco(Meta("C", (B,), ns,           *)
(* flag=1)), Meta type when none, of a namespace the body's statements     *)
(* fill, with no __mro_entries__, __prepare__ or type parameter. A         *)
(* __prepare__ may return a dict subclass whose Python __setitem__         *)
(* logs the body's implicit stores of __module__ ("module"), before        *)
(* its statements, and __static_attributes__ ("static"), after them;       *)
(* the body then ends with def m, logging "def", a load of m, logging      *)
(* "load" by its Python __getitem__, and del m, logging "del" by its       *)
(* Python __delitem__, then k = j = 1, logging "chain" for j, and del      *)
(* k, j, logging "del" for each, then a handler's except ... as e,         *)
(* logging "caught" for its store, "handler" for its store of None,        *)
(* and "del", then the same of a handler that raises, then two plain      *)
(* stores, logging "plain" each.                                           *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Metas == {"none", "meta", "prepare", "init", "mro"}
Programs == [meta : Metas, subclass_hook : BOOLEAN, set_names : 0..2, deco : BOOLEAN, flag : BOOLEAN, calls : BOOLEAN, entries : BOOLEAN, annotated : BOOLEAN, generic : BOOLEAN, call : BOOLEAN, logged : BOOLEAN, builder : BOOLEAN]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<<<>>, "pending">>

Create(p) ==
    LET custom == p.meta \in {"meta", "prepare", "init"}
        \* type.__new__ calls __set_name__ on each attribute in definition
        \* order, then the first base's __init_subclass__ (object's takes
        \* no keyword arguments).
        names == <<"set_name a", "set_name b">>
        fails == p.flag /\ ~p.subclass_hook
        typeNew == SubSeq(names, 1, p.set_names)
                   \o (IF p.subclass_hook THEN <<IF p.flag THEN "init_subclass flag" ELSE "init_subclass">> ELSE <<>>)
        logged == p.logged /\ p.meta = "prepare" /\ ~p.call
        before == (IF p.entries /\ ~p.call THEN <<"base", "mro_entries">> ELSE <<>>) \o (IF p.meta = "prepare" /\ ~p.call THEN <<"prepare_get", "prepare">> ELSE <<>>)
                  \o (IF logged THEN <<"module">> ELSE <<>>) \o (IF p.calls THEN <<"body">> ELSE IF p.call THEN <<>> ELSE <<"add">>) \o (IF logged THEN <<"def", "load", "del", "chain", "del", "del", "caught", "handler", "del", "caught", "handler", "del", "plain", "plain", "static">> ELSE <<>>)
                  \o (IF p.meta \in {"meta", "prepare"} THEN <<"new">> ELSE <<>>)
                  \o (IF p.meta = "mro" THEN <<"mro">> ELSE <<>>) \o typeNew
    IN  IF fails THEN <<before, "TypeError">>
        ELSE <<before \o (IF custom THEN <<"init">> ELSE <<>>) \o (IF p.deco THEN <<"decorate">> ELSE <<>>), "ok">>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Create(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
Log == outcome[1]
Index(x) == CHOOSE i \in DOMAIN Log : Log[i] = x
Logged(x) == \E i \in DOMAIN Log : Log[i] = x

\* The namespace is prepared before the body runs, and the body before the
\* metaclass is called.
BodyBetween == Done /\ Logged("body") => (Logged("prepare") => Index("prepare") < Index("body"))
                                         /\ (Logged("new") => Index("body") < Index("new"))

\* The implicit names surround the body's statements.
ImplicitAroundBody == Done /\ Logged("module") /\ Logged("body") => Index("module") < Index("body") /\ Index("body") < Index("static")

\* The body's statements bind and delete through the namespace in order, between the implicit names.
BindsInBody == Done /\ Logged("def") => Index("module") < Index("def") /\ Index("def") < Index("del") /\ Index("del") < Index("static")

\* The body loads a name through the namespace between its binding and deletion.
LoadsInBody == Done /\ Logged("load") => Index("def") < Index("load") /\ Index("load") < Index("del")

\* The bases are evaluated, then resolved, before anything else runs.
EntriesFirst == Done /\ Logged("mro_entries") => Index("base") = 1 /\ Index("mro_entries") = 2

\* __set_name__ runs before __init_subclass__, and both before Meta.__init__.
HooksInOrder == Done /\ Logged("set_name a") /\ Logged("init") => Index("set_name a") < Index("init")

\* A metaclass's mro() runs before the class's callbacks.
MroBeforeHooks == Done /\ Logged("mro") /\ Logged("set_name a") => Index("mro") < Index("set_name a")

\* The decorator gets the finished class: it is always last.
DecoratorLast == Done /\ Logged("decorate") => Index("decorate") = Len(Log)
=============================================================================
