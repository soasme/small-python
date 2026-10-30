# Small Python development instructions

## Product and architecture

- Build a small, embeddable Python engine in **C11 only**. The language target
  is Python **3.15**. The earlier 3.14 mention is superseded by that target.
- Use **`spy`** as the public prefix: `spy`, `spyc`, `spy_*`, `SPYContext`,
  `SPYValue`, and `libspy.a`. The project name is Small Python.
- Follow QuickJS's organization: a few understandable C files, a small public
  embedding header, a separate command-line host and executable generator,
  an ordinary Makefile, examples, versioned documentation, and upstream test
  runners. Inspect upstream designs rather than guessing at their structure.
- Runtime dependencies are limited to the C runtime and math library. Do not
  embed, invoke, or link CPython as the implementation. Development tools may
  use Python; this must not become a runtime dependency.
- Prefer the pinned Python 3.15 interpreter for semantic comparisons when it
  is available. Do not copy older host-version diagnostics or representations
  into the target runtime merely to satisfy a local differential test.
- After any user conversion callback, re-read mutable container size and data
  before bounds checks or memory access. Shared builtin argument parsing must
  handle unnamed positional-only parameters without dereferencing name tables.
- Keep standard-library modules out of the core. Language builtins, object
  protocols, and import semantics are part of the language and cannot be
  excluded merely because CPython documents them near its standard library.
  Host I/O and optional C library wrappers belong at an explicit host boundary.
  The `open` builtin is the one file service in the core, and it reaches only
  directories the host mounted with `spy_mount`; keep every new path check
  inside `mount_resolve` and never expose descriptors the context did not open.
  Modules are registered QuickJS-style: `spy_new_module(ctx, name, init)`
  (like `JS_NewCModule`), with `init` filling the module on first import.
  `spy.c`/`spy.h` hold no module but `builtins`; every other module is the
  embedder's choice. `spy_init_primitives` fills a host-registered module
  (`_spy`) with the engine primitives (module cache, weak table, frames,
  collection, limits, host output); add a primitive only when a host module
  cannot be written without it. The standard layer `spy-std.c` (like
  `quickjs-libc.c`) supplies the host modules `sys`, `gc`, and `weakref` (with
  its primitive half `_weakref`) on them through the public API. Their Python
  sources are in `modules/`, embedded in `spy-std-modules.h` by
  `tools/build_intrinsics.py`. The `spy` command links the standard layer and
  `spyc -M` selects from it; `libspy.a` does not. Conformance runs on
  `tests/run-spec` (like `run-test262`), the bare core with only `_spy`; tests
  reach host facilities through the harness's `host`, never a library module.
- Work on the language core, not the library. Do not add further standard
  library modules (`math`, `_struct`, `_sre`, `os`, `array`, ...), even when a
  CPython test imports one; skip tests that are blocked only by a missing
  module and raise pass rates by fixing core semantics instead. Add a module
  only when the user explicitly asks for it. The same holds inside the
  existing modules: do not grow `sys`, `gc`, `weakref` and the rest with more
  library surface (hooks, structseqs, helpers) just because a test reaches for
  it; the engine reports core behavior such as ignored exceptions itself.
- Cache at most one released tuple allocation for each length zero through
  eight inside its owning context. Cached storage owns no element references,
  is excluded from the live-value graph, and is freed during context shutdown.
- Use reference counting for prompt reclamation and a cycle collector for
  cyclic graphs. Keep C API ownership explicit. Contexts must be independent;
  avoid process-global mutable runtime state.
- Suspend generator functions with heap-owned operand and cleanup stacks.
  Keep every retained stack value visible to the cycle collector. Instructions
  borrow original AST nodes from a retained source unit; never retain temporary
  copies of definition nodes. Preserve evaluation order and cleanup across
  `yield`, delegation, exceptions, returns, and loop exits.
- Reuse those suspension and cleanup stacks for coroutines and asynchronous
  generators. Distinguish yielding a value from suspending an await; track an
  async-generator operation across suspension to reject concurrent resumes.
  Keep await wrappers and their arguments visible to cycle collection.
