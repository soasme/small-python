--------------------------- MODULE SpyBuildOutput ---------------------------
(***************************************************************************)
(* What spyc writes, leaves behind and returns (docs/build.md 2.1, 5.3),   *)
(* as spyc/__main__.py implements it on the C module spyc/_spyc.c.         *)
(* SpyBuild.tla models what the bundle holds; SpyCache.tla the cache; this *)
(* models the files it lands in. TLC checks, for each mode, each choice of *)
(* metafile and dependency rule, each old file, every step that fails, and *)
(* an interruption (SIGINT or SIGTERM) at any point:                       *)
(*                                                                         *)
(*  - A build that succeeds leaves new files, the asked ones only.         *)
(*  - A build that fails or is interrupted leaves each file as it was or   *)
(*    removes it, and removes only files it began to write: a file once    *)
(*    opened, the executable once the compiler started.                    *)
(*  - The temporary C file never outlives the build, nor does any compiler *)
(*    process that could still write the output; every build ends.         *)
(*                                                                         *)
(* The implementation, step by step (names are _spyc's):                   *)
(*                                                                         *)
(*  - write records a path in written once fopen succeeds, then writes; a  *)
(*    failed write leaves a partial file. -e and -c write the C output so; *)
(*    the metafile and the dependency rule follow, in order.               *)
(*  - temp records the mkstemp file and writes it; a failed write fails    *)
(*    the build. compile, with SIGINT and SIGTERM blocked, spawns the      *)
(*    compiler in its own process group and, if that succeeded, records    *)
(*    the output and the compiler: one step. After waitpid, or a failed    *)
(*    spawn, unlink removes the temporary file, then drops it from         *)
(*    written.                                                             *)
(*  - A failure ends in done(True), whose discard removes every recorded   *)
(*    path.                                                                *)
(*  - written changes so that it lists a superset of the files at every    *)
(*    point (unlink before the count drops, copy before it shrinks), so a  *)
(*    change to it is one step here.                                       *)
(*  - interrupted, which guard installs, signals the compiler's group,     *)
(*    waits for the compiler, kills what is left of the group, discards,   *)
(*    and dies of the signal.                                              *)
(*                                                                         *)
(* The compiler is the environment. Its driver may leave a child that      *)
(* ignores the signal, as a linker may; while any of it runs it may write  *)
(* the output. A driver exits after its children, with the output new, or  *)
(* failing with the output in any state. Its own temporary files are its   *)
(* own (docs/build.md 5.3) and are not modelled.                           *)
(***************************************************************************)
EXTENDS Naturals, Sequences

Files == {"out", "meta", "deps", "temp"}
States == {"absent", "old", "partial", "new"}

VARIABLES pc, mode, wants, init, disk, written, compiler, driver, child, ok, status,  \* spyc.c's
          begun                                                                     \* a ghost

vars == <<pc, mode, wants, init, disk, written, compiler, driver, child, ok, status, begun>>

Init == /\ mode \in {"exe", "c"}
        /\ wants \in [{"meta", "deps"} -> BOOLEAN]
        /\ init \in [Files -> {"absent", "old"}] /\ init["temp"] = "absent"
        /\ disk = init /\ written = {} /\ begun = {}
        /\ compiler = FALSE /\ driver = "none" /\ child = "none" /\ ok = TRUE
        /\ status = "none" /\ pc = "resolve"

Set(f, v) == disk' = [disk EXCEPT ![f] = v]
\* The step after the output: the metafile, the dependency rule, success.
After(f) == IF f = "out" /\ wants["meta"] THEN "open_meta"
            ELSE IF f # "deps" /\ wants["deps"] THEN "open_deps"
            ELSE "exit"
Name(f) == "open_" \o f
Body(f) == "write_" \o f

\* Bundling found every module, or failed before writing anything (SpyBuild).
Resolve == /\ pc = "resolve"
           /\ pc' \in {IF mode = "exe" THEN "mkstemp" ELSE "open_out", "fail"}
           /\ UNCHANGED <<mode, wants, init, disk, written, compiler, driver, child, ok, status, begun>>

\* write_file(f): fopen, recorded on success, then the write.
Open(f) == /\ pc = Name(f)
           /\ \/ /\ Set(f, "partial") /\ written' = written \cup {f} /\ begun' = begun \cup {f}
                 /\ pc' = Body(f)
              \/ /\ pc' = "fail" /\ UNCHANGED <<disk, written, begun>>
           /\ UNCHANGED <<mode, wants, init, compiler, driver, child, ok, status>>
Write(f) == /\ pc = Body(f)
            /\ \/ Set(f, "new") /\ pc' = After(f)
               \/ pc' = "fail" /\ UNCHANGED disk
            /\ UNCHANGED <<mode, wants, init, written, compiler, driver, child, ok, status, begun>>

\* compile: mkstemp creates the file and records it; write_to fills it.
Mkstemp == /\ pc = "mkstemp"
           /\ \/ /\ Set("temp", "partial") /\ written' = written \cup {"temp"} /\ begun' = begun \cup {"temp"}
                 /\ pc' = "write_temp"
              \/ /\ pc' = "fail" /\ UNCHANGED <<disk, written, begun>>
           /\ UNCHANGED <<mode, wants, init, compiler, driver, child, ok, status>>
WriteTemp == /\ pc = "write_temp"
             /\ \/ Set("temp", "new") /\ pc' = "spawn" /\ UNCHANGED ok
                \/ pc' = "fail" /\ ok' = FALSE /\ UNCHANGED disk
             /\ UNCHANGED <<mode, wants, init, written, compiler, driver, child, status, begun>>
\* posix_spawnp with the signals blocked: the compiler starts, and the output
\* and the compiler are recorded, or it does not start and nothing is.
Spawn == /\ pc = "spawn"
         /\ \/ /\ written' = written \cup {"out"} /\ begun' = begun \cup {"out"}
               /\ compiler' = TRUE /\ driver' = "running" /\ child' \in {"none", "running"}
               /\ pc' = "wait" /\ UNCHANGED ok
            \/ /\ pc' = "untemp" /\ ok' = FALSE
               /\ UNCHANGED <<written, compiler, driver, child, begun>>
         /\ UNCHANGED <<mode, wants, init, disk, status>>
\* waitpid returns once the driver has exited.
Reap == /\ pc = "wait" /\ driver = "exited"
        /\ compiler' = FALSE /\ driver' = "none" /\ pc' = "untemp"
        /\ UNCHANGED <<mode, wants, init, disk, written, child, ok, status, begun>>
\* unlink(source), then its entry leaves written.
Untemp == /\ pc = "untemp" /\ Set("temp", "absent") /\ pc' = "unlist"
          /\ UNCHANGED <<mode, wants, init, written, compiler, driver, child, ok, status, begun>>
Unlist == /\ pc = "unlist" /\ written' = written \ {"temp"}
          /\ pc' = IF ok THEN After("out") ELSE "fail"
          /\ UNCHANGED <<mode, wants, init, disk, compiler, driver, child, ok, status, begun>>

\* discard: every recorded path is removed.
Discarded == disk' = [f \in Files |-> IF f \in written THEN "absent" ELSE disk[f]] /\ written' = {}
\* A failure ends in discard and status 1; success returns 0.
Fail == /\ pc = "fail" /\ Discarded /\ status' = "1" /\ pc' = "done"
        /\ UNCHANGED <<mode, wants, init, compiler, driver, child, ok, begun>>
Exit == /\ pc = "exit" /\ status' = "0" /\ pc' = "done"
        /\ UNCHANGED <<mode, wants, init, disk, written, compiler, driver, child, ok, begun>>

\* A signal: the handler runs to the end, while the compiler acts between
\* its steps. Not while spyc blocks it (Spawn is one step), nor once done.
Handler == {"kill", "reap_killed", "sweep", "discard"}
Interrupt == /\ pc \notin Handler \cup {"done"}
             /\ pc' = IF compiler THEN "kill" ELSE "discard"
             /\ UNCHANGED <<mode, wants, init, disk, written, compiler, driver, child, ok, status, begun>>
\* kill(-compiler, sig): the driver dies; a child that ignores it does not.
Kill == /\ pc = "kill" /\ pc' = "reap_killed"
        /\ driver' = IF driver = "running" THEN "exited" ELSE driver
        /\ UNCHANGED <<mode, wants, init, disk, written, compiler, child, ok, status, begun>>
ReapKilled == /\ pc = "reap_killed" /\ driver = "exited" /\ driver' = "none" /\ pc' = "sweep"
              /\ UNCHANGED <<mode, wants, init, disk, written, compiler, child, ok, status, begun>>
\* kill(-compiler, SIGKILL): nothing of the group survives.
Sweep == /\ pc = "sweep" /\ child' = "none" /\ pc' = "discard"
         /\ UNCHANGED <<mode, wants, init, disk, written, compiler, driver, ok, status, begun>>
Discard == /\ pc = "discard" /\ Discarded /\ status' = "signal" /\ pc' = "done"
           /\ UNCHANGED <<mode, wants, init, compiler, driver, child, ok, begun>>

\* The compiler. While any of it runs, it may write the output.
Scribble == /\ driver = "running" \/ child = "running"
            /\ \E v \in {"partial", "new"} : Set("out", v)
            /\ UNCHANGED <<pc, mode, wants, init, written, compiler, driver, child, ok, status, begun>>
ChildEnds == /\ child = "running" /\ child' = "none"
             /\ UNCHANGED <<pc, mode, wants, init, disk, written, compiler, driver, ok, status, begun>>
DriverExits == /\ driver = "running" /\ child = "none" /\ driver' = "exited"
               /\ \/ Set("out", "new") /\ UNCHANGED ok
                  \/ \E v \in States : Set("out", v) /\ ok' = FALSE
               /\ UNCHANGED <<pc, mode, wants, init, written, compiler, child, status, begun>>

Done == pc = "done" /\ UNCHANGED vars

\* spyc's own steps, which it takes unless interrupted.
SpycStep == \/ Resolve \/ Mkstemp \/ WriteTemp \/ Spawn \/ Reap \/ Untemp \/ Unlist
            \/ \E f \in {"out", "meta", "deps"} : Open(f) \/ Write(f)
            \/ Fail \/ Exit \/ Kill \/ ReapKilled \/ Sweep \/ Discard

Next == SpycStep \/ Interrupt \/ Scribble \/ ChildEnds \/ DriverExits \/ Done

\* spyc and the compiler make progress; the compiler may scribble forever.
Spec == Init /\ [][Next]_vars /\ WF_vars(SpycStep) /\ WF_vars(DriverExits) /\ WF_vars(ChildEnds)

TypeOK == /\ pc \in {"resolve", "mkstemp", "write_temp", "spawn", "wait", "untemp", "unlist",
                     "open_out", "write_out", "open_meta", "write_meta", "open_deps", "write_deps",
                     "fail", "exit", "done"} \cup Handler
          /\ mode \in {"exe", "c"} /\ wants \in [{"meta", "deps"} -> BOOLEAN]
          /\ disk \in [Files -> States] /\ written \subseteq Files /\ begun \subseteq Files
          /\ compiler \in BOOLEAN /\ driver \in {"none", "running", "exited"} /\ child \in {"none", "running"}
          /\ ok \in BOOLEAN /\ status \in {"none", "0", "1", "signal"}

Finished == pc = "done"
Kept == {"out", "meta", "deps"}
\* Success: every asked file is new, the others are as they were.
Complete == Finished /\ status = "0" =>
    /\ disk["out"] = "new"
    /\ \A f \in {"meta", "deps"} : disk[f] = IF wants[f] THEN "new" ELSE init[f]
\* Failure or interruption: each file as it was, or removed.
Clean == Finished /\ status # "0" => \A f \in Kept : disk[f] \in {init[f], "absent"}
\* Only a file the build began to write is removed.
Reached == Finished => \A f \in Kept : disk[f] = "absent" /\ init[f] = "old" => f \in begun
\* Nothing outlives the build that could change a file afterwards.
NothingLeft == Finished => disk["temp"] = "absent" /\ driver = "none" /\ child = "none"
\* Every build ends, interrupted or not.
Termination == <>Finished
=============================================================================
