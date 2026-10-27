----------------------------- MODULE Constants ------------------------------
(***************************************************************************)
(* Built-in constants, as The Python Standard Library specifies them       *)
(* (library/constants.html, with                                           *)
(* reference/lexical_analysis.html#keywords): None, False, and True are    *)
(* keywords, so binding, deleting, or naming them in any target position   *)
(* is a SyntaxError, as is binding or deleting __debug__ (its global       *)
(* declaration aside), even as an attribute; Ellipsis and NotImplemented   *)
(* are ordinary builtins names that can be shadowed; None, NotImplemented, *)
(* and Ellipsis (...) are the sole instances of their types, whose         *)
(* constructors return them and take no arguments; NotImplemented returned *)
(* by a binary special method makes the interpreter try the reflected      *)
(* operation and then the fallback, and is an error in a boolean context;  *)
(* and __debug__ is True without -O.                                       *)
(*                                                                         *)
(* A program compiles one of the statements of CONTEXTS (assignment,       *)
(* augmented and annotated assignment, del, for, with, parameter, keyword  *)
(* argument, assignment expression, import as, def, class, attribute,      *)
(* lambda, global, except as, starred, and comprehension targets) with a   *)
(* NAME among None, True, False, __debug__, Ellipsis, NotImplemented, and  *)
(* x in the target position; or runs one of the sources of CASES in a      *)
(* fresh namespace. The outcome is ok or the SyntaxError's message, or the *)
(* repr of the case's result, or the exception and its message.            *)
(***************************************************************************)
EXTENDS Sequences

VARIABLES program, outcome
vars == <<program, outcome>>

Names == {"None", "True", "False", "__debug__", "Ellipsis", "NotImplemented", "x"}
Keywords == {"None", "True", "False"}
Contexts == {"assign", "augassign", "annotated", "delete", "for", "with", "param", "keyword", "walrus",
             "import_as", "def", "class", "attribute", "lambda", "global", "except_as", "starred", "comprehension"}
\* Contexts in which the grammar admits only a NAME token, never a keyword.
NameOnly == {"param", "def", "class", "attribute", "lambda", "global"}


Cases == {"assign_none", "assign_true", "assign_false_attr", "assign_debug", "del_debug", "debug_param", "debug_kw",
          "none_kw", "debug_value", "assert_runs", "none_type", "none_type_args", "ni_type", "ni_bool",
          "ni_reflected", "ni_both", "ni_identity_fallback", "ni_ordering", "ellipsis", "ellipsis_bool",
          "true_false", "bool_subclass", "builtins_name", "hash_singletons", "keyword_shadow",
          "builtins_dict", "assign_ellipsis_name", "assign_ni_name", "debug_walrus", "true_walrus",
          "none_import_as", "debug_import_as", "debug_for", "debug_class", "debug_attr_ok",
          "debug_global_ok_getattr"}
Programs == [name : Names, context : Contexts]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    LET n == p.name  k == p.context IN
    CASE n \in Keywords /\ k \in NameOnly -> "SyntaxError: invalid syntax"
      [] n \in Keywords /\ k = "augassign" -> "SyntaxError: '" \o n \o "' is an illegal expression for augmented assignment"
      [] n \in Keywords /\ k = "annotated" -> "SyntaxError: illegal target for annotation"
      [] n \in Keywords /\ k = "walrus" -> "SyntaxError: cannot use assignment expressions with " \o n
      [] n \in Keywords /\ k = "import_as" -> "SyntaxError: cannot use " \o n \o " as import target"
      [] n \in Keywords /\ k = "except_as" -> "SyntaxError: cannot use except statement with " \o n
      [] n \in Keywords \cup {"__debug__"} /\ k = "delete" -> "SyntaxError: cannot delete " \o n
      [] n \in Keywords -> "SyntaxError: cannot assign to " \o n
      [] n = "__debug__" /\ k # "global" -> "SyntaxError: cannot assign to __debug__"
      [] OTHER -> "ok"

Case(c) ==
    CASE c = "assign_none" -> "SyntaxError: cannot assign to None"
      [] c = "assign_true" -> "SyntaxError: cannot assign to True"
      [] c = "assign_false_attr" -> "SyntaxError: invalid syntax"
      [] c = "assign_debug" -> "SyntaxError: cannot assign to __debug__"
      [] c = "del_debug" -> "SyntaxError: cannot delete __debug__"
      [] c = "debug_param" -> "SyntaxError: cannot assign to __debug__"
      [] c = "debug_kw" -> "SyntaxError: cannot assign to __debug__"
      [] c = "none_kw" -> "SyntaxError: cannot assign to None"
      [] c = "debug_value" -> "(True, 'bool')"
      [] c = "assert_runs" -> "('m',)"
      [] c = "none_type" -> "(None, 'NoneType', True)"
      [] c = "none_type_args" -> "TypeError: NoneType takes no arguments"
      [] c = "ni_type" -> "(True, 'NotImplemented', 'NotImplementedType')"
      [] c = "ni_bool" -> "TypeError: NotImplemented should not be used in a boolean context"
      [] c = "ni_reflected" -> "'B.eq'"
      [] c = "ni_both" -> "(False, True)"
      [] c = "ni_identity_fallback" -> "(True, False)"
      [] c = "ni_ordering" -> "TypeError: '<' not supported between instances of 'A' and 'A'"
      [] c = "ellipsis" -> "(True, 'Ellipsis', 'ellipsis', True, 'Ellipsis')"
      [] c = "ellipsis_bool" -> "True"
      [] c = "true_false" -> "(2, 0, 'True', True, 'int')"
      [] c = "bool_subclass" -> "TypeError: type 'bool' is not an acceptable base type"
      [] c = "builtins_name" -> "('NoneType', 'NotImplementedType', 'ellipsis')"
      [] c = "hash_singletons" -> "(True, True, True)"
      [] c = "keyword_shadow" -> "True"
      [] c = "builtins_dict" -> "(True, True, True, True)"
      [] c = "assign_ellipsis_name" -> "(1, True)"
      [] c = "assign_ni_name" -> "2"
      [] c = "debug_walrus" -> "SyntaxError: cannot assign to __debug__"
      [] c = "true_walrus" -> "SyntaxError: cannot use assignment expressions with True"
      [] c = "none_import_as" -> "SyntaxError: cannot use None as import target"
      [] c = "debug_import_as" -> "SyntaxError: cannot assign to __debug__"
      [] c = "debug_for" -> "SyntaxError: cannot assign to __debug__"
      [] c = "debug_class" -> "SyntaxError: cannot assign to __debug__"
      [] c = "debug_attr_ok" -> "SyntaxError: cannot assign to __debug__"
      [] c = "debug_global_ok_getattr" -> "True"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* Only the keywords and __debug__ are protected; any other name binds,
\* and __debug__ may still be declared global.
Protected == Done /\ "name" \in DOMAIN program =>
    (outcome = "ok" <=> program.name \notin Keywords \cup {"__debug__"}
                      \/ (program.name = "__debug__" /\ program.context = "global"))
=============================================================================
