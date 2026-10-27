--------------------------- MODULE BuiltinsScope ---------------------------
(***************************************************************************)
(* Builtins and restricted execution, as The Python Language Reference     *)
(* specifies them (reference/executionmodel.html#builtins-and-restricted-  *)
(* execution): a name not found locally or in the globals is looked up in  *)
(* the builtins namespace, which is the globals' __builtins__ (a module or *)
(* a dictionary), inserted as the builtins module when exec() or eval() is *)
(* given globals without one; a global shadows a builtin, and the builtins *)
(* module can be extended; a dictionary of builtins restricts what code    *)
(* can find, the import machinery's __import__ included.                   *)
(*                                                                         *)
(* A lookup program evaluates NAME with eval() in globals whose            *)
(* __builtins__ is absent, the builtins module, a dictionary mapping len   *)
(* to a custom function, or an empty dictionary, with or without a global  *)
(* len; NAME is len, a name the program first adds to the builtins module, *)
(* or __import__ (used by an import statement run with exec()). An insert  *)
(* program runs exec() in an empty dictionary and checks that it gained    *)
(* __builtins__ bound to the builtins module or its dictionary. The        *)
(* outcome is which object was found, or the exception.                    *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [part : {"lookup"}, builtins : {"absent", "module", "custom", "empty"}, shadow : BOOLEAN,
             name : {"len", "added", "import"}]
            \cup [part : {"insert"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Lookup(p) ==
    LET standard == p.builtins \in {"absent", "module"}
    IN  CASE p.name = "len" /\ p.shadow -> "global"
          [] p.name = "len" /\ p.builtins = "custom" -> "custom"
          [] p.name = "import" /\ ~standard -> "ImportError"   \* __import__ not found
          [] standard -> "builtin"
          [] OTHER -> "NameError"

Run(p) == IF p.part = "lookup" THEN Lookup(p) ELSE "True"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Globals always win over builtins.
GlobalsFirst == Done /\ program.part = "lookup" /\ program.shadow /\ program.name = "len" => outcome = "global"
=============================================================================
