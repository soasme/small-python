------------------------------- MODULE Calls -------------------------------
(***************************************************************************)
(* How a call binds its arguments to a function's parameters, as The       *)
(* Python Language Reference specifies it (reference/expressions.html#    *)
(* calls and reference/compound_stmts.html#function-definitions), for     *)
(* every signature and call of these shapes:                               *)
(*                                                                         *)
(*     def f(a, /, b, *args, c, **kw)     # each part optional; a, b, and *)
(*                                        # c optional with a default     *)
(*     f(p1, p2, ..., a=k_a, b=k_b, c=k_c, z=k_z)                          *)
(*                                                                         *)
(* where a is positional-only, b positional-or-keyword, c keyword-only    *)
(* (after a bare * when there is no *args), and z names no parameter. The *)
(* outcome is the value each parameter is bound to, or the exception.     *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

Kinds == {"none", "req", "opt"}      \* absent, required, or with a default
Names == {"a", "b", "c", "z"}
Programs == [po : Kinds, pk : Kinds, star : BOOLEAN, ko : Kinds, kw : BOOLEAN,
             npos : 0..3, keys : SUBSET Names]

VARIABLES program, outcome
vars == <<program, outcome>>

Absent == "-"
Ok(a, b, c, args, kw) == <<"ok", a, b, c, args, kw>>
Fail(name) == <<name, Absent, Absent, Absent, <<>>, {}>>
Pending == Fail("pending")

Positional(n) == [i \in 1..n |-> IF i = 1 THEN "p1" ELSE IF i = 2 THEN "p2" ELSE "p3"]
Key(k) == "k_" \o k
Default(k) == "d_" \o k

\* "A non-default parameter cannot follow a default one" among the
\* positional parameters.
BadDefaults(p) == p.po = "opt" /\ p.pk = "req"

Bind(p) ==
    LET slots == (IF p.po # "none" THEN <<"a">> ELSE <<>>) \o (IF p.pk # "none" THEN <<"b">> ELSE <<>>)
        args == Positional(p.npos)
        filled == {slots[i] : i \in 1..(IF p.npos < Len(slots) THEN p.npos ELSE Len(slots))}
        value(name) == args[CHOOSE i \in 1..Len(slots) : slots[i] = name]
        extra == SubSeq(args, Len(slots) + 1, p.npos)
        \* A keyword names a parameter that can take it: b and c (when they
        \* exist); never the positional-only a.
        takes(k) == (k = "b" /\ p.pk # "none") \/ (k = "c" /\ p.ko # "none")
        unknown == {k \in p.keys : ~takes(k)}
        twice == {k \in p.keys : takes(k) /\ k \in filled}
        bound(k) == k \in filled \/ (k \in p.keys /\ takes(k))
        kind(k) == CASE k = "a" -> p.po [] k = "b" -> p.pk [] k = "c" -> p.ko
        missing == {k \in {"a", "b", "c"} : kind(k) = "req" /\ ~bound(k)}
        final(k) == CASE kind(k) = "none" -> Absent
                      [] k \in filled -> value(k)
                      [] k \in p.keys /\ takes(k) -> Key(k)
                      [] OTHER -> Default(k)
    IN  CASE BadDefaults(p) -> Fail("syntax")
          [] Len(extra) > 0 /\ ~p.star -> Fail("TypeError")      \* too many positional arguments
          [] unknown # {} /\ ~p.kw -> Fail("TypeError")          \* unexpected (or positional-only) keyword
          [] twice # {} -> Fail("TypeError")                      \* multiple values for an argument
          [] missing # {} -> Fail("TypeError")                    \* missing required argument
          [] OTHER -> Ok(final("a"), final("b"), final("c"),
                         IF p.star THEN extra ELSE <<>>,
                         IF p.kw THEN {<<k, Key(k)>> : k \in unknown} ELSE {})

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Bind(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
(* What the reference states about every binding.                          *)

Done == outcome # Pending
Bound == Done /\ outcome[1] = "ok"

\* Positional arguments fill the positional parameters in order; the rest
\* go to *args.
InOrder == Bound /\ program.po # "none" /\ program.npos >= 1 => outcome[2] = "p1"
ExtraToStar == Bound => Len(outcome[5]) = (LET n == (IF program.po # "none" THEN 1 ELSE 0) + (IF program.pk # "none" THEN 1 ELSE 0)
                                           IN IF program.npos > n THEN program.npos - n ELSE 0)

\* Keyword-only parameters are never filled positionally.
KeywordOnly == Bound /\ program.ko # "none" => outcome[4] \in {Key("c"), Default("c")}

\* A positional-only parameter's name passed as a keyword goes to **kw.
PositionalOnlyName == Bound /\ program.po # "none" /\ "a" \in program.keys => <<"a", Key("a")>> \in outcome[6]

\* Without **kw and *args, a call binds only names and counts the signature has.
Strict == Bound /\ ~program.kw => program.keys \subseteq {"b", "c"}
=============================================================================
