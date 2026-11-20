--------------------------- MODULE DeadAwaitClose ---------------------------
(***************************************************************************)
(* The close of a dead asynchronous generator or coroutine suspended in an *)
(* await of a generator-based coroutine, as PLS-315 27.2.4 and 27.5        *)
(* specify it. The awaited one is live, or was closed (ended) before the   *)
(* other dies; the other dies when dropped or as part of a cycle a         *)
(* collection reclaims. Its close first closes a live awaited one, which   *)
(* logs "inner", then raises GeneratorExit at the await, whose handler     *)
(* logs "exit" and then finishes, raises KeyError, or yields (awaits, for  *)
(* a coroutine), which is a RuntimeError the close reports. An enclosing   *)
(* finally logs "done" unless the close was ignored so: the frame is then *)
(* cleared without running it. The outcome is the log.                     *)
(***************************************************************************)
Programs == [kind : {"asyncgen", "coroutine"}, inner : {"live", "ended"}, death : {"drop", "cycle"},
             handler : {"finish", "raise", "yield"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Log(p) == CASE p.inner = "live" /\ p.handler = "yield" -> "inner exit"
            [] p.inner = "live" -> "inner exit done"
            [] p.handler = "yield" -> "exit"
            [] OTHER -> "exit done"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ UNCHANGED program /\ outcome' = Log(program)
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
\* How it dies never changes what its close runs.
DeathUnseen == outcome # Pending =>
    \A q \in Programs : (q.kind = program.kind /\ q.inner = program.inner /\ q.handler = program.handler) => Log(q) = outcome
=============================================================================
