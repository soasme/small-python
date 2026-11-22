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

The second stage records three code properties during parsing: whether the
current function contains a yield, the location of its first valued return
in compiler diagnostic order, and whether a statement writes through a
module or class namespace. Function bodies get their scope record before
binding analysis; binding analysis fills that record and resolves its parent.
Decorators and defaults remain in the enclosing parser context, while
nested function, lambda and class bodies have their own context. Formatted
string fields inherit that context.

This removes the recursive `namespace_bindings` and `check_async_return`
walkers and the generator-detection walk from `compile_generator`. The
return diagnostic still follows binding errors and preserves Python 3.15's
ordering between try suites and handlers. Recording yields before dropping
optimized assertions also fixes generator classification under `-O` and
`-OO`. Symbol binding and instruction emission still traverse trees; this
stage does not claim to have completed the direct compiler.

The third stage gives name loads their own `BC_NAME` instruction. Its
operand holds the spelling and lookup cache; the lookup helpers accept
that record rather than a syntax node. Both constant and name loads now
read their instruction operands directly. A `BC_NAME` cache miss continues on
the machine, including Python namespace lookups and key comparisons,
instead of falling back to `eval`. The instruction still borrows its
source-location node for tracing and diagnostics.

The name record currently lives inside its source node, with the same
ownership and tracing of its cached dictionary key. This extraction adds
no allocation and leaves `Instruction` at 32 bytes and `Node` at 312 bytes
on arm64. Other instructions and the parser still depend on trees. The
next ownership change must move these records into code-owned storage
before those nodes can be removed.

The fourth stage removes tree reads from fused operators. An operator on
operands at hand (a literal, a name, an item of those, or a name's
attribute) compiles to a fused `BC_OPERATE` followed by its plain steps:
the operands' loads and the operator's `BC_BINARY`, `BC_COMPARE` or
`BC_INDEX`. The fused step reads its operands from those loads' operands,
and jumps past them when it computes the result without running Python
code. Otherwise it falls through, and the plain steps evaluate the
operator on the machine. A truth test fuses with the `BC_FALSE` after the
plain steps into `BC_TEST`, sharing its target. Neither step evaluates a
tree or calls Python code, so the machine paths that resumed them after a
call are gone. Literal constants are made when an operand first compiles,
since a comprehension may compile before the pass that makes the rest.
`tests/spec/expressions/operator_operands_once.py` checks that operands
and special methods run once along every fall-through.

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
targeted coverage, not complete engine coverage.

On the same Linux arm64 copy, `make fuzz FUZZ_SECONDS=600` passed all four
targets: eval, compile and spyc ran for 620 seconds each, and allocation
failure ran for 602 seconds. `make fuzz-replay` then passed all four targets
under MemorySanitizer against the 4,090 retained corpus files. Both runs
used the source fingerprint recorded in the benchmark report. Full
`make sanitize` targets, ThreadSanitizer and full engine coverage have not
been completed for this checkpoint; the checks above do not establish them.

The parser-property stage passed 1,041 specification tests, all 158 TLA+
models, the C API and metering probes, and all 205 allocation-failure
programs plus intrinsic initialization on macOS arm64. All 33 standalone
build tests passed, with their oracle checks. The new function-scope test
fails on the saved pre-change engine's optimized generator classification
and passes on this engine and the pinned oracle. Its `FunctionScopes`
model checks 128 states and replays 64 transitions, including optimized
assertions, nested function bodies and yields in defaults.

The same 1,041 specification tests passed under Clang 18 AddressSanitizer
and UndefinedBehaviorSanitizer on native Linux arm64. The longer fuzz,
replay and full sanitizer runs for this second stage are not yet complete.
Its alternating compilation measurements are 0.9–2.0% lower; end-to-end
execution changes range from 0.7% faster to 1.0% slower. These small, mixed
execution differences do not establish a general runtime improvement.

The name-operand stage passed the 1,041 existing specification tests and
the added `name_operands.py` test on macOS arm64, including their pinned
oracle checks. All 1,042 tests also passed on native Linux arm64 under
AddressSanitizer and UndefinedBehaviorSanitizer. The new tests cover shared
code with different globals, invalidated name caches, closure rebinding,
collection during key and truth callbacks, and suspended-frame lifetime.
The updated `DynamicScopes` model checks 44 states and replays 22
transitions; all 158 models passed. The native C API and metering probes,
all 205 allocation-failure programs and intrinsic initialization, and all
33 standalone-build tests passed. The worker binding suite passed 127
tests, with its one Windows-only test skipped; it required running outside
the outer macOS sandbox so the worker could initialize its own sandbox.

The name-operand stage's longer fuzz and replay checks and its final
alternating performance comparison are still pending. Preliminary timings
while verification jobs were running are not used to establish a
performance difference. The source for these completed checks is `spy.c`
SHA-256 `68d514dc8cd32b1aa7a9153d79f15d1bceaa01130f2223119c3a99d0fe75febb`.

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
