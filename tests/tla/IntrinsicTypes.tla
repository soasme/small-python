--------------------------- MODULE IntrinsicTypes ---------------------------
(***************************************************************************)
(* The standard interpreter types, as The Python Standard Library          *)
(* specifies them (library/types.html#standard-interpreter-types): each    *)
(* name of the types module is the type of the objects it describes,       *)
(* defined in builtins except GenericAlias (types) and UnionType (typing); *)
(* LambdaType is FunctionType and BuiltinMethodType is                     *)
(* BuiltinFunctionType; MethodType, ModuleType, CellType, FunctionType,    *)
(* and MappingProxyType construct their objects, a mapping proxy being a   *)
(* read-only live view of its mapping; NoneType and NotImplementedType     *)
(* return their singletons; the method, wrapper, class-method, getset, and *)
(* member descriptors bind and check their owner class; tracebacks and     *)
(* frames link to their neighbors; and generator and function types        *)
(* neither construct nor subclass.                                         *)
(*                                                                         *)
(* A program makes a sample object for each name of NAMES and reports its  *)
(* type's __name__, whether the name is that type, the type's __module__,  *)
(* and whether the sample is an instance of the name; or runs one of the   *)
(* sources of CASES in a fresh namespace. The outcome is the repr of that  *)
(* tuple or of the case's result, or the exception and its message.        *)
(***************************************************************************)
EXTENDS Integers, Sequences

VARIABLES program, outcome
vars == <<program, outcome>>

Kind == [FunctionType |-> "function", LambdaType |-> "function", GeneratorType |-> "generator",
         CoroutineType |-> "coroutine", AsyncGeneratorType |-> "async_generator", CodeType |-> "code",
         CellType |-> "cell", MethodType |-> "method", BuiltinFunctionType |-> "builtin_function_or_method",
         BuiltinMethodType |-> "builtin_function_or_method", WrapperDescriptorType |-> "wrapper_descriptor",
         MethodWrapperType |-> "method-wrapper", NotImplementedType |-> "NotImplementedType",
         MethodDescriptorType |-> "method_descriptor", ClassMethodDescriptorType |-> "classmethod_descriptor",
         ModuleType |-> "module", TracebackType |-> "traceback", FrameType |-> "frame",
         GetSetDescriptorType |-> "getset_descriptor", MemberDescriptorType |-> "member_descriptor",
         MappingProxyType |-> "mappingproxy", EllipsisType |-> "ellipsis", NoneType |-> "NoneType",
         GenericAlias |-> "GenericAlias", UnionType |-> "Union", FrameLocalsProxyType |-> "FrameLocalsProxy"]
Module(n) == CASE n = "GenericAlias" -> "types" [] n = "UnionType" -> "typing" [] OTHER -> "builtins"


Cases == {"method_ctor", "method_not_callable", "module_ctor", "module_bad_name", "cell_empty", "cell_set",
          "cell_shared", "proxy_readonly", "proxy_live", "proxy_bad", "proxy_or", "proxy_copy",
          "class_dict_proxy", "function_ctor", "code_replace", "notimplemented_ctor", "none_ctor",
          "classmethod_descr_repr", "classmethod_descr_call", "classmethod_descr_get",
          "classmethod_descr_instance", "classmethod_descr_objclass", "classmethod_descr_no_arg",
          "classmethod_descr_not_type", "classmethod_descr_not_subtype", "getset_get", "getset_readonly",
          "member_unset", "member_set", "method_descr_wrong_type", "method_descr_objclass",
          "wrapper_descr_call", "method_wrapper_self", "builtin_self", "generator_no_ctor",
          "function_no_subclass", "traceback_fields", "frame_back"}
Programs == [name : DOMAIN Kind]
            \cup [case : Cases]

Pending == "pending"

Generated(p) == "('" \o Kind[p.name] \o "', True, '" \o Module(p.name) \o "', True)"

Case(c) ==
    CASE c = "method_ctor" -> "(True, True, 1)"
      [] c = "method_not_callable" -> "TypeError: first argument must be callable"
      [] c = "module_ctor" -> "('m', 'doc', 1, \"<module 'm'>\")"
      [] c = "module_bad_name" -> "TypeError: module() argument 'name' must be str, not int"
      [] c = "cell_empty" -> "ValueError: Cell is empty"
      [] c = "cell_set" -> "2"
      [] c = "cell_shared" -> "5"
      [] c = "proxy_readonly" -> "TypeError: 'mappingproxy' object does not support item assignment"
      [] c = "proxy_live" -> "(2, 2, True, 0)"
      [] c = "proxy_bad" -> "TypeError: mappingproxy() argument must be a mapping, not list"
      [] c = "proxy_or" -> "{'a': 1, 'b': 2}"
      [] c = "proxy_copy" -> "('dict', {'a': 1})"
      [] c = "class_dict_proxy" -> "TypeError: 'mappingproxy' object does not support item assignment"
      [] c = "function_ctor" -> "(5, 'g')"
      [] c = "code_replace" -> "'g'"
      [] c = "notimplemented_ctor" -> "True"
      [] c = "none_ctor" -> "True"
      [] c = "classmethod_descr_repr" -> "\"<method 'fromkeys' of 'dict' objects>\""
      [] c = "classmethod_descr_call" -> "{'a': None, 'b': None}"
      [] c = "classmethod_descr_get" -> "{'a': None}"
      [] c = "classmethod_descr_instance" -> "{'x': None}"
      [] c = "classmethod_descr_objclass" -> "(True, 'fromkeys', 'dict.fromkeys', True)"
      [] c = "classmethod_descr_no_arg" -> "TypeError: descriptor 'fromkeys' of 'dict' object needs an argument"
      [] c = "classmethod_descr_not_type" -> "TypeError: descriptor 'fromkeys' for type 'dict' needs a type, not a 'int' as arg 2"
      [] c = "classmethod_descr_not_subtype" -> "TypeError: descriptor 'fromkeys' requires a subtype of 'dict' but received 'int'"
      [] c = "getset_get" -> "3"
      [] c = "getset_readonly" -> "AttributeError: attribute 'real' of 'int' objects is not writable"
      [] c = "member_unset" -> "AttributeError: 'S' object has no attribute 'a'"
      [] c = "member_set" -> "(7, 'a', True)"
      [] c = "method_descr_wrong_type" -> "TypeError: descriptor 'join' for 'str' objects doesn't apply to a 'int' object"
      [] c = "method_descr_objclass" -> "(True, 'join', 'str.join')"
      [] c = "wrapper_descr_call" -> "('ab', True)"
      [] c = "method_wrapper_self" -> "(True, '__str__')"
      [] c = "builtin_self" -> "('builtins', True)"
      [] c = "generator_no_ctor" -> "TypeError: cannot create 'generator' instances"
      [] c = "function_no_subclass" -> "TypeError: type 'function' is not an acceptable base type"
      [] c = "traceback_fields" -> "('<module>', 'f', None)"
      [] c = "frame_back" -> "'g'"

Run(p) == IF "case" \in DOMAIN p THEN Case(p.case) ELSE Generated(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
\* The aliases name the same type as what they alias.
Aliases == Kind["LambdaType"] = Kind["FunctionType"] /\ Kind["BuiltinMethodType"] = Kind["BuiltinFunctionType"]
\* Every name is the type of its sample.
Identity == Done /\ "name" \in DOMAIN program => outcome = Generated(program)
=============================================================================
