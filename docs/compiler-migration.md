# Direct source-to-bytecode compilation

The target is one parse of the source that emits executable instructions,
without constructing an executable syntax tree and walking it afterward.
Symbol and label resolution may patch emitted instructions. They must not
reparse the source or traverse an AST. This migration is incomplete.

## Current checkpoint

Constant loads now carry their value as an instruction operand.
The constant path of `BC_LOAD` retains that value onto the machine's operand stack without
calling `eval` or reading the value through an AST node. It shares storage
with branch operands; `Instruction` remains 32 bytes on arm64. The source
unit still owns and traces the constant through its node. Instructions
borrow it, and the executing frame retains the unit.

The compiler recognizes a materialized constant before asking whether its
expression needs machine steps. Name loads keep their existing lookup and
fallback behavior. Source locations, tracing and pause accounting still use
the original node.

This is preparation for a different compiler, not its completion. The parser
still builds `Node` trees. Scope analysis, `compile_expr`, `compile_body`,
metadata queries and several instruction implementations still walk them.
`BC_EVAL`, `BC_EXEC` and `BC_BLOCK` still execute trees. No claim of a
single-pass compiler or general speedup follows from this checkpoint.

## Remaining stages

1. Separate the remaining executable operands and definition records from
   source-location metadata. Preserve the existing fast paths while moving
   their operands out of tree links. Put constants and names in storage
   owned and traced by their code, including failure cleanup.
2. Emit expressions and statements from the parser. Collect bindings and
   declaration locations as each scope is parsed; resolve forward local,
   global, nonlocal and cell references by patching instructions. Branches
   use labels, and assignment parsing keeps target descriptors. Deferred
   annotations, comprehension bodies and reordered argument evaluation need
   instruction fragments that can be placed in their execution order.
3. Move the remaining executable subtrees onto the instruction machine,
   including interactive and expression input. Preserve heap frames and
   cleanup stacks for every call, generator, coroutine and comprehension.
   Remove tree execution instructions and their walker implementations.
4. Build code metadata from code records and recorded symbol uses. Remove
   executable tree allocation, scope tree walks and node-based code caches.
   Keep source spans and definition identity without retaining a tree.

Each stage must preserve Python 3.15 semantics and report its own measured
cost. Compiling every operation in the existing pausing mode is not an
acceptable substitute for this work: it changes the runtime costs without
removing the AST compiler.

## Evidence required

Before changing each stage, identify the affected cases in these groups:

- Binding order and diagnostics: reads before later assignments, `global`
  and `nonlocal`, class cells, private names, annotations, comprehension
  scopes, invalid syntax and competing errors.
- Execution order: short circuits, comparison chains, decorators, defaults,
  keyword and starred arguments, assignment targets and exception cleanup.
- Lifetime and suspension: constants, closures, code identity, source spans,
  collection during callbacks, suspended generators, coroutines and async
  generators, tracing, pause/resume and allocation failures.
- Cost: compilation and release, execution of already compiled code,
  end-to-end benchmarks, executable size and retained memory. Alternate old
  and new executables over rounds; do not report noisy differences as wins.

`tests/spec/execution/constant_lifetime.py` and the `ConstantLoads` TLA+
model exercise the checkpoint's constant lifetime through functions,
generators and coroutines. The model replays are semantic checks; they do
not prove the instruction representation. The full spec and model suites,
C API tests, allocation-failure tests and sanitizer runs remain required.
Platform claims require native checks on that platform.

The 2026-11-22 checkpoint passed 1,040 specification tests on macOS arm64,
with no invalid tests on the pinned Python 3.15.2 oracle, and all 157 TLA+
models. The C API and metering probes passed. Allocation-failure tests
passed all 205 programs, imports and intrinsic initialization. The same
1,040 specification tests passed with Clang 18 AddressSanitizer and
UndefinedBehaviorSanitizer on native Linux arm64 in Docker. That run
exposed an existing zero-argument cleanup path that computed `NULL + 0`;
the checkpoint also guards that empty range. The full allocation-failure
run preceded that guard; specification, API, metering and sanitizer checks
used it.

A separate Clang coverage build ran the new lifetime test: the instruction
constant branch ran 23 times and its name branch ran 119 times. This is
targeted coverage, not complete engine coverage. Full sanitizer targets,
fuzzing, MemorySanitizer replay, ThreadSanitizer and full engine coverage
are separate checks; a passing specification run does not establish them.

`bench/compiler.c` and `bench/compiler.py` measure compilation separately
from repeated execution. See [benchmark.md](benchmark.md) for the method
and results. The compilation measurement currently includes parsing, scope
analysis, eager function instruction generation and code release. Module
instructions are still generated on first execution, so this is not yet a
measurement of complete source-to-bytecode compilation.

## Design source

QuickJS at the revision in `tests/upstream.json`,
`7d1c13c5d8f8c6b32893786ed35cdcebd88194d2`, was inspected for its parser and
compiler organization. In `quickjs.c`, `js_parse_expr_binary` emits
operations during parsing, `emit_push_const` records constant-pool indices,
and `js_create_function` runs `resolve_variables` and `resolve_labels` over
the emitted code. This informs the design; Python's binding, annotation and
comprehension semantics still require their own implementation. Its license
is retained in [licenses/quickjs.txt](licenses/quickjs.txt).
