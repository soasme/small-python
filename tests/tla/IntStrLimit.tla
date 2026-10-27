---------------------------- MODULE IntStrLimit -----------------------------
(***************************************************************************)
(* The integer string conversion length limit, as the Built-in Types       *)
(* chapter specifies it (library/stdtypes.html#int-max-str-digits):        *)
(* converting an int to or from a string in a base that is not a power of  *)
(* two raises ValueError when the digits (not signs or underscores,        *)
(* leading zeros included) exceed the limit, the message naming the limit  *)
(* and, when parsing, the digit count; str(), repr(), format() with d, %d, *)
(* f-strings, int() of str, bytes, and bytearray, and decimal literals are *)
(* affected (a literal raising SyntaxError), while bases 2, 8, and 16 and  *)
(* float() are not; the limit defaults to 4300, is read and set with       *)
(* sys.get_int_max_str_digits() and sys.set_int_max_str_digits() (0        *)
(* meaning unlimited, other values below 640 raising ValueError), and is   *)
(* reported in sys.int_info and sys.flags.                                 *)
(*                                                                         *)
(* A program sets the limit to 0, 640, or 1000, and for a digit count n    *)
(* among 639, 640, 641, 999, 1000, 1001, 4300, and 4301 reports the length *)
(* of str(10 ** (n - 1)) or of str(-10 ** (n - 1)), the length of          *)
(* str(int('1' * n)), whether int() of -1...1, of 1_1..._1, or of '1' * n  *)
(* in base 7 succeeds, or the hex length of int('1' * n, 16); or runs one  *)
(* of the sources of CASES in a fresh namespace. The outcome is the repr   *)
(* of that result or of the case's result, or the exception and its        *)
(* message.                                                                *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

VARIABLES program, outcome
vars == <<program, outcome>>

Ops == {"str", "neg_str", "int", "int_neg", "underscore", "int7", "int16"}
R(n) == ToString(n)
Use == "; use sys.set_int_max_str_digits() to increase the limit"
Exceeds(limit, n) == limit # 0 /\ n > limit
Prefix(limit) == "ValueError: Exceeds the limit (" \o R(limit) \o " digits) for integer string conversion"


Cases == {"default", "str_over", "str_at_limit", "int_over", "int_at_limit", "underscores_ignored",
          "leading_zeros_count", "hex_unlimited", "base_8_unlimited", "base_10_explicit", "base_7_limited",
          "base_0", "set_limit", "set_zero", "set_too_small", "set_negative", "set_keyword", "set_type",
          "repr_over", "format_d_over", "fstring_over", "percent_over", "format_x_ok", "float_unaffected",
          "int_from_bytes", "int_bytearray", "negative_str", "negative_over", "int_sign_over",
          "literal_over", "literal_hex", "decimal_digits_check", "int_subclass_str", "error_message_int"}
Programs == [limit : {0, 640, 1000}, digits : {639, 640, 641, 999, 1000, 1001, 4300, 4301}, op : Ops]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    LET n == p.digits  limit == p.limit IN
    CASE p.op = "int16" -> R(n)                          \* a power-of-two base is not limited
      [] p.op \in {"str", "neg_str"} /\ Exceeds(limit, n) -> Prefix(limit) \o Use
      [] Exceeds(limit, n) -> Prefix(limit) \o ": value has " \o R(n) \o " digits" \o Use
      [] p.op = "neg_str" -> R(n + 1)
      [] p.op \in {"str", "int"} -> R(n)
      [] OTHER -> "True"

Case(c) ==
    CASE c = "default" -> "(4300, 4300, 640, 4300)"
      [] c = "str_over" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "str_at_limit" -> "4300"
      [] c = "int_over" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "int_at_limit" -> "4300"
      [] c = "underscores_ignored" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "leading_zeros_count" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "hex_unlimited" -> "20000"
      [] c = "base_8_unlimited" -> "5539"
      [] c = "base_10_explicit" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "base_7_limited" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "base_0" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "set_limit" -> "(640, 640, 'Exceeds the limit (640 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit')"
      [] c = "set_zero" -> "10001"
      [] c = "set_too_small" -> "ValueError: maxdigits must be >= 640 or 0 for unlimited"
      [] c = "set_negative" -> "ValueError: maxdigits must be >= 640 or 0 for unlimited"
      [] c = "set_keyword" -> "1000"
      [] c = "set_type" -> "TypeError: 'str' object cannot be interpreted as an integer"
      [] c = "repr_over" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "format_d_over" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "fstring_over" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "percent_over" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "format_x_ok" -> "3572"
      [] c = "float_unaffected" -> "inf"
      [] c = "int_from_bytes" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "int_bytearray" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "negative_str" -> "4301"
      [] c = "negative_over" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "int_sign_over" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "literal_over" -> "SyntaxError: Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit - Consider hexadecimal for huge integer literals to avoid decimal conversion limits."
      [] c = "literal_hex" -> "20000"
      [] c = "decimal_digits_check" -> "1111111111"
      [] c = "int_subclass_str" -> "ValueError: Exceeds the limit (4300 digits) for integer string conversion; use sys.set_int_max_str_digits() to increase the limit"
      [] c = "error_message_int" -> "'Exceeds the limit (4300 digits) for integer string conversion: value has 4301 digits; use sys.set_int_max_str_digits() to increase the limit'"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* Within the limit (or with none), every conversion succeeds.
WithinLimit == Done /\ "op" \in DOMAIN program /\ ~Exceeds(program.limit, program.digits) =>
    outcome \notin {Prefix(program.limit) \o Use,
                      Prefix(program.limit) \o ": value has " \o R(program.digits) \o " digits" \o Use}
=============================================================================