- Keep comprehension loops on that same execution machinery. Acquire the first
  iterator eagerly in the outer scope; preserve lazy generator-expression bodies
  and distinguish ordinary comprehension exceptions from generator termination.
- Keep import syntax and relative-name resolution in the core, filesystem search
  in the host loader, and import-hook lookup in the frame's builtin namespace.
  Cache modules before executing them and remove failed initializations.
- Keep small integers inline and arbitrary magnitudes in owned limbs. Check
  host-width conversions explicitly; never use stack-shaped values where a
  numeric operation may retain its operand.
- Share exact quotient rounding between numeric division and decimal rounding.
  Preserve ties to even and signed zero without depending on the host's current
  floating-point rounding mode or an inexact decimal multiplication.
- Build symbol tables before execution. Lexical environments must retain the
  source units owning their symbol tables. Keep class namespace lookup separate
  from method closures, and mangle private names in the parser's class context.
- Evaluate decorators before defaults/bases, then apply them in reverse order.
  Keep descriptor lookup and method binding shared by normal attributes and
  special-method calls; trace all wrapper and property fields during collection.
- Expose actual dictionaries for module globals. Class and explicit execution
  locals retain their original mappings and dispatch through mapping methods.
  Missing lookups fall back only on KeyError; DELETE_NAME converts deletion
  errors into NameError. Dictionary-subclass globals dispatch reads through
  __getitem__, while global writes/deletes use dictionary storage. Optimized
  function locals are snapshots. Keep intrinsic exception
  classes rooted separately from the user-mutable builtin namespace.
- Function binding must read the exposed positional-default tuple and keyword-
  default dictionary. Keep code metadata attached to its owning parsed unit so
  it remains valid after the function is released.
- Cache code objects per parsed definition. Functions created from the same
  definition and their suspended instances share that identity. Closed
  generators retain their code while releasing execution environments; trace
  the source-unit/code cache cycle explicitly.
- Suspended instances snapshot the creating function's exposed name and
  qualified name. Retain both through closure and close; later renaming either
  object is independent. Trace string-subclass names through cycle collection.
- Class calls invoke `__new__` before initialization. Initialize only a returned
  instance of the requested class, using the returned instance's actual type.
  Wrap plain `__new__` functions as static methods when building the class.
- Honor metaclass __prepare__ on any callable, preserve namespace callback
  order, and pass the original mapping to the metaclass. Native type.__new__
  copies dictionary-subclass storage without invoking its mapping overrides.
  Collect class static attributes during scope analysis; their names retain
  unmangled spelling. Keep borrowed AST links distinct from owned scope fields.
- Invoke custom metaclass mro methods before class finalization. Explicit
  type.mro computes C3 from the bases independently of the installed MRO.
  Reject empty orders, non-class entries, and incompatible builtin layouts.
- Compute default C3 method resolution during class construction and share it among
  attribute lookup, subclass checks, special methods, and `super`. Trace bases,
  MROs, bound super objects, and class cells through cycle collection.
- Class headers share call-argument grammar and evaluation order. Finalize classes
  through one path: wrap implicit methods, notify an owned namespace snapshot
  with `__set_name__`, then invoke the inherited `__init_subclass__`. Preserve
  the original callback exception and add its Python 3.15 diagnostic note.
- Keep the lexical `__class__` cell separate from the class namespace. Methods
  retain it through their closure; a class attribute with the same spelling
  must not replace the cell used by zero-argument `super()`.
- Attribute deletion and `delattr` share descriptor and metadata rules. Deleting
  function defaults resets their metadata and immediately changes call binding.
- Instance attribute reads, writes and deletions dispatch through type-level
  interception hooks. The explicit `object` methods reach default operations
  without redispatch. Implicit special-method lookup bypasses interception.
- Validate keywords in call order before reporting excess positional arguments
  or filling defaults. Preserve exception and assertion objects through ordinary
  and suspended execution; do not replace assertion arguments with formatted text.
- Sort keys are evaluated once in input order. Preserve stable ordering in both
  directions and retain keys across comparison callbacks and failure cleanup.
  Detach a list's contents while sorting so callbacks see an empty list; keep
  the detached contents traced and detect mutations before restoring them.
