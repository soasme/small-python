# Roadmap

Planned work, not implemented features. The manual describes what exists;
[docs/benchmark.md](docs/benchmark.md) records what was measured.

## Performance

spy is 1.1 to 3.1 times slower than CPython 3.15 on the core-language
benchmarks. Profiles of `fib`, `classes`, `generators` and `nbody` show the
time spread across the evaluator rather than in one operation, so the
remaining work is structural. Each step must keep `make test`, the spec
suite, the TLA+ models and the sanitizer runs green, and its commit reports
before and after timings.

### Function locals in an array

A call now builds a map value for its locals, keyed by symbol, and a local
read checks a cached entry position before falling back to a lookup. Store a
plain function's locals in an array indexed by symbol number instead, and
build a dictionary only when `locals()`, a frame object or a traceback asks
for one: optimized locals are already snapshots. Cells, `del`, generator
suspension, `exec` with explicit locals and frame introspection must keep
their current behavior.

Expected gain: 20 to 30 percent on call-heavy programs (`fib`, `classes`,
`generators`).

Measured so far: a fresh environment already places parameters first and
then the other locals in symbol order, and each name node caches its entry
position, so reads are nearly array reads. The cost is in building and
releasing the environment value per call: in `fib(32)`, call setup and
teardown take about a fifth of the time and name resolution about a sixth.
Writing entries directly instead of through `map_append` gained nothing; the
win needs the environment itself to stop being a full map value per call.

### Compiled dispatch

Ordinary code is evaluated by `eval`, a switch over node kinds called
recursively, with a stack-depth probe and step bookkeeping per node. Compile
each body once into a form that dispatches directly: first a handler chosen
per node at compile time, then possibly a register bytecode. The generator
machine already runs an instruction list that borrows tree nodes; suspended
bodies must keep heap-owned operand and cleanup stacks visible to the cycle
collector, and instructions must keep borrowing nodes from the retained
source unit.

Expected gain: two to three times on interpreter-bound programs. Largest and
riskiest change; measure it separately from the steps above.

First stage done: nodes marked `F_OPERATOR` at compile time (arithmetic, a
single comparison or an index on literal or name operands) skip dispatch
when `tick` has only the line to record, which took `fib` down 9 percent and
`nbody` 10. Extending the operands to attributes of plain instances helped
`classes` (6 percent) but slowed `nbody` and `fib` by 2 to 5 percent through
code layout, so it was left out. Any handler added to `eval` must keep its
stack frame small: `eval` sits on every level of Python recursion, and the
recursion spec test runs within 4 MiB of native stack under ASan.

### Smaller values

Every value has one size, 216 bytes, large enough for a dictionary, class or
instance. An int needs about 48. This is why `sort` and `dicts` use two to
three times CPython's memory. Allocate each value at the size its type needs;
the tuple cache, the spare-value list and every in-place retyping of a value
must follow.

### Considered and set aside

- Leaving ints, floats and strings off the context's list of all values, as
  CPython leaves them untracked: the list also backs the live-value count
  that the C API reports, object walks and shutdown, so it is not only a
  collector detail.
- Inlining the reference-count release: measured twice, no gain beyond noise.
