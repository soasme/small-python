---------------------------- MODULE OperationThrow ----------------------------
(***************************************************************************)
(* throw() into a coroutine whose await of an async generator's asend()    *)
(* awaitable (anext(g)) is in progress, as PLS-315 27.4.2 and 27.5.1       *)
(* specify it: the generator is suspended in an await of its own, where    *)
(* the exception is raised. The body                                       *)
(*                                                                         *)
(*     try: await Pause()                                                  *)
(*     except KeyError:                                                    *)
(*         after: yield "handled" | yield await Pause() | return | pass    *)
(*     yield "end"                                                         *)
(*                                                                         *)
(* receives KeyError("k"), the class KeyError, or ValueError, which it     *)
(* does not handle. The outcome is what throw() does: the await's value    *)
(* (StopIteration), a suspension of the coroutine, or the exception, then  *)
(* whether the handler ran.                                                *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [after : {"yield", "await", "return", "pass"}, thrown : {"instance", "class", "other"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Handled(p) == p.thrown # "other"

Run(p) == IF ~Handled(p) THEN "raised ValueError caught=False"
          ELSE CASE p.after = "yield" -> "value handled caught=True"
                 [] p.after = "await" -> "suspended caught=True"
                 [] p.after = "return" -> "raised StopAsyncIteration caught=True"
                 [] p.after = "pass" -> "value end caught=True"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A class thrown acts as its instance.
ClassAsInstance == Done /\ program.thrown = "class" => outcome = Run([program EXCEPT !.thrown = "instance"])

\* An exception the body does not handle ends the await with it.
Unhandled == Done /\ program.thrown = "other" => outcome = "raised ValueError caught=False"
=============================================================================
