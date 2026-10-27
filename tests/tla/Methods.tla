------------------------------- MODULE Methods -------------------------------
(***************************************************************************)
(* Instance methods, built-in functions, and built-in methods, as The      *)
(* Python Language Reference specifies them (reference/datamodel.html#     *)
(* instance-methods, #built-in-functions, #built-in-methods): a function   *)
(* got from a class through an instance is bound to it (__self__ the       *)
(* instance, __func__ the function); a classmethod is bound to the class   *)
(* either way; a staticmethod, a function got from the class itself, and a *)
(* function stored on the instance are plain functions. A method's name,  *)
(* qualified name, documentation, and module are its function's, and the   *)
(* function's attributes can be read but not set through it. Calling a     *)
(* bound method inserts __self__ before the arguments. Built-in methods    *)
(* carry the object they belong to as __self__; their documentation is a  *)
(* str, or None if unavailable.                                            *)
(*                                                                         *)
(* A program, in module m, defines                                         *)
(*                                                                         *)
(*     def plain( *args): "plain doc"; return args        (plain.tag = "T") *)
(*     class C:                                                            *)
(*         def f(self, *args): "f doc"; return args      (f.tag = "T")     *)
(*         @classmethod  def cm(cls, *args): return args                   *)
(*         @staticmethod def sm( *args): return args                        *)
(*     c = C(); c.attr = plain                                             *)
(*                                                                         *)
(* and reads one of c.f, C.f, c.cm, C.cm, c.sm, c.attr, [].append, len,    *)
(* [].__len__, then its type, __self__, __func__, __name__, __qualname__,  *)
(* __doc__, __module__, or tag, sets an attribute on it, or calls it with  *)
(* 1 ([1] for len, nothing for __len__).                                   *)
(*                                                                         *)
(* The outcome is what is read or returned, or the exception.              *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Accesses == {"c.f", "C.f", "c.cm", "C.cm", "c.sm", "c.attr", "[].append", "len", "[].__len__"}
Ops == {"type", "__self__", "__func__", "__name__", "__qualname__", "__doc__", "__module__", "tag", "set", "call"}
Programs == [access : Accesses, op : Ops]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* What the access gives, and the object it was found on.
Kind(a) == CASE a = "c.f" -> "bound" [] a \in {"c.cm", "C.cm"} -> "class bound"
             [] a \in {"C.f", "c.sm", "c.attr"} -> "function"
             [] a = "[].append" -> "builtin method" [] a = "len" -> "builtin function" [] a = "[].__len__" -> "wrapper"
\* The underlying function or builtin.
Underlying(a) == CASE a \in {"c.f", "C.f"} -> "f" [] a \in {"c.cm", "C.cm"} -> "cm" [] a = "c.sm" -> "sm"
                   [] a = "c.attr" -> "plain" [] a = "[].append" -> "append" [] a = "len" -> "len" [] a = "[].__len__" -> "__len__"
Qualname(u) == CASE u \in {"f", "cm", "sm"} -> "C." \o u [] u \in {"append", "__len__"} -> "list." \o u [] OTHER -> u
Builtin(a) == Kind(a) \in {"builtin method", "builtin function", "wrapper"}

Run(p) ==
    LET a == p.access  k == Kind(a)  u == Underlying(a)
    IN  CASE p.op = "type" -> CASE k \in {"bound", "class bound"} -> "method" [] k = "function" -> "function"
                                 [] k = "wrapper" -> "method-wrapper" [] OTHER -> "builtin_function_or_method"
          [] p.op = "__self__" -> CASE k = "bound" -> "c" [] k = "class bound" -> "C" [] k = "builtin function" -> "builtins"
                                     [] k \in {"builtin method", "wrapper"} -> "the list" [] OTHER -> "AttributeError"
          [] p.op = "__func__" -> IF k \in {"bound", "class bound"} THEN Qualname(u) ELSE "AttributeError"
          [] p.op = "__name__" -> "'" \o u \o "'"
          [] p.op = "__qualname__" -> "'" \o Qualname(u) \o "'"
          [] p.op = "__doc__" -> CASE u = "f" -> "'f doc'" [] u = "plain" -> "'plain doc'" [] Builtin(a) -> "a str or None"
                                    [] OTHER -> "None"
          [] p.op = "__module__" -> CASE ~Builtin(a) -> "'m'" [] k = "builtin function" -> "'builtins'"
                                       [] k = "builtin method" -> "None" [] OTHER -> "AttributeError"
          \* A function's attributes, read through a method.
          [] p.op = "tag" -> IF u \in {"f", "plain"} THEN "'T'" ELSE "AttributeError"
          [] p.op = "set" -> IF k = "function" THEN "ok" ELSE "AttributeError"
          [] p.op = "call" -> CASE k \in {"bound", "class bound"} -> "(1,)"     \* self or cls comes first
                                 [] a = "C.f" -> "()"                           \* 1 is self
                                 [] k = "function" -> "(1,)"
                                 [] k = "builtin method" -> "None"
                                 [] OTHER -> IF a = "len" THEN "1" ELSE "0"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A method has __self__ exactly when it has __func__ (user-defined).
SelfAndFunc == Done /\ program.op = "__func__" /\ outcome # "AttributeError" =>
    Run([access |-> program.access, op |-> "__self__"]) # "AttributeError"

\* Only plain functions take new attributes.
Settable == Done /\ program.op = "set" /\ outcome = "ok" => Run([access |-> program.access, op |-> "type"]) = "function"
=============================================================================
