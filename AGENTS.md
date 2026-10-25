# slim.py development instructions

Read `/Users/soasme/.codex/RTK.md` when it exists. Prefix shell commands with
`rtk`; use `rtk proxy` when raw output is required. On machines without RTK,
run the equivalent command directly.

## Product and architecture

- Build a small, embeddable Python engine in **C11 only**. The language target
  is Python **3.15**. The earlier 3.14 mention is superseded by that target.
- Use **`spy`** as the public prefix: `spy`, `spyc`, `spy_*`, `SPYContext`,
  `SPYValue`, and `libspy.a`. The project name is slim.py.
- Follow QuickJS's organization: a few understandable C files, a small public
  embedding header, a separate command-line host and executable generator,
  an ordinary Makefile, examples, versioned documentation, and upstream test
  runners. Inspect upstream designs rather than guessing at their structure.
- Runtime dependencies are limited to the C runtime and math library. Do not
  embed, invoke, or link CPython as the implementation. Development tools may
  use Python; this must not become a runtime dependency.
- Keep standard-library modules out of the core. Language builtins, object
  protocols, and import semantics are part of the language and cannot be
  excluded merely because CPython documents them near its standard library.
  Host I/O and optional C library wrappers belong at an explicit host boundary.
- Use reference counting for prompt reclamation and a cycle collector for
  cyclic graphs. Keep C API ownership explicit. Contexts must be independent;
  avoid process-global mutable runtime state.
- Preserve the targets of full syntax/modules/async support, standalone
  executables, a Python-written interactive shell with contextual coloring,
  and very low startup time. Current omissions are implementation gaps, not
  permission to redefine the target standard.
- The few-kilobyte size and sub-300-microsecond lifecycle goals require
  reproducible measurements. Report platform, build flags, measured operation,
  and output treatment. Never present a partial engine's measurements as full
  Python compatibility results.

## Language standard and documentation

- `docs/slimpy.md` is the engine manual, with the same broad organization as
  QuickJS's manual: introduction, usage, specifications, internals, references.
- `docs/standards/3_15.md` is the single-file, versioned language target. Give
  clauses stable identifiers. Pin source revisions and state document status.
  Distinguish normative requirements, host choices, and implementation status.
- Implement the standard faithfully. Never weaken its semantics to make a
  failing test disappear. Arbitrary integers, Unicode, exception behavior,
  scope rules, and evaluation order are requirements, not optional optimizations.
- Do not claim that this project authors an official Python or Ecma standard.
  Python has a language reference, grammar, builtins documentation, and PEPs;
  consolidate and attribute those sources accurately.
- Keep the manual factual. A roadmap item is not an implemented feature. Keep
  compatibility reports separate from normative language requirements.

## Tests and evidence

- Download and inspect **upstream Cython** and relevant CPython tests. Pin
  commits, retain upstream licenses, and provide reproducible fetch/run steps.
  Local tests complement upstream coverage; they do not replace it.
- Preserve upstream source and expected output. Adapter changes must be
  explained. Do not remove imports, decorators, unsupported expressions, or
  assertions to turn an upstream test into a pass.
- Report passed, failed, skipped, and adapter-ineligible cases separately.
  Label pure-Python doctests separately from Cython compiler and C-extension
  tests. Cython compatibility requires a separate CPython C API/ABI effort.
- A missing suite, prerequisite, or failed runner must fail explicitly, not
  report success with zero tests. Never count skips as passes.
- Use strict C11 warnings, meaningful semantic checks, ownership tests, and
  sanitizers. Record environment failures accurately. Do not claim a test ran
  when only a workflow or test target was added.

## Code taste

Follow `/Users/soasme/github.com/soasme/polishing-code/skills/code-taste/SKILL.md`
when available. The enduring requirements are:

- Solve the real problem. Prefer simple, direct code with few concepts.
- Make code readable to a newcomer; hide complexity behind clear operations.
- Avoid speculative frameworks, unnecessary dependencies, and abstractions
  added only for hypothetical future features.
- Keep ownership and failure paths symmetric. Match neighboring conventions.
- Borrow established designs with attribution, then adapt them deliberately.
- Rework awkward code instead of layering patches over it. Before finishing,
  ask what can be deleted, whether the result solves the actual problem, and
  whether it will still make sense years from now.

These preferences do not authorize sending messages, publishing, or pushing
changes. Routine local implementation, testing, and documentation are authorized
by the task and do not require repeated confirmation.
