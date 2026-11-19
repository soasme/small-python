----------------------------- MODULE ClosureCells -----------------------------
(***************************************************************************)
(* The locals a completed call leaves to the closures it made, as PLS-315  *)
(* 9.2.3 step 3 specifies it: a function call binds big and kept, makes a  *)
(* nested scope that reads kept, or big, or neither (a lambda, a def, a    *)
(* class body or a generator expression), and either returns it or raises, *)
(* the traceback then kept. The outcome is which of big and kept are still *)
(* alive (weak references) once the call has completed.                    *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [scope : {"lambda", "def", "class", "genexpr"}, reads : {"kept", "big", "none"}, ends : {"return", "raise"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* A cell lives on in the closure; a frame object (the traceback's) keeps
\* every local; the call's other locals are released.
Alive(p, name) == p.ends = "raise" \/ p.reads = name
Shown(b) == IF b THEN "alive" ELSE "freed"
Run(p) == "big " \o Shown(Alive(p, "big")) \o " kept " \o Shown(Alive(p, "kept"))

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The kind of nested scope does not matter, only what it reads.
ScopeIndependent == Done => \A s \in {"lambda", "def", "class", "genexpr"} : outcome = Run([program EXCEPT !.scope = s])

\* A returned call keeps nothing its closures do not read.
NothingExtra == Done /\ program.ends = "return" /\ program.reads = "none" => outcome = "big freed kept freed"
=============================================================================
