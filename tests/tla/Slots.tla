-------------------------------- MODULE Slots --------------------------------
(***************************************************************************)
(* __slots__, as The Python Language Reference specifies it                *)
(* (reference/datamodel.html#slots): declared slots replace the instance   *)
(* __dict__ and __weakref__ (unless declared, or inherited from a base     *)
(* without __slots__, or the class declares none), so other names cannot   *)
(* be assigned; slots are descriptors, so a class variable of the same     *)
(* name is a conflict; a base's slots are available in subclasses; a       *)
(* __dict__ slot over a base that has a __dict__ is refused; and __class__ *)
(* can be assigned between classes with the same slots.                    *)
(*                                                                         *)
(* A program defines class S(BASE) with __slots__ = SLOTS (or none), BASE  *)
(* object, Plain (class Plain: pass), or P (class P: __slots__ = ("p",)),  *)
(* and SLOTS ("a",), ("a", "__dict__"), or (); then, for s = S(), tests    *)
(* for __dict__ or __weakref__, assigns s.c, s.a, or s.p (reading it       *)
(* back), reads s.a unset, defines S again with a = 0 in its body, or      *)
(* assigns s.__class__ = T for T defined as S is. The outcome is the       *)
(* result or the exception.                                                *)
(***************************************************************************)
EXTENDS Naturals, Sequences

SlotSets == {"none", "a", "a dict", "empty"}
Bases == {"object", "Plain", "P"}
Ops == {"hasdict", "hasweakref", "newattr", "seta", "setp", "unseta", "conflict", "assign"}
Programs == [slots : SlotSets, base : Bases, op : Ops]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* A base without __slots__, or a class declaring none, brings both.
Inherits(p) == p.slots = "none" \/ p.base = "Plain"
HasDict(p) == Inherits(p) \/ p.slots = "a dict"
HasWeakref(p) == Inherits(p)
HasSlotA(p) == p.slots \in {"a", "a dict"}

Bool(b) == IF b THEN "True" ELSE "False"

\* Declaring __dict__ over a base that has one is refused, before any conflict.
Refused(p) == p.slots = "a dict" /\ p.base = "Plain"

Run(p) ==
    CASE Refused(p) -> "TypeError"
      [] p.op = "hasdict" -> Bool(HasDict(p))
      [] p.op = "hasweakref" -> Bool(HasWeakref(p))
      [] p.op = "newattr" -> IF HasDict(p) THEN "1" ELSE "AttributeError"
      [] p.op = "seta" -> IF HasSlotA(p) \/ HasDict(p) THEN "1" ELSE "AttributeError"
      [] p.op = "setp" -> IF p.base = "P" \/ HasDict(p) THEN "1" ELSE "AttributeError"
      [] p.op = "unseta" -> "AttributeError"            \* an empty slot reads as missing
      [] p.op = "conflict" -> IF HasSlotA(p) THEN "ValueError" ELSE "ok"
      [] p.op = "assign" -> "T"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Without a __dict__, only declared slots can be assigned.
OnlySlots == Done /\ program.op = "newattr" /\ ~HasDict(program) /\ ~Refused(program) => outcome = "AttributeError"
=============================================================================
