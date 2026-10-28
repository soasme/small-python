---------------------------- MODULE NumericHash -----------------------------
(***************************************************************************)
(* Hashing of numeric types, as the Built-in Types chapter specifies it    *)
(* (library/stdtypes.html#hashing-of-numeric-types): numbers that compare  *)
(* equal hash equal, whatever their types; the hash of a nonnegative       *)
(* rational m / n is m times the inverse of n modulo the prime P = 2^61 -  *)
(* 1 (CPython's on 64-bit platforms), reduced modulo P, so that the hash   *)
(* of m * 2^e is m rotated left by e modulo 61 within 61 bits; a negative  *)
(* number hashes to the negation of its absolute value's hash, -1 becoming *)
(* -2; the infinities hash to plus and minus 314159, and a NaN by its     *)
(* identity; and a complex number combines the hashes of its parts as      *)
(* hash(real) + 1000003 * hash(imag), reduced to a signed 64-bit value, -1 *)
(* again becoming -2.                                                      *)
(*                                                                         *)
(* A program hashes m * 2^e, or its negation, as an int (for e >= 0) or a  *)
(* float, for m among small integers and e among exponents from the        *)
(* subnormal range to beyond the modulus period; or runs one of the        *)
(* sources of CASES in a fresh namespace. The outcome is the hash in       *)
(* canonical form, 0 or rot(o, j) with o odd and below 2^24, possibly      *)
(* negated, standing for o rotated left by j bits within 61, which is m *  *)
(* 2^j modulo P; or the repr of the case's result.                         *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

Ms == {0, 1, 3, 5, 12, 255}
Es == {-1074, -1070, -62, -61, -60, -3, -1, 0, 1, 3, 60, 61, 62, 122, 1000}

RECURSIVE OddPart(_)
OddPart(m) == IF m % 2 = 1 THEN m ELSE OddPart(m \div 2)
RECURSIVE Twos(_)
Twos(m) == IF m % 2 = 1 THEN 0 ELSE 1 + Twos(m \div 2)

\* m * 2^e is OddPart(m) rotated left by (e + Twos(m)) mod 61 bits.
Rot(o, j) == "rot(" \o ToString(o) \o ", " \o ToString(j) \o ")"
Hash(m, e, negative) ==
    LET o == OddPart(m)  j == (e + Twos(m)) % 61
    IN  CASE m = 0 -> "0"
          [] ~negative -> Rot(o, j)
          [] o = 1 /\ j = 0 -> "-" \o Rot(1, 1)          \* -1 becomes -2
          [] OTHER -> "-" \o Rot(o, j)


Cases == {"hash_info", "inf", "nan_identity", "modulus", "minus_one", "bool", "complex_real", "complex_formula",
          "complex_imag_only", "complex_inf", "equal_implies_hash", "negative_zero",
          "dict_key_equal_numbers", "set_mixed", "int_subclass", "float_subclass", "hash_returns_int",
          "big_negative", "large_float_integral"}
Programs == [type : {"int"}, m : Ms, e : {e \in Es : e >= 0}, negative : BOOLEAN]
            \cup [type : {"float"}, m : Ms, e : Es, negative : BOOLEAN]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Generated(p) == Hash(p.m, p.e, p.negative)

Case(c) ==
    CASE c = "hash_info" -> "(True, 314159, 1000003)"
      [] c = "inf" -> "(314159, -314159)"
      [] c = "nan_identity" -> "(True, True, False)"
      [] c = "modulus" -> "(0, 1, 0, 5, True)"
      [] c = "minus_one" -> "(-2, -2, -2, True)"
      [] c = "bool" -> "(1, 0, True)"
      [] c = "complex_real" -> "True"
      [] c = "complex_formula" -> "True"
      [] c = "complex_imag_only" -> "True"
      [] c = "complex_inf" -> "True"
      [] c = "equal_implies_hash" -> "True"
      [] c = "negative_zero" -> "(0, 0)"
      [] c = "dict_key_equal_numbers" -> "{1: 'bool'}"
      [] c = "set_mixed" -> "1"
      [] c = "int_subclass" -> "True"
      [] c = "float_subclass" -> "True"
      [] c = "hash_returns_int" -> "'int'"
      [] c = "big_negative" -> "True"
      [] c = "large_float_integral" -> "True"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* An int and a float of one value hash alike, and negation negates the hash.
CrossType == Done /\ "type" \in DOMAIN program /\ program.e >= 0 =>
    outcome = Hash(program.m, program.e, program.negative)
NeverMinusOne == Done /\ "type" \in DOMAIN program => outcome # "-" \o Rot(1, 0)
=============================================================================
