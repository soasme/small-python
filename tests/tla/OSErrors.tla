------------------------------ MODULE OSErrors ------------------------------
(***************************************************************************)
(* The OS exceptions, as The Python Standard Library specifies them        *)
(* (library/exceptions.html#os-exceptions, with OSError under #concrete-   *)
(* exceptions): OSError called with two to five arguments takes them as    *)
(* errno, strerror, filename, winerror (ignored off Windows), and          *)
(* filename2, keeps only the first two in args, and becomes the subclass   *)
(* for its errno (EPERM and EACCES PermissionError, ENOENT                 *)
(* FileNotFoundError, ESRCH ProcessLookupError, EINTR InterruptedError,    *)
(* ECHILD ChildProcessError, EEXIST FileExistsError, ENOTDIR               *)
(* NotADirectoryError, EISDIR IsADirectoryError, EPIPE BrokenPipeError,    *)
(* and the others listed), which neither a subclass call nor a user        *)
(* subclass does; str() is [Errno e] strerror with the filenames' reprs    *)
(* when a filename was set and otherwise str() of args; BlockingIOError's  *)
(* characters_written exists only when given; and the ConnectionError      *)
(* family and TimeoutError sit under OSError.                              *)
(*                                                                         *)
(* A program calls OSError, FileNotFoundError, or a user subclass          *)
(* MyOSError with the first one to five of errno, 'm', 'f', None, and 'g', *)
(* for errno among 1, 2, 3, 4, 5, 10, 13, 17, 20, 21, 22, and 32 (the      *)
(* numbers Linux and macOS share), and reports the class name, errno,      *)
(* strerror, filename, filename2, and str() of the result; or runs one of  *)
(* the sources of CASES in a fresh namespace. The outcome is the repr of   *)
(* that tuple or of the case's result, or the exception and its message.   *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

VARIABLES program, outcome
vars == <<program, outcome>>

\* The errno values both platforms give these classes; 5 and 22 map to none.
Mapped == [n \in {1, 2, 3, 4, 10, 13, 17, 20, 21, 32} |->
             CASE n \in {1, 13} -> "PermissionError"
               [] n = 2 -> "FileNotFoundError"
               [] n = 3 -> "ProcessLookupError"
               [] n = 4 -> "InterruptedError"
               [] n = 10 -> "ChildProcessError"
               [] n = 17 -> "FileExistsError"
               [] n = 20 -> "NotADirectoryError"
               [] n = 21 -> "IsADirectoryError"
               [] n = 32 -> "BrokenPipeError"]
R(n) == ToString(n)
\* Only OSError itself picks a subclass, and only from two to five arguments.
Class(p) == IF p.cls = "OSError" /\ p.arity >= 2 /\ p.errno \in DOMAIN Mapped THEN Mapped[p.errno] ELSE p.cls
Text(p) == "[Errno " \o R(p.errno) \o "] m" \o (IF p.arity >= 3 THEN ": 'f'" ELSE "")
           \o (IF p.arity = 5 THEN " -> 'g'" ELSE "")


Cases == {"six_args", "none_errno", "str_errno", "args_kept", "blocking_written", "blocking_unset", "blocking_delete",
          "attrs_writable", "connection_family", "timeout_alias", "kwargs_refused",
          "subclass_init_override", "subclass_new_override", "reduce", "filename_repr", "filename_int",
          "empty"}
Programs == [cls : {"OSError", "FileNotFoundError", "MyOSError"}, errno : DOMAIN Mapped \cup {5, 22}, arity : 1..5]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    "('" \o Class(p) \o "', "
    \o (IF p.arity = 1 THEN "None, None, None, None, '" \o R(p.errno) \o "'"
        ELSE R(p.errno) \o ", 'm', " \o (IF p.arity >= 3 THEN "'f'" ELSE "None") \o ", "
             \o (IF p.arity = 5 THEN "'g'" ELSE "None") \o ", "
             \* The repr of a str holding ' is in double quotes.
             \o (IF p.arity >= 3 THEN "\"" \o Text(p) \o "\"" ELSE "'" \o Text(p) \o "'"))
    \o ")"

Case(c) ==
    CASE c = "six_args" -> "('OSError', None, (2, 'm', 'f', None, 'g', 'h'), \"(2, 'm', 'f', None, 'g', 'h')\")"
      [] c = "none_errno" -> "('OSError', None, '[Errno None] m')"
      [] c = "str_errno" -> "('OSError', '2', '[Errno 2] m')"
      [] c = "args_kept" -> "(2, 'm')"
      [] c = "blocking_written" -> "(3, None)"
      [] c = "blocking_unset" -> "AttributeError: characters_written"
      [] c = "blocking_delete" -> "False"
      [] c = "attrs_writable" -> "(\"[Errno 7] s: 'q'\", (1, 'm'))"
      [] c = "connection_family" -> "['BrokenPipeError', 'ConnectionAbortedError', 'ConnectionRefusedError', 'ConnectionResetError']"
      [] c = "timeout_alias" -> "'OSError'"
      [] c = "kwargs_refused" -> "TypeError: OSError() takes no keyword arguments"
      [] c = "subclass_init_override" -> "('E', 2)"
      [] c = "subclass_new_override" -> "'E'"
      [] c = "reduce" -> "('FileNotFoundError', (2, 'm', 'f'))"
      [] c = "filename_repr" -> "\"[Errno 1] m: b'bytes\\\\xff'\""
      [] c = "filename_int" -> "'[Errno 1] m: 3'"
      [] c = "empty" -> "(None, '', ())"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* A call on a subclass always yields that subclass.
SubclassKept == Done /\ "cls" \in DOMAIN program /\ program.cls # "OSError" => Class(program) = program.cls
=============================================================================
