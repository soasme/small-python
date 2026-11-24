------------------------------- MODULE Super -------------------------------
(***************************************************************************)
(* Cooperative method calls through super(), as Python specifies them      *)
(* (library/functions.html#super: it searches the MRO of the instance's    *)
(* type, starting after the class the method was defined in), for the      *)
(* diamond                                                                 *)
(*                                                                         *)
(*     class A: ...                                                        *)
(*     class B(A): ...                                                     *)
(*     class C(A): ...                                                     *)
(*     class D(B, C): ...                                                  *)
(*                                                                         *)
(* where each class's m is                                                 *)
(*                                                                         *)
(*     none     not defined                                                *)
(*     stop     def m(self): log.append(<name>)                            *)
(*     super    def m(self): log.append(<name>); super().m()               *)
(*                                                                         *)
(* and the program calls X().m() for one of the classes X. The outcome is  *)
(* the log, and AttributeError if a lookup found no m (object has none).   *)
(* The method may instead be named __get__, called with None, each super   *)
(* call passing self: a super object finds a class's __get__ before its    *)
(* own, which answers when no class after the start has one. Or it may be *)
(* a property p, whose getter reads super().p, as m calls super().m().     *)
(* The receiver may instead be a proxy, an object of another class whose   *)
(* __class__ property loops, then answers X: X's method called on it       *)
(* (X.m(proxy), X.p.fget(proxy)) reads that __class__ at each super()     *)
(* and runs as on an instance of X.                                        *)
(*                                                                         *)
(* Or the program calls super() with no arguments in a frame (op "frame") *)
(* whose code has no positional parameter: a lambda nested in a method,   *)
(*  (lambda: super())() , or a generic class's bases, which run in its    *)
(* type parameters' scope,  class G[T](super()): pass . Both raise        *)
(* RuntimeError "super(): no arguments"; a method's own super() does not. *)
(*                                                                         *)
(* Or it binds a super object by the slot super.__get__ (op "bind"): one  *)
(* of super or of a subclass S whose __init__ logs, unbound or bound, to  *)
(* an instance or None. An unbound one binds to the instance, S's by      *)
(* calling S; otherwise the object itself is the result. Or it reads      *)
(* __prepare__ of a class whose metaclass's metaclass holds an S          *)
(* instance (op "meta"): with S defining __set__ the instance is a data   *)
(* descriptor and binds to the class, else type's __prepare__ answers.    *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Classes == {"A", "B", "C", "D"}
Kinds == {"none", "stop", "super"}
MRO(x) == CASE x = "A" -> <<"A">> [] x = "B" -> <<"B", "A">> [] x = "C" -> <<"C", "A">>
             [] x = "D" -> <<"D", "B", "C", "A">>
Diamonds == [kind : [Classes -> Kinds], call : Classes, name : {"m", "__get__", "p"}, receiver : {"instance", "proxy"}]
Frames == [op : {"frame"}, frame : {"method", "lambda", "generic"}]
Binds == [op : {"bind"}, cls : {"super", "S"}, bound : BOOLEAN, obj : {"instance", "None"}]
Metas == [op : {"meta"}, set : BOOLEAN]
Programs == Diamonds \cup Frames \cup Binds \cup Metas

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == <<<<>>, "pending">>

Call(p) ==
    LET mro == MRO(p.call)
        \* m as found from position i of the MRO on (the receiver's class
        \* is position 1; super() in mro[j] starts at j + 1).
        RECURSIVE From(_, _)
        From(i, viaSuper) == IF i > Len(mro) THEN <<<<>>, IF viaSuper /\ p.name = "__get__" THEN "ok" ELSE "AttributeError">>
                   ELSE IF p.kind[mro[i]] = "none" THEN From(i + 1, viaSuper)
                   ELSE IF p.kind[mro[i]] = "stop" THEN <<<<mro[i]>>, "ok">>
                   ELSE LET rest == From(i + 1, TRUE) IN <<<<mro[i]>> \o rest[1], rest[2]>>
    IN  From(1, FALSE)

Bind(p) == IF p.bound \/ p.obj = "None" THEN <<<<>>, "itself">>
           ELSE IF p.cls = "super" THEN <<<<>>, "super bound">> ELSE <<<<"init">>, "S bound">>

Run(p) == IF p \in Binds THEN Bind(p) ELSE IF p \in Metas THEN <<<<>>, IF p.set THEN "S bound" ELSE "type's">>
          ELSE IF p \in Frames THEN <<<<>>, IF p.frame = "method" THEN "ok" ELSE "RuntimeError: super(): no arguments">> ELSE Call(p)

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending
Diamond == Done /\ program \in Diamonds

\* Only an unbound super object bound to an instance changes; only a
\* subclass's binding calls it.
BindsOnce == Done /\ program \in Binds => (outcome[1] # <<>> <=> program.cls = "S" /\ outcome[2] = "S bound")
Log == outcome[1]
Index(s, x) == CHOOSE i \in DOMAIN s : s[i] = x

\* Methods run in MRO order: for D, C's runs after B's although C is not
\* B's base.
InMROOrder == Diamond => \A i, j \in DOMAIN Log : i < j => Index(MRO(program.call), Log[i]) < Index(MRO(program.call), Log[j])

\* Each method runs at most once, even A's in the diamond.
AtMostOnce == Diamond => \A i, j \in DOMAIN Log : i # j => Log[i] # Log[j]

\* When every class cooperates, every class's method runs, then lookup
\* fails at object, or the super object's own __get__ answers.
AllCooperate == Diamond /\ (\A c \in Classes : program.kind[c] = "super") =>
    Log = MRO(program.call) /\ outcome[2] = IF program.name = "__get__" THEN "ok" ELSE "AttributeError"

\* A property read through super() runs its getter as a method call does.
PropertyIsMethod == Diamond /\ program.name = "p" => outcome = Call([program EXCEPT !.name = "m"])

\* A proxy whose __class__ answers X receives X's methods as an X does.
ProxyIsInstance == Diamond /\ program.receiver = "proxy" => outcome = Call([program EXCEPT !.receiver = "instance"])
=============================================================================
