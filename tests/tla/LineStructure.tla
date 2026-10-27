--------------------------- MODULE LineStructure ---------------------------
(***************************************************************************)
(* Line structure, as The Python Language Reference specifies it           *)
(* (reference/lexical_analysis.html#line-structure): physical lines ended  *)
(* by LF, CR LF, or CR; logical lines; comments; explicit joining with a   *)
(* backslash, which must end its line; implicit joining inside brackets;   *)
(* blank lines; and encoding declarations. Two families of programs:       *)
(*                                                                         *)
(*   - "r = " followed by up to five characters from  1 + ( ) \ # and      *)
(*     newline (with CR LF or CR for up to four), run as a module. These   *)
(*     form numbers, unary and binary +, parentheses, calls such as 1(1),  *)
(*     and the empty tuple (). The outcome is r's repr, or the exception.  *)
(*                                                                         *)
(*   - byte sources whose first two lines are each "pass", a comment, or   *)
(*     an encoding declaration "# -*- coding: <codec> -*-", optionally     *)
(*     after a UTF-8 byte order mark, followed by  r = '<payload>'  where  *)
(*     the payload is the byte E9 or the bytes C3 A9. The outcome is r's   *)
(*     code points, or SyntaxError.                                        *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Chars == {"1", "+", "(", ")", "\\", "#", "\n"}
Joining == {[kind |-> "join", chars |-> s, eol |-> "\n"] : s \in UNION {[1..n -> Chars] : n \in 1..5}}
           \cup {[kind |-> "join", chars |-> s, eol |-> e] : s \in UNION {[1..n -> Chars] : n \in 1..4}, e \in {"\r\n", "\r"}}
Codecs == {"latin-1", "utf-8", "ascii", "bogus"}
Encoding == [kind : {"encoding"}, first : {"decl", "comment", "pass"}, second : {"decl", "comment", "pass"},
             codec : Codecs, payload : {<<233>>, <<195, 169>>}, bom : BOOLEAN]
Programs == Joining \cup Encoding

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", "">>
Error(name) == <<name, "">>
At(s, i) == IF i >= 1 /\ i <= Len(s) THEN s[i] ELSE "EOF"

(***************************************************************************)
(* Joining. Tokens, as <<kind, value>>: numbers, "+", "(", ")", and "nl"   *)
(* (NEWLINE), or "error"; a comment runs to the end of its line, a         *)
(* backslash joins its line with the next, and a newline inside brackets   *)
(* is ignored.                                                             *)
(***************************************************************************)
RECURSIVE Digits(_, _)
Digits(s, i) == IF At(s, i) = "1" THEN Digits(s, i + 1) ELSE i
RECURSIVE Ones(_)
Ones(n) == IF n = 0 THEN 0 ELSE 10 * Ones(n - 1) + 1
T(kind) == <<kind, 0>>
RECURSIVE Lex(_, _, _)
Lex(s, i, depth) ==
    CASE i > Len(s) -> IF depth > 0 THEN <<T("error")>> ELSE <<>>      \* an unclosed bracket
      [] s[i] = "#" -> LET RECURSIVE Skip(_) Skip(j) == IF At(s, j) \in {"\n", "EOF"} THEN j ELSE Skip(j + 1)
                       IN  Lex(s, Skip(i), depth)
      \* A backslash joins only with a following line.
      [] s[i] = "\\" -> IF At(s, i + 1) = "\n" /\ i + 2 <= Len(s) THEN Lex(s, i + 2, depth) ELSE <<T("error")>>
      [] s[i] = "\n" -> IF depth > 0 THEN Lex(s, i + 1, depth) ELSE <<T("nl")>> \o Lex(s, i + 1, depth)
      [] s[i] = "1" -> <<<<"num", Ones(Digits(s, i) - i)>>>> \o Lex(s, Digits(s, i), depth)
      [] s[i] = "(" -> <<T("(")>> \o Lex(s, i + 1, depth + 1)
      [] s[i] = ")" -> IF depth = 0 THEN <<T("error")>> ELSE <<T(")")>> \o Lex(s, i + 1, depth - 1)
      [] s[i] = "+" -> <<T("+")>> \o Lex(s, i + 1, depth)
Kind(t, i) == IF i >= 1 /\ i <= Len(t) THEN t[i][1] ELSE "EOF"

\* Expressions over the tokens t[i..]: <<ok, next position, value>>. A value
\* is <<"int", n>>, <<"tuple", 0>> (the empty tuple), or <<"TypeError", 0>>
\* once an operation fails; parsing goes on to find syntax errors.
Failed == <<"TypeError", 0>>
Plus(a, b) == CASE a[1] = "int" /\ b[1] = "int" -> <<"int", a[2] + b[2]>>
                [] a[1] = "tuple" /\ b[1] = "tuple" -> a          \* () + () == ()
                [] OTHER -> Failed
RECURSIVE Expr(_, _), Unary(_, _), Primary(_, _), Calls(_, _, _), More(_, _, _)
Expr(t, i) == LET u == Unary(t, i) IN IF ~u[1] THEN u ELSE More(t, u[2], u[3])
More(t, i, v) == IF Kind(t, i) = "+" THEN LET u == Unary(t, i + 1) IN IF ~u[1] THEN u ELSE More(t, u[2], Plus(v, u[3]))
                 ELSE <<TRUE, i, v>>
Unary(t, i) == IF Kind(t, i) = "+" THEN LET u == Unary(t, i + 1)
                                        IN  IF ~u[1] THEN u ELSE <<TRUE, u[2], IF u[3][1] = "int" THEN u[3] ELSE Failed>>
               ELSE Primary(t, i)
Primary(t, i) ==
    CASE Kind(t, i) = "num" -> Calls(t, i + 1, <<"int", t[i][2]>>)
      [] Kind(t, i) = "(" /\ Kind(t, i + 1) = ")" -> Calls(t, i + 2, <<"tuple", 0>>)
      [] Kind(t, i) = "(" -> LET e == Expr(t, i + 1)
                             IN  IF e[1] /\ Kind(t, e[2]) = ")" THEN Calls(t, e[2] + 1, e[3]) ELSE <<FALSE, 0, Failed>>
      [] OTHER -> <<FALSE, 0, Failed>>
\* A call f() or f(x): neither an int nor () can be called.
Calls(t, i, v) ==
    IF Kind(t, i) # "(" THEN <<TRUE, i, v>>
    ELSE IF Kind(t, i + 1) = ")" THEN Calls(t, i + 2, Failed)
    ELSE LET e == Expr(t, i + 1)
         IN  IF e[1] /\ Kind(t, e[2]) = ")" THEN Calls(t, e[2] + 1, Failed) ELSE <<FALSE, 0, Failed>>

\* Logical lines: "r = <expression>" first, then expression statements;
\* the first line's tokens follow "r = " directly. <<ok, raised>>
RECURSIVE Lines(_, _)
Lines(t, i) ==
    IF i > Len(t) THEN <<TRUE, FALSE>>
    ELSE IF Kind(t, i) = "nl" THEN Lines(t, i + 1)                    \* a blank line
    ELSE LET e == Expr(t, i)
         IN  IF ~e[1] \/ Kind(t, e[2]) \notin {"nl", "EOF"} THEN <<FALSE, FALSE>>
             ELSE LET rest == Lines(t, e[2]) IN <<rest[1], rest[2] \/ e[3] = Failed>>
Join(p) ==
    LET t == Lex(p.chars, 1, 0)
        e == Expr(t, 1)
        rest == Lines(t, e[2])
    IN  CASE \E i \in DOMAIN t : t[i][1] = "error" -> Error("SyntaxError")
          [] ~e[1] \/ Kind(t, e[2]) \notin {"nl", "EOF"} \/ ~rest[1] -> Error("SyntaxError")
          [] e[3] = Failed \/ rest[2] -> Error("TypeError")
          [] e[3][1] = "tuple" -> <<"value", "()">>
          [] OTHER -> <<"value", ToString(e[3][2])>>

(***************************************************************************)
(* Encoding declarations: a comment on line 1, or on line 2 after a        *)
(* comment-only line 1, names the source encoding; the default is UTF-8.  *)
(* A byte order mark requires UTF-8.                                       *)
(***************************************************************************)
Codec(p) == IF p.first = "decl" THEN p.codec
            ELSE IF p.second = "decl" /\ p.first = "comment" THEN p.codec
            ELSE "utf-8"
Decode(codec, b) ==
    CASE codec = "latin-1" -> b
      [] codec = "utf-8" -> IF b = <<195, 169>> THEN <<233>> ELSE <<>>
      [] OTHER -> <<>>
Encode(p) ==
    LET codec == Codec(p)  value == Decode(codec, p.payload)
    IN  IF codec = "bogus" \/ (p.bom /\ codec # "utf-8") \/ value = <<>> THEN Error("SyntaxError")
        ELSE <<"value", IF Len(value) = 1 THEN ToString(value[1]) ELSE ToString(value[1]) \o "," \o ToString(value[2])>>

Run(p) == IF p.kind = "join" THEN Join(p) ELSE Encode(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Every physical line ending means the same.
LineEndings == Done /\ program.kind = "join" => outcome = Join([program EXCEPT !.eol = "\n"])

\* A comment at the end of a program that runs changes nothing.
TrailingComment == Done /\ program.kind = "join" /\ Len(program.chars) < 5 /\ outcome[1] = "value" =>
    Join([program EXCEPT !.chars = Append(program.chars, "#")]) = outcome

\* A declaration on the second line counts only after a comment.
SecondLine == Done /\ program.kind = "encoding" /\ program.first = "pass" /\ program.payload = <<195, 169>> /\ ~program.bom
              => outcome = <<"value", "233">>
=============================================================================
