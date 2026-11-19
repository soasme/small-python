--------------------------- MODULE AbstractChecks ---------------------------
(***************************************************************************)
(* isinstance() and issubclass() of objects that are not classes, as       *)
(* PLS-315 19.3.21 and 19.3.22 state them: each argument that is not a      *)
(* class must have a __bases__ tuple, the derived one checked first; the   *)
(* subclass search reads __bases__, following a single base in a loop and  *)
(* searching several in order, each nested search counting toward the     *)
(* recursion depth; isinstance reads the instance's __class__ after        *)
(* checking the target. A read may come from a property or a __getattr__  *)
(* fallback.                                                               *)
(*                                                                         *)
(* Objects A, B, C, D and Z have __bases__ properties giving (), (A,),     *)
(* (B, A), (C,) and (), and log their names when read; G's __getattr__     *)
(* gives (A,) and logs "getattr"; N has no __bases__; Loop's property      *)
(* gives (Loop, Loop); int and K are classes. A program calls              *)
(* issubclass(S, T), or isinstance(I, T) for an I whose __class__          *)
(* property logs "class" and gives S, where T is A, C, Z, N, K, or the     *)
(* tuple (Z, A), with its arguments given in turn or starred, alike, or  *)
(* calls type.__subclasscheck__(T, S) or type.__instancecheck__(T, I),    *)
(* the same check of a class T without its hook, refusing another T.     *)
(* The outcome is the result or exception, then the log.                   *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Subjects == {"A", "B", "D", "G", "N", "int", "Loop"}
Targets == {"A", "C", "Z", "N", "K", "pair"}
Programs == [check : {"isinstance", "issubclass"}, subject : Subjects, target : Targets, via : {"direct", "starred", "type"}]
Limit == 4  \* stands for the recursion limit

Bases(x) == CASE x = "B" -> <<"A">>
              [] x = "C" -> <<"B", "A">>
              [] x = "D" -> <<"C">>
              [] x = "G" -> <<"A">>
              [] x = "Loop" -> <<"Loop", "Loop">>
              [] x = "int" -> <<"object">>
              [] OTHER -> <<>>
Read(x) == IF x \in {"A", "B", "C", "D", "Z"} THEN " " \o x
           ELSE IF x = "G" THEN " getattr" ELSE ""
IsClass(x) == x \in {"int", "K"}

Res(r, log) == [r |-> r, log |-> log]
\* Prefix a log to a result.
After(log, w) == Res(w.r, log \o w.log)

RECURSIVE Walk(_, _, _), Any(_, _, _, _)
Walk(d, c, n) ==
    IF d = c THEN Res("True", "")
    ELSE IF d = "N" THEN Res("False", "")          \* no __bases__
    ELSE IF Len(Bases(d)) = 1 THEN After(Read(d), Walk(Bases(d)[1], c, n))
    ELSE After(Read(d), Any(Bases(d), 1, c, n))
Any(b, i, c, n) ==
    IF i > Len(b) THEN Res("False", "")
    ELSE IF n + 1 >= Limit THEN Res("RecursionError", "")
    ELSE LET w == Walk(b[i], c, n + 1)
         IN IF w.r = "False" THEN After(w.log, Any(b, i + 1, c, n)) ELSE w

Subclass(s, t) ==
    IF IsClass(s) /\ IsClass(t) THEN Res("False", "")
    ELSE IF s = "N" THEN Res("TypeError:1", "")
    ELSE IF t = "N" THEN Res("TypeError:2", Read(s))
    ELSE After(Read(s) \o Read(t), Walk(s, t, 0))

Instance(s, t) ==
    IF t = "K" THEN Res("False", " class")
    ELSE IF t = "N" THEN Res("TypeError:2", "")
    ELSE After(Read(t) \o " class", Walk(s, t, 0))

One(p, t) == IF p.check = "issubclass" THEN Subclass(p.subject, t) ELSE Instance(p.subject, t)

\* A tuple tries its items in order until one is true or raises.
Run(p) == IF p.via = "type" /\ ~IsClass(p.target) THEN Res("TypeError:d", "")
          ELSE IF p.target # "pair" THEN One(p, p.target)
          ELSE LET z == One(p, "Z") IN IF z.r = "False" THEN After(z.log, One(p, "A")) ELSE z

Show(w) == IF w.r = "RecursionError" THEN w.r ELSE w.r \o w.log

VARIABLES program, outcome, verdict
vars == <<program, outcome, verdict>>

Pending == "pending"

Init == program \in Programs /\ outcome = Pending /\ verdict = Pending
Execute == outcome = Pending
    /\ outcome' = Show(Run(program)) /\ verdict' = Run(program).r
    /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

Verdicts == Done => verdict \in {"True", "False", "TypeError:1", "TypeError:2", "TypeError:d", "RecursionError"}

\* type's methods check only a class target.
TypeTarget == Done /\ program.via = "type" => (verdict = "TypeError:d") = ~IsClass(program.target)

\* Searching a cycle of several bases exhausts the recursion depth.
LoopRaises == Done /\ program.subject = "Loop" /\ program.target \in {"A", "C", "Z"} /\ program.via # "type"
    => verdict = "RecursionError"

\* What D reaches through __bases__ it is a subclass of.
Reaches == Done /\ program.check = "issubclass" /\ program.subject = "D" /\ program.target \in {"A", "C"} /\ program.via # "type"
    => verdict = "True"
=============================================================================
