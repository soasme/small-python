---------------------------- MODULE AsyncLookup ----------------------------
(***************************************************************************)
(* The lookup of __aiter__, __anext__ and __await__, as PLS-315 7.3.2,     *)
(* 7.7.4, 7.7.5, 19.3.2 and 19.3.4 specify it: each is looked up on the    *)
(* object's type (LookupSpecial), and an AttributeError a descriptor's     *)
(* read raises becomes AttributeError "object C does not have M method",   *)
(* whatever its message; any other exception of the read propagates.      *)
(*                                                                         *)
(* A program defines M on class C as a method (class), or as a property    *)
(* whose getter raises AttributeError (failing) or ValueError (raising),   *)
(* and reaches it on an instance c by aiter(c) or anext(c) (builtin), or   *)
(* by async for over c or await c (statement). __aiter__ returns c, whose *)
(* class has an __anext__ that ends the iteration; __await__ returns an    *)
(* empty iterator. The outcome is "ok", or the exception and its message.  *)
(***************************************************************************)
EXTENDS Sequences

Methods == {"__aiter__", "__anext__", "__await__"}
\* await has no builtin.
Programs == {p \in [method : Methods, where : {"class", "failing", "raising"}, via : {"builtin", "statement"}] :
                ~(p.method = "__await__" /\ p.via = "builtin")}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Run(p) == CASE p.where = "class" -> "ok"
            [] p.where = "failing" -> "AttributeError: object C does not have " \o p.method \o " method"
            [] OTHER -> "ValueError: read"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The read's own AttributeError never escapes; another exception does.
Replaced == Done /\ program.where # "class" =>
    outcome \in {"ValueError: read"} \cup {"AttributeError: object C does not have " \o m \o " method" : m \in Methods}
=============================================================================
