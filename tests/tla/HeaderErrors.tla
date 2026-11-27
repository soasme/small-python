---------------------------- MODULE HeaderErrors ----------------------------
(***************************************************************************)
(* Which error a definition's or statement's header reports, as PLS-315    *)
(* 16.7, 16.5, 14.12 and 14.15 state it: type parameters of a function or  *)
(* a class that fail after a name, or after a bound's expression; a        *)
(* TypeVarTuple's bound and a ParamSpec's constraint tuple; a type alias   *)
(* whose parameters no "=" follows; a decorator followed by a name; and an *)
(* import of no names, plain or lazy. The outcome is the message, column   *)
(* and end column.                                                         *)
(***************************************************************************)
EXTENDS Naturals

Programs == {"def_name", "def_bound", "class_name", "alias_equals", "tuple_bound", "spec_constraints", "decorator",
             "import", "lazy_import"}

VARIABLES program, outcome
vars == <<program, outcome>>

Reported(p) == CASE p = "def_name" -> <<"expected '('", 6, 7>>
                 [] p = "def_bound" -> <<"invalid syntax. Perhaps you forgot a comma?", 10, 13>>
                 [] p = "class_name" -> <<"invalid syntax", 11, 12>>
                 [] p = "alias_equals" -> <<"invalid syntax", 11, 12>>
                 [] p = "tuple_bound" -> <<"cannot use bound with TypeVarTuple", 10, 21>>
                 [] p = "spec_constraints" -> <<"cannot use constraints with ParamSpec", 10, 18>>
                 [] p = "decorator" -> <<"invalid syntax", 4, 5>>
                 [] p = "import" -> <<"Expected one or more names after 'import'", 7, 7>>
                 [] p = "lazy_import" -> <<"invalid syntax", 12, 13>>

Init == program \in Programs /\ outcome = <<"pending", 0, 0>>
Execute == outcome[1] = "pending" /\ outcome' = Reported(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome[1] # "pending"

\* Only a function definition forces a token after its type parameters.
ForcedParen == Done /\ outcome[1] = "expected '('" => program = "def_name"

\* An error is never empty, except the end of an import's line.
Located == Done => outcome[2] < outcome[3] \/ program = "import"
=============================================================================
