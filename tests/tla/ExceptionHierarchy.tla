------------------------- MODULE ExceptionHierarchy -------------------------
(***************************************************************************)
(* The built-in exception hierarchy, as The Python Standard Library        *)
(* specifies it (library/exceptions.html#exception-hierarchy, with #base-  *)
(* classes and #warnings): every built-in exception class derives from     *)
(* BaseException, all but SystemExit, KeyboardInterrupt, GeneratorExit,    *)
(* and BaseExceptionGroup through Exception; the documented intermediate   *)
(* bases (ArithmeticError, LookupError, OSError and ConnectionError,       *)
(* RuntimeError, SyntaxError and IndentationError, NameError, ImportError, *)
(* ValueError and UnicodeError, and Warning for every warning category)    *)
(* order each class's MRO; ExceptionGroup derives from both                *)
(* BaseExceptionGroup and Exception; EnvironmentError and IOError are      *)
(* aliases of OSError; every class lives in builtins; and an except clause *)
(* catches the subclasses of the classes it names.                         *)
(*                                                                         *)
(* A program looks up each built-in exception name and reports the names   *)
(* along its __mro__ and its __module__; or runs one of the sources of     *)
(* CASES in a fresh namespace. The outcome is the repr of that pair or of  *)
(* the case's result, or the exception and its message.                    *)
(***************************************************************************)
EXTENDS Integers, Sequences

VARIABLES program, outcome
vars == <<program, outcome>>

Names == {"ArithmeticError", "AssertionError", "AttributeError", "BaseException", "BaseExceptionGroup",
          "BlockingIOError", "BrokenPipeError", "BufferError", "BytesWarning", "ChildProcessError",
          "ConnectionAbortedError", "ConnectionError", "ConnectionRefusedError", "ConnectionResetError",
          "DeprecationWarning", "EOFError", "EncodingWarning", "EnvironmentError", "Exception", "ExceptionGroup",
          "FileExistsError", "FileNotFoundError", "FloatingPointError", "FutureWarning", "GeneratorExit",
          "IOError", "ImportCycleError", "ImportError", "ImportWarning", "IndentationError", "IndexError",
          "InterruptedError", "IsADirectoryError", "KeyError", "KeyboardInterrupt", "LookupError", "MemoryError",
          "ModuleNotFoundError", "NameError", "NotADirectoryError", "NotImplementedError", "OSError",
          "OverflowError", "PendingDeprecationWarning", "PermissionError", "ProcessLookupError",
          "PythonFinalizationError", "RecursionError", "ReferenceError", "ResourceWarning", "RuntimeError",
          "RuntimeWarning", "StopAsyncIteration", "StopIteration", "SyntaxError", "SyntaxWarning", "SystemError",
          "SystemExit", "TabError", "TimeoutError", "TypeError", "UnboundLocalError", "UnicodeDecodeError",
          "UnicodeEncodeError", "UnicodeError", "UnicodeTranslateError", "UnicodeWarning", "UserWarning",
          "ValueError", "Warning", "ZeroDivisionError"}
Parent == [ArithmeticError |-> "Exception", AssertionError |-> "Exception", AttributeError |-> "Exception",
           BaseExceptionGroup |-> "BaseException", BlockingIOError |-> "OSError",
           BrokenPipeError |-> "ConnectionError", BufferError |-> "Exception", BytesWarning |-> "Warning",
           ChildProcessError |-> "OSError", ConnectionAbortedError |-> "ConnectionError",
           ConnectionError |-> "OSError", ConnectionRefusedError |-> "ConnectionError",
           ConnectionResetError |-> "ConnectionError", DeprecationWarning |-> "Warning", EOFError |-> "Exception",
           EncodingWarning |-> "Warning", Exception |-> "BaseException", FileExistsError |-> "OSError",
           FileNotFoundError |-> "OSError", FloatingPointError |-> "ArithmeticError", FutureWarning |-> "Warning",
           GeneratorExit |-> "BaseException", ImportCycleError |-> "ImportError", ImportError |-> "Exception",
           ImportWarning |-> "Warning", IndentationError |-> "SyntaxError", IndexError |-> "LookupError",
           InterruptedError |-> "OSError", IsADirectoryError |-> "OSError", KeyError |-> "LookupError",
           KeyboardInterrupt |-> "BaseException", LookupError |-> "Exception", MemoryError |-> "Exception",
           ModuleNotFoundError |-> "ImportError", NameError |-> "Exception", NotADirectoryError |-> "OSError",
           NotImplementedError |-> "RuntimeError", OSError |-> "Exception", OverflowError |-> "ArithmeticError",
           PendingDeprecationWarning |-> "Warning", PermissionError |-> "OSError",
           ProcessLookupError |-> "OSError", PythonFinalizationError |-> "RuntimeError",
           RecursionError |-> "RuntimeError", ReferenceError |-> "Exception", ResourceWarning |-> "Warning",
           RuntimeError |-> "Exception", RuntimeWarning |-> "Warning", StopAsyncIteration |-> "Exception",
           StopIteration |-> "Exception", SyntaxError |-> "Exception", SyntaxWarning |-> "Warning",
           SystemError |-> "Exception", SystemExit |-> "BaseException", TabError |-> "IndentationError",
           TimeoutError |-> "OSError", TypeError |-> "Exception", UnboundLocalError |-> "NameError",
           UnicodeDecodeError |-> "UnicodeError", UnicodeEncodeError |-> "UnicodeError",
           UnicodeError |-> "ValueError", UnicodeTranslateError |-> "UnicodeError", UnicodeWarning |-> "Warning",
           UserWarning |-> "Warning", ValueError |-> "Exception", Warning |-> "Exception",
           ZeroDivisionError |-> "ArithmeticError"]
Alias == [EnvironmentError |-> "OSError", IOError |-> "OSError"]
Class(n) == IF n \in DOMAIN Alias THEN Alias[n] ELSE n

RECURSIVE Mro(_)
\* The C3 linearization of ExceptionGroup(BaseExceptionGroup, Exception).
Mro(n) == CASE n = "BaseException" -> <<"BaseException", "object">>
            [] n = "ExceptionGroup" -> <<"ExceptionGroup", "BaseExceptionGroup", "Exception", "BaseException", "object">>
            [] OTHER -> <<n>> \o Mro(Parent[n])

RECURSIVE Join(_)
Join(s) == IF s = <<>> THEN "" ELSE IF Len(s) = 1 THEN Head(s) ELSE Head(s) \o ", " \o Join(Tail(s))
Quoted(s) == [i \in DOMAIN s |-> "'" \o s[i] \o "'"]


Cases == {"exception_misses_base", "aliases", "warning_raisable", "group_bases", "subclass_catch",
          "not_subclass_catch", "bool_base_flags", "multiple_inheritance_ok", "layout_conflict",
          "raise_non_exception", "raise_class_instantiates", "raise_class_bad_init"}
Programs == [name : Names]
            \cup [case : Cases]

Pending == "pending"

Generated(p) == "([" \o Join(Quoted(Mro(Class(p.name)))) \o "], 'builtins')"

Case(c) ==
    CASE c = "exception_misses_base" -> "('escaped', 'SystemExit', 3)"
      [] c = "aliases" -> "(True, True)"
      [] c = "warning_raisable" -> "('DeprecationWarning', ('old',))"
      [] c = "group_bases" -> "((<class 'BaseExceptionGroup'>, <class 'Exception'>), (<class 'BaseException'>,))"
      [] c = "subclass_catch" -> "'KeyError'"
      [] c = "not_subclass_catch" -> "'ZeroDivisionError'"
      [] c = "bool_base_flags" -> "['SystemExit', 'KeyboardInterrupt', 'GeneratorExit', 'BaseExceptionGroup']"
      [] c = "multiple_inheritance_ok" -> "['E', 'ValueError', 'KeyError', 'LookupError', 'Exception', 'BaseException', 'object']"
      [] c = "layout_conflict" -> "None"
      [] c = "raise_non_exception" -> "TypeError: exceptions must derive from BaseException"
      [] c = "raise_class_instantiates" -> "('KeyError', ())"
      [] c = "raise_class_bad_init" -> "TypeError: E.__init__() missing 1 required positional argument: 'x'"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* Every class derives from BaseException, and from Exception unless it is
\* one of the four that must escape `except Exception`.
Rooted == Done /\ "name" \in DOMAIN program =>
    LET m == Mro(Class(program.name))  has(k) == \E i \in DOMAIN m : m[i] = k IN
    /\ m[Len(m)] = "object" /\ m[Len(m) - 1] = "BaseException"
    /\ has("Exception") <=> Class(program.name) \notin
           {"BaseException", "SystemExit", "KeyboardInterrupt", "GeneratorExit", "BaseExceptionGroup"}
=============================================================================
