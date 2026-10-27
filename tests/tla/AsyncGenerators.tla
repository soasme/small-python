-------------------------- MODULE AsyncGenerators --------------------------
(***************************************************************************)
(* The life cycle of an asynchronous generator driven through asend(),     *)
(* athrow(), and aclose(), each awaitable run to completion, as The Python *)
(* Language Reference specifies it (reference/expressions.html#           *)
(* asynchronous-generator-iterator-methods), with CPython's behavior where *)
(* the reference is silent: athrow() on a finished generator returns None, *)
(* and once aclose() has been called, athrow() and aclose() raise          *)
(* StopAsyncIteration without running the body, while asend() still       *)
(* resumes it. The body:                                                   *)
(*                                                                         *)
(*     last, i = None, 0                                                   *)
(*     while i < K:                                                        *)
(*         try:                                                            *)
(*             got = yield (i, last)                                       *)
(*         except ValueError:                                              *)
(*             got = 'caught'                                              *)
(*         except GeneratorExit:                                           *)
(*             if variant == 'plain': raise                                *)
(*             got = 'exit'                                                *)
(*             yield ('ignored', i)                                        *)
(*         if got == 'stop': return                                        *)
(*         last, i = got, i + 1                                            *)
(*                                                                         *)
(* `result` is the value an awaitable returned ("yield" with what the      *)
(* body yielded, "return" with None) or the exception it raised.           *)
(***************************************************************************)
EXTENDS Naturals, Sequences

CONSTANT K

Variants == {"plain", "stubborn"}
Sent == {"None", "go", "stop"}
Thrown == {"ValueError", "KeyError"}
Ops == {<<"asend", v>> : v \in Sent} \cup {<<"athrow", e>> : e \in Thrown} \cup {<<"aclose">>}
Pcs == {"start", "loop", "ignored", "done"}

VARIABLES variant, pc, i, last, closed, op, result
vars == <<variant, pc, i, last, closed, op, result>>

Results ==
    {<<"yield", n, l>> : n \in 0..K, l \in Sent \cup {"caught", "exit"}} \cup
    {<<"raise", e>> : e \in Thrown \cup {"TypeError", "RuntimeError", "StopAsyncIteration"}} \cup
    {<<"return", "None">>, <<"init">>}

TypeOK ==
    /\ variant \in Variants /\ pc \in Pcs /\ i \in 0..K /\ last \in Sent \cup {"caught", "exit"} /\ closed \in BOOLEAN
    /\ op \in Ops \cup {<<"init">>} /\ result \in Results

Init == variant \in Variants /\ pc = "start" /\ i = 0 /\ last = "None" /\ closed = FALSE /\ op = <<"init">> /\ result = <<"init">>

\* An async generator cannot return a value: running off its end, or a
\* bare return, makes the awaitable raise StopAsyncIteration.
Exhausted == <<"raise", "StopAsyncIteration">>
Finish(r) == pc' = "done" /\ result' = r /\ UNCHANGED <<i, last>>
Stay(r) == result' = r /\ UNCHANGED <<pc, i, last>>

Continue(got) ==
    IF got = "stop" THEN Finish(Exhausted)
    ELSE IF i + 1 < K THEN pc' = "loop" /\ i' = i + 1 /\ last' = got /\ result' = <<"yield", i + 1, got>>
    ELSE Finish(Exhausted)

ASend(v) ==
    /\ op' = <<"asend", v>>
    /\ CASE pc = "start" /\ v # "None" -> Stay(<<"raise", "TypeError">>)
         [] pc = "start" -> pc' = "loop" /\ result' = <<"yield", 0, "None">> /\ UNCHANGED <<i, last>>
         [] pc = "loop" -> Continue(v)
         [] pc = "ignored" -> Continue("exit")
         [] pc = "done" -> Stay(Exhausted)
    /\ UNCHANGED closed

AThrow(e) ==
    /\ op' = <<"athrow", e>>
    /\ CASE pc = "done" -> Stay(<<"return", "None">>)
         [] closed -> Stay(Exhausted)
         [] pc = "loop" /\ e = "ValueError" -> Continue("caught")
         [] OTHER -> Finish(<<"raise", e>>)
    /\ UNCHANGED closed

AClose ==
    /\ op' = <<"aclose">>
    /\ closed' = TRUE
    /\ CASE pc = "done" -> Stay(<<"return", "None">>)
         [] closed -> Stay(Exhausted)
         [] pc = "loop" /\ variant = "stubborn" ->
            pc' = "ignored" /\ result' = <<"raise", "RuntimeError">> /\ UNCHANGED <<i, last>>
         [] OTHER -> Finish(<<"return", "None">>)

Next == UNCHANGED variant /\ (AClose \/ \E v \in Sent : ASend(v) \/ \E e \in Thrown : AThrow(e))
Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
DoneIsFinal == [][(pc = "done" => pc' = "done")]_vars

\* A finished async generator answers asend() with StopAsyncIteration and
\* aclose() with None.
FinishedAnswers == [][(pc = "done" => (op'[1] = "asend" => result' = Exhausted)
                                      /\ (op' = <<"aclose">> => result' = <<"return", "None">>))]_vars

\* aclose() never yields a value; it raises RuntimeError only when the body
\* yielded again, and only the first time.
ACloseNeverYields == [][(op' = <<"aclose">> => result'[1] # "yield" /\
                         (result' = <<"raise", "RuntimeError">> => pc' = "ignored" /\ ~closed))]_vars

YieldOnlySuspended == result[1] = "yield" => pc \in {"loop", "ignored"}
=============================================================================
