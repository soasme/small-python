---------------------------- MODULE MatchErrors ----------------------------
(***************************************************************************)
(* Where the early errors of a case pattern are located, as PLS-315        *)
(* 15.6.1 states it, for statements of this shape:                         *)
(*                                                                         *)
(*     match x:                                                            *)
(*         case <pattern>: pass                                            *)
(*                                                                         *)
(* A pattern is named by its source, which begins at column 10. Each is   *)
(* described by its parts: the patterns that bind a name, in visiting     *)
(* order, with the name and the span (from, to) of the binding pattern    *)
(* (a capture, starred or as pattern, or the mapping pattern of a **      *)
(* rest); the span of an or-pattern whose alternatives bind different     *)
(* names; and the number of starred names of its sequence pattern, with   *)
(* that pattern's span. The outcome is the message, column and end        *)
(* column of the SyntaxError, or "ok".                                     *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Patterns == {"[b, 1 as b]", "[b, *b]", "{1: b, **b}", "C(x=b, y=b)", "b as b", "[x, (y, x)]",
             "[a, b] | [a]", "1 | a", "[*a, *b]", "*a, *b", "[a, *r]", "(b, c) as d"}

Bind(name, from, to) == <<name, from, to>>
Binders(p) == CASE p = "[b, 1 as b]" -> <<Bind("b", 1, 2), Bind("b", 4, 10)>>
                [] p = "[b, *b]" -> <<Bind("b", 1, 2), Bind("b", 4, 6)>>
                [] p = "{1: b, **b}" -> <<Bind("b", 4, 5), Bind("b", 0, 11)>>
                [] p = "C(x=b, y=b)" -> <<Bind("b", 4, 5), Bind("b", 9, 10)>>
                [] p = "b as b" -> <<Bind("b", 0, 1), Bind("b", 0, 6)>>
                [] p = "[x, (y, x)]" -> <<Bind("x", 1, 2), Bind("y", 5, 6), Bind("x", 8, 9)>>
                [] p = "[a, *r]" -> <<Bind("a", 1, 2), Bind("r", 4, 6)>>
                [] p = "(b, c) as d" -> <<Bind("b", 1, 2), Bind("c", 4, 5), Bind("d", 0, 11)>>
                [] OTHER -> <<>>
\* The or-pattern whose alternatives bind different names.
Differing(p) == CASE p = "[a, b] | [a]" -> <<0, 12>> [] p = "1 | a" -> <<0, 5>> [] OTHER -> <<>>
\* A sequence pattern's starred names and span.
Stars(p) == CASE p = "[*a, *b]" -> <<2, 0, 8>> [] p = "*a, *b" -> <<2, 0, 6>> [] p = "[a, *r]" -> <<1, 0, 7>> [] OTHER -> <<0, 0, 0>>

Column(n) == 10 + n
Error(message, from, to) == <<message, Column(from), Column(to)>>

\* The first binding pattern that binds a name bound before it.
Again(b) == {i \in 1..Len(b) : \E j \in 1..(i - 1) : b[j][1] = b[i][1]}
First(s) == CHOOSE i \in s : \A j \in s : i <= j

Located(p) ==
    LET b == Binders(p)  s == Stars(p)
    IN  CASE s[1] > 1 -> Error("multiple starred names in sequence pattern", s[2], s[3])
          [] Again(b) # {} -> LET i == First(Again(b))
                              IN Error("multiple assignments to name '" \o b[i][1] \o "' in pattern", b[i][2], b[i][3])
          [] Differing(p) # <<>> -> Error("alternative patterns bind different names", Differing(p)[1], Differing(p)[2])
          [] OTHER -> <<"ok", 0, 0>>

VARIABLES program, outcome
vars == <<program, outcome>>

Init == program \in Patterns /\ outcome = <<"pending", 0, 0>>
Execute == outcome[1] = "pending" /\ outcome' = Located(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome[1] # "pending"

\* An error lies within the pattern, and is never empty.
WithinPattern == Done /\ outcome[1] # "ok" => Column(0) <= outcome[2] /\ outcome[2] < outcome[3]

\* A pattern binding each name once, with one starred name at most, compiles.
Distinct == Done /\ Again(Binders(program)) = {} /\ Differing(program) = <<>> /\ Stars(program)[1] <= 1 => outcome[1] = "ok"
=============================================================================
