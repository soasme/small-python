----------------------------- MODULE Iteration -----------------------------
(***************************************************************************)
(* The for statement and the iteration protocol, as The Python Language    *)
(* Reference specifies them (reference/compound_stmts.html#the-for-        *)
(* statement and reference/datamodel.html#object.__iter__), for            *)
(*                                                                         *)
(*     for x in S():                                                       *)
(*         if x == brk: log.append('break'); break                         *)
(*         if x == skip: log.append('skip'); continue                      *)
(*         log.append(str(x))                                              *)
(*     else:                                                               *)
(*         log.append('else')                                              *)
(*                                                                         *)
(* where S produces 0, 1, ..., n - 1 through                               *)
(*                                                                         *)
(*     iter       __iter__ returning an iterator with __next__             *)
(*     getitem    only __getitem__, raising IndexError at n                *)
(*     none       neither (not iterable)                                   *)
(*     bad        __iter__ returning 1, which is not an iterator           *)
(*     blocked    __iter__ = None with __getitem__ (explicitly not        *)
(*                iterable)                                                *)
(*                                                                         *)
(* brk and skip are an item or -1. The outcome is the log and the          *)
(* exception, if any.                                                      *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Protocols == {"iter", "getitem", "none", "bad", "blocked"}
Programs == [protocol : Protocols, n : 0..2, brk : -1..1, skip : -1..1]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<<<>>, "pending">>

Loop(p) ==
    LET RECURSIVE From(_)
        From(x) == IF x = p.n THEN <<"else">>                       \* exhausted: the else clause runs
                   ELSE IF x = p.brk THEN <<"break">>                \* break skips it
                   ELSE IF x = p.skip THEN <<"skip">> \o From(x + 1)
                   ELSE <<ToString(x)>> \o From(x + 1)
    IN  IF p.protocol \in {"iter", "getitem"} THEN <<From(0), "ok">> ELSE <<<<>>, "TypeError">>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Loop(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
Log == outcome[1]
Logged(x) == \E i \in DOMAIN Log : Log[i] = x

\* The else clause runs exactly when the loop was not left by break.
ElseUnlessBreak == Done /\ outcome[2] = "ok" => (Logged("else") <=> ~Logged("break"))

\* The old sequence protocol iterates exactly like the iterator protocol.
SameProtocols == Done /\ program.protocol = "getitem" => outcome = Loop([program EXCEPT !.protocol = "iter"])

\* Not iterable means the body never runs.
NotIterable == Done /\ outcome[2] = "TypeError" => Log = <<>>
=============================================================================
