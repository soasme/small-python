----------------------------- MODULE AnextDefault -----------------------------
(***************************************************************************)
(* An await of anext(it, "d"), as PLS-315 19.3.4 specifies it, where it's  *)
(* __anext__ is a coroutine with the body below, or a generator with       *)
(* CO_ITERABLE_COROUTINE awaiting by yield from, or it is an async         *)
(* generator with that body, whose return "caught" is a yield of it and    *)
(* whose raise StopAsyncIteration is a return, yielding got at its end,   *)
(* or an instance whose Python __await__ gives that body's generator:     *)
(*                                                                         *)
(*     try: got = await Pause()                                            *)
(*     except handled: after: return "caught" | raise StopAsyncIteration   *)
(*                            | await Pause() | raise ValueError           *)
(*     return got                                                          *)
(*                                                                         *)
(* handled KeyError, or KeyError and GeneratorExit (handles "exits").      *)
(* The awaiting coroutine, suspended at Pause's yield, its cr_await then   *)
(* the anext awaitable, is resumed by a send of "sent", a throw of         *)
(* KeyError("k"), of the class KeyError, of IndexError, or a close. The    *)
(* outcome is what that did: the await's value (StopIteration), a          *)
(* suspension, the exception, or what a close returned; then whether       *)
(* cr_await is None after it. Or the program resumes the awaitable itself, *)
(* by its __await__()'s send, throw or close, which acts as through the   *)
(* await,                                                                  *)
(* awaiting then whether it is suspended; its first step a send, or a     *)
(* next() of it (via next); or by the methods of its type, given it       *)
(* first (via type).                                                      *)
(***************************************************************************)
EXTENDS Naturals

Programs == [source : {"coroutine", "generator", "agen", "instance"}, after : {"return", "stop", "await", "raise"}, resume : {"send", "instance", "class", "other", "close"},
             via : {"await", "direct", "next", "type"}, handles : {"KeyError", "exits"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

\* The coroutine's end ends the await: a value as its value,
\* StopAsyncIteration as the default; a suspension keeps cr_await; an async
\* generator's yield is a coroutine's return.
\* A close the body handles: a further await is ignoring GeneratorExit; a
\* coroutine's return or StopAsyncIteration is the close's value, through
\* the await that value or the default, given the await (13.16.3); an
\* async generator's asend closes with None.
Closing(p) == CASE p.after = "await" -> "raised RuntimeError awaiting=False"
                [] p.after = "raise" -> "raised ValueError awaiting=False"
                [] p.source = "agen" -> "closed None awaiting=False"
                [] p.via = "await" /\ p.after = "stop" -> "closed d awaiting=False"
                [] p.via = "await" -> "closed None awaiting=False"
                [] p.after = "stop" -> "value d awaiting=False"
                [] OTHER -> "closed caught awaiting=False"

Run(p) == CASE p.resume = "send" -> "value sent awaiting=False"
            [] p.resume = "close" /\ p.handles = "exits" -> Closing(p)
            [] p.resume = "close" -> "closed None awaiting=False"
            [] p.resume = "other" -> "raised IndexError awaiting=False"
            [] p.after = "return" -> "value caught awaiting=False"
            [] p.after = "stop" -> "value d awaiting=False"
            [] p.after = "await" -> "suspended awaiting=True"
            [] p.after = "raise" -> "raised ValueError awaiting=False"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A class thrown acts as its instance.
ClassAsInstance == Done /\ program.resume = "class" => outcome = Run([program EXCEPT !.resume = "instance"])

\* The awaitable's own methods act as an await of it does, but a close the
\* body handles, whose value the awaiting coroutine takes.
DirectAsAwait == Done /\ program.via # "await" /\ (program.resume # "close" \/ program.handles = "KeyError")
                 => outcome = Run([program EXCEPT !.via = "await"])

\* A coroutine's close its __anext__ answers with StopAsyncIteration gives
\* the await the default, which the awaiting coroutine returns.
CloseDefault == Done /\ program.resume = "close" /\ program.handles = "exits" /\ program.after = "stop" /\ program.source # "agen" /\
                program.via = "await" => outcome = "closed d awaiting=False"

\* StopAsyncIteration ending the coroutine is the default, never raised.
Default == Done /\ program.after = "stop" /\ program.resume \in {"instance", "class"} => outcome = "value d awaiting=False"
=============================================================================
