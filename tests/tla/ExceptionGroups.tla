-------------------------- MODULE ExceptionGroups ---------------------------
(***************************************************************************)
(* Exception groups, as The Python Standard Library specifies them         *)
(* (library/exceptions.html#exception-groups): BaseExceptionGroup(message, *)
(* exceptions) takes a str and a non-empty sequence of exceptions, copied  *)
(* to a tuple, becoming an ExceptionGroup when all are Exceptions, while   *)
(* ExceptionGroup refuses BaseExceptions; message and exceptions are read- *)
(* only; str() adds the count of sub-exceptions; subgroup() and split()    *)
(* take an exception type, a tuple of them, or a predicate, test the group *)
(* itself first and then each leaf and nested group, keep the nesting of   *)
(* what matches, drop emptied groups, and return None for nothing; the     *)
(* parts are built by derive(), ExceptionGroup's own derive() not keeping  *)
(* a subclass, and copy the original's __traceback__, __cause__,           *)
(* __context__, and __notes__; and except* unwraps matching parts.         *)
(*                                                                         *)
(* A program builds ExceptionGroup('top', items) for one to three items    *)
(* among ValueError, TypeError, a group of ValueError and TypeError        *)
(* ('inner'), and a group of TypeError ('only'), and reports the shape     *)
(* (G(...) for a group, V or T for a leaf, or None) of both parts of       *)
(* split(ValueError) or split(TypeError), of subgroup(ValueError), and of  *)
(* the split by a predicate matching groups named 'inner', or its str();   *)
(* or runs one of the sources of CASES in a fresh namespace. The outcome   *)
(* is that text, or the repr of the case's result, or the exception and    *)
(* its message.                                                            *)
(***************************************************************************)
EXTENDS Integers, Sequences, TLC

VARIABLES program, outcome
vars == <<program, outcome>>

Ops == {"split_value", "split_type", "subgroup_value", "split_pred", "str"}
Children == [GVT |-> <<"V", "T">>, GT |-> <<"T">>]

RECURSIVE JoinC(_)
JoinC(s) == IF Len(s) = 1 THEN Head(s) ELSE Head(s) \o "," \o JoinC(Tail(s))
\* A group of the shapes left, or "" when none is.
Group(shapes) == LET kept == SelectSeq(shapes, LAMBDA x : x # "") IN IF kept = <<>> THEN "" ELSE "G(" \o JoinC(kept) \o ")"

\* The part of an item made of the leaves in keep, nesting kept.
RECURSIVE Kept(_, _)
Kept(item, keep) == IF item \in {"V", "T"} THEN (IF item \in keep THEN item ELSE "")
                    ELSE Group([k \in DOMAIN Children[item] |-> Kept(Children[item][k], keep)])
\* A predicate matching the group named 'inner' takes it whole.
Inner(item, matched) == IF (item = "GVT") = matched THEN Kept(item, {"V", "T"}) ELSE ""

Top(items, keep) == Group([k \in DOMAIN items |-> Kept(items[k], keep)])
TopInner(items, matched) == Group([k \in DOMAIN items |-> Inner(items[k], matched)])
Shown(s) == IF s = "" THEN "None" ELSE s


Cases == {"base_to_exception", "eg_rejects_base", "empty", "not_sequence", "not_exception_item", "message_type",
          "arity", "attributes", "readonly", "repr", "derive_custom", "derive_default_drops_subclass",
          "split_copies_metadata", "split_tuple_types", "split_all_returns_self", "split_group_type",
          "split_bad_arg", "subgroup_none", "str_count", "except_star_unwrap", "nested_traceback_kept",
          "generic_alias", "list_copied"}
Programs == [op : Ops, items : UNION {[1..n -> {"V", "T", "GVT", "GT"}] : n \in 1..3}]
            \cup [case : Cases]

Pending == "pending"

Generated(p) ==
    LET items == p.items IN
    CASE p.op = "split_value" -> Shown(Top(items, {"V"})) \o " " \o Shown(Top(items, {"T"}))
      [] p.op = "split_type" -> Shown(Top(items, {"T"})) \o " " \o Shown(Top(items, {"V"}))
      [] p.op = "subgroup_value" -> Shown(Top(items, {"V"}))
      [] p.op = "split_pred" -> Shown(TopInner(items, TRUE)) \o " " \o Shown(TopInner(items, FALSE))
      [] p.op = "str" -> "top (" \o ToString(Len(items)) \o (IF Len(items) = 1 THEN " sub-exception)" ELSE " sub-exceptions)")

Case(c) ==
    CASE c = "base_to_exception" -> "('ExceptionGroup', 'BaseExceptionGroup')"
      [] c = "eg_rejects_base" -> "TypeError: Cannot nest BaseExceptions in an ExceptionGroup"
      [] c = "empty" -> "ValueError: second argument (exceptions) must be a non-empty sequence"
      [] c = "not_sequence" -> "TypeError: second argument (exceptions) must be a sequence"
      [] c = "not_exception_item" -> "ValueError: Item 0 of second argument (exceptions) is not an exception"
      [] c = "message_type" -> "TypeError: BaseExceptionGroup.__new__() argument 1 must be str, not int"
      [] c = "arity" -> "TypeError: BaseExceptionGroup.__new__() takes exactly 2 arguments (1 given)"
      [] c = "attributes" -> "('m', 'tuple', 'm', 'list')"
      [] c = "readonly" -> "AttributeError: readonly attribute"
      [] c = "repr" -> "\"ExceptionGroup('m', [ValueError(1), TypeError(2)])\""
      [] c = "derive_custom" -> "('MyEG', 'm!', 'm!')"
      [] c = "derive_default_drops_subclass" -> "('ExceptionGroup', 'ExceptionGroup')"
      [] c = "split_copies_metadata" -> "(['n'], 'KeyError', False)"
      [] c = "split_tuple_types" -> "(2, 1)"
      [] c = "split_all_returns_self" -> "(False, None)"
      [] c = "split_group_type" -> "(True, None)"
      [] c = "split_bad_arg" -> "TypeError: expected an exception type, a tuple of exception types, or a callable (other than a class)"
      [] c = "subgroup_none" -> "None"
      [] c = "str_count" -> "('m (1 sub-exception)', 'm (2 sub-exceptions)')"
      [] c = "except_star_unwrap" -> "('ExceptionGroup', 1)"
      [] c = "nested_traceback_kept" -> "None"
      [] c = "generic_alias" -> "'ExceptionGroup[ValueError]'"
      [] c = "list_copied" -> "1"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* The two parts of a split partition the leaves: whatever is kept is
\* missing from the rest, and the whole group is one of them only when the
\* other is None.
Partition == Done /\ "op" \in DOMAIN program =>
    LET items == program.items IN
    /\ Top(items, {"V", "T"}) # ""
    /\ (Top(items, {"V"}) = Top(items, {"V", "T"})) => Top(items, {"T"}) = ""
    /\ (Top(items, {"T"}) = Top(items, {"V", "T"})) => Top(items, {"V"}) = ""
=============================================================================
