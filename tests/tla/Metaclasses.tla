---------------------------- MODULE Metaclasses ----------------------------
(***************************************************************************)
(* Metaclasses, as The Python Language Reference specifies them            *)
(* (reference/datamodel.html#metaclasses): a base that is not a class but  *)
(* defines __mro_entries__ is replaced by the bases it returns, and the    *)
(* original bases are kept as __orig_bases__; an explicit metaclass that   *)
(* is not a class is called as is; otherwise the most derived of the       *)
(* explicit metaclass (type by default) and the bases' metaclasses is      *)
(* used, and if none is a subclass of all the others the definition        *)
(* raises TypeError; and a __class__ cell made for a method that uses      *)
(* super() or __class__ is filled by type.__new__ from __classcell__, so   *)
(* a metaclass that drops it makes the definition raise RuntimeError.      *)
(*                                                                         *)
(* A program defines metaclasses MA(type), MB(MA), and MC(type), classes   *)
(* A, B, and C of each, and E, an object whose __mro_entries__ returns     *)
(* (B,); then class X(BASES, metaclass=META) for BASES (), (A,), (B,),     *)
(* (C,), (A, B), (A, C), (E,), or (E, A), and META absent, type, MA, MB,   *)
(* MC, or a function returning "f". The outcome is the name of type(X)     *)
(* with whether X has __orig_bases__, "f", or the exception. A cell        *)
(* program gives X a method returning __class__, under a metaclass whose   *)
(* __new__ passes the namespace on, removes __classcell__, or creates no   *)
(* cell because no method needs one; the outcome is the method's result.   *)
(***************************************************************************)
EXTENDS Naturals, Sequences

BaseSets == {"none", "A", "B", "C", "AB", "AC", "E", "EA"}
Metas == {"none", "type", "MA", "MB", "MC", "func"}
Programs == [part : {"derive"}, bases : BaseSets, meta : Metas]
            \cup [part : {"cell"}, cell : {"kept", "dropped", "unused"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* The resolved bases, after __mro_entries__.
Resolved(b) == CASE b = "none" -> <<>> [] b = "A" -> <<"A">> [] b = "B" -> <<"B">> [] b = "C" -> <<"C">>
                 [] b = "AB" -> <<"A", "B">> [] b = "AC" -> <<"A", "C">>
                 [] b = "E" -> <<"B">> [] b = "EA" -> <<"B", "A">>

MetaOf(cls) == CASE cls = "A" -> "MA" [] cls = "B" -> "MB" [] cls = "C" -> "MC"

\* Subclass relation among the metaclasses.
Sub(m, n) == m = n \/ n = "type" \/ (m = "MB" /\ n = "MA")

Derive(p) ==
    LET bases == Resolved(p.bases)
        cands == {IF p.meta = "none" THEN "type" ELSE p.meta} \cup {MetaOf(bases[i]) : i \in 1..Len(bases)}
        winners == {m \in cands : \A n \in cands : Sub(m, n)}
        orig == IF p.bases \in {"E", "EA"} THEN "orig" ELSE "plain"
    IN  IF p.meta = "func" THEN "f"
        ELSE IF winners = {} THEN "TypeError"
        ELSE (CHOOSE m \in winners : TRUE) \o " " \o orig

Cell(p) == IF p.cell = "dropped" THEN "RuntimeError" ELSE "X"

Run(p) == IF p.part = "derive" THEN Derive(p) ELSE Cell(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* An explicit metaclass never loses to a base's metaclass it derives from.
ExplicitWins == Done /\ program.part = "derive" /\ program.meta = "MB" /\ program.bases \in {"A", "B", "AB"} =>
    outcome = "MB plain"

\* Unrelated metaclasses conflict.
Conflict == Done /\ program.part = "derive" /\ program.bases = "AC" /\ program.meta # "func" => outcome = "TypeError"
=============================================================================
