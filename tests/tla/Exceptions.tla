---------------------------- MODULE Exceptions ----------------------------
(***************************************************************************)
(* The try and with statements, as The Python Language Reference           *)
(* specifies them (reference/compound_stmts.html#the-try-statement, #the-  *)
(* with-statement, and reference/simple_stmts.html#the-raise-statement),   *)
(* over every program of these two shapes:                                 *)
(*                                                                         *)
(*     def run():                         def run():                       *)
(*         for _ in range(1):                 for _ in range(1):           *)
(*             try:                               with CM():   # __exit__  *)
(*                 BODY                               BODY     # is EXIT   *)
(*             except E1:                         log('after')             *)
(*                 HANDLER                    return 'end'                 *)
(*             else:                                                       *)
(*                 ELSE                                                    *)
(*             finally:                                                    *)
(*                 FINALLY                                                 *)
(*             log('after')                                                *)
(*         return 'end'                                                    *)
(*                                                                         *)
(* where each block logs its name and then does one thing: nothing, raise  *)
(* E1 or E2, re-raise with a bare `raise`, return its name, break, or      *)
(* continue; and __exit__ logs the type it is given and returns True,      *)
(* returns False, or raises E2. `log` is the sequence of blocks run, and   *)
(* `outcome` how run() ended: returning a name, or raising an exception,   *)
(* given with its chain of __context__ types (<<kind, name, chain>>).      *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Actions == {"pass", "E1", "E2", "reraise", "return", "break", "continue"}
Exits == {"suppress", "propagate", "E2"}
Programs ==
    [shape : {"try"}, body : Actions, handler : Actions, else : Actions, finally : Actions] \cup
    [shape : {"with"}, body : Actions, exit : Exits]

VARIABLES program, log, outcome
vars == <<program, log, outcome>>

\* How a block or statement completes: normally, by return (with the
\* returning block's name), break, continue, or by raising an exception,
\* which is its chain of __context__ types, newest first.
Completion(kind, name, chain) == [kind |-> kind, name |-> name, chain |-> chain]
Normal == Completion("normal", "", <<>>)

\* A block named `name` doing `action` while `active` is the exception being
\* handled (<<>> for none), after the blocks in `trail` ran.
Block(name, action, active, trail) ==
    [log |-> Append(trail, name),
     done |-> CASE action = "pass" -> Normal
                [] action \in {"E1", "E2"} -> Completion("raise", "", <<action>> \o active)
                [] action = "reraise" -> IF active = <<>> THEN Completion("raise", "", <<"RuntimeError">>)
                                         ELSE Completion("raise", "", active)
                [] action = "return" -> Completion("return", name, <<>>)
                [] action \in {"break", "continue"} -> Completion(action, "", <<>>)]

TryStatement(p) ==
    LET body == Block("body", p.body, <<>>, <<>>)
        middle == CASE body.done.kind = "raise" /\ body.done.chain[1] = "E1" ->
                         Block("handler", p.handler, body.done.chain, body.log)
                    [] body.done.kind = "normal" -> Block("else", p.else, <<>>, body.log)
                    [] OTHER -> body
        pending == middle.done.chain
        final == Block("finally", p.finally, pending, middle.log)
    IN  [log |-> final.log, done |-> IF final.done.kind = "normal" THEN middle.done ELSE final.done]

WithStatement(p) ==
    LET body == Block("body", p.body, <<>>, <<"enter">>)
        raised == body.done.kind = "raise"
        given == IF raised THEN body.done.chain[1] ELSE "None"
        exited == Append(body.log, "exit:" \o given)
        handled == body.done.chain
    IN  [log |-> exited,
         done |-> CASE p.exit = "E2" -> Completion("raise", "", <<"E2">> \o handled)
                    [] raised /\ p.exit = "suppress" -> Normal
                    [] OTHER -> body.done]

\* The loop: break and continue end it (it has one iteration), a statement
\* completing normally logs 'after', and run() then returns 'end'.
Run(p) ==
    LET stmt == IF p.shape = "try" THEN TryStatement(p) ELSE WithStatement(p)
        k == stmt.done.kind
    IN  CASE k = "normal" -> [log |-> Append(stmt.log, "after"), outcome |-> <<"return", "end", <<>>>>]
          [] k \in {"break", "continue"} -> [log |-> stmt.log, outcome |-> <<"return", "end", <<>>>>]
          [] k = "return" -> [log |-> stmt.log, outcome |-> <<"return", stmt.done.name, <<>>>>]
          [] k = "raise" -> [log |-> stmt.log, outcome |-> <<"raise", "", stmt.done.chain>>]

Pending == <<"pending", "", <<>>>>
Init == program \in Programs /\ log = <<>> /\ outcome = Pending

Execute ==
    /\ outcome = Pending
    /\ LET r == Run(program) IN log' = r.log /\ outcome' = r.outcome
    /\ UNCHANGED program

Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
(* What the reference states about every run, checked against the model.   *)

Ran(name) == \E k \in 1..Len(log) : log[k] = name
Done == outcome # Pending
Try == program.shape = "try"

\* "The finally clause is always executed."
FinallyAlways == Done /\ Try => Ran("finally") /\ log[Len(log)] \in {"finally", "after"}

\* The else clause runs exactly when the try clause completes normally.
ElseExactly == Done /\ Try => (Ran("else") <=> program.body = "pass")

\* The handler runs exactly when the try clause raises a matching exception.
HandlerExactly == Done /\ Try => (Ran("handler") <=> program.body = "E1")

\* "If the finally clause executes a return, break or continue statement,
\* the saved exception is discarded"; a return there decides the value.
FinallyDecides == Done /\ Try /\ program.finally = "return" => outcome = <<"return", "finally", <<>>>>
FinallyDiscards == Done /\ Try /\ program.finally \in {"return", "break", "continue"} => outcome[1] = "return"

\* An exception raised while another is handled has it as __context__.
HandlerContext == Done /\ Try /\ program.body = "E1" /\ program.handler = "E2" /\ program.finally = "pass" =>
                  outcome = <<"raise", "", <<"E2", "E1">>>>

\* A bare raise outside any handler raises RuntimeError.
NoActive == Done /\ program.body = "reraise" /\ program.shape = "with" /\ program.exit = "propagate" =>
            outcome = <<"raise", "", <<"RuntimeError">>>>

\* __exit__ always runs, after __enter__ and the body; returning a true
\* value suppresses the body's exception.
ExitAlways == Done /\ ~Try => log[1] = "enter" /\ \E k \in 1..Len(log) : log[k] \in {"exit:None", "exit:E1", "exit:E2", "exit:RuntimeError"}
Suppressed == Done /\ ~Try /\ program.exit = "suppress" => outcome[1] = "return"
=============================================================================
