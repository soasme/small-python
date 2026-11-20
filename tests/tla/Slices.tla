------------------------------- MODULE Slices -------------------------------
(***************************************************************************)
(* Slice objects, as The Python Language Reference specifies them          *)
(* (reference/datamodel.html#slice-objects): start, stop, and step are     *)
(* read-only, None when omitted, and of any type; indices(length) gives    *)
(* the start, stop, and step a sequence of that length uses, missing or    *)
(* out-of-bounds indices handled as for regular slices (and a zero step,   *)
(* or a bound without __index__, refused); slices compare and hash by      *)
(* their parts; slice[float] is a generic alias. The step, the start and   *)
(* the stop are taken in turn, each checked and its __index__ called as it *)
(* is reached.                                                             *)
(*                                                                         *)
(* A program makes s = slice(START, STOP, STEP) with bounds from None,     *)
(* -9, -2, 0, 3, 9, "x", an object whose Python __index__ returns 3,       *)
(* an int subclass worth 3 (its __index__ never called), and steps         *)
(* from None, -2, -1, 1, 2, 0, then calls s.indices(L) for L in 0, 4,      *)
(* given as an int or by an object whose Python __index__ returns it,      *)
(* which runs first, or takes list(range(L))[s], or reads the              *)
(* attributes, assigns s.start, or compares and hashes s with a copy;      *)
(* or evaluates slice[float]. The outcome is the repr of the result or     *)
(* the exception, followed by the bounds whose __index__ ran. A compare    *)
(* program puts at one part of two slices, None elsewhere, objects whose   *)
(* Python __eq__ and __lt__ loop and log, worth 1 and 1, 2, or a raising   *)
(* one on the left, and compares them by == or <, as tuples of the parts:  *)
(* the outcome is the result or exception, then the methods called.        *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

None == 99  \* sentinels: None, the str "x", the object of __index__ 3, an int subclass
X == 98
I3 == 97
J3 == 96    \* an int subclass worth 3, whose __index__ never runs
Bounds == {None, -9, -2, 0, 3, 9, X, I3, J3}
Steps == {None, -2, -1, 1, 2, 0}
Programs == [start : Bounds, stop : Bounds, step : Steps, length : {0, 4}, op : {"indices", "subscript", "lengthed"}]
            \cup [start : Bounds, stop : Bounds, step : Steps, length : {0}, op : {"attrs", "set", "eqhash"}]
            \cup [op : {"generic"}]
            \cup [op : {"compare"}, part : {1, 2, 3}, rel : {"eq", "lt"}, other : {"one", "two", "raise"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Repr(v) == CASE v = None -> "None" [] v = X -> "'x'" [] v = I3 -> "I3" [] v = J3 -> "3" [] OTHER -> ToString(v)

\* One bound clamped as PySlice_AdjustIndices does.
Clamp(w, default, length, lower, upper) ==
    LET v == IF w \in {I3, J3} THEN 3 ELSE w IN
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

\* The step is checked first, then the start, then the stop.
Refused(p) == CASE p.step = 0 -> "ValueError" [] p.start = X \/ p.stop = X -> "TypeError" [] OTHER -> ""

\* The bounds whose __index__ runs: the start's before the stop is checked,
\* and a length's before them.
Called(p) == (IF p.op = "lengthed" THEN " length" ELSE "") \o
             (IF p.op \notin {"indices", "subscript", "lengthed"} \/ p.step = 0 THEN ""
              ELSE (IF p.start = I3 THEN " start" ELSE "") \o (IF p.start # X /\ p.stop = I3 THEN " stop" ELSE ""))

Result(p) ==
    CASE p.op = "generic" -> "slice[float]"
      [] p.op = "attrs" -> Repr(p.start) \o " " \o Repr(p.stop) \o " " \o Repr(p.step)
      [] p.op = "set" -> "AttributeError"
      [] p.op = "eqhash" -> "True"
      [] Refused(p) # "" -> Refused(p)
      [] p.op \in {"indices", "lengthed"} -> LET i == Indices(p) IN "(" \o Join(i) \o ")"
      [] p.op = "subscript" -> LET i == Indices(p) IN "[" \o Join(Items(i[1], i[2], i[3])) \o "]"

\* The parts' pair is compared by __eq__; an unequal one orders by __lt__,
\* an equal one leaves the Nones after it, whose tuples are then equal.
Compared(p) == CASE p.other = "raise" -> "KeyError eq"
                 [] p.rel = "eq" -> IF p.other = "one" THEN "True eq" ELSE "False eq"
                 [] p.other = "one" -> "False eq"
                 [] OTHER -> "True eq lt"

Run(p) == CASE p.op = "compare" -> Compared(p) [] p.op = "generic" -> Result(p) [] OTHER -> Result(p) \o Called(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* indices() stays within the sequence: start and stop in [-1, length].
InBounds == Done /\ program.op \in {"indices", "lengthed"} /\ Refused(program) = "" =>
    LET i == Indices(program) IN i[1] \in -1..program.length /\ i[2] \in -1..program.length

\* A slice of a sequence takes only its own items.
SubscriptItems == Done /\ program.op = "subscript" /\ Refused(program) = "" =>
    LET i == Indices(program)  s == Items(i[1], i[2], i[3]) IN \A k \in DOMAIN s : s[k] \in 0..(program.length - 1)
=============================================================================
