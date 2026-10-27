---------------------------- MODULE BuiltinsText ----------------------------
(***************************************************************************)
(* The text built-in functions, as The Python Standard Library specifies   *)
(* them (library/functions.html, with                                      *)
(* library/stdtypes.html#str.isprintable): chr() of an __index__ value in  *)
(* range(0x110000) and its inverse ord(), which also takes a byte; repr()  *)
(* of a str quoting with ' unless the text has ' and no ", escaping the    *)
(* backslash, the chosen quote, \t, \n, and \r, other non-printable        *)
(* characters as \x, \u, or \U escapes, and keeping printable ones;        *)
(* ascii(), which also escapes every non-ASCII character; repr() and str() *)
(* requiring a str from __repr__ and __str__; format() through __format__, *)
(* object.__format__ refusing a non-empty spec; and print() writing str()  *)
(* of each argument with sep and end (None meaning the default) to file's  *)
(* write(), flushing on request.                                           *)
(*                                                                         *)
(* A program takes a string of up to two characters among A, ', ", \,      *)
(* newline, tab, U+007F, U+00E9, U+03B1, and U+1F600 and reports ascii()   *)
(* of it, the length of its repr(), or the ord() of each character; or     *)
(* runs one of the sources of CASES in a fresh namespace. The outcome is   *)
(* the ascii() text itself, or the repr of the other results and of the    *)
(* case's result, or the exception and its message.                        *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

VARIABLES program, outcome
vars == <<program, outcome>>

Points == {65, 39, 34, 92, 10, 9, 127, 233, 945, 128512}
Strings == UNION {[1..n -> Points] : n \in 0..2}

R(n) == ToString(n)
RECURSIVE Join(_)
Join(s) == IF s = <<>> THEN "" ELSE IF Len(s) = 1 THEN Head(s) ELSE Head(s) \o ", " \o Join(Tail(s))
RECURSIVE Concat(_)
Concat(s) == IF s = <<>> THEN "" ELSE Head(s) \o Concat(Tail(s))
Contains(s, x) == \E i \in DOMAIN s : s[i] = x

Hex == "0123456789abcdef"
RECURSIVE Digits(_, _)
Digits(n, width) == IF width = 0 THEN "" ELSE Digits(n \div 16, width - 1) \o SubSeq(Hex, (n % 16) + 1, (n % 16) + 1)

\* ' unless the text holds ' and no ".
Quote(s) == IF Contains(s, 39) /\ ~Contains(s, 34) THEN "\"" ELSE "'"

\* The ASCII escape of a character in a literal quoted by q.
Escape(cp, q) ==
    CASE cp = 92 -> "\\\\"
      [] cp = 39 /\ q = "'" -> "\\'"
      [] cp = 10 -> "\\n"
      [] cp = 9 -> "\\t"
      [] cp = 13 -> "\\r"
      [] cp < 32 \/ (cp >= 127 /\ cp < 256) -> "\\x" \o Digits(cp, 2)
      [] cp >= 256 /\ cp < 65536 -> "\\u" \o Digits(cp, 4)
      [] cp >= 65536 -> "\\U" \o Digits(cp, 8)
      \* The printable ASCII characters among the points stand for themselves.
      [] cp = 65 -> "A"
      [] cp = 39 -> "'"
      [] cp = 34 -> "\""

Ascii(s) == LET q == Quote(s) IN q \o Concat([i \in DOMAIN s |-> Escape(s[i], q)]) \o q

\* repr() keeps the printable characters beyond ASCII (here U+00E9, U+03B1,
\* and U+1F600) and escapes the rest as ascii() does.
ReprWidth(cp, q) == IF cp \in {233, 945, 128512} THEN 1 ELSE Len(Escape(cp, q))
RECURSIVE Sum(_)
Sum(s) == IF s = <<>> THEN 0 ELSE Head(s) + Sum(Tail(s))


Cases == {"chr_bounds", "chr_over", "chr_negative", "chr_float", "chr_huge", "ord_long", "ord_empty", "ord_bytes",
          "ord_int", "ascii_object", "repr_bad", "str_bad", "repr_recursive", "repr_bytes_quotes",
          "format_hook", "format_object_spec", "format_object_empty", "format_bad_return",
          "format_spec_type", "print_sep_end", "print_none_sep", "print_no_args", "print_flush",
          "print_bad_sep", "print_bad_end", "print_file_none_ok", "print_file_nowrite", "print_unknown_kw",
          "print_str_calls", "str_bytes_warns_not", "repr_str_quotes", "repr_nonprintable",
          "isprintable_rule", "format_width_unicode", "ascii_bytes_unchanged", "bin_format_spec"}
Programs == [op : {"ascii", "repr_len", "ord"}, s : Strings]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    LET s == p.s IN
    CASE p.op = "ascii" -> Ascii(s)
      [] p.op = "repr_len" -> R(2 + Sum([i \in DOMAIN s |-> ReprWidth(s[i], Quote(s))]))
      [] p.op = "ord" -> "[" \o Join([i \in DOMAIN s |-> R(s[i])]) \o "]"

Case(c) ==
    CASE c = "chr_bounds" -> "('\\x00', True, 1114111)"
      [] c = "chr_over" -> "ValueError: chr() arg not in range(0x110000)"
      [] c = "chr_negative" -> "ValueError: chr() arg not in range(0x110000)"
      [] c = "chr_float" -> "TypeError: 'float' object cannot be interpreted as an integer"
      [] c = "chr_huge" -> "ValueError: chr() arg not in range(0x110000)"
      [] c = "ord_long" -> "TypeError: ord() expected a character, but string of length 2 found"
      [] c = "ord_empty" -> "TypeError: ord() expected a character, but string of length 0 found"
      [] c = "ord_bytes" -> "(97, 98)"
      [] c = "ord_int" -> "TypeError: ord() expected string of length 1, but int found"
      [] c = "ascii_object" -> "('\\\\u03b1', True, '[\\\\u03b1]')"
      [] c = "repr_bad" -> "TypeError: BadRepr.__repr__() must return a str, not int"
      [] c = "str_bad" -> "TypeError: BadStr.__str__() must return a str, not bytes"
      [] c = "repr_recursive" -> "'[1, [...]]'"
      [] c = "repr_bytes_quotes" -> "('b\"\\'\"', 'b\\'\"\\'', 'b\\'\\\\\\'\"\\'')"
      [] c = "format_hook" -> "('F<x>', 'F<>', 'F<yz>')"
      [] c = "format_object_spec" -> "TypeError: unsupported format string passed to object.__format__"
      [] c = "format_object_empty" -> "'<object '"
      [] c = "format_bad_return" -> "TypeError: BadFormat.__format__() must return a str, not int"
      [] c = "format_spec_type" -> "TypeError: format() argument 2 must be str, not int"
      [] c = "print_sep_end" -> "['1', '|', 'a', '|', 'None', '!\\n']"
      [] c = "print_none_sep" -> "['1', ' ', '2', '\\n']"
      [] c = "print_no_args" -> "['\\n']"
      [] c = "print_flush" -> "1"
      [] c = "print_bad_sep" -> "TypeError: sep must be None or a string, not int"
      [] c = "print_bad_end" -> "TypeError: end must be None or a string, not bytes"
      [] c = "print_file_none_ok" -> "True"
      [] c = "print_file_nowrite" -> "AttributeError: 'int' object has no attribute 'write'"
      [] c = "print_unknown_kw" -> "TypeError: print() got an unexpected keyword argument 'x'"
      [] c = "print_str_calls" -> "['S!', '\\n']"
      [] c = "str_bytes_warns_not" -> "\"b'ab'\""
      [] c = "repr_str_quotes" -> "('\"it\\'s\"', '\\'say \"hi\"\\'', '\\'both \\\\\\' \"\\'')"
      [] c = "repr_nonprintable" -> "(\"'\\\\x00\\\\x1f\\\\x7f\\\\x80\\\\xa0\\\\xad'\", \"'\\\\u2028'\", \"'\\\\ud800'\")"
      [] c = "isprintable_rule" -> "(True, False, True, False)"
      [] c = "format_width_unicode" -> "'**\\u03b1**'"
      [] c = "ascii_bytes_unchanged" -> "\"b'\\\\xff'\""
      [] c = "bin_format_spec" -> "('1010', '0xa', '1111_1111')"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* The ascii() of a string is never shorter than its repr(), and they agree
\* on ASCII text.
AsciiWidens == Done /\ "s" \in DOMAIN program =>
    LET s == program.s  q == Quote(s) IN
    /\ Len(Ascii(s)) >= 2 + Sum([i \in DOMAIN s |-> ReprWidth(s[i], q)])
    /\ (\A i \in DOMAIN s : s[i] < 128) => Len(Ascii(s)) = 2 + Sum([i \in DOMAIN s |-> ReprWidth(s[i], q)])
=============================================================================
