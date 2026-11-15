------------------------------- MODULE Raise -------------------------------
(***************************************************************************)
(* The raise statement and exception chaining, as The Python Language      *)
(* Reference specifies them                                                *)
(* (reference/simple_stmts.html#the-raise-statement,                       *)
(* reference/executionmodel.html#exceptions, and                           *)
(* library/exceptions.html#exception-context): `raise E` raises E,         *)
(* instantiating it first if it is a class; anything that is not an        *)
(* exception (class or instance) raises TypeError instead; `from C` sets   *)
(* __cause__ (C instantiated if a class; None clears it) and               *)
(* __suppress_context__, and a cause that is not an exception or None      *)
(* raises TypeError; an exception raised while another is being handled,   *)
(* by a raise statement or by an operation that fails, gets it as          *)
(* __context__; and a bare raise re-raises the exception being handled, or *)
(* raises RuntimeError when there is none.                                 *)
(*                                                                         *)
(* A program runs `raise WHAT from CAUSE`, either alone or inside the      *)
(* handler of `try: raise KeyError / except KeyError:`, where WHAT is      *)
(* ValueError, ValueError(), 5, a class that is not an exception, a       *)
(* ValueError subclass whose Python __init__ logs "e", one whose __init__  *)
(* returns 1, one whose Python __new__ logs "n" before its __init__ logs   *)
(* "i", one whose __new__ logs "n" and returns 5, one whose __new__ logs  *)
(* "r" and returns a KeyError unless it is given one, so the raise calls   *)
(* the class again with that KeyError, after the cause, the cause staying  *)
(* on the KeyError, one like it whose Python __init__ logs "j" in that    *)
(* second call, a ValueError subclass whose metaclass's Python __call__   *)
(* logs "k" and makes it, with no __init__ after it, or one whose          *)
(* __call__ logs "s" and returns a KeyError unless given one, as "r" does, *)
(* or nothing (a bare raise, which takes no cause), or runs                *)
(* 1 / 0 instead; and CAUSE is                                             *)
(* absent, TypeError, TypeError(), None, 5, a TypeError subclass whose     *)
(* Python __init__ logs "c", one whose Python __new__ logs "m" and         *)
(* returns a KeyError, the cause without its class's __init__, or one     *)
(* whose metaclass's Python __call__ logs "q" and makes it. The           *)
(* outcome is the type of the exception raised, of its __cause__ and       *)
(* __context__, its __suppress_context__, and the log: the exception is    *)
(* made before the cause.                                                  *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Whats == {"class", "instance", "int", "other", "bare", "divide", "python", "returns", "new", "new_int", "renew", "reinit",
          "meta", "meta_swap"}
Causes == {"absent", "class", "instance", "None", "int", "python", "new_other", "meta"}
Programs == {p \in [what : Whats, cause : Causes, handling : BOOLEAN] : p.what \in {"bare", "divide"} => p.cause = "absent"}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Context(p) == IF p.handling THEN "KeyError" ELSE "None"

Show(kind, cause, context, suppress) == kind \o " cause=" \o cause \o " context=" \o context \o " suppress=" \o suppress

\* The Python __new__ and __init__ calls, the exception's and then a valid cause's.
\* A renew's class is called again once the cause is made.
CauseLog(p) == CASE p.cause = "python" -> "c" [] p.cause = "new_other" -> "m" [] p.cause = "meta" -> "q" [] OTHER -> ""
Inits(p) == (CASE p.what = "python" -> "e" [] p.what = "new" -> "ni" [] p.what = "new_int" -> "n"
                [] p.what \in {"renew", "reinit"} -> "r" [] p.what = "meta" -> "k" [] p.what = "meta_swap" -> "s"
                [] OTHER -> "") \o
            (IF p.what \in {"class", "instance", "python", "new", "renew", "reinit", "meta", "meta_swap"} THEN CauseLog(p) ELSE "") \o
            (IF p.what = "renew" /\ p.cause # "int" THEN "r" ELSE "") \o
            (IF p.what = "meta_swap" /\ p.cause # "int" THEN "s" ELSE "") \o
            (IF p.what = "reinit" /\ p.cause # "int" THEN "rj" ELSE "")

Kind(p) == CASE p.what = "python" -> "PyError" [] p.what = "new" -> "PyNew" [] p.what = "renew" -> "Renew"
             [] p.what = "meta" -> "PyMeta" [] OTHER -> "ValueError"

Raised(p) ==
    CASE p.what = "bare" /\ p.handling -> Show("KeyError", "None", "None", "False")     \* the same exception again
      [] p.what = "bare" -> Show("RuntimeError", "None", "None", "False")
      [] p.what = "divide" -> Show("ZeroDivisionError", "None", Context(p), "False")
      [] p.what \in {"int", "other", "returns", "new_int"} -> Show("TypeError", "None", Context(p), "False")
      [] p.cause = "int" -> Show("TypeError", "None", Context(p), "False")
      [] p.what = "renew" -> Show("Renew", "None", Context(p), "False")
      [] p.what = "reinit" -> Show("Reinit", "None", Context(p), "False")
      [] p.what = "meta_swap" -> Show("MetaSwap", "None", Context(p), "False")
      [] p.cause = "absent" -> Show(Kind(p), "None", Context(p), "False")
      [] p.cause = "None" -> Show(Kind(p), "None", Context(p), "True")
      [] p.cause = "python" -> Show(Kind(p), "PyCause", Context(p), "True")
      [] p.cause = "new_other" -> Show(Kind(p), "KeyError", Context(p), "True")      \* the other exception __new__ made
      [] p.cause = "meta" -> Show(Kind(p), "MetaCause", Context(p), "True")
      [] OTHER -> Show(Kind(p), "TypeError", Context(p), "True")

Run(p) == Raised(p) \o " log=" \o Inits(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A cause, or `from None`, always suppresses the context in tracebacks.
FromSuppresses == Done /\ program.what \in {"class", "instance"} /\ program.cause \in {"class", "instance", "None"} =>
    outcome = Run(program) /\ \E k \in {"ValueError"} : outcome = Show(k, IF program.cause = "None" THEN "None" ELSE "TypeError",
                                                            Context(program), "True") \o " log="
=============================================================================
