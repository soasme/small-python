---------------------------- MODULE Generators ----------------------------
(***************************************************************************)
(* The life cycle of a generator or coroutine object driven from outside   *)
(* through next(), send(), throw(), and close(), as The Python Language    *)
(* Reference specifies it (reference/expressions.html#generator-iterator-  *)
(* methods and reference/datamodel.html#coroutine-objects).                *)
(*                                                                         *)
(* The object runs one fixed body, written out in tla_check.py, where each *)
(* step of this spec becomes a Python call; `op` names the call and        *)
(* `result` what it returned or raised:                                    *)
(*                                                                         *)
(*     last, i = None, 0                                                   *)
(*     while i < K:                                                        *)
(*         try:                                                            *)
(*             got = yield (i, last)        # await Y((i, last)) in a      *)
(*         except ValueError:               # coroutine                    *)
(*             got = 'caught'                                              *)
(*         except GeneratorExit:                                           *)
(*             if variant == 'plain': raise                                *)
(*             got = 'exit'                                                *)
(*             yield ('ignored', i)                                        *)
(*         if got == 'stop': return 'early'                                *)
(*         if got == 'reenter':             # resuming itself from inside  *)
(*             try: next(me)                # its own body                 *)
(*             except ValueError: got = 'blocked'                          *)
(*         last, i = got, i + 1                                            *)
(*     return 'done'                                                       *)
(***************************************************************************)
EXTENDS Naturals, Sequences

CONSTANT K          \* iterations of the body's loop

Kinds == {"generator", "coroutine"}
Variants == {"plain", "stubborn"}
Sent == {"None", "go", "stop", "reenter"}       \* "None" is next() itself
Thrown == {"ValueError", "KeyError"}
Ops == {<<"send", v>> : v \in Sent} \cup {<<"throw", e>> : e \in Thrown} \cup {<<"close">>}

\* Where the body is suspended: before its first line, at the loop's yield,
\* at the yield inside the GeneratorExit handler, or finished.
Pcs == {"start", "loop", "ignored", "done"}

VARIABLES kind, variant, pc, i, last, op, result
vars == <<kind, variant, pc, i, last, op, result>>

Results ==
    {<<"yield", n, l>> : n \in 0..K, l \in Sent \cup {"caught", "blocked", "exit"}} \cup
    {<<"stop", v>> : v \in {"None", "done", "early"}} \cup
    {<<"raise", e>> : e \in Thrown \cup {"TypeError", "RuntimeError"}} \cup
    {<<"return", "None">>, <<"init">>}

TypeOK ==
    /\ kind \in Kinds /\ variant \in Variants /\ pc \in Pcs
    /\ i \in 0..K /\ last \in Sent \cup {"caught", "blocked", "exit"}
    /\ op \in Ops \cup {<<"init">>} /\ result \in Results

Init ==
    /\ kind \in Kinds /\ variant \in Variants
    /\ pc = "start" /\ i = 0 /\ last = "None"
    /\ op = <<"init">> /\ result = <<"init">>

(* The body resumes after its loop's yield with `got` bound: it returns,   *)
(* or reaches the yield again with the next iteration's values.            *)
Continue(got) ==
    LET kept == IF got = "reenter" THEN "blocked" ELSE got   \* next(me) raised ValueError
    IN  IF got = "stop" THEN /\ pc' = "done" /\ result' = <<"stop", "early">> /\ UNCHANGED <<i, last>>
        ELSE IF i + 1 < K
             THEN /\ pc' = "loop" /\ i' = i + 1 /\ last' = kept
                  /\ result' = <<"yield", i + 1, kept>>
             ELSE /\ pc' = "done" /\ result' = <<"stop", "done">> /\ UNCHANGED <<i, last>>

Finish(r) == pc' = "done" /\ result' = r /\ UNCHANGED <<i, last>>
Stay(r) == result' = r /\ UNCHANGED <<pc, i, last>>

Send(v) ==
    /\ op' = <<"send", v>>
    /\ CASE pc = "start" /\ v # "None" -> Stay(<<"raise", "TypeError">>)   \* can't send non-None to a just-started generator
         [] pc = "start" -> pc' = "loop" /\ result' = <<"yield", 0, "None">> /\ UNCHANGED <<i, last>>
         [] pc = "loop" -> Continue(v)
         [] pc = "ignored" -> Continue("exit")            \* the sent value is discarded
         [] pc = "done" /\ kind = "generator" -> Stay(<<"stop", "None">>)
         [] pc = "done" -> Stay(<<"raise", "RuntimeError">>)     \* cannot reuse already awaited coroutine

Throw(e) ==
    /\ op' = <<"throw", e>>
    /\ CASE pc = "loop" /\ e = "ValueError" -> Continue("caught")
         [] pc = "done" /\ kind = "coroutine" -> Stay(<<"raise", "RuntimeError">>)  \* cannot reuse already awaited coroutine
         [] OTHER -> Finish(<<"raise", e>>)  \* a just-started body never runs; elsewhere nothing catches e

Close ==
    /\ op' = <<"close">>
    /\ IF pc = "loop" /\ variant = "stubborn"
       THEN pc' = "ignored" /\ result' = <<"raise", "RuntimeError">> /\ UNCHANGED <<i, last>>  \* ignored GeneratorExit
       ELSE Finish(<<"return", "None">>)

Next ==
    /\ UNCHANGED <<kind, variant>>
    /\ \/ \E v \in Sent : Send(v)
       \/ \E e \in Thrown : Throw(e)
       \/ Close

Spec == Init /\ [][(Next)]_vars

-----------------------------------------------------------------------------
(* Properties the Language Reference states.                               *)

\* A finished generator stays finished, whatever is done to it.
DoneIsFinal == [][(pc = "done" => pc' = "done")]_vars

\* Throwing into a just-started generator raises at its start: the body
\* never runs and the object is finished.
ThrowAtStart == [][(pc = "start" /\ op'[1] = "throw" => pc' = "done" /\ result' = <<"raise", op'[2]>>)]_vars

\* close() on a finished or just-started object returns None and finishes it.
CloseFinished == [][(pc \in {"start", "done"} /\ op' = <<"close">> => result' = <<"return", "None">> /\ pc' = "done")]_vars

\* close() either finishes the object or raises RuntimeError because the body
\* yielded again; it never yields a value to the caller.
CloseNeverYields == [][(op' = <<"close">> => result'[1] \in {"return", "raise"} /\
                        (result'[1] = "raise" => result' = <<"raise", "RuntimeError">> /\ pc' = "ignored"))]_vars

\* The body runs at most K iterations, and a value is yielded only while suspended.
Bounded == i < K
YieldOnlySuspended == result[1] = "yield" => pc \in {"loop", "ignored"}

\* Closing again after an ignored GeneratorExit finishes the object, so two
\* close() calls always finish it.
CloseTwice == [][(pc = "ignored" /\ op' = <<"close">> => pc' = "done")]_vars
=============================================================================
