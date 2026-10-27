------------------------------- MODULE Match -------------------------------
(***************************************************************************)
(* Structural pattern matching, as The Python Language Reference           *)
(* specifies it (reference/compound_stmts.html#the-match-statement), for   *)
(* every statement of this shape:                                          *)
(*                                                                         *)
(*     match <subject>:                                                    *)
(*         case <pattern 1>: ...                                           *)
(*         case <pattern 2>: ...                                           *)
(*                                                                         *)
(* Subjects and the values patterns bind are named by their repr; P is an  *)
(* instance of                                                             *)
(*                                                                         *)
(*     class P:                                                            *)
(*         __match_args__ = ('x', 'y')                                     *)
(*         x, y = 1, 2                                                     *)
(*                                                                         *)
(* Patterns are named by their source. The outcome is which case matched,  *)
(* with the names it bound (in alphabetical order), or the exception.      *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Subjects == {"1", "True", "None", "'ab'", "(1, 2)", "[1]", "{'k': 1, 'j': 2}", "P"}
Patterns == {"1", "True", "None", "x", "_", "[a, b]", "[a, *r]", "{'k': a}", "{'k': a, **r}",
             "P(a)", "P(y=b)", "P(a, b, n)", "int(n)", "str(s)", "[a, _] | [a]", "(a, b) as t",
             "{'k': a, 'k': b}"}
Programs == Subjects \X Patterns \X Patterns

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending", <<>>>>

\* What the subjects are.
IsInt(v) == v \in {"1", "True"}                      \* isinstance(v, int)
EqualsOne(v) == v \in {"1", "True"}                  \* v == 1
IsSequence(v) == v \in {"(1, 2)", "[1]"}             \* str is not one, for patterns
Items(v) == IF v = "(1, 2)" THEN <<"1", "2">> ELSE IF v = "[1]" THEN <<"1">> ELSE <<>>
IsMapping(v) == v = "{'k': 1, 'j': 2}"

RECURSIVE Join(_)
Join(s) == IF s = <<>> THEN "" ELSE IF Len(s) = 1 THEN Head(s) ELSE Head(s) \o ", " \o Join(Tail(s))

Yes(b) == <<"yes", b>>
No == <<"no", <<>>>>
Bind(name, v) == <<name, v>>

\* Matching one pattern: whether it matches, and its bindings.
Match(pat, v) ==
    CASE pat = "1" -> IF EqualsOne(v) THEN Yes(<<>>) ELSE No          \* literals compare with ==
      [] pat \in {"True", "None"} -> IF v = pat THEN Yes(<<>>) ELSE No  \* ... singletons with is
      [] pat = "x" -> Yes(<<Bind("x", v)>>)
      [] pat = "_" -> Yes(<<>>)
      [] pat = "[a, b]" -> IF IsSequence(v) /\ Len(Items(v)) = 2
                           THEN Yes(<<Bind("a", Items(v)[1]), Bind("b", Items(v)[2])>>) ELSE No
      [] pat = "[a, *r]" -> IF IsSequence(v) /\ Len(Items(v)) >= 1   \* a star always binds a list
                            THEN Yes(<<Bind("a", Items(v)[1]), Bind("r", "[" \o Join(Tail(Items(v))) \o "]")>>) ELSE No
      [] pat = "{'k': a}" -> IF IsMapping(v) THEN Yes(<<Bind("a", "1")>>) ELSE No   \* other keys are ignored
      [] pat = "{'k': a, **r}" -> IF IsMapping(v) THEN Yes(<<Bind("a", "1"), Bind("r", "{'j': 2}")>>) ELSE No
      [] pat = "P(a)" -> IF v = "P" THEN Yes(<<Bind("a", "1")>>) ELSE No   \* by __match_args__
      [] pat = "P(y=b)" -> IF v = "P" THEN Yes(<<Bind("b", "2")>>) ELSE No
      [] pat = "P(a, b, n)" -> IF v = "P" THEN <<"TypeError", <<>>>> ELSE No  \* more than __match_args__
      [] pat = "int(n)" -> IF IsInt(v) THEN Yes(<<Bind("n", v)>>) ELSE No     \* int matches itself
      [] pat = "str(s)" -> IF v = "'ab'" THEN Yes(<<Bind("s", v)>>) ELSE No
      [] pat = "[a, _] | [a]" -> IF IsSequence(v) THEN Yes(<<Bind("a", Items(v)[1])>>) ELSE No
      [] pat = "(a, b) as t" -> IF IsSequence(v) /\ Len(Items(v)) = 2
                                THEN Yes(<<Bind("a", Items(v)[1]), Bind("b", Items(v)[2]), Bind("t", v)>>) ELSE No

\* An irrefutable pattern makes later cases unreachable; a mapping pattern
\* cannot repeat a key. Both are syntax errors.
Irrefutable(pat) == pat \in {"x", "_"}
Invalid(p) == Irrefutable(p[2]) \/ "{'k': a, 'k': b}" \in {p[2], p[3]}

\* Cases are tried in order; the first that matches runs.
Run(p) ==
    LET first == Match(p[2], p[1])  second == Match(p[3], p[1])
    IN  CASE Invalid(p) -> <<"syntax", <<>>>>
          [] first[1] = "yes" -> <<"case 1", first[2]>>
          [] first[1] = "TypeError" -> first
          [] second[1] = "yes" -> <<"case 2", second[2]>>
          [] second[1] = "TypeError" -> second
          [] OTHER -> <<"none", <<>>>>

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A case whose pattern always matches catches everything not caught before.
CatchAll == Done /\ ~Invalid(program) /\ Irrefutable(program[3]) => outcome[1] # "none"

\* Strings and mappings never match sequence patterns.
StrNotSequence == Done /\ program[1] \in {"'ab'", "{'k': 1, 'j': 2}"} /\ program[2] = "[a, b]" => outcome[1] # "case 1"

\* `case True` matches only True, though `case 1` matches it too.
Singletons == Done /\ program[2] = "True" /\ outcome[1] = "case 1" => program[1] = "True"
=============================================================================
