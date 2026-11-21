---------------------------- MODULE ConstantLoads ----------------------------
(* PLS-315 9.7, 27.2, 27.3, 28.2: a retained function or suspended instance
 * keeps its executable code and constants alive. Releasing the source and
 * explicit code references, then collecting during argument evaluation,
 * does not change the value loaded after that call. *)
EXTENDS Naturals

Literals == {"123456789012345678901234567890", "12379813738877118345",
             "1.25", "2.5j", "-0.0", "-123456789012345678901234567890"}
Programs == [literal : Literals, kind : {"function", "generator", "coroutine"}]
VARIABLES program, outcome
vars == <<program, outcome>>

Init == program \in Programs /\ outcome = "pending"
Load == outcome = "pending" /\ outcome' = program.literal /\ UNCHANGED program
Spec == Init /\ [][Load]_vars
Preserved == outcome = "pending" \/ outcome = program.literal
=============================================================================
