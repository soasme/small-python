------------------------------ MODULE SpyRust ------------------------------
(***************************************************************************)
(* The value lifetimes of the small-python crate (docs/packaging/rust.md),*)
(* as lib.rs and value.rs implement them. TLC checks that after every    *)
(* step:                                                                   *)
(*                                                                         *)
(*  - The engine never runs with a reference the crate has released or a *)
(*    context it has freed, including when a host function calls back     *)
(*    into the runtime while the engine is in the middle of a call.       *)
(*  - Each reference is released once, while its context is alive.       *)
(*                                                                         *)
(* Here the borrow checker does the work Java's and Go's collectors      *)
(* cannot. Its rules are the guards below:                                *)
(*                                                                         *)
(*  - A Value<'rt> is released by its Drop, at once. A method takes       *)
(*    &self, so the value cannot be dropped while the engine borrows it  *)
(*    for that method; Clone retains a second reference.                  *)
(*  - Every Value borrows its Runtime, so the Runtime's Drop, which frees *)
(*    the context, comes after the last value's. A host function receives *)
(*    a non-owning &Runtime (Runtime::borrowed), which it cannot drop.     *)
(*  - Host functions, module initializers, output, loader, and policy run *)
(*    under guard or catch_unwind, so a panic, such as a RefCell re-borrow *)
(*    of a hook, raises in the engine and never unwinds into C.           *)
(***************************************************************************)
EXTENDS Naturals, Sequences

CONSTANTS Objs,     \* references, each owned by one Value
          Depth     \* the most engine calls in progress at once

NoObj == "none"

VARIABLES eng,      \* eng[o]: "none" (not made), "owned", "released"
          open,     \* the Runtime is not dropped
          stack,    \* engine calls in progress, innermost last: [obj, cb]
          bad       \* ghost: a release of a reference not owned

vars == <<eng, open, stack, bad>>

Init == /\ eng = [o \in Objs |-> "none"] /\ open = TRUE /\ stack = <<>> /\ bad = FALSE

Program == IF stack = <<>> THEN TRUE ELSE stack[Len(stack)].cb
Engine == IF stack = <<>> THEN FALSE ELSE ~stack[Len(stack)].cb
Borrowed(o) == \E i \in 1..Len(stack) : stack[i].obj = o
Live == {o \in Objs : eng[o] = "owned"}

\* A call into the engine: the Runtime's operations borrow nothing, a
\* Value's method borrows its reference.
Call(o) == /\ Program /\ open /\ Len(stack) < Depth
           /\ IF o = NoObj THEN TRUE ELSE eng[o] = "owned"
           /\ stack' = Append(stack, [obj |-> o, cb |-> FALSE])
           /\ UNCHANGED <<eng, open, bad>>

Callback == /\ Engine /\ stack' = [stack EXCEPT ![Len(stack)].cb = TRUE]
            /\ UNCHANGED <<eng, open, bad>>
Resume == /\ IF stack = <<>> THEN FALSE ELSE stack[Len(stack)].cb
          /\ stack' = [stack EXCEPT ![Len(stack)].cb = FALSE]
          /\ UNCHANGED <<eng, open, bad>>

\* The call returns, maybe a new owned reference (wrap, or Clone).
Return(o) == /\ Engine /\ stack' = SubSeq(stack, 1, Len(stack) - 1)
             /\ IF o = NoObj THEN UNCHANGED eng
                ELSE eng[o] = "none" /\ eng' = [eng EXCEPT ![o] = "owned"]
             /\ UNCHANGED <<open, bad>>

\* Drop for Value: spy_release, at once; not while a method borrows it.
Drop(o) == /\ Program /\ eng[o] = "owned" /\ ~Borrowed(o)
           /\ bad' = (bad \/ ~open)
           /\ eng' = [eng EXCEPT ![o] = "released"]
           /\ UNCHANGED <<open, stack>>

\* Drop for Runtime: only by its owner at the top level, after every Value.
Close == /\ open /\ stack = <<>> /\ Live = {}
         /\ open' = FALSE
         /\ UNCHANGED <<eng, stack, bad>>

Next == \/ Callback \/ Resume \/ Close
        \/ \E o \in Objs \cup {NoObj} : Call(o) \/ Return(o)
        \/ \E o \in Objs : Drop(o)

Spec == Init /\ [][Next]_vars

TypeOK == /\ eng \in [Objs -> {"none", "owned", "released"}]
          /\ open \in BOOLEAN /\ Len(stack) <= Depth

\* What the engine is running with is alive.
BorrowedLive == \A i \in 1..Len(stack) :
                    /\ open
                    /\ stack[i].obj # NoObj => eng[stack[i].obj] = "owned"
\* No Value outlives its Runtime, and each is released once, while it lived.
NoneOutlive == ~open => Live = {}
ReleasedOnce == ~bad
=============================================================================
