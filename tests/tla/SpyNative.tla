------------------------------ MODULE SpyNative ------------------------------
(***************************************************************************)
(* Native modules (manual 3.4.9, spy-module.h) as the spy command imports  *)
(* one name, and as an in-process binding's LoadNative or the worker's     *)
(* NATIVE request loads the name's library: what each finds, opens, leaves *)
(* behind and raises. TLC checks every file layout, library, init outcome  *)
(* and policy answer, in process and in the worker, and every sequence of  *)
(* imports, host loads and removals from sys.modules:                      *)
(*                                                                         *)
(*  - A library is opened only with the policy's leave: "import" and      *)
(*    "dlopen" for an import, "dlopen" for a host load. One that fails to  *)
(*    load is closed; one that loads stays open. An import opens it at     *)
(*    most once per context; each host load that succeeds holds one more.  *)
(*  - The engine's table goes only to a library no other engine in the     *)
(*    process linked, and an init runs only with it.                       *)
(*  - A package directory comes first, then NAME.so, then NAME.py; nothing *)
(*    is "not found" while any of them exists. After a host load, every    *)
(*    import runs the library's init, whatever the directory holds.        *)
(*  - The worker opens no library once it has sealed itself.               *)
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
(*  - LoadNative (Go), load_native (Rust) and loadNative (Java) call       *)
(*    spy_std_load_native with NAME.so's path, outside any import: it      *)
(*    registers the init and leaves sys.modules alone.                     *)
(*  - In the worker (spy-worker.c, protocol.md 7.1, 9), NATIVE does the    *)
(*    same, but raises PermissionError once sealed; the worker seals       *)
(*    before it first runs engine code, so before any import, and its      *)
(*    loader is the parent's, which answers only sources.                  *)
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

VARIABLES dir, so, py, init, foreign, worker,         \* the environment
          cache, registered, handles, link, err,      \* spy's
          sealed,
          opens, loads, breach, unlinked, hosted,     \* ghosts
          stale, late

vars == <<dir, so, py, init, foreign, worker, cache, registered, handles, link, err, sealed,
          opens, loads, breach, unlinked, hosted, stale, late>>
env == <<dir, so, py, init, foreign, worker>>

Init == /\ dir \in Dirs /\ so \in Sos /\ py \in BOOLEAN /\ init \in Inits /\ foreign \in BOOLEAN /\ worker \in BOOLEAN
        /\ sealed = FALSE /\ late = FALSE
        /\ cache = "none" /\ registered = FALSE /\ handles = 0
        /\ link = (IF foreign THEN "theirs" ELSE "none") /\ err = ""
        /\ opens = 0 /\ loads = 0 /\ breach = FALSE /\ unlinked = FALSE
        /\ hosted = 0 /\ stale = FALSE

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

\* import NAME, with the policy's answers about "import" and "dlopen". In
\* the worker it runs in engine code, which seals the worker first.
Import(importing, dlopening) ==
    /\ cache = "none"
    /\ sealed' = (sealed \/ worker)
    /\ IF ~importing THEN Fails("PermissionError") /\ UNCHANGED opens
       ELSE IF registered THEN /\ UNCHANGED <<registered, handles, link, loads, opens>> /\ RunInit(link)
       ELSE IF dir = "package" THEN Finds("package") /\ UNCHANGED opens
       ELSE IF so \in Libraries /\ ~worker THEN LoadNative(dlopening)
       ELSE IF py THEN Finds("source") /\ UNCHANGED opens
       ELSE IF dir = "namespace" THEN Finds("namespace") /\ UNCHANGED opens
       ELSE Fails("ModuleNotFoundError") /\ UNCHANGED opens
    /\ breach' = (breach \/ (opens' > opens /\ ~(importing /\ dlopening)))
    /\ late' = (late \/ (opens' > opens /\ sealed'))
    /\ stale' = FALSE /\ UNCHANGED <<env, hosted>>

\* A binding's LoadNative(NAME, NAME.so) or the worker's NATIVE, with the
\* policy's answer about "dlopen": what does not open fails before an open,
\* as dlopen does; what loads is registered, and sys.modules keeps what it
\* held. A sealed worker refuses before asking.
HostLoad(allowed) ==
    /\ IF worker /\ sealed THEN Fails("PermissionError") /\ UNCHANGED opens
       ELSE IF ~allowed THEN Fails("PermissionError") /\ UNCHANGED opens
       ELSE IF so \notin Libraries THEN Fails("ImportError") /\ UNCHANGED opens
       ELSE /\ opens' = opens + 1
            /\ IF so \in {"plain", "misnamed", "old"} \/ link = "theirs" THEN Fails("ImportError")
               ELSE /\ link' = "ours" /\ registered' = TRUE /\ handles' = handles + 1 /\ loads' = loads + 1
                    /\ err' = "" /\ UNCHANGED <<cache, unlinked>>
    /\ hosted' = IF registered' /\ handles' > handles THEN hosted + 1 ELSE hosted
    /\ stale' = IF hosted' > hosted THEN cache # "none" ELSE stale
    /\ breach' = (breach \/ (opens' > opens /\ ~allowed))
    /\ late' = (late \/ (opens' > opens /\ sealed))
    /\ UNCHANGED <<env, sealed>>

\* del sys.modules[NAME]
Remove == /\ cache # "none" /\ cache' = "none" /\ err' = ""
          /\ stale' = FALSE
          /\ UNCHANGED <<env, registered, handles, link, sealed, opens, loads, breach, unlinked, hosted, late>>

Next == \/ \E importing, dlopening \in BOOLEAN : Import(importing, dlopening)
        \/ \E allowed \in BOOLEAN : HostLoad(allowed)
        \/ Remove

Spec == Init /\ [][Next]_vars

\* A library that fails opens again on each import; three show it.
Small == opens <= 3

TypeOK == /\ dir \in Dirs /\ so \in Sos /\ py \in BOOLEAN /\ init \in Inits /\ foreign \in BOOLEAN /\ worker \in BOOLEAN
          /\ cache \in {"none", "native", "package", "source", "namespace"}
          /\ registered \in BOOLEAN /\ handles \in Nat /\ link \in {"none", "ours", "theirs"} /\ err \in Errors
          /\ hosted \in Nat /\ stale \in BOOLEAN /\ sealed \in BOOLEAN /\ late \in BOOLEAN

\* A library is opened only with the leaves it needs; an import keeps it
\* open once, and each host load one more time.
PolicyGates == ~breach
\* Nothing is opened in a sealed worker.
SealedShut == ~late
OpenOnce == handles <= hosted + 1
\* What failed to load was closed: every open handle is a load.
NothingLeftOpen == handles = loads
\* Another engine's table is never replaced, and inits run with ours.
TableKept == foreign => link = "theirs"
InitLinked == ~unlinked
\* A package before NAME.so before NAME.py; not found means none exists.
PackageFirst == dir = "package" /\ hosted = 0 => cache \in {"none", "package"}
\* After a host load, what an import caches is the library's module.
HostFirst == hosted > 0 /\ ~stale => cache \in {"none", "native"}
\* (The worker's loader answers only sources.)
NativeFirst == cache = "source" => so \notin Libraries \/ worker
NotFoundAbsent == err = "ModuleNotFoundError" => dir = "none" /\ ~py /\ (so \notin Libraries \/ worker)
\* A cached native module was initialized.
NativeComplete == cache = "native" => registered /\ init = "ok"
=============================================================================
