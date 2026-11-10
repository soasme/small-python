--------------------------- MODULE ClassCreation ---------------------------
(***************************************************************************)
(* The steps of creating a class, as The Python Language Reference         *)
(* specifies them (reference/datamodel.html#customizing-class-creation     *)
(* and reference/compound_stmts.html#class-definitions), for              *)
(*                                                                         *)
(*     @deco                       # optional                              *)
(*     class C(B, metaclass=Meta, flag=1):   # Meta and flag optional      *)
(*         a = D()                 # 0, 1, or 2 attributes whose class     *)
(*         b = D()                 #   defines __set_name__                *)
(*                                                                         *)
(* where B may define __init_subclass__(cls, **kw), or be given by an      *)
(* object whose __mro_entries__ returns (B,), and Meta (a subclass        *)
(* of type) defines __new__ and __init__, and possibly __prepare__, each   *)
(* passing flag on to type.__new__ but not to type.__init__, or __init__   *)
(* alone, type.__new__ then receiving flag itself. Every hook              *)
(* logs its name; the class body logs "body" when it calls, else it only   *)
(* assigns, and may begin with an annotated assignment; C may take a type  *)
(* parameter, class C[T](...), which adds the base Generic[T]. Neither     *)
(* changes an outcome. The outcome is the log and whether the statement   *)
(* raised.                                                                 *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Metas == {"none", "meta", "prepare", "init"}
Programs == [meta : Metas, subclass_hook : BOOLEAN, set_names : 0..2, deco : BOOLEAN, flag : BOOLEAN, calls : BOOLEAN, entries : BOOLEAN, annotated : BOOLEAN, generic : BOOLEAN]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<<<>>, "pending">>

Create(p) ==
    LET custom == p.meta # "none"
        \* type.__new__ calls __set_name__ on each attribute in definition
        \* order, then the first base's __init_subclass__ (object's takes
        \* no keyword arguments).
        names == <<"set_name a", "set_name b">>
        fails == p.flag /\ ~p.subclass_hook
        typeNew == SubSeq(names, 1, p.set_names)
                   \o (IF p.subclass_hook THEN <<IF p.flag THEN "init_subclass flag" ELSE "init_subclass">> ELSE <<>>)
        before == (IF p.entries THEN <<"mro_entries">> ELSE <<>>) \o (IF p.meta = "prepare" THEN <<"prepare">> ELSE <<>>) \o (IF p.calls THEN <<"body">> ELSE <<>>)
                  \o (IF p.meta \in {"meta", "prepare"} THEN <<"new">> ELSE <<>>) \o typeNew
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

\* The bases are resolved before anything else runs.
EntriesFirst == Done /\ Logged("mro_entries") => Index("mro_entries") = 1

\* __set_name__ runs before __init_subclass__, and both before Meta.__init__.
HooksInOrder == Done /\ Logged("set_name a") /\ Logged("init") => Index("set_name a") < Index("init")

\* The decorator gets the finished class: it is always last.
DecoratorLast == Done /\ Logged("decorate") => Index("decorate") = Len(Log)
=============================================================================
