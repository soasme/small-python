------------------------------ MODULE Scopes ------------------------------
(***************************************************************************)
(* Name binding and resolution, as The Python Language Reference           *)
(* specifies it (reference/executionmodel.html#naming-and-binding), over   *)
(* every program of this shape:                                            *)
(*                                                                         *)
(*     x = 'global'                                                        *)
(*     def outer():                                                        *)
(*         [global x]                          # odecl                     *)
(*         [x = 'outer']                       # oassign                   *)
(*         [class C:                           # cls: inner is a function  *)
(*              seen = x                       # in a class body, which    *)
(*              x = 'class']                   # binds x itself            *)
(*         def inner():                                                    *)
(*             [global x | nonlocal x]         # idecl                     *)
(*             [x = 'inner']                   # before                    *)
(*             r = x | [x for _ in (1,)][0]    # read                      *)
(*             [x = 'inner']                   # after                     *)
(*             return r                                                    *)
(*         [x = 'late']                        # late                      *)
(*         return inner(), x                   # C.inner() with a class    *)
(*     result = outer(), x                                                 *)
(*                                                                         *)
(* The outcome is what inner read, outer's x after the call, the global x  *)
(* at the end, and what the class body saw; or the exception raised; or a  *)
(* SyntaxError at compile time.                                            *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [odecl : {"none", "global"}, oassign : BOOLEAN, late : BOOLEAN,
             idecl : {"none", "global", "nonlocal"}, before : BOOLEAN, after : BOOLEAN,
             read : {"direct", "comprehension"}, cls : BOOLEAN]

VARIABLES program, outcome
vars == <<program, outcome>>

\* outer binds x locally if it assigns x without declaring it global.
OuterLocal(p) == p.odecl = "none" /\ (p.oassign \/ p.late)

\* Where each function's x lives: the global namespace "G", outer's local
\* (a cell, since inner may refer to it) "O", or inner's local "I". A class
\* body between them is skipped: its names are not visible to functions.
OuterTarget(p) == IF OuterLocal(p) THEN "O" ELSE "G"
InnerTarget(p) ==
    CASE p.idecl = "global" -> "G"
      [] p.idecl = "nonlocal" -> "O"
      [] p.before \/ p.after -> "I"            \* any assignment makes x local to the whole block
      [] OTHER -> OuterTarget(p)                \* free: the nearest enclosing function binding, else global

\* nonlocal must name a binding in an enclosing function scope.
SyntaxErrorAt(p) == p.idecl = "nonlocal" /\ ~OuterLocal(p)

Outcome(kind, read, view, global, seen) == <<kind, read, view, global, seen>>

\* A comprehension reads x as its enclosing function would (the comprehension
\* is a scope of its own, whose free x resolves to inner's), so p.read does
\* not change the outcome; the replay checks that on both implementations.
Run(p) ==
    LET g1 == IF p.oassign /\ OuterTarget(p) = "G" THEN "outer" ELSE "global"
        o1 == IF p.oassign /\ OuterTarget(p) = "O" THEN "outer" ELSE "unbound"
        \* x is local to the class block, which reads unbound locals from
        \* the globals, never from the enclosing function.
        seen == IF p.cls THEN g1 ELSE ""
        g2 == IF p.late /\ OuterTarget(p) = "G" THEN "late" ELSE g1
        o2 == IF p.late /\ OuterTarget(p) = "O" THEN "late" ELSE o1
        t == InnerTarget(p)
        g3 == IF p.before /\ t = "G" THEN "inner" ELSE g2
        o3 == IF p.before /\ t = "O" THEN "inner" ELSE o2
        i3 == IF p.before /\ t = "I" THEN "inner" ELSE "unbound"
        value == CASE t = "G" -> g3 [] t = "O" -> o3 [] t = "I" -> i3
        g4 == IF p.after /\ t = "G" THEN "inner" ELSE g3
        o4 == IF p.after /\ t = "O" THEN "inner" ELSE o3
        view == IF OuterTarget(p) = "O" THEN o4 ELSE g4
    IN  CASE SyntaxErrorAt(p) -> Outcome("syntax", "", "", "", "")
          [] value = "unbound" -> Outcome("raise", "UnboundLocalError", "", "", "")
          [] OTHER -> Outcome("ok", value, view, g4, seen)

Init == program \in Programs /\ outcome = Outcome("pending", "", "", "", "")

Execute ==
    /\ outcome[1] = "pending"
    /\ outcome' = Run(program)
    /\ UNCHANGED program

Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
(* What the reference states, checked against the model.                  *)

Done == outcome[1] # "pending"

\* "If a name is bound in a block, it is a local variable of that block":
\* a read before the only assignment fails, even if an outer x exists.
UnboundLocal == Done /\ program.idecl = "none" /\ program.after /\ ~program.before =>
                outcome[1] = "raise" /\ outcome[2] = "UnboundLocalError"

\* global makes assignments rebind the module's name.
GlobalRebinds == Done /\ program.idecl = "global" /\ (program.before \/ program.after) => outcome[4] = "inner"

\* nonlocal rebinds outer's variable, which outer then sees.
NonlocalRebinds == Done /\ outcome[1] = "ok" /\ program.idecl = "nonlocal" /\ (program.before \/ program.after) =>
                   outcome[3] = "inner" /\ outcome[4] = "global"

\* Free variables are looked up when used: a closure sees a later rebinding.
LateBinding == Done /\ outcome[1] = "ok" /\ program.late /\ program.odecl = "none" /\ program.idecl = "none" /\
               ~program.before /\ ~program.after => outcome[2] = "late"

\* "The scope of names defined in a class block is limited to the class
\* block": a function in the class never sees the class's x.
ClassInvisible == Done /\ outcome[1] = "ok" => outcome[2] # "class"

=============================================================================
