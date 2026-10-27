------------------------------- MODULE Bytes --------------------------------
(***************************************************************************)
(* Bytes and bytearray objects, as the Built-in Types chapter specifies    *)
(* them (library/stdtypes.html#bytes-objects, #bytearray-objects, and      *)
(* #bytes-and-bytearray-operations): immutable bytes and mutable bytearray *)
(* sequences of integers in range(256), written as ASCII literals with     *)
(* escapes; constructed from a length, an iterable of ints, a buffer,      *)
(* __bytes__, or a str with an encoding; with fromhex and hex; indexing    *)
(* yields ints and slicing the same type; bytearray adds item and slice    *)
(* assignment and the mutating list methods, refusing to resize while      *)
(* exported; and both offer the str methods over ASCII bytes, accepting    *)
(* any bytes-like argument (and an int for searches), returning results of *)
(* the receiver's type: find, rfind, index, count, startswith, endswith,   *)
(* split, rsplit, partition, rpartition, replace, removeprefix,            *)
(* removesuffix, strip, lstrip, and rstrip behave as for str, and so do    *)
(* center, ljust, rjust, and zfill with a fill byte; case mappings and     *)
(* predicates consider only ASCII letters, and bytes have no titlecase.    *)
(*                                                                         *)
(* A program calls a search, split, replace, affix, or strip method on a   *)
(* bytes or bytearray object holding every string s of up to three         *)
(* characters from a, b, and space, with every bytes argument t of up to   *)
(* two (replace substituting X, with and without a count of 1, and rsplit  *)
(* with a maxsplit of 1), or splits or strips s at whitespace; or pads     *)
(* every such object of up to three characters from a and - to every width *)
(* up to 6 with * (zfill with zeros); or runs one of the sources of CASES  *)
(* in a fresh namespace. The outcome is the repr of the result, or the     *)
(* exception and its message.                                              *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

VARIABLES program, outcome
vars == <<program, outcome>>

Kinds == {"bytes", "bytearray"}
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
\* A result of the receiver's type.
Wrap(text) == IF program.kind = "bytes" THEN "b'" \o text \o "'" ELSE "bytearray(b'" \o text \o "')"
Q(s) == Wrap(Cat(s))
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
          [] p.method = "index" -> IF at = {} THEN "ValueError: subsection not found" ELSE R(Min(at) - 1)
          [] p.method = "count" -> R(IF t = <<>> THEN Len(s) + 1 ELSE Count(s, t))
          [] p.method = "startswith" -> Bool(1 \in at)
          [] p.method = "endswith" -> Bool(Len(s) - Len(t) + 1 \in at)
          [] p.method = "split" -> List(Split(s, t))
          [] p.method = "rsplit1" -> IF at = {} THEN List(<<s>>) ELSE List(<<Before(s, Max(at)), After(s, Max(at), t)>>)
          [] p.method = "partition" -> IF at = {} THEN Triple(s, <<>>, <<>>)
                                       ELSE Triple(Before(s, Min(at)), t, After(s, Min(at), t))
          [] p.method = "rpartition" -> IF at = {} THEN Triple(<<>>, <<>>, s)
                                        ELSE Triple(Before(s, Max(at)), t, After(s, Max(at), t))
          [] p.method = "replace" -> Wrap(IF t = <<>> THEN "X" \o XAfter(s) ELSE Replace(s, t))
          [] p.method = "replace1" -> Wrap(IF at = {} THEN Cat(s)
                                         ELSE Cat(Before(s, Min(at))) \o "X" \o Cat(After(s, Min(at), t)))
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
          [] p.method = "center" -> Wrap(Fill("*", left) \o Cat(s) \o Fill("*", pad - left))
          [] p.method = "ljust" -> Wrap(Cat(s) \o Fill("*", pad))
          [] p.method = "rjust" -> Wrap(Fill("*", pad) \o Cat(s))
          [] s # <<>> /\ Head(s) = "-" -> Wrap("-" \o Fill("0", pad) \o Cat(Tail(s)))
          [] OTHER -> Wrap(Fill("0", pad) \o Cat(s))


Cases == {"literal_forms", "literal_non_ascii", "ctor_forms", "ctor_str_encoding", "ctor_negative",
          "ctor_range_error", "ctor_float", "bytearray_ctor", "fromhex", "fromhex_bad",
          "fromhex_space_middle", "fromhex_non_hex", "hex", "hex_bad_sep", "index_is_int", "iterate_ints",
          "repr_escapes", "immutable", "concat_repeat", "concat_str", "contains", "contains_str", "compare",
          "hash", "hash_bytearray", "count_int", "count_range", "search_str", "case_ascii_only",
          "predicates", "expandtabs", "splitlines", "split_maxsplit", "split_str_sep", "join", "join_str",
          "maketrans_translate", "maketrans_unequal", "translate_bad_table", "zfill", "replace_count",
          "decode", "decode_error", "removeprefix_types", "strip_bytes_arg", "bytearray_mutations",
          "bytearray_methods", "bytearray_inplace", "bytearray_setitem_range", "bytearray_append_bad",
          "bytearray_remove_missing", "bytearray_pop_empty", "bytearray_slice_assign_int",
          "bytearray_slice_assign_str", "bytearray_extended_slice", "bytearray_extended_slice_size",
          "bytearray_resize_exported", "bytearray_methods_return_new", "bytes_methods_on_bytearray_args",
          "isascii_empty", "len_and_bool"}
Programs == [kind : Kinds, method : Search, s : Strs, t : Subs]
            \cup [kind : Kinds, method : Whole, s : Strs]
            \cup [kind : Kinds, method : Pad, s : PadStrs, width : 0..6]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    CASE p.method \in Search -> Searched(p)
      [] p.method = "split_ws" -> List(Words(p.s))
      [] p.method = "rsplit_ws1" -> List(RSplitWords(p.s))
      [] p.method = "strip_ws" -> Q(RStrip(LStrip(p.s, {" "}), {" "}))
      [] OTHER -> Padded(p)

Case(c) ==
    CASE c = "literal_forms" -> "(b'still allows embedded \"double\" quotes', b\"a'b\", b'3', b'\\\\d', 1)"
      [] c = "literal_non_ascii" -> "SyntaxError: bytes can only contain ASCII literal characters"
      [] c = "ctor_forms" -> "(b'', b'\\x00\\x00\\x00', b'\\x00\\x01\\x02', b'ab', b'c', b'm', b'dunder', b'\\x00\\x00\\x00')"
      [] c = "ctor_str_encoding" -> "(b'\\xc3\\xa9', b'\\xe9', b'a')"
      [] c = "ctor_negative" -> "ValueError: negative count"
      [] c = "ctor_range_error" -> "ValueError: bytes must be in range(0, 256)"
      [] c = "ctor_float" -> "TypeError: cannot convert 'float' object to bytes"
      [] c = "bytearray_ctor" -> "(bytearray(b''), bytearray(b'\\x00\\x00'), bytearray(b'ab'), bytearray(b'\\xc3\\xa9'), bytearray(b'\\x00\\x01'))"
      [] c = "fromhex" -> "(b'.\\xf0\\xf1\\xf2', bytearray(b'.\\xf0'), b'', b'\\x00')"
      [] c = "fromhex_bad" -> "ValueError: fromhex() arg must contain an even number of hexadecimal digits"
      [] c = "fromhex_space_middle" -> "ValueError: non-hexadecimal number found in fromhex() arg at position 1"
      [] c = "fromhex_non_hex" -> "ValueError: non-hexadecimal number found in fromhex() arg at position 0"
      [] c = "hex" -> "('f0f1f2', 'f0-f1-f2', '5555 44444c52 4c524142', '55554444:4c524c52:4142', '01')"
      [] c = "hex_bad_sep" -> "ValueError: sep must be length 1."
      [] c = "index_is_int" -> "(97, b'a', 99, 'int')"
      [] c = "iterate_ints" -> "[97, 98]"
      [] c = "repr_escapes" -> "(b\"\\x00\\t\\n\\r\\\\'\\x7f\\x80\", bytearray(b'\"'))"
      [] c = "immutable" -> "TypeError: 'bytes' object does not support item assignment"
      [] c = "concat_repeat" -> "(b'abcd', b'abc', bytearray(b'ab'), b'abab', bytearray(b'xx'))"
      [] c = "concat_str" -> "TypeError: can't concat str to bytes"
      [] c = "contains" -> "ValueError: byte must be in range(0, 256)"
      [] c = "contains_str" -> "TypeError: a bytes-like object is required, not 'str'"
      [] c = "compare" -> "(True, True, False, True)"
      [] c = "hash" -> "True"
      [] c = "hash_bytearray" -> "TypeError: unhashable type: 'bytearray'"
      [] c = "count_int" -> "(2, 2, 2, 1)"
      [] c = "count_range" -> "ValueError: byte must be in range(0, 256)"
      [] c = "search_str" -> "TypeError: argument should be integer or bytes-like object, not 'str'"
      [] c = "case_ascii_only" -> "(b'AB\\xe9', b'ab\\xc9', b'Hello World', b'Ab', b'Hello')"
      [] c = "predicates" -> "(True, True, False, True, True, True, True, True, True, False)"
      [] c = "expandtabs" -> "(b'01      012     0123    01234', b'a   b')"
      [] c = "splitlines" -> "([b'ab c', b'', b'de fg', b'kl'], [b'a\\n', b'b'], [b'a\\x0bb'])"
      [] c = "split_maxsplit" -> "([b'1', b'2,3'], [b'1', b'2'], [b'a', b'b'])"
      [] c = "split_str_sep" -> "TypeError: a bytes-like object is required, not 'str'"
      [] c = "join" -> "(b'a-b-c', bytearray(b'x,y'))"
      [] c = "join_str" -> "TypeError: sequence item 0: expected a bytes-like object, str found"
      [] c = "maketrans_translate" -> "(256, b'xxyyzz', b'rd ths shrt txt')"
      [] c = "maketrans_unequal" -> "ValueError: maketrans arguments must have same length"
      [] c = "translate_bad_table" -> "ValueError: translation table must be 256 characters long"
      [] c = "zfill" -> "(b'00042', b'-0042', bytearray(b'+001'))"
      [] c = "replace_count" -> "(b'bba', b'-a-b-c-')"
      [] c = "decode" -> "('caf\\xe9', '\\xe9', '\\ufffd', '')"
      [] c = "decode_error" -> "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"
      [] c = "removeprefix_types" -> "(b'bc', bytearray(b'ab'))"
      [] c = "strip_bytes_arg" -> "(b'a', b'a', bytearray(b'b'))"
      [] c = "bytearray_mutations" -> "(bytearray(b'xYYc!'), 63)"
      [] c = "bytearray_methods" -> "(bytearray(b''), bytearray(b'cba'), True)"
      [] c = "bytearray_inplace" -> "(bytearray(b'abcabc'), True)"
      [] c = "bytearray_setitem_range" -> "ValueError: byte must be in range(0, 256)"
      [] c = "bytearray_append_bad" -> "TypeError: 'bytes' object cannot be interpreted as an integer"
      [] c = "bytearray_remove_missing" -> "ValueError: value not found in bytearray"
      [] c = "bytearray_pop_empty" -> "IndexError: pop from empty bytearray"
      [] c = "bytearray_slice_assign_int" -> "TypeError: can assign only bytes, buffers, or iterables of ints in range(0, 256)"
      [] c = "bytearray_slice_assign_str" -> "TypeError: can assign only bytes, buffers, or iterables of ints in range(0, 256)"
      [] c = "bytearray_extended_slice" -> "bytearray(b'XbYdZf')"
      [] c = "bytearray_extended_slice_size" -> "ValueError: attempt to assign bytes of size 2 to extended slice of size 3"
      [] c = "bytearray_resize_exported" -> "BufferError: Existing exports of data: object cannot be re-sized"
      [] c = "bytearray_methods_return_new" -> "(False, 'bytearray', 'bytearray')"
      [] c = "bytes_methods_on_bytearray_args" -> "True"
      [] c = "isascii_empty" -> "(True, False)"
      [] c = "len_and_bool" -> "(0, False, True)"

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
