------------------------------ MODULE Strings -------------------------------
(***************************************************************************)
(* The str type and its methods, as the Built-in Types chapter specifies   *)
(* them (library/stdtypes.html#text-sequence-type-str and #string-         *)
(* methods): strings are immutable sequences of code points, indexing      *)
(* yields strings of length 1, and str() of an object is its __str__ (or   *)
(* repr), of bytes with an encoding their decoding; find and rfind give    *)
(* the lowest and highest index of a substring or -1, index and rindex     *)
(* raise ValueError instead, count counts non-overlapping occurrences (an  *)
(* empty one between every character), startswith and endswith test the    *)
(* ends; split cuts at every occurrence of a nonempty separator and,       *)
(* without one, at runs of whitespace, dropping empty strings; rsplit with *)
(* maxsplit cuts from the right; partition and rpartition split at the     *)
(* first or last occurrence; replace substitutes non-overlapping           *)
(* occurrences from the left, an empty old string matching between every   *)
(* character; removeprefix and removesuffix drop an exact affix, while     *)
(* strip, lstrip, and rstrip drop any characters of a set; center, ljust,  *)
(* rjust, and zfill pad to a width, center giving the extra fill character *)
(* to the left only when both the padding and the width are odd, and zfill *)
(* keeping a leading sign first; and the case mappings, character-class    *)
(* predicates, expandtabs, splitlines, join, maketrans, translate, and     *)
(* encode behave as the chapter describes, with CPython's argument errors. *)
(*                                                                         *)
(* A program calls a search, split, replace, affix, or strip method on     *)
(* every string s of up to three characters from a, b, and space, with     *)
(* every argument t of up to two (replace substituting X, with and without *)
(* a count of 1, and rsplit with a maxsplit of 1), or splits or strips s   *)
(* at whitespace; or pads every string of up to three characters from a    *)
(* and - to every width up to 6 with * (zfill with zeros); or runs one of  *)
(* the sources of CASES in a fresh namespace. The outcome is the repr of   *)
(* the result, or the exception and its message.                           *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Search == {"find", "rfind", "count", "startswith", "endswith", "partition", "rpartition", "split", "rsplit1", "replace",
           "replace1", "removeprefix", "removesuffix", "strip", "lstrip", "rstrip", "index"}
Whole == {"split_ws", "rsplit_ws1", "strip_ws"}
Pad == {"center", "ljust", "rjust", "zfill"}
Strs == UNION {[1..n -> {"a", "b", " "}] : n \in 0..3}
Subs == UNION {[1..n -> {"a", "b", " "}] : n \in 0..2}
PadStrs == UNION {[1..n -> {"a", "-"}] : n \in 0..3}

R(n) == ToString(n)
Bool(b) == IF b THEN "True" ELSE "False"
Min(S) == CHOOSE x \in S : \A y \in S : x <= y
Max(S) == CHOOSE x \in S : \A y \in S : x >= y
RECURSIVE Cat(_)
Cat(s) == IF s = <<>> THEN "" ELSE Head(s) \o Cat(Tail(s))
Q(s) == "'" \o Cat(s) \o "'"
RECURSIVE Join(_)
Join(l) == IF l = <<>> THEN "" ELSE IF Len(l) = 1 THEN Head(l) ELSE Head(l) \o ", " \o Join(Tail(l))
List(parts) == "[" \o Join([i \in 1..Len(parts) |-> Q(parts[i])]) \o "]"
Triple(a, b, c) == "(" \o Q(a) \o ", " \o Q(b) \o ", " \o Q(c) \o ")"
Before(s, i) == SubSeq(s, 1, i - 1)
After(s, i, t) == SubSeq(s, i + Len(t), Len(s))

\* The 1-based positions where t occurs in s; an empty t occurs everywhere.
Positions(s, t) == {i \in 1..Len(s) + 1 : i + Len(t) - 1 <= Len(s) /\ SubSeq(s, i, i + Len(t) - 1) = t}

RECURSIVE Count(_, _)
Count(s, t) == IF Positions(s, t) = {} THEN 0
               ELSE 1 + Count(After(s, Min(Positions(s, t)), t), t)
RECURSIVE Split(_, _)
Split(s, t) == IF Positions(s, t) = {} THEN <<s>>
               ELSE LET i == Min(Positions(s, t)) IN <<Before(s, i)>> \o Split(After(s, i, t), t)
RECURSIVE Replace(_, _)
Replace(s, t) == IF Positions(s, t) = {} THEN Cat(s)
                 ELSE LET i == Min(Positions(s, t)) IN Cat(Before(s, i)) \o "X" \o Replace(After(s, i, t), t)
RECURSIVE XAfter(_)
XAfter(s) == IF s = <<>> THEN "" ELSE Head(s) \o "X" \o XAfter(Tail(s))

RECURSIVE LStrip(_, _)
LStrip(s, chars) == IF s # <<>> /\ Head(s) \in chars THEN LStrip(Tail(s), chars) ELSE s
RECURSIVE RStrip(_, _)
RStrip(s, chars) == IF s # <<>> /\ s[Len(s)] \in chars THEN RStrip(SubSeq(s, 1, Len(s) - 1), chars) ELSE s
Chars(t) == {t[i] : i \in DOMAIN t}

\* Runs of non-whitespace, left to right.
RECURSIVE Words(_)
Words(s) == LET rest == LStrip(s, {" "})
                gaps == {i \in DOMAIN rest : rest[i] = " "}
                end == IF gaps = {} THEN Len(rest) + 1 ELSE Min(gaps)
            IN  IF rest = <<>> THEN <<>> ELSE <<SubSeq(rest, 1, end - 1)>> \o Words(SubSeq(rest, end, Len(rest)))
\* rsplit(None, 1): the last word, and what precedes it with trailing
\* whitespace removed, if anything.
RSplitWords(s) == LET r == RStrip(s, {" "})  gaps == {i \in DOMAIN r : r[i] = " "}
                  IN  IF r = <<>> THEN <<>>
                      ELSE IF gaps = {} THEN <<r>>
                      ELSE LET head == RStrip(Before(r, Max(gaps)), {" "})
                           IN  (IF head = <<>> THEN <<>> ELSE <<head>>) \o <<SubSeq(r, Max(gaps) + 1, Len(r))>>

Searched(p) ==
    LET s == p.s  t == p.t  at == Positions(s, t)
    IN  CASE p.method \in {"split", "rsplit1", "partition", "rpartition"} /\ t = <<>> -> "ValueError: empty separator"
          [] p.method = "find" -> R(IF at = {} THEN -1 ELSE Min(at) - 1)
          [] p.method = "rfind" -> R(IF at = {} THEN -1 ELSE Max(at) - 1)
          [] p.method = "index" -> IF at = {} THEN "ValueError: substring not found" ELSE R(Min(at) - 1)
          [] p.method = "count" -> R(IF t = <<>> THEN Len(s) + 1 ELSE Count(s, t))
          [] p.method = "startswith" -> Bool(1 \in at)
          [] p.method = "endswith" -> Bool(Len(s) - Len(t) + 1 \in at)
          [] p.method = "split" -> List(Split(s, t))
          [] p.method = "rsplit1" -> IF at = {} THEN List(<<s>>) ELSE List(<<Before(s, Max(at)), After(s, Max(at), t)>>)
          [] p.method = "partition" -> IF at = {} THEN Triple(s, <<>>, <<>>)
                                       ELSE Triple(Before(s, Min(at)), t, After(s, Min(at), t))
          [] p.method = "rpartition" -> IF at = {} THEN Triple(<<>>, <<>>, s)
                                        ELSE Triple(Before(s, Max(at)), t, After(s, Max(at), t))
          [] p.method = "replace" -> "'" \o (IF t = <<>> THEN "X" \o XAfter(s) ELSE Replace(s, t)) \o "'"
          [] p.method = "replace1" -> "'" \o (IF at = {} THEN Cat(s)
                                              ELSE Cat(Before(s, Min(at))) \o "X" \o Cat(After(s, Min(at), t))) \o "'"
          [] p.method = "removeprefix" -> Q(IF 1 \in at THEN After(s, 1, t) ELSE s)
          [] p.method = "removesuffix" -> Q(IF Len(s) - Len(t) + 1 \in at THEN SubSeq(s, 1, Len(s) - Len(t)) ELSE s)
          [] p.method = "strip" -> Q(RStrip(LStrip(s, Chars(t)), Chars(t)))
          [] p.method = "lstrip" -> Q(LStrip(s, Chars(t)))
          [] p.method = "rstrip" -> Q(RStrip(s, Chars(t)))

RECURSIVE Fill(_, _)
Fill(c, n) == IF n <= 0 THEN "" ELSE c \o Fill(c, n - 1)
\* CPython's pad: the left share of center's padding gets the extra
\* character when the padding and the width are both odd.
Padded(p) ==
    LET s == p.s  w == p.width  pad == w - Len(s)
        left == pad \div 2 + (IF pad % 2 = 1 /\ w % 2 = 1 THEN 1 ELSE 0)
    IN  CASE w <= Len(s) -> Q(s)
          [] p.method = "center" -> "'" \o Fill("*", left) \o Cat(s) \o Fill("*", pad - left) \o "'"
          [] p.method = "ljust" -> "'" \o Cat(s) \o Fill("*", pad) \o "'"
          [] p.method = "rjust" -> "'" \o Fill("*", pad) \o Cat(s) \o "'"
          [] s # <<>> /\ Head(s) = "-" -> "'-" \o Fill("0", pad) \o Cat(Tail(s)) \o "'"
          [] OTHER -> "'" \o Fill("0", pad) \o Cat(s) \o "'"


Cases == {"capitalize", "casefold", "lower_upper", "final_sigma", "swapcase", "title", "istitle", "isupper_islower",
          "isalpha_isalnum", "isascii", "digit_classes", "isidentifier", "isprintable", "isspace",
          "expandtabs", "splitlines", "splitlines_boundaries", "split_vs_splitlines", "split_maxsplit",
          "rsplit_maxsplit", "split_bad_sep", "join", "join_nonstr", "join_bytes", "maketrans_dict",
          "maketrans_three", "maketrans_unequal", "maketrans_bad_key", "translate",
          "translate_lookup_error", "translate_bad_value", "translate_ord_value", "encode", "encode_error",
          "encode_unknown", "count_range", "find_range", "find_in_operator", "index_error", "rindex_error",
          "startswith_tuple", "startswith_bad", "startswith_tuple_bad", "strip_examples",
          "lstrip_vs_removeprefix", "strip_none", "strip_bad", "replace_count_keyword", "zfill_examples",
          "center_bad_fill", "ljust_bad_fill", "center_index_width", "center_float_width",
          "pad_unicode_fill", "partition_bad", "str_no_args", "str_object", "str_bad_dunder",
          "str_bytes_repr", "str_decode", "str_decode_error", "str_decode_replace", "str_encoding_nonbytes",
          "str_encoding_int", "str_subclass_returns", "index_char", "immutable", "concat_literals",
          "triple_quoted", "u_prefix", "ur_prefix", "code_points", "method_on_type", "method_wrong_self",
          "too_many_args", "keyword_rejected", "format_map"}
Programs == [method : Search, s : Strs, t : Subs]
            \cup [method : Whole, s : Strs]
            \cup [method : Pad, s : PadStrs, width : 0..6]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Generated(p) ==
    CASE p.method \in Search -> Searched(p)
      [] p.method = "split_ws" -> List(Words(p.s))
      [] p.method = "rsplit_ws1" -> List(RSplitWords(p.s))
      [] p.method = "strip_ws" -> Q(RStrip(LStrip(p.s, {" "}), {" "}))
      [] OTHER -> Padded(p)

Case(c) ==
    CASE c = "capitalize" -> "('Hello world', '\\u01c5a', '', '1a')"
      [] c = "casefold" -> "('strasse', '\\u03c3\\u03b1\\u03c3', 'fi')"
      [] c = "lower_upper" -> "('\\xe0b\\xe7', 'STRASSE', 'FI', 'i\\u0307', 2)"
      [] c = "final_sigma" -> "('\\u03c3\\u03b1\\u03c2', '\\u03b1\\u03c2 \\u03c3', '\\u03c3')"
      [] c = "swapcase" -> "('hELLO SS', '\\u01c5')"
      [] c = "title" -> "(\"They'Re Bill'S Friends\", 'Hello1World', '\\u01c5emal', 'Ssa')"
      [] c = "istitle" -> "(True, False, False, True, True)"
      [] c = "isupper_islower" -> "(True, False, True, False, False)"
      [] c = "isalpha_isalnum" -> "(True, False, False, True, False)"
      [] c = "isascii" -> "(True, True, False)"
      [] c = "digit_classes" -> "[(True, True, True), (False, True, True), (False, False, True), (True, True, True), (False, False, True), (False, False, False)]"
      [] c = "isidentifier" -> "(True, False, True, True, True, False)"
      [] c = "isprintable" -> "(True, False, True, False, False)"
      [] c = "isspace" -> "(True, False, False)"
      [] c = "expandtabs" -> "('01      012     0123    01234', '01  012 0123    01234', 'a\\n  b', 'ab', 'ab')"
      [] c = "splitlines" -> "(['ab c', '', 'de fg', 'kl'], ['ab c\\n', '\\n', 'de fg\\r', 'kl\\r\\n'], [], ['One line'])"
      [] c = "splitlines_boundaries" -> "['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']"
      [] c = "split_vs_splitlines" -> "([''], ['Two lines', ''])"
      [] c = "split_maxsplit" -> "(['1', '2,3'], ['1', '2', '', '3', ''], ['1', '2   3   '], ['1', '2', '3<4'])"
      [] c = "rsplit_maxsplit" -> "(['1,2', '3'], ['  a b', 'c'])"
      [] c = "split_bad_sep" -> "TypeError: must be str or None, not int"
      [] c = "join" -> "('a, b', '', 'a-b-c', '1')"
      [] c = "join_nonstr" -> "TypeError: sequence item 1: expected str instance, int found"
      [] c = "join_bytes" -> "TypeError: sequence item 0: expected str instance, bytes found"
      [] c = "maketrans_dict" -> "{97: '1', 98: None, 99: 'xyz'}"
      [] c = "maketrans_three" -> "{97: 120, 98: 121, 99: None}"
      [] c = "maketrans_unequal" -> "ValueError: the first two maketrans arguments must have equal length"
      [] c = "maketrans_bad_key" -> "ValueError: string keys in translatetable must be of length 1"
      [] c = "translate" -> "'1xyz1d'"
      [] c = "translate_lookup_error" -> "'Abc'"
      [] c = "translate_bad_value" -> "TypeError: character mapping must return integer, None or str"
      [] c = "translate_ord_value" -> "'b'"
      [] c = "encode" -> "(b'\\xc3\\xa9', b'\\xe9', b'?', b'')"
      [] c = "encode_error" -> "UnicodeEncodeError: 'ascii' codec can't encode character '\\xe9' in position 0: ordinal not in range(128)"
      [] c = "encode_unknown" -> "LookupError: unknown encoding: nosuch"
      [] c = "count_range" -> "(2, 3, 1, 0)"
      [] c = "find_range" -> "(5, -1, -1, 3, 2)"
      [] c = "find_in_operator" -> "(True, True)"
      [] c = "index_error" -> "ValueError: substring not found"
      [] c = "rindex_error" -> "ValueError: substring not found"
      [] c = "startswith_tuple" -> "(True, False, True, False)"
      [] c = "startswith_bad" -> "TypeError: startswith first arg must be str or a tuple of str, not list"
      [] c = "startswith_tuple_bad" -> "True"
      [] c = "strip_examples" -> "('spacious', 'example', 'Section 3.2.1 Issue #32')"
      [] c = "lstrip_vs_removeprefix" -> "('ee!', 'three!')"
      [] c = "strip_none" -> "'a'"
      [] c = "strip_bad" -> "TypeError: strip arg must be None or str"
      [] c = "replace_count_keyword" -> "('bba', 'bbb', '-a-bc')"
      [] c = "zfill_examples" -> "('00042', '-0042', '+00', '00')"
      [] c = "center_bad_fill" -> "TypeError: The fill character must be exactly one character long"
      [] c = "ljust_bad_fill" -> "TypeError: The fill character must be a unicode character, not int"
      [] c = "center_index_width" -> "'-a--'"
      [] c = "center_float_width" -> "TypeError: 'float' object cannot be interpreted as an integer"
      [] c = "pad_unicode_fill" -> "'\\xe9a\\xe9\\xe9'"
      [] c = "partition_bad" -> "TypeError: must be str, not NoneType"
      [] c = "str_no_args" -> "''"
      [] c = "str_object" -> "('S!', 'NoStr()', '1.5', 'None')"
      [] c = "str_bad_dunder" -> "TypeError: BadStr.__str__() must return a str, not int"
      [] c = "str_bytes_repr" -> "\"b'Zoot!'\""
      [] c = "str_decode" -> "('caf\\xe9', 'caf\\xe9', 'a', 'ab')"
      [] c = "str_decode_error" -> "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"
      [] c = "str_decode_replace" -> "'a\\ufffdb'"
      [] c = "str_encoding_nonbytes" -> "TypeError: decoding str is not supported"
      [] c = "str_encoding_int" -> "TypeError: decoding to str: need a bytes-like object, int found"
      [] c = "str_subclass_returns" -> "('str', 'str', 'str')"
      [] c = "index_char" -> "(True, 'str', 'c', 1)"
      [] c = "immutable" -> "TypeError: 'str' object does not support item assignment"
      [] c = "concat_literals" -> "True"
      [] c = "triple_quoted" -> "'a\\nb'"
      [] c = "u_prefix" -> "True"
      [] c = "ur_prefix" -> "SyntaxError: 'u' and 'r' prefixes are incompatible"
      [] c = "code_points" -> "(1, 2, [128512, 97])"
      [] c = "method_on_type" -> "('A', 'a-b')"
      [] c = "method_wrong_self" -> "TypeError: descriptor 'upper' for 'str' objects doesn't apply to a 'int' object"
      [] c = "too_many_args" -> "TypeError: str.upper() takes no arguments (1 given)"
      [] c = "keyword_rejected" -> "TypeError: str.find() takes no keyword arguments"
      [] c = "format_map" -> "'Guido was born in country'"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* Splitting and joining with the separator restores the string.
SplitJoins == \A s \in Strs, t \in Subs \ {<<>>} :
    LET parts == Split(s, t)
    IN  Cat(s) = Cat([i \in 1..Len(parts) |-> IF i = 1 THEN Cat(parts[i]) ELSE Cat(t) \o Cat(parts[i])])
=============================================================================
