--------------------------- MODULE StringLiterals ---------------------------
(***************************************************************************)
(* String and bytes literals, as The Python Language Reference specifies   *)
(* them (reference/lexical_analysis.html#string-and-bytes-literals):       *)
(* quotes and triple quotes, prefixes, escape sequences (ignored end of    *)
(* line, escaped characters, octal, hexadecimal, named and hexadecimal     *)
(* Unicode characters, unrecognized escapes, which are kept), raw strings, *)
(* bytes, and the concatenation of adjacent literals.                      *)
(*                                                                         *)
(* A program is a literal  <prefix><quote><body><quote>  evaluated in      *)
(* parentheses (so newlines between literals join lines). Its body is      *)
(*                                                                         *)
(*   - any string of up to four of  a  q  0  '  \  newline,  with prefix   *)
(*     "", r, b, or rb and quote ' or ''', so that quotes in the body end  *)
(*     the literal early and start others; or                              *)
(*   - one of a set of longer escape sequences (\x41, A, \U0010ffff,  *)
(*     \N{SPACE}, \400, and malformed ones), with the prefixes "", r, b,   *)
(*     rb, Rb, u, and ub (not a prefix).                                    *)
(*                                                                         *)
(* The outcome is the value, as str or bytes and its code points, or       *)
(* SyntaxError. The SyntaxWarning for unrecognized escapes is not modeled. *)
(***************************************************************************)
EXTENDS Integers, Sequences, FiniteSets, TLC

BodyA == {"a", "q", "0", "'", "\\", "\n"}
BodiesB == {<<"\\", "x", "4", "1">>,
            <<"\\", "x", "4">>,
            <<"\\", "x", "g", "0">>,
            <<"\\", "x", "f", "f">>,
            <<"\\", "x", "7", "F">>,
            <<"\\", "u", "0", "0", "4", "1">>,
            <<"\\", "u", "0", "0", "4">>,
            <<"\\", "u">>,
            <<"\\", "U", "0", "0", "0", "0", "0", "0", "4", "1">>,
            <<"\\", "U", "0", "0", "1", "0", "f", "f", "f", "f">>,
            <<"\\", "U", "0", "0", "1", "1", "0", "0", "0", "0">>,
            <<"\\", "N", "{", "S", "P", "A", "C", "E", "}">>,
            <<"\\", "N", "{", "s", "p", "a", "c", "e", "}">>,
            <<"\\", "N", "{", "L", "A", "T", "I", "N", " ", "S", "M", "A", "L", "L", " ", "L", "E", "T", "T", "E", "R", " ", "A", "}">>,
            <<"\\", "N", "{", "}">>,
            <<"\\", "N", "{", "N", "O", "P", "E", "}">>,
            <<"\\", "N", "{", "S", "P", "A", "C", "E">>,
            <<"\\", "N">>,
            <<"\\", "1", "0", "1">>,
            <<"\\", "4", "0", "0">>,
            <<"\\", "7", "7", "7">>,
            <<"\\", "8">>,
            <<"\\", "1", "8">>,
            <<"\\", "1">>}
PrefixesA == {"", "r", "b", "rb"}
PrefixesB == {"", "r", "b", "rb", "Rb", "u", "ub"}
Programs == {[prefix |-> x, triple |-> t, body |-> s] :
                x \in PrefixesA, t \in BOOLEAN, s \in UNION {[1..n -> BodyA] : n \in 0..4}}
            \cup {[prefix |-> x, triple |-> FALSE, body |-> s] : x \in PrefixesB, s \in BodiesB}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", <<>>>>
Error == <<"SyntaxError", <<>>>>

\* Code points, hexadecimal digits, upper case, the one-character escapes,
\* and the character names the bodies use.
Ord == ("\n" :> 10) @@ (" " :> 32) @@ ("'" :> 39) @@ ("0" :> 48) @@ ("1" :> 49) @@ ("4" :> 52) @@ ("7" :> 55) @@ ("8" :> 56) @@ ("A" :> 65) @@ ("C" :> 67) @@ ("E" :> 69) @@ ("F" :> 70) @@ ("I" :> 73) @@ ("L" :> 76) @@ ("M" :> 77) @@ ("N" :> 78) @@ ("O" :> 79) @@ ("P" :> 80) @@ ("R" :> 82) @@ ("S" :> 83) @@ ("T" :> 84) @@ ("U" :> 85) @@ ("\\" :> 92) @@ ("a" :> 97) @@ ("c" :> 99) @@ ("e" :> 101) @@ ("f" :> 102) @@ ("g" :> 103) @@ ("p" :> 112) @@ ("q" :> 113) @@ ("s" :> 115) @@ ("u" :> 117) @@ ("x" :> 120) @@ ("{" :> 123) @@ ("}" :> 125)
HexValue == ("0" :> 0) @@ ("1" :> 1) @@ ("4" :> 4) @@ ("7" :> 7) @@ ("8" :> 8) @@ ("A" :> 10) @@ ("C" :> 12) @@ ("E" :> 14) @@ ("F" :> 15) @@ ("a" :> 10) @@ ("c" :> 12) @@ ("e" :> 14) @@ ("f" :> 15)
Uppercase == ("a" :> "A") @@ ("c" :> "C") @@ ("e" :> "E") @@ ("f" :> "F") @@ ("g" :> "G") @@ ("p" :> "P") @@ ("q" :> "Q") @@ ("s" :> "S") @@ ("u" :> "U") @@ ("x" :> "X")
Simple == ("\\" :> 92) @@ ("'" :> 39) @@ ("\"" :> 34) @@ ("a" :> 7) @@ ("b" :> 8) @@ ("f" :> 12) @@ ("n" :> 10) @@ ("r" :> 13) @@ ("t" :> 9) @@ ("v" :> 11)
Names == (<<"S", "P", "A", "C", "E">> :> 32) @@ (<<"L", "A", "T", "I", "N", " ", "S", "M", "A", "L", "L", " ", "L", "E", "T", "T", "E", "R", " ", "A">> :> 97)
Upper(c) == IF c \in DOMAIN Uppercase THEN Uppercase[c] ELSE c
At(s, i) == IF i >= 1 /\ i <= Len(s) THEN s[i] ELSE "EOF"
Range(s) == {s[i] : i \in DOMAIN s}

ValidPrefixes == {"", "r", "R", "b", "B", "rb", "rB", "Rb", "RB", "br", "bR", "Br", "BR", "u", "U"}
IsRaw(x) == x \in {"r", "R", "rb", "rB", "Rb", "RB", "br", "bR", "Br", "BR"}
IsBytes(x) == x \in {"b", "B", "rb", "rB", "Rb", "RB", "br", "bR", "Br", "BR"}

\* The content of a literal whose body starts at j, up to its closing
\* quote: a backslash keeps the next character in the literal (even in a
\* raw one), and only triple quotes allow a newline.
RECURSIVE Content(_, _, _, _)
Content(s, j, triple, acc) ==
    CASE j > Len(s) -> <<0, acc>>                                   \* unterminated
      [] s[j] = "\\" -> IF j = Len(s) THEN <<0, acc>> ELSE Content(s, j + 2, triple, acc \o <<s[j], s[j + 1]>>)
      [] ~triple /\ s[j] = "'" -> <<j + 1, acc>>
      [] triple /\ s[j] = "'" /\ At(s, j + 1) = "'" /\ At(s, j + 2) = "'" -> <<j + 3, acc>>
      [] ~triple /\ s[j] = "\n" -> <<0, acc>>
      [] OTHER -> Content(s, j + 1, triple, acc \o <<s[j]>>)

\* The literal's value from its content: <<ok, code points>>.
IsHex(c) == c \in DOMAIN HexValue
RECURSIVE HexRun(_, _, _)
HexRun(c, i, n) == IF n = 0 THEN 0 ELSE HexValue[c[i]] * (16 ^ (n - 1)) + HexRun(c, i + 1, n - 1)
Hex(c, i, n) == /\ i + n - 1 <= Len(c)
                /\ \A k \in i..(i + n - 1) : IsHex(c[k])
IsOctal(c) == c \in {"0", "1", "4", "7"}
OctalValue(c) == CASE c = "0" -> 0 [] c = "1" -> 1 [] c = "4" -> 4 [] c = "7" -> 7
RECURSIVE Octal(_, _, _, _)
Octal(c, i, n, v) == IF n < 3 /\ IsOctal(At(c, i)) THEN Octal(c, i + 1, n + 1, v * 8 + OctalValue(c[i])) ELSE <<i, v>>
RECURSIVE Close(_, _)
Close(c, i) == IF i > Len(c) THEN 0 ELSE IF c[i] = "}" THEN i ELSE Close(c, i + 1)

RECURSIVE Decode(_, _, _)
Decode(c, i, bytes) ==
    IF i > Len(c) THEN <<TRUE, <<>>>>
    ELSE IF c[i] # "\\" THEN LET r == Decode(c, i + 1, bytes) IN <<r[1], <<Ord[c[i]]>> \o r[2]>>
    ELSE LET d == c[i + 1]
             Then(code, j) == LET r == Decode(c, j, bytes) IN <<r[1], <<code>> \o r[2]>>
             Fail == <<FALSE, <<>>>>
         IN  CASE d = "\n" -> Decode(c, i + 2, bytes)                \* ignored end of line
               [] d \in DOMAIN Simple -> Then(Simple[d], i + 2)
               [] IsOctal(d) -> LET o == Octal(c, i + 1, 0, 0)
                                IN  Then(IF bytes THEN o[2] % 256 ELSE o[2], o[1])
               [] d = "x" -> IF Hex(c, i + 2, 2) THEN Then(HexRun(c, i + 2, 2), i + 4) ELSE Fail
               [] d = "u" /\ ~bytes -> IF Hex(c, i + 2, 4) THEN Then(HexRun(c, i + 2, 4), i + 6) ELSE Fail
               [] d = "U" /\ ~bytes -> IF Hex(c, i + 2, 8) /\ HexRun(c, i + 2, 8) <= 1114111
                                       THEN Then(HexRun(c, i + 2, 8), i + 10) ELSE Fail
               [] d = "N" /\ ~bytes ->
                    LET e == Close(c, i + 3)
                        name == [k \in 1..(e - i - 3) |-> Upper(c[i + 2 + k])]
                    IN  IF At(c, i + 2) # "{" \/ e = 0 \/ name \notin DOMAIN Names THEN Fail
                        ELSE Then(Names[name], e + 1)
               \* Unrecognized: the backslash is kept, and the character
               \* after it is read as usual.
               [] OTHER -> LET r == Decode(c, i + 1, bytes) IN <<r[1], <<92>> \o r[2]>>

\* The literals of the source from position i, adjacent or separated by
\* newlines or backslash-newline: <<ok, <<bytes, code points>> ...>>.
RECURSIVE Literals(_, _, _)
Literals(s, i, prefix) ==
    CASE i > Len(s) -> <<TRUE, <<>>>>
      [] s[i] = "\n" -> Literals(s, i + 1, "")
      [] s[i] = "\\" /\ At(s, i + 1) = "\n" -> Literals(s, i + 2, "")
      [] s[i] = "'" ->
            LET triple == At(s, i + 1) = "'" /\ At(s, i + 2) = "'"
                c == Content(s, i + (IF triple THEN 3 ELSE 1), triple, <<>>)
                v == IF IsRaw(prefix) THEN <<TRUE, [k \in DOMAIN c[2] |-> Ord[c[2][k]]]>>
                     ELSE Decode(c[2], 1, IsBytes(prefix))
                rest == Literals(s, c[1], "")
            IN  IF c[1] = 0 \/ ~v[1] \/ ~rest[1] THEN <<FALSE, <<>>>>
                ELSE <<TRUE, <<<<IsBytes(prefix), v[2]>>>> \o rest[2]>>
      [] OTHER -> <<FALSE, <<>>>>

Evaluate(p) ==
    LET quote == IF p.triple THEN <<"'", "'", "'">> ELSE <<"'">>
        r == Literals(quote \o p.body \o quote, 1, p.prefix)
        kinds == {r[2][k][1] : k \in DOMAIN r[2]}
        RECURSIVE Join(_)
        Join(k) == IF k > Len(r[2]) THEN <<>> ELSE r[2][k][2] \o Join(k + 1)
    IN  IF p.prefix \notin ValidPrefixes \/ ~r[1] \/ Cardinality(kinds) > 1 THEN Error   \* bytes and str cannot mix
        ELSE <<IF TRUE \in kinds THEN "bytes" ELSE "str", Join(1)>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Evaluate(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Escapes never lengthen a literal: each produces at most one code point
\* per source character (an unrecognized one keeps both).
NeverLonger == Done /\ outcome # Error => Len(outcome[2]) <= Len(program.body)

\* Bytes hold bytes.
BytesInRange == Done /\ outcome[1] = "bytes" => \A k \in DOMAIN outcome[2] : outcome[2][k] < 256
=============================================================================
