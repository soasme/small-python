----------------------------- MODULE SpyProgram -----------------------------
(***************************************************************************)
(* What a program spyc builds is linked from, and how it starts            *)
(* (docs/build.md 5.3, 5.4, 5.5), as spyc.c implements it. SpyBuild.tla    *)
(* models what the bundle holds and SpyBuildOutput.tla the files a build   *)
(* writes; this models the module inputs, the link, and main. TLC checks,  *)
(* for every list of up to two module inputs (a C file NAME.c or an        *)
(* archive libNAME.a, either one defining its init or not, well or badly   *)
(* named), and for each failure main may meet:                             *)
(*                                                                         *)
(*  - spyc rejects a bad name, or a name given twice, as a usage error     *)
(*    (status 2) before any link; it accepts every other list.             *)
(*  - A link succeeds exactly when every input defines its init; then      *)
(*    each module's init comes from the input of that name.                *)
(*  - The entry runs only with the command line set and every module       *)
(*    registered; a failed mount does not stop it, a failed command line   *)
(*    does (status 1).                                                     *)
(*                                                                         *)
(* The implementation, step by step:                                       *)
(*                                                                         *)
(*  - spyc's argument loop takes NAME.c and libNAME.a as module NAME,      *)
(*    which must be an identifier not taken by an earlier input.           *)
(*  - compile runs CC ... -x c PROGRAM -x none INPUTS... ARGS... libspy.a  *)
(*    -lm: the generated program first, the inputs in their order, the     *)
(*    arguments after -- (a library an archive needs), then the engine.    *)
(*  - The linker reads the line once, left to right. An object is linked   *)
(*    whole, and a symbol two objects define fails the link. An archive's *)
(*    member is linked only if it defines a symbol still undefined. A      *)
(*    symbol still undefined at the end fails the link.                    *)
(*  - The generated main makes a context, mounts the working directory     *)
(*    (clearing the error if that fails), registers each module with       *)
(*    spy_new_module in input order, sets the command line with           *)
(*    spy_set_argv, and runs the entry.                                    *)
(*                                                                         *)
(* Seeded faults show what each check holds: without the duplicate check,  *)
(* NAME.c twice fails the link (Complete), and NAME.c with libNAME.a       *)
(* takes the C file's init for both (Provenance); with the engine before   *)
(* the inputs, an archive's calls into it stay undefined (Complete).       *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

\* An input: its form, the module name its file gives ("bad" is not an
\* identifier), whether an archive's file starts with "lib", and whether it
\* defines spy_init_NAME.
Names == {"fib", "json", "bad"}
Input == [form : {"c", "archive"}, name : Names, lib : BOOLEAN, init : BOOLEAN]
Lists == {<<>>} \cup {<<i>> : i \in Input} \cup {<<i, j>> : i, j \in Input}

Init(n) == "spy_init_" \o n
\* What the line holds, each item with the symbols it defines and needs:
\* the generated program needs every module's init; an input needs the
\* engine, and an archive (a Rust library) also a system library, which the
\* arguments after -- provide.
\* from is 0 for the program, k for input k, 3 and 4 for the libraries.
Item(kind, from, defines, needs) == [kind |-> kind, from |-> from, defines |-> defines, needs |-> needs]
Program(list) == Item("object", 0, {"main"}, {Init(list[k].name) : k \in 1..Len(list)})
Module(list, k) ==
    LET i == list[k] IN
    Item(IF i.form = "c" THEN "object" ELSE "archive", k,
         IF i.init THEN {Init(i.name)} ELSE {},
         IF i.form = "c" THEN {"engine"} ELSE {"engine", "system"})
LinkLine(list) ==
    <<Program(list)>> \o [k \in 1..Len(list) |-> Module(list, k)]
    \o <<Item("archive", 3, {"system"}, {}), Item("archive", 4, {"engine"}, {})>>

\* spyc's argument checks: an identifier, "lib" before an archive's name,
\* and each name once.
Valid(i) == i.name # "bad" /\ (i.form = "c" \/ i.lib)
Accepted(list) == (\A k \in 1..Len(list) : Valid(list[k])) /\
                  \A k, m \in 1..Len(list) : k # m => list[k].name # list[m].name

VARIABLES list, pc, line, at, origin, undefined, status, registered, argv, ran,  \* spyc's, the linker's, main's
          linked                                                                \* a ghost
vars == <<list, pc, line, at, origin, undefined, status, registered, argv, ran, linked>>

Defined == DOMAIN origin

Start == /\ list \in Lists
         /\ pc = "spyc" /\ line = <<>> /\ at = 1 /\ origin = <<>> /\ undefined = {}
         /\ status = "none" /\ registered = {} /\ argv = FALSE /\ ran = FALSE /\ linked = FALSE

Spyc == /\ pc = "spyc"
        /\ IF Accepted(list) THEN pc' = "link" /\ line' = LinkLine(list) /\ UNCHANGED status
           ELSE pc' = "done" /\ status' = "2" /\ UNCHANGED line
        /\ UNCHANGED <<list, at, origin, undefined, registered, argv, ran, linked>>

\* Record where each newly defined symbol came from.
Take(item) == /\ origin' = [s \in Defined \cup item.defines |-> IF s \in Defined THEN origin[s] ELSE item.from]
              /\ undefined' = (undefined \cup item.needs) \ (Defined \cup item.defines)
Link == /\ pc = "link" /\ at <= Len(line)
        /\ LET item == line[at] IN
           IF item.kind = "object" /\ item.defines \cap Defined # {} THEN
               pc' = "done" /\ status' = "1" /\ UNCHANGED <<at, origin, undefined>>
           ELSE /\ IF item.kind = "object" \/ item.defines \cap undefined # {} THEN Take(item)
                   ELSE UNCHANGED <<origin, undefined>>
                /\ at' = at + 1 /\ UNCHANGED <<pc, status>>
        /\ UNCHANGED <<list, line, registered, argv, ran, linked>>
Linked == /\ pc = "link" /\ at > Len(line)
          /\ IF undefined = {} THEN pc' = "mount" /\ linked' = TRUE /\ UNCHANGED status
             ELSE pc' = "done" /\ status' = "1" /\ UNCHANGED linked
          /\ UNCHANGED <<list, line, at, origin, undefined, registered, argv, ran>>

\* main: the mount may fail and is ignored; registration cannot fail for a
\* new name; spy_set_argv may fail (MemoryError), and then nothing runs.
Mount == /\ pc = "mount" /\ pc' = "register"
         /\ UNCHANGED <<list, line, at, origin, undefined, status, registered, argv, ran, linked>>
Register == /\ pc = "register" /\ registered' = {list[k].name : k \in 1..Len(list)} /\ pc' = "argv"
            /\ UNCHANGED <<list, line, at, origin, undefined, status, argv, ran, linked>>
Argv == /\ pc = "argv"
        /\ \/ argv' = TRUE /\ pc' = "run" /\ UNCHANGED status
           \/ pc' = "done" /\ status' = "1" /\ UNCHANGED argv
        /\ UNCHANGED <<list, line, at, origin, undefined, registered, ran, linked>>
Run == /\ pc = "run" /\ ran' = TRUE /\ pc' = "done" /\ status' = "0"
       /\ UNCHANGED <<list, line, at, origin, undefined, registered, argv, linked>>

Done == pc = "done" /\ UNCHANGED vars
Next == Spyc \/ Link \/ Linked \/ Mount \/ Register \/ Argv \/ Run \/ Done
Spec == Start /\ [][Next]_vars /\ WF_vars(Next)

-----------------------------------------------------------------------------
Finished == pc = "done"
TypeOK == /\ list \in Lists /\ at \in 1..6 /\ undefined \subseteq {"main", "engine", "system"} \cup {Init(n) : n \in Names}
          /\ pc \in {"spyc", "link", "mount", "register", "argv", "run", "done"}
          /\ status \in {"none", "0", "1", "2"} /\ argv \in BOOLEAN /\ ran \in BOOLEAN /\ linked \in BOOLEAN
\* A bad or repeated name is a usage error, and nothing is linked.
Usage == Finished => ((status = "2") <=> ~Accepted(list)) /\ (status = "2" => line = <<>>)
\* An accepted list links exactly when every input defines its init, and
\* a failed link is status 1 with nothing run.
Complete == Finished /\ Accepted(list) => (linked <=> \A k \in 1..Len(list) : list[k].init)
                                         /\ (~linked => status = "1" /\ ~ran)
\* Each module's init is the one its input defines.
Provenance == registered # {} => \A k \in 1..Len(list) : origin[Init(list[k].name)] = k
\* The entry runs with the command line and every module registered.
Started == ran => argv /\ registered = {list[k].name : k \in 1..Len(list)}
Termination == <>Finished
=============================================================================
