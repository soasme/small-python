---------------------------- MODULE OperationClose ----------------------------
(***************************************************************************)
(* close(), throw() or next() of an asend(), athrow() or aclose()          *)
(* awaitable, or of anext(g, "d"), as PLS-315 27.5.1 and 19.3.4 specify    *)
(* it, or close() of a coroutine suspended in an await of one (coclose).   *)
(* Begun, its async generator is suspended in                              *)
(* an await of its own, where GeneratorExit, or KeyError, is raised; the   *)
(* body handles either and then yields a value, awaits, raises LookupError *)
(* or returns. Not begun, the generator is at its first yield, which       *)
(* handles only GeneratorExit and then awaits. next() goes on from that    *)
(* await, the body then returning. anext()'s methods are its asend's,     *)
(* whose StopAsyncIteration it makes StopIteration, of its default; a      *)
(* coroutine's close closes the awaitable as its close() does, raising     *)
(* what that raises. The outcome is what the call does: a value or None, a *)
(* suspension, or the exception it raises.                                 *)
(***************************************************************************)
EXTENDS Naturals

Programs == [kind : {"asend", "athrow", "aclose", "anext"}, after : {"yield", "await", "raise", "return"},
             how : {"close", "throw", "next", "coclose"}, begun : BOOLEAN]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* A close ends with None but where its generator awaits, or an aclose()'s
\* yields a value, which raise RuntimeError.
Close(p) == CASE p.after = "await" -> "RuntimeError"
              [] p.after = "raise" -> "LookupError"
              [] p.after = "yield" /\ p.kind = "aclose" -> "RuntimeError"
              [] OTHER -> "None"

\* A throw ends as the awaitable's send does: a value yielded is its
\* StopIteration, an await suspends, a return raises StopAsyncIteration,
\* or, for aclose(), StopIteration, whose yielded value raises RuntimeError.
Throw(p) == CASE p.after = "await" -> "suspended"
              [] p.after = "raise" -> "LookupError"
              [] p.after = "yield" -> IF p.kind = "aclose" THEN "RuntimeError" ELSE "StopIteration"
              [] p.after = "return" -> IF p.kind \in {"aclose", "anext"} THEN "StopIteration" ELSE "StopAsyncIteration"

\* A next() of one begun resumes its await, and the body returns, which ends
\* an aclose() with StopIteration and the others with StopAsyncIteration;
\* one not begun runs to the await, which suspends.
Next(p) == IF ~p.begun THEN "suspended" ELSE IF p.kind \in {"aclose", "anext"} THEN "StopIteration" ELSE "StopAsyncIteration"

Init == program \in Programs /\ outcome = Pending
\* One not begun throws at the first yield: KeyError propagates, and a
\* close's GeneratorExit is handled by an await.
Fresh(p) == IF p.how = "close" THEN "RuntimeError" ELSE "KeyError"

Execute == outcome = Pending /\ UNCHANGED program /\
           outcome' = (IF program.how = "next" THEN Next(program) ELSE IF program.how = "coclose" THEN Close(program)
                       ELSE IF ~program.begun THEN Fresh(program) ELSE IF program.how = "close" THEN Close(program) ELSE Throw(program))
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* An await a begun generator suspends in never ends the call quietly.
AwaitNotQuiet == Done /\ program.begun /\ program.after = "await" /\ program.how # "next" => outcome \in {"RuntimeError", "suspended"}

\* A coroutine's close of the awaitable it awaits ends as the awaitable's close.
CoroutineCloses == Done /\ program.how = "coclose" => outcome = Close(program)
=============================================================================
