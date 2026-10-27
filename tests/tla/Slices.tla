------------------------------- MODULE Slices -------------------------------
(***************************************************************************)
(* Slice objects, as The Python Language Reference specifies them          *)
(* (reference/datamodel.html#slice-objects): start, stop, and step are     *)
(* read-only, None when omitted, and of any type; indices(length) gives    *)
(* the start, stop, and step a sequence of that length uses, missing or    *)
(* out-of-bounds indices handled as for regular slices (and a zero step,   *)
(* or a bound without __index__, refused); slices compare and hash by      *)
(* their parts; slice[float] is a generic alias.                           *)
(*                                                                         *)
(* A program makes s = slice(START, STOP, STEP) with bounds from None, -9, *)
(* -2, 0, 3, 9, "x" and steps from None, -2, -1, 1, 2, 0, then calls       *)
(* s.indices(L) for L in 0, 4, or takes list(range(L))[s], or reads the    *)
(* attributes, assigns s.start, or compares and hashes s with a copy; or   *)
(* evaluates slice[float]. The outcome is the repr of the result or the    *)
(* exception.                                                              *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

None == 99  \* sentinels: None, and the str "x"
X == 98
Bounds == {None, -9, -2, 0, 3, 9, X}
Steps == {None, -2, -1, 1, 2, 0}
Programs == [start : Bounds, stop : Bounds, step : Steps, length : {0, 4}, op : {"indices", "subscript"}]
            \cup [start : Bounds, stop : Bounds, step : Steps, length : {0}, op : {"attrs", "set", "eqhash"}]
            \cup [op : {"generic"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Repr(v) == CASE v = None -> "None" [] v = X -> "'x'" [] OTHER -> ToString(v)

\* One bound clamped as PySlice_AdjustIndices does.
Clamp(v, default, length, lower, upper) ==
    IF v = None THEN default
    ELSE IF v < 0 THEN (IF v + length < lower THEN lower ELSE v + length)
    ELSE IF v > upper THEN upper ELSE v

Indices(p) ==
    LET step == IF p.step = None THEN 1 ELSE p.step
        lower == IF step < 0 THEN -1 ELSE 0
        upper == IF step < 0 THEN p.length - 1 ELSE p.length
    IN  <<Clamp(p.start, IF step < 0 THEN upper ELSE lower, p.length, lower, upper),
          Clamp(p.stop, IF step < 0 THEN lower ELSE upper, p.length, lower, upper), step>>

\* The indices start, start + step, ... before stop.
RECURSIVE Items(_, _, _)
Items(i, stop, step) == IF (step > 0 /\ i < stop) \/ (step < 0 /\ i > stop) THEN <<i>> \o Items(i + step, stop, step) ELSE <<>>

RECURSIVE Join(_)
Join(s) == CASE s = <<>> -> "" [] Len(s) = 1 -> ToString(s[1]) [] OTHER -> ToString(s[1]) \o ", " \o Join(Tail(s))

\* The step is checked first, then the bounds.
Refused(p) == CASE p.step = 0 -> "ValueError" [] p.start = X \/ p.stop = X -> "TypeError" [] OTHER -> ""

Run(p) ==
    CASE p.op = "generic" -> "slice[float]"
      [] p.op = "attrs" -> Repr(p.start) \o " " \o Repr(p.stop) \o " " \o Repr(p.step)
      [] p.op = "set" -> "AttributeError"
      [] p.op = "eqhash" -> "True"
      [] Refused(p) # "" -> Refused(p)
      [] p.op = "indices" -> LET i == Indices(p) IN "(" \o Join(i) \o ")"
      [] p.op = "subscript" -> LET i == Indices(p) IN "[" \o Join(Items(i[1], i[2], i[3])) \o "]"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* indices() stays within the sequence: start and stop in [-1, length].
InBounds == Done /\ program.op = "indices" /\ Refused(program) = "" =>
    LET i == Indices(program) IN i[1] \in -1..program.length /\ i[2] \in -1..program.length

\* A slice of a sequence takes only its own items.
SubscriptItems == Done /\ program.op = "subscript" /\ Refused(program) = "" =>
    LET i == Indices(program)  s == Items(i[1], i[2], i[3]) IN \A k \in DOMAIN s : s[k] \in 0..(program.length - 1)
=============================================================================
