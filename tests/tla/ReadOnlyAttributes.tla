------------------------- MODULE ReadOnlyAttributes -------------------------
(***************************************************************************)
(* Setting and deleting an attribute of an object that has no instance     *)
(* namespace (SLP-315 7.3.8 GenericSetAttr, steps 3 and 4), for a name a   *)
(* that the object's type defines as                                       *)
(*                                                                         *)
(*     member     a read-only member descriptor (complex.real)             *)
(*     getset     a getset descriptor without a setter (memoryview.nbytes) *)
(*     method     a method (list.append)                                   *)
(*     doc        __doc__, which every type's namespace holds              *)
(*     none       nothing                                                  *)
(*                                                                         *)
(* A descriptor's __set__ or __delete__ decides (step 3), raising          *)
(* "readonly attribute" for a member and "attribute 'a' of 'T' objects is  *)
(* not writable" for a getset; any other class attribute is read-only      *)
(* (step 4.1); and a name the type lacks cannot be added (step 4.2). Every *)
(* attempt fails, so a read afterwards sees the original value.            *)
(***************************************************************************)
EXTENDS Naturals

Kinds == {"member", "getset", "method", "doc", "none"}
Ops == {"set", "del"}

VARIABLES kind, op, result, intact
vars == <<kind, op, result, intact>>

Descriptor == kind \in {"member", "getset"}
InType == kind # "none"

Refusal ==
    CASE kind = "member" -> "readonly attribute"
      [] kind = "getset" -> "not writable"
      [] InType -> "read-only"
      [] OTHER -> "no __dict__"

Attempt(o) == /\ op' = o
              /\ result' = Refusal
              /\ UNCHANGED <<kind, intact>>

Init == kind \in Kinds /\ op = "new" /\ result = "ok" /\ intact = TRUE
Next == \E o \in Ops : Attempt(o)
Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
TypeOK == /\ kind \in Kinds /\ op \in Ops \cup {"new"} /\ intact \in BOOLEAN
          /\ result \in {"ok", "readonly attribute", "not writable", "read-only", "no __dict__"}

\* Nothing is ever stored: the object keeps its value.
Intact == intact

\* Setting and deleting fail alike.
SameRefusal == op # "new" => result = Refusal

\* Only a descriptor speaks for itself; otherwise the refusal names the
\* object's type, and step 4.2 applies only to a name the type lacks.
DescriptorMessages == op # "new" /\ result \in {"readonly attribute", "not writable"} => Descriptor
NoDictOnlyWhenAbsent == result = "no __dict__" => ~InType
=============================================================================
