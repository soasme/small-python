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
(* RuntimeError; coroutines are not iterable; the first send must be None; *)
(* throw() into a fresh coroutine raises the exception and finishes it; an *)
(* async generator's await passes values out through its asend() alike;    *)
(* and close() of a suspended one gives what it returns on GeneratorExit,  *)
(* or raises RuntimeError if it awaits a suspension again.                 *)
(*                                                                         *)
(* An await program drives `async def main(): return await X` with         *)
(* send(None) until it finishes, where X is a coroutine returning 7, an    *)
(* object whose __await__ returns iter([1, 2]), one whose __await__ yields *)
(* 1 and returns 5, a coroutine awaiting that one and returning its value  *)
(* plus 1, one whose __await__ returns 5, the int 5, a generator, a        *)
(* coroutine awaited once already, or an object whose __await__ returns an *)
(* instance with a Python __next__ giving 1 and 2 and then raising         *)
(* StopIteration(300), or one whose __await__ returns the chain            *)
(* coroutine's __await__() wrapper. An object program, on a fresh          *)
(* coroutine, calls iter(), sends 1, closes it and sends None, or throws   *)
(* ValueError and then sends None; or, suspended in await Gen() catching   *)
(* GeneratorExit, closes it as it returns 3 or awaits Gen() again; or,     *)
(* suspended in an await of iter([1, 2]) catching ValueError and returning *)
(* 4, throws ValueError, which raises at the await. A                     *)
(* wrapper program drives the chain coroutine through its __await__()      *)
(* wrapper with next() and send(None), throws ValueError through the       *)
(* wrapper into a coroutine returning 4 on it, or drops a coroutine        *)
(* suspended in await Gen() whose finally records "closed". An agen        *)
(* program takes asend(None) of an async generator that awaits Gen() and   *)
(* yields its value, or yields 'caught' when the await raises ValueError,  *)
(* and sends None to the asend twice, or sends None and then throws        *)
(* ValueError into it; the second step goes on at the await. The outcome   *)
(* is the values the driver received and the result, or the exception.     *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [part : {"await"}, x : {"coroutine", "iter", "gen", "chain", "bad", "int", "generator", "reused", "next", "wrapped"}]
            \cup [part : {"object"}, op : {"iter", "send1", "close", "throw", "closed", "ignored", "iterthrow"}]
            \cup [part : {"wrapper"}, op : {"drive", "throw", "dropped"}]
            \cup [part : {"agen"}, op : {"send", "throw"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Await(p) == CASE p.x = "coroutine" -> "[] 7"
              [] p.x = "iter" -> "[1, 2] None"
              [] p.x = "gen" -> "[1] 5"
              [] p.x = "chain" -> "[1] 6"   \* the inner await's value passes out
              [] p.x = "wrapped" -> "[1] 6"  \* as through the chain's __await__() wrapper
              [] p.x = "reused" -> "[] RuntimeError"
              [] p.x = "next" -> "[1, 2] 300"
              [] OTHER -> "[] TypeError"

Object(p) == CASE p.op \in {"iter", "send1"} -> "TypeError"
               [] p.op \in {"close", "ignored"} -> "RuntimeError"
               [] p.op = "closed" -> "3"
               [] p.op = "iterthrow" -> "4"
               [] p.op = "throw" -> "ValueError RuntimeError"

\* A wrapper's methods are its coroutine's; a dropped suspended coroutine closes.
Wrapper(p) == CASE p.op = "drive" -> "[1] 6" [] p.op = "throw" -> "4" [] p.op = "dropped" -> "closed"

\* An asend passes its async generator's await out; the await's value, or
\* its exception caught, is the next yield, which ends the asend.
AGen(p) == IF p.op = "send" THEN "[1] 5" ELSE "[1] 'caught'"

Run(p) == CASE p.part = "await" -> Await(p) [] p.part = "object" -> Object(p) [] p.part = "agen" -> AGen(p) [] OTHER -> Wrapper(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Only awaitables pass values out.
OnlyAwaitablesYield == Done /\ program.part = "await" /\ program.x \in {"bad", "int", "generator"} =>
    outcome = "[] TypeError"
=============================================================================
