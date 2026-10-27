-------------------------- MODULE SimpleStatements --------------------------
(***************************************************************************)
(* Assignment, augmented assignment, assert, del, and pass, as The Python  *)
(* Language Reference specifies them                                       *)
(* (reference/simple_stmts.html#assignment-statements, #augmented-         *)
(* assignment-statements, #the-assert-statement, #the-pass-statement, and  *)
(* #the-del-statement): an assignment evaluates its expression first, then *)
(* assigns the value to each target list from left to right, each target   *)
(* left to right, unpacking into a list of several targets, where an       *)
(* attribute target evaluates its primary and calls __setattr__ and a      *)
(* subscription its primary and subscript and calls __setitem__; an        *)
(* augmented assignment evaluates its target's primary (and subscript)     *)
(* once, gets the current value, evaluates the expression, and stores the  *)
(* result, in place for a mutable object; del deletes each target from     *)
(* left to right in the same way, a deleted name becoming unbound; assert  *)
(* evaluates its expression and, only when false, its message, raising     *)
(* AssertionError; and the targets each statement accepts are restricted   *)
(* by the grammar.                                                         *)
(*                                                                         *)
(* A program assigns to CHAIN copies of a target list of one or two        *)
(* targets, each a name, an attribute t(o).a<i>, or an item t(r)[t(i)],    *)
(* of a value t('v') (or t((1, 2)) for two targets); or augments one such  *)
(* target by t(1); or deletes one or two targets; or runs one of the       *)
(* CASES. o and r log their attribute and item operations and t logs a     *)
(* value. The outcome is the result's repr or the exception, and the log.  *)
(***************************************************************************)
EXTENDS Naturals, Sequences, TLC

Targets == {"name", "attr", "item"}
TargetLists == UNION {[1..n -> Targets] : n \in 1..2}
Cases == {"chain_names", "swap", "swap_index", "star_target", "star_only", "star_alone", "two_stars", "nested_target",
          "list_target", "slice_assign", "ext_slice_len", "too_many", "too_few", "star_too_few", "not_iterable",
          "assign_literal", "assign_call", "assign_keyword", "assign_debug", "aug_name_unbound", "aug_tuple",
          "aug_star", "aug_list_identity", "aug_tuple_identity", "aug_tuple_item_list", "ann_assign_order",
          "ann_no_value_attr", "ann_tuple", "assert_true", "assert_false", "assert_no_msg", "assert_exc_class",
          "assert_debug", "del_name", "del_unbound", "del_global_missing", "del_nested", "del_slice", "del_star",
          "del_literal", "del_call", "del_local_then_use", "del_free_var", "del_attr_missing", "pass_stmt"}
Programs == [assign : TargetLists, chain : 1..2] \cup [augment : Targets] \cup [delete : TargetLists] \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

R(n) == ToString(n)

\* What storing value v into target kind k at position i logs.
Store(k, i, v) == CASE k = "attr" -> <<"o", "setattr a" \o R(i) \o " " \o v>>
                    [] k = "item" -> <<"r", R(i), "set " \o R(i) \o " " \o v>>
                    [] k = "name" -> <<>>
Delete(k, i) == CASE k = "attr" -> <<"o", "delattr a" \o R(i)>>
                  [] k = "item" -> <<"r", R(i), "del " \o R(i)>>
                  [] k = "name" -> <<>>

RECURSIVE StoreAll(_, _, _), DeleteAll(_, _), Repeat(_, _)
StoreAll(ts, i, vs) == IF i > Len(ts) THEN <<>> ELSE Store(ts[i], i, vs[i]) \o StoreAll(ts, i + 1, vs)
DeleteAll(ts, i) == IF i > Len(ts) THEN <<>> ELSE Delete(ts[i], i) \o DeleteAll(ts, i + 1)
Repeat(s, n) == IF n = 0 THEN <<>> ELSE s \o Repeat(s, n - 1)

Assign(p) ==
    LET single == Len(p.assign) = 1
        values == IF single THEN <<"'v'">> ELSE <<"1", "2">>
    IN  <<"None", <<IF single THEN "'v'" ELSE "(1, 2)">> \o Repeat(StoreAll(p.assign, 1, values), p.chain)>>

\* x op= y: the target's primary (and subscript) once, the old value, y, the store.
Augment(k) == CASE k = "name" -> <<"11", <<"1">>>>
                [] k = "attr" -> <<"None", <<"o", "getattr x", "1", "setattr x 11">>>>
                [] k = "item" -> <<"None", <<"r", "1", "get 1", "1", "set 1 11">>>>

Error(m) == <<m, <<>>>>
Case(c) ==
    CASE c = "chain_names" -> <<"True", <<"[]">>>>                       \* one value bound twice
      [] c = "swap" -> <<"(2, 1)", <<>>>>
      [] c = "swap_index" -> <<"[0, 9]", <<>>>>                          \* i is assigned before l[i]
      [] c = "star_target" -> <<"(0, [1, 2, 3], 4)", <<"range(0, 5)">>>>
      [] c = "star_only" -> <<"['x', 'y']", <<>>>>
      [] c = "star_alone" -> Error("SyntaxError: starred assignment target must be in a list or tuple")
      [] c = "two_stars" -> Error("SyntaxError: multiple starred expressions in assignment")
      [] c = "nested_target" -> <<"(1, 2, 3)", <<>>>>
      [] c = "list_target" -> <<"('x', 'y')", <<>>>>
      [] c = "slice_assign" -> <<"[1, 'a', 'b', 4]", <<>>>>
      [] c = "ext_slice_len" -> Error("ValueError: attempt to assign sequence of size 1 to extended slice of size 2")
      [] c = "too_many" -> Error("ValueError: too many values to unpack (expected 2, got 3)")
      [] c = "too_few" -> Error("ValueError: not enough values to unpack (expected 3, got 2)")
      [] c = "star_too_few" -> Error("ValueError: not enough values to unpack (expected at least 2, got 1)")
      [] c = "not_iterable" -> Error("TypeError: cannot unpack non-iterable int object")
      [] c = "assign_literal" -> Error("SyntaxError: cannot assign to literal here. Maybe you meant '==' instead of '='?")
      [] c = "assign_call" -> Error("SyntaxError: cannot assign to function call here. Maybe you meant '==' instead of '='?")
      [] c = "assign_keyword" -> Error("SyntaxError: cannot assign to None")
      [] c = "assign_debug" -> Error("SyntaxError: cannot assign to __debug__")
      [] c = "aug_name_unbound" -> Error("UnboundLocalError: cannot access local variable 'x' where it is not associated with a value")
      [] c = "aug_tuple" -> Error("SyntaxError: 'tuple' is an illegal expression for augmented assignment")
      [] c = "aug_star" -> Error("SyntaxError: 'starred' is an illegal expression for augmented assignment")
      [] c = "aug_list_identity" -> <<"([1, 2], True)", <<>>>>              \* in place
      [] c = "aug_tuple_identity" -> <<"((1,), False)", <<>>>>             \* a new tuple
      [] c = "aug_tuple_item_list" -> <<"(([1, 2],), \"'tuple' object does not support item assignment\")", <<>>>>
      [] c = "ann_assign_order" -> <<"None", <<"5", "o", "setattr z 5">>>>   \* the annotation is not evaluated
      [] c = "ann_no_value_attr" -> <<"None", <<"o">>>>
      [] c = "ann_tuple" -> Error("SyntaxError: only single target (not tuple) can be annotated")
      [] c = "assert_true" -> <<"'ok'", <<"1">>>>                          \* the message is not evaluated
      [] c = "assert_false" -> <<"AssertionError: msg", <<"0", "'msg'">>>>
      [] c = "assert_no_msg" -> <<"AssertionError: ", <<"[]">>>>
      [] c = "assert_exc_class" -> <<"('AssertionError', ('m',))", <<>>>>
      [] c = "assert_debug" -> <<"True", <<>>>>
      [] c = "del_name" -> Error("NameError: name 'a' is not defined")
      [] c \in {"del_unbound", "del_local_then_use"} ->
            Error("UnboundLocalError: cannot access local variable 'x' where it is not associated with a value")
      [] c = "del_global_missing" -> Error("NameError: name 'nosuchname' is not defined")
      [] c = "del_nested" -> <<"False", <<>>>>
      [] c = "del_slice" -> <<"[2, 4]", <<>>>>
      [] c = "del_star" -> Error("SyntaxError: cannot delete starred")
      [] c = "del_literal" -> Error("SyntaxError: cannot delete literal")
      [] c = "del_call" -> Error("SyntaxError: cannot delete function call")
      [] c = "del_free_var" ->
            Error("NameError: cannot access free variable 'x' where it is not associated with a value in enclosing scope")
      [] c = "del_attr_missing" -> Error("AttributeError: 'P' object has no attribute 'nope'")
      [] c = "pass_stmt" -> <<"'ok'", <<>>>>

Run(p) == CASE "assign" \in DOMAIN p -> Assign(p)
             [] "augment" \in DOMAIN p -> Augment(p.augment)
             [] "delete" \in DOMAIN p -> <<"None", DeleteAll(p.delete, 1)>>
             [] OTHER -> Case(p.case)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* The value of an assignment is evaluated once, before any target.
ValueFirst == Done /\ "assign" \in DOMAIN program => outcome[2][1] \in {"'v'", "(1, 2)"} /\
    \A i \in 2..Len(outcome[2]) : outcome[2][i] \notin {"'v'", "(1, 2)"}

\* Each target of a chained assignment is stored once per copy.
StoresPerCopy == Done /\ "assign" \in DOMAIN program =>
    Len(SelectSeq(outcome[2], LAMBDA e : e \in {"o", "r"})) =
        program.chain * Len(SelectSeq(program.assign, LAMBDA k : k # "name"))
=============================================================================
