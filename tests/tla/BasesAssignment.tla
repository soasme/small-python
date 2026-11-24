---------------------------- MODULE BasesAssignment ----------------------------
(***************************************************************************)
(* Assigning a class's __bases__ (PLS-315 10.4.2, step 7), for every       *)
(* program                                                                 *)
(*                                                                         *)
(*     class A: pass                                                       *)
(*     class B: pass                                                       *)
(*     class C(A, metaclass=M): pass   # M.mro logs the class, raises      *)
(*     class D(C): pass                # LookupError for the failing one,  *)
(*     class E(D): pass                # else returns type.mro(cls)        *)
(*     <store> C.__bases__ = <container>((<target>,))                      *)
(*                                                                         *)
(* stored by an assignment, a for target or setattr(), the container       *)
(* tuple or a tuple subclass T: C's MRO and then                           *)
(* each subclass's are recomputed, oldest first, each mro() called once;   *)
(* when one raises, every MRO and C's bases are restored and the           *)
(* LookupError propagates. The outcome is the exception or "ok", C's       *)
(* bases, D's and E's MROs, the classes mro() was called for, and whether  *)
(* C.__bases__ is the very tuple stored, or the old one once restored.     *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Order == <<"C", "D", "E">>
Programs == [store : {"assign", "for", "setattr"}, fail : {"none", "C", "D", "E"}, target : {"A", "B"},
             container : {"tuple", "T"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", <<>>, <<>>, <<>>, <<>>, FALSE>>

\* The classes whose mro() runs: all, or those up to the failing one.
Called(p) == IF p.fail = "none" THEN Order
             ELSE SubSeq(Order, 1, CHOOSE i \in 1..3 : Order[i] = p.fail)
MroOf(cls, base) == IF cls = "D" THEN <<"D", "C", base, "object">> ELSE <<"E", "D", "C", base, "object">>

Run(p) ==
    LET base == IF p.fail = "none" THEN p.target ELSE "A"
    IN  <<IF p.fail = "none" THEN "ok" ELSE "LookupError", <<base>>, MroOf("D", base), MroOf("E", base), Called(p), TRUE>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* C's mro() runs first, and a failure leaves the bases and MROs as they were.
CFirst == Done => outcome[5][1] = "C"
Restored == Done /\ outcome[1] = "LookupError" => outcome[2] = <<"A">> /\ outcome[3] = MroOf("D", "A")
=============================================================================
