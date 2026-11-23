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
(* module level, or nowhere. An order program has two errors: unbound      *)
(* nonlocal names in sibling functions, in a function and one nested in it *)
(* (inner or outer first in the source), in a function and the module, or *)
(* an async generator's valued return before or after an unbound nonlocal; *)
(* the first met visiting scopes from the module downward, sibling scopes  *)
(* in source order, is raised, and a return only when no scope has one     *)
(* (PLS-315 8.4, 14.9). A statements program has two early errors, a yield *)
(* in a module's or class's annotation and an annotated global name, either *)
(* first, or a binding in a for, except or case header before a global     *)
(* declaration in its suite: the first in statement order, a header before *)
(* its suite, is raised (8.3.1, 8.7). An expressions program has a yield *)
(* in a comprehension on each of two lines of one construct: the first    *)
(* met visiting it (a target before its value, keys before values, a      *)
(* call's positional arguments before its keywords, defaults before       *)
(* decorators, a dict comprehension's value before its key, a test before *)
(* its branches) is raised. A locals program binds a target and, with an  *)
(* assignment expression, a name in its value: the value's is numbered    *)
(* first (28.2). The outcome is "ok", the message and line, or the locals. *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Decls == {"global", "nonlocal"}
Programs == [part : {"decl"}, decl : Decls, prior : {"none", "param", "use", "assign", "annot", "other"},
             after : {"none", "assign", "annot"}]
            \cup [part : {"place"}, decl : Decls, where : {"module", "class"}]
            \cup [part : {"binding"}, source : {"enclosing", "module", "none"}]
            \cup [part : {"order"}, shape : {"siblings", "inner_first", "outer_first", "module", "returns", "return_first", "return_last"}]
            \cup [part : {"statements"}, body : {"module", "class"}, first : {"annotation", "global"}]
            \cup [part : {"headers"}, header : {"for", "except", "case"}]
            \cup [part : {"expressions"}, shape : {"assign", "for", "annassign", "dict", "call", "decorator", "dictcomp", "cond"}]
            \cup [part : {"locals"}, shape : {"assign", "for", "annassign", "def"}]

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

\* Scopes from the module downward, siblings in source order; returns last.
Order(p) == CASE p.shape = "siblings" -> "no binding for nonlocal 'a' found@2"
              [] p.shape = "inner_first" -> "no binding for nonlocal 'b' found@4"
              [] p.shape = "outer_first" -> "no binding for nonlocal 'b' found@2"
              [] p.shape = "module" -> "nonlocal declaration not allowed at module level@3"
              [] p.shape = "returns" -> "'return' with value in async generator@3"
              [] p.shape = "return_first" -> "no binding for nonlocal 'z' found@5"
              [] p.shape = "return_last" -> "no binding for nonlocal 'z' found@2"

\* The earlier statement's error; a module's global annotation is no error.
Statements(p) == IF p.first = "annotation" \/ p.body = "module"
                 THEN "yield expression cannot be used within an annotation@" \o (IF p.first = "annotation" THEN "2" ELSE "4")
                 ELSE "annotated name 'a' can't be global@3"

\* The line of the first error met: a target's, or the later line's.
Expressions(p) == "'yield' inside list comprehension@" \o (IF p.shape \in {"assign", "for", "annassign"} THEN "2" ELSE "3")
Locals(p) == IF p.shape = "def" THEN "z,f" ELSE "y,x"

Run(p) == CASE p.part = "decl" -> Decl(p) [] p.part = "place" -> Place(p) [] p.part = "binding" -> Binding(p)
            [] p.part = "order" -> Order(p) [] p.part = "statements" -> Statements(p)
            [] p.part = "headers" -> "name 'x' is assigned to before global declaration@4"
            [] p.part = "expressions" -> Expressions(p) [] p.part = "locals" -> Locals(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A declaration that comes first, alone, with a plain assignment, is fine.
CleanDeclarations == Done /\ program.part = "decl" /\ program.prior = "none" /\ program.after # "annot" => outcome = "ok"

\* A header's binding is analysed before the declaration in its suite.
HeadersFirst == Done /\ program.part = "headers" => outcome # "ok"

\* A target is analysed before the value it is assigned, but numbered after.
TargetsFirst == Done /\ program.part = "expressions" /\ program.shape \in {"assign", "for", "annassign"} =>
                outcome = "'yield' inside list comprehension@2"
ValuesNumberedFirst == Done /\ program.part = "locals" /\ program.shape # "def" => outcome = "y,x"

\* A valued async generator return is never reported over a nonlocal error.
ScopesBeforeReturns == Done /\ program.part = "order" /\ program.shape \in {"return_first", "return_last"} =>
                       outcome # "'return' with value in async generator@3"
=============================================================================
