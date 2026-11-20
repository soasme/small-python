------------------------------ MODULE Buffers ------------------------------
(***************************************************************************)
(* Emulating buffer types, as The Python Language Reference specifies it   *)
(* (reference/datamodel.html#emulating-buffer-types): a class exports a    *)
(* buffer by defining __buffer__(flags), which must return a memoryview;   *)
(* memoryview(), bytes() and bytearray() then use it, and when the buffer  *)
(* is released (by release(), leaving a with block, or the view being      *)
(* destroyed, and by bytes() or bytearray() once it has copied)            *)
(* __release_buffer__ receives the view, an exception it raises reported   *)
(* as unraisable and not propagated; an object that exports no buffer      *)
(* is refused with TypeError; and while a view of a bytearray is           *)
(* unreleased the bytearray cannot be resized. A view released by Python   *)
(* code it runs is not touched after: an index or an item converted after  *)
(* the release fails with ValueError, and hash(m), while it hashes the     *)
(* exporter, and m.hex(sep), while it converts sep, keep m exported, so    *)
(* its release fails with BufferError.                                     *)
(*                                                                         *)
(* An export program defines class B whose __buffer__ logs "buffer" and    *)
(* its flags, 284, and returns memoryview(b"abc") or b"abc", or raises     *)
(* ValueError, with no __release_buffer__ or one that logs "release" and   *)
(* returns or then raises KeyError;                                        *)
(* then takes bytes(B()) or bytes(bytearray(B())), or makes m =            *)
(* memoryview(B()) and reads bytes(m) inside `with m:`, before m.release() *)
(* or memoryview.release(m), or before del m. A resize program appends to  *)
(* a bytearray with a view that is unreleased or released; a plain program *)
(* takes memoryview(object()). A reenter program releases a view of a      *)
(* bytearray, and empties the bytearray, from the __index__ of the key of  *)
(* m[k] or of the item of m[0] = v, from the exporter's __hash__ during    *)
(* hash(m), or from the __len__ of sep during m.hex(sep). An index program *)
(* reads m[k] or stores m[k] = 66, k's __index__ logging "index" and       *)
(* returning 1, of a view of bytearray(b"ab") that is plain, released,     *)
(* read-only, of no dimension, or of shape (1, 2): a released view, one of *)
(* no dimension, a store into a read-only or two-dimensional view fail     *)
(* before the index; a two-dimensional item fails after it. A grid program *)
(* reads or stores m[a, b] of a (2, 2) view of bytearray(b"abcd"), a's and *)
(* b's __index__ logging their names, b returning 1 and a 0, or 5, out of  *)
(* bounds. A several program has exporters A of b"XY" and B of b"Q",      *)
(* whose __buffer__ and __release_buffer__ log "getA" and "relA" and loop: *)
(* b"zXYz".replace(A, B), b"-".join([A, B]) directly or by a starred call *)
(* of it in a Python function, b"XYz".startswith((A, B)) or                *)
(* startswith((B, A)), or                                                  *)
(* memoryview(b"XY") == A. A subclass program has                          *)
(* a subclass X of bytes or bytearray whose __buffer__ logs "get" and      *)
(* returns memoryview(b"BUF") and whose __release_buffer__ logs "rel", and *)
(* x = X(b"own"): it reads memoryview(x) inside `with`, b"a" + x,         *)
(* b"own" == x, x.decode(), or b"-".join([x, x]). The outcome is the log   *)
(* and the result or the exception. An item program stores into item 0 of *)
(* a view of format B, d or ? an instance whose Python __index__,          *)
(* __float__ or __bool__ logs its name and returns 7, 2.5 or True, or a    *)
(* bad 256, "x" or 1, and reads the item back.                             *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Programs == [part : {"export"}, ret : {"view", "bytes", "raise"}, release : {"none", "logs", "fails"}, how : {"bytes", "bytearray", "with", "release", "unbound", "del"}]
            \cup [part : {"resize"}, released : BOOLEAN]
            \cup [part : {"plain"}]
            \cup [part : {"reenter"}, during : {"index", "store", "hash", "hex"}]
            \cup [part : {"index"}, view : {"plain", "released", "readonly", "zero", "grid"}, store : BOOLEAN]
            \cup [part : {"grid"}, first : {"in", "out"}, store : BOOLEAN]
            \cup [part : {"several"}, op : {"replace", "join", "starred", "first", "second", "compare"}]
            \cup [part : {"subclass"}, base : {"bytes", "bytearray"}, use : {"view", "concat", "compare", "decode", "twice"}]
            \cup [part : {"item"}, format : {"B", "d", "?"}, bad : BOOLEAN]

VARIABLES program, outcome
vars == <<program, outcome>>

Pending == "pending"

Export(p) ==
    CASE p.ret = "bytes" -> "buffer 284 TypeError"             \* __buffer__ must return a memoryview
      [] p.ret = "raise" -> "buffer 284 ValueError"            \* its exception propagates, nothing exported
      [] OTHER -> "buffer 284 " \o (IF p.release # "none" THEN "release " ELSE "") \o "b'abc'"

\* Whether an item of view v, or a store into it, converts its index.
Indexes(v, store) == v \in IF store THEN {"plain"} ELSE {"plain", "readonly", "grid"}

Index(p) ==
    IF ~Indexes(p.view, p.store)
    THEN CASE p.view = "released" -> "ValueError"
           [] p.view = "grid" -> "NotImplementedError"
           [] OTHER -> "TypeError"
    ELSE "index " \o (CASE p.view = "grid" -> "NotImplementedError"
                        [] p.store -> "b'aB'"
                        [] OTHER -> "98")

\* A grid's key converts its items in order, each checked for its dimension before the next.
Grid(p) == IF p.first = "out" THEN "a IndexError" ELSE "a b " \o (IF p.store THEN "b'aBcd'" ELSE "98")

\* Several buffers are all obtained, in the order read, before any is
\* released; startswith takes each choice in turn and stops at a match.
Several(p) == CASE p.op = "replace" -> "getA getB relA relB b'zQz'"
                [] p.op \in {"join", "starred"} -> "getA getB relA relB b'XY-Q'"
                [] p.op = "first" -> "getA relA True"
                [] p.op = "second" -> "getB relB getA relA True"
                [] p.op = "compare" -> "getA relA True"

\* A subclass's own __buffer__ exports its buffer; a bytes comparison and
\* bytes.decode read a bytes subclass's contents, and a join asks for each
\* item's buffer, the same object twice.
Subclass(p) == CASE p.use = "view" -> "get rel b'BUF'"
                 [] p.use = "concat" -> "get rel b'aBUF'"
                 [] p.use = "twice" -> "get get rel rel b'BUF-BUF'"
                 [] p.base = "bytes" -> IF p.use = "compare" THEN "True" ELSE "'own'"
                 [] OTHER -> IF p.use = "compare" THEN "get rel False" ELSE "get rel 'BUF'"

Run(p) == CASE p.part = "export" -> Export(p)
            [] p.part = "subclass" -> Subclass(p)
            [] p.part = "several" -> Several(p)
            [] p.part = "index" -> Index(p)
            [] p.part = "grid" -> Grid(p)
            [] p.part = "resize" -> IF p.released THEN "3" ELSE "BufferError"
            [] p.part = "plain" -> "TypeError"
            [] p.part = "reenter" -> IF p.during \in {"index", "store"} THEN "ValueError" ELSE "BufferError"
            \* The value converts once for the format; a bad number is invalid.
            [] p.part = "item" -> CASE p.format = "B" -> IF p.bad THEN "index ValueError" ELSE "index 7"
                                   [] p.format = "d" -> IF p.bad THEN "float TypeError" ELSE "float 2.5"
                                   [] OTHER -> IF p.bad THEN "bool TypeError" ELSE "bool True"

Init == program \in Programs /\ outcome = Pending
Execute == outcome = Pending /\ outcome' = Run(program) /\ UNCHANGED program
Spec == Init /\ [][Execute]_vars

-----------------------------------------------------------------------------
Done == outcome # Pending

\* A buffer obtained is released exactly once, however it is let go and
\* whether or not its __release_buffer__ raises.
ReleasedOnce == Done /\ program.part = "export" /\ program.ret = "view" /\ program.release # "none" =>
    outcome = "buffer 284 release b'abc'"

\* A buffer never obtained is never released.
UnexportedUnreleased == Done /\ program.part = "export" /\ program.ret # "view" =>
    outcome \in {"buffer 284 TypeError", "buffer 284 ValueError"}

\* A view released by the code it runs is neither read nor written after.
ReleasedUntouched == Done /\ program.part = "reenter" => outcome \in {"ValueError", "BufferError"}

\* A view checks what it can before an index's __index__ runs.
ChecksFirst == Done /\ program.part = "index" /\ program.view \in {"released", "zero"} => outcome \in {"ValueError", "TypeError"}

\* An operation reading several buffers releases none of them before it has them all.
HeldTogether == Done /\ program.part = "several" /\ program.op \in {"replace", "join", "starred"} => outcome \in {"getA getB relA relB b'zQz'", "getA getB relA relB b'XY-Q'"}

\* Every buffer obtained is released, a choice's before the next is obtained.
ChoicesInTurn == Done /\ program.part = "several" /\ program.op = "second" => outcome = "getB relB getA relA True"

\* A bytes subclass's contents are what a bytes comparison and decode read.
ContentsRead == Done /\ program.part = "subclass" /\ program.base = "bytes" /\ program.use \in {"compare", "decode"} =>
    outcome \in {"True", "'own'"}

\* A join asks for the buffer of each item it reads, however often an object recurs.
EachAsked == Done /\ program.part = "subclass" /\ program.use = "twice" => outcome = "get get rel rel b'BUF-BUF'"

\* A dimension out of bounds stops the key before its next item's __index__.
DimensionsInOrder == Done /\ program.part = "grid" /\ program.first = "out" => outcome = "a IndexError"
=============================================================================
