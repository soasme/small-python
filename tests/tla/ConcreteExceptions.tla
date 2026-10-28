------------------------- MODULE ConcreteExceptions -------------------------
(***************************************************************************)
(* The concrete exceptions, as The Python Standard Library specifies them  *)
(* (library/exceptions.html#concrete-exceptions): AttributeError's name    *)
(* and obj and NameError's name (also as keywords), UnboundLocalError      *)
(* under NameError, ImportError's name, path, and name_from,               *)
(* ModuleNotFoundError, IndexError and KeyError, OSError's errno,          *)
(* strerror, filename, and filename2 with its str() and the subclass       *)
(* chosen by errno, StopIteration and StopAsyncIteration turned into       *)
(* RuntimeError when they escape a generator or async generator,           *)
(* SyntaxError's location attributes and str(), IndentationError and       *)
(* TabError, UnicodeDecodeError, UnicodeEncodeError, and                   *)
(* UnicodeTranslateError with encoding, object, start, end, and reason,    *)
(* whose str() names one byte or character when end is start + 1 within    *)
(* the object and a position range otherwise, and the remaining classes'   *)
(* arguments.                                                              *)
(*                                                                         *)
(* A program builds UnicodeDecodeError('utf-8', b'\x80\xffA', start, end,  *)
(* 'r'), UnicodeEncodeError('ascii', '\xe9\u03b1\U0001f600A', start, end,  *)
(* 'r'), or UnicodeTranslateError over that text, for start and end from   *)
(* -1 to 5, and reports ascii() of its str(); or runs one of the sources   *)
(* of CASES in a fresh namespace. The outcome is that text, or the repr of *)
(* the case's result, or the exception and its message.                    *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

VARIABLES program, outcome
vars == <<program, outcome>>

Bytes == <<128, 255, 65>>
Points == <<233, 945, 128512, 65>>
R(n) == ToString(n)
Hex == "0123456789abcdef"
RECURSIVE Digits(_, _)
Digits(n, width) == IF width = 0 THEN "" ELSE Digits(n \div 16, width - 1) \o SubSeq(Hex, (n % 16) + 1, (n % 16) + 1)
\* A character as its str() message shows it, with ascii()'s doubled backslash.
Escaped(cp) == IF cp < 256 THEN "\\\\x" \o Digits(cp, 2)
               ELSE IF cp < 65536 THEN "\\\\u" \o Digits(cp, 4) ELSE "\\\\U" \o Digits(cp, 8)

\* One item when end = start + 1 inside the object, else a range.
Single(s, e, n) == s >= 0 /\ s < n /\ e = s + 1
Range(s, e) == "in position " \o R(s) \o "-" \o R(e - 1) \o ": r"


Cases == {"attributeerror_attrs", "attributeerror_kw", "attributeerror_bad_kw", "nameerror_name",
          "nameerror_suggestion_attr", "unboundlocal", "importerror_attrs", "importerror_bad_kw",
          "importerror_from", "modulenotfound", "indexerror", "keyerror_missing", "oserror_args",
          "oserror_two_files", "oserror_single_arg", "stopiteration_in_gen", "stopasync_in_agen",
          "syntaxerror_attrs", "syntaxerror_build", "syntaxerror_str_no_file", "indentation_tab",
          "unicode_decode", "unicode_encode", "unicode_build_bad", "unicode_translate", "zero_division",
          "overflow_float", "recursion", "notimplemented_error", "assertion_msg", "systemexit_attrs",
          "generator_exit_close", "eoferror_type", "memoryerror_type", "typeerror_args", "buffererror",
          "finalization_error", "import_cycle_error"}
Programs == [kind : {"decode", "encode", "translate"}, start : -1..5, end : -1..5]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    LET s == p.start  e == p.end IN
    "\"" \o
    (CASE p.kind = "decode" ->
            "'utf-8' codec can't decode " \o (IF Single(s, e, 3) THEN "byte 0x" \o Digits(Bytes[s + 1], 2) \o " in position " \o R(s) \o ": r"
                                                ELSE "bytes " \o Range(s, e))
       [] p.kind = "encode" ->
            "'ascii' codec can't encode " \o (IF Single(s, e, 4) THEN "character '" \o Escaped(Points[s + 1]) \o "' in position " \o R(s) \o ": r"
                                               ELSE "characters " \o Range(s, e))
       [] p.kind = "translate" ->
            "can't translate " \o (IF Single(s, e, 4) THEN "character '" \o Escaped(Points[s + 1]) \o "' in position " \o R(s) \o ": r"
                                    ELSE "characters " \o Range(s, e)))
    \o "\""

Case(c) ==
    CASE c = "attributeerror_attrs" -> "('missing', 'Obj', \"'Obj' object has no attribute 'missing'\")"
      [] c = "attributeerror_kw" -> "('n', 1, ('m',))"
      [] c = "attributeerror_bad_kw" -> "TypeError: AttributeError() got an unexpected keyword argument 'x'"
      [] c = "nameerror_name" -> "('undefined_name', \"name 'undefined_name' is not defined\")"
      [] c = "nameerror_suggestion_attr" -> "'q'"
      [] c = "unboundlocal" -> "('NameError', None, \"cannot access local variable 'v' where it is not associated with a value\")"
      [] c = "importerror_attrs" -> "('n', 'p', 'msg', 'msg', None)"
      [] c = "importerror_bad_kw" -> "TypeError: ImportError() got an unexpected keyword argument 'x'"
      [] c = "importerror_from" -> "('builtins', 'nosuchname', 'ImportError')"
      [] c = "modulenotfound" -> "('nosuchmod_q', None, \"No module named 'nosuchmod_q'\")"
      [] c = "indexerror" -> "'list index out of range'"
      [] c = "keyerror_missing" -> "(((),), '()')"
      [] c = "oserror_args" -> "('FileNotFoundError', 2, 'No such file', 'f.txt', \"[Errno 2] No such file: 'f.txt'\")"
      [] c = "oserror_two_files" -> "('a', 'b', \"[Errno 1] x: 'a' -> 'b'\")"
      [] c = "oserror_single_arg" -> "(None, None, ('just',), 'just')"
      [] c = "stopiteration_in_gen" -> "('generator raised StopIteration', 'StopIteration')"
      [] c = "stopasync_in_agen" -> "'async generator raised StopAsyncIteration'"
      [] c = "syntaxerror_attrs" -> "('f.py', 1, 'a +\\n', 'invalid syntax')"
      [] c = "syntaxerror_build" -> "('m', 'f', 1, 2, 'txt', 1, 3, 'm (f, line 1)')"
      [] c = "syntaxerror_str_no_file" -> "'m (line 1)'"
      [] c = "indentation_tab" -> "(True, True)"
      [] c = "unicode_decode" -> "('utf-8', b'\\xff', 0, 1, 'invalid start byte', \"'utf-8' codec can't decode byte 0xff in position 0: invalid start byte\")"
      [] c = "unicode_encode" -> "('ascii', '\\xe9', 0, 1, 'ordinal not in range(128)', \"'ascii' codec can't encode character '\\\\xe9' in position 0: ordinal not in range(128)\")"
      [] c = "unicode_build_bad" -> "TypeError: a bytes-like object is required, not 'str'"
      [] c = "unicode_translate" -> "(None, \"can't translate character '\\\\xe9' in position 0: bad\")"
      [] c = "zero_division" -> "'division by zero'"
      [] c = "overflow_float" -> "(34, 'Result too large')"
      [] c = "recursion" -> "True"
      [] c = "notimplemented_error" -> "True"
      [] c = "assertion_msg" -> "(('m', 1),)"
      [] c = "systemexit_attrs" -> "('bye', 'bye')"
      [] c = "generator_exit_close" -> "['GeneratorExit']"
      [] c = "eoferror_type" -> "True"
      [] c = "memoryerror_type" -> "(True, ())"
      [] c = "typeerror_args" -> "('a', 'b')"
      [] c = "buffererror" -> "'Existing exports of data: object cannot be re-sized'"
      [] c = "finalization_error" -> "True"
      [] c = "import_cycle_error" -> "True"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* A single item is named only when it exists.
SingleInRange == Done /\ "kind" \in DOMAIN program /\ Single(program.start, program.end, 3) =>
    program.start \in 0..2
=============================================================================
