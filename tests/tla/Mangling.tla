------------------------------ MODULE Mangling ------------------------------
(***************************************************************************)
(* Private name mangling, as The Python Language Reference specifies it    *)
(* (reference/lexical_analysis.html#reserved-classes-of-identifiers and    *)
(* reference/expressions.html#private-name-mangling): in a class, a name   *)
(* that starts with two underscores and does not end with two is           *)
(* rewritten to _ + the class name without its leading underscores + the   *)
(* name; not when the class name is all underscores.                       *)
(*                                                                         *)
(* A program defines a class, named with up to three of  _ C,  that binds  *)
(* a name, spelled with up to four of  _ x, in one of these ways:          *)
(*                                                                         *)
(*     attr     <name> = 1                    in the class body            *)
(*     self     self.<name> = 1               in a method                  *)
(*     param    def m(self, <name>=1)         a method's parameter         *)
(*     kwarg    r = dict(<name>=1)            in the class body            *)
(*     global   global <name>; <name> = 1     in a method                  *)
(*                                                                         *)
(* The outcome is the name that is bound. A keyword argument's name is    *)
(* not an identifier in an expression, and is not mangled.                 *)
(***************************************************************************)
EXTENDS Integers, Sequences

Words(chars, n) == UNION {[1..k -> chars] : k \in 1..n}
Programs == [cls : Words({"_", "C"}, 3), name : Words({"_", "x"}, 4),
             how : {"attr", "self", "param", "kwarg", "global"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

RECURSIVE Spell(_)
Spell(s) == IF s = <<>> THEN "" ELSE Head(s) \o Spell(Tail(s))
RECURSIVE Strip(_)
Strip(s) == IF s # <<>> /\ Head(s) = "_" THEN Strip(Tail(s)) ELSE s

Private(n) == Len(n) >= 2 /\ n[1] = "_" /\ n[2] = "_" /\ ~(n[Len(n)] = "_" /\ n[Len(n) - 1] = "_")
Mangle(cls, n) == IF Private(n) /\ Strip(cls) # <<>> THEN <<"_">> \o Strip(cls) \o n ELSE n

Bind(p) == IF p.how = "kwarg" THEN Spell(p.name) ELSE Spell(Mangle(p.cls, p.name))

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Bind(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Names that end with two underscores are never mangled.
Dunders == Done /\ Len(program.name) >= 2 /\ program.name[Len(program.name)] = "_" /\
           program.name[Len(program.name) - 1] = "_" => outcome = Spell(program.name)

\* Every other way of binding the name mangles it the same.
Uniform == Done /\ program.how # "kwarg" => outcome = Bind([program EXCEPT !.how = "attr"])
=============================================================================
