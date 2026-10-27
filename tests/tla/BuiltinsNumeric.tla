-------------------------- MODULE BuiltinsNumeric ---------------------------
(***************************************************************************)
(* The numeric built-in functions, as The Python Standard Library          *)
(* specifies them (library/functions.html): abs() (or __abs__); divmod()   *)
(* as (a // b, a % b) with the floor convention; pow() with an optional    *)
(* modulus, a negative exponent then taking the modular inverse; round()   *)
(* to the nearest multiple of 10 ** -ndigits, ties to even, returning an   *)
(* int without ndigits (or __round__); bin(), oct(), and hex() of          *)
(* __index__ values; min() and max() over an iterable or several arguments *)
(* with key and default; sum() from start, refusing str and bytes starts;  *)
(* and the int(), float(), complex(), and bool() constructors with their   *)
(* string forms and argument errors.                                       *)
(*                                                                         *)
(* A program applies one of OPS to a and b, a among -25, -15, -7, -1, 0,   *)
(* 3, 8, 25, and 35 and b among -3, -1, 0, 2, and 5: divmod(a, b), pow(a,  *)
(* b) (or the type of its result for negative b), pow(a, b, 7), pow(a, 2,  *)
(* b), round(a, b), abs(a), bin(a), oct(a), hex(a), (min(a, b), max(a, b), *)
(* min([b, a], key=abs), max((), default=a)), or sum([a, b], 10); or runs  *)
(* one of the sources of CASES in a fresh namespace. The outcome is the    *)
(* repr of the result, or the exception and its message.                   *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

VARIABLES program, outcome
vars == <<program, outcome>>

Ops == {"divmod", "pow", "pow_mod", "pow_mod_by", "round", "abs", "bin", "oct", "hex", "minmax", "sum"}
R(n) == ToString(n)
\* Python's power, with 0 ** 0 = 1.
Pow(a, b) == IF b = 0 THEN 1 ELSE a ^ b
Abs(n) == IF n < 0 THEN -n ELSE n

\* Floor division and its remainder, for either sign of b.
Div(a, b) == IF b > 0 THEN a \div b ELSE (-a) \div (-b)
Mod(a, b) == a - b * Div(a, b)

\* The x in 0..m-1 with a * x = 1 (mod m), or -1 when there is none.
Inverse(a, m) == IF \E x \in 0..(m - 1) : Mod(a * x, m) = 1 THEN CHOOSE x \in 0..(m - 1) : Mod(a * x, m) = 1 ELSE -1

\* The nearest multiple of 10^-n, ties to the even multiple.
Round(a, n) ==
    IF n >= 0 THEN a
    ELSE LET p == 10 ^ (-n)  q == Div(a, p)  r == a - q * p
         IN  IF 2 * r > p \/ (2 * r = p /\ q % 2 = 1) THEN (q + 1) * p ELSE q * p

RECURSIVE Digits(_, _)
Digits(n, base) == IF n < base THEN SubSeq("0123456789abcdef", n + 1, n + 1)
                   ELSE Digits(n \div base, base) \o SubSeq("0123456789abcdef", (n % base) + 1, (n % base) + 1)
Based(n, base, prefix) == "'" \o (IF n < 0 THEN "-" ELSE "") \o prefix \o Digits(Abs(n), base) \o "'"


Cases == {"round_half_even", "round_float_digits", "round_none", "round_hook", "round_no_hook", "round_inf",
          "round_nan", "round_bad_ndigits", "abs_hook", "abs_bad", "divmod_float", "divmod_hook",
          "divmod_complex", "divmod_zero_float", "pow_float", "pow_mod_float", "pow_keywords",
          "pow_zero_zero", "sum_floats", "sum_strings", "sum_bytes", "sum_start_kw", "sum_empty",
          "min_key_default", "min_empty", "max_empty", "min_default_with_many", "min_no_args",
          "min_first_of_equal", "max_mixed", "bin_index", "bin_float", "hex_float_method", "complex_forms",
          "complex_bad_string", "complex_string_second", "float_forms", "float_bad", "int_forms",
          "int_bad_base", "int_leading_zero", "int_float_inf", "int_float_nan", "bool_forms", "bool_kw"}
Programs == [op : Ops, a : {-25, -15, -7, -1, 0, 3, 8, 25, 35}, b : {-3, -1, 0, 2, 5}]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    LET a == p.a  b == p.b IN
    CASE p.op = "divmod" -> IF b = 0 THEN "ZeroDivisionError: division by zero"
                            ELSE "(" \o R(Div(a, b)) \o ", " \o R(Mod(a, b)) \o ")"
      [] p.op = "pow" -> IF b >= 0 THEN R(Pow(a, b))
                         ELSE IF a = 0 THEN "ZeroDivisionError: zero to a negative power" ELSE "'float'"
      [] p.op = "pow_mod" -> IF b >= 0 THEN R(Mod(Pow(a, b), 7))
                             ELSE IF Inverse(a, 7) < 0 THEN "ValueError: base is not invertible for the given modulus"
                             ELSE R(Mod(Inverse(a, 7) ^ (-b), 7))
      [] p.op = "pow_mod_by" -> IF b = 0 THEN "ValueError: pow() 3rd argument cannot be 0" ELSE R(Mod(a * a, b))
      [] p.op = "round" -> R(Round(a, b))
      [] p.op = "abs" -> R(Abs(a))
      [] p.op = "bin" -> Based(a, 2, "0b")
      [] p.op = "oct" -> Based(a, 8, "0o")
      [] p.op = "hex" -> Based(a, 16, "0x")
      \* min with a key keeps the first of equal keys.
      [] p.op = "minmax" -> "(" \o R(IF a < b THEN a ELSE b) \o ", " \o R(IF a > b THEN a ELSE b) \o ", "
                            \o R(IF Abs(a) < Abs(b) THEN a ELSE b) \o ", " \o R(a) \o ")"
      [] p.op = "sum" -> R(a + b + 10)

Case(c) ==
    CASE c = "round_half_even" -> "(0, 2, 2, 0, -2)"
      [] c = "round_float_digits" -> "(2.67, 1200.0, 0.12, 'float')"
      [] c = "round_none" -> "(4, 'int', 5)"
      [] c = "round_hook" -> "(('round', None), ('round', 2))"
      [] c = "round_no_hook" -> "TypeError: type object doesn't define __round__ method"
      [] c = "round_inf" -> "OverflowError: cannot convert float infinity to integer"
      [] c = "round_nan" -> "ValueError: cannot convert float NaN to integer"
      [] c = "round_bad_ndigits" -> "TypeError: 'float' object cannot be interpreted as an integer"
      [] c = "abs_hook" -> "('abs', 2.5, 5.0, 1, 0.0)"
      [] c = "abs_bad" -> "TypeError: bad operand type for abs(): 'str'"
      [] c = "divmod_float" -> "((3.0, 1.5), (-4.0, 0.5), (-4.0, -1.0))"
      [] c = "divmod_hook" -> "('divmod', 'rpow')"
      [] c = "divmod_complex" -> "TypeError: unsupported operand type(s) for divmod(): 'complex' and 'int'"
      [] c = "divmod_zero_float" -> "ZeroDivisionError: division by zero"
      [] c = "pow_float" -> "(1.4142135623730951, 0.25, 8.0, True)"
      [] c = "pow_mod_float" -> "TypeError: pow() 3rd argument not allowed unless all arguments are integers"
      [] c = "pow_keywords" -> "24"
      [] c = "pow_zero_zero" -> "(1, 1.0, 1)"
      [] c = "sum_floats" -> "(1.0, True, 1.0)"
      [] c = "sum_strings" -> "TypeError: sum() can't sum strings [use ''.join(seq) instead]"
      [] c = "sum_bytes" -> "TypeError: sum() can't sum bytes [use b''.join(seq) instead]"
      [] c = "sum_start_kw" -> "(13, [1, 2])"
      [] c = "sum_empty" -> "(0, 5, 'float')"
      [] c = "min_key_default" -> "(3, 'd', 'c', 3)"
      [] c = "min_empty" -> "ValueError: min() iterable argument is empty"
      [] c = "max_empty" -> "ValueError: max() iterable argument is empty"
      [] c = "min_default_with_many" -> "TypeError: Cannot specify a default for min() with multiple positional arguments"
      [] c = "min_no_args" -> "TypeError: min expected at least 1 argument, got 0"
      [] c = "min_first_of_equal" -> "((1, 'a'), (1, 'a'))"
      [] c = "max_mixed" -> "TypeError: '>' not supported between instances of 'str' and 'int'"
      [] c = "bin_index" -> "('0b1010', '0o12', '0xa', '-0xff')"
      [] c = "bin_float" -> "TypeError: 'float' object cannot be interpreted as an integer"
      [] c = "hex_float_method" -> "'0x1.8000000000000p+0'"
      [] c = "complex_forms" -> "(0j, (1+0j), (1+2j), (1+2j), 3j, (-1+1j))"
      [] c = "complex_bad_string" -> "ValueError: complex() arg is a malformed string"
      [] c = "complex_string_second" -> "TypeError: complex() argument 'real' must be a real number, not str"
      [] c = "float_forms" -> "(0.0, -1500.0, -inf, 'nan', 10.5, 1.0)"
      [] c = "float_bad" -> "ValueError: could not convert string to float: '1__0'"
      [] c = "int_forms" -> "(0, 3, -3, 31, 31, 5, 35, 1)"
      [] c = "int_bad_base" -> "ValueError: int() base must be >= 2 and <= 36, or 0"
      [] c = "int_leading_zero" -> "ValueError: invalid literal for int() with base 0: '010'"
      [] c = "int_float_inf" -> "OverflowError: cannot convert float infinity to integer"
      [] c = "int_float_nan" -> "ValueError: cannot convert float NaN to integer"
      [] c = "bool_forms" -> "(False, False, True, False, True)"
      [] c = "bool_kw" -> "TypeError: bool() takes no keyword arguments"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
IsOp == Done /\ "op" \in DOMAIN program

\* The quotient and remainder recompose a, the remainder taking b's sign.
DivmodLaw == IsOp /\ program.b # 0 =>
    LET a == program.a  b == program.b  r == Mod(a, b) IN
    /\ b * Div(a, b) + r = a
    /\ Abs(r) < Abs(b)
    /\ (r = 0 \/ (r > 0) = (b > 0))

\* Rounding moves a by at most half the unit, to a multiple of it.
RoundLaw == IsOp /\ program.b < 0 =>
    LET p == 10 ^ (-program.b)  x == Round(program.a, program.b) IN
    Mod(x, p) = 0 /\ 2 * Abs(x - program.a) <= p
=============================================================================
