------------------------------ MODULE SpyBuild ------------------------------
(***************************************************************************)
(* spyc's bundler (docs/build.md), checked against CPython's path finder.  *)
(*                                                                         *)
(* FindIn restates importlib's PathFinder and FileFinder over the search   *)
(* roots (docs/build.md 3.1): in each location a package directory with    *)
(* __init__ first, then a module file, else the directory becomes a        *)
(* namespace portion; a regular package's submodules are searched in its   *)
(* own directory only, a namespace package's in all its portions. The     *)
(* build tests check these rules on the CPython oracle (tests/build,       *)
(* search_order.py and namespace.py).                                      *)
(*                                                                         *)
(* The bundler resolves each import where it stands (3.3): an unguarded    *)
(* import, relative import, or -D name that does not resolve fails the     *)
(* build; a guarded one, or a from-import name that is not a module, is    *)
(* left out (3.4); externals are never visited. It visits the modules it   *)
(* found in any order, adding each to the table and queueing its parent    *)
(* and the modules its imports found (3.2).                                *)
(*                                                                         *)
(* The fixed tree has two roots: a regular package with a subpackage and   *)
(* relative imports, a module beyond the top-level package, a namespace    *)
(* package split across the roots, a module shadowing a later root's       *)
(* package, a submodule in the wrong root, an external whose own import is *)
(* missing, a module only -D reaches, and a cycle. Every choice of         *)
(* externals and -D names is checked, with every visiting order.           *)
(*                                                                         *)
(* The engine asks its loader for NAME.__init__, NAME, NAME.__namespace__ *)
(* in that order (spy.h), and Imports.tla models the import system over    *)
(* that loader. TLC checks that the bundle's table answers those probes as *)
(* the finder does, so a bundled program imports what it would unbundled.  *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

Roots == <<"app", "lib">>

\* Source files as <<root, path>>, the path without ".py".
Main == <<"app", <<"main">>>>
Files == {Main,
          <<"app", <<"pkg", "__init__">>>>, <<"app", <<"pkg", "sub">>>>,
          <<"app", <<"pkg", "inner", "__init__">>>>, <<"app", <<"pkg", "inner", "leaf">>>>,
          <<"app", <<"pkg", "beyond">>>>, <<"app", <<"shadow">>>>, <<"app", <<"ns", "a">>>>,
          <<"app", <<"ext", "__init__">>>>, <<"app", <<"cyc_a">>>>, <<"app", <<"cyc_b">>>>,
          <<"lib", <<"shadow", "__init__">>>>, <<"lib", <<"ns", "b">>>>,
          <<"lib", <<"pkg", "extra">>>>, <<"lib", <<"dyn">>>>}

\* An import names target at a relative level; a from-import's names are
\* "maybe" modules; a guarded import sits in a try that catches ImportError.
Imp(target, level, maybe, guarded) == [target |-> target, level |-> level, maybe |-> maybe, guarded |-> guarded]
Imports(f) ==
    CASE f = Main -> {Imp(<<"pkg", "sub">>, 0, FALSE, FALSE),                   \* import pkg.sub
                      Imp(<<"pkg">>, 0, FALSE, FALSE), Imp(<<"pkg", "helper">>, 0, TRUE, FALSE),  \* from pkg import helper
                      Imp(<<"ns", "a">>, 0, FALSE, FALSE), Imp(<<"ns", "b">>, 0, FALSE, FALSE),
                      Imp(<<"shadow">>, 0, FALSE, FALSE), Imp(<<"ext">>, 0, FALSE, FALSE),
                      Imp(<<"cyc_a">>, 0, FALSE, FALSE),
                      Imp(<<"optional">>, 0, FALSE, TRUE),                      \* try: import optional
                      Imp(<<"pkg", "extra">>, 0, FALSE, TRUE)}                  \* try: import pkg.extra
      [] f = <<"app", <<"pkg", "__init__">>>> -> {Imp(<<>>, 1, FALSE, FALSE), Imp(<<"sub">>, 1, TRUE, FALSE)}   \* from . import sub
      [] f = <<"app", <<"pkg", "sub">>>> -> {Imp(<<"inner">>, 1, FALSE, FALSE), Imp(<<"inner", "leaf">>, 1, TRUE, FALSE)}
      [] f = <<"app", <<"pkg", "inner", "leaf">>>> -> {Imp(<<>>, 2, FALSE, FALSE), Imp(<<"sub">>, 2, TRUE, FALSE)}
      [] f = <<"app", <<"pkg", "beyond">>>> -> {Imp(<<>>, 3, FALSE, FALSE)}      \* from ... import x
      [] f = <<"app", <<"ext", "__init__">>>> -> {Imp(<<"missing_dep">>, 0, FALSE, FALSE)}
      [] f = <<"app", <<"cyc_a">>>> -> {Imp(<<"cyc_b">>, 0, FALSE, FALSE)}
      [] f = <<"app", <<"cyc_b">>>> -> {Imp(<<"cyc_a">>, 0, FALSE, FALSE)}
      [] f = <<"lib", <<"dyn">>>> -> {Imp(<<"cyc_a">>, 0, FALSE, FALSE), Imp(<<"helper">>, 1, FALSE, TRUE)}
      [] OTHER -> {}

ExternalChoices == {<<"ext">>, <<"cyc_a">>}
\* -D names: a module, a submodule in the wrong root, a missing name, the
\* namespace package's modules, and the package's (which reach pkg.beyond).
Include(name, star) == [name |-> name, star |-> star]
Dyn == Include(<<"dyn">>, FALSE)
NsStar == Include(<<"ns">>, TRUE)
IncludeChoices == {{}, {Dyn}, {Include(<<"pkg", "extra">>, FALSE)}, {Include(<<"nosuch">>, FALSE)},
                   {NsStar}, {Include(<<"pkg">>, TRUE)}, {Dyn, NsStar}}

-----------------------------------------------------------------------------
Prefix(p, n) == Len(p) <= Len(n) /\ SubSeq(n, 1, Len(p)) = p
Parent(n) == SubSeq(n, 1, Len(n) - 1)
IsDir(r, d) == \E f \in Files : f[1] = r /\ Len(f[2]) > Len(d) /\ Prefix(d, f[2])

None == [kind |-> "none", file |-> <<>>, locs |-> <<>>]
Found(r) == r.kind # "none"

\* FileFinder over each location in order, keeping namespace portions.
RECURSIVE Search(_, _, _, _)
Search(locs, tail, i, portions) ==
    IF i > Len(locs) THEN
        IF portions = <<>> THEN None ELSE [kind |-> "namespace", file |-> <<>>, locs |-> portions]
    ELSE LET r == locs[i][1]
             d == Append(locs[i][2], tail)
         IN IF <<r, Append(d, "__init__")>> \in Files
                THEN [kind |-> "package", file |-> <<r, Append(d, "__init__")>>, locs |-> <<<<r, d>>>>]
            ELSE IF <<r, d>> \in Files THEN [kind |-> "module", file |-> <<r, d>>, locs |-> <<>>]
            ELSE IF IsDir(r, d) THEN Search(locs, tail, i + 1, Append(portions, <<r, d>>))
            ELSE Search(locs, tail, i + 1, portions)

\* PathFinder: top-level names search the roots, submodules their parent's locations.
RECURSIVE FindIn(_)
FindIn(n) ==
    LET locs == IF Len(n) = 1 THEN [i \in 1..Len(Roots) |-> <<Roots[i], <<>>>>] ELSE FindIn(Parent(n)).locs
    IN Search(locs, n[Len(n)], 1, <<>>)

\* Every module name the tree gives, with its parents, and every name an
\* import or -D asks for; relative imports resolve within the first.
FileName(f) == IF f[2][Len(f[2])] = "__init__" THEN Parent(f[2]) ELSE f[2]
Names == UNION {{SubSeq(FileName(f), 1, k) : k \in 1..Len(FileName(f))} : f \in Files}
Asked == Names \cup {i.target : i \in {j \in UNION {Imports(f) : f \in Files} : j.level = 0}}
               \cup {d.name : d \in UNION IncludeChoices}
\* The finder's answer for every name, computed once.
Finder == [n \in Asked |-> FindIn(n)]

-----------------------------------------------------------------------------
\* Resolution under one choice of externals.
IsExternal(n, ext) == \E x \in ext : Prefix(x, n)

\* The package relative imports resolve against: a package itself, else its
\* parent; the entry script and top-level modules have none (<<>>).
Package(n) == IF Finder[n].kind = "package" THEN n ELSE Parent(n)
\* A relative import with no known parent, or beyond the top-level package.
Unresolvable(i, package) == i.level > 0 /\ (package = <<>> \/ Len(package) < i.level)
\* An import's absolute name (PEP 328).
Resolve(i, package) == IF i.level = 0 THEN i.target ELSE SubSeq(package, 1, Len(package) - (i.level - 1)) \o i.target
Required(i) == ~i.maybe /\ ~i.guarded

\* The names one source file's imports ask for, externals aside, and
\* whether one of them fails the build where it stands.
Asks(f, package, ext) ==
    {n \in {Resolve(i, package) : i \in {j \in Imports(f) : ~Unresolvable(j, package)}} : ~IsExternal(n, ext)}
ScanFails(f, package, ext) ==
    \E i \in Imports(f) : Required(i) /\
        (Unresolvable(i, package) \/ (~IsExternal(Resolve(i, package), ext) /\ ~Found(Finder[Resolve(i, package)])))
Scan(f, package, ext) == {n \in Asks(f, package, ext) : Found(Finder[n])}

\* -D: a name must resolve; a star needs a package and gives every module below it.
Includes(inc) ==
    {d.name : d \in {e \in inc : ~e.star}}
    \cup {m \in Names : \E d \in inc : d.star /\ Len(m) > Len(d.name) /\ Prefix(d.name, m)
                                        /\ Finder[m].kind \in {"package", "module"}}
IncludesFail(inc) ==
    \E d \in inc : IF d.star THEN Finder[d.name].kind \notin {"package", "namespace"} ELSE ~Found(Finder[d.name])

Source(n) == Finder[n].file

VARIABLES externals, includes, pending, table, failed
vars == <<externals, includes, pending, table, failed>>

Init ==
    /\ externals \in SUBSET ExternalChoices
    /\ includes \in IncludeChoices
    /\ pending = Scan(Main, <<>>, externals) \cup {n \in Includes(includes) : Found(Finder[n])}
    /\ table = {}
    /\ failed = (ScanFails(Main, <<>>, externals) \/ IncludesFail(includes))

\* Visit one found module: add it, queue its parent and what its imports found.
Visit(n) ==
    LET parent == IF Len(n) > 1 THEN {Parent(n)} ELSE {}
        asks == IF Source(n) = <<>> THEN {} ELSE Scan(Source(n), Package(n), externals)
    IN /\ ~failed
       /\ table' = table \cup {n}
       /\ pending' = (pending \cup parent \cup asks) \ table'
       /\ failed' = (Source(n) # <<>> /\ ScanFails(Source(n), Package(n), externals))
       /\ UNCHANGED <<externals, includes>>

\* A build ends: each visit adds a module to the finite table. Done
\* stutters, so TLC's deadlock check finds any other stuck state.
Done == failed \/ pending = {}
Next == (\E n \in pending : Visit(n)) \/ (Done /\ UNCHANGED vars)
Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
\* The declarative bundle (3.2): the least set closed under parents and imports.
Edges(n, ext) ==
    (IF Len(n) > 1 THEN {Parent(n)} ELSE {}) \cup (IF Source(n) = <<>> THEN {} ELSE Scan(Source(n), Package(n), ext))
RECURSIVE Fix(_, _)
Fix(S, ext) == LET T == S \cup UNION {Edges(n, ext) : n \in S} IN IF T = S THEN S ELSE Fix(T, ext)
ClosureOf(ext, inc) == Fix(Scan(Main, <<>>, ext) \cup {n \in Includes(inc) : Found(Finder[n])}, ext)
\* Every name the bundled sources ask for, guarded misses included.
AskedOf(ext, inc) ==
    Asks(Main, <<>>, ext) \cup UNION {IF Source(n) = <<>> THEN {} ELSE Asks(Source(n), Package(n), ext) : n \in ClosureOf(ext, inc)}
FailsOf(ext, inc) ==
    \/ ScanFails(Main, <<>>, ext) \/ IncludesFail(inc)
    \/ \E n \in ClosureOf(ext, inc) : Source(n) # <<>> /\ ScanFails(Source(n), Package(n), ext)
\* The expected outcome of every build, computed once.
Expected == [c \in (SUBSET ExternalChoices) \X IncludeChoices |->
                [closure |-> ClosureOf(c[1], c[2]), asked |-> AskedOf(c[1], c[2]), fails |-> FailsOf(c[1], c[2])]]
Outcome == Expected[<<externals, includes>>]

\* The loader's keys (5.1), and what the engine makes of probing them in
\* order: a package, a module, a namespace package, or nothing.
Suffix(kind) == CASE kind = "package" -> "__init__" [] kind = "module" -> "" [] kind = "namespace" -> "__namespace__"
Keys == {[name |-> n, suffix |-> Suffix(Finder[n].kind)] : n \in table}
Probe(n) ==
    IF [name |-> n, suffix |-> "__init__"] \in Keys THEN [kind |-> "package", file |-> Source(n)]
    ELSE IF [name |-> n, suffix |-> ""] \in Keys THEN [kind |-> "module", file |-> Source(n)]
    ELSE IF [name |-> n, suffix |-> "__namespace__"] \in Keys THEN [kind |-> "namespace", file |-> <<>>]
    ELSE [kind |-> "none", file |-> <<>>]
\* What the finder gives an unbundled program.
Answer(n) == [kind |-> Finder[n].kind, file |-> Finder[n].file]

TypeOK ==
    /\ externals \subseteq ExternalChoices /\ includes \in IncludeChoices
    /\ table \subseteq Names /\ pending \subseteq Names /\ failed \in BOOLEAN

\* The build fails exactly when a required import or -D name does not resolve.
FailsCorrectly == Done => (failed <=> Outcome.fails)
\* Any visiting order gives the declarative bundle.
Deterministic == (Done /\ ~failed) => table = Outcome.closure
ParentsBundled == (Done /\ ~failed) => \A n \in table : Len(n) > 1 => Parent(n) \in table
NothingExternal == \A n \in table : ~IsExternal(n, externals)
\* Every name the bundled sources ask for, guarded misses included, gets
\* the finder's answer from the loader; externals are left to the host.
Transparent == (Done /\ ~failed) => \A n \in Outcome.asked : Probe(n) = Answer(n)
\* Any other name, such as a computed import's, is the finder's or unanswered:
\* the bundle never gives a different module.
Sound == \A n \in Asked : Probe(n) \in {Answer(n), [kind |-> "none", file |-> <<>>]}
=============================================================================
