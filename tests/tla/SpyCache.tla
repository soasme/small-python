------------------------------ MODULE SpyCache ------------------------------
(***************************************************************************)
(* The executable cache of spyc run and spyc test (docs/build.md 2.3), as  *)
(* cache() and clean() in spyc/__main__.py implement it on spyc/_spyc.c.   *)
(* Two builds of one slot run at once, each with a stamp, the same or not, *)
(* and spyc clean may run beside them. TLC checks every interleaving, with *)
(* each build interrupted (SIGINT or SIGTERM, which discard) or killed     *)
(* (SIGKILL, after which nothing of it runs) at any step:                  *)
(*                                                                         *)
(*  - A name in the cache holds the complete program of its stamp.         *)
(*  - A build runs nothing but its own stamp's complete program. It fails  *)
(*    to run one only when a build of another stamp or spyc clean removed  *)
(*    it; builds of one stamp, without clean, always run.                  *)
(*  - clean removes only files the cache made.                             *)
(*  - A build that ends, other than by SIGKILL, leaves no temporary file.  *)
(*  - Every build and clean ends.                                          *)
(*                                                                         *)
(* The implementation, step by step:                                       *)
(*                                                                         *)
(*  - cache() looks for the name with executable(); a hit runs it.         *)
(*  - A miss makes .spyc, then the compiler writes NAME.PID, which compile *)
(*    records once the compiler runs; a failure or an interruption         *)
(*    discards it. rename moves it to NAME, and fails if it is gone.       *)
(*  - The build lists .spyc, then unlinks its slot's other names, one at a *)
(*    time, and runs NAME with exec, which fails if NAME is gone.          *)
(*  - clean lists .spyc, unlinks each name with the cache's prefix, a      *)
(*    temporary one too, then rmdir, which fails while any file is left.   *)
(***************************************************************************)
EXTENDS Naturals, FiniteSets

Builds == {"b1", "b2"}
Stamps == {"s1", "s2"}
Contents == {"absent", "partial"} \cup Stamps

VARIABLES pc, stamp, final, temp, dir, mine, ran, listed, cleans, cpc, clisted

vars == <<pc, stamp, final, temp, dir, mine, ran, listed, cleans, cpc, clisted>>
builds == <<pc, stamp, final, temp, dir, ran, listed>>
cleaner == <<cleans, cpc, clisted>>

\* A program's content is the stamp it was built from; a temporary file in
\* the making is partial.
Init == /\ stamp \in [Builds -> Stamps] /\ cleans \in BOOLEAN
        /\ final \in [Stamps -> {"absent"} \cup Stamps] /\ \A s \in Stamps : final[s] \in {"absent", s}
        /\ temp = [b \in Builds |-> "absent"] /\ dir \in {"absent", "present"}
        /\ (dir = "absent" => \A s \in Stamps : final[s] = "absent")
        /\ mine \in BOOLEAN /\ (dir = "absent" => ~mine)
        /\ ran = [b \in Builds |-> "none"] /\ listed = [b \in Builds |-> {}]
        /\ pc = [b \in Builds |-> "check"] /\ cpc = (IF cleans THEN "list" ELSE "done") /\ clisted = {}

Go(b, next) == pc' = [pc EXCEPT ![b] = next]
SetTemp(b, v) == temp' = [temp EXCEPT ![b] = v]

Check(b) == /\ pc[b] = "check"
            /\ Go(b, IF final[stamp[b]] # "absent" THEN "exec" ELSE "mkdir")
            /\ UNCHANGED <<stamp, final, temp, dir, ran, listed>>
Mkdir(b) == /\ pc[b] = "mkdir" /\ dir' = "present" /\ Go(b, "compile")
            /\ UNCHANGED <<stamp, final, temp, ran, listed>>
\* The compiler cannot write into a directory clean removed.
Compile(b) == /\ pc[b] = "compile"
              /\ IF dir = "present"
                 THEN SetTemp(b, "partial") /\ Go(b, "compiled")
                 ELSE Go(b, "fail") /\ UNCHANGED temp
              /\ UNCHANGED <<stamp, final, dir, ran, listed>>
Compiled(b) == /\ pc[b] = "compiled"
               /\ \/ /\ temp[b] # "absent" /\ SetTemp(b, stamp[b]) /\ Go(b, "rename")
                  \/ Go(b, "fail") /\ UNCHANGED temp
               /\ UNCHANGED <<stamp, final, dir, ran, listed>>
Rename(b) == /\ pc[b] = "rename"
             /\ IF temp[b] = "absent"
                THEN Go(b, "fail") /\ UNCHANGED <<final, temp>>
                ELSE /\ final' = [final EXCEPT ![stamp[b]] = temp[b]] /\ SetTemp(b, "absent")
                     /\ Go(b, "list")
             /\ UNCHANGED <<stamp, dir, ran, listed>>
List(b) == /\ pc[b] = "list"
           /\ listed' = [listed EXCEPT ![b] = {s \in Stamps : s # stamp[b] /\ final[s] # "absent"}]
           /\ Go(b, "prune")
           /\ UNCHANGED <<stamp, final, temp, dir, ran>>
Prune(b) == /\ pc[b] = "prune"
            /\ IF listed[b] = {}
               THEN Go(b, "exec") /\ UNCHANGED <<final, listed>>
               ELSE \E s \in listed[b] : /\ final' = [final EXCEPT ![s] = "absent"]
                                         /\ listed' = [listed EXCEPT ![b] = @ \ {s}]
                                         /\ UNCHANGED pc
            /\ UNCHANGED <<stamp, temp, dir, ran>>
Exec(b) == /\ pc[b] = "exec"
           /\ IF final[stamp[b]] = "absent"
              THEN Go(b, "unrun") /\ UNCHANGED ran
              ELSE ran' = [ran EXCEPT ![b] = final[stamp[b]]] /\ Go(b, "ran")
           /\ UNCHANGED <<stamp, final, temp, dir, listed>>
\* A failure ends in discard: the recorded temporary file goes.
Fail(b) == /\ pc[b] = "fail" /\ SetTemp(b, "absent") /\ Go(b, "failed")
           /\ UNCHANGED <<stamp, final, dir, ran, listed>>
Ends == {"ran", "unrun", "failed", "interrupted", "killed"}
Interrupt(b) == /\ pc[b] \notin Ends /\ SetTemp(b, "absent") /\ Go(b, "interrupted")
                /\ UNCHANGED <<stamp, final, dir, ran, listed, mine, cleaner>>
Kill(b) == /\ pc[b] \notin Ends /\ Go(b, "killed")
           /\ UNCHANGED <<stamp, final, temp, dir, ran, listed, mine, cleaner>>
\* A build's own steps leave mine and clean alone.
BuildStep(b) == /\ Check(b) \/ Mkdir(b) \/ Compile(b) \/ Compiled(b) \/ Rename(b) \/ List(b) \/ Prune(b) \/ Exec(b) \/ Fail(b)
                /\ UNCHANGED <<mine, cleaner>>

\* clean's names: the programs and the temporary files, never mine.
Names == {<<"final", s>> : s \in Stamps} \cup {<<"temp", b>> : b \in Builds}
Present(n) == IF n[1] = "final" THEN final[n[2]] # "absent" ELSE temp[n[2]] # "absent"
CleanList == /\ cpc = "list" /\ clisted' = {n \in Names : Present(n)} /\ cpc' = "unlink"
             /\ UNCHANGED <<builds, mine, cleans>>
CleanUnlink == /\ cpc = "unlink"
               /\ IF clisted = {}
                  THEN cpc' = "rmdir" /\ UNCHANGED <<clisted, final, temp>>
                  ELSE \E n \in clisted : /\ clisted' = clisted \ {n}
                                          /\ IF n[1] = "final"
                                             THEN final' = [final EXCEPT ![n[2]] = "absent"] /\ UNCHANGED temp
                                             ELSE temp' = [temp EXCEPT ![n[2]] = "absent"] /\ UNCHANGED final
                                          /\ UNCHANGED cpc
               /\ UNCHANGED <<pc, stamp, dir, ran, listed, mine, cleans>>
Empty == ~mine /\ \A n \in Names : ~Present(n)
CleanRmdir == /\ cpc = "rmdir"
              /\ IF Empty THEN dir' = "absent" /\ cpc' = "done" ELSE cpc' = "error" /\ UNCHANGED dir
              /\ UNCHANGED <<pc, stamp, final, temp, ran, listed, mine, cleans, clisted>>
CleanStep == CleanList \/ CleanUnlink \/ CleanRmdir

Done == /\ \A b \in Builds : pc[b] \in Ends /\ cpc \in {"done", "error"} /\ UNCHANGED vars

Next == \/ \E b \in Builds : BuildStep(b) \/ Interrupt(b) \/ Kill(b)
        \/ CleanStep \/ Done

Spec == Init /\ [][Next]_vars /\ \A b \in Builds : WF_vars(BuildStep(b)) /\ WF_vars(CleanStep)

TypeOK == /\ pc \in [Builds -> {"check", "mkdir", "compile", "compiled", "rename", "list", "prune", "exec", "fail"} \cup Ends]
          /\ stamp \in [Builds -> Stamps] /\ final \in [Stamps -> Contents] /\ temp \in [Builds -> Contents]
          /\ dir \in {"absent", "present"} /\ mine \in BOOLEAN /\ ran \in [Builds -> {"none"} \cup Contents]
          /\ listed \in [Builds -> SUBSET Stamps] /\ cleans \in BOOLEAN
          /\ cpc \in {"list", "unlink", "rmdir", "done", "error"} /\ clisted \subseteq Names

\* A name in the cache holds the complete program of its stamp.
Whole == \A s \in Stamps : final[s] \in {"absent", s}
\* A build runs only its own stamp's complete program.
Right == \A b \in Builds : ran[b] \in {"none", stamp[b]}
\* Without clean, builds of one stamp always run.
Runs == (~cleans /\ stamp["b1"] = stamp["b2"]) => \A b \in Builds : pc[b] # "unrun"
\* A build that ended other than by SIGKILL left no temporary file.
NoTemp == \A b \in Builds : pc[b] \in Ends \ {"killed"} => temp[b] = "absent"
\* rmdir removes the cache only once it is empty, mine included.
Kept == dir = "absent" => Empty
\* Every build and clean ends.
Termination == <>(\A b \in Builds : pc[b] \in Ends /\ cpc \in {"done", "error"})
=============================================================================
