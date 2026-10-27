----------------------------- MODULE FormatSpec -----------------------------
(***************************************************************************)
(* The format specification mini-language and format string syntax, as the *)
(* reference specifies them (library/string.html#formatspec and            *)
(* #formatstrings, with library/stdtypes.html#formatted-string-literals-f- *)
(* strings's format specifier): a spec is                                  *)
(* [[fill]align][sign][z][#][0][width][grouping][.precision][type];        *)
(* numbers align right by default and strings left, ^ centers with the     *)
(* extra fill on the right, and = pads between the sign and the digits; a  *)
(* 0 before the width selects 0 as the fill and, without an explicit       *)
(* alignment, = alignment, and then grouping extends to the padding zeros; *)
(* the sign is - for negatives only, + always, or a space for non-         *)
(* negatives; # adds the base prefix; , and _ group decimal digits by      *)
(* three, _ also binary, octal, and hex digits by four; integers take b,   *)
(* c, d, o, x, X, and n; f, %, and e round to the precision (six by        *)
(* default) with ties to even, % scaling by 100, e writing a two-digit     *)
(* signed exponent, and z turns a negative zero result positive; each type *)
(* and object rejects the options it does not support; and replacement     *)
(* fields name a positional argument (automatic or manual numbering, never *)
(* both), a keyword, attributes, and indexes, with a conversion !r, !s, or *)
(* !a, and a spec that may nest one level of replacement fields; doubled   *)
(* braces are literal.                                                     *)
(*                                                                         *)
(* A program formats an int (0, 5, -42, or 1234567) with every combination *)
(* of alignment, sign, alternate form, zero padding, width, grouping, and  *)
(* integer type, or a float num / 8 (0, 2.5, -0.125, 1234.375, or 0.5)     *)
(* with every combination of alignment, sign, z, zero padding, width,      *)
(* grouping, precision up to 2 or none, and type f, %, or e; or runs one   *)
(* of the sources of CASES in a fresh namespace. The outcome is the repr   *)
(* of the result, or the exception and its message.                        *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Signs == {"", "+", " "}
Groups == {"", ",", "_"}

Abs(n) == IF n < 0 THEN -n ELSE n
RECURSIVE Cat(_)
Cat(s) == IF s = <<>> THEN "" ELSE Head(s) \o Cat(Tail(s))
Lower == <<"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f">>
Upper == <<"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F">>
\* The digits of n >= 0 in base, most significant first.
RECURSIVE Digits(_, _, _)
Digits(n, base, chars) == IF n < base THEN <<chars[n + 1]>>
                          ELSE Digits(n \div base, base, chars) \o <<chars[(n % base) + 1]>>
Copies(c, k) == IF k <= 0 THEN <<>> ELSE [i \in 1..k |-> c]

\* Grouping by size; with a minimum, zeros first extend the digits to the
\* fewest whose grouped form is that long.
RECURSIVE Group(_, _, _)
Group(d, sep, size) == IF Len(d) <= size THEN d
                       ELSE Group(SubSeq(d, 1, Len(d) - size), sep, size) \o <<sep>> \o SubSeq(d, Len(d) - size + 1, Len(d))
Grouped(d, sep, size, minimum) ==
    LET k == CHOOSE k \in Len(d)..Len(d) + (IF minimum > 0 THEN minimum ELSE 0) :
                 /\ k + (k - 1) \div size >= minimum
                 /\ \A j \in Len(d)..k - 1 : j + (j - 1) \div size < minimum
    IN  Group(Copies("0", k - Len(d)) \o d, sep, size)

\* Padding to width: = goes between the sign (and prefix) and the digits;
\* ^ puts the odd fill character on the right.
Aligned(lead, digits, fill, align, width) ==
    LET body == lead \o digits  pad == width - Len(body)
    IN  CASE pad <= 0 -> body
          [] align = "<" -> body \o Copies(fill, pad)
          [] align = ">" -> Copies(fill, pad) \o body
          [] align = "^" -> Copies(fill, pad \div 2) \o body \o Copies(fill, pad - pad \div 2)
          [] align = "=" -> lead \o Copies(fill, pad) \o digits

\* A 0 before the width fills with 0 and, without an alignment, pads after
\* the sign.
Fill(explicit, zero) == IF explicit # "" THEN explicit ELSE IF zero = "0" THEN "0" ELSE " "
Align(given, zero) == IF given # "" THEN given ELSE IF zero = "0" THEN "=" ELSE ">"
Sign(negative, flag) == IF negative THEN <<"-">> ELSE IF flag = "" THEN <<>> ELSE <<flag>>

IntText(p) ==
    LET t == IF p.type = "" THEN "d" ELSE p.type
        fill == Fill(IF p.align = "*^" THEN "*" ELSE "", p.zero)
        align == Align(IF p.align = "*^" THEN "^" ELSE p.align, p.zero)
        sign == Sign(p.n < 0, p.sign)
        prefix == IF p.alt = "#" /\ t # "d" THEN <<"0", t>> ELSE <<>>
        base == CASE t = "b" -> 2 [] t = "o" -> 8 [] t \in {"x", "X"} -> 16 [] OTHER -> 10
        raw == Digits(Abs(p.n), base, IF t = "X" THEN Upper ELSE Lower)
        digits == IF p.group = "" THEN raw
                  ELSE Grouped(raw, p.group, IF t = "d" THEN 3 ELSE 4,
                               IF align = "=" /\ fill = "0" THEN p.width - Len(sign) - Len(prefix) ELSE 0)
    IN  Aligned(sign \o prefix, digits, fill, align, p.width)
IntFormat(p) ==
    IF p.group = "," /\ p.type \notin {"", "d"} THEN "ValueError: Cannot specify ',' with '" \o p.type \o "'."
    ELSE "'" \o Cat(IntText(p)) \o "'"

\* The nearest integer to num / den, ties to even.
Round(num, den) == LET q == num \div den  r == num % den
                   IN  IF 2 * r > den \/ (2 * r = den /\ q % 2 = 1) THEN q + 1 ELSE q
\* num / 8 is m / 1000 exactly, m = |num| * 125 (times 100 for %); f and %
\* round m to prec decimals, e to prec + 1 significant digits.
Fixed(m, prec) ==
    LET q == IF prec >= 3 THEN Digits(m, 10, Lower) \o Copies("0", prec - 3) ELSE Digits(Round(m, 10 ^ (3 - prec)), 10, Lower)
        text == Copies("0", prec + 1 - Len(q)) \o q
    IN  <<SubSeq(text, 1, Len(text) - prec), SubSeq(text, Len(text) - prec + 1, Len(text)), <<>>>>
Exponent(e) == <<"e", IF e < 0 THEN "-" ELSE "+">> \o (IF Abs(e) < 10 THEN <<"0">> ELSE <<>>) \o Digits(Abs(e), 10, Lower)
Scientific(m, prec) ==
    IF m = 0 THEN <<<<"0">>, Copies("0", prec), Exponent(0)>>
    ELSE LET dm == Digits(m, 10, Lower)  shift == Len(dm) - 1 - prec
             q0 == IF shift >= 0 THEN Digits(Round(m, 10 ^ shift), 10, Lower) ELSE dm \o Copies("0", -shift)
             carry == Len(q0) > prec + 1
             q == IF carry THEN SubSeq(q0, 1, Len(q0) - 1) ELSE q0
         IN  <<<<q[1]>>, Tail(q), Exponent(Len(dm) - 4 + (IF carry THEN 1 ELSE 0))>>

FloatFormat(p) ==
    LET prec == IF p.prec = -1 THEN 6 ELSE p.prec
        m == Abs(p.num) * 125 * (IF p.type = "%" THEN 100 ELSE 1)
        parts == IF p.type = "e" THEN Scientific(m, prec) ELSE Fixed(m, prec)
        whole == parts[1]  frac == parts[2]
        zero_value == \A i \in 1..Len(whole \o frac) : (whole \o frac)[i] = "0"
        fill == Fill("", p.zero)  align == Align(p.align, p.zero)
        sign == Sign(p.num < 0 /\ ~(p.z = "z" /\ zero_value), p.sign)
        tail == (IF frac = <<>> THEN <<>> ELSE <<".">> \o frac) \o parts[3] \o (IF p.type = "%" THEN <<"%">> ELSE <<>>)
        digits == IF p.group = "" THEN whole
                  ELSE Grouped(whole, p.group, 3, IF align = "=" /\ fill = "0" THEN p.width - Len(sign) - Len(tail) ELSE 0)
    IN  "'" \o Cat(Aligned(sign, digits \o tail, fill, align, p.width)) \o "'"


Cases == {"str_align", "str_precision", "str_equal_align", "str_sign", "str_type_bad", "str_grouping",
          "str_alternate", "int_precision", "int_c", "int_c_sign", "int_c_range", "int_n", "int_n_grouping",
          "int_float_types", "int_z", "int_bad_type", "bool_formats", "float_default", "float_g",
          "float_upper", "float_special_width", "float_alternate", "float_c", "float_grouping_frac",
          "float_underscore", "float_negative_zero", "complex_format", "complex_zero_pad", "complex_equal",
          "fill_brace", "fill_unicode", "width_huge", "invalid_spec", "precision_too_big", "format_dunder",
          "format_bad_return", "object_format_nonempty", "object_format_empty", "format_spec_type",
          "str_format_positional", "str_format_auto", "str_format_mixed", "str_format_mixed_auto_first",
          "str_format_keywords", "str_format_attr_index", "str_format_index_int_key",
          "str_format_conversions", "str_format_bad_conversion", "str_format_nested",
          "str_format_nested_too_deep", "str_format_braces", "str_format_single_close",
          "str_format_single_open", "str_format_missing_index", "str_format_missing_key",
          "str_format_missing_auto", "str_format_empty_attr", "str_format_index_unclosed",
          "str_format_negative_index", "str_format_conversion_then_spec", "str_format_example_align",
          "str_format_example_bases", "str_format_example_prefix", "str_format_example_percent",
          "str_format_example_comma", "str_format_example_nesting", "str_format_example_items",
          "str_format_extra_args", "format_map_missing", "fstring_format_spec", "format_builtin_default"}
Programs == [kind : {"int"}, n : {0, 5, -42, 1234567}, align : {"", "<", ">", "^", "=", "*^"}, sign : Signs,
             alt : {"", "#"}, zero : {"", "0"}, width : {0, 9}, group : Groups, type : {"", "d", "b", "x", "X", "o"}]
            \cup [kind : {"float"}, num : {0, 20, -1, 9875, 4}, align : {"", "<", "^", "="}, sign : Signs,
                   z : {"", "z"}, zero : {"", "0"}, width : {0, 12}, group : Groups, prec : -1..2,
                   type : {"f", "%", "e"}]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Generated(p) == IF p.kind = "int" THEN IntFormat(p) ELSE FloatFormat(p)

Case(c) ==
    CASE c = "str_align" -> "('ab   ', '   ab', ' ab  ', '**ab**', 'ab   ')"
      [] c = "str_precision" -> "('abc', '    ab')"
      [] c = "str_equal_align" -> "ValueError: '=' alignment not allowed in string format specifier"
      [] c = "str_sign" -> "ValueError: Sign not allowed in string format specifier"
      [] c = "str_type_bad" -> "ValueError: Unknown format code 'd' for object of type 'str'"
      [] c = "str_grouping" -> "ValueError: Cannot specify ',' with 's'."
      [] c = "str_alternate" -> "ValueError: Alternate form (#) not allowed in string format specifier"
      [] c = "int_precision" -> "ValueError: Precision not allowed in integer format specifier"
      [] c = "int_c" -> "('A', '\\U0001f600')"
      [] c = "int_c_sign" -> "ValueError: Sign not allowed with integer format specifier 'c'"
      [] c = "int_c_range" -> "OverflowError: %c arg not in range(0x110000)"
      [] c = "int_n" -> "('1234567', '-5')"
      [] c = "int_n_grouping" -> "ValueError: Cannot specify ',' with 'n'."
      [] c = "int_float_types" -> "('5.000000', '5.000000e+00', '500.000000%', '5')"
      [] c = "int_z" -> "ValueError: Negative zero coercion (z) not allowed in integer format specifier"
      [] c = "int_bad_type" -> "ValueError: Unknown format code 's' for object of type 'int'"
      [] c = "bool_formats" -> "('True', '1', '    0', '1')"
      [] c = "float_default" -> "('1.5', '1e+16', '1e-05', '1.0', '1.23e+05')"
      [] c = "float_g" -> "('0.0001234', '1.23457e+08', '100', '100.000', '2')"
      [] c = "float_upper" -> "('1.000000E+20', 'INF', 'NAN', '-inf')"
      [] c = "float_special_width" -> "('00000inf', '+nan')"
      [] c = "float_alternate" -> "('2.', '2.e+00')"
      [] c = "float_c" -> "ValueError: Unknown format code 'c' for object of type 'float'"
      [] c = "float_grouping_frac" -> "'1,234,567.125'"
      [] c = "float_underscore" -> "'1_234_567.0'"
      [] c = "float_negative_zero" -> "('-0.000000', '0.000000', '0.00')"
      [] c = "complex_format" -> "('(1+2j)', '1.0+2.0j', '(-0-1j)', '       (1+2j)       ')"
      [] c = "complex_zero_pad" -> "ValueError: Zero padding is not allowed in complex format specifier"
      [] c = "complex_equal" -> "ValueError: '=' alignment flag is not allowed in complex format specifier"
      [] c = "fill_brace" -> "'{{5{{'"
      [] c = "fill_unicode" -> "'\\xe9\\xe95\\xe9\\xe9'"
      [] c = "width_huge" -> "ValueError: Too many decimal digits in format string"
      [] c = "invalid_spec" -> "ValueError: Unknown format code '<' for object of type 'int'"
      [] c = "precision_too_big" -> "ValueError: Too many decimal digits in format string"
      [] c = "format_dunder" -> "('P[abc]', 'P[xyz]', 'P[q]')"
      [] c = "format_bad_return" -> "TypeError: BadFormat.__format__() must return a str, not int"
      [] c = "object_format_nonempty" -> "TypeError: unsupported format string passed to object.__format__"
      [] c = "object_format_empty" -> "'o'"
      [] c = "format_spec_type" -> "TypeError: format() argument 2 must be str, not int"
      [] c = "str_format_positional" -> "'a, b, a'"
      [] c = "str_format_auto" -> "'a, b'"
      [] c = "str_format_mixed" -> "ValueError: cannot switch from manual field specification to automatic field numbering"
      [] c = "str_format_mixed_auto_first" -> "ValueError: cannot switch from automatic field numbering to manual field specification"
      [] c = "str_format_keywords" -> "'n1'"
      [] c = "str_format_attr_index" -> "'3 5 9'"
      [] c = "str_format_index_int_key" -> "'int'"
      [] c = "str_format_conversions" -> "\"P() p P() '\\xe9'\""
      [] c = "str_format_bad_conversion" -> "ValueError: Unknown conversion specifier x"
      [] c = "str_format_nested" -> "'3.14'"
      [] c = "str_format_nested_too_deep" -> "ValueError: Max string recursion exceeded"
      [] c = "str_format_braces" -> "'{} {7}'"
      [] c = "str_format_single_close" -> "ValueError: Single '}' encountered in format string"
      [] c = "str_format_single_open" -> "ValueError: expected '}' before end of string"
      [] c = "str_format_missing_index" -> "IndexError: Replacement index 2 out of range for positional args tuple"
      [] c = "str_format_missing_key" -> "KeyError: 'k'"
      [] c = "str_format_missing_auto" -> "IndexError: Replacement index 1 out of range for positional args tuple"
      [] c = "str_format_empty_attr" -> "ValueError: Empty attribute in format string"
      [] c = "str_format_index_unclosed" -> "ValueError: expected '}' before end of string"
      [] c = "str_format_negative_index" -> "KeyError: '-1'"
      [] c = "str_format_conversion_then_spec" -> "\"   'a'\""
      [] c = "str_format_example_align" -> "('left aligned                  ', '***********centered***********')"
      [] c = "str_format_example_bases" -> "'int: 42;  hex: 2a;  oct: 52;  bin: 101010'"
      [] c = "str_format_example_prefix" -> "'int: 42;  hex: 0x2a;  oct: 0o52;  bin: 0b101010'"
      [] c = "str_format_example_percent" -> "'Correct answers: 86.36%'"
      [] c = "str_format_example_comma" -> "'1,234,567,890'"
      [] c = "str_format_example_nesting" -> "['text<<<<<<<<<<<<', '^^^^^^text^^^^^^', '>>>>>>>>>>>>text']"
      [] c = "str_format_example_items" -> "'The complex number (3-5j) is formed from the real part 3.0 and the imaginary part -5.0.'"
      [] c = "str_format_extra_args" -> "'1'"
      [] c = "format_map_missing" -> "KeyError: 'a'"
      [] c = "fstring_format_spec" -> "\"  3.14| 'x' \""
      [] c = "format_builtin_default" -> "('5', 'a', 'None')"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* A width is a minimum: the formatted int is never shorter.
WidthIsMinimum == Done /\ "n" \in DOMAIN program => Len(IntText(program)) >= program.width
=============================================================================
