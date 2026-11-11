--------------------------------- MODULE GC ---------------------------------
(***************************************************************************)
(* Object lifetime and finalization as Python specifies it                 *)
(* (reference/datamodel.html#object.__del__, PEP 442, the gc module's      *)
(* collect(), and generator finalization), with CPython's order for what   *)
(* the reference leaves open.                                              *)
(* An object is destroyed when its last reference goes away; its __del__   *)
(* runs at most once per lifetime even if it resurrects itself; a          *)
(* suspended generator is closed when it dies, and its frame outlives it   *)
(* without keeping it (27.2.4); and gc.collect() finalizes and frees the   *)
(* garbage only reference cycles keep alive.                               *)
(*                                                                         *)
(* Up to three instances can exist, each with two attribute slots, ref and *)
(* other (set in that order by its constructor). All have a __del__ that   *)
(* records their name; p's also stores p in the global `saved`,            *)
(* resurrecting it. The generator g is suspended in a try whose finally    *)
(* records "g"; its frame f exists once g.gi_frame is asked for, and g     *)
(* holds it (in its ref slot here) until g is closed. Neither takes        *)
(* attributes, and f has no __del__.                                       *)
(* The program's variables x, y, and saved are the roots. The steps        *)
(* (Python in GC.replay.py):                                               *)
(*                                                                         *)
(*     x = A('a')        # New: a fresh object into x or y                 *)
(*     x = started()     #   (g: a generator, run to its yield)            *)
(*     x.ref = y         # Link: an instance's slot takes a root's value *)
(*     x = y.other       # Load: a root takes what a slot refers to        *)
(*     x = y.gi_frame    # Frame: a root takes the generator's frame       *)
(*     x = None          # Del: a root lets go                             *)
(*     gc.collect()      # Collect                                         *)
(*                                                                         *)
(* `out` is the sequence of __del__ and close calls each step makes; for a *)
(* collection, whose finalization order Python leaves unspecified, it is   *)
(* listed in name order. When an object is freed, CPython releases its     *)
(* attributes last to first, each completely (with everything that frees)  *)
(* before the next.                                                        *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

CONSTANT Obj       \* the finalizable objects: some of "a", "b", "p", and "g"
ASSUME Obj \subseteq {"a", "b", "g", "p"}
Order == SelectSeq(<<"a", "b", "g", "p">>, LAMBDA o : o \in Obj)
Instances == Obj \ {"g"}
Frames == IF "g" \in Obj THEN {"f"} ELSE {}
Things == Obj \cup Frames
Slots == {"ref", "other"}
Roots == {"x", "y", "saved"}
None == "none"
Empty == [f \in Slots |-> None]

VARIABLES alive, root, ref, finalized, op, out
vars == <<alive, root, ref, finalized, op, out>>

\* A heap: the objects alive, the roots, each object's slots, the objects
\* whose __del__ or close has run in their current lifetime, and the step's
\* log.
State == [alive : SUBSET Things, root : [Roots -> Things \cup {None}], ref : [Things -> [Slots -> Things \cup {None}]],
          finalized : SUBSET Obj, log : Seq(Obj)]

\* How many references an object has: roots and slots. A freed object's
\* slots are empty, except while it is being freed and lets go of them.
RC(s, o) == Cardinality({r \in Roots : s.root[r] = o}) + Cardinality({e \in Things \X Slots : s.ref[e[1]][e[2]] = o})

\* What objects in a set refer to.
Targets(s, set) == {s.ref[q][f] : q \in set, f \in Slots} \ {None}

\* The objects reachable from a set, and from the roots.
Closure(s, set) ==
    LET RECURSIVE From(_)
        From(x) == LET more == x \cup Targets(s, x) IN IF more = x THEN x ELSE From(more)
    IN From(set)
Reach(s) == Closure(s, {s.root[r] : r \in Roots} \ {None})

\* __del__ or close runs: it is logged; p's resurrects p into `saved`
\* (which then cannot hold anything else, since only p is ever saved and p
\* was dying), and g's close lets go of g's frame.
Finalize(s, o) ==
    [s EXCEPT !.log = Append(@, o), !.finalized = @ \cup {o},
              !.root = IF o = "p" THEN [@ EXCEPT !["saved"] = "p"] ELSE @,
              !.ref = IF o = "g" THEN [@ EXCEPT !["g"]["ref"] = None] ELSE @]

\* A reference to o has gone: with none left, o's finalizer runs if it has
\* one that has not run yet, and unless that resurrected o, o is freed and
\* lets go of its slots, other before ref, each slot cleared before what it
\* held is released.
RECURSIVE Release(_, _)
Release(s, o) ==
    IF o = None \/ o \notin s.alive \/ RC(s, o) > 0 THEN s
    ELSE LET t == IF o \in s.finalized \/ o \notin Obj THEN s
                  ELSE IF o = "g" THEN Release(Finalize(s, o), s.ref["g"]["ref"])
                  ELSE Finalize(s, o)
         IN  IF RC(t, o) > 0 THEN t
             ELSE LET freed == [t EXCEPT !.alive = @ \ {o}, !.finalized = @ \ {o}]
                      other == Release([freed EXCEPT !.ref[o]["other"] = None], t.ref[o]["other"])
                  IN  Release([other EXCEPT !.ref[o]["ref"] = None], t.ref[o]["ref"])

\* gc.collect(): every unreachable object's finalizer runs if it has not
\* yet; then whatever is still unreachable is freed.
Collect(s) ==
    LET pending == ((s.alive \ Reach(s)) \cap Obj) \ s.finalized
        ran == [s EXCEPT !.finalized = @ \cup pending,
                         !.log = SelectSeq(Order, LAMBDA o : o \in pending),
                         !.root = IF "p" \in pending THEN [@ EXCEPT !["saved"] = "p"] ELSE @,
                         !.ref = IF "g" \in pending THEN [@ EXCEPT !["g"]["ref"] = None] ELSE @]
        dead == ran.alive \ Reach(ran)
    IN  [ran EXCEPT !.alive = @ \ dead, !.finalized = @ \ dead,
                    !.ref = [q \in Things |-> IF q \in dead THEN Empty ELSE @[q]]]

\* An assignment: the new value is referenced before the old one is let go.
DoNew(s, v, o) == Release([s EXCEPT !.alive = @ \cup {o}, !.ref[o] = Empty, !.root[v] = o], s.root[v])
DoLink(s, v, f, w) == Release([s EXCEPT !.ref[s.root[v]][f] = s.root[w]], s.ref[s.root[v]][f])
DoLoad(s, v, w, f) == Release([s EXCEPT !.root[v] = s.ref[s.root[w]][f]], s.root[v])
DoDel(s, v) == Release([s EXCEPT !.root[v] = None], s.root[v])
\* g.gi_frame: the frame g holds, made on first use.
DoFrame(s, v) ==
    LET made == IF s.ref["g"]["ref"] = "f" THEN s
                ELSE [s EXCEPT !.alive = @ \cup {"f"}, !.ref["f"] = Empty, !.ref["g"]["ref"] = "f"]
    IN  Release([made EXCEPT !.root[v] = "f"], s.root[v])

Steps ==
    {<<"new", v, o>> : v \in {"x", "y"}, o \in Obj} \cup
    {<<"link", v, f, w>> : v \in Roots, f \in Slots, w \in Roots} \cup
    {<<"load", v, w, f>> : v \in {"x", "y"}, w \in Roots, f \in Slots} \cup
    {<<"frame", v, w>> : v \in {"x", "y"}, w \in Roots} \cup
    {<<"del", v>> : v \in Roots} \cup {<<"collect">>}

\* A new g waits for the frame of the last one to go, so that f names one
\* frame.
Enabled(s, step) ==
    CASE step[1] = "new" -> step[3] \notin s.alive /\ (step[3] = "g" => "f" \notin s.alive)
      [] step[1] = "link" -> s.root[step[2]] \in Instances
      [] step[1] = "load" -> s.root[step[3]] \in Instances
      [] step[1] = "frame" -> s.root[step[3]] = "g"
      [] OTHER -> TRUE

Apply(s, step) ==
    CASE step[1] = "new" -> DoNew(s, step[2], step[3])
      [] step[1] = "link" -> DoLink(s, step[2], step[3], step[4])
      [] step[1] = "load" -> DoLoad(s, step[2], step[3], step[4])
      [] step[1] = "frame" -> DoFrame(s, step[2])
      [] step[1] = "del" -> DoDel(s, step[2])
      [] step[1] = "collect" -> Collect(s)

Current == [alive |-> alive, root |-> root, ref |-> ref, finalized |-> finalized, log |-> <<>>]

Init ==
    /\ alive = {} /\ root = [r \in Roots |-> None] /\ ref = [o \in Things |-> Empty]
    /\ finalized = {} /\ op = <<"init">> /\ out = <<>>

Next ==
    \E step \in Steps :
        /\ Enabled(Current, step)
        /\ LET s == Apply(Current, step)
           IN  /\ alive' = s.alive /\ root' = s.root /\ ref' = s.ref /\ finalized' = s.finalized
               /\ op' = step /\ out' = s.log

Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
TypeOK == Current \in State /\ out \in Seq(Obj)

\* Nothing reachable is ever freed: every root and every live slot refers to
\* a live object, and a freed object's slots are empty.
NoDangling == /\ \A r \in Roots : root[r] \in alive \cup {None}
              /\ \A q \in alive : \A f \in Slots : ref[q][f] \in alive \cup {None}
              /\ \A q \in Things \ alive : ref[q] = Empty

\* Reference counting leaves no object alive without references, so only
\* reference cycles (and what they reach) outlive their last root.
NoZeroRC == \A o \in alive : RC(Current, o) > 0

\* A collection leaves only reachable objects alive.
CollectComplete == op = <<"collect">> => alive = Reach(Current)

\* Only p resurrects, so only p is ever saved.
OnlyPSaved == root["saved"] \in {None, "p"}

\* A frame does not keep its generator: nothing refers to g but roots and
\* instances, and a live g is suspended, unfinalized.
FrameKeepsNoGenerator == /\ \A q \in Things \ Instances : \A f \in Slots : ref[q][f] # "g"
                         /\ "g" \in alive => "g" \notin finalized

\* No __del__ runs twice in one lifetime: a step logs each object at most
\* once, and never one that was already finalized and stays alive.
NoRepeat == \A j, k \in 1..Len(out) : j # k => out[j] # out[k]
OnceEach == [][\A o \in Obj : (o \in finalized /\ o \in alive') => \A k \in 1..Len(out') : out'[k] # o]_vars
=============================================================================
