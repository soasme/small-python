---------------------------- MODULE NumericTypes ----------------------------
(***************************************************************************)
(* The numeric types, as The Python Language Reference specifies them      *)
(* (reference/datamodel.html#numbers-number and its subsections): numbers  *)
(* are immutable; their repr is a valid literal of the same value, in base *)
(* 10, without leading or trailing zeros (but for one zero next to a       *)
(* decimal point), signed only when negative; integers are unlimited and   *)
(* behave as an infinite two's complement under shifts and masks; bool is  *)
(* a subtype of int whose two values behave as 0 and 1 except as strings;  *)
(* a complex number's real and imag are read-only. Three families:         *)
(*                                                                         *)
(*   - x <op> y for x, y in -3..3, False, True and op in  & | ^ >> << + - *  *)
(*     and the unary ~x, -x, str(x), and repr(x);                          *)
(*   - numeric literals: a sign, one to three digits from 0 1 5, a decimal *)
(*     point at any place or none, and an exponent e-6, e-5, e0, e14, e+16 *)
(*     or none;                                                            *)
(*   - z.real, z.imag, and assigning to them, for z = 1.5+2j.              *)
(*                                                                         *)
(* The outcome is the result's type and repr (or str), or the exception.   *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

\* Operands, as <<"int", n>> or <<"bool", 0 or 1>>.
Operands == {<<"int", n>> : n \in -3..3} \cup {<<"bool", 0>>, <<"bool", 1>>}
Binary == {"&", "|", "^", ">>", "<<", "+", "-", "*"}
Unary == {"~", "neg", "str", "repr"}

Digits == UNION {[1..n -> {"0", "1", "5"}] : n \in 1..3}
Exponents == {<<>>, <<"e", "-", "6">>, <<"e", "-", "5">>, <<"e", "0">>, <<"e", "1", "4">>, <<"e", "+", "1", "6">>}
Literal(sign, d, point, e) ==
    (IF sign THEN <<"-">> ELSE <<>>) \o
    (IF point = -1 THEN d ELSE SubSeq(d, 1, point) \o <<".">> \o SubSeq(d, point + 1, Len(d))) \o e

Programs == [kind : {"binary"}, op : Binary, x : Operands, y : Operands]
            \cup [kind : {"unary"}, op : Unary, x : Operands]
            \cup UNION {{[kind |-> "literal", text |-> Literal(sign, d, point, e)] : point \in -1..Len(d)} :
                         sign \in BOOLEAN, d \in Digits, e \in Exponents}
            \cup [kind : {"complex"}, op : {"real", "imag", "set real", "set imag"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", "">>

(***************************************************************************)
(* Integers and bools.                                                     *)
(***************************************************************************)
AsInt(v) == v[2]
Bool(n) == IF n = 1 THEN "True" ELSE "False"
\* Bitwise operations on 6-bit two's complement, enough for these values.
RECURSIVE Bits(_, _, _, _)
Bits(op, a, b, k) ==
    IF k = 6 THEN 0
    ELSE LET p == a % 2  q == b % 2
             bit == CASE op = "&" -> p * q [] op = "|" -> IF p + q > 0 THEN 1 ELSE 0 [] op = "^" -> (p + q) % 2
         IN  bit + 2 * Bits(op, a \div 2, b \div 2, k + 1)
Bitwise(op, a, b) == LET r == Bits(op, a % 64, b % 64, 0) IN IF r >= 32 THEN r - 64 ELSE r
IntRepr(n) == <<"int", ToString(n)>>
BinaryOp(p) ==
    LET a == AsInt(p.x)  b == AsInt(p.y)
    IN  CASE p.op \in {"&", "|", "^"} ->
                 IF p.x[1] = "bool" /\ p.y[1] = "bool"
                 THEN <<"bool", Bool(Bitwise(p.op, a, b))>>
                 ELSE IntRepr(Bitwise(p.op, a, b))
          [] p.op \in {">>", "<<"} /\ b < 0 -> <<"ValueError", "">>       \* negative shift count
          [] p.op = ">>" -> IntRepr(a \div (2 ^ b))                        \* floor, as sign bits shift in
          [] p.op = "<<" -> IntRepr(a * 2 ^ b)
          [] p.op = "+" -> IntRepr(a + b)
          [] p.op = "-" -> IntRepr(a - b)
          [] p.op = "*" -> IntRepr(a * b)
UnaryOp(p) ==
    CASE p.op = "~" -> IntRepr(-AsInt(p.x) - 1)
      [] p.op = "neg" -> IntRepr(-AsInt(p.x))
      [] p.x[1] = "bool" -> <<"str", Bool(p.x[2])>>
      [] OTHER -> <<"str", ToString(p.x[2])>>

(***************************************************************************)
(* Literals. The value is digits * 10^q with the digits' decimal point at  *)
(* decpt (the place value of the first significant digit); repr shows     *)
(* the significant digits positionally when -4 < decpt <= 16, and with an  *)
(* exponent of at least two digits otherwise.                              *)
(***************************************************************************)
Char(n) == CASE n = 0 -> "0" [] n = 1 -> "1" [] n = 2 -> "2" [] n = 3 -> "3" [] n = 4 -> "4"
             [] n = 5 -> "5" [] n = 6 -> "6" [] n = 7 -> "7" [] n = 8 -> "8" [] n = 9 -> "9"
Value(c) == CHOOSE n \in 0..9 : Char(n) = c
RECURSIVE Decimal(_)
Decimal(n) == IF n < 10 THEN <<Char(n)>> ELSE Decimal(n \div 10) \o <<Char(n % 10)>>
Zeros(n) == [k \in 1..n |-> "0"]
RECURSIVE Number(_)
Number(s) == IF s = <<>> THEN 0 ELSE 10 * Number(SubSeq(s, 1, Len(s) - 1)) + Value(s[Len(s)])
Index(s, c) == IF \E k \in DOMAIN s : s[k] = c THEN CHOOSE k \in DOMAIN s : s[k] = c ELSE 0
RECURSIVE Strip(_), StripEnd(_)
Strip(s) == IF s # <<>> /\ Head(s) = "0" THEN Strip(Tail(s)) ELSE s
StripEnd(s) == IF s # <<>> /\ s[Len(s)] = "0" THEN StripEnd(SubSeq(s, 1, Len(s) - 1)) ELSE s
Spell(s) == LET RECURSIVE F(_) F(t) == IF t = <<>> THEN "" ELSE Head(t) \o F(Tail(t)) IN F(s)

\* A literal's parts: <<negative, digits, point index or 0, exponent>>.
Parse(t) ==
    LET negative == t # <<>> /\ t[1] = "-"
        u == IF negative THEN Tail(t) ELSE t
        e == Index(u, "e")
        mantissa == IF e = 0 THEN u ELSE SubSeq(u, 1, e - 1)
        expo == IF e = 0 THEN <<>> ELSE SubSeq(u, e + 1, Len(u))
        exponent == CASE expo = <<>> -> 0
                      [] expo[1] = "-" -> -Number(Tail(expo))
                      [] expo[1] = "+" -> Number(Tail(expo))
                      [] OTHER -> Number(expo)
        point == Index(mantissa, ".")
        digits == IF point = 0 THEN mantissa ELSE SubSeq(mantissa, 1, point - 1) \o SubSeq(mantissa, point + 1, Len(mantissa))
        \* The exponent of the last digit.
        q == exponent - (IF point = 0 THEN 0 ELSE Len(mantissa) - point)
    IN  [negative |-> negative, digits |-> digits, q |-> q, float |-> point # 0 \/ e # 0, mantissa |-> mantissa]

FloatRepr(negative, digits, q) ==
    LET s0 == Strip(digits)
        s == StripEnd(s0)
        qq == q + (Len(s0) - Len(s))
        k == Len(s)
        decpt == k + qq
        sign == IF negative THEN <<"-">> ELSE <<>>
        x == decpt - 1
        body == CASE k = 0 -> <<"0", ".", "0">>
                  [] decpt > -4 /\ decpt <= 16 ->
                        IF decpt <= 0 THEN <<"0", ".">> \o Zeros(-decpt) \o s
                        ELSE IF decpt >= k THEN s \o Zeros(decpt - k) \o <<".", "0">>
                        ELSE SubSeq(s, 1, decpt) \o <<".">> \o SubSeq(s, decpt + 1, k)
                  [] OTHER -> <<s[1]>> \o (IF k > 1 THEN <<".">> \o SubSeq(s, 2, k) ELSE <<>>) \o
                              <<"e", IF x < 0 THEN "-" ELSE "+">> \o
                              (IF (IF x < 0 THEN -x ELSE x) < 10 THEN <<"0">> ELSE <<>>) \o Decimal(IF x < 0 THEN -x ELSE x)
    IN  sign \o body

LiteralRepr(t) ==
    LET p == Parse(t)
        lead == p.mantissa # <<>> /\ p.mantissa[1] = "0" /\ Len(p.mantissa) > 1 /\ Strip(p.mantissa) # <<>>
    IN  CASE p.float -> <<"float", Spell(FloatRepr(p.negative, p.digits, p.q))>>
          [] lead -> <<"SyntaxError", "">>          \* leading zeros in a decimal integer literal
          [] OTHER -> LET n == Number(p.digits) IN <<"int", Spell((IF p.negative /\ n # 0 THEN <<"-">> ELSE <<>>) \o Decimal(n))>>

Run(p) == CASE p.kind = "binary" -> BinaryOp(p)
             [] p.kind = "unary" -> UnaryOp(p)
             [] p.kind = "literal" -> LiteralRepr(p.text)
             [] p.kind = "complex" -> CASE p.op = "real" -> <<"float", "1.5">> [] p.op = "imag" -> <<"float", "2.0">>
                                        [] OTHER -> <<"AttributeError", "">>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A float's repr is a literal of the same value, and so its own repr.
RoundTrip == Done /\ program.kind = "literal" /\ outcome[1] = "float" =>
    LET p == Parse(program.text) IN
    LiteralRepr(FloatRepr(p.negative, p.digits, p.q)) = outcome

\* bool behaves as 0 and 1: the result's value is int arithmetic's.
BoolAsInt == Done /\ program.kind = "binary" /\ outcome[1] = "bool" =>
    BinaryOp([program EXCEPT !.x = <<"int", program.x[2]>>, !.y = <<"int", program.y[2]>>])[2] = (IF outcome[2] = "True" THEN "1" ELSE "0")
=============================================================================
