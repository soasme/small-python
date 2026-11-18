------------------------- MODULE ClassAttributeHooks -------------------------
(***************************************************************************)
(* Assignment and deletion on a class, as PLS-315 7.3.7, 7.3.9 and 10.4.1 *)
(* specify them: they call the special method of the class's metaclass,   *)
(* so a metaclass's own __setattr__ or __delattr__ runs for C.a = v and    *)
(* del C.a, and type's own slots do the store when it defers to them.      *)
(*                                                                         *)
(* A program runs, on a class C of metaclass M, a step that sets C.a,      *)
(* deletes C.a, or deletes it again. M's __setattr__ and __delattr__ are   *)
(* each absent, a hook that logs and defers to super(), or a hook that     *)
(* refuses with AttributeError. M may also define a as a data descriptor *)
(* (descr), whose __set__ and __delete__ log and hold the value: the store *)
(* type's slots make reaches it instead of C's namespace, and deleting it  *)
(* unset raises AttributeError. The outcome records the hook log, each     *)
(* step's "ok" or "AttributeError", and whether C.a is in C's namespace.   *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Hooks == {"absent", "defer", "refuse"}
Programs == [setattr : Hooks, delattr : Hooks, descr : BOOLEAN, steps : {<<"set">>, <<"set", "del">>, <<"set", "del", "del">>, <<"del">>}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == [log |-> "", results |-> "pending", present |-> FALSE]

\* One step on the state <<log, results, present, held>>, held the value
\* the descriptor keeps.
Step(p, s, op) ==
    LET hook == IF op = "set" THEN p.setattr ELSE p.delattr
        hooked == IF hook = "absent" THEN s[1] ELSE s[1] \o op \o " "
        reaches == hook # "refuse"
        logged == IF reaches /\ p.descr THEN hooked \o "d" \o op \o " " ELSE hooked
        had == IF p.descr THEN s[4] ELSE s[3]
        stores == reaches /\ (op = "set" \/ had)
        result == IF ~stores THEN "AttributeError" ELSE "ok"
        now == IF stores THEN op = "set" ELSE had
    IN <<logged, s[2] \o result \o " ", IF p.descr THEN s[3] ELSE now, IF p.descr THEN now ELSE s[4]>>

RECURSIVE Steps(_, _, _)
Steps(p, s, i) == IF i > Len(p.steps) THEN s ELSE Steps(p, Step(p, s, p.steps[i]), i + 1)

Run(p) == LET s == Steps(p, <<"", "", FALSE, FALSE>>, 1)
          IN [log |-> s[1], results |-> s[2], present |-> s[3]]

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* With no hooks the class behaves as type's own slots make it.
TypeSlots == Done /\ program.setattr = "absent" /\ program.delattr = "absent" /\ ~program.descr /\ program.steps = <<"set">> =>
    outcome = [log |-> "", results |-> "ok ", present |-> TRUE]

\* A refusing __setattr__ leaves the class unchanged.
RefusalStoresNothing == Done /\ program.setattr = "refuse" => ~outcome.present

\* A metaclass's data descriptor takes the stores: C's namespace stays empty.
DescriptorTakesStores == Done /\ program.descr => ~outcome.present
=============================================================================
