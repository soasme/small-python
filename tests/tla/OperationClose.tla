---------------------------- MODULE OperationClose ----------------------------
(***************************************************************************)
(* close() or throw() of an asend(), athrow() or aclose() awaitable, as    *)
(* PLS-315 27.5.1 specifies it. Begun, its async generator is suspended in *)
(* an await of its own, where GeneratorExit, or KeyError, is raised; the   *)
(* body handles either and then yields a value, awaits, raises LookupError *)
(* or returns. Not begun, the generator is at its first yield, which       *)
(* handles only GeneratorExit and then awaits. The outcome is what the     *)
(* call does: a value or None, a suspension, or the exception it raises.   *)
(***************************************************************************)
EXTENDS Naturals

Programs == [kind : {"asend", "athrow", "aclose"}, after : {"yield", "await", "raise", "return"}, how : {"close", "throw"}, begun : BOOLEAN]

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
              [] p.after = "return" -> IF p.kind = "aclose" THEN "StopIteration" ELSE "StopAsyncIteration"

Init == program \in Programs /\ outcome = Pending
\* One not begun throws at the first yield: KeyError propagates, and a
\* close's GeneratorExit is handled by an await.
Fresh(p) == IF p.how = "close" THEN "RuntimeError" ELSE "KeyError"

Execute == outcome = Pending /\ UNCHANGED program /\
           outcome' = (IF ~program.begun THEN Fresh(program) ELSE IF program.how = "close" THEN Close(program) ELSE Throw(program))
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* An await a begun generator suspends in never ends the call quietly.
AwaitNotQuiet == Done /\ program.begun /\ program.after = "await" => outcome \in {"RuntimeError", "suspended"}
=============================================================================
