-------------------------- MODULE NumericLiterals --------------------------
(***************************************************************************)
(* Numeric literals, as The Python Language Reference specifies them       *)
(* (reference/lexical_analysis.html#numeric-literals): integer literals in *)
(* decimal, hexadecimal, and binary, with underscores between digits and   *)
(* no leading zeros in a nonzero decimal; floating-point literals with a   *)
(* fraction, an exponent, or both; imaginary literals; and the rule that a *)
(* numeric literal may not run into an identifier ("1x" is not 1 followed  *)
(* by x). A program is every string of up to four characters from         *)
(*                                                                         *)
(*     0  1  _  .  e  j  x  b                                              *)
(*                                                                         *)
(* evaluated as an expression with no names defined. Besides literals,     *)
(* such strings form names, attribute references, and the ellipsis "...".  *)
(* The outcome is the value's repr, SyntaxError, NameError, or             *)
(* AttributeError (no int, float, complex, or Ellipsis attribute is        *)
(* spelled with these letters).                                            *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Alphabet == {"0", "1", "_", ".", "e", "j", "x", "b"}
Programs == UNION {[1..n -> Alphabet] : n \in 1..4}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", "">>

IsDigit(c) == c \in {"0", "1"}
IdStart(c) == c \in {"_", "e", "j", "x", "b"}
IdChar(c) == IdStart(c) \/ IsDigit(c)
InBase(c, base) == IF base = 2 THEN IsDigit(c) ELSE c \in {"0", "1", "b", "e"}
DigitValue(c) == CASE c = "0" -> 0 [] c = "1" -> 1 [] c = "b" -> 11 [] c = "e" -> 14
At(s, i) == IF i >= 1 /\ i <= Len(s) THEN s[i] ELSE "EOF"

\* The value of the digits of s[a..b-1] in a base, skipping underscores and
\* a decimal point.
RECURSIVE Value(_, _, _, _)
Value(s, a, b, base) == IF b <= a THEN 0
                        ELSE IF s[b - 1] \in {"_", "."} THEN Value(s, a, b - 1, base)
                        ELSE Value(s, a, b - 1, base) * base + DigitValue(s[b - 1])
RECURSIVE Count(_, _, _)
Count(s, a, b) == IF b <= a THEN 0 ELSE Count(s, a, b - 1) + (IF IsDigit(s[b - 1]) THEN 1 ELSE 0)

\* Tokens. A number token is an int with value v, or a float or imaginary
\* number with value m * 10^k.
Err == [kind |-> "error", end |-> 0, v |-> 0, m |-> 0, k |-> 0]
Tok(kind, end, v, m, k) == [kind |-> kind, end |-> end, v |-> v, m |-> m, k |-> k]

\* digit (["_"] digit)*, after a first digit at i - 1: the position after
\* it, and whether an underscore was not followed by a digit.
RECURSIVE DecTail(_, _)
DecTail(s, i) == IF IsDigit(At(s, i)) THEN DecTail(s, i + 1)
                 ELSE IF At(s, i) = "_" THEN (IF IsDigit(At(s, i + 1)) THEN DecTail(s, i + 2) ELSE <<i, FALSE>>)
                 ELSE <<i, TRUE>>

\* A literal ends where no identifier character follows it.
Ends(s, i) == ~IdChar(At(s, i))

\* After the mantissa (digits s[a..f-1] with fl fraction digits) at j: an
\* exponent, a j suffix, or the end of a float.
FloatTail(s, a, f, fl, j, imagOnly) ==
    LET m == Value(s, a, f, 10)
    IN  IF At(s, j) = "e" THEN
            IF ~IsDigit(At(s, j + 1)) THEN Err
            ELSE LET t == DecTail(s, j + 2)  e == Value(s, j + 1, t[1], 10)
                 IN  IF ~t[2] THEN Err
                     ELSE IF At(s, t[1]) = "j" THEN (IF Ends(s, t[1] + 1) THEN Tok("imag", t[1] + 1, 0, m, e - fl) ELSE Err)
                     ELSE IF Ends(s, t[1]) THEN Tok("float", t[1], 0, m, e - fl) ELSE Err
        ELSE IF At(s, j) = "j" THEN (IF Ends(s, j + 1) THEN Tok("imag", j + 1, 0, m, -fl) ELSE Err)
        ELSE IF imagOnly THEN Err
        ELSE IF Ends(s, j) THEN Tok("float", j, 0, m, -fl) ELSE Err

\* A fraction: the digits after the point at dot, if any (the integer part
\* is s[a..dot-1]).
Fraction(s, a, dot) ==
    IF IsDigit(At(s, dot + 1))
    THEN LET t == DecTail(s, dot + 2)
         IN  IF ~t[2] THEN Err ELSE FloatTail(s, a, t[1], Count(s, dot + 1, t[1]), t[1], FALSE)
    ELSE FloatTail(s, a, dot + 1, 0, dot + 1, FALSE)

\* After an integer part s[a..j-1] (with nonzero digits after leading
\* zeros when nonzero): a float, an imaginary number, or an int.
AfterInt(s, a, j, nonzero) ==
    CASE At(s, j) = "." -> Fraction(s, a, j)
      [] At(s, j) \in {"e", "j"} -> FloatTail(s, a, j, 0, j, TRUE)
      [] nonzero -> Err                         \* leading zeros in a decimal integer
      [] Ends(s, j) -> Tok("int", j, Value(s, a, j, 10), 0, 0)
      [] OTHER -> Err

\* 0x... and 0b...: groups of digits, each after at most one underscore.
RECURSIVE Run(_, _, _)
Run(s, i, base) == IF InBase(At(s, i), base) THEN Run(s, i + 1, base) ELSE i
RECURSIVE Groups(_, _, _)
Groups(s, j, base) ==
    LET p == IF At(s, j) = "_" THEN j + 1 ELSE j
    IN  IF ~InBase(At(s, p), base) THEN 0
        ELSE LET q == Run(s, p + 1, base) IN IF At(s, q) = "_" THEN Groups(s, q, base) ELSE q
Radix(s, i, base) ==
    LET q == Groups(s, i + 2, base)
    IN  IF q = 0 \/ ~Ends(s, q) THEN Err ELSE Tok("int", q, Value(s, i + 2, q, base), 0, 0)

\* 0, 00, 0_0, ...: zeros, each after at most one underscore.
RECURSIVE Zeros(_, _)
Zeros(s, j) == IF At(s, j) = "_" THEN (IF IsDigit(At(s, j + 1)) THEN (IF s[j + 1] = "0" THEN Zeros(s, j + 2) ELSE j + 1) ELSE 0)
               ELSE IF At(s, j) = "0" THEN Zeros(s, j + 1) ELSE j

Number(s, i) ==
    CASE s[i] = "." -> Fraction(s, i, i)
      [] s[i] = "0" /\ At(s, i + 1) = "x" -> Radix(s, i, 16)
      [] s[i] = "0" /\ At(s, i + 1) = "b" -> Radix(s, i, 2)
      [] s[i] = "0" -> LET p == Zeros(s, i + 1)
                       IN  IF p = 0 THEN Err
                           ELSE IF IsDigit(At(s, p))
                           THEN LET t == DecTail(s, p + 1) IN IF ~t[2] THEN Err ELSE AfterInt(s, i, t[1], TRUE)
                           ELSE AfterInt(s, i, p, FALSE)
      [] OTHER -> LET t == DecTail(s, i + 1) IN IF ~t[2] THEN Err ELSE AfterInt(s, i, t[1], FALSE)

RECURSIVE NameEnd(_, _)
NameEnd(s, i) == IF IdChar(At(s, i)) THEN NameEnd(s, i + 1) ELSE i

RECURSIVE Lex(_, _)
Lex(s, i) ==
    IF i > Len(s) THEN <<>>
    ELSE CASE IsDigit(s[i]) \/ (s[i] = "." /\ IsDigit(At(s, i + 1))) ->
                LET t == Number(s, i) IN IF t.kind = "error" THEN <<t>> ELSE <<t>> \o Lex(s, t.end)
           [] s[i] = "." /\ At(s, i + 1) = "." /\ At(s, i + 2) = "." -> <<Tok("ellipsis", i + 3, 0, 0, 0)>> \o Lex(s, i + 3)
           [] s[i] = "." -> <<Tok("dot", i + 1, 0, 0, 0)>> \o Lex(s, i + 1)
           [] OTHER -> <<Tok("name", NameEnd(s, i), 0, 0, 0)>> \o Lex(s, NameEnd(s, i))

\* repr of m * 10^k as a float, or as the imaginary part of a complex
\* (which drops ".0"), built as a string: TLC's integers are 32-bit.
RECURSIVE ZeroString(_)
ZeroString(n) == IF n = 0 THEN "" ELSE "0" \o ZeroString(n - 1)
RECURSIVE Digits(_, _)
Digits(v, n) == IF n = 0 THEN "" ELSE Digits(v \div 10, n - 1) \o ToString(v % 10)
RECURSIVE Trim(_, _)
Trim(v, n) == IF n > 0 /\ v % 10 = 0 THEN Trim(v \div 10, n - 1) ELSE <<v, n>>
Show(m, k, imag) ==
    LET whole == IF m = 0 THEN "0"
                 ELSE IF k >= 0 THEN ToString(m) \o ZeroString(k)
                 ELSE ToString(m \div (10 ^ (-k)))
        frac == IF m = 0 \/ k >= 0 THEN <<0, 0>> ELSE Trim(m % (10 ^ (-k)), -k)
        point == IF frac[2] = 0 THEN (IF imag THEN "" ELSE ".0") ELSE "." \o Digits(frac[1], frac[2])
    IN  whole \o point \o (IF imag THEN "j" ELSE "")

\* atom ("." name)*, where an atom is a number, a name, or "...".
Evaluate(s) ==
    LET t == Lex(s, 1)
        error == \E i \in DOMAIN t : t[i].kind = "error"
        attrs == \A i \in 2..Len(t) : t[i].kind = IF i % 2 = 0 THEN "dot" ELSE "name"
    IN  CASE error \/ t[1].kind = "dot" \/ Len(t) % 2 = 0 \/ ~attrs -> <<"SyntaxError", "">>
          [] t[1].kind = "name" -> <<"NameError", "">>
          [] Len(t) > 1 -> <<"AttributeError", "">>
          [] t[1].kind = "int" -> <<"value", ToString(t[1].v)>>
          [] t[1].kind = "float" -> <<"value", Show(t[1].m, t[1].k, FALSE)>>
          [] t[1].kind = "imag" -> <<"value", Show(t[1].m, t[1].k, TRUE)>>
          [] t[1].kind = "ellipsis" -> <<"value", "Ellipsis">>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Evaluate(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Underscores never change a literal's value: dropping them gives the same
\* number, when that is a literal too.
Underscores == Done /\ outcome[1] = "value" /\ program[1] # "." =>
    LET plain == SelectSeq(program, LAMBDA c : c # "_")
    IN  Evaluate(plain)[1] = "value" => Evaluate(plain) = outcome

\* A literal never ends in an underscore.
NoTrailingUnderscore == Done /\ outcome[1] = "value" /\ outcome[2] # "Ellipsis" => program[Len(program)] # "_"
=============================================================================
