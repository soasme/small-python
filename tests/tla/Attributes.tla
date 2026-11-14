---------------------------- MODULE Attributes ----------------------------
(***************************************************************************)
(* Getting, setting, and deleting an instance attribute, as The Python     *)
(* Language Reference specifies it (reference/datamodel.html#customizing-  *)
(* attribute-access and #implementing-descriptors), for an object o of a   *)
(* class whose attribute a is                                              *)
(*                                                                         *)
(*     none       not defined                                              *)
(*     value      a = 'cls'                                                *)
(*     nondata    a descriptor with only __get__, returning 'nget'         *)
(*     data       a descriptor whose __get__ returns 'dget', whose         *)
(*                __set__ stores into o.__dict__, and whose __delete__     *)
(*                removes it from there                                    *)
(*     property   a property with only a getter, returning 'pget'          *)
(*     raising    a property with only a getter, raising AttributeError    *)
(*     slot       __slots__ = ('a',)                                       *)
(*                                                                         *)
(* with or without a __getattr__ returning 'ga', and with no Python       *)
(* __getattribute__ (hook none), one passing the name to object's (pass), *)
(* or one raising AttributeError (refuse). The steps are o.a,             *)
(* o.a = v (v is 'v1' or 'v2'), and del o.a; `stored` is what o's          *)
(* __dict__ or slot holds for a.                                           *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Kinds == {"none", "value", "nondata", "data", "property", "raising", "slot"}
Values == {"v1", "v2"}
Missing == "missing"

Hooks == {"none", "pass", "refuse"}

VARIABLES kind, getattr, hook, stored, op, result
vars == <<kind, getattr, hook, stored, op, result>>

DataDescriptor == kind \in {"data", "property", "raising", "slot"}

\* o.a: a data descriptor wins over the instance, which wins over the rest
\* of the class; failing that, on a getter's AttributeError, or when the
\* class's __getattribute__ refuses, __getattr__.
Lookup ==
    CASE kind = "data" -> "dget"
      [] kind = "property" -> "pget"
      [] kind = "raising" -> Missing
      [] stored # Missing -> stored
      [] kind = "nondata" -> "nget"
      [] kind = "value" -> "cls"
      [] OTHER -> Missing
Get == /\ op' = "get"
       /\ result' = IF hook # "refuse" /\ Lookup # Missing THEN Lookup ELSE IF getattr THEN "ga" ELSE "AttributeError"
       /\ UNCHANGED <<kind, getattr, hook, stored>>

\* o.a = v: a data descriptor's __set__, otherwise the instance's __dict__.
Set(v) == /\ op' = "set " \o v
          /\ IF kind \in {"property", "raising"}
             THEN result' = "AttributeError" /\ UNCHANGED stored
             ELSE result' = "ok" /\ stored' = v
          /\ UNCHANGED <<kind, getattr, hook>>

\* del o.a: a data descriptor's __delete__, otherwise the instance's own.
Del == /\ op' = "del"
       /\ CASE kind \in {"property", "raising"} -> result' = "AttributeError" /\ UNCHANGED stored
            [] kind = "data" -> result' = "ok" /\ stored' = Missing
            [] stored # Missing -> result' = "ok" /\ stored' = Missing
            [] OTHER -> result' = "AttributeError" /\ UNCHANGED stored
       /\ UNCHANGED <<kind, getattr, hook>>

Init == kind \in Kinds /\ getattr \in BOOLEAN /\ hook \in Hooks /\ stored = Missing /\ op = "new" /\ result = "ok"
Next == Get \/ Del \/ \E v \in Values : Set(v)
Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
TypeOK == kind \in Kinds /\ getattr \in BOOLEAN /\ hook \in Hooks /\ stored \in Values \cup {Missing}

\* A data descriptor's __get__ answers whatever the instance holds, unless
\* __getattribute__ refuses before it.
DescriptorWins == op = "get" /\ kind \in {"data", "property"} /\ hook # "refuse" => result \in {"dget", "pget"}

\* What is set is what is got, unless a data descriptor intervenes.
SetThenGet == [][(op = "set v1" \/ op = "set v2") /\ result = "ok" /\ ~(kind \in {"data", "property", "raising"}) /\ hook # "refuse" /\ op' = "get"
                 => result' = stored]_vars

\* __getattr__ is only consulted when lookup fails, so o.a never fails with it.
GetattrFallback == op = "get" /\ getattr => result # "AttributeError"

\* A read-only property cannot change.
ReadOnly == kind \in {"property", "raising"} => stored = Missing
=============================================================================
