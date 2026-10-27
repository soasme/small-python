------------------------------- MODULE Super -------------------------------
(***************************************************************************)
(* Cooperative method calls through super(), as Python specifies them      *)
(* (library/functions.html#super: it searches the MRO of the instance's    *)
(* type, starting after the class the method was defined in), for the      *)
(* diamond                                                                 *)
(*                                                                         *)
(*     class A: ...                                                        *)
(*     class B(A): ...                                                     *)
(*     class C(A): ...                                                     *)
(*     class D(B, C): ...                                                  *)
(*                                                                         *)
(* where each class's m is                                                 *)
(*                                                                         *)
(*     none     not defined                                                *)
(*     stop     def m(self): log.append(<name>)                            *)
(*     super    def m(self): log.append(<name>); super().m()               *)
(*                                                                         *)
(* and the program calls X().m() for one of the classes X. The outcome is  *)
(* the log, and AttributeError if a lookup found no m (object has none).   *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Classes == {"A", "B", "C", "D"}
Kinds == {"none", "stop", "super"}
MRO(x) == CASE x = "A" -> <<"A">> [] x = "B" -> <<"B", "A">> [] x = "C" -> <<"C", "A">>
             [] x = "D" -> <<"D", "B", "C", "A">>
Programs == [kind : [Classes -> Kinds], call : Classes]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<<<>>, "pending">>

Call(p) ==
    LET mro == MRO(p.call)
        \* m as found from position i of the MRO on (the receiver's class
        \* is position 1; super() in mro[j] starts at j + 1).
        RECURSIVE From(_)
        From(i) == IF i > Len(mro) THEN <<<<>>, "AttributeError">>
                   ELSE IF p.kind[mro[i]] = "none" THEN From(i + 1)
                   ELSE IF p.kind[mro[i]] = "stop" THEN <<<<mro[i]>>, "ok">>
                   ELSE LET rest == From(i + 1) IN <<<<mro[i]>> \o rest[1], rest[2]>>
    IN  From(1)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Call(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
Log == outcome[1]
Index(s, x) == CHOOSE i \in DOMAIN s : s[i] = x

\* Methods run in MRO order: for D, C's runs after B's although C is not
\* B's base.
InMROOrder == Done => \A i, j \in DOMAIN Log : i < j => Index(MRO(program.call), Log[i]) < Index(MRO(program.call), Log[j])

\* Each method runs at most once, even A's in the diamond.
AtMostOnce == Done => \A i, j \in DOMAIN Log : i # j => Log[i] # Log[j]

\* When every class cooperates, every class's method runs, then lookup
\* fails at object.
AllCooperate == Done /\ (\A c \in Classes : program.kind[c] = "super") =>
    Log = MRO(program.call) /\ outcome[2] = "AttributeError"
=============================================================================
