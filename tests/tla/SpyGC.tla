------------------------------- MODULE SpyGC -------------------------------
(***************************************************************************)
(* spy's memory manager, as spy.c implements it, run in lockstep with the  *)
(* language semantics of GC.tla. TLC checks that after every step both     *)
(* have the same objects alive, the same roots and slots, the same         *)
(* finalized objects, and made the same __del__ calls, and that spy's      *)
(* internal bookkeeping stays sound.                                       *)
(*                                                                         *)
(* The implementation, step by step (function names are spy.c's):          *)
(*                                                                         *)
(*  - Every object carries a reference count, `refs`. spy_release drops    *)
(*    one; at zero, finalize_later queues an object whose __del__ has not  *)
(*    run, keeping it alive with the queue's own reference, and otherwise  *)
(*    the object is freed and releases its slot.                           *)
(*  - At the next statement boundary, weak_callbacks runs each queued      *)
(*    __del__ and then releases the queue's reference.                     *)
(*  - collect_once finds garbage by trial deletion: a count minus the      *)
(*    references from other objects leaves the external ones (roots and    *)
(*    the queue); objects with any, and all they reach, are live. Dead     *)
(*    objects awaiting __del__ are queued and kept with all they reach;    *)
(*    the rest is freed, after their references into live objects are      *)
(*    dropped (release_live_edge) without recursion.                       *)
(*  - spy_collect repeats collect_once after running the queue until no    *)
(*    __del__ is pending.                                                  *)
(*  - Automatic collection: an allocation that takes a new pool (pool_new, *)
(*    a choice here) makes a collection due once the objects exceed the    *)
(*    last collection's survivors by SPY_LIMIT_COLLECTION and memory has   *)
(*    doubled; objects stand for memory. The next statement boundary       *)
(*    (tick_full) then collects before it runs the queue. A limit of zero  *)
(*    never collects automatically.                                        *)
(*    To the language, such a collection is a gc.collect() the host made   *)
(*    after the statement (9.7 leaves its time to the implementation).     *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

CONSTANT Obj
VARIABLES spec, impl, op

G == INSTANCE GC WITH alive <- spec.alive, root <- spec.root, ref <- spec.ref,
                      finalized <- spec.finalized, out <- spec.log

None == G!None
Slots == G!Slots
Never == Cardinality(Obj) + 1 \* SIZE_MAX: no heap exceeds it
Limits == 0..2                \* SPY_LIMIT_COLLECTION, chosen at the start

\* spy's heap: GC.tla's fields plus each object's reference count, the
\* pending stack of spy_release, the queue of objects awaiting __del__, and
\* a flag raised when the code would touch freed memory or free an object
\* something still refers to.
Heap == [alive : SUBSET Obj, root : [G!Roots -> Obj \cup {None}], ref : [Obj -> [Slots -> Obj \cup {None}]],
         finalized : SUBSET Obj, log : Seq(Obj), refs : [Obj -> Nat], pending : Seq(Obj),
         queue : Seq(Obj), broken : BOOLEAN, limit : Limits, collectListed : Nat, collectMemory : Nat,
         due : BOOLEAN, collected : BOOLEAN]

Retain(s, o) == IF o = None THEN s ELSE [s EXCEPT !.refs[o] = @ + 1]

\* release_edge: one reference fewer; an object left with none is pushed on
\* the pending stack.
Drop(s, o) ==
    IF o = None THEN s
    ELSE IF o \notin s.alive \/ s.refs[o] = 0 THEN [s EXCEPT !.broken = TRUE]     \* use after free
    ELSE IF s.refs[o] = 1 THEN [s EXCEPT !.refs[o] = 0, !.pending = Append(@, o)]
    ELSE [s EXCEPT !.refs[o] = @ - 1]

\* The pending loop of spy_release, last in first out: finalize_later queues
\* an object whose __del__ has not run, keeping it with the queue's
\* reference; any other is freed, dropping its slots in their order (the
\* constructor sets ref, then other).
RECURSIVE Drain(_)
Drain(s) ==
    IF s.pending = <<>> THEN s
    ELSE LET o == s.pending[Len(s.pending)]
             t == [s EXCEPT !.pending = SubSeq(@, 1, Len(@) - 1)]
         IN  IF o \notin t.finalized
             THEN Drain([t EXCEPT !.refs[o] = 1, !.queue = Append(@, o), !.finalized = @ \cup {o}])
             ELSE Drain(Drop(Drop([t EXCEPT !.alive = @ \ {o}, !.finalized = @ \ {o}, !.ref[o] = G!Empty],
                                  t.ref[o]["ref"]), t.ref[o]["other"]))

\* spy_release.
Release(s, o) == Drain(Drop(s, o))

\* An assignment: the new value is retained before the old one is released.
Store(s, write(_, _), old, new) == Release(write(Retain(s, new), new), old)

\* weak_callbacks: each queued __del__ runs (p's stores itself in `saved`),
\* then the queue's reference is released; whatever that queued goes ahead
\* of the objects that were already waiting.
RECURSIVE Callbacks(_)
Callbacks(s) ==
    IF s.queue = <<>> THEN s
    ELSE LET self == Head(s.queue)
             t == [s EXCEPT !.queue = Tail(@), !.log = Append(@, self)]
             u == IF self = "p"
                  THEN Store(t, LAMBDA h, v : [h EXCEPT !.root["saved"] = v], t.root["saved"], "p")
                  ELSE t
             w == Release(u, self)
             waiting == Len(t.queue)
         IN  Callbacks([w EXCEPT !.queue = SubSeq(@, waiting + 1, Len(@)) \o SubSeq(@, 1, waiting)])

\* collect_once.
CollectOnce(s) ==
    LET internal(o) == Cardinality({e \in s.alive \X Slots : s.ref[e[1]][e[2]] = o})
        live == G!Closure(s, {o \in s.alive : s.refs[o] - internal(o) > 0})
        waiting == {o \in s.alive \ live : o \notin s.finalized}
        kept == G!Closure(s, live \cup waiting)
        dead == s.alive \ kept
        refs == [o \in Obj |-> IF o \in kept
                               THEN s.refs[o] + (IF o \in waiting THEN 1 ELSE 0)
                                    - Cardinality({e \in dead \X Slots : s.ref[e[1]][e[2]] = o})
                               ELSE 0]
    IN  [s EXCEPT !.refs = refs, !.finalized = (@ \cup waiting) \ dead,
                  !.queue = @ \o SelectSeq(G!Order, LAMBDA o : o \in waiting),
                  !.alive = @ \ dead, !.ref = [q \in Obj |-> IF q \in dead THEN G!Empty ELSE @[q]],
                  !.broken = @ \/ \E o \in kept : refs[o] = 0]

\* The repetition of collect, after its first collect_once.
RECURSIVE Repeat(_)
Repeat(s) == IF s.queue = <<>> THEN s ELSE Repeat(CollectOnce(Callbacks(s)))

\* schedule_collection.
Schedule(s) ==
    LET live == Cardinality(s.alive)
    IN  [s EXCEPT !.due = FALSE, !.collectListed = IF s.limit = 0 THEN Never ELSE live + s.limit,
                  !.collectMemory = 2 * live]

\* pool_new, when an allocation takes a new pool.
Grow(s) ==
    LET live == Cardinality(s.alive)
    IN  IF live > s.collectListed /\ live > s.collectMemory THEN [s EXCEPT !.due = TRUE] ELSE s

\* collect, as spy_collect and the automatic collection run it.
Collect(s) == Schedule(Repeat(CollectOnce(s)))

\* tick_full: the boundary after a statement collects when due, and
\* otherwise runs the callbacks; `collected` records which it did.
Boundary(s) == IF s.due THEN [Collect(s) EXCEPT !.collected = TRUE] ELSE Callbacks(s)

\* Each step is one statement; the boundary after it collects or runs the callbacks.
Apply(s, step, pooled) ==
    CASE step[1] = "new" ->
            LET o == step[3]
                born == [s EXCEPT !.alive = @ \cup {o}, !.ref[o] = G!Empty, !.refs[o] = 1, !.finalized = @ \ {o}]
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
      [] step[1] = "del" ->
            Boundary(Store(s, LAMBDA h, v : [h EXCEPT !.root[step[2]] = v], s.root[step[2]], None))
      [] step[1] = "collect" -> Collect(s)

Init ==
    /\ spec = [alive |-> {}, root |-> [r \in G!Roots |-> None], ref |-> [o \in Obj |-> G!Empty],
               finalized |-> {}, log |-> <<>>]
    /\ \E limit \in Limits : impl = Schedule([alive |-> {}, root |-> [r \in G!Roots |-> None], ref |-> [o \in Obj |-> G!Empty],
               finalized |-> {}, log |-> <<>>, refs |-> [o \in Obj |-> 0], pending |-> <<>>,
               queue |-> <<>>, broken |-> FALSE, limit |-> limit, collectListed |-> Never,
               collectMemory |-> 0, due |-> FALSE, collected |-> FALSE])
    /\ op = <<"init">>

\* After a statement at whose boundary spy collected automatically, the
\* language collects too, as if the host had called gc.collect(); op then
\* records <<"after", step, n>>, with the n __del__ calls of the statement.
Next ==
    \E step \in G!Steps :
        /\ G!Enabled(spec, step)
        /\ \E pooled \in BOOLEAN : impl' = Apply([impl EXCEPT !.log = <<>>, !.collected = FALSE], step, pooled)
        /\ LET ran == G!Apply([spec EXCEPT !.log = <<>>], step)
               swept == G!Apply(ran, <<"collect">>)
           IN  spec' = IF impl'.collected THEN [swept EXCEPT !.log = ran.log \o @] ELSE ran
        /\ op' = IF impl'.collected THEN <<"after", step, Len(G!Apply([spec EXCEPT !.log = <<>>], step).log)>> ELSE step

Spec == Init /\ [][Next]_<<spec, impl, op>>

-----------------------------------------------------------------------------
TypeOK == impl \in Heap

\* spy and the language agree on every observable after every step.
SameHeap ==
    /\ impl.alive = spec.alive /\ impl.root = spec.root /\ impl.ref = spec.ref
    /\ impl.finalized = spec.finalized

\* The order of a collection's finalizers is unspecified; those a statement
\* ran before an automatic collection come first, in order.
SameFinalizers ==
    LET n == IF op = <<"collect">> THEN 0 ELSE IF op[1] = "after" THEN op[3] ELSE Len(spec.log)
        rest(log) == {log[k] : k \in n + 1..Len(log)}
    IN  /\ Len(impl.log) = Len(spec.log)
        /\ SubSeq(impl.log, 1, n) = SubSeq(spec.log, 1, n)
        /\ rest(impl.log) = rest(spec.log)

\* No statement ends with a collection still due.
Collected == ~impl.due

\* spy never touches freed memory, never frees what is still referenced, and
\* between statements every count is exact and nothing waits for __del__.
Sound == ~impl.broken
ExactCounts == \A o \in impl.alive : impl.refs[o] = G!RC(impl, o)
Drained == impl.queue = <<>> /\ impl.pending = <<>>
=============================================================================
