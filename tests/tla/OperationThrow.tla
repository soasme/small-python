---------------------------- MODULE OperationThrow ----------------------------
(***************************************************************************)
(* throw() or close() of a coroutine whose await of an async generator's   *)
(* asend() awaitable (anext(g)) is in progress, as PLS-315 27.4.2 and      *)
(* 27.5.1 specify it: the generator is suspended in an await of its own,   *)
(* where the exception, or GeneratorExit, is raised. The body              *)
(*                                                                         *)
(*     try: await Pause()                                                  *)
(*     except (KeyError, GeneratorExit):                                   *)
(*         after: yield "handled" | yield await Pause() | return | pass    *)
(*     yield "end"                                                         *)
(*                                                                         *)
(* receives KeyError("k"), the class KeyError, ValueError, which it does   *)
(* not handle, or a close. The outcome is what throw() or close() does:    *)
(* the await's value (StopIteration), a suspension of the coroutine, the   *)
(* exception, or a close's None, then whether the handler ran.             *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [after : {"yield", "await", "return", "pass"}, thrown : {"instance", "class", "other", "close"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Handled(p) == p.thrown # "other"

\* A close closes the awaitable first: an await raises RuntimeError, and
\* anything else ends it, the coroutine then closing.
Run(p) == IF p.thrown = "close" THEN (IF p.after = "await" THEN "raised RuntimeError caught=True" ELSE "closed caught=True")
          ELSE IF ~Handled(p) THEN "raised ValueError caught=False"
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
