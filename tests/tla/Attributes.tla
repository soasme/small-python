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
(*     subproperty, subraising   the same of a subclass of property       *)
(*     slot       __slots__ = ('a',)                                       *)
(*                                                                         *)
(* with or without a __getattr__ returning 'ga', and with no Python       *)
(* __getattribute__ (hook none), one passing the name to object's (pass), *)
(* or one raising AttributeError (refuse). The steps are o.a,             *)
(* o.a() (each value is callable, returning itself), o.a = v (v is 'v1'   *)
(* or 'v2'), and del o.a; `stored` is what o's                             *)
(* __dict__ or slot holds for a. Each is spelled with the attribute        *)
(* (spelling "attr") or by getattr, setattr and delattr given an instance  *)
(* n of a str subclass (spelling "named"), which answers alike: n itself   *)
(* is the name __getattribute__ and __getattr__ receive, the name of       *)
(* getattr's AttributeError, and the key o.__dict__ binds.                 *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Kinds == {"none", "value", "nondata", "data", "property", "raising", "subproperty", "subraising", "slot"}
\* A property, or an instance of a subclass, with only a getter.
Getters == {"property", "raising", "subproperty", "subraising"}
Values == {"v1", "v2"}
Missing == "missing"

Hooks == {"none", "pass", "refuse"}

Spellings == {"attr", "named"}

VARIABLES kind, getattr, hook, spelling, stored, op, result
vars == <<kind, getattr, hook, spelling, stored, op, result>>

DataDescriptor == kind \in {"data", "slot"} \cup Getters

\* o.a: a data descriptor wins over the instance, which wins over the rest
\* of the class; failing that, on a getter's AttributeError, or when the
\* class's __getattribute__ refuses, __getattr__.
Lookup ==
    CASE kind = "data" -> "dget"
      [] kind \in {"property", "subproperty"} -> "pget"
      [] kind \in {"raising", "subraising"} -> Missing
      [] stored # Missing -> stored
      [] kind = "nondata" -> "nget"
      [] kind = "value" -> "cls"
      [] OTHER -> Missing
Read == IF hook # "refuse" /\ Lookup # Missing THEN Lookup ELSE IF getattr THEN "ga" ELSE "AttributeError"
Get == /\ op' = "get"
       /\ result' = Read
       /\ UNCHANGED <<kind, getattr, hook, spelling, stored>>

\* o.a(): the method call reads o.a as Get does, then calls what it read.
Call == /\ op' = "call"
        /\ result' = Read
        /\ UNCHANGED <<kind, getattr, hook, spelling, stored>>

\* o.a = v: a data descriptor's __set__, otherwise the instance's __dict__.
Set(v) == /\ op' = "set " \o v
          /\ IF kind \in Getters
             THEN result' = "AttributeError" /\ UNCHANGED stored
             ELSE result' = "ok" /\ stored' = v
          /\ UNCHANGED <<kind, getattr, hook, spelling>>

\* del o.a: a data descriptor's __delete__, otherwise the instance's own.
Del == /\ op' = "del"
       /\ CASE kind \in Getters -> result' = "AttributeError" /\ UNCHANGED stored
            [] kind = "data" -> result' = "ok" /\ stored' = Missing
            [] stored # Missing -> result' = "ok" /\ stored' = Missing
            [] OTHER -> result' = "AttributeError" /\ UNCHANGED stored
       /\ UNCHANGED <<kind, getattr, hook, spelling>>

Init == kind \in Kinds /\ getattr \in BOOLEAN /\ hook \in Hooks /\ spelling \in Spellings /\ stored = Missing /\ op = "new" /\ result = "ok"
Next == Get \/ Call \/ Del \/ \E v \in Values : Set(v)
Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
TypeOK == kind \in Kinds /\ getattr \in BOOLEAN /\ hook \in Hooks /\ spelling \in Spellings /\ stored \in Values \cup {Missing}

\* A data descriptor's __get__ answers whatever the instance holds, unless
\* __getattribute__ refuses before it.
DescriptorWins == op = "get" /\ kind \in {"data", "property", "subproperty"} /\ hook # "refuse" => result \in {"dget", "pget"}

\* What is set is what is got, unless a data descriptor intervenes.
SetThenGet == [][(op = "set v1" \/ op = "set v2") /\ result = "ok" /\ ~(kind \in {"data"} \cup Getters) /\ hook # "refuse" /\ op' = "get"
                 => result' = stored]_vars

\* __getattr__ is only consulted when lookup fails, so o.a never fails with it.
GetattrFallback == op \in {"get", "call"} /\ getattr => result # "AttributeError"

\* A read-only property cannot change.
ReadOnly == kind \in Getters => stored = Missing
=============================================================================
