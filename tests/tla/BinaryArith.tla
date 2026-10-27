---------------------------- MODULE BinaryArith ----------------------------
(***************************************************************************)
(* Binary and unary arithmetic, as The Python Language Reference and the   *)
(* built-in types chapter specify them                                     *)
(* (reference/expressions.html#arithmetic-conversions, #the-power-         *)
(* operator, #unary-arithmetic-and-bitwise-operations, and #binary-        *)
(* arithmetic-operations, library/stdtypes.html#numeric-types-int-float-   *)
(* complex, with reference/datamodel.html#emulating-numeric-types): x op y *)
(* calls x's __op__ and, if it is missing or returns NotImplemented, y's   *)
(* __rop__ (when y's type differs), calling y's __rop__ first when y's     *)
(* type is a subclass of x's that overrides it; x op= y first tries x's    *)
(* __iop__; when all decline the operation raises TypeError naming the     *)
(* operator (op= for an augmented assignment, "** or pow()" for a power)   *)
(* and both types; a number of a narrower type is widened (int to float to *)
(* complex) before a built-in operation, true division of ints is a float, *)
(* floor division and modulo follow the divisor's sign, a negative power   *)
(* of an int is a float and of a negative float a fractional power is      *)
(* complex, zero to a negative power and division by zero raise            *)
(* ZeroDivisionError, results too large for a float raise OverflowError,   *)
(* and types without an operator (complex with //, %, and bitwise ones,    *)
(* float with bitwise ones, every number with @) decline it; three-        *)
(* argument pow() tries each operand's power, int's needing ints, float's  *)
(* and complex's refusing a modulus.                                       *)
(*                                                                         *)
(* A program evaluates x OP y (or x OP= y) for an instance x of class A    *)
(* and y of class B, where B is unrelated to A, a subclass of it, or A     *)
(* itself (RELATION), and each class has KIND: no arithmetic methods,      *)
(* __op__ and __rop__ for every operator returning the description of the  *)
(* call ("A.__add__(L)" for A's __add__ on the left operand) or            *)
(* NotImplemented, only the __rop__ methods, or only the __iop__ methods;  *)
(* or it runs one of the CASES. The outcome is the result's repr (<self>   *)
(* if an augmented assignment kept x) or the exception, and the methods    *)
(* called.                                                                 *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Ops == {"+", "-", "*", "@", "**", "<<", "+=", "*="}
Kinds == {"none", "value", "notimpl", "rop_only", "iop"}
Cases == {"int_float", "true_div", "floor_div", "mod_sign", "divmod", "complex_mix", "complex_floordiv", "complex_mod",
          "bool_arith", "int_div_zero", "int_floordiv_zero", "int_mod_zero", "float_div_zero", "float_mod_zero",
          "complex_div_zero", "pow_neg", "pow_frac_neg", "pow_zero_neg", "pow_zero_neg_float", "pow_precedence",
          "pow_overflow", "pow_float_neg_frac", "int_to_float_overflow", "int_true_div_big", "int_true_div_overflow",
          "unary_str", "unary_neg_list", "unary_invert_float", "unary_ops", "str_mul", "str_mul_float",
          "str_add_int", "list_add_tuple", "int_add_str", "matmul_int", "float_floor_big", "nan_inf", "shift_neg",
          "shift_float", "bitwise_float", "big_mul", "complex_zero_power", "complex_overflow", "complex_matmul",
          "bool_matmul", "complex_shift", "divmod_complex", "complex_zero_div", "pow3_instance", "pow3_methods",
          "pow3_float", "pow3_complex", "pow3_zero", "pow3_inverse", "inplace_messages", "inplace_pow_message"}
Programs == [op : Ops, left : Kinds, right : Kinds, relation : {"unrelated", "sub"}]
            \cup [op : Ops, left : Kinds, right : {"same"}, relation : {"same"}]
            \cup [case : Cases]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<"pending">>

Name == [o \in Ops |-> CASE o \in {"+", "+="} -> "add" [] o = "-" -> "sub" [] o \in {"*", "*="} -> "mul"
                         [] o = "@" -> "matmul" [] o = "**" -> "pow" [] o = "<<" -> "lshift"]
Augmented(o) == o \in {"+=", "*="}

Defines(kind, prefix) == CASE kind \in {"value", "notimpl"} -> prefix \in {"", "r"}
                           [] kind = "rop_only" -> prefix = "r"
                           [] kind = "iop" -> prefix = "i"
                           [] OTHER -> FALSE
RightKind(p) == IF p.relation = "same" THEN p.left ELSE p.right

\* Where an instance of cls finds its __<prefix>op__: B, then A when B
\* subclasses A (an instance of A when both operands are A's).
Owner(p, cls, prefix) ==
    IF cls = "B" /\ p.relation # "same" /\ Defines(p.right, prefix) THEN "B"
    ELSE IF (cls = "A" \/ p.relation = "sub") /\ Defines(p.left, prefix) THEN "A"
    ELSE "none"

Method(p, prefix) == "__" \o prefix \o Name[p.op] \o "__"
Call(p, cls, side, prefix) ==
    LET owner == Owner(p, cls, prefix)  entry == owner \o "." \o Method(p, prefix) \o "(" \o side \o ")"
    IN  IF owner = "none" THEN <<"NI", <<>>>>
        ELSE <<IF (IF owner = "A" THEN p.left ELSE p.right) = "notimpl" THEN "NI" ELSE "'" \o entry \o "'",
               <<entry>>>>

Arith(p) ==
    LET B == IF p.relation = "same" THEN "A" ELSE "B"
        inplace == IF Augmented(p.op) THEN Call(p, "A", "L", "i") ELSE <<"NI", <<>>>>
        \* y's __rop__ runs first when B subclasses A and overrides it.
        overrides == p.relation = "sub" /\ Owner(p, "B", "r") = "B"
        forward == Call(p, "A", "L", "")
        reflected == IF p.relation = "same" THEN <<"NI", <<>>>> ELSE Call(p, B, "R", "r")
        first == IF overrides THEN reflected ELSE forward
        second == IF overrides THEN forward ELSE reflected
        symbol == IF p.op = "**" THEN "** or pow()" ELSE p.op
        failure == "TypeError: unsupported operand type(s) for " \o symbol \o ": 'A' and '" \o B \o "'"
    IN  CASE inplace[1] # "NI" -> inplace
          [] first[1] # "NI" -> <<first[1], inplace[2] \o first[2]>>
          [] second[1] # "NI" -> <<second[1], inplace[2] \o first[2] \o second[2]>>
          [] OTHER -> <<failure, inplace[2] \o first[2] \o second[2]>>

Unsupported(op, a, b) == "TypeError: unsupported operand type(s) for " \o op \o ": '" \o a \o "' and '" \o b \o "'"
Case(c) ==
    CASE c = "int_float" -> "(2.0, 'float', 1.5)"
      [] c = "true_div" -> "(3.5, 2.0, 'float')"
      [] c = "floor_div" -> "(3, -4, -4, 3.0, -4.0)"
      [] c = "mod_sign" -> "(1, 2, -2, 0.5, -0.5, 0.0)"                  \* the divisor's sign
      [] c = "divmod" -> "((-4, 1), (-4.0, -0.5))"
      [] c = "complex_mix" -> "((1+2j), 3j, (5+5j), 'complex')"
      [] c = "complex_floordiv" -> Unsupported("//", "complex", "int")
      [] c = "complex_mod" -> Unsupported("%", "complex", "int")
      [] c = "bool_arith" -> "(2, 3.5, -1, -1, 0.5, 'int')"
      [] c \in {"int_div_zero", "int_floordiv_zero", "int_mod_zero", "float_div_zero", "float_mod_zero",
                "complex_div_zero", "complex_zero_div"} -> "ZeroDivisionError: division by zero"
      [] c = "pow_neg" -> "(0.5, 'float', 1, 1)"
      [] c = "pow_frac_neg" -> "'complex'"
      [] c \in {"pow_zero_neg", "pow_zero_neg_float"} -> "ZeroDivisionError: zero to a negative power"
      [] c = "pow_precedence" -> "(-4, 0.5, 512, 4)"                      \* binds tighter than unary minus on its left
      [] c = "pow_overflow" -> "OverflowError: (34, 'Result too large')"
      [] c = "pow_float_neg_frac" -> "(1.7319121124709868e-16+2.8284271247461903j)"
      [] c = "int_to_float_overflow" -> "OverflowError: int too large to convert to float"
      [] c = "int_true_div_big" -> "10.0"
      [] c = "int_true_div_overflow" -> "OverflowError: integer division result too large for a float"
      [] c = "unary_str" -> "TypeError: bad operand type for unary +: 'str'"
      [] c = "unary_neg_list" -> "TypeError: bad operand type for unary -: 'list'"
      [] c = "unary_invert_float" -> "TypeError: bad operand type for unary ~: 'float'"
      [] c = "unary_ops" -> "(3, 3.5, -6, -0.0, 2)"
      [] c = "str_mul" -> "('abab', 'abab', [0, 0, 0], '', 'a')"
      [] c = "str_mul_float" -> "TypeError: can't multiply sequence by non-int of type 'float'"
      [] c = "str_add_int" -> "TypeError: can only concatenate str (not \"int\") to str"
      [] c = "list_add_tuple" -> "TypeError: can only concatenate list (not \"tuple\") to list"
      [] c = "int_add_str" -> Unsupported("+", "int", "str")
      [] c = "matmul_int" -> Unsupported("@", "int", "int")
      [] c = "float_floor_big" -> "(True, 49.0)"
      [] c = "nan_inf" -> "(nan, nan, 0.0)"
      [] c = "shift_neg" -> "ValueError: negative shift count"
      [] c = "shift_float" -> Unsupported("<<", "int", "float")
      [] c = "bitwise_float" -> Unsupported("&", "int", "float")
      [] c = "big_mul" -> "(340282366920938463463374607431768211456, 9223372036854775808, 1)"
      [] c = "complex_zero_power" -> "ZeroDivisionError: zero to a negative or complex power"
      [] c = "complex_overflow" -> "OverflowError: complex exponentiation"
      [] c = "complex_matmul" -> Unsupported("@", "complex", "complex")
      [] c = "bool_matmul" -> Unsupported("@", "bool", "bool")
      [] c = "complex_shift" -> Unsupported("<<", "complex", "int")
      [] c = "divmod_complex" -> Unsupported("divmod()", "complex", "int")
      [] c = "pow3_instance" -> "TypeError: unsupported operand type(s) for ** or pow(): 'A', 'int', 'int'"
      [] c = "pow3_methods" -> "(('P', 2, 3), ('rP', 2, 3))"               \* __rpow__ takes a modulus too
      [] c = "pow3_float" -> "TypeError: pow() 3rd argument not allowed unless all arguments are integers"
      [] c = "pow3_complex" -> "ValueError: complex modulo"
      [] c = "pow3_zero" -> "ValueError: pow() 3rd argument cannot be 0"
      [] c = "pow3_inverse" -> "(3, 'ValueError: base is not invertible for the given modulus')"
      [] c = "inplace_messages" -> "TypeError: unsupported operand type(s) for <<=: 'A' and 'int'"
      [] c = "inplace_pow_message" -> "TypeError: unsupported operand type(s) for **=: 'int' and 'str'"

Run(p) == IF "case" \in DOMAIN p THEN <<Case(p.case), <<>>>> ELSE Arith(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
IsArith == Done /\ "op" \in DOMAIN program

\* At most an __iop__, an __op__, and an __rop__ run, each once.
AtMostThree == IsArith => Len(outcome[2]) <= 3 /\ \A i, j \in DOMAIN outcome[2] : i # j => outcome[2][i] # outcome[2][j]

\* With both operands of one class, the reflected method never runs.
NoReflectionOnSameType == IsArith /\ program.relation = "same" =>
    \A i \in DOMAIN outcome[2] : outcome[2][i] \notin {"A.__r" \o Name[program.op] \o "__(R)"}
=============================================================================
