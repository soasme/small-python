---------------------------- MODULE Awaitables ----------------------------
(***************************************************************************)
(* Awaitables and coroutine objects, as The Python Language Reference      *)
(* specifies them (reference/expressions.html#await, reference/            *)
(* datamodel.html#awaitable-objects and #coroutine-objects, and            *)
(* reference/compound_stmts.html#coroutine-function-definition): `await x` *)
(* awaits a coroutine, or an object whose __await__ returns an iterator,   *)
(* passing that iterator's values out to whoever drives the coroutine and  *)
(* taking its return value as the await's result; any other object, a      *)
(* plain generator included, raises TypeError; a coroutine can be awaited  *)
(* once, after which awaiting, sending to, or resuming it raises           *)
(* RuntimeError; coroutines are not iterable; the first send must be       *)
(* None; and throw() into a fresh coroutine raises the exception and       *)
(* finishes it.                                                            *)
(*                                                                         *)
(* An await program drives `async def main(): return await X` with         *)
(* send(None) until it finishes, where X is a coroutine returning 7, an    *)
(* object whose __await__ returns iter([1, 2]), one whose __await__        *)
(* yields 1 and returns 5, one whose __await__ returns 5, the int 5, a     *)
(* generator, or a coroutine awaited once already. An object program, on a *)
(* fresh coroutine, calls iter(), sends 1, closes it and sends None, or    *)
(* throws ValueError and then sends None. The outcome is the values the    *)
(* driver received and the result, or the exception.                       *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [part : {"await"}, x : {"coroutine", "iter", "gen", "bad", "int", "generator", "reused"}]
            \cup [part : {"object"}, op : {"iter", "send1", "close", "throw"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Await(p) == CASE p.x = "coroutine" -> "[] 7"
              [] p.x = "iter" -> "[1, 2] None"
              [] p.x = "gen" -> "[1] 5"
              [] p.x = "reused" -> "[] RuntimeError"
              [] OTHER -> "[] TypeError"

Object(p) == CASE p.op \in {"iter", "send1"} -> "TypeError"
               [] p.op = "close" -> "RuntimeError"
               [] p.op = "throw" -> "ValueError RuntimeError"

Run(p) == IF p.part = "await" THEN Await(p) ELSE Object(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Only awaitables pass values out.
OnlyAwaitablesYield == Done /\ program.part = "await" /\ program.x \in {"bad", "int", "generator"} =>
    outcome = "[] TypeError"
=============================================================================
