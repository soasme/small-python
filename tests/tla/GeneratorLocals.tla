--------------------------- MODULE GeneratorLocals ---------------------------
(***************************************************************************)
(* When a finished generator's local variables are released, as PLS-315   *)
(* 27.2.4 specifies it: at its end, unless a frame object of it is still  *)
(* referenced, which keeps them until it is released; the generator       *)
(* itself may live on. The frame does not keep the generator reachable.   *)
(*                                                                         *)
(* A program runs                                                          *)
(*                                                                         *)
(*     def g():                                                            *)
(*         local = Noted()          # its __del__ notes the release       *)
(*         yield 1                                                         *)
(*         raise ValueError        # or return, for a "return" ending     *)
(*                                                                         *)
(* after one next(), and ends it: by next() (a "return" or a "raise"      *)
(* ending), by throw(KeyError) ("throw"), or by throw(1), which a yield   *)
(* from's delegate refuses with a TypeError raised at it ("refused").     *)
(* The caller keeps the generator, and may keep the exception it caught   *)
(* (whose traceback holds the frame) or the gi_frame it read before the   *)
(* end. The outcome is whether the local was released at the end, after  *)
(* what was kept is dropped, and whether a weak reference to the          *)
(* generator dies once the generator is dropped while the kept exception  *)
(* lives on.                                                               *)
(***************************************************************************)
EXTENDS Naturals

Programs == [ending : {"return", "raise", "throw", "refused"}, keep_exception : BOOLEAN, keep_frame : BOOLEAN]

VARIABLES program, outcome
vars == <<program, outcome>>

\* Before the program runs; after it, the local is always released.
Pending == [at_end |-> FALSE, after_drop |-> FALSE, generator_dead |-> FALSE]

\* A return raises its StopIteration in the caller, whose traceback holds
\* no frame of the generator.
FrameHeld(p) == p.keep_frame \/ (p.keep_exception /\ p.ending # "return")

Run(p) == [at_end |-> ~FrameHeld(p), after_drop |-> TRUE, generator_dead |-> TRUE]

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome.after_drop

\* Nothing but a frame object keeps a finished generator's locals.
OnlyFramesKeep == Done /\ ~outcome.at_end => FrameHeld(program)
\* No frame keeps the generator reachable.
FrameKeepsNoGenerator == Done => outcome.generator_dead
=============================================================================