- Share operator dispatch between ordinary and suspended execution. Preserve
  reflected subclass priority, NotImplemented fallback, target evaluation order,
  and the identity of mutable containers during augmented assignment.
- Rich comparisons may return arbitrary objects or mutate their operands.
  Retain compared elements across callbacks, recheck collection positions after
  callbacks, and preserve identity shortcuts used by container lookup.
- Dictionary/set entries retain the hash computed on insertion. Call a lookup
  key's hash once, compare only matching hashes, and reuse stored hashes for
  copies, dictionary merges, and equality. Recheck positions after comparison
  callbacks. Preserve equal numeric values' hash equality across types.
- Frozen dictionaries share dictionary storage and lookup. Build them privately,
  then reject every exposed mutation path, including global writes and deletes.
  Hash item pairs with stored key hashes and cache only a completed hash. Copies
  and unions must distinguish exact frozen values from subclass backing storage.
- Mapping proxies are native C values retaining a live mapping. Class __dict__
  and dictionary-view mapping attributes share this read-only wrapper. Follow
  Python 3.15's exact-dictionary copying rule for reflected equality callbacks;
  callbacks must not receive a mutable builtin class namespace through equality.
- The inherited implementation currently embeds intrinsics.py through
  spy-intrinsics.h and executes it on this engine for generic/type objects.
  This requires no external Python runtime, but language semantics implemented
  in Python remain a gap against the requested C11-only implementation. Do not
  describe them as C implementations. Preserve their behavior and tests when
  moving them into C. Fingerprint both source and generated header in reports.
- Generate Unicode properties from the pinned oracle into checked-in C data.
  Ordinary builds must not require Python or the generator. Retain the Unicode
  license and verify the table against all code points.
- Normalize source identifiers with Unicode NFKC before scope analysis and
  private-name mangling. Preserve spelling in dynamic string names. Validate
  source UTF-8 independently of the host locale; include generated tables in
  upstream report hashes.
- Decode source bytes and host-loaded files in the core. Honor PEP 263 comments
  and UTF-8 BOMs before parsing; Unicode string inputs ignore encoding comments.
  Normalize CR/CRLF before tokenization, including inside string literals.
  Indentation uses eight-column tab stops and a second one-column count to
  reject inconsistent mixing; blank and comment-only lines do not change it.
- Keep buffered output and flushing at the host callback boundary. Optional
  Python file objects use their `write` and `flush` methods.
- Template strings use native C Template and Interpolation values. Retain raw
  interpolation values and source spelling; conversions remain metadata. Evaluate
  format specifications with the shared formatted-string machinery. Trace every
  retained value through GC, including template iterators and suspended fields.
- Preserve the targets of full syntax/modules/async support, standalone
  executables, a Python-written interactive shell with contextual coloring,
  and very low startup time. Current omissions are implementation gaps, not
  permission to redefine the target standard.
- The few-kilobyte size and sub-300-microsecond lifecycle goals require
  reproducible measurements. Report platform, build flags, measured operation,
  and output treatment. Never present a partial engine's measurements as full
  Python compatibility results.

## Language standard and documentation

- `docs/manual.md` is the engine manual, with the same broad organization as
  QuickJS's manual: introduction, usage, specifications, internals, references.
- `docs/standards/3_15.md` is the single-file, versioned language target,
  written in the style of ECMA-262: numbered clauses, abstract operations, and
  algorithm steps. It depends on no library module; library facilities are
  intrinsics or host hooks (Annex B), and library facades are informative
  (Annex C). Verify every message and behaviour it states against the pinned
  CPython. Distinguish normative requirements, host choices, and
  implementation status.
- Implement the standard faithfully. Never weaken its semantics to make a
  failing test disappear. Arbitrary integers, Unicode, exception behavior,
  scope rules, and evaluation order are requirements, not optional optimizations.
- Do not claim that this project authors an official Python or Ecma standard.
  Python has a language reference, grammar, builtins documentation, and PEPs;
  consolidate and attribute those sources accurately.
- Keep the manual factual. A roadmap item is not an implemented feature. Keep
  compatibility reports separate from normative language requirements.

## Tests and evidence

