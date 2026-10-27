------------------------------ MODULE FStrings ------------------------------
(***************************************************************************)
(* f-strings, as The Python Language Reference specifies them              *)
(* (reference/lexical_analysis.html#f-strings and #formal-grammar-for-f-   *)
(* strings): literal text with doubled braces, replacement fields of an    *)
(* expression, an optional "=" that adds the expression's text, an         *)
(* optional conversion, and an optional format specification that may hold *)
(* replacement fields itself (but no deeper); fields are evaluated left to *)
(* right and formatted with format().                                      *)
(*                                                                         *)
(* A program is  f'<body>'  evaluated with x bound to an object whose      *)
(* __format__(spec) is "<" + spec + ">", whose repr() is "R", and whose == *)
(* and != return itself. The body is up to five characters from            *)
(*                                                                         *)
(*     {  }  x  r  !  =  :  space                                          *)
(*                                                                         *)
(* or one of a set of longer bodies. The name r is unbound. The outcome is *)
(* the string, or the exception.                                           *)
(***************************************************************************)
EXTENDS Integers, Sequences

Chars == {"{", "}", "x", "r", "!", "=", ":", " "}
S(text) == [k \in 1..Len(text) |-> CASE text[k] = 1 -> "{" [] text[k] = 2 -> "}" [] text[k] = 3 -> "x"
                                     [] text[k] = 4 -> "r" [] text[k] = 5 -> "!" [] text[k] = 6 -> "="
                                     [] text[k] = 7 -> ":" [] text[k] = 8 -> " " [] text[k] = 9 -> "#"
                                     [] text[k] = 10 -> "\n"]
\* Longer bodies, spelled with the codes above.
Bodies == {<<1, 3, 7, 1, 3, 2, 2>>,                     \* {x:{x}}
           <<1, 3, 7, 1, 3, 7, 1, 3, 2, 2, 2>>,         \* {x:{x:{x}}}
           <<1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 2, 2, 2, 2>>,  \* {x:{x:{x:{x}}}}  (too deep)
           <<1, 8, 1, 2, 7, 3, 2>>,                     \* { {}:x}
           <<1, 8, 1, 2, 6, 2>>,                        \* { {}=}
           <<1, 3, 5, 4, 8, 2>>,                        \* {x!r }
           <<1, 3, 5, 4, 7, 1, 3, 7, 3, 2, 2>>,         \* {x!r:{x:x}}
           <<1, 3, 6, 5, 4, 7, 1, 3, 2, 2>>,            \* {x=!r:{x}}
           <<1, 3, 7, 1, 3, 2, 3, 1, 3, 2, 2>>,         \* {x:{x}x{x}}
           <<1, 3, 7, 1, 1, 2, 2, 2>>,                  \* {x:{{}}}
           <<1, 8, 3, 8, 6, 8, 5, 4, 2>>,               \* { x = !r}
           <<1, 3, 6, 6, 3, 6, 2>>,                     \* {x==x=}
           <<1, 3, 5, 6, 3, 6, 7, 6, 2>>,               \* {x!=x=:=}
           <<1, 3, 8, 9, 3, 10, 2>>,                    \* {x #x<newline>}
           <<1, 10, 3, 10, 6, 10, 2>>,                  \* {<newline>x<newline>=<newline>}
           <<1, 4, 7, 1, 3, 2, 2>>,                     \* {r:{x}}
           <<1, 3, 7, 1, 4, 2, 2>>,                     \* {x:{r}}
           <<1, 3, 5, 4, 7, 1, 3, 2, 2>>,               \* {x!r:{x}}
           <<1, 3, 5, 4, 7, 2, 1, 4, 2>>,               \* {x!r:}{r}
           <<1, 4, 2, 1, 3, 5, 4, 7, 3, 2>>}            \* {r}{x!r:x}
Programs == UNION {[1..n -> Chars] : n \in 0..5} \cup {S(b) : b \in Bodies}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", "">>
At(s, i) == IF i >= 1 /\ i <= Len(s) THEN s[i] ELSE "EOF"
RECURSIVE Text(_, _, _)
Text(s, a, b) == IF a >= b THEN "" ELSE s[a] \o Text(s, a + 1, b)

(***************************************************************************)
(* Values, as <<kind, text>>: <<"str", text>>, <<"F", "">> (the object),   *)
(* <<"dict", "">> (an empty dict display), or an exception. Parsing returns <<ok, next position, value>>; values   *)
(* are computed as parsing goes, an exception carried along, so that the   *)
(* first one raised wins and a syntax error anywhere wins over all.        *)
(***************************************************************************)
Failed(v) == v[1] \notin {"str", "F", "dict"}
Then(x, y, F(_, _)) == IF Failed(x) THEN x ELSE IF Failed(y) THEN y ELSE F(x, y)
Cat(x, y) == Then(x, y, LAMBDA a, b : <<"str", a[2] \o b[2]>>)
Fail == <<FALSE, 0, <<"SyntaxError", "">>>>
Str(text) == <<"str", text>>

Letter(c) == c \in {"x", "r"}
RECURSIVE NameEnd(_, _), Spaces(_, _)
NameEnd(s, i) == IF Letter(At(s, i)) THEN NameEnd(s, i + 1) ELSE i
Spaces(s, i) == IF At(s, i) \in {" ", "\n"} THEN Spaces(s, i + 1) ELSE i
\* A comment runs to the end of its line.
Blank(s, i) == LET j == Spaces(s, i)
               IN  IF At(s, j) = "#" THEN LET RECURSIVE Eol(_) Eol(k) == IF At(s, k) \in {"\n", "EOF"} THEN k ELSE Eol(k + 1)
                                          IN  Spaces(s, Eol(j))
                   ELSE j
Operand(s, i) ==
    LET a == Blank(s, i)  b == NameEnd(s, a)
    IN  IF At(s, a) = "{" THEN IF At(s, Blank(s, a + 1)) = "}" THEN <<TRUE, Blank(s, Blank(s, a + 1) + 1), <<"dict", "">>>> ELSE Fail
        ELSE IF a = b THEN Fail ELSE <<TRUE, Blank(s, b), IF Text(s, a, b) = "x" THEN <<"F", "">> ELSE <<"NameError", "">>>>
\* Comparisons with == and != (which return the object).
RECURSIVE Compare(_, _, _)
Compare(s, i, v) ==
    IF At(s, i) \in {"=", "!"} /\ At(s, i + 1) = "="
    THEN LET o == Operand(s, i + 2) IN IF ~o[1] THEN o ELSE Compare(s, o[2], Then(v, o[3], LAMBDA a, b : a))
    ELSE <<TRUE, i, v>>
Expression(s, i) == LET o == Operand(s, i) IN IF ~o[1] THEN o ELSE Compare(s, o[2], o[3])

Convert(v) == CASE Failed(v) \/ v[1] = "str" -> v [] v[1] = "dict" -> Str("{}") [] OTHER -> Str("R")
Format(v, spec) == CASE Failed(v) -> v
                     [] Failed(spec) -> spec
                     [] v[1] = "F" -> Str("<" \o spec[2] \o ">")
                     [] spec[2] = "" -> IF v[1] = "dict" THEN Str("{}") ELSE v
                     [] v[1] = "dict" -> <<"TypeError", "">>
                     [] spec[2] = "<>" -> v                     \* fill "<", align ">"
                     [] OTHER -> <<"ValueError", "">>     \* no other such spec for str

(***************************************************************************)
(* Literal text and fields from i, to the end (depth 0) or to the "}" that *)
(* ends a format specification (depth > 0, which is not consumed).         *)
(***************************************************************************)
RECURSIVE Body(_, _, _), Field(_, _, _)
Body(s, i, depth) ==
    LET More(j, v) == LET r == Body(s, j, depth) IN IF ~r[1] THEN r ELSE <<TRUE, r[2], Cat(v, r[3])>>
    IN  CASE i > Len(s) -> IF depth = 0 THEN <<TRUE, i, Str("")>> ELSE Fail
          [] s[i] = "{" /\ At(s, i + 1) = "{" /\ depth = 0 -> More(i + 2, Str("{"))
          [] s[i] = "{" -> LET f == Field(s, i + 1, depth) IN IF ~f[1] THEN f ELSE More(f[2], f[3])
          [] s[i] = "}" /\ depth > 0 -> <<TRUE, i, Str("")>>
          [] s[i] = "}" /\ At(s, i + 1) = "}" -> More(i + 2, Str("}"))
          [] s[i] = "}" -> Fail                                      \* single '}'
          [] OTHER -> More(i + 1, Str(s[i]))
\* A replacement field after its "{"; returns the position after its "}".
Field(s, i, depth) ==
    LET e == Expression(s, i)
        debug == e[1] /\ At(s, e[2]) = "=" /\ At(s, e[2] + 1) # "="
        j == IF debug THEN Spaces(s, e[2] + 1) ELSE e[2]
        conversion == At(s, j) = "!"
        k == IF conversion THEN Spaces(s, NameEnd(s, j + 1)) ELSE j
        spec == IF At(s, k) = ":" THEN Body(s, k + 1, depth + 1) ELSE <<TRUE, k, Str("")>>
        value == IF conversion \/ (debug /\ At(s, k) # ":") THEN Convert(e[3]) ELSE e[3]
    IN  CASE depth >= 3 -> Fail                                     \* nested too deeply
          [] ~e[1] -> Fail
          [] conversion /\ Text(s, j + 1, NameEnd(s, j + 1)) # "r" -> Fail
          [] ~spec[1] \/ At(s, spec[2]) # "}" -> Fail
          [] OTHER -> <<TRUE, spec[2] + 1,
                        Cat(Str(IF debug THEN Text(s, i, j) ELSE ""), Format(value, spec[3]))>>

Evaluate(s) == LET r == Body(s, 1, 0) IN IF ~r[1] THEN <<"SyntaxError", "">> ELSE IF Failed(r[3]) THEN <<r[3][1], "">> ELSE r[3]

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Evaluate(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Text without braces is itself.
Plain == Done /\ (\A k \in DOMAIN program : program[k] \notin {"{", "}"}) => outcome = Str(Text(program, 1, Len(program) + 1))

\* Doubled braces stand for themselves.
Doubled == Done /\ Len(program) <= 3 /\ outcome[1] = "str" =>
    Evaluate(<<"{", "{">> \o program \o <<"}", "}">>) = Str("{" \o outcome[2] \o "}")
=============================================================================
