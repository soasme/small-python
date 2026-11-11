------------------------------- MODULE SpyGC -------------------------------
(***************************************************************************)
(* spy's memory manager, as spy.c implements it, run in lockstep with the  *)
(* language semantics of GC.tla. TLC checks that after every step both     *)
(* have the same objects alive, the same roots and slots, the same         *)
(* finalized objects, and made the same __del__ and close calls, that a    *)
(* weak reference answers exactly while its object is alive to Python, and *)
(* that spy's internal bookkeeping stays sound.                            *)
(*                                                                         *)
(* The implementation, step by step (function names are spy.c's):          *)
(*                                                                         *)
(*  - Every object carries a reference count, `refs`. spy_release drops    *)
(*    one; at zero, finalize_later queues an object whose __del__ or close *)
(*    has not run, keeping it alive with the queue's own reference         *)
(*    (finalize_push, which allocates nothing). A closed generator whose   *)
(*    frame something else holds is handed to that frame (frame_take): the *)
(*    frame then holds it, its weak references die, and it is gone to      *)
(*    Python. Any other object is freed and releases its slots.            *)
(*  - A generator holds its frame from g.gi_frame until it dies; the frame *)
(*    refers back to it without a count.                                   *)
(*  - At the next statement boundary (tick_full) the queued finalizers     *)
(*    run: all of them in C (weak_callbacks), or on the machine one at a   *)
(*    time (finalizer_call, finalized, finalize_close), the boundary       *)
(*    ticking again after each. Each releases the queue's reference after  *)
(*    its call; whatever that queued goes ahead of the objects that were   *)
(*    already waiting (finalize_ahead).                                    *)
(*  - collect_once finds garbage by trial deletion: a count minus the      *)
(*    references from other objects leaves the external ones (roots and    *)
(*    the queue); objects with any, and all they reach, are live. Dead     *)
(*    objects awaiting a finalizer are queued and kept with all they       *)
(*    reach, and a closed generator whose frame is kept is handed to it;   *)
(*    the rest is freed, after their references into live objects are      *)
(*    dropped (release_live_edge) without recursion. Its work arrays are   *)
(*    allocated, and a pass whose allocation fails does nothing.           *)
(*  - spy_collect repeats collect_once after running the queue until no    *)
(*    finalizer is pending.                                                *)
(*  - Automatic collection: an allocation that takes a new pool (pool_new, *)
(*    a choice here, also inside a finalizer) makes a collection due once  *)
(*    the listed values exceed the last collection's survivors by          *)
(*    SPY_LIMIT_COLLECTION and memory has doubled; every object here is    *)
(*    listed, and objects stand for memory. A collection lifts the memory  *)
(*    bound while it runs. A boundary collects when one is due, unless     *)
(*    finalizers wait (finalizers_wait: a boundary inside a __del__ or a   *)
(*    close), and then before it runs the queue. A limit of zero never     *)
(*    collects automatically.                                              *)
(*    To the language, such a collection is a gc.collect() the host made   *)
(*    after the statement (9.7 leaves its time to the implementation).     *)
(*                                                                         *)
(* Allocation failure: collect_once's arrays are the only allocation that  *)
(* can fail on these paths. A collection with a failed pass may leave      *)
(* finalized garbage for a later one, which the language model does not    *)
(* describe; from then on `failed` holds, the language model stops, and    *)
(* spy alone is checked: soundness, exact counts, weak references, and     *)
(* that a later collection reclaims every unreachable object.              *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

CONSTANT Obj
VARIABLES spec, impl, op

G == INSTANCE GC WITH alive <- spec.alive, root <- spec.root, ref <- spec.ref,
                      finalized <- spec.finalized, out <- spec.log

None == G!None
Slots == G!Slots
Things == G!Things
Never == Cardinality(Things) + 1 \* SIZE_MAX: no heap exceeds it
Limits == 0..2                   \* SPY_LIMIT_COLLECTION, chosen at the start
Grows == {{}, {1}}               \* whether a step's first finalizer takes a new pool
Fails == {"none", "first", "repeat"} \* which passes of a collection fail to allocate

\* spy's heap: GC.tla's fields plus each object's reference count, the
\* pending stack of spy_release, the queue of objects awaiting a finalizer,
\* the generators their frames hold, the objects weak references still
\* reach, and a flag raised when the code would touch freed memory or free
\* an object something still refers to.
Heap == [alive : SUBSET Things, root : [G!Roots -> Things \cup {None}], ref : [Things -> [Slots -> Things \cup {None}]],
         finalized : SUBSET Obj, log : Seq(Obj), refs : [Things -> Nat], pending : Seq(Things),
         queue : Seq(Obj), taken : SUBSET {"g"}, weak : SUBSET Obj, broken : BOOLEAN, limit : Limits,
         collectListed : Nat, collectMemory : Nat, due : BOOLEAN, collected : BOOLEAN, failed : BOOLEAN]

\* The references spy counts: GC.tla's, and a frame's to the generator it holds.
Owned(s, o) == IF o \in s.taken /\ "f" \in s.alive THEN 1 ELSE 0
Count(s, o) == G!RC(s, o) + Owned(s, o)
Targets(s, set) == G!Targets(s, set) \cup (IF "f" \in set THEN s.taken ELSE {})
Closure(s, set) ==
    LET RECURSIVE From(_)
        From(x) == LET more == x \cup Targets(s, x) IN IF more = x THEN x ELSE From(more)
    IN From(set)
Reach(s) == Closure(s, {s.root[r] : r \in G!Roots} \ {None})

Retain(s, o) == IF o = None THEN s ELSE [s EXCEPT !.refs[o] = @ + 1]

\* release_edge: one reference fewer; an object left with none is pushed on
\* the pending stack.
Drop(s, o) ==
    IF o = None THEN s
    ELSE IF o \notin s.alive \/ s.refs[o] = 0 THEN [s EXCEPT !.broken = TRUE]     \* use after free
    ELSE IF s.refs[o] = 1 THEN [s EXCEPT !.refs[o] = 0, !.pending = Append(@, o)]
    ELSE [s EXCEPT !.refs[o] = @ - 1]

\* frame_take: the closed generator g, whose frame something else holds,
\* lets go of the frame, which holds g instead; g's weak references die.
Take(s) == [s EXCEPT !.taken = {"g"}, !.refs["g"] = @ + 1, !.ref["g"]["ref"] = None,
                     !.refs["f"] = @ - 1, !.weak = @ \ {"g"}]

\* The pending loop of spy_release, last in first out: finalize_later queues
\* an object whose finalizer has not run, keeping it with the queue's
\* reference, or hands a closed generator to its frame; any other is freed,
\* dropping its slots in their order (the constructor sets ref, then other)
\* and, for a frame, the generator it holds.
RECURSIVE Drain(_)
Drain(s) ==
    IF s.pending = <<>> THEN s
    ELSE LET o == s.pending[Len(s.pending)]
             t == [s EXCEPT !.pending = SubSeq(@, 1, Len(@) - 1)]
         IN  IF o \in Obj /\ o \notin t.finalized
             THEN Drain([t EXCEPT !.refs[o] = 1, !.queue = Append(@, o), !.finalized = @ \cup {o}])
             ELSE IF o = "g" /\ t.ref["g"]["ref"] = "f" /\ t.refs["f"] > 1
             THEN Drain(Take(t))
             ELSE LET freed == [t EXCEPT !.alive = @ \ {o}, !.finalized = @ \ {o}, !.ref[o] = G!Empty,
                                         !.weak = @ \ {o}, !.taken = @ \ {o}]
                      slots == Drop(Drop(freed, t.ref[o]["ref"]), t.ref[o]["other"])
                  IN  Drain(IF o = "f" /\ "g" \in t.taken THEN Drop(slots, "g") ELSE slots)

\* spy_release.
Release(s, o) == Drain(Drop(s, o))

\* An assignment: the new value is retained before the old one is released.
Store(s, write(_, _), old, new) == Release(write(Retain(s, new), new), old)

\* pool_new, when an allocation takes a new pool.
Grow(s) ==
    LET live == Cardinality(s.alive)
    IN  IF live > s.collectListed /\ live > s.collectMemory THEN [s EXCEPT !.due = TRUE] ELSE s

\* One finalizer, first in the queue: __del__ (p's stores itself in
\* `saved`) or close; it may allocate (grow); a boundary inside it neither
\* collects nor runs the queue, since finalizers wait. Then the queue's
\* reference is released, and whatever that queued goes ahead of the
\* objects that were already waiting.
RunOne(s, grow) ==
    LET self == Head(s.queue)
        t == [s EXCEPT !.queue = Tail(@), !.log = Append(@, self)]
        u == IF self = "p"
             THEN Store(t, LAMBDA h, v : [h EXCEPT !.root["saved"] = v], t.root["saved"], "p")
             ELSE t
        w == Release(IF Len(t.log) \in grow THEN Grow(u) ELSE u, self)
        waiting == Len(t.queue)
    IN  [w EXCEPT !.queue = SubSeq(@, waiting + 1, Len(@)) \o SubSeq(@, 1, waiting)]

\* weak_callbacks.
RECURSIVE Callbacks(_, _)
Callbacks(s, grow) == IF s.queue = <<>> THEN s ELSE Callbacks(RunOne(s, grow), grow)

\* collect_once; with fail, its allocation fails and it does nothing.
CollectOnce(s, fail) ==
    LET internal(o) == Cardinality({e \in s.alive \X Slots : s.ref[e[1]][e[2]] = o}) + Owned(s, o)
        live == Closure(s, {o \in s.alive : s.refs[o] - internal(o) > 0})
        waiting == {o \in (s.alive \ live) \cap Obj : o \notin s.finalized}
        marked == Closure(s, live \cup waiting)
        take == "g" \in s.alive \ marked /\ s.ref["g"]["ref"] = "f" /\ "f" \in marked
        t == IF take THEN Take(s) ELSE s
        kept == IF take THEN marked \cup {"g"} ELSE marked
        dead == s.alive \ kept
        from(o) == Cardinality({e \in dead \X Slots : t.ref[e[1]][e[2]] = o}) +
                   (IF o \in t.taken /\ "f" \in dead THEN 1 ELSE 0)
        refs == [o \in Things |-> IF o \in kept
                                  THEN t.refs[o] + (IF o \in waiting THEN 1 ELSE 0) - from(o)
                                  ELSE 0]
    IN  IF fail THEN [s EXCEPT !.failed = TRUE]
        ELSE [t EXCEPT !.refs = refs, !.finalized = (@ \cup waiting) \ dead,
                       !.queue = @ \o SelectSeq(G!Order, LAMBDA o : o \in waiting),
                       !.alive = @ \ dead, !.ref = [q \in Things |-> IF q \in dead THEN G!Empty ELSE @[q]],
                       !.weak = @ \ dead, !.taken = @ \ dead,
                       !.broken = @ \/ \E o \in kept : refs[o] = 0]

\* The repetition of collect, after its first collect_once.
RECURSIVE Repeat(_, _)
Repeat(s, fail) == IF s.queue = <<>> THEN s ELSE Repeat(CollectOnce(Callbacks(s, {}), fail = "repeat"), fail)

\* schedule_collection.
Schedule(s) ==
    LET live == Cardinality(s.alive)
    IN  [s EXCEPT !.due = FALSE, !.collectListed = IF s.limit = 0 THEN Never ELSE live + s.limit,
                  !.collectMemory = 2 * live]

\* collect, as spy_collect and the automatic collection run it.
Collect(s, fail) == Schedule(Repeat(CollectOnce([s EXCEPT !.collectMemory = Never], fail = "first"), fail))

\* tick_full, at the boundary after a statement and again whenever the
\* machine ran a finalizer: it collects when due, else runs the queue, on
\* the machine one finalizer at a time or in C all of them; `collected`
\* records whether it collected. After the C run, the tick before the next
\* statement collects if a finalizer made a collection due.
RECURSIVE Tick(_, _, _, _)
Tick(s, machine, grow, fail) ==
    IF s.due THEN Tick([Collect(s, fail) EXCEPT !.collected = TRUE], machine, grow, fail)
    ELSE IF s.queue = <<>> THEN s
    ELSE IF machine THEN Tick(RunOne(s, grow), machine, grow, fail)
    ELSE Tick(Callbacks(s, grow), machine, grow, fail)

\* g.gi_frame: the frame g holds, made on first use.
Frame(s, v, pooled) ==
    IF s.ref["g"]["ref"] = "f"
    THEN Store(s, LAMBDA h, w : [h EXCEPT !.root[v] = w], s.root[v], "f")
    ELSE LET born == [s EXCEPT !.alive = @ \cup {"f"}, !.ref["f"] = G!Empty, !.refs["f"] = 1]
             made == IF pooled THEN Grow(born) ELSE born
             held == [Retain(made, "f") EXCEPT !.ref["g"]["ref"] = "f"]
         IN  Release(Store(held, LAMBDA h, w : [h EXCEPT !.root[v] = w], s.root[v], "f"), "f")

\* Each step is one statement; the boundary after it collects or runs the queue.
Apply(s, step, pooled, machine, grow, fail) ==
    LET Boundary(t) == Tick(t, machine, grow, fail)
    IN
    CASE step[1] = "new" ->
            LET o == step[3]
                born == [s EXCEPT !.alive = @ \cup {o}, !.ref[o] = G!Empty, !.refs[o] = 1, !.finalized = @ \ {o},
                                  !.weak = @ \cup {o}]
                made == IF pooled THEN Grow(born) ELSE born
                stored == Store(made, LAMBDA h, v : [h EXCEPT !.root[step[2]] = v], s.root[step[2]], o)
            IN  Boundary(Release(stored, o))          \* the constructor's own reference
      [] step[1] = "link" ->
            LET q == s.root[step[2]]
                f == step[3]
            IN  Boundary(Store(s, LAMBDA h, v : [h EXCEPT !.ref[q][f] = v], s.ref[q][f], s.root[step[4]]))
      [] step[1] = "load" ->
            Boundary(Store(s, LAMBDA h, v : [h EXCEPT !.root[step[2]] = v], s.root[step[2]],
                           s.ref[s.root[step[3]]][step[4]]))
      [] step[1] = "frame" -> Boundary(Frame(s, step[2], pooled))
      [] step[1] = "del" ->
            Boundary(Store(s, LAMBDA h, v : [h EXCEPT !.root[step[2]] = v], s.root[step[2]], None))
      [] step[1] = "collect" -> Collect(s, fail)

Blank == [alive |-> {}, root |-> [r \in G!Roots |-> None], ref |-> [o \in Things |-> G!Empty],
          finalized |-> {}, log |-> <<>>]

Init ==
    /\ spec = Blank
    /\ \E limit \in Limits : impl = Schedule([alive |-> {}, root |-> Blank.root, ref |-> Blank.ref,
               finalized |-> {}, log |-> <<>>, refs |-> [o \in Things |-> 0], pending |-> <<>>,
               queue |-> <<>>, taken |-> {}, weak |-> {}, broken |-> FALSE, limit |-> limit, collectListed |-> Never,
               collectMemory |-> 0, due |-> FALSE, collected |-> FALSE, failed |-> FALSE])
    /\ op = <<"init">>

\* The heaps a step can leave, its choices each offered only where it can
\* matter: the finalizers on the machine and their allocations where
\* finalizers run, and failing allocations where a collection runs.
Choices(s, step, pooled) ==
    LET ran == Apply(s, step, pooled, FALSE, {}, "none").log # <<>>
        fails(machine, grow) ==
            IF ~s.failed /\ (step = <<"collect">> \/ Apply(s, step, pooled, machine, grow, "none").collected)
            THEN Fails ELSE {"none"}
    IN  UNION {{Apply(s, step, pooled, machine, grow, fail) : fail \in fails(machine, grow)} :
                  machine \in IF ran THEN BOOLEAN ELSE {FALSE}, grow \in IF ran THEN Grows ELSE {{}}}

\* After a statement at whose boundary spy collected automatically, the
\* language collects too, as if the host had called gc.collect(); op then
\* records <<"after", step, n>>, with the n finalizer calls of the
\* statement. Once a collection failed, the language model is set aside
\* (Blank), and no further allocation fails.
Next ==
    \E step \in G!Steps, pooled \in BOOLEAN :
        /\ G!Enabled(impl, step)
        /\ impl' \in Choices([impl EXCEPT !.log = <<>>, !.collected = FALSE], step, pooled)
        /\ LET ran == G!Apply([spec EXCEPT !.log = <<>>], step)
               swept == G!Apply(ran, <<"collect">>)
           IN  /\ spec' = IF impl'.failed THEN Blank ELSE IF impl'.collected THEN [swept EXCEPT !.log = ran.log \o @] ELSE ran
               /\ op' = IF impl'.collected /\ ~impl'.failed THEN <<"after", step, Len(ran.log)>> ELSE step

Spec == Init /\ [][Next]_<<spec, impl, op>>

-----------------------------------------------------------------------------
TypeOK == impl \in Heap

\* spy and the language agree on every observable after every step: a
\* generator its frame holds is gone to Python.
SameHeap ==
    ~impl.failed =>
        /\ impl.alive \ impl.taken = spec.alive /\ impl.root = spec.root /\ impl.ref = spec.ref
        /\ impl.finalized \ impl.taken = spec.finalized

\* The order of a collection's finalizers is unspecified; those a statement
\* ran before an automatic collection come first, in order.
SameFinalizers ==
    LET n == IF op = <<"collect">> THEN 0 ELSE IF op[1] = "after" THEN op[3] ELSE Len(spec.log)
        rest(log) == {log[k] : k \in n + 1..Len(log)}
    IN  ~impl.failed =>
            /\ Len(impl.log) = Len(spec.log)
            /\ SubSeq(impl.log, 1, n) = SubSeq(spec.log, 1, n)
            /\ rest(impl.log) = rest(spec.log)

\* A weak reference answers exactly while its object is alive to Python.
WeakAnswers == impl.weak = (impl.alive \ impl.taken) \cap Obj

\* A frame reaches its generator (for its code and line) as long as it
\* lives: borrowed from the generator that holds it, or its own after
\* frame_take; a generator its frame holds holds nothing itself.
Taken == /\ "f" \in impl.alive => \/ "g" \in impl.alive \ impl.taken /\ impl.ref["g"]["ref"] = "f"
                                  \/ "g" \in impl.taken /\ impl.ref["g"] = G!Empty
         /\ impl.taken \subseteq impl.alive

\* No statement ends with a collection still due.
Collected == ~impl.due

\* spy never touches freed memory, never frees what is still referenced, and
\* between statements every count is exact and nothing waits for a finalizer.
Sound == ~impl.broken
ExactCounts == \A o \in impl.alive : impl.refs[o] = Count(impl, o)
Drained == impl.queue = <<>> /\ impl.pending = <<>>

\* Also after a failed collection: an explicit one that does not fail
\* leaves only what Python can reach (a frame's generator is the frame's),
\* and no finalizer runs twice in one lifetime.
CollectComplete == [][op' = <<"collect">> /\ (impl.failed \/ ~impl'.failed) => impl'.alive = Reach(impl')]_<<spec, impl, op>>
OnceEach == [][\A o \in Obj : (o \in impl.finalized /\ o \in impl'.alive) => \A k \in 1..Len(impl'.log) : impl'.log[k] # o]_<<spec, impl, op>>
=============================================================================
