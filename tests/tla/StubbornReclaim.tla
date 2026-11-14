-------------------------- MODULE StubbornReclaim --------------------------
(***************************************************************************)
(* Reclaiming a generator or coroutine whose close on becoming unreachable *)
(* is ignored, as PLS-315 27.2.4 and 9.7 specify it: the close runs its    *)
(* GeneratorExit handler, which suspends again, plainly or in a yield from *)
(* or await of an iterator; the close's RuntimeError is reported; and the  *)
(* object is then reclaimed all the same, the iterator it waits on closed  *)
(* and its locals finalized, though the handled exception's traceback      *)
(* refers to its frame. Each round reclaims its own object, whatever       *)
(* rounds came before.                                                     *)
(*                                                                         *)
(* A program makes `rounds` objects of `kind` one after another, each      *)
(* holding a local whose __del__ logs "del", suspends it in a try, and     *)
(* drops it. Its handler logs "ignored" and then yields, or, when          *)
(* delegates, waits on an iterator whose finally logs "inner". The outcome *)
(* is the log of the rounds, each ending with "dropped".                   *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [kind : {"generator", "coroutine"}, delegates : BOOLEAN, rounds : 1..3]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

\* One round: the handler, the delegate's close, the local's __del__.
Round(p) == <<"ignored">> \o (IF p.delegates THEN <<"inner">> ELSE <<>>) \o <<"del", "dropped">>

RECURSIVE Rounds(_, _)
Rounds(p, n) == IF n = 0 THEN <<>> ELSE Rounds(p, n - 1) \o Round(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Rounds(program, program.rounds) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Every round's object is reclaimed: as many locals finalized as rounds.
EachReclaimed == Done => Len(SelectSeq(outcome, LAMBDA e : e = "del")) = program.rounds
=============================================================================
