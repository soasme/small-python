--------------------------------- MODULE GC ---------------------------------
(***************************************************************************)
(* Object lifetime and finalization as Python specifies it                 *)
(* (reference/datamodel.html#object.__del__, PEP 442, and the gc module's  *)
(* collect()), with CPython's order for what the reference leaves open.    *)
(* An object is destroyed when its last reference goes away; its __del__   *)
(* runs at most once per lifetime even if it resurrects itself; and        *)
(* gc.collect() finalizes and frees the garbage only reference cycles keep *)
(* alive.                                                                  *)
(*                                                                         *)
(* Up to three objects can exist, each with two attribute slots, ref and   *)
(* other (set in that order by its constructor). All have a __del__ that   *)
(* records their name; p's also stores p in the global `saved`,            *)
(* resurrecting it.                                                        *)
(* The program's variables x, y, and saved are the roots. The steps        *)
(* (Python in GC.replay.py):                                               *)
(*                                                                         *)
(*     x = A('a')        # New: a fresh object into x or y                 *)
(*     x.ref = y         # Link: a slot of one root's object takes another *)
(*     x = y.other       # Load: a root takes what a slot refers to        *)
(*     x = None          # Del: a root lets go                             *)
(*     gc.collect()      # Collect                                         *)
(*                                                                         *)
(* `out` is the sequence of __del__ calls each step makes; for a           *)
(* collection, whose finalization order Python leaves unspecified, it is   *)
(* listed in name order. When an object is freed, CPython releases its     *)
(* attributes last to first, each completely (with everything that frees)  *)
(* before the next.                                                        *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

CONSTANT Obj       \* the objects: some of "a", "b", and "p"
ASSUME Obj \subseteq {"a", "b", "p"}
Order == SelectSeq(<<"a", "b", "p">>, LAMBDA o : o \in Obj)
Slots == {"ref", "other"}
Roots == {"x", "y", "saved"}
None == "none"
Empty == [f \in Slots |-> None]

VARIABLES alive, root, ref, finalized, op, out
vars == <<alive, root, ref, finalized, op, out>>

\* A heap: the objects alive, the roots, each object's slots, the objects
\* whose __del__ has run in their current lifetime, and the step's log.
State == [alive : SUBSET Obj, root : [Roots -> Obj \cup {None}], ref : [Obj -> [Slots -> Obj \cup {None}]],
          finalized : SUBSET Obj, log : Seq(Obj)]

\* How many references an object has: roots and slots. A freed object's
\* slots are empty, except while it is being freed and lets go of them.
RC(s, o) == Cardinality({r \in Roots : s.root[r] = o}) + Cardinality({e \in Obj \X Slots : s.ref[e[1]][e[2]] = o})

\* What objects in a set refer to.
Targets(s, set) == {s.ref[q][f] : q \in set, f \in Slots} \ {None}

\* The objects reachable from a set, and from the roots.
Closure(s, set) ==
    LET RECURSIVE From(_)
        From(x) == LET more == x \cup Targets(s, x) IN IF more = x THEN x ELSE From(more)
    IN From(set)
Reach(s) == Closure(s, {s.root[r] : r \in Roots} \ {None})

\* __del__ runs: it is logged, and p's resurrects p into `saved` (which then
\* cannot hold anything else, since only p is ever saved and p was dying).
Finalize(s, o) ==
    [s EXCEPT !.log = Append(@, o), !.finalized = @ \cup {o},
              !.root = IF o = "p" THEN [@ EXCEPT !["saved"] = "p"] ELSE @]

\* A reference to o has gone: with none left, o's __del__ runs if it has not
\* yet, and unless that resurrected o, o is freed and lets go of its slots,
\* other before ref, each slot cleared before what it held is released.
RECURSIVE Release(_, _)
Release(s, o) ==
    IF o = None \/ o \notin s.alive \/ RC(s, o) > 0 THEN s
    ELSE LET t == IF o \in s.finalized THEN s ELSE Finalize(s, o)
         IN  IF RC(t, o) > 0 THEN t
             ELSE LET freed == [t EXCEPT !.alive = @ \ {o}, !.finalized = @ \ {o}]
                      other == Release([freed EXCEPT !.ref[o]["other"] = None], t.ref[o]["other"])
                  IN  Release([other EXCEPT !.ref[o]["ref"] = None], t.ref[o]["ref"])

\* gc.collect(): every unreachable object's __del__ runs if it has not yet;
\* then whatever is still unreachable is freed.
Collect(s) ==
    LET pending == (s.alive \ Reach(s)) \ s.finalized
        ran == [s EXCEPT !.finalized = @ \cup pending,
                         !.log = SelectSeq(Order, LAMBDA o : o \in pending),
                         !.root = IF "p" \in pending THEN [@ EXCEPT !["saved"] = "p"] ELSE @]
        dead == ran.alive \ Reach(ran)
    IN  [ran EXCEPT !.alive = @ \ dead, !.finalized = @ \ dead,
                    !.ref = [q \in Obj |-> IF q \in dead THEN Empty ELSE @[q]]]

\* An assignment: the new value is referenced before the old one is let go.
DoNew(s, v, o) == Release([s EXCEPT !.alive = @ \cup {o}, !.ref[o] = Empty, !.root[v] = o], s.root[v])
DoLink(s, v, f, w) == Release([s EXCEPT !.ref[s.root[v]][f] = s.root[w]], s.ref[s.root[v]][f])
DoLoad(s, v, w, f) == Release([s EXCEPT !.root[v] = s.ref[s.root[w]][f]], s.root[v])
DoDel(s, v) == Release([s EXCEPT !.root[v] = None], s.root[v])

Steps ==
    {<<"new", v, o>> : v \in {"x", "y"}, o \in Obj} \cup
    {<<"link", v, f, w>> : v \in Roots, f \in Slots, w \in Roots} \cup
    {<<"load", v, w, f>> : v \in {"x", "y"}, w \in Roots, f \in Slots} \cup
    {<<"del", v>> : v \in Roots} \cup {<<"collect">>}

Enabled(s, step) ==
    CASE step[1] = "new" -> step[3] \notin s.alive
      [] step[1] = "link" -> s.root[step[2]] # None
      [] step[1] = "load" -> s.root[step[3]] # None
      [] OTHER -> TRUE

Apply(s, step) ==
    CASE step[1] = "new" -> DoNew(s, step[2], step[3])
      [] step[1] = "link" -> DoLink(s, step[2], step[3], step[4])
      [] step[1] = "load" -> DoLoad(s, step[2], step[3], step[4])
      [] step[1] = "del" -> DoDel(s, step[2])
      [] step[1] = "collect" -> Collect(s)

Current == [alive |-> alive, root |-> root, ref |-> ref, finalized |-> finalized, log |-> <<>>]

Init ==
    /\ alive = {} /\ root = [r \in Roots |-> None] /\ ref = [o \in Obj |-> Empty]
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
              /\ \A q \in Obj \ alive : ref[q] = Empty

\* Reference counting leaves no object alive without references, so only
\* reference cycles (and what they reach) outlive their last root.
NoZeroRC == \A o \in alive : RC(Current, o) > 0

\* A collection leaves only reachable objects alive.
CollectComplete == op = <<"collect">> => alive = Reach(Current)

\* Only p resurrects, so only p is ever saved.
OnlyPSaved == root["saved"] \in {None, "p"}

\* No __del__ runs twice in one lifetime: a step logs each object at most
\* once, and never one that was already finalized and stays alive.
NoRepeat == \A j, k \in 1..Len(out) : j # k => out[j] # out[k]
OnceEach == [][\A o \in Obj : (o \in finalized /\ o \in alive') => \A k \in 1..Len(out') : out'[k] # o]_vars
=============================================================================
