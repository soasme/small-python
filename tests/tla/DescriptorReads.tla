---------------------------- MODULE DescriptorReads --------------------------
(***************************************************************************)
(* Special methods read through a descriptor: __aiter__, __anext__,        *)
(* __await__, __iter__, __bool__ and __hash__, as PLS-315 3.3.1, 7.3.2,    *)
(* 7.5.1, 7.7.4, 7.7.5, 15.1, 15.3, 19.3.2 and 19.3.4 specify them: each   *)
(* is looked up on the object's type (LookupSpecial), and an               *)
(* AttributeError a descriptor's read raises becomes AttributeError        *)
(* "object C does not have M method", whatever its message, for __iter__   *)
(* TypeError "'C' object is not iterable", for __hash__ TypeError          *)
(* "unhashable type: 'C'" (as a set element, "cannot use 'C' as a set      *)
(* element (unhashable type: 'C')"), and for __bool__ leaves the object    *)
(* true; any other exception of the read propagates, and a read's result   *)
(* is the method called.                                                   *)
(*                                                                         *)
(* A program defines M on class C as a method (class), or as a property    *)
(* whose getter returns the method bound to the object (read), raises      *)
(* AttributeError (failing) or ValueError (raising), and reaches it on an  *)
(* instance c by aiter(c), anext(c), iter(c), bool(c) or hash(c)           *)
(* (builtin), or by async for over c, await c, for over c, if c or the     *)
(* display {c} (statement). __aiter__ returns c, whose class has an        *)
(* __anext__ that ends the iteration; __await__ and __iter__ return an     *)
(* empty iterator, __bool__ False, __hash__ 0. The outcome is "ok", or c's *)
(* truth, or the exception and its message.                                *)
(***************************************************************************)
EXTENDS Sequences

Methods == {"__aiter__", "__anext__", "__await__", "__iter__", "__bool__", "__hash__"}
\* await has no builtin.
Programs == {p \in [method : Methods, where : {"class", "read", "failing", "raising"}, via : {"builtin", "statement"}] :
                ~(p.method = "__await__" /\ p.via = "builtin")}

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Absent(m, via) ==
            CASE m = "__iter__" -> "TypeError: 'C' object is not iterable"
               [] m = "__hash__" /\ via = "builtin" -> "TypeError: unhashable type: 'C'"
               [] m = "__hash__" -> "TypeError: cannot use 'C' as a set element (unhashable type: 'C')"
               [] m = "__bool__" -> "True"
               [] OTHER -> "AttributeError: object C does not have " \o m \o " method"

Run(p) == CASE p.where \in {"class", "read"} -> IF p.method = "__bool__" THEN "False" ELSE "ok"
            [] p.where = "failing" -> Absent(p.method, p.via)
            [] OTHER -> "ValueError: read"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The read's own AttributeError never escapes; another exception does.
Replaced == Done /\ program.where \in {"failing", "raising"} =>
    outcome \in {"ValueError: read"} \cup {Absent(m, v) : m \in Methods, v \in {"builtin", "statement"}}
=============================================================================
