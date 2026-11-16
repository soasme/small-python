----------------------------- MODULE Containers -----------------------------
(***************************************************************************)
(* Emulating container types, as The Python Language Reference             *)
(* specifies it (reference/datamodel.html#emulating-container-types):      *)
(* `in` uses __contains__ (its result converted to bool), else             *)
(* iterates; iteration uses __iter__, else __getitem__ with 0, 1, ...      *)
(* until IndexError, and setting __iter__ to None makes the object not     *)
(* iterable even with __getitem__; reversed() uses __reversed__ (None      *)
(* again blocks it), else __len__ and __getitem__; len() and bool()        *)
(* take __len__'s result as an index, by its __index__ after __len__;      *)
(* a dict subclass's __missing__ answers d[key] for an absent key, but     *)
(* not d.get(); and assignment or deletion without __setitem__ or          *)
(* __delitem__ raises TypeError.                                           *)
(*                                                                         *)
(* A program defines class X with __contains__ (absent, returning 1,       *)
(* or returning 0), __iter__ (absent, yielding 1 and 2, or None), and      *)
(* __getitem__ (absent, or indexing [1, 2]), then evaluates 2 in X()       *)
(* or list(X()); or defines __reversed__ (absent, returning iter([9]),     *)
(* or None) with or without __len__ and __getitem__ over [1, 2] and        *)
(* takes list(reversed(X())); or subclasses dict with or without           *)
(* __missing__ returning "m" and evaluates d["a"] or d.get("a") on         *)
(* {"b": 1}; or defines __getitem__ alone and assigns or deletes x[0];     *)
(* or takes len(), bool() or the items of reversed() of X() whose          *)
(* __len__ returns 3 or an object whose Python __index__ returns 2, -1     *)
(* or "s", with __getitem__ giving ten times the index. The outcome is     *)
(* the result or the exception, and for a length the calls of __len__      *)
(* and __index__ in turn.                                                  *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [part : {"in", "list"}, contains : {"none", "one", "zero"}, iter : {"none", "gen", "None"}, getitem : BOOLEAN]
            \cup [part : {"reversed"}, rev : {"none", "nine", "None"}, seq : BOOLEAN]
            \cup [part : {"missing"}, missing : BOOLEAN, op : {"index", "get"}]
            \cup [part : {"store"}, op : {"set", "del"}]
            \cup [part : {"length"}, length : {"three", "index", "negative", "str"}, op : {"len", "bool", "reversed"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* What iterating X() yields, or TypeError.
Iterate(p) == CASE p.iter = "None" -> "TypeError"
                [] p.iter = "gen" \/ p.getitem -> "[1, 2]"
                [] OTHER -> "TypeError"

Contains(p) == CASE p.contains = "one" -> "True"
                 [] p.contains = "zero" -> "False"
                 [] Iterate(p) = "TypeError" -> "TypeError"
                 [] OTHER -> "True"                           \* 2 is among the items

Reversed(p) == CASE p.rev = "nine" -> "[9]"
                 [] p.rev = "None" -> "TypeError"
                 [] p.seq -> "[2, 1]"
                 [] OTHER -> "TypeError"

Missing(p) == CASE p.op = "get" -> "None"                     \* get() never calls __missing__
                [] p.missing -> "'m'"
                [] OTHER -> "KeyError"

\* len(), bool() or reversed() of X() whose __len__ returns 3, or an object
\* whose __index__, called after __len__, returns 2, -1 or "s".
Length(p) ==
    LET calls == IF p.length = "three" THEN " len" ELSE " len index"
        three == p.length = "three"
    IN  CASE p.length = "negative" -> "ValueError" \o calls
          [] p.length = "str" -> "TypeError" \o calls
          [] p.op = "len" -> (IF three THEN "3" ELSE "2") \o calls
          [] p.op = "bool" -> "True" \o calls
          [] p.op = "reversed" -> (IF three THEN "[20, 10, 0]" ELSE "[10, 0]") \o calls

Run(p) == CASE p.part = "in" -> Contains(p)
            [] p.part = "list" -> IF p.contains # "none" /\ Iterate(p) = "TypeError" THEN "TypeError" ELSE Iterate(p)
            [] p.part = "reversed" -> Reversed(p)
            [] p.part = "missing" -> Missing(p)
            [] p.part = "store" -> "TypeError"
            [] p.part = "length" -> Length(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* __iter__ = None blocks iteration whatever else is defined.
NoneBlocks == Done /\ program.part = "list" /\ program.iter = "None" => outcome = "TypeError"

\* __contains__ decides membership without iterating.
ContainsDecides == Done /\ program.part = "in" /\ program.contains # "none" => outcome \in {"True", "False"}
=============================================================================
