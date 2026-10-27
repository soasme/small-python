---------------------------- MODULE Identifiers ----------------------------
(***************************************************************************)
(* Names, as The Python Language Reference specifies them                  *)
(* (reference/lexical_analysis.html#identifiers): a name starts with a     *)
(* character with the XID_Start property (or _) and continues with         *)
(* XID_Continue characters; keywords are reserved, soft keywords are not;  *)
(* names are NFKC-normalized while parsing, so differently spelled names   *)
(* can be the same; and __debug__ cannot be assigned.                      *)
(*                                                                         *)
(* A program is  <name> = 1  for a name spelled with up to three of        *)
(*                                                                         *)
(*     a  1  _  e-acute (U+00E9)  middot (U+00B7)  euro (U+20AC)           *)
(*     fraktur-H (U+210C)  roman-9 (U+2168)  acute (U+0301, combining)     *)
(*                                                                         *)
(* or one of a set of words: keywords, soft keywords, __debug__, and names *)
(* spelled with full-width letters, the ligature fi (U+FB01), e with a     *)
(* combining acute, and superscript two (U+00B2). Characters are named,    *)
(* as TLC's strings are ASCII. The outcome is the name the assignment      *)
(* binds, normalized and spelled as character names joined by ".", or     *)
(* the exception: SyntaxError, or ValueError for a name that normalizes    *)
(* to None, True, or False (CPython's compiler cannot represent it).       *)
(***************************************************************************)
EXTENDS Integers, Sequences

Letters == {"a", "b", "c", "d", "e", "f", "g", "h", "i", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u", "w", "x", "y", "F", "H", "I", "N", "T", "X"}
\* Per character: XID_Start, XID_Continue, and its NFKC form.
Start == Letters \cup {"_", "e-acute", "fraktur-H", "roman-9", "fi", "fw-i", "fw-f", "fw-g", "fw-T"}
Continue == Start \cup {"1", "middot", "acute"}
NFKC(c) == CASE c = "fraktur-H" -> <<"H">> [] c = "roman-9" -> <<"I", "X">> [] c = "fi" -> <<"f", "i">>
             [] c = "fw-i" -> <<"i">> [] c = "fw-f" -> <<"f">> [] c = "fw-g" -> <<"g">> [] c = "fw-T" -> <<"T">>
             [] OTHER -> <<c>>

Alphabet == {"a", "1", "_", "e-acute", "middot", "euro", "fraktur-H", "roman-9", "acute"}
Words == {<<"i", "f">>, <<"N", "o", "n", "e">>, <<"T", "r", "u", "e">>, <<"a", "s", "y", "n", "c">>,
          <<"a", "w", "a", "i", "t">>, <<"m", "a", "t", "c", "h">>, <<"c", "a", "s", "e">>, <<"t", "y", "p", "e">>,
          <<"_", "_", "d", "e", "b", "u", "g", "_", "_">>, <<"_", "_", "d", "e", "b", "u", "fw-g", "_", "_">>,
          <<"fw-i", "fw-f">>, <<"fw-T", "r", "u", "e">>, <<"fi", "x">>, <<"e", "acute">>, <<"x", "sup2">>}
Programs == UNION {[1..n -> Alphabet] : n \in 1..3} \cup Words

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", "">>
Keywords == {<<"i", "f">>, <<"N", "o", "n", "e">>, <<"T", "r", "u", "e">>, <<"F", "a", "l", "s", "e">>,
             <<"a", "s", "y", "n", "c">>, <<"a", "w", "a", "i", "t">>}
Constants == {<<"N", "o", "n", "e">>, <<"T", "r", "u", "e">>, <<"F", "a", "l", "s", "e">>}
Debug == <<"_", "_", "d", "e", "b", "u", "g", "_", "_">>

\* NFKC: each character's compatibility form, then canonical composition
\* (a or e followed by a combining acute is one character).
RECURSIVE Decompose(_)
Decompose(s) == IF s = <<>> THEN <<>> ELSE NFKC(Head(s)) \o Decompose(Tail(s))
RECURSIVE Compose(_)
Compose(s) == CASE Len(s) < 2 -> s
                [] s[1] = "e" /\ s[2] = "acute" -> Compose(<<"e-acute">> \o Tail(Tail(s)))
                [] s[1] = "a" /\ s[2] = "acute" -> Compose(<<"a-acute">> \o Tail(Tail(s)))
                [] OTHER -> <<s[1]>> \o Compose(Tail(s))
Normalize(s) == Compose(Decompose(s))

RECURSIVE Spell(_)
Spell(s) == IF Len(s) = 1 THEN s[1] ELSE s[1] \o "." \o Spell(Tail(s))

Assign(s) ==
    CASE s[1] \notin Start \/ \E i \in DOMAIN s : s[i] \notin Continue -> <<"SyntaxError", "">>
      [] s \in Keywords -> <<"SyntaxError", "">>                      \* keywords are matched as spelled
      [] Normalize(s) \in Constants -> <<"ValueError", "">>
      [] Normalize(s) = Debug -> <<"SyntaxError", "">>                 \* cannot assign to __debug__
      [] OTHER -> <<"ok", Spell(Normalize(s))>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Assign(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Normalizing twice changes nothing more.
Idempotent == Done /\ outcome[1] = "ok" => Normalize(Normalize(program)) = Normalize(program)

\* Soft keywords are names.
SoftKeywords == Done /\ program \in {<<"m", "a", "t", "c", "h">>, <<"c", "a", "s", "e">>, <<"t", "y", "p", "e">>, <<"_">>}
                => outcome = <<"ok", Spell(program)>>
=============================================================================
