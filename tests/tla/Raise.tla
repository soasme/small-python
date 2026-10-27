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
(* ValueError, ValueError(), 5, a class that is not an exception, or       *)
(* nothing (a bare raise, which takes no cause), or runs 1 / 0 instead;    *)
(* and CAUSE is absent, TypeError, TypeError(), None, or 5. The outcome is *)
(* the type of the exception raised, of its __cause__ and __context__, and *)
(* its __suppress_context__.                                               *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Whats == {"class", "instance", "int", "other", "bare", "divide"}
Causes == {"absent", "class", "instance", "None", "int"}
Programs == {p \in [what : Whats, cause : Causes, handling : BOOLEAN] : p.what \in {"bare", "divide"} => p.cause = "absent"}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Context(p) == IF p.handling THEN "KeyError" ELSE "None"

Show(kind, cause, context, suppress) == kind \o " cause=" \o cause \o " context=" \o context \o " suppress=" \o suppress

Run(p) ==
    CASE p.what = "bare" /\ p.handling -> Show("KeyError", "None", "None", "False")     \* the same exception again
      [] p.what = "bare" -> Show("RuntimeError", "None", "None", "False")
      [] p.what = "divide" -> Show("ZeroDivisionError", "None", Context(p), "False")
      [] p.what \in {"int", "other"} -> Show("TypeError", "None", Context(p), "False")
      [] p.cause = "int" -> Show("TypeError", "None", Context(p), "False")
      [] p.cause = "absent" -> Show("ValueError", "None", Context(p), "False")
      [] p.cause = "None" -> Show("ValueError", "None", Context(p), "True")
      [] OTHER -> Show("ValueError", "TypeError", Context(p), "True")

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A cause, or `from None`, always suppresses the context in tracebacks.
FromSuppresses == Done /\ program.what \in {"class", "instance"} /\ program.cause \in {"class", "instance", "None"} =>
    outcome = Run(program) /\ \E k \in {"ValueError"} : outcome = Show(k, IF program.cause = "None" THEN "None" ELSE "TypeError",
                                                            Context(program), "True")
=============================================================================
