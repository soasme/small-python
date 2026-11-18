----------------------------- MODULE AsyncFor -----------------------------
(***************************************************************************)
(* Asynchronous iteration, as The Python Language Reference specifies it   *)
(* (reference/compound_stmts.html#the-async-for-statement, reference/      *)
(* datamodel.html#asynchronous-iterators, and reference/expressions.html#  *)
(* asynchronous-comprehensions): `async for` calls __aiter__ (an ordinary  *)
(* method) and awaits __anext__() for each item until it raises            *)
(* StopAsyncIteration, after which the else clause runs unless the loop    *)
(* broke or raised; the values an awaited __anext__ passes out reach the   *)
(* coroutine's driver; an object without __aiter__, an __aiter__ result    *)
(* without __anext__, and an __anext__ result that is not awaitable each   *)
(* raise TypeError; asynchronous comprehensions iterate the same way; and  *)
(* async for, async with, await, and asynchronous comprehensions outside   *)
(* an async function are syntax errors.                                    *)
(*                                                                         *)
(* A loop program drives a coroutine running `async for x in SRC:          *)
(* BODY` with an else clause, where SRC is an async generator that         *)
(* awaits a step (which passes out "tick") before yielding 0 and 1, an     *)
(* async generator that yields each of its items by a yield statement      *)
(* inside its own async for over it, a class whose __anext__ returns 1     *)
(* and 2, a class whose plain-function __anext__ returns coroutines of 1   *)
(* and 2 and then raises StopAsyncIteration itself, a class whose          *)
(* __anext__ awaits a step before returning 1 and                          *)
(* 2 and before raising StopAsyncIteration, a class without __aiter__,     *)
(* a class whose __anext__ returns 5, or a class whose __aiter__           *)
(* returns 5; and BODY appends x and then completes, breaks, or raises     *)
(* KeyError. A comprehension program builds a list, set, or dict over      *)
(* the first generator, a list over it whose element awaits a step         *)
(* before giving ten times the item, the steps of both passing out in      *)
(* turn, or a list over the class whose __anext__ returns 1 and 2, its     *)
(* Python __aiter__ called as the comprehension is evaluated. A syntax     *)
(* program compiles async for, async with, await, or an asynchronous       *)
(* comprehension in a plain function. The outcome is the values passed     *)
(* out, the items, and whether else ran, or the exception.                 *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [part : {"loop"}, source : {"agen", "relay", "class", "plain", "awaiting", "noaiter", "badanext", "noanext"}, body : {"normal", "break", "raise"}]
            \cup [part : {"comprehension"}, kind : {"list", "set", "dict", "class", "element"}]
            \cup [part : {"syntax"}, construct : {"for", "with", "await", "comprehension"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Ticks(n) == CASE n = 0 -> "[]" [] n = 1 -> "['tick']" [] n = 2 -> "['tick', 'tick']" [] n = 3 -> "['tick', 'tick', 'tick']"
                [] n = 4 -> "['tick', 'tick', 'tick', 'tick']"

Loop(p) ==
    IF p.source \in {"noaiter", "badanext", "noanext"} THEN "[] TypeError"
    ELSE LET agen == p.source \in {"agen", "relay"}
             awaiting == p.source = "awaiting"
             first == IF agen THEN "0" ELSE "1"
             second == IF agen THEN "1" ELSE "2"
         IN  CASE p.body = "normal" -> Ticks(IF agen THEN 2 ELSE IF awaiting THEN 3 ELSE 0) \o " [" \o first \o ", " \o second \o ", 'else']"
               [] p.body = "break" -> Ticks(IF agen \/ awaiting THEN 1 ELSE 0) \o " [" \o first \o "]"
               [] p.body = "raise" -> Ticks(IF agen \/ awaiting THEN 1 ELSE 0) \o " KeyError"

Comprehension(p) == CASE p.kind = "list" -> "['tick', 'tick'] [0, 1]"
                      [] p.kind = "set" -> "['tick', 'tick'] {0, 1}"
                      [] p.kind = "dict" -> "['tick', 'tick'] {0: 0, 1: 1}"
                      [] p.kind = "class" -> "[] [1, 2]"
                      [] p.kind = "element" -> Ticks(4) \o " [0, 10]"

Run(p) == CASE p.part = "loop" -> Loop(p)
            [] p.part = "comprehension" -> Comprehension(p)
            [] p.part = "syntax" -> "SyntaxError"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The else clause runs exactly when the loop ran out of items.
ElseOnExhaustion == Done /\ program.part = "loop" /\ program.body # "normal" =>
    ~(\E i \in 1..Len(outcome) : SubSeq(outcome, i, Len(outcome)) = "'else']")
=============================================================================
