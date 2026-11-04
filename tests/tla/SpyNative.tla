------------------------------ MODULE SpyNative ------------------------------
(***************************************************************************)
(* Native modules (manual 3.2, spy-module.h) as the spy command imports    *)
(* one name: what the import finds, opens, leaves behind and raises. TLC   *)
(* checks every file layout, library, init outcome and policy answer, and  *)
(* every sequence of imports and removals from sys.modules:                *)
(*                                                                         *)
(*  - A library is opened only with the policy's leave for "import" and    *)
(*    "dlopen". One that fails to load is closed; one that loads stays     *)
(*    open, once per context.                                              *)
(*  - The engine's table goes only to a library no other engine in the     *)
(*    process linked, and an init runs only with it.                       *)
(*  - A package directory comes first, then NAME.so, then NAME.py; nothing *)
(*    is "not found" while any of them exists.                             *)
(*  - sys.modules holds a native module only after its init succeeded; a   *)
(*    failed init runs again on the next import, without opening again.    *)
(*                                                                         *)
(* The implementation, step by step (names are spy.c's, spy-std.c's and    *)
(* cli.c's):                                                               *)
(*                                                                         *)
(*  - load_source_module returns a cached module; otherwise it asks the    *)
(*    policy about "import" and runs a registered module's init without    *)
(*    calling the loader. Else it probes NAME.__init__, then NAME, then,   *)
(*    if the loader registered nothing, NAME.__namespace__.                *)
(*  - cli.c's load_module answers the NAME probe: a regular file NAME.so   *)
(*    goes to spy_std_load_native and the probe returns no source;         *)
(*    otherwise host_load_module reads NAME.py.                            *)
(*  - spy_std_load_native asks about "dlopen", opens the library, finds    *)
(*    spy_module and spy_init_NAME, checks the version, links the table    *)
(*    by compare-and-swap, and registers the init; a failure after the     *)
(*    open closes the library, and every failure raises ImportError.       *)
(*  - An init that fails without raising becomes SystemError; a failed     *)
(*    import leaves no entry in sys.modules.                               *)
(***************************************************************************)
EXTENDS Naturals

\* What the directory holds under the name: a package directory (with
\* __init__.py), a bare directory (a namespace package), or neither; the
\* NAME.so entry; and NAME.py.
Dirs == {"none", "package", "namespace"}
\* "folder" is a directory named NAME.so; "garbage" a file that is not a
\* library; "plain" a library without spy_module; "misnamed" one without
\* spy_init_NAME; "old" one built for an incompatible engine.
Sos == {"none", "folder", "garbage", "plain", "misnamed", "old", "module"}
Libraries == Sos \ {"none", "folder"}
Inits == {"ok", "raises", "silent"}
Errors == {"", "PermissionError", "ImportError", "ModuleNotFoundError", "ValueError", "SystemError"}

VARIABLES dir, so, py, init, foreign,                 \* the environment
          cache, registered, handles, link, err,      \* spy's
          opens, loads, breach, unlinked              \* ghosts

vars == <<dir, so, py, init, foreign, cache, registered, handles, link, err, opens, loads, breach, unlinked>>
env == <<dir, so, py, init, foreign>>

Init == /\ dir \in Dirs /\ so \in Sos /\ py \in BOOLEAN /\ init \in Inits /\ foreign \in BOOLEAN
        /\ cache = "none" /\ registered = FALSE /\ handles = 0
        /\ link = (IF foreign THEN "theirs" ELSE "none") /\ err = ""
        /\ opens = 0 /\ loads = 0 /\ breach = FALSE /\ unlinked = FALSE

\* The registered init runs in the new module, with the library linked to
\* l: sys.modules keeps the module only when the init succeeded.
RunInit(l) == /\ cache' = IF init = "ok" THEN "native" ELSE "none"
              /\ err' = CASE init = "ok" -> "" [] init = "raises" -> "ValueError" [] init = "silent" -> "SystemError"
              /\ unlinked' = (unlinked \/ l # "ours")

Fails(e) == /\ err' = e /\ UNCHANGED <<cache, registered, handles, link, loads, unlinked>>
Finds(m) == /\ cache' = m /\ err' = "" /\ UNCHANGED <<registered, handles, link, loads, unlinked>>

\* spy_std_load_native, with the policy's answer about "dlopen".
LoadNative(allowed) ==
    IF ~allowed THEN Fails("PermissionError") /\ UNCHANGED opens
    ELSE IF so = "garbage" THEN Fails("ImportError") /\ UNCHANGED opens
    ELSE /\ opens' = opens + 1
         /\ IF so \in {"plain", "misnamed", "old"} \/ link = "theirs" THEN Fails("ImportError")
            ELSE /\ link' = "ours" /\ registered' = TRUE /\ handles' = handles + 1 /\ loads' = loads + 1
                 /\ RunInit("ours")

\* import NAME, with the policy's answers about "import" and "dlopen".
Import(importing, dlopening) ==
    /\ cache = "none"
    /\ IF ~importing THEN Fails("PermissionError") /\ UNCHANGED opens
       ELSE IF registered THEN /\ UNCHANGED <<registered, handles, link, loads, opens>> /\ RunInit(link)
       ELSE IF dir = "package" THEN Finds("package") /\ UNCHANGED opens
       ELSE IF so \in Libraries THEN LoadNative(dlopening)
       ELSE IF py THEN Finds("source") /\ UNCHANGED opens
       ELSE IF dir = "namespace" THEN Finds("namespace") /\ UNCHANGED opens
       ELSE Fails("ModuleNotFoundError") /\ UNCHANGED opens
    /\ breach' = (breach \/ (opens' > opens /\ ~(importing /\ dlopening)))
    /\ UNCHANGED env

\* del sys.modules[NAME]
Remove == /\ cache # "none" /\ cache' = "none" /\ err' = ""
          /\ UNCHANGED <<env, registered, handles, link, opens, loads, breach, unlinked>>

Next == \/ \E importing, dlopening \in BOOLEAN : Import(importing, dlopening)
        \/ Remove

Spec == Init /\ [][Next]_vars

\* A library that fails opens again on each import; three show it.
Small == opens <= 3

TypeOK == /\ dir \in Dirs /\ so \in Sos /\ py \in BOOLEAN /\ init \in Inits /\ foreign \in BOOLEAN
          /\ cache \in {"none", "native", "package", "source", "namespace"}
          /\ registered \in BOOLEAN /\ handles \in Nat /\ link \in {"none", "ours", "theirs"} /\ err \in Errors

\* A library is opened only with both leaves, and stays open once.
PolicyGates == ~breach
OpenOnce == handles <= 1
\* What failed to load was closed: every open handle is a load.
NothingLeftOpen == handles = loads
\* Another engine's table is never replaced, and inits run with ours.
TableKept == foreign => link = "theirs"
InitLinked == ~unlinked
\* A package before NAME.so before NAME.py; not found means none exists.
PackageFirst == dir = "package" => cache \in {"none", "package"}
NativeFirst == cache = "source" => so \notin Libraries
NotFoundAbsent == err = "ModuleNotFoundError" => dir = "none" /\ ~py /\ so \notin Libraries
\* A cached native module was initialized.
NativeComplete == cache = "native" => registered /\ init = "ok"
=============================================================================
