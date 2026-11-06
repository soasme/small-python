------------------------------ MODULE SpyPause ------------------------------
(***************************************************************************)
(* Pausing a call (docs/metering.md 3.8), as spy.c's halt, run_steps,     *)
(* module_end, spy_resume and spy_context_free do it. A program is a      *)
(* sequence of machine steps and native calls; a native call spends Cost  *)
(* steps one at a time with no point at which the call can pause, as      *)
(* sorted() calling a key function does.                                  *)
(*                                                                         *)
(* With pausing set, the first spent budget of an outermost call makes a  *)
(* pause due and refills the budget; the call pauses at its next machine  *)
(* step, before running it. A budget spent while a pause is due stops the *)
(* call. spy_resume refills the budget and runs on from the paused step;  *)
(* freeing the context stops a paused call.                               *)
(*                                                                         *)
(* TLC checks that after every step:                                      *)
(*                                                                         *)
(*  - A call pauses only when a pause is due, and never inside a native   *)
(*    call: then nothing but the machines holds its state.                *)
(*  - No step is lost or run twice: a call that ends ran each step of the *)
(*    program once, however often it paused.                              *)
(*  - An outermost call, or a resume, spends at most two budgets.         *)
(*  - A paused call stays paused until it is resumed or freed.            *)
(***************************************************************************)
EXTENDS Naturals, Sequences

CONSTANTS Budget,   \* the largest step budget an outermost call gets
          Cost      \* the steps of a native call

\* The program: its steps and native calls, back to back and apart.
Program == <<"step", "native", "step", "step", "native", "native", "step">>

VARIABLES state,    \* "idle", "running", "paused", "stopped", "done" or "freed"
          pc,       \* the next instruction of the call
          inside,   \* steps a running native call has spent, or 0
          fuel,     \* steps left in the budget
          due,      \* a pause is due
          ran,      \* ran[i]: times instruction i ran
          spent,    \* steps spent since the outermost call or the resume
          limit     \* the step limit the host set

vars == <<state, pc, inside, fuel, due, ran, spent, limit>>

Init == /\ state = "idle" /\ pc = 1 /\ inside = 0 /\ fuel = Budget /\ due = FALSE
        /\ ran = [i \in 1..Len(Program) |-> 0] /\ spent = 0 /\ limit = Budget

\* spend(1): a spent budget makes a pause due once, then stops the call.
Spend == IF fuel > 0 THEN /\ fuel' = fuel - 1 /\ UNCHANGED <<due, state>>
         ELSE IF ~due THEN /\ due' = TRUE /\ fuel' = limit - 1 /\ UNCHANGED state
         ELSE /\ state' = "stopped" /\ UNCHANGED <<due, fuel>>

Start == /\ state = "idle" /\ state' = "running"
         /\ \E b \in 1..Budget : limit' = b /\ fuel' = b
         /\ UNCHANGED <<pc, inside, due, ran, spent>>

\* A machine step: the pause point first, then the step, which spends one.
Step == /\ state = "running" /\ inside = 0 /\ pc <= Len(Program) /\ Program[pc] = "step"
        /\ IF due THEN /\ state' = "paused" /\ UNCHANGED <<pc, fuel, due, ran, spent>>
           ELSE /\ Spend
                /\ spent' = IF state' = "stopped" THEN spent ELSE spent + 1
                /\ IF state' = "running"
                   THEN /\ ran' = [ran EXCEPT ![pc] = @ + 1] /\ pc' = pc + 1
                   ELSE UNCHANGED <<ran, pc>>
        /\ UNCHANGED <<inside, limit>>

\* A native call: its pause point is before it; inside, it only spends.
Native == /\ state = "running" /\ pc <= Len(Program) /\ Program[pc] = "native"
          /\ UNCHANGED limit
          /\ IF inside = 0 /\ due THEN /\ state' = "paused" /\ UNCHANGED <<pc, inside, fuel, due, ran, spent>>
             ELSE /\ Spend
                  /\ spent' = IF state' = "stopped" THEN spent ELSE spent + 1
                  /\ IF state' = "stopped" THEN UNCHANGED <<inside, ran, pc>>
                     ELSE IF inside + 1 = Cost
                     THEN /\ inside' = 0 /\ ran' = [ran EXCEPT ![pc] = @ + 1] /\ pc' = pc + 1
                     ELSE /\ inside' = inside + 1 /\ UNCHANGED <<ran, pc>>

End == /\ state = "running" /\ pc > Len(Program) /\ state' = "done"
       /\ UNCHANGED <<pc, inside, fuel, due, ran, spent, limit>>

\* spy_resume: a fresh budget, of any limit the host set meanwhile, no
\* pause due, the same step next.
Resume == /\ state = "paused" /\ state' = "running"
          /\ \E b \in 1..Budget : limit' = b /\ fuel' = b
          /\ due' = FALSE /\ spent' = 0
          /\ UNCHANGED <<pc, inside, ran>>

\* spy_context_free stops the paused call, which unwinds running no step.
Free == /\ state = "paused" /\ state' = "freed"
        /\ UNCHANGED <<pc, inside, fuel, due, ran, spent, limit>>

Next == Start \/ Step \/ Native \/ End \/ Resume \/ Free

Spec == Init /\ [][Next]_vars

TypeOK == /\ state \in {"idle", "running", "paused", "stopped", "done", "freed"}
          /\ pc \in 1..Len(Program) + 1 /\ inside \in 0..Cost /\ fuel \in 0..limit

\* A pause is due when taken, and never inside a native call.
PausesAtSteps == state = "paused" => (due /\ inside = 0)
\* Each instruction runs at most once, and a call that ends ran them all.
EachStepOnce == /\ \A i \in 1..Len(Program) : ran[i] <= 1
                /\ \A i \in 1..Len(Program) : i < pc => ran[i] = 1
                /\ state = "done" => \A i \in 1..Len(Program) : ran[i] = 1
\* Two budgets bound what an outermost call or a resume spends.
Bounded == spent <= 2 * limit
=============================================================================
