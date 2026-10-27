---------------------------- MODULE ScopeErrors ----------------------------
(***************************************************************************)
(* The binding rules for global and nonlocal, as The Python Language       *)
(* Reference specifies them (reference/simple_stmts.html#the-global-       *)
(* statement and #the-nonlocal-statement, reference/executionmodel.html#   *)
(* binding-of-names): a name may not be declared global or nonlocal after  *)
(* it is used, assigned, or annotated in the same block, nor when it is a  *)
(* parameter, nor be annotated after the declaration (outside the module), *)
(* nor be both global and nonlocal; nonlocal needs a binding in an         *)
(* enclosing function and is not allowed at module level; and each error   *)
(* is a SyntaxError at the declaration (for global with nonlocal, at the   *)
(* first of the two, though only once an annotation has been checked) or   *)
(* at the annotation.                                                      *)
(*                                                                         *)
(* A declaration program compiles                                          *)
(*                                                                         *)
(*     def g():                                                            *)
(*         x = 1                                                           *)
(*         def f(PARAM):                                                   *)
(*             PRIOR                                                       *)
(*             DECL x                                                      *)
(*             AFTER                                                       *)
(*                                                                         *)
(* where DECL is global or nonlocal; PRIOR is pass, x as a parameter, a    *)
(* use, an assignment, an annotation, or the other declaration; and AFTER  *)
(* is pass, an assignment, or an annotated assignment. A placement program *)
(* puts the declaration at module level or in a class body inside g; a     *)
(* binding program declares nonlocal x where x is bound in g, only at      *)
(* module level, or nowhere. The outcome is "ok" or the message and line.  *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Decls == {"global", "nonlocal"}
Programs == [part : {"decl"}, decl : Decls, prior : {"none", "param", "use", "assign", "annot", "other"},
             after : {"none", "assign", "annot"}]
            \cup [part : {"place"}, decl : Decls, where : {"module", "class"}]
            \cup [part : {"binding"}, source : {"enclosing", "module", "none"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Decl(p) ==
    CASE p.prior = "param" -> "name 'x' is parameter and " \o p.decl \o "@5"
      [] p.prior = "use" -> "name 'x' is used prior to " \o p.decl \o " declaration@5"
      [] p.prior = "annot" -> "annotated name 'x' can't be " \o p.decl \o "@5"
      [] p.prior = "assign" -> "name 'x' is assigned to before " \o p.decl \o " declaration@5"
      [] p.after = "annot" -> "annotated name 'x' can't be " \o (IF p.prior = "other" THEN "global" ELSE p.decl) \o "@6"
      [] p.prior = "other" -> "name 'x' is nonlocal and global@4"   \* found after the block is read
      [] OTHER -> "ok"

Place(p) == IF p.decl = "nonlocal" /\ p.where = "module" THEN "nonlocal declaration not allowed at module level@1" ELSE "ok"

Binding(p) == CASE p.source = "enclosing" -> "ok"
                [] p.source = "module" -> "no binding for nonlocal 'x' found@4"
                [] p.source = "none" -> "no binding for nonlocal 'x' found@3"

Run(p) == CASE p.part = "decl" -> Decl(p) [] p.part = "place" -> Place(p) [] p.part = "binding" -> Binding(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A declaration that comes first, alone, with a plain assignment, is fine.
CleanDeclarations == Done /\ program.part = "decl" /\ program.prior = "none" /\ program.after # "annot" => outcome = "ok"
=============================================================================
