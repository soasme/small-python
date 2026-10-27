------------------------------- MODULE Atoms --------------------------------
(***************************************************************************)
(* Atoms and literals, as The Python Language Reference specifies them     *)
(* (reference/expressions.html#atoms, #built-in-constants, #identifiers-   *)
(* names, #literals, and #literals-and-object-identity): True, False,      *)
(* None, and ... evaluate to their constants and, being keywords, cannot   *)
(* be assigned, deleted, bound as targets, parameters, keywords, or import *)
(* names, nor used as attributes, while Ellipsis is an ordinary name; a    *)
(* bound name evaluates to its object and an unbound one raises NameError; *)
(* a literal evaluates to an int, float, complex, str, bytes, or Template  *)
(* of its value, approximated for floats and imaginaries, and negative and *)
(* complex numbers are operations, not literals; literals are immutable,   *)
(* so only their values are guaranteed, and whether equal literals are one *)
(* object is unspecified, except that each evaluation of a template string *)
(* is a new object sharing the identities of its interpolated values; and  *)
(* a parenthesized group yields its expression.                            *)
(*                                                                         *)
(* A program runs one of the sources of CASES in a fresh namespace. The    *)
(* outcome is the repr of its result, or the exception and its message.    *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Cases == {"true_const", "none_const", "ellipsis_const", "assign_false", "assign_none", "assign_true_aug", "attr_none",
          "attr_true_read", "assign_ellipsis", "del_none", "for_true", "param_none", "kwarg_true",
          "import_as_none", "assign_debug", "ellipsis_name", "name_bound", "name_unbound", "name_deleted",
          "literal_int", "literal_float", "literal_imag", "literal_str", "literal_bytes", "literal_fstring",
          "literal_tstring", "negative_not_literal", "complex_not_literal", "same_value", "str_equal",
          "tstring_distinct", "tstring_values_shared", "tstring_mutable_value", "literal_immutable_int",
          "literal_immutable_str", "literal_immutable_bytes", "float_approx", "huge_imag",
          "small_identity_unspecified", "large_identity_unspecified", "repeated_evaluation_equal",
          "group_value", "empty_tuple", "yield_atom_outside"}
Programs == [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Run(p) ==
    CASE p.case = "true_const" -> "(True, 'bool')"
      [] p.case = "none_const" -> "None"
      [] p.case = "ellipsis_const" -> "(Ellipsis, True, 'ellipsis')"
      [] p.case = "assign_false" -> "SyntaxError: cannot assign to False"
      [] p.case = "assign_none" -> "SyntaxError: cannot assign to None"
      [] p.case = "assign_true_aug" -> "SyntaxError: 'True' is an illegal expression for augmented assignment"
      [] p.case = "attr_none" -> "SyntaxError: invalid syntax"
      [] p.case = "attr_true_read" -> "SyntaxError: invalid syntax"
      [] p.case = "assign_ellipsis" -> "SyntaxError: cannot assign to ellipsis here. Maybe you meant '==' instead of '='?"
      [] p.case = "del_none" -> "SyntaxError: cannot delete None"
      [] p.case = "for_true" -> "SyntaxError: cannot assign to True"
      [] p.case = "param_none" -> "SyntaxError: invalid syntax"
      [] p.case = "kwarg_true" -> "SyntaxError: cannot assign to True"
      [] p.case = "import_as_none" -> "SyntaxError: cannot use None as import target"
      [] p.case = "assign_debug" -> "SyntaxError: cannot assign to __debug__"
      [] p.case = "ellipsis_name" -> "(3, True)"
      [] p.case = "name_bound" -> "[1]"
      [] p.case = "name_unbound" -> "NameError: name 'undefined_name' is not defined"
      [] p.case = "name_deleted" -> "NameError: name 'x' is not defined"
      [] p.case = "literal_int" -> "'int'"
      [] p.case = "literal_float" -> "('float', inf, 0.30000000000000004)"
      [] p.case = "literal_imag" -> "('complex', 0.0, 2.0)"
      [] p.case = "literal_str" -> "'str'"
      [] p.case = "literal_bytes" -> "'bytes'"
      [] p.case = "literal_fstring" -> "'str'"
      [] p.case = "literal_tstring" -> "'Template'"
      [] p.case = "negative_not_literal" -> "(-4, 4)"
      [] p.case = "complex_not_literal" -> "((3+4.2j), 'complex')"
      [] p.case = "same_value" -> "(True, True)"
      [] p.case = "str_equal" -> "True"
      [] p.case = "tstring_distinct" -> "False"
      [] p.case = "tstring_values_shared" -> "(True, True)"
      [] p.case = "tstring_mutable_value" -> "([1],)"
      [] p.case = "literal_immutable_int" -> "'immutable'"
      [] p.case = "literal_immutable_str" -> "\"'str' object does not support item assignment\""
      [] p.case = "literal_immutable_bytes" -> "\"'bytes' object does not support item assignment\""
      [] p.case = "float_approx" -> "True"
      [] p.case = "huge_imag" -> "infj"
      [] p.case = "small_identity_unspecified" -> "True"
      [] p.case = "large_identity_unspecified" -> "True"
      [] p.case = "repeated_evaluation_equal" -> "True"
      [] p.case = "group_value" -> "9"
      [] p.case = "empty_tuple" -> "()"
      [] p.case = "yield_atom_outside" -> "SyntaxError: 'yield' outside function"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* Every keyword constant used as a target is a SyntaxError.
KeywordTargets == {"assign_false", "assign_none", "assign_true_aug", "attr_none", "attr_true_read", "assign_ellipsis",
                   "del_none", "for_true", "param_none", "kwarg_true", "import_as_none", "assign_debug"}
NotAssignable == Done /\ program.case \in KeywordTargets => SubSeq(outcome, 1, 12) = "SyntaxError:"

\* Only the values of literals are guaranteed, never their identity.
IdentityUnspecified == Done /\ program.case \in {"small_identity_unspecified", "large_identity_unspecified"} =>
    outcome = "True"
=============================================================================
