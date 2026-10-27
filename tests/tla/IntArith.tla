----------------------------- MODULE IntArith -----------------------------
(***************************************************************************)
(* Integer arithmetic as The Python Language Reference specifies it        *)
(* (reference/expressions.html#binary-arithmetic-operations, #shifting-   *)
(* operations, #binary-bitwise-operations, #unary-arithmetic-and-bitwise- *)
(* operations, and #the-power-operator) for every pair of operands in a   *)
(* range: floor division and modulo with the divisor's sign, bitwise       *)
(* operations on the infinite two's complement form of negative numbers,  *)
(* and shifts, each as the expression `(a) op (b)` or `op(a)`.             *)
(***************************************************************************)
EXTENDS Integers

CONSTANT N           \* operands range over -N..N
Range == -N..N
Binary == {"+", "-", "*", "//", "%", "divmod", "**", "<<", ">>", "&", "|", "^"}
Unary == {"-", "~", "abs"}
Programs == [kind : {"binary"}, op : Binary, a : Range, b : Range] \cup
            [kind : {"unary"}, op : Unary, a : Range, b : {0}]

VARIABLES program, outcome
vars == <<program, outcome>>

\* Outcomes: an int, a (quotient, remainder) pair, a float (from a negative
\* power), or an exception.
IntOf(v) == <<"int", v, 0, "">>
Pair(q, r) == <<"pair", q, r, "">>
Raise(name) == <<"raise", 0, 0, name>>
Pending == <<"pending", 0, 0, "">>

\* "Integer division ... is floor division": the quotient rounded toward
\* minus infinity, and a remainder with the divisor's sign.
FloorDiv(a, b) ==
    LET bound == (IF a < 0 THEN -a ELSE a) + 1
    IN  CHOOSE q \in -bound..bound : IF b > 0 THEN b * q <= a /\ a < b * q + b
                                                ELSE b * q >= a /\ a > b * q + b
Mod(a, b) == a - b * FloorDiv(a, b)

RECURSIVE Power(_, _)
Power(a, n) == IF n = 0 THEN 1 ELSE a * Power(a, n - 1)

\* Bitwise operations on two's complement with infinitely many sign bits:
\* 0 and -1 are all zeros and all ones; others split off their lowest bit.
Bit(a) == Mod(a, 2)
Half(a) == FloorDiv(a, 2)
Done(a) == a \in {0, -1}
RECURSIVE And(_, _), Or(_, _), Xor(_, _)
And(a, b) == IF Done(a) /\ Done(b) THEN (IF a = -1 /\ b = -1 THEN -1 ELSE 0)
             ELSE 2 * And(Half(a), Half(b)) + Bit(a) * Bit(b)
Or(a, b) == IF Done(a) /\ Done(b) THEN (IF a = -1 \/ b = -1 THEN -1 ELSE 0)
            ELSE 2 * Or(Half(a), Half(b)) + (IF Bit(a) + Bit(b) > 0 THEN 1 ELSE 0)
Xor(a, b) == IF Done(a) /\ Done(b) THEN (IF a # b THEN -1 ELSE 0)
             ELSE 2 * Xor(Half(a), Half(b)) + Mod(Bit(a) + Bit(b), 2)

Eval(p) ==
    LET a == p.a  b == p.b
    IN  IF p.kind = "unary"
        THEN CASE p.op = "-" -> IntOf(-a)
               [] p.op = "~" -> IntOf(-(a + 1))       \* "the bitwise inversion of x is defined as -(x+1)"
               [] p.op = "abs" -> IntOf(IF a < 0 THEN -a ELSE a)
        ELSE CASE p.op = "+" -> IntOf(a + b)
               [] p.op = "-" -> IntOf(a - b)
               [] p.op = "*" -> IntOf(a * b)
               [] p.op \in {"//", "%", "divmod"} /\ b = 0 -> Raise("ZeroDivisionError")
               [] p.op = "//" -> IntOf(FloorDiv(a, b))
               [] p.op = "%" -> IntOf(Mod(a, b))
               [] p.op = "divmod" -> Pair(FloorDiv(a, b), Mod(a, b))
               [] p.op = "**" /\ b >= 0 -> IntOf(Power(a, b))
               [] p.op = "**" /\ a = 0 -> Raise("ZeroDivisionError")
               [] p.op = "**" -> <<"float", 0, 0, "">>  \* a negative exponent gives a float
               [] p.op \in {"<<", ">>"} /\ b < 0 -> Raise("ValueError")   \* negative shift count
               [] p.op = "<<" -> IntOf(a * Power(2, b))
               [] p.op = ">>" -> IntOf(FloorDiv(a, Power(2, b)))
               [] p.op = "&" -> IntOf(And(a, b))
               [] p.op = "|" -> IntOf(Or(a, b))
               [] p.op = "^" -> IntOf(Xor(a, b))

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Eval(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
(* Identities the reference states, checked for every pair in range.       *)

Pairs == Range \X Range

\* "x == (x//y)*y + (x%y)", and the remainder is smaller than the divisor
\* and has its sign.
DivModIdentity == \A e \in Pairs : e[2] # 0 =>
    LET q == FloorDiv(e[1], e[2])  r == Mod(e[1], e[2])
    IN  /\ e[1] = q * e[2] + r
        /\ (IF r < 0 THEN -r ELSE r) < (IF e[2] < 0 THEN -e[2] ELSE e[2])
        /\ r = 0 \/ (r > 0) = (e[2] > 0)

\* "A right shift by n bits is defined as floor division by pow(2,n)"; a
\* left shift then a right shift by the same count gives the number back.
ShiftsInverse == \A e \in Pairs : e[2] >= 0 => FloorDiv(e[1] * Power(2, e[2]), Power(2, e[2])) = e[1]

\* Bitwise operations agree with each other and with inversion.
BitwiseLaws == \A e \in Pairs :
    LET a == e[1]  b == e[2]
    IN  /\ Xor(a, b) = Or(a, b) - And(a, b)
        /\ And(a, -(a + 1)) = 0 /\ Or(a, -(a + 1)) = -1
        /\ And(a, b) = And(b, a) /\ Or(a, -1) = -1 /\ And(a, -1) = a
=============================================================================
