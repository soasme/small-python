--------------------------- MODULE PercentFormat ----------------------------
(***************************************************************************)
(* printf-style string and bytes formatting, as the Built-in Types chapter *)
(* specifies it (library/stdtypes.html#printf-style-string-formatting and  *)
(* #printf-style-bytes-formatting): each conversion is % with an optional  *)
(* parenthesized mapping key, flags (- left-adjusts, overriding 0, which   *)
(* pads with zeros after the sign; + and space set the sign of non-        *)
(* negatives; # adds the 0o, 0x, or 0X prefix and keeps a float's point),  *)
(* a minimum width and a precision (either may be * to take an argument),  *)
(* an ignored length modifier, and a type; for d, i, u, o, x, and X the    *)
(* precision is a minimum number of digits, and for f and e the number of  *)
(* decimals (six by default) rounded half to even; %% is a literal         *)
(* percent; c takes an integer or a single character, s and r and a        *)
(* convert with str, repr, and ascii, while bytes formatting takes bytes-  *)
(* like objects or __bytes__ for s and b and treats r as a; and the        *)
(* arguments must match the conversions, a mapping only with keys, or a    *)
(* TypeError or ValueError reports the mismatch.                           *)
(*                                                                         *)
(* A program formats an int (0, 5, -42, or 255) with every flag            *)
(* combination among -, +, space, 0, #, -0, +0, #0, and - space, width 7   *)
(* or none, precision 0, 3, or none, and type d, i, o, x, X, or u, or a    *)
(* float num / 8 (0, 2.5, -0.125, or 1234.375) the same way with type f or *)
(* e, into a str or a bytes object; or runs one of the sources of CASES in *)
(* a fresh namespace. The outcome is the repr of the result, or the        *)
(* exception and its message.                                              *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Flags == {{}, {"-"}, {"+"}, {" "}, {"0"}, {"#"}, {"-", "0"}, {"+", "0"}, {"#", "0"}, {"-", " "}}

Abs(n) == IF n < 0 THEN -n ELSE n
RECURSIVE Cat(_)
Cat(s) == IF s = <<>> THEN "" ELSE Head(s) \o Cat(Tail(s))
Lower == <<"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f">>
Upper == <<"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F">>
RECURSIVE Digits(_, _, _)
Digits(n, base, chars) == IF n < base THEN <<chars[n + 1]>>
                          ELSE Digits(n \div base, base, chars) \o <<chars[(n % base) + 1]>>
Copies(c, k) == IF k <= 0 THEN <<>> ELSE [i \in 1..k |-> c]
Round(num, den) == LET q == num \div den  r == num % den
                   IN  IF 2 * r > den \/ (2 * r = den /\ q % 2 = 1) THEN q + 1 ELSE q

Sign(negative, flags) == CASE negative -> <<"-">> [] "+" \in flags -> <<"+">> [] " " \in flags -> <<" ">>
                           [] OTHER -> <<>>
\* - pads on the right and overrides 0, which pads between sign and digits.
Padded(lead, body, flags, width) ==
    LET n == width - Len(lead) - Len(body)
    IN  CASE n <= 0 -> lead \o body
          [] "-" \in flags -> lead \o body \o Copies(" ", n)
          [] "0" \in flags -> lead \o Copies("0", n) \o body
          [] OTHER -> Copies(" ", n) \o lead \o body

\* The precision of an integer conversion is its minimum number of digits.
IntText(p) ==
    LET base == CASE p.type = "o" -> 8 [] p.type \in {"x", "X"} -> 16 [] OTHER -> 10
        raw == Digits(Abs(p.n), base, IF p.type = "X" THEN Upper ELSE Lower)
        digits == Copies("0", p.prec - Len(raw)) \o raw
        prefix == IF "#" \in p.flags /\ base # 10 THEN <<"0", p.type>> ELSE <<>>
    IN  Padded(Sign(p.n < 0, p.flags) \o prefix, digits, p.flags, p.width)

Exponent(e) == <<"e", IF e < 0 THEN "-" ELSE "+">> \o (IF Abs(e) < 10 THEN <<"0">> ELSE <<>>) \o Digits(Abs(e), 10, Lower)
\* num / 8 = m / 1000 with m = |num| * 125; # keeps the point at precision 0.
FloatText(p) ==
    LET prec == IF p.prec = -1 THEN 6 ELSE p.prec
        m == Abs(p.num) * 125
        point(frac) == IF frac # <<>> THEN <<".">> \o frac ELSE IF "#" \in p.flags THEN <<".">> ELSE <<>>
        fixed == LET q == IF prec >= 3 THEN Digits(m, 10, Lower) \o Copies("0", prec - 3)
                          ELSE Digits(Round(m, 10 ^ (3 - prec)), 10, Lower)
                     text == Copies("0", prec + 1 - Len(q)) \o q
                 IN  SubSeq(text, 1, Len(text) - prec) \o point(SubSeq(text, Len(text) - prec + 1, Len(text)))
        sci == IF m = 0 THEN <<"0">> \o point(Copies("0", prec)) \o Exponent(0)
               ELSE LET dm == Digits(m, 10, Lower)  shift == Len(dm) - 1 - prec
                        q0 == IF shift >= 0 THEN Digits(Round(m, 10 ^ shift), 10, Lower) ELSE dm \o Copies("0", -shift)
                        carry == Len(q0) > prec + 1
                        q == IF carry THEN SubSeq(q0, 1, Len(q0) - 1) ELSE q0
                    IN  <<q[1]>> \o point(Tail(q)) \o Exponent(Len(dm) - 4 + (IF carry THEN 1 ELSE 0))
    IN  Padded(Sign(p.num < 0, p.flags), IF p.type = "f" THEN fixed ELSE sci, p.flags, p.width)


Cases == {"s_r_a", "s_object", "percent_literal", "mapping", "mapping_missing", "mapping_needs_dict", "mapping_mixed",
          "star_width", "star_negative", "star_not_int", "single_value", "tuple_value", "not_enough",
          "not_all_converted", "no_format_tuple", "no_format_dict", "unsupported_char", "incomplete",
          "c_conversion", "c_bad", "c_range", "c_float", "d_float", "d_index", "d_str", "x_float",
          "x_index", "f_int", "f_str", "g_formats", "E_F", "huge_int", "x_negative_alt", "length_modifier",
          "bytes_basic", "bytes_b_alias", "bytes_dunder", "bytes_str_rejected", "bytes_r_is_a", "bytes_c",
          "bytes_c_bad", "bytes_mapping", "bytes_percent", "bytearray_result", "bytes_not_all",
          "bytes_unsupported", "bytes_float"}
Programs == [kind : {"int"}, n : {0, 5, -42, 255}, flags : Flags, width : {0, 7}, prec : {-1, 0, 3},
             type : {"d", "i", "o", "x", "X", "u"}, target : {"str", "bytes"}]
            \cup [kind : {"float"}, num : {0, 20, -1, 9875}, flags : Flags, width : {0, 7}, prec : {-1, 0, 3},
                   type : {"f", "e"}, target : {"str", "bytes"}]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Generated(p) ==
    LET text == IF p.kind = "int" THEN IntText(p) ELSE FloatText(p)
    IN  (IF p.target = "bytes" THEN "b'" ELSE "'") \o Cat(text) \o "'"

Case(c) ==
    CASE c = "s_r_a" -> "\"\\xe9 '\\xe9' '\\\\xe9'\""
      [] c = "s_object" -> "'p|P()|   ab|ab   |x'"
      [] c = "percent_literal" -> "'100% 5'"
      [] c = "mapping" -> "'Python has 002 quote types.'"
      [] c = "mapping_missing" -> "KeyError: 'x'"
      [] c = "mapping_needs_dict" -> "TypeError: format requires a mapping, not tuple"
      [] c = "mapping_mixed" -> "ValueError: format requires a parenthesised mapping key at position 6"
      [] c = "star_width" -> "'    1|2   |3.14'"
      [] c = "star_negative" -> "'1    '"
      [] c = "star_not_int" -> "TypeError: format argument 1: * requires int, not str"
      [] c = "single_value" -> "('5', '5', '[1, 2]')"
      [] c = "tuple_value" -> "'(1, 2)'"
      [] c = "not_enough" -> "TypeError: not enough arguments for format string (got 1)"
      [] c = "not_all_converted" -> "TypeError: not all arguments converted during string formatting (required 1, got 2)"
      [] c = "no_format_tuple" -> "TypeError: not all arguments converted during string formatting (required 0, got 1)"
      [] c = "no_format_dict" -> "'abc'"
      [] c = "unsupported_char" -> "ValueError: unsupported format %y at position 0"
      [] c = "incomplete" -> "ValueError: stray % at position 4"
      [] c = "c_conversion" -> "('A', 'z', '\\U0001f600')"
      [] c = "c_bad" -> "TypeError: format argument: %c requires an integer or a unicode character, not a string of length 2"
      [] c = "c_range" -> "OverflowError: format argument: %c argument not in range(0x110000)"
      [] c = "c_float" -> "TypeError: format argument: %c requires an integer or a unicode character, not float"
      [] c = "d_float" -> "('2', '-2', '1')"
      [] c = "d_index" -> "'7'"
      [] c = "d_str" -> "TypeError: format argument: %d requires a real number, not str"
      [] c = "x_float" -> "TypeError: format argument: %x requires an integer, not float"
      [] c = "x_index" -> "'7'"
      [] c = "f_int" -> "('3.000000', '1.50')"
      [] c = "f_str" -> "TypeError: format argument: %f requires a real number, not str"
      [] c = "g_formats" -> "('0.0001', '1e+20', '1.00000', '1E-10', '1.23e+03')"
      [] c = "E_F" -> "('1.500000E+00', 'INF', 'nan', ' -inf')"
      [] c = "huge_int" -> "'1000000000000000000000000000000'"
      [] c = "x_negative_alt" -> "('-0xff', '0o0', '0XFF')"
      [] c = "length_modifier" -> "'1 2 3.000000'"
      [] c = "bytes_basic" -> "b'ab 5 ff  2.50'"
      [] c = "bytes_b_alias" -> "b'x|m'"
      [] c = "bytes_dunder" -> "b'bb'"
      [] c = "bytes_str_rejected" -> "TypeError: format argument: %b requires a bytes-like object, or an object that implements __bytes__, not str"
      [] c = "bytes_r_is_a" -> "b\"'\\\\xe9' '\\\\xe9'\""
      [] c = "bytes_c" -> "(b'A', b'z')"
      [] c = "bytes_c_bad" -> "OverflowError: format argument: %c argument not in range(256)"
      [] c = "bytes_mapping" -> "b'v'"
      [] c = "bytes_percent" -> "b'%1'"
      [] c = "bytearray_result" -> "bytearray(b'5')"
      [] c = "bytes_not_all" -> "TypeError: not all arguments converted during bytes formatting (required 1, got 2)"
      [] c = "bytes_unsupported" -> "ValueError: unsupported format %y at position 0"
      [] c = "bytes_float" -> "b'1.2e+04'"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* Width is a minimum, and - never pads on the left.
WidthIsMinimum == Done /\ "n" \in DOMAIN program => Len(IntText(program)) >= program.width
LeftAdjusted == Done /\ "n" \in DOMAIN program /\ "-" \in program.flags =>
    (Head(IntText(program)) = " " => " " \in program.flags)
=============================================================================
