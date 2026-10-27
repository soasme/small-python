------------------------------ MODULE Buffers ------------------------------
(***************************************************************************)
(* Emulating buffer types, as The Python Language Reference specifies it   *)
(* (reference/datamodel.html#emulating-buffer-types): a class exports a    *)
(* buffer by defining __buffer__(flags), which must return a memoryview;   *)
(* memoryview() and bytes() then use it, and when the buffer is released   *)
(* (by release(), leaving a with block, or the view being destroyed, and   *)
(* by bytes() once it has copied) __release_buffer__ receives the view;    *)
(* an object that exports no buffer is refused with TypeError; and while   *)
(* a view of a bytearray is unreleased the bytearray cannot be resized.    *)
(*                                                                         *)
(* An export program defines class B whose __buffer__ logs "buffer" and    *)
(* returns memoryview(b"abc") or b"abc", with or without a                 *)
(* __release_buffer__ that logs "release"; then takes bytes(B()), or makes *)
(* m = memoryview(B()) and reads bytes(m) inside `with m:`, before         *)
(* m.release(), or before del m. A resize program appends to a bytearray   *)
(* with a view that is unreleased or released; a plain program takes       *)
(* memoryview(object()). The outcome is the log and the result or the      *)
(* exception.                                                              *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [part : {"export"}, ret : {"view", "bytes"}, release : BOOLEAN, how : {"bytes", "with", "release", "del"}]
            \cup [part : {"resize"}, released : BOOLEAN]
            \cup [part : {"plain"}]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Export(p) ==
    IF p.ret = "bytes" THEN "buffer TypeError"                \* __buffer__ must return a memoryview
    ELSE "buffer " \o (IF p.release THEN "release " ELSE "") \o "b'abc'"

Run(p) == CASE p.part = "export" -> Export(p)
            [] p.part = "resize" -> IF p.released THEN "3" ELSE "BufferError"
            [] p.part = "plain" -> "TypeError"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A buffer obtained is released exactly once, however it is let go.
ReleasedOnce == Done /\ program.part = "export" /\ program.ret = "view" /\ program.release =>
    outcome = "buffer release b'abc'"
=============================================================================
