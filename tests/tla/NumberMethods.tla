--------------------------- MODULE NumberMethods ----------------------------
(***************************************************************************)
(* The additional methods of int, float, and complex, as the Built-in      *)
(* Types chapter specifies them (library/stdtypes.html#additional-methods- *)
(* on-integer-types, #additional-methods-on-float, and #additional-        *)
(* methods-on-complex): bit_length is the k with 2^(k-1) <= |n| < 2^k, or  *)
(* 0 for 0; bit_count counts the ones of |n|; to_bytes writes n in length  *)
(* bytes, two's complement when signed, most significant first for big and *)
(* last for little, and raises OverflowError for a negative unsigned or an *)
(* unrepresentable n; from_bytes reads them back from any bytes-like       *)
(* object or iterable of byte values, as an instance of the class it is    *)
(* called on; as_integer_ratio is n over 1 and is_integer is true;         *)
(* float.from_number delegates to __float__, then __index__; a float's     *)
(* as_integer_ratio is exact and in lowest terms, raising for infinities   *)
(* and NaNs; float.hex and float.fromhex convert exactly to and from       *)
(* hexadecimal strings with optional sign, prefix, fraction, and binary    *)
(* exponent; and complex.from_number delegates to __complex__, then        *)
(* __float__, then __index__.                                              *)
(*                                                                         *)
(* A program calls an int method on a boundary value n: bit_length,        *)
(* bit_count, as_integer_ratio, is_integer, or to_bytes for every length   *)
(* up to 3, byte order, and signedness; or calls int.from_bytes on every   *)
(* sequence of up to two bytes drawn from 0, 1, 127, 128, and 255; or runs *)
(* one of the sources of CASES in a fresh namespace. The outcome is the    *)
(* repr of the result, of the list of a to_bytes result's byte values, or  *)
(* the exception and its message.                                          *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Ns == {-65536, -32769, -32768, -257, -256, -129, -128, -37, -1, 0, 1, 19, 127, 128, 255, 256, 32767, 32768, 65535}
Orders == {"big", "little"}
Byte == {0, 1, 127, 128, 255}
ByteSeqs == {<<>>} \cup {<<a>> : a \in Byte} \cup {<<a, b>> : a, b \in Byte}

Abs(n) == IF n < 0 THEN -n ELSE n
RECURSIVE BitLength(_)
BitLength(n) == IF n = 0 THEN 0 ELSE 1 + BitLength(n \div 2)
RECURSIVE BitCount(_)
BitCount(n) == IF n = 0 THEN 0 ELSE (n % 2) + BitCount(n \div 2)

R(n) == ToString(n)
RECURSIVE Join(_)
Join(s) == IF s = <<>> THEN "" ELSE IF Len(s) = 1 THEN R(Head(s)) ELSE R(Head(s)) \o ", " \o Join(Tail(s))
Reverse(s) == [i \in 1..Len(s) |-> s[Len(s) + 1 - i]]

\* n in length bytes, most significant first, or the error.
Fits(n, length, signed) ==
    IF length = 0 THEN n = 0
    ELSE IF signed THEN -(2 ^ (8 * length - 1)) <= n /\ n < 2 ^ (8 * length - 1)
    ELSE n < 256 ^ length
ToBytes(p) ==
    LET v == IF p.n < 0 THEN p.n + 256 ^ p.length ELSE p.n
        big == [i \in 1..p.length |-> (v \div 256 ^ (p.length - i)) % 256]
    IN  CASE p.n < 0 /\ ~p.signed -> "OverflowError: can't convert negative int to unsigned"
          [] ~Fits(p.n, p.length, p.signed) -> "OverflowError: int too big to convert"
          [] OTHER -> "[" \o Join(IF p.order = "big" THEN big ELSE Reverse(big)) \o "]"

RECURSIVE Unsigned(_)
Unsigned(s) == IF s = <<>> THEN 0 ELSE Unsigned(SubSeq(s, 1, Len(s) - 1)) * 256 + s[Len(s)]
FromBytes(p) ==
    LET big == IF p.order = "big" THEN p.bytes ELSE Reverse(p.bytes)
        u == Unsigned(big)
    IN  IF p.signed /\ big # <<>> /\ big[1] >= 128 THEN u - 256 ^ Len(big) ELSE u


Cases == {"to_bytes_default", "to_bytes_default_overflow", "to_bytes_bad_order", "to_bytes_negative_length",
          "to_bytes_signed_keyword_only", "to_bytes_length_index", "to_bytes_length_float",
          "to_bytes_order_type", "from_bytes_iterable", "from_bytes_bytearray", "from_bytes_empty_signed",
          "from_bytes_bad_item", "from_bytes_not_iterable", "from_bytes_str", "from_bytes_bad_order",
          "from_bytes_subclass", "from_bytes_bool", "as_integer_ratio_int", "is_integer_int",
          "bit_length_huge", "bit_count_huge", "bool_bit_length", "float_from_number_int",
          "float_from_number_big", "float_from_number_dunder", "float_from_number_index",
          "float_from_number_both", "float_from_number_str", "float_from_number_bool", "float_ratio",
          "float_ratio_negative", "float_ratio_inf", "float_ratio_nan", "float_ratio_zero",
          "float_is_integer", "float_hex", "float_hex_special", "float_hex_subnormal", "float_hex_max",
          "float_hex_one", "fromhex_example", "fromhex_whitespace", "fromhex_no_prefix",
          "fromhex_fraction_only", "fromhex_case", "fromhex_special", "fromhex_no_digits",
          "fromhex_garbage", "fromhex_overflow", "fromhex_underflow", "fromhex_round", "fromhex_round_odd",
          "fromhex_subclass", "fromhex_not_str", "hex_roundtrip", "complex_from_number_float",
          "complex_from_number_dunder", "complex_from_number_float_dunder", "complex_from_number_index",
          "complex_from_number_str", "complex_from_number_complex", "float_hex_method_on_int",
          "fromhex_instance", "from_bytes_index_object", "from_bytes_float", "from_bytes_dunder_bytes",
          "from_bytes_iter_typeerror", "from_bytes_iter_valueerror", "from_bytes_order_type",
          "to_bytes_too_many", "bytes_from_float", "bytearray_from_none", "bytearray_ignores_dunder_bytes",
          "bytes_uses_dunder_bytes", "bytearray_iter_typeerror", "bytes_iter_valueerror", "bytearray_count",
          "fromhex_bytes"}
Programs == [method : {"bit_length", "bit_count", "as_integer_ratio", "is_integer"}, n : Ns]
            \cup [method : {"to_bytes"}, n : Ns, length : 0..3, order : Orders, signed : BOOLEAN]
            \cup [method : {"from_bytes"}, bytes : ByteSeqs, order : Orders, signed : BOOLEAN]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Generated(p) ==
    CASE p.method = "bit_length" -> R(BitLength(Abs(p.n)))
      [] p.method = "bit_count" -> R(BitCount(Abs(p.n)))
      [] p.method = "as_integer_ratio" -> "(" \o R(p.n) \o ", 1)"
      [] p.method = "is_integer" -> "True"
      [] p.method = "to_bytes" -> ToBytes(p)
      [] p.method = "from_bytes" -> R(FromBytes(p))

Case(c) ==
    CASE c = "to_bytes_default" -> "b'A'"
      [] c = "to_bytes_default_overflow" -> "OverflowError: int too big to convert"
      [] c = "to_bytes_bad_order" -> "ValueError: byteorder must be either 'little' or 'big'"
      [] c = "to_bytes_negative_length" -> "ValueError: length cannot be negative"
      [] c = "to_bytes_signed_keyword_only" -> "TypeError: to_bytes() takes at most 2 positional arguments (3 given)"
      [] c = "to_bytes_length_index" -> "b'\\x01\\x00\\x00\\x00\\x00\\x00\\x00'"
      [] c = "to_bytes_length_float" -> "TypeError: 'float' object cannot be interpreted as an integer"
      [] c = "to_bytes_order_type" -> "TypeError: to_bytes() argument 'byteorder' must be str, not bytes"
      [] c = "from_bytes_iterable" -> "16711680"
      [] c = "from_bytes_bytearray" -> "1"
      [] c = "from_bytes_empty_signed" -> "0"
      [] c = "from_bytes_bad_item" -> "ValueError: bytes must be in range(0, 256)"
      [] c = "from_bytes_not_iterable" -> "TypeError: cannot convert 'int' object to bytes"
      [] c = "from_bytes_str" -> "TypeError: cannot convert 'str' object to bytes"
      [] c = "from_bytes_bad_order" -> "ValueError: byteorder must be either 'little' or 'big'"
      [] c = "from_bytes_subclass" -> "('Sub', 5)"
      [] c = "from_bytes_bool" -> "True"
      [] c = "as_integer_ratio_int" -> "((-7, 1), (1, 1), 'int')"
      [] c = "is_integer_int" -> "True"
      [] c = "bit_length_huge" -> "1001"
      [] c = "bit_count_huge" -> "1000"
      [] c = "bool_bit_length" -> "1"
      [] c = "float_from_number_int" -> "3.0"
      [] c = "float_from_number_big" -> "OverflowError: int too large to convert to float"
      [] c = "float_from_number_dunder" -> "2.5"
      [] c = "float_from_number_index" -> "7.0"
      [] c = "float_from_number_both" -> "1.5"
      [] c = "float_from_number_str" -> "TypeError: must be real number, not str"
      [] c = "float_from_number_bool" -> "1.0"
      [] c = "float_ratio" -> "(3, 4)"
      [] c = "float_ratio_negative" -> "(-3602879701896397, 36028797018963968)"
      [] c = "float_ratio_inf" -> "OverflowError: cannot convert Infinity to integer ratio"
      [] c = "float_ratio_nan" -> "ValueError: cannot convert NaN to integer ratio"
      [] c = "float_ratio_zero" -> "(0, 1)"
      [] c = "float_is_integer" -> "(True, False, False, False, True)"
      [] c = "float_hex" -> "'0x1.d380000000000p+11'"
      [] c = "float_hex_special" -> "('inf', '-inf', 'nan', '0x0.0p+0', '-0x0.0p+0')"
      [] c = "float_hex_subnormal" -> "'0x0.0000000000001p-1022'"
      [] c = "float_hex_max" -> "'0x1.fffffffffffffp+1023'"
      [] c = "float_hex_one" -> "('0x1.0000000000000p+0', '0x1.999999999999ap-4')"
      [] c = "fromhex_example" -> "3740.0"
      [] c = "fromhex_whitespace" -> "-0.25"
      [] c = "fromhex_no_prefix" -> "255.0"
      [] c = "fromhex_fraction_only" -> "0.5"
      [] c = "fromhex_case" -> "3.0"
      [] c = "fromhex_special" -> "(inf, -inf, nan)"
      [] c = "fromhex_no_digits" -> "ValueError: invalid hexadecimal floating-point string"
      [] c = "fromhex_garbage" -> "ValueError: invalid hexadecimal floating-point string"
      [] c = "fromhex_overflow" -> "OverflowError: hexadecimal value too large to represent as a float"
      [] c = "fromhex_underflow" -> "0.0"
      [] c = "fromhex_round" -> "1.0"
      [] c = "fromhex_round_odd" -> "1.0000000000000004"
      [] c = "fromhex_subclass" -> "'G'"
      [] c = "fromhex_not_str" -> "TypeError: bad argument type for built-in operation"
      [] c = "hex_roundtrip" -> "True"
      [] c = "complex_from_number_float" -> "(2.5+0j)"
      [] c = "complex_from_number_dunder" -> "(1+2j)"
      [] c = "complex_from_number_float_dunder" -> "(2.5+0j)"
      [] c = "complex_from_number_index" -> "(7+0j)"
      [] c = "complex_from_number_str" -> "TypeError: must be real number, not str"
      [] c = "complex_from_number_complex" -> "3j"
      [] c = "float_hex_method_on_int" -> "TypeError: descriptor 'hex' for 'float' objects doesn't apply to a 'int' object"
      [] c = "fromhex_instance" -> "2.0"
      [] c = "from_bytes_index_object" -> "TypeError: cannot convert 'I' object to bytes"
      [] c = "from_bytes_float" -> "TypeError: cannot convert 'float' object to bytes"
      [] c = "from_bytes_dunder_bytes" -> "30841"
      [] c = "from_bytes_iter_typeerror" -> "TypeError: cannot convert 'Bad' object to bytes"
      [] c = "from_bytes_iter_valueerror" -> "ValueError: boom"
      [] c = "from_bytes_order_type" -> "TypeError: from_bytes() argument 'byteorder' must be str, not bytes"
      [] c = "to_bytes_too_many" -> "TypeError: to_bytes() takes at most 3 arguments (4 given)"
      [] c = "bytes_from_float" -> "TypeError: cannot convert 'float' object to bytes"
      [] c = "bytearray_from_none" -> "TypeError: cannot convert 'NoneType' object to bytearray"
      [] c = "bytearray_ignores_dunder_bytes" -> "bytearray(b'\\x01')"
      [] c = "bytes_uses_dunder_bytes" -> "b'xy'"
      [] c = "bytearray_iter_typeerror" -> "TypeError: cannot convert 'Bad' object to bytearray"
      [] c = "bytes_iter_valueerror" -> "ValueError: boom"
      [] c = "bytearray_count" -> "bytearray(b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00')"
      [] c = "fromhex_bytes" -> "TypeError: bad argument type for built-in operation"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* bit_length is the k with 2^(k-1) <= |n| < 2^k.
BitLengthBounds == Done /\ "method" \in DOMAIN program /\ program.method = "bit_length" /\ program.n # 0 =>
    LET k == BitLength(Abs(program.n)) IN 2 ^ (k - 1) <= Abs(program.n) /\ Abs(program.n) < 2 ^ k

\* from_bytes undoes to_bytes.
RoundTrip == \A n \in Ns, length \in 1..3, order \in Orders, signed \in BOOLEAN :
    LET p == [n |-> n, length |-> length, order |-> order, signed |-> signed]
        v == IF n < 0 THEN n + 256 ^ length ELSE n
        big == [i \in 1..length |-> (v \div 256 ^ (length - i)) % 256]
    IN  (n >= 0 \/ signed) /\ Fits(n, length, signed) =>
        FromBytes([bytes |-> IF order = "big" THEN big ELSE Reverse(big), order |-> order, signed |-> signed]) = n
=============================================================================
