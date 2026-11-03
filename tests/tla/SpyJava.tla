------------------------------ MODULE SpyJava ------------------------------
(***************************************************************************)
(* The value lifetimes of the Java binding io.github.soasme.spy           *)
(* (docs/packaging/java.md 3), as Interpreter.java and PyObject.java      *)
(* implement them. TLC checks that after every step:                      *)
(*                                                                         *)
(*  - The engine never runs with a reference the binding has released or *)
(*    a context it has freed, including when a host function calls back  *)
(*    into the interpreter while the engine is in the middle of a call.  *)
(*  - Each reference is released once, while its context is alive, and   *)
(*    only after its PyObject became unreachable.                         *)
(*  - The garbage collector's thread never calls the engine; it only     *)
(*    queues references, which the next call releases.                   *)
(*                                                                         *)
(* The implementation, step by step (names are the Java sources'):       *)
(*                                                                         *)
(*  - The program holds PyObjects. A method of one passes its ptr to the  *)
(*    engine, which borrows it until the call returns; inside, the engine *)
(*    may call a host function, which may use the interpreter again.      *)
(*  - The JVM may find a PyObject unreachable as soon as the program has  *)
(*    no further use of it, even while one of its own methods is still   *)
(*    running, unless the method's reachabilityFence keeps it (with).     *)
(*  - The Cleaner's action, drop, reads ctx and then queues the ptr; it  *)
(*    holds no lock, so close may run between the two.                   *)
(*  - enter, on the interpreter's monitor, throws once ctx is 0 and      *)
(*    otherwise releases every queued ptr.                                *)
(*  - close frees the context and every value in it and clears the       *)
(*    queue; it throws while a host function of the interpreter runs.    *)
(***************************************************************************)
EXTENDS Naturals, Sequences

CONSTANTS Objs,     \* engine values, each wrapped by one PyObject
          Depth     \* the most native calls in progress at once

NoObj == "none"

VARIABLES eng,      \* eng[o]: "none" (not made), "owned", "released", "freed"
          held,     \* the program still uses o's PyObject
          gc,       \* the JVM's view of the PyObject: "reachable", "found", "adding", "done"
          queue,    \* released: ptrs the cleaner queued
          open,     \* ctx # 0
          stack,    \* native calls in progress, innermost last: [obj, cb]
          bad       \* ghost: a release of a value not owned

vars == <<eng, held, gc, queue, open, stack, bad>>

Init == /\ eng = [o \in Objs |-> "none"] /\ held = [o \in Objs |-> FALSE]
        /\ gc = [o \in Objs |-> "reachable"] /\ queue = {} /\ open = TRUE
        /\ stack = <<>> /\ bad = FALSE

\* The program runs: at the top level or inside a host function.
Program == IF stack = <<>> THEN TRUE ELSE stack[Len(stack)].cb
\* The engine runs a call, outside any host function.
Engine == IF stack = <<>> THEN FALSE ELSE ~stack[Len(stack)].cb
Borrowed(o) == \E i \in 1..Len(stack) : stack[i].obj = o

\* enter: throws when closed; otherwise releases the queue.
Drain == /\ eng' = [o \in Objs |-> IF o \in queue THEN "released" ELSE eng[o]]
         /\ bad' = (bad \/ \E o \in queue : eng[o] # "owned")
         /\ queue' = {}

\* A call into the engine: Interpreter's operations borrow nothing, a
\* PyObject's method borrows its ptr.
Call(o) == /\ Program /\ open /\ Len(stack) < Depth
           /\ IF o = NoObj THEN TRUE ELSE held[o]
           /\ Drain
           /\ stack' = Append(stack, [obj |-> o, cb |-> FALSE])
           /\ UNCHANGED <<held, gc, open>>

\* The engine calls a host function, and it returns.
Callback == /\ Engine /\ stack' = [stack EXCEPT ![Len(stack)].cb = TRUE]
            /\ UNCHANGED <<eng, held, gc, queue, open, bad>>
Resume == /\ IF stack = <<>> THEN FALSE ELSE stack[Len(stack)].cb
          /\ stack' = [stack EXCEPT ![Len(stack)].cb = FALSE]
          /\ UNCHANGED <<eng, held, gc, queue, open, bad>>

\* The engine call returns, maybe a new value that wrap gives the program.
Return(o) == /\ Engine /\ open
             /\ stack' = SubSeq(stack, 1, Len(stack) - 1)
             /\ IF o = NoObj THEN UNCHANGED <<eng, held>>
                ELSE /\ eng[o] = "none" /\ eng' = [eng EXCEPT ![o] = "owned"]
                     /\ held' = [held EXCEPT ![o] = TRUE]
             /\ UNCHANGED <<gc, queue, open, bad>>

\* The program no longer uses o: a local goes out of scope, or a temporary
\* such as py.eval(...).call(f) is never mentioned again.
Forget(o) == /\ Program /\ held[o] /\ held' = [held EXCEPT ![o] = FALSE]
             /\ UNCHANGED <<eng, gc, queue, open, stack, bad>>

\* The JVM finds o's PyObject unreachable; with's fence keeps it while
\* one of its methods runs.
Collect(o) == /\ eng[o] # "none" /\ gc[o] = "reachable" /\ ~held[o] /\ ~Borrowed(o)
              /\ gc' = [gc EXCEPT ![o] = "found"]
              /\ UNCHANGED <<eng, held, queue, open, stack, bad>>

\* drop, on the Cleaner's thread: if (ctx != 0) released.add(v).
Check(o) == /\ gc[o] = "found" /\ gc' = [gc EXCEPT ![o] = IF open THEN "adding" ELSE "done"]
            /\ UNCHANGED <<eng, held, queue, open, stack, bad>>
Add(o) == /\ gc[o] = "adding" /\ gc' = [gc EXCEPT ![o] = "done"] /\ queue' = queue \cup {o}
          /\ UNCHANGED <<eng, held, open, stack, bad>>

\* close, refused inside a host function.
Close == /\ Program /\ open /\ stack = <<>>
         /\ open' = FALSE /\ queue' = {}
         /\ eng' = [o \in Objs |-> IF eng[o] = "owned" THEN "freed" ELSE eng[o]]
         /\ UNCHANGED <<held, gc, stack, bad>>

Next == \/ Callback \/ Resume \/ Close
        \/ \E o \in Objs \cup {NoObj} : Call(o) \/ Return(o)
        \/ \E o \in Objs : Forget(o) \/ Collect(o) \/ Check(o) \/ Add(o)

Spec == Init /\ [][Next]_vars

TypeOK == /\ eng \in [Objs -> {"none", "owned", "released", "freed"}]
          /\ held \in [Objs -> BOOLEAN]
          /\ gc \in [Objs -> {"reachable", "found", "adding", "done"}]
          /\ queue \subseteq Objs /\ open \in BOOLEAN /\ Len(stack) <= Depth

\* What the engine is running with is alive.
BorrowedLive == \A i \in 1..Len(stack) :
                    /\ open
                    /\ stack[i].obj # NoObj => eng[stack[i].obj] = "owned"
\* What the program can still use is alive while the interpreter is open.
HeldLive == \A o \in Objs : held[o] /\ open => eng[o] = "owned"
\* Released once, while the context lived, and only when unreachable.
ReleasedOnce == ~bad
ReleasedUnreachable == \A o \in Objs : eng[o] = "released" => gc[o] = "done"
=============================================================================
