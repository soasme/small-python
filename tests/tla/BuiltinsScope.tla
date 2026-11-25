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
(* to a custom function, an empty dictionary, or an empty dict subclass    *)
(* whose Python __missing__, which may loop, gives that function for len   *)
(* and the added name and raises KeyError for others, with or without a    *)
(* global len; NAME is len, a name the program first adds to the builtins  *)
(* module, or __import__ (used by an import statement run with exec()). An *)
(* insert program runs exec() in an empty dictionary and checks that it    *)
(* gained __builtins__ bound to the builtins module or its dictionary. The *)
(* outcome is which object was found, or the exception. A builder program  *)
(* runs class C(base()) with exec() under builtins whose Python            *)
(* __missing__, which may loop, logs each name and gives base and          *)
(* __build_class__, or lacks the latter: the outcome is the names looked   *)
(* up, in order, and whether the statement raised NameError; with globals *)
(* lacking __name__, the body's read of it for __module__ looks it up and  *)
(* raises the NameError in the body's frame C, which the outcome names     *)
(* with the innermost frame of the traceback. A keyed                      *)
(* program replaces the builtins module's len key by an object of its hash *)
(* whose Python __eq__, which may loop, counts its calls, then calls a     *)
(* function that reads len as a call's callee, as an argument, or twice:   *)
(* each read compares once, and the outcome is the value and the count.    *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [part : {"lookup"}, builtins : {"absent", "module", "custom", "empty", "missing"}, shadow : BOOLEAN,
             name : {"len", "added", "import"}]
            \cup [part : {"insert"}]
            \cup [part : {"builder"}, lacking : BOOLEAN, keyed : BOOLEAN, nameless : BOOLEAN]
            \cup [part : {"keyed"}, where : {"callee", "argument", "twice"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Lookup(p) ==
    LET standard == p.builtins \in {"absent", "module"}
    IN  CASE p.name = "len" /\ p.shadow -> "global"
          [] p.name = "len" /\ p.builtins = "custom" -> "custom"
          [] p.name \in {"len", "added"} /\ p.builtins = "missing" -> "custom"
          [] p.name = "import" /\ ~standard -> "ImportError"   \* __import__ not found
          [] standard -> "builtin"
          [] OTHER -> "NameError"

\* __build_class__ is looked up before the bases are evaluated (16.4.1);
\* a stored key of its hash is compared before __missing__ is called.
Built(p) == LET eq == IF p.keyed THEN "eq " ELSE ""
              IN  eq \o CASE p.lacking /\ p.nameless -> "__build_class__ NameError <module>"
                         [] p.lacking -> "__build_class__ NameError"
                         [] p.nameless -> "__build_class__ base __name__ NameError C"
                         [] OTHER -> "__build_class__ base"

Keyed(p) == CASE p.where = "callee" -> "2 1" [] p.where = "argument" -> "builtin_function_or_method 1" [] OTHER -> "0 2"

Run(p) == CASE p.part = "lookup" -> Lookup(p) [] p.part = "builder" -> Built(p) [] p.part = "keyed" -> Keyed(p) [] OTHER -> "True"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* Globals always win over builtins.
GlobalsFirst == Done /\ program.part = "lookup" /\ program.shadow /\ program.name = "len" => outcome = "global"
=============================================================================
