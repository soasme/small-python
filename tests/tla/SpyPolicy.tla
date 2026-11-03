----------------------------- MODULE SpyPolicy -----------------------------
(***************************************************************************)
(* spy's host policy and output limit (manual 3.4.6), as spy.c implements  *)
(* them. TLC checks that what the host promised holds after every step:    *)
(*                                                                         *)
(*  - An outermost call prints at most the output limit in force at each   *)
(*    write, even when a host function lowers the limit mid-call; then     *)
(*    the call halts and its except clauses cannot resume it. The next     *)
(*    outermost call starts with nothing printed.                          *)
(*  - A file is opened, source executed, input read, or a module loaded    *)
(*    only when no policy is set or the policy allowed that event: it      *)
(*    returned 0 and set no error. A refusal raises the error the policy   *)
(*    set, or else PermissionError, which Python code may catch.           *)
(*  - A module is asked about only while it is not loaded, so a refused    *)
(*    import is asked again and a loaded one never is.                     *)
(*                                                                         *)
(* The implementation, step by step (names are spy.c's):                   *)
(*                                                                         *)
(*  - enter resets output_used and the stop for the outermost call only.   *)
(*  - output_write halts with SPY_STOP_OUTPUT when the limit is set and    *)
(*    output_used is past it or the text does not fit in what is left;     *)
(*    otherwise it adds the length to output_used and writes. size_t       *)
(*    arithmetic wraps, modelled modulo Wrap: without the first test, a    *)
(*    limit lowered below output_used left a huge remainder.               *)
(*  - halt sets the stop and spends the fuel, so every later step stops    *)
(*    again until the outermost call returns.                              *)
(*  - spy_policy_check calls the policy; unless it returned 0 with no      *)
(*    error set, errorf raises PermissionError, which keeps an error the   *)
(*    policy set.                                                          *)
(*  - load_source_module returns a cached module before asking "import";   *)
(*    a refused module is not cached.                                      *)
(***************************************************************************)
EXTENDS Naturals

CONSTANTS Limits,   \* output limits the host may set; 0 is unlimited
          Sizes,    \* lengths of one write
          Mods,     \* module names
          Wrap      \* the modulus of size_t, scaled down

Events == {"open", "exec", "input"}
Errors == {"", "PermissionError", "Custom", "RuntimeError"}

VARIABLES limit, used, stopped, entries, err, cache, policy,   \* spy.c's
          written, over, breach, misnamed, granted              \* ghosts

vars == <<limit, used, stopped, entries, err, cache, policy, written, over, breach, misnamed, granted>>
ghosts == <<over, breach, misnamed, granted>>

Init == /\ limit \in Limits /\ used = 0 /\ stopped = FALSE /\ entries = 0 /\ err = ""
        /\ cache = {} /\ policy \in BOOLEAN
        /\ written = 0 /\ over = FALSE /\ breach = FALSE /\ misnamed = FALSE /\ granted = {}

\* Python code runs: inside a call, with no error pending and no stop.
Running == entries > 0 /\ err = "" /\ ~stopped

\* The host's outermost call: enter starts it fresh. The host cleared the
\* last call's error.
Call == /\ entries = 0
        /\ entries' = 1 /\ used' = 0 /\ stopped' = FALSE /\ err' = "" /\ written' = 0
        /\ UNCHANGED <<limit, cache, policy, over, breach, misnamed, granted>>

\* Python calls a host function, which may call back in, print, and change
\* the limit or the policy; enter at depth > 0 resets nothing.
HostFunction == /\ Running /\ entries = 1 /\ entries' = 2
                /\ UNCHANGED <<limit, used, stopped, err, cache, policy, written, ghosts>>

Return == /\ entries > 0 /\ entries' = entries - 1
          /\ UNCHANGED <<limit, used, stopped, err, cache, policy, written, ghosts>>

\* spy_set_limit(SPY_LIMIT_OUTPUT) and spy_set_policy, between calls or from
\* a host function.
SetLimit(v) == /\ entries # 1 /\ limit' = v
               /\ UNCHANGED <<used, stopped, entries, err, cache, policy, written, ghosts>>
SetPolicy == /\ entries # 1 /\ policy' = ~policy
             /\ UNCHANGED <<limit, used, stopped, entries, err, cache, written, ghosts>>

\* output_write of n bytes.
Halts(n) == limit # 0 /\ (used > limit \/ n > (limit + Wrap - used) % Wrap)
Print(n) == /\ Running /\ used + n < Wrap
            /\ IF Halts(n)
               THEN /\ stopped' = TRUE /\ err' = "RuntimeError"
                    /\ UNCHANGED <<used, written, over>>
               ELSE /\ used' = used + n /\ written' = written + n
                    /\ over' = (over \/ (limit # 0 /\ written + n > limit))
                    /\ UNCHANGED <<stopped, err>>
            /\ UNCHANGED <<limit, entries, cache, policy, breach, misnamed, granted>>

\* spy_policy_check when the policy returns r and sets its own error or not.
\* The result is the error left pending, "" when the event may go ahead.
Check(r, sets) == LET pending == IF sets THEN "Custom" ELSE ""
                  IN IF r = 0 /\ pending = "" THEN ""
                     ELSE IF pending # "" THEN pending ELSE "PermissionError"
\* What the host was promised.
Allowed(r, sets) == r = 0 /\ ~sets
Named(r, sets) == IF sets THEN "Custom" ELSE "PermissionError"

\* open, exec/eval/compile of source, input: the effect happens when the
\* check leaves no error.
Ask(r, sets) == /\ Running /\ r \in {0, 1} /\ sets \in BOOLEAN /\ (policy \/ (r = 0 /\ ~sets))
                /\ LET e == IF policy THEN Check(r, sets) ELSE ""
                   IN /\ err' = e
                      /\ breach' = (breach \/ (e = "" /\ policy /\ ~Allowed(r, sets)))
                      /\ misnamed' = (misnamed \/ (e # "" /\ e # Named(r, sets)))
                /\ UNCHANGED <<limit, used, stopped, entries, cache, policy, written, over, granted>>

\* import m: a cached module is returned unasked; otherwise the policy is
\* asked and an allowed module is loaded and cached.
Import(m, r, sets) ==
    /\ Running /\ r \in {0, 1} /\ sets \in BOOLEAN /\ (policy \/ (r = 0 /\ ~sets))
    /\ IF m \in cache
       THEN UNCHANGED <<err, cache, breach, misnamed, granted>>
       ELSE LET e == IF policy THEN Check(r, sets) ELSE ""
            IN /\ err' = e
               /\ cache' = IF e = "" THEN cache \cup {m} ELSE cache
               /\ granted' = IF ~policy \/ Allowed(r, sets) THEN granted \cup {m} ELSE granted
               /\ breach' = (breach \/ (e = "" /\ policy /\ ~Allowed(r, sets)))
               /\ misnamed' = (misnamed \/ (e # "" /\ e # Named(r, sets)))
    /\ UNCHANGED <<limit, used, stopped, entries, policy, written, over>>

\* except catches a refusal; a stop spends the fuel, so it runs nothing.
Catch == /\ entries > 0 /\ err \in {"PermissionError", "Custom"} /\ ~stopped /\ err' = ""
         /\ UNCHANGED <<limit, used, stopped, entries, cache, policy, written, ghosts>>

Next == \/ Call \/ HostFunction \/ Return \/ SetPolicy \/ Catch
        \/ \E v \in Limits : SetLimit(v)
        \/ \E n \in Sizes : Print(n)
        \/ \E r \in {0, 1}, sets \in BOOLEAN : Ask(r, sets) \/ \E m \in Mods : Import(m, r, sets)

Spec == Init /\ [][Next]_vars

TypeOK == /\ limit \in Limits /\ used \in 0..Wrap /\ stopped \in BOOLEAN /\ entries \in 0..2
          /\ err \in Errors /\ cache \subseteq Mods /\ policy \in BOOLEAN

\* No write took an outermost call past the limit in force.
OutputBounded == ~over
\* output_used counts what this outermost call printed.
UsedIsWritten == used = written
\* A stop raises RuntimeError and stays until the outermost call returns.
StopSticks == stopped => err = "RuntimeError"
\* Effects happen only when allowed; refusals raise the promised error.
PolicyGates == ~breach
RefusalNamed == ~misnamed
\* A cached module was loaded with the policy's leave.
CacheGranted == cache \subseteq granted
=============================================================================
