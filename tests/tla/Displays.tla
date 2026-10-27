----------------------------- MODULE Displays ------------------------------
(***************************************************************************)
(* Parenthesized forms and container displays, as The Python Language      *)
(* Reference specifies them (reference/expressions.html#parenthesized-     *)
(* forms and #displays-for-lists-sets-and-dictionaries): items are         *)
(* evaluated left to right, each once, and a starred item contributes      *)
(* every item of its iterable; a list, tuple, or set display builds a new  *)
(* object, a set keeping the first of equal elements; a dict display       *)
(* evaluates each key before its value, a key keeping its first form and   *)
(* its last value, and ** merges a mapping; a failed item stops            *)
(* evaluation; a parenthesized expression is the expression itself, and a  *)
(* tuple needs a comma.                                                    *)
(*                                                                         *)
(* A program is either a display of KIND (list, tuple, set, or dict) with  *)
(* up to three items, or one of the CASES. Item i of a list, tuple, or set *)
(* display is i, True, *[i, i + 10], *[], or *i; of a dict display, i:     *)
(* i + 100, True: i + 100, **{1: i + 200}, or **i. Every item is logged as *)
(* it is evaluated. The outcome is "ok", the result (the repr of each      *)
(* element, the set of them for a set), and the log, or the exception and  *)
(* the log.                                                                *)
(***************************************************************************)
EXTENDS Naturals, Sequences, TLC

SeqItems == {"plain", "true", "star", "empty", "bad"}
DictItems == {"pair", "true_pair", "merge", "bad"}
Cases == {"paren_same", "paren_yield", "empty", "tuple_needs_comma", "trailing_comma", "nested", "dict_unhashable",
          "set_unhashable", "dict_late_unhashable", "dstar_keys_protocol", "dstar_bad_keys", "star_generator_error",
          "star_bare", "dstar_in_list", "dstar_in_set", "list_identity"}
Programs == [kind : {"list", "tuple", "set"}, items : UNION {[1..n -> SeqItems] : n \in 0..3}]
            \cup [kind : {"dict"}, items : UNION {[1..n -> DictItems] : n \in 0..3}]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

R(n) == ToString(n)
Equal(a, b) == a = b \/ {a, b} = {"1", "True"}                            \* True == 1

\* What item i logs, and the elements (or the key-value pairs) it gives.
Log(kind, t, i) ==
    CASE kind = "dict" /\ t = "pair" -> <<R(i), R(i + 100)>>
      [] kind = "dict" /\ t = "true_pair" -> <<"True", R(i + 100)>>
      [] kind = "dict" /\ t = "merge" -> <<"{1: " \o R(i + 200) \o "}">>
      [] t = "true" -> <<"True">>
      [] t = "star" -> <<"[" \o R(i) \o ", " \o R(i + 10) \o "]">>
      [] t = "empty" -> <<"[]">>
      [] OTHER -> <<R(i)>>                                             \* plain, and the bad *i or **i
Gives(kind, t, i) ==
    CASE kind = "dict" /\ t = "pair" -> <<<<R(i), R(i + 100)>>>>
      [] kind = "dict" /\ t = "true_pair" -> <<<<"True", R(i + 100)>>>>
      [] kind = "dict" /\ t = "merge" -> <<<<"1", R(i + 200)>>>>
      [] t = "plain" -> <<R(i)>>
      [] t = "true" -> <<"True">>
      [] t = "star" -> <<R(i), R(i + 10)>>
      [] OTHER -> <<>>

Bad(p) == {i \in DOMAIN p.items : p.items[i] = "bad"}
FirstBad(p) == CHOOSE i \in Bad(p) : \A j \in Bad(p) : i <= j

RECURSIVE LogTo(_, _), GivenTo(_, _), Insert(_, _), Merged(_)
LogTo(p, n) == IF n = 0 THEN <<>> ELSE LogTo(p, n - 1) \o Log(p.kind, p.items[n], n)
GivenTo(p, n) == IF n = 0 THEN <<>> ELSE GivenTo(p, n - 1) \o Gives(p.kind, p.items[n], n)

\* A dict keeps the first of equal keys, at its place, with the last value.
Insert(d, e) == IF d = <<>> THEN <<e>>
                ELSE IF Equal(Head(d)[1], e[1]) THEN <<<<Head(d)[1], e[2]>>>> \o Tail(d)
                ELSE <<Head(d)>> \o Insert(Tail(d), e)
Merged(s) == IF s = <<>> THEN <<>> ELSE Insert(Merged(SubSeq(s, 1, Len(s) - 1)), s[Len(s)])

\* A set keeps the first of equal elements.
Kept(s) == {s[k] : k \in {k \in DOMAIN s : \A j \in 1..(k - 1) : ~Equal(s[j], s[k])}}

Display(p) ==
    IF Bad(p) # {} THEN
        <<CASE p.kind = "dict" -> "TypeError: 'int' object is not a mapping"
            [] p.kind = "set" -> "TypeError: 'int' object is not iterable"
            [] OTHER -> "TypeError: Value after * must be an iterable, not int",
          <<>>, LogTo(p, FirstBad(p))>>
    ELSE LET s == GivenTo(p, Len(p.items))
         IN  <<"ok", CASE p.kind = "set" -> Kept(s)
                       [] p.kind = "dict" -> Merged(s)
                       [] OTHER -> s, LogTo(p, Len(p.items))>>

Case(c) ==
    CASE c = "paren_same" -> <<"ok", "True", <<>>>>                      \* (x) is x
      [] c = "paren_yield" -> <<"ok", "5", <<>>>>                        \* (yield 1) receives send(5)
      [] c = "empty" -> <<"ok", "((), [], {}, 'dict')", <<>>>>
      [] c = "tuple_needs_comma" -> <<"ok", "(1, int)", <<>>>>           \* (1,) and (1)
      [] c = "trailing_comma" -> <<"ok", "([1, 2], {1}, {1: 2})", <<>>>>
      [] c = "nested" -> <<"ok", "[1, [2, (3, {4})], {5: [6]}]", <<"1", "2", "3", "4", "5", "6">>>>
      [] c = "dict_unhashable" -> <<"TypeError: cannot use 'list' as a dict key", <<>>, <<>>>>
      [] c = "set_unhashable" -> <<"TypeError: cannot use 'list' as a set element", <<>>, <<>>>>
      [] c = "dict_late_unhashable" -> <<"TypeError: cannot use 'list' as a dict key", <<>>, <<"1", "2", "[]", "3">>>>
      [] c = "dstar_keys_protocol" -> <<"ok", "{'k': 'K'}", <<>>>>         \* keys() and __getitem__
      [] c = "dstar_bad_keys" -> <<"TypeError: M.keys() must return an iterable, not int", <<>>, <<>>>>
      [] c = "star_generator_error" -> <<"ValueError: mid", <<>>, <<"1">>>>
      [] c = "star_bare" -> <<"SyntaxError: can't use starred expression here", <<>>, <<>>>>
      [] c = "dstar_in_list" -> <<"SyntaxError: cannot use dict unpacking here", <<>>, <<>>>>
      [] c = "dstar_in_set" -> <<"SyntaxError: ':' expected after dictionary key", <<>>, <<>>>>
      [] c = "list_identity" -> <<"ok", "True", <<>>>>                   \* [] is not []

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Display(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
IsDisplay == Done /\ "items" \in DOMAIN program

\* Every item is evaluated once, in order, up to the first that fails.
EachItemOnce == IsDisplay =>
    LET n == IF outcome[1] = "ok" THEN Len(program.items) ELSE FirstBad(program)
    IN  Len(outcome[3]) = n + Len(SelectSeq(program.items, LAMBDA t : t \in {"pair", "true_pair"})) -
                             Len(SelectSeq(SubSeq(program.items, n + 1, Len(program.items)), LAMBDA t : t \in {"pair", "true_pair"}))

\* A dict display has no two equal keys.
UniqueKeys == IsDisplay /\ outcome[1] = "ok" /\ program.kind = "dict" =>
    \A i, j \in DOMAIN outcome[2] : i # j => ~Equal(outcome[2][i][1], outcome[2][j][1])
=============================================================================
