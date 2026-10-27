----------------------------- MODULE YieldFrom -----------------------------
(***************************************************************************)
(* Delegation to a subgenerator with yield from, as The Python Language    *)
(* Reference (reference/expressions.html#yield-expressions) and PEP 380    *)
(* specify it, driven from outside through next(), send(), throw(), and    *)
(* close():                                                                *)
(*                                                                         *)
(*     def inner():                                                        *)
(*         last, i = 'None', 0                                             *)
(*         try:                                                            *)
(*             while i < 2:                                                *)
(*                 try:                                                    *)
(*                     got = yield ('in', str(i), last)                    *)
(*                 except ValueError:                                      *)
(*                     got = 'caught'                                      *)
(*                 if got == 'stop': return 'early'                        *)
(*                 last, i = str(got), i + 1                               *)
(*             return 'done'                                               *)
(*         finally:                                                        *)
(*             log.append('inner')                                         *)
(*                                                                         *)
(*     def outer():                                                        *)
(*         try:                                                            *)
(*             r = yield from inner()                                      *)
(*         except KeyError:                                                *)
(*             r = 'keyerror'                                              *)
(*         yield ('after', r, '-')                                         *)
(*         return 'end'                                                    *)
(*                                                                         *)
(* `result` is what the call on outer returned or raised; `finalized`     *)
(* whether inner's finally clause has run.                                 *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Sent == {"None", "go", "stop"}
Thrown == {"ValueError", "KeyError"}
Ops == {<<"send", v>> : v \in Sent} \cup {<<"throw", e>> : e \in Thrown} \cup {<<"close">>}
Pcs == {"start", "inner", "after", "done"}
Lasts == {"None", "go", "caught"}

VARIABLES pc, i, last, finalized, op, result
vars == <<pc, i, last, finalized, op, result>>

Results ==
    {<<"yield", "in", n, l>> : n \in {"0", "1"}, l \in Lasts} \cup
    {<<"yield", "after", r, "-">> : r \in {"done", "early", "keyerror"}} \cup
    {<<"stop", v, "-", "-">> : v \in {"None", "end"}} \cup
    {<<"raise", e, "-", "-">> : e \in Thrown \cup {"TypeError"}} \cup
    {<<"return", "None", "-", "-">>, <<"init", "-", "-", "-">>}

TypeOK == pc \in Pcs /\ i \in 0..1 /\ last \in Lasts /\ finalized \in BOOLEAN
          /\ op \in Ops \cup {<<"init">>} /\ result \in Results

Init == pc = "start" /\ i = 0 /\ last = "None" /\ finalized = FALSE
        /\ op = <<"init">> /\ result = <<"init", "-", "-", "-">>

Str(n) == IF n = 0 THEN "0" ELSE "1"
Stay(r) == result' = r /\ UNCHANGED <<pc, i, last, finalized>>
Finish(r) == pc' = "done" /\ result' = r /\ UNCHANGED <<i, last, finalized>>

\* inner returns r: its finally clause runs, and the value of yield from
\* is r, which outer yields.
Returned(r) == pc' = "after" /\ finalized' = TRUE /\ result' = <<"yield", "after", r, "-">> /\ UNCHANGED <<i, last>>

\* inner resumes with got bound.
Resume(got) ==
    IF got = "stop" THEN Returned("early")
    ELSE IF i = 0 THEN i' = 1 /\ last' = got /\ result' = <<"yield", "in", "1", got>> /\ UNCHANGED <<pc, finalized>>
    ELSE Returned("done")

Send(v) ==
    /\ op' = <<"send", v>>
    /\ CASE pc = "start" /\ v # "None" -> Stay(<<"raise", "TypeError", "-", "-">>)
         [] pc = "start" -> pc' = "inner" /\ result' = <<"yield", "in", "0", "None">> /\ UNCHANGED <<i, last, finalized>>
         \* Values sent while delegating go to inner.
         [] pc = "inner" -> Resume(v)
         [] pc = "after" -> Finish(<<"stop", "end", "-", "-">>)
         [] pc = "done" -> Stay(<<"stop", "None", "-", "-">>)

Throw(e) ==
    /\ op' = <<"throw", e>>
    /\ CASE pc = "inner" /\ e = "ValueError" -> Resume("caught")     \* thrown into inner, which catches it
         \* inner lets it propagate (running its finally); it is raised in
         \* outer at the yield from, where outer catches it.
         [] pc = "inner" -> Returned("keyerror")
         [] OTHER -> Finish(<<"raise", e, "-", "-">>)

\* close() closes inner first, then raises GeneratorExit in outer.
Close ==
    /\ op' = <<"close">>
    /\ result' = <<"return", "None", "-", "-">>
    /\ pc' = "done"
    /\ finalized' = (finalized \/ pc = "inner")
    /\ UNCHANGED <<i, last>>

Next == Close \/ \E v \in Sent : Send(v) \/ \E e \in Thrown : Throw(e)
Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
\* While delegating, the caller sees exactly what inner yields.
Transparent == pc = "inner" /\ result[1] = "yield" => result[2] = "in"

\* Once outer is past the yield from, inner has finished.
InnerFinished == pc = "after" => finalized

\* inner's finally clause runs at most once, and never while delegating.
FinallyOnce == [][(finalized => finalized')]_vars
NotWhileDelegating == pc = "inner" => ~finalized
=============================================================================