- Conformance to PLS-315 is established by the specification tests in
  `tests/spec` and the TLA+ models in `tests/tla`, and by nothing else. Both
  model the standard; neither depends on the upstream CPython tree at run time.
- Spec tests are test262-style: small, self-checking, core-only scripts that
  name the clauses they exercise. Write each from the standard's text, then run
  it on spy and on the pinned CPython oracle (`make test-spec-oracle`). When
  both fail the same way, the standard or the test is wrong; when only spy
  fails, spy is wrong. Every clause must keep a test (`tests/spec_coverage.py`).
- Port CPython's language tests into `tests/spec/ports`: copy the module once,
  replace each library import by a core equivalent, and mark every change
  "(Ported)". A test of a library facility is not ported. Do not delete
  assertions to make a port pass; fix spy or, if CPython disagrees with the
  standard, the standard.
- Upstream Cython tests are a separate compatibility baseline. Pin commits,
  retain upstream licenses, and report passed, failed, and adapter-ineligible
  cases separately; Cython compatibility requires a separate CPython C API/ABI
  effort.
- Build pinned CPython out of tree as a development oracle. Keep it under
  ignored `tests/upstream/`; never make it an engine or test dependency.
- A missing suite, prerequisite, or failed runner must fail explicitly, not
  report success with zero tests. Never count skips as passes.
- Use strict C11 warnings, meaningful semantic checks, ownership tests, and
  sanitizers. Record environment failures accurately. Do not claim a test ran
  when only a workflow or test target was added.
- When a tool does not work on macOS, run it in a Linux Docker container
  instead (e.g. `python:3.14` plus `apt-get install clang`) on a copy of the
  tree, not the mounted checkout. AddressSanitizer hangs at startup on this
  macOS, so `make sanitize` and `make libfuzzer` (see fuzz/README) run there.
- Memory checks beyond `make sanitize` run locally when asked or when a change
  touches C, not in CI. Fuzz with `make fuzz FUZZ_SECONDS=600` (eval, compile,
  spyc, and allocation-failure targets), then `make fuzz-replay` to rerun the
  kept inputs under MemorySanitizer; `make CC=clang SANITIZERS=memory
  sanitize` runs the tests under it, and `make coverage` shows what nothing
  executes. They need clang with compiler-rt (Ubuntu: `libclang-rt-18-dev`).
  A finding lands in `.obj/fuzz/`; reproduce it with `./fuzz/<target> FILE`,
  fix the engine, and keep the input as a test.

## Code taste

Before you finish, ask:

- What can I delete until nothing cannot be deleted?
- Would a newcomer read this without help?
- Did I solve the real problem?
- Did I followed YAGNI (You ain't gonna need it)?
- Does it match its neighbours?

Trust your discomfort. If something feels ugly, find out why and fix it. Check what means not ugly:

* **Is simple.** Remove parts until nothing more can go. As few concepts and branches as possible.
* **Solves the right problem.** Check the problem first. A neat answer to the wrong question is waste.
* **Looks easy.** Hard work hides behind a clear result. Keep refining until it 
* **Is timeless.** Prefer designs that will still make sense in ten years over fashion.
* **Uses symmetry.** Make similar things look and behave alike. Break the pattern only for a reason.
* **Fits its parts to the whole.** Follow how the system already works. Do not fight it.
* **Is suggestive.** A good core makes the next feature obvious. Prefer general tools over special cases.
* **Is strong, not fussy.** Skip needless ornament, config, comment and abstration.
* **Is redesigned.** Expect the first draft/implementation to be wrong. Rewrite it when you see better.
* **Can borrow.** Copy good designs, then adopt. Imitation teaches taste.
* **May be odd.** A bold or unusual choice is fine when it is simpler or truer.
* **Polishing.** Good code does not yield once at a time. They come after iterations until no extra can be simplified or trimmed.

These preferences do not authorize sending messages, publishing, or pushing
changes. Routine local implementation, testing, and documentation are authorized
by the task and do not require repeated confirmation.

## Workflow

* Commit as often as you can when you made progress.
* Run bench and update docs before release a new version.
* Commit message should come with a brief of test or bench results.
