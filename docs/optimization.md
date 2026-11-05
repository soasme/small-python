# Optimization

This file records each change made for speed: what it does, why it keeps
the language's behavior, and what it measured. [benchmark.md](benchmark.md)
has the wall-time comparison with other engines; this file has the reasons
behind the numbers.

## How a change is measured

Two measures, both against the commit before the change:

- **Instructions.** `callgrind` counts the instructions of each program in
  `bench/programs`, scaled down about ten times so a run takes seconds:
  `fib(22)`, `loop` to 300,000, `nbody` 5,000 steps, `strings` 6,000
  lines, `dicts` 20,000 keys, `sort` 10,000 items, `classes` 30,000
  objects, `generators` 50,000 values, and `bigint` unchanged. The engine is
  built with `cc -O2 -std=c11` (GCC 14) in a Linux arm64 container, and
  CPython 3.15.2 runs the same programs there for reference. Counts are
  deterministic, so a change of 0.5% is real.
- **Time.** `bench/compare.py` with the pinned CPython 3.15 oracle as the
  reference, on the machine of [benchmark.md](benchmark.md), every few
  changes. Instructions are not time: a change that saves instructions but
  adds cache misses can lose, so a change is kept only when the time agrees.

The ratio to CPython in the tables is spy's instructions over CPython's for
the same scaled program, start-up included (CPython takes about 74 M
instructions to start and exit, spy about 1 M).

## Where the time goes

Profiles of the scaled programs share one shape. No single function
dominates; the cost is the evaluator's per-node work spread over many
small steps:

- every expression node passes through `eval`, which checks for a literal,
  a fast-path name and a fast-path operator before the general switch;
- every name is looked up through the environment chain, with a per-node
  cache of the symbol and the entry it was last found in;
- every function call builds an environment map, appends each parameter and
  local under its symbol's key, enters a frame and releases it all on
  return;
- every intermediate number is a heap value that is allocated, linked into
  the context's value list and freed again.

Each change below removes work from one of those steps.

## No machine code

spy will not compile Python to machine code. A just-in-time compiler is
how PyPy runs `loop` 15 times and `nbody` 6 times faster than CPython: it
keeps numbers in registers, removes objects that never leave a loop and
inlines calls. It also emits code for each processor, needs writable
executable memory that some hosts forbid, is far larger than the rest of
the engine, and must undo its guesses whenever Python's dynamism breaks
them. None of that fits a small, portable C11 engine.

The goal is therefore the fastest interpreter the design allows: CPython's
speed or better on every program, with PyPy's lead on loop-heavy code
accepted. Each change must keep the engine portable C and the behavior
unchanged.

## Toward bytecode

The tree walker pays at every node for work a bytecode interpreter pays
once: recording the line, testing for a pending error, guarding the C
stack, and finding operands through child nodes and remembered slots. A
call recurses in C and binds its locals in a map. The plan is to replace
that, gradually, with three changes that only pay off together:

1. **Fine-grained bytecode.** Generators already run on an instruction
   machine with heap-owned stacks, but it hands every expression and
   statement that cannot suspend back to the walker (`BC_EVAL`,
   `BC_EXEC`). Compiling operators to machine instructions as they stand
   cost generators 8% more instructions: each instruction carries about
   45 instructions of fixed work. The machine's loop is made cheaper
   first, then node kinds move to instructions one at a time, each only
   once it measures faster than the walker.
2. **Locals in slots.** A function's locals get indices at compile time
   (`scope_order` already lists them); the keyed map is built only for
   `locals()`, frame views and closures that need it.
3. **Calls without C recursion.** A Python call pushes a frame and the
   same loop continues; calls that C makes into Python (`__init__`,
   `sorted` keys, comparison callbacks) keep the C stack guard.

Measured at 0.4.0 (see *Tried and left out*), steps 2 and 3 do not pay
yet: locals are already read by index, and a function body on the
machine costs more than the walker even before its calls. Step 1, a
cheaper machine step, comes first.

Every step keeps the tests, spec, TLA models and fuzzers passing and is
measured against the commit before it; a step that makes a program slower
does not land.

## Measuring one feature

The scaled programs mix many features. To find which feature costs most
against CPython, small programs in the same container each repeat one
operation 100,000 times inside a function (an empty `for` loop over a
range, a local addition, a call, an attribute read, ...), and the
instructions of an empty loop are subtracted. The ratio to CPython per
feature points at the worst offenders: the first such table showed an
empty `for i in range(n)` loop at about 900 instructions an iteration.

## Changes

| Change | Suite instructions |
| --- | --- |
| [Releasing a number or string frees it at once](#releasing-a-number-or-string-frees-it-at-once) | -1.6% to -9.7% |
| [A name remembers what it is in its function](#a-name-remembers-what-it-is-in-its-function) | -5.2% (nbody) to +0.4% |
| [A call opens all its locals at once](#a-call-opens-all-its-locals-at-once) | -7.3% (classes), -6.5% (fib) |
| [A local is known by its key; one word says a tick has work](#a-local-is-known-by-its-key-one-word-says-a-tick-has-work) | -0.3% to -4.0% |
| [Calls test for a Python function first](#calls-test-for-a-python-function-first) | -0.1% to -0.8% |
| [A range steps in machine integers](#a-range-steps-in-machine-integers) | -8.2% (dicts) to -1.7% |
| [The context's hot fields come first](#the-contexts-hot-fields-come-first) | -0.3% to -1.5% |
| [A tick is inline; a new number is cleared in place](#a-tick-is-inline-a-new-number-is-cleared-in-place) | -2.8% to -9.2% |
| [An attribute's remembered answer is checked inline](#an-attributes-remembered-answer-is-checked-inline) | -2.0% (classes) |
| [A name keeps its local's key](#a-name-keeps-its-locals-key) | -2.3% (nbody) to 0% |
| [The stack check and the right operand are inline](#the-stack-check-and-the-right-operand-are-inline) | -1.0% to -3.6% |
| [Numbers and strings take half an allocation](#numbers-and-strings-take-half-an-allocation) | dicts -12%, sort -14% (time) |
| [A call opens its locals with its arguments](#a-call-opens-its-locals-with-its-arguments) | -3.9% (fib), -3.3% (classes) |
| [A smaller value header](#a-smaller-value-header) | dicts memory -11% |
| [A tick compares units; a push grows only when full](#a-tick-compares-units-a-push-grows-only-when-full) | -0.2% to -3.2% |
| [Class and small-map lookups skip hashing](#class-and-small-map-lookups-skip-hashing) | -2.6% (classes) |
| [A builtin method is called without a bound method](#a-builtin-method-is-called-without-a-bound-method) | -3.0% (strings) |
| [A builtin name remembers it is not a global](#a-builtin-name-remembers-it-is-not-a-global) | `len(l)`: -18% |
| [A call node is evaluated in its own function](#a-call-node-is-evaluated-in-its-own-function) | M2 time: loop -3.4%, classes -3.3% |
| [A str keeps its hash](#a-str-keeps-its-hash) | -2.8% (strings), `d["a"]`: -10% |
| [A name store skips the step bookkeeping](#a-name-store-skips-the-step-bookkeeping) | -1.1% to -4.3%; M2 time: nbody -4.0% |
| [Numbers have their own allocation path](#numbers-have-their-own-allocation-path) | -2.4% (fib) to +0.5% |
| [A call releases its own environment](#a-call-releases-its-own-environment) | -3.8% (fib), -1.8% (classes); M2: fib -4.5% |
| [A remembered name is read inline](#a-remembered-name-is-read-inline) | -0.6% to -4.8% |
| [Each call depth keeps an environment](#each-call-depth-keeps-an-environment) | -4.7% (fib), -0.6% (sort) |
| [A jump in a generator ticks only when there is work](#a-jump-in-a-generator-ticks-only-when-there-is-work) | -3.7% (generators); inline push -2.5% |
| [A float result takes a dying operand's place](#a-float-result-takes-a-dying-operands-place) | -10.1% (nbody), others +0.1% to +0.3% |
| [An operator reads list items in place](#an-operator-reads-list-items-in-place) | -6.4% (nbody), others 0% to +0.3% |
| [A built string keeps its storage](#a-built-string-keeps-its-storage) | -3.6% (dicts), -1.4% (strings); `s + s`: -27% |
| [`str` of an int writes its digits](#str-of-an-int-writes-its-digits) | -8.9% (dicts), -2.2% (strings) |
| [Short text lives in its value](#short-text-lives-in-its-value) | -4.6% (bigint), -3.0% (strings), -2.0% (dicts) |
| [A call without locals keeps its environment](#a-call-without-locals-keeps-its-environment) | `f()`: -12%; fib +0.3% |
| [Values live in pools](#values-live-in-pools) | -15.7% (sort), -13.0% (dicts), -5.1% (bigint), -1.7% (fib) |
| [A loop steps its iterator directly](#a-loop-steps-its-iterator-directly) | -0.9% (dicts), -0.6% (nbody), the rest -0.5% to 0% |
| [Numbers stay off the value list](#numbers-stay-off-the-value-list) | -1.5% (dicts), -1.2% (nbody), -1.0% (loop, sort) |
| [A release inlines its common case](#a-release-inlines-its-common-case) | -10.1% (loop), -7.5% (nbody), -6.8% (classes), -6.3% (generators), -5.5% (fib); M2: loop -17%, nbody -13.5% |
| [Arithmetic on numbers skips the dispatch](#arithmetic-on-numbers-skips-the-dispatch) | -11.7% (loop), -7.8% (fib), -6.2% (generators), -5.9% (nbody), -4.6% (classes) |
| [A test of two numbers makes no bool](#a-test-of-two-numbers-makes-no-bool) | -10.3% (fib), -8.6% (loop); M2: loop -15%, fib -8.8% |
| [Hot sites make numbers inline](#hot-sites-make-numbers-inline) | -2.5% (nbody), -1.8% (loop), -1.3% (fib) |
| [Any single comparison is tested without a bool](#any-single-comparison-is-tested-without-a-bool) | -12.2% (loop); fib +0.6% |
| [A store takes its target's operands at hand](#a-store-takes-its-targets-operands-at-hand) | -3.2% (nbody), -0.8% (strings), -0.6% (classes) |
| [A call knows its arguments are plain](#a-call-knows-its-arguments-are-plain) | -1.1% (strings), -0.7% (classes), -0.5% (fib) |
| [A kept environment serves any function of its depth](#a-kept-environment-serves-any-function-of-its-depth) | -2.4% (classes) |
| [An attribute takes its name at hand](#an-attribute-takes-its-name-at-hand) | -2.0% (classes) |
| [A quiet tick is one comparison](#a-quiet-tick-is-one-comparison) | -1.5% (generators), -1.4% (loop), -1.0% (nbody) |
| [Machine ints divide on the fast path](#machine-ints-divide-on-the-fast-path) | -10.7% (loop), -5.0% (sort), -4.9% (generators) |
| [Any comparison of two numbers skips the dispatch](#any-comparison-of-two-numbers-skips-the-dispatch) | -0.9% (generators) |
| [A dict read goes straight to its entries](#a-dict-read-goes-straight-to-its-entries) | -1.2% (strings), -0.7% (dicts) |
| [The machine loads leaves itself](#the-machine-loads-leaves-itself) | -2.2% (generators) |
| [Comparisons become machine steps](#comparisons-become-machine-steps) | -0.1% (generators) |
| [A function reads its module's globals directly](#a-function-reads-its-modules-globals-directly) | -4.3% (fib), -0.8% (strings) |
| [The machine operates on leaves in one step](#the-machine-operates-on-leaves-in-one-step) | -4.7% (generators) |
| [A Python call skips the general dispatch](#a-python-call-skips-the-general-dispatch) | -2.1% (fib) |
| [A scope keeps its own environments](#a-scope-keeps-its-own-environments) | -3.1% (classes), -1.9% (fib); M2: classes -5.8% |
| [An environment remembers it holds its scope's keys](#an-environment-remembers-it-holds-its-scopes-keys) | -1.4% (classes), -1.2% (fib) |
| [A method object calls its function directly](#a-method-object-calls-its-function-directly) | -0.7% (classes) |
| [Built text starts at 32 bytes; short text lives in its value](#built-text-starts-at-32-bytes-short-text-lives-in-its-value) | -5.5% (dicts), -4.5% (strings); M2: -5% each |
| [A called name is taken at hand](#a-called-name-is-taken-at-hand) | -1.9% (fib), -0.4% (dicts), -0.3% (classes) |
| [A class call tests the builtin types once](#a-class-call-tests-the-builtin-types-once) | -0.6% (dicts), -0.5% (classes), -0.4% (bigint) |
| [A machine test's bool is its truth](#a-machine-tests-bool-is-its-truth) | -1.2% (generators) |
| [A call operand skips a second eval](#a-call-operand-skips-a-second-eval) | -5.7% (fib), -1.1% (dicts), -0.8% (strings); nbody +0.1%; M2: fib -5.6%, dicts -4.2% |
| [An attribute operand skips a second eval](#an-attribute-operand-skips-a-second-eval) | -7.8% (classes); M2: classes -11.2% |
| [An append that fits does not call grow](#an-append-that-fits-does-not-call-grow) | -1.0% (strings), -0.3% (bigint) |
| [A machine test is one step](#a-machine-test-is-one-step) | -3.0% (generators); M2: generators -5.5% |
| [A machine assignment skips the statement dispatch](#a-machine-assignment-skips-the-statement-dispatch) | -1.8% (generators); M2: generators -13%, nbody -2.7% |
| [Hot functions start on a cache line](#hot-functions-start-on-a-cache-line) | none; steadies wall-time comparisons |
| [A leaf yield is one step](#a-leaf-yield-is-one-step) | -3.4% (generators); M2: generators -4.9% |
| [A yield statement drops what is sent](#a-yield-statement-drops-what-is-sent) | -4.1% (generators); M2: generators -4.2% |
| [Keys of one kind sort without dispatch](#keys-of-one-kind-sort-without-dispatch) | -23.8% (sort); M2: sort -11.6% |
| [A profile-guided build](#a-profile-guided-build) | M2 time: generators -21%, fib -16%, strings -14%, classes -12%; loop +2% |
| [An unpacking reads a tuple or list in place](#an-unpacking-reads-a-tuple-or-list-in-place) | `a, b = t`: -76%, `a, b = b, a`: -73%; programs within 1% |
| [A method without arguments names itself only for an error](#a-method-without-arguments-names-itself-only-for-an-error) | `s.upper()`: -60%; M2: strings -3.7% |
| [`in` searches a list or tuple in place](#in-searches-a-list-or-tuple-in-place) | `3 in l`: -46%; programs within 0.4% |
| [A builtin class call names itself only for an error](#a-builtin-class-call-names-itself-only-for-an-error) | -5.4% (dicts), -4.0% (bigint); `str(i)`: -15%; M2: dicts -3.2% |
| [A free variable is remembered in its enclosing environment](#a-free-variable-is-remembered-in-its-enclosing-environment) | closure call: -16%; programs within 0.5% |
| [A list, tuple or range iterates without a protocol search](#a-list-tuple-or-range-iterates-without-a-protocol-search) | `[k for k in range(3)]`: -4%; M2: nbody -1.5%, strings -1.1% |
| [A comprehension reuses its environment](#a-comprehension-reuses-its-environment) | `[k for k in range(3)]`: -5.5%; M2: strings -0.7% |
| [A growing buffer moves through the spare blocks](#a-growing-buffer-moves-through-the-spare-blocks) | M2: strings -6.8%, peak memory 11.7 → 3.1 MiB |
| [A machine step keeps its place in a local](#a-machine-step-keeps-its-place-in-a-local) | -1.2% (generators); M2: generators -2.7% |
| [A machine jump reads a bool's truth](#a-machine-jump-reads-a-bools-truth) | -1.5% (generators); M2: generators -3.4% |
| [A negated number is a constant](#a-negated-number-is-a-constant) | `while` testing `i == -1`: -22%; M2: -27%; programs within 0.6% |
| [A float power from a positive base skips the dispatch](#a-float-power-from-a-positive-base-skips-the-dispatch) | -3.4% (nbody); M2: nbody -3.1% |
| [A dying number returns to its spare list directly](#a-dying-number-returns-to-its-spare-list-directly) | -5.6% (loop, nbody), -3.2% (generators), -2.4% (classes); M2: nbody -6.5%, loop -3.0%, classes -2.6% |
| [Two strs concatenate before the operator dispatch](#two-strs-concatenate-before-the-operator-dispatch) | -2.9% (dicts); M2: dicts -1.6% |
| [A Python call enters and leaves its frame inline](#a-python-call-enters-and-leaves-its-frame-inline) | -5.4% (fib), -4.2% (generators), -2.6% (classes); M2: fib -9.2%, generators -5.0%, classes -3.8% |
| [Each hot machine step dispatches the next](#each-hot-machine-step-dispatches-the-next) | -3.4% (generators); M2: generators -10.9%, strings -2.5% |
| [A call statement skips eval's other cases](#a-call-statement-skips-evals-other-cases) | -2.1% (classes), -1.6% (loop), -1.4% (fib, generators); M2: classes -2.9%, loop -2.1% |
| [Hot paths stay out of large functions](#hot-paths-stay-out-of-large-functions) | -3.1% (fib), -2.2% (dicts), -1.8% (nbody); empty range loop -17%; M2: fib -3.3%, loop -2.3% |
| [An attribute is an operand at hand](#an-attribute-is-an-operand-at-hand) | -5.3% (classes); M2: classes -2.1% |

### Releasing a number or string frees it at once

`spy_release` queued a value whose count reached zero on a pending list,
asked whether it needs a finalizer, visited its edges and only then freed
it. That loop exists for containers, whose release frees what they hold
without recursing. Ints, floats and strs hold no edges and never take a
finalizer, and they are most of what dies: every intermediate result of
arithmetic is one. They are now freed directly when their count reaches
zero; everything else takes the loop as before. What is freed, and when,
is unchanged.

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| fib | 127.0 M | 124.9 M | -1.6% |
| loop | 747.1 M | 683.5 M | -8.5% |
| nbody | 1,027.6 M | 928.3 M | -9.7% |
| classes | 421.7 M | 404.6 M | -4.1% |
| generators | 466.6 M | 444.5 M | -4.7% |
| strings | 319.2 M | 306.6 M | -4.0% |
| dicts | 212.3 M | 203.4 M | -4.2% |
| sort | 151.8 M | 148.0 M | -2.5% |
| bigint | 31.7 M | 30.9 M | -2.6% |

### A name remembers what it is in its function

A name node already remembered its symbol in the scope it last ran in and
the entry it was last found at. Each read still walked the full decision:
is the environment a plain function environment, is the remembered scope
its scope, is the symbol global, nonlocal, local or free, and only then
the entry. The node now also remembers the outcome, *here* (a local of
that scope) or *further out* (free or global), when it remembers the
symbol. A read in an environment of the remembered scope tests that the
environment keeps its locals in its own entries and that the entry at the
remembered position still has the symbol's key, and returns its value; a
name found further out starts at the parent environment. Every other
case, and every miss, takes the full lookup as before, so no lookup can
answer differently.

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| fib | 124.9 M | 120.8 M | -3.3% |
| nbody | 928.3 M | 879.9 M | -5.2% |
| classes | 404.6 M | 396.7 M | -2.0% |
| generators | 444.5 M | 433.0 M | -2.6% |
| loop | 683.5 M | 686.1 M | +0.4% |

`loop` runs at module level, where names are found in the globals
dictionary and the new test only adds a comparison.

### A call opens all its locals at once

A call made its environment one entry at a time: each parameter went
through the general map append (find spare storage, grow, retain the key
and value, keep the index), and then each other local was appended the
same way, unbound. A function's locals are the same names on every call,
so the scope now computes their order once, on its first call, and each
new environment takes storage for all of them and fills it in one loop:
the symbol's key and hash, and the unbound marker. A call that passes
exactly the positional parameters then stores each argument in its
entry, which is the parameter's position.

The order is CPython's `co_varnames` order: positional and keyword-only
parameters, `*args`, `**kwargs`, then the other locals in order of first
appearance. Before, a call that bound parameters by keyword left them in
the environment in binding order, so `locals()` listed them in the order
the call happened to give them; it now lists them as CPython does. A
`code.replace()` copy that renames parameters still binds under its new
names first and declares the body's locals after them, as before.

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| fib | 120.8 M | 113.0 M | -6.5% |
| classes | 396.7 M | 367.8 M | -7.3% |
| sort | 147.2 M | 145.8 M | -0.9% |
| strings | 304.9 M | 303.8 M | -0.3% |

### A local is known by its key; one word says a tick has work

Two smaller cuts of per-node work.

A name read in its function's environment tested that the environment
was a plain function environment of the remembered scope before it
compared the remembered entry's key. Only an environment of that scope
holds the symbol's own key object in its entries (other environments
make their keys from text, or keep their bindings in a separate
mapping), so the key comparison alone now decides, after a check that
the environment is one at all.

`tick`, which runs for every statement and every node evaluated off the
fast paths, asked five questions before recording the line: an error
pending, weak-reference callbacks queued, finalizers queued, a step
limit set, a new source file. The three rare ones are now one word,
`attention`, which the code that queues callbacks, runs them or sets the
step limit keeps current (CPython's eval breaker plays the same part).

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| nbody | 879.9 M | 845.1 M | -4.0% |
| generators | 433.0 M | 420.2 M | -3.0% |
| loop | 686.1 M | 678.0 M | -1.2% |
| classes | 367.8 M | 364.4 M | -0.9% |
| fib | 113.0 M | 112.1 M | -0.7% |

### Calls test for a Python function first

`call_keywords` tested a callee against eight other kinds (native
functions, bound methods, static methods, classes, instances, ...)
before reaching a Python function, the commonest callee. The function
case now comes first, and its body is its own function,
`call_function`. A small int's release no longer calls `free` with a
null pointer.

### A range steps in machine integers

A `range` iterator compared its counter with the stop and added the step
with the arbitrary-precision routines, which build a temporary digit
array on the heap for every step, then free it and look for a small
int. When the counter, the stop and the step are all machine integers
and the next counter fits in one, the iterator now compares and adds
them directly. Ranges past 64 bits take the old path, and so does the
last step before an overflow.

An empty `for i in range(n)` iteration took 902 instructions and now
takes 521.

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| dicts | 202.3 M | 185.8 M | -8.2% |
| strings | 301.6 M | 287.6 M | -4.6% |
| nbody | 845.2 M | 813.1 M | -3.8% |
| classes | 361.3 M | 349.8 M | -3.2% |
| sort | 144.4 M | 140.6 M | -2.6% |
| bigint | 30.8 M | 30.3 M | -1.7% |

Wall time, median of seven runs: dicts 145.3 to 133.0 ms (-8.5%),
classes 194.0 to 179.0 ms (-7.7%), strings 188.7 to 175.8 ms (-6.9%),
nbody 469.0 to 447.8 ms (-4.5%), sort 191.4 to 186.7 ms (-2.5%).

### The context's hot fields come first

`SPYContext` began with a 14 KB table of class lookups, so the fields read
on every step (the pending error's name, the frame stack, the settings)
sat 15 to 19 KB in. An arm64 load reaches a byte at most 4 KB from its
base register and a 4-byte word 16 KB away, so each test of
`c->error_type[0]`, the commonest test in the engine, took an extra
address computation. The lookup tables and the long message buffers now
end the structure, and the error name begins it. The instructions fall by
0.3% to 1.5%; on the M2 the wall time does not move, since the extra
additions were cheap there, but they are gone everywhere.

### A tick is inline; a new number is cleared in place

`tick` runs for every statement, every loop pass and every node off the
fast paths, and was a call: its quiet case, three tests and two stores of
the line, now compiles into each caller, while the rare full path
(`tick_full`) stays a call. `relocate`, the two stores of the line, is
inline too. `value_alloc` cleared a reused value with `memset` of a size
chosen at run time, a library call; it now picks between two constant
sizes, which the compiler clears with a few stores.

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| generators | 412.3 M | 378.3 M | -8.2% |
| loop | 664.3 M | 617.4 M | -7.1% |
| classes | 346.2 M | 323.7 M | -6.5% |
| nbody | 805.9 M | 766.8 M | -4.9% |
| fib | 110.0 M | 104.5 M | -5.0% |
| strings | 285.7 M | 273.3 M | -4.4% |
| dicts | 184.5 M | 179.0 M | -3.0% |
| sort | 139.6 M | 135.4 M | -3.0% |

The M2 gains less in time (loop -3.2%, fib -2.5%, generators -1.4%,
the rest within noise): it runs this interpreter at about six
instructions a cycle, so its time follows chains of dependent loads more
than the count of instructions. The executable's text did not grow.

### An attribute's remembered answer is checked inline

An attribute node remembers how its last instance's class answers it and
under which class epoch. The check that the answer still holds was a
call, which also recomputed the answer when it did not; the check is now
inline and the recomputation a separate call. An assignment to an
existing attribute no longer hashes the name before it looks at the
remembered entry. A plain read `y = o.x` fell from 400 to 359
instructions, a store `o.x = i` from 353 to 319, and classes by 2.0%.

### A name keeps its local's key

The test that a remembered local is still at its position compared the
entry's key with the symbol's key, which it reached from the node through
the scope and its symbol table: three dependent loads before the
comparison. The node now keeps the key itself, borrowed from the scope
like the scope itself, set when the full lookup finds the local and
cleared when the node remembers another symbol. Wall time: nbody -2.1%,
generators -2.0%, fib -1.6%.

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| nbody | 748.2 M | 731.0 M | -2.3% |
| generators | 367.5 M | 362.6 M | -1.3% |
| fib | 103.1 M | 102.3 M | -0.7% |
| classes | 312.7 M | 310.6 M | -0.7% |

### The stack check and the right operand are inline

Two calls on every operator node became inline code. The fast operator
path asked `operator_right` for its right operand, a call that repeats
the tests the compiler made when it marked the node; a marked node's
right operand is its comparison's or its own second child. `deeper`,
the native-stack check run by every evaluation off the fast paths, is
inline, with the error report a separate call.

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| fib | 102.3 M | 98.4 M | -3.9% |
| nbody | 731.0 M | 705.7 M | -3.5% |
| classes | 310.6 M | 303.0 M | -2.5% |
| generators | 362.6 M | 354.3 M | -2.3% |
| loop | 605.6 M | 589.3 M | -2.7% |
| dicts | 177.6 M | 174.6 M | -1.7% |

On the M2 the wall time stays within noise (fib -0.3%, classes -0.7%,
loop +1.3%), and the executable's text is the same size.

### Numbers and strings take half an allocation

Every value took the size of the largest member of its union, 216 bytes
on a 64-bit host, though an int uses 16 of them and a str 48. A dict of
a million int keys and values held two million such allocations. Ints,
floats, complex numbers, strs, bytes and bytearrays now take an
allocation that ends with the string member, 112 bytes; every other
value keeps the full size. A value never changes into a type of the
other size (str and bytes, set and frozenset, module and instance change
within one), and the two places that exchanged the whole union of two
values of one type now exchange only what their type holds. Released
allocations are kept in two spare lists, one per size.

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| dicts, time | 130.2 ms | 114.1 ms | -12.4% |
| sort, time | 184.3 ms | 158.6 ms | -13.9% |
| dicts, peak memory | 97.6 MiB | 53.8 MiB | -45% |
| sort, peak memory | 108.1 MiB | 86.4 MiB | -20% |
| fib, time | 66.7 ms | 65.5 ms | -1.9% |
| classes, time | 171.2 ms | 174.1 ms | +1.7% |
| nbody, time | 423.0 ms | 427.5 ms | +1.1% |

The instructions move by -3.7% (dicts) to +2.7% (nbody), the cost of
choosing a spare list on every allocation and release.

### A call opens its locals with its arguments

A call that passes exactly a function's parameters by position opened
its locals unbound and then replaced the first ones with the arguments,
counting the positional parameters again on every call. The scope now
counts them once, with the locals' order, and such a call fills the
parameters' entries with the arguments as it opens the environment.
Wall time: classes -4.0%, fib -2.6%.

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| fib | 100.5 M | 96.6 M | -3.9% |
| classes | 303.4 M | 293.4 M | -3.3% |

### A smaller value header

Every value began with 64 bytes of bookkeeping. The reference count and
the collector's trial count are now 32-bit (four billion references to
one value would need 32 GB of pointers), and the type tag is a byte
beside the other flags, so the header takes 48 bytes: a number or string
96, any other value 200. Two small cuts went with it: a dying value whose
type can never need a finalizer skips the finalizer probe, and a frame
that returns without an error skips the traceback call.

Peak memory of `dicts` fell from 53.8 to 47.7 MiB and `sort` from 86.4
to 83.4 MiB; wall time moved between -2.4% (fib) and +1.5% (loop),
instructions between -1.2% and +0.2%.

### A tick compares units; a push grows only when full

`tick` copies the running unit's file name into the context when the
running unit changes, and its quiet test compared the name it last
copied with the frame's unit's name, a load through the unit. It now
remembers and compares the unit itself. A generator's machine called
`grow` on every push of its operand stack; the push now calls it only
when the stack is full.

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| generators | 348.5 M | 337.4 M | -3.2% |
| loop | 580.4 M | 577.7 M | -0.5% |
| nbody | 719.1 M | 716.1 M | -0.4% |

Wall time: generators -1.4%, nbody -0.7%.

### Class and small-map lookups skip hashing

`class_lookup` keeps recent answers in a table, but found an answer's
entry by hashing the name's text on every call. Nearly every name it is
given is a literal, so the entry is now chosen by the name's address and
the class's, and the entry's own copy of the name decides whether it is
a hit: a different name at a reused address compares unequal. Releasing
an instance, which asks its class for `__del__`, no longer hashes
`"__del__"` each time.

`env_find`, the search of an environment's or instance's own entries by
name, scans a map too small for an index directly, comparing stored
hashes, instead of through the general search cursor; and the name
node's cached length and hash are read inline. A method call on an
instance runs this search to rule out an instance attribute of the same
name.

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| classes | 290.9 M | 283.3 M | -2.6% |
| bigint | 28.8 M | 28.7 M | -0.5% |

### A builtin method is called without a bound method

`l.append(x)` evaluated `l.append` to a new bound method, called it, and
freed it: an allocation, a release through the collector's edge walk, and
the bound method's dispatch, for every call. A call node already
remembered, per type, that its attribute is a native method of a builtin
value. The bound method's call is now a function of the receiver, the
method and its name (`call_method`), which the call node invokes directly,
as CPython's method-call instructions skip the bound method. Calling a
bound method object goes through the same function, so both behave alike,
keyword arguments and error messages included.

An `l.append(i)` loop fell from 1,334 to 928 instructions an iteration.

| Program | Before | After | |
| --- | ---: | ---: | ---: |
| strings | 264.0 M | 256.2 M | -3.0% |
| sort | 128.4 M | 126.3 M | -1.7% |
| dicts | 166.8 M | 164.6 M | -1.3% |

Wall time: strings -4.0%, the others within noise.

### A builtin name remembers it is not a global

Reading `len` inside a function searched the module's globals, missed,
and found it in the builtins. The miss cost a search of the globals' hash
index on every read, about 125 instructions. The context now counts the
keys dictionaries gain (an insertion, or an instance's attributes becoming
a dictionary), and a name node remembers the dictionary it was missing
from and the count at that time: while the count holds, no dictionary has
gained a key, so the name is still missing and the read passes to the
builtins directly. A dictionary that gains any key moves the count, so
the remembered miss can never outlive a binding of the name; a new
dictionary at a freed one's address gains its keys the same way.

A `len(l)` call in a function fell from 690 to 564 instructions. The
suite, whose loops call few builtins, moved by -0.7% to +0.8%.

### A call node is evaluated in its own function

`eval` contains the whole expression switch, `eval_inner`, inlined. The
call case keeps up to nine arguments in an array on the C stack, so with
Apple Clang every evaluation of every node reserved that space, saved
twelve registers and checked the stack protector's guard on return. The
call case is now its own function, `eval_call`, and `eval` saves ten
registers and has no guard. GCC on Linux already compiled `eval`
without the cost, so the instruction counts there do not move; on the
M2: loop -3.4%, classes -3.3%, nbody -2.0%, strings -1.9%, generators
and fib within noise.

The same rule moved the cold branches that declare arrays or take a
local's address out of `call_keywords`, `get_index`, `set_index`,
`leave_frame` and `inplace` (`call_with_self`, `call_pair`,
`frame_link_back`, `list_repeat`, `augmented_error`); `type_call` now
initializes a plain instance through `call_with_self` too. The wall time
stayed within noise (-1.6% to +1.7% while the fuzzers ran), and the
duplicate argument-shifting code is gone.

### A str keeps its hash

A dictionary lookup hashed its key every time, walking every byte of a
str, and compared the stored key through the general equality, which
first asks whether either side has an `__eq__` to call. A str or bytes
now keeps its hash once computed, as CPython's do, in the word a
bytearray uses to count its exports; the one place that grows a str in
place clears it. Two exact str values compare their bytes directly:
neither can run Python code. A loop of `x = d["a"]` takes 10% fewer
instructions; `strings` 2.8% and `dicts` 0.9% fewer, the rest within
0.2%.

### A name store skips the step bookkeeping

Every assignment target recorded its line and checked for pending work,
as a statement does, before the general target code; a loop that binds
its variable and one local paid that twice an iteration. A name whose
slot is remembered, a local in its function's environment or a global
in its dictionary, cannot fail to store, so `store_target` is now an
inline test for that case, as `eval`'s names are, and everything else
goes to `store_slow`, which records the line first. A trace function
still sees every target. A machine-integer `range` likewise steps at
the top of `iterator_next`, before the generic iterator tests and the
recursion check. Instructions: loop -4.3%, generators -3.3%, nbody
-2.9%, the rest -1.1% to -1.8%, fib unchanged; on the M2 nbody -4.0%,
loop -2.5%, generators -2.2%, sort and fib within noise.

### Numbers have their own allocation path

A reused value was cleared with `memset` of a size chosen at run time,
so a function's environment, 200 bytes, paid a call into the C library
on every call. Clearing each size separately lets the compiler store
the zeros in place, but made `value_alloc` too large for the compiler to
inline into `spy_int` and `spy_float`, and every float operation then
paid a call: nbody took 4.4% more instructions. Ints and floats now take
a spare value through their own small inline `number_new`, which clears
only the header and the first union member, and `value_alloc` clears
every other value at its constant size. The check that each argument
belongs to the calling context moved from every call to the public
`spy_call` and `spy_call_keywords`: the engine's own values never
cross contexts. Instructions: fib -2.4%, classes -1.1%, loop and nbody
-0.4%, dicts and bigint +0.4% to +0.5%; the M2's times stayed within
noise but for loop (-2.1%) and classes (-1.6%).

### A call releases its own environment

A function's environment died through `spy_release`, which walks any
value's edges through a callback and a pending list so that long chains
of garbage free without recursion: for a function environment, eight
fixed fields, each entry's key and value, a finalizer check and the
general `free_value`. When the call that made the environment is its
only holder, as it is unless a closure, frame or generator kept it, the
call now releases the locals itself, from the last as CPython clears a
frame, then the parent and the unit. Anything else falls back to
`spy_release`. Instructions: fib -3.8%, classes -1.8%, sort -0.5%, the
rest unchanged; on the M2 fib -4.5%, classes -3.6%.

### A remembered name is read inline

`name_fast` held the remembered-local test and the walk out through
enclosing environments and dictionaries, so even a local read paid the
walk's register saves. The test for the entry a name was last found at,
a local in its function's environment or, in module code, a global in
the module's dictionary, is now inline wherever a name is read, and the
walk is `name_outer`. Testing only locals inline had sped nbody up 3.7%
but slowed loop 0.6%, whose module-level names then always took the
call. Instructions: loop -4.8%, classes and generators -2.7%, nbody
-3.0%, dicts -2.1%, the rest -0.6% to -1.2%; on the M2 loop and classes
-3.6%, nbody -1.5%, fib and sort within noise.

### Each call depth keeps an environment

A call allocated its environment, cleared it, took entry storage, and
retained each local's symbol key; returning undid all of it. CPython
instead runs frames on a stack it reuses. Each depth of spy's frame stack
now keeps the environment its last call returned, when nothing else held
it, unlinked from the context's values with its storage and keys; the
next call of the same scope at that depth takes it back and fills in the
arguments. A recursive function's sibling calls, and any loop calling one
function, reuse one environment per depth. A kept environment borrows
its unit, whose release drops it, so that a dead scope's address taken
by a new scope is never mistaken for it, its keys checked as well; the
context's release frees kept environments before its values. One slot
for the whole context, instead of one per depth, reused only every
other call of a recursion and replacing the kept environment on each
return cost more than it saved (fib +10%). Instructions: fib -4.7%,
sort -0.6%, generators +0.3%, the rest within 0.1%.

### A jump in a generator ticks only when there is work

A suspendable body's instructions without a node of their own, its
jumps and stack operations, ticked on the function's definition and then
put back the line the definition's tick had overwritten. When tick has
only the line to record, such an instruction now does nothing; otherwise
it still ticks and restores the line, so pending work and trace
functions see every jump as before. Instructions: generators -3.7%,
strings -0.6%, sort -0.4%, the rest unchanged.

Pushing onto a machine's operand stack is likewise inline now, with the
stack's growth in `machine_grow`: generators -2.5%, strings -0.4%.

### A float result takes a dying operand's place

In `dx * dx + dy * dy`, the products are new floats that the addition
reads once and releases: the sum allocated a third float while two died.
When an arithmetic node or an augmented assignment owns two float
operands and nothing else holds one of them, the result of `+`, `-`,
`*` or `/` (by a nonzero divisor) is written into that operand, as
CPython's float operations reuse a dying operand. A value that only the
evaluation holds cannot be seen by anyone else, so the reuse is
invisible. Other callers of `binary` and `inplace` pass borrowed
operands and keep allocating. Instructions: nbody -10.1%, the others
+0.1% to +0.3% for the type test.

With the local read inline, GCC split `operand`, the fast path's
reading of a literal or name, into an out-of-line part; it is now always
inline: -0.1% to -1.1%.

### An operator reads list items in place

An operator whose operands are literals or names takes them borrowed,
without evaluating them through `eval`. In `b[0] - c[0]` the operands are
indexes, so the subtraction went the general way: two nested `eval`s,
each retaining an item and releasing it. Finding an item of a list or
tuple at an int runs no code, so it is an operand on the fast path too:
an index whose own operands are literals or names, read in
`item_operand`, out of line so that the common operands stay as cheap
as before (inline, it cost the other programs up to 0.6%). Instructions:
nbody -6.4%, the others 0% to +0.3%.

### A built string keeps its storage

`str.join`, f-strings and `replace` build their text in a growing buffer
and then made the str by copying it: one more allocation, copy and free
per result. `buffer_text` now gives the buffer's storage to the new str
or bytes, shrinking it only when more than 64 bytes would go unused.
Concatenating two strs grew such a buffer through several reallocations
for a length known from the start; `text_concat` allocates exactly once,
as CPython does. Instructions: dicts -3.6%, strings -1.4%, the rest
unchanged; a loop of `x = s + s` -27%.

### `str` of an int writes its digits

`str(i)` formatted a machine integer with `snprintf` into a scratch
array, appended that to a buffer, then copied the buffer into a new str.
`format_small` now writes the digits from the last into the buffer
directly, and `stringify`, which serves `str`, `repr` and `format`,
hands its buffer to the str through `buffer_text`. Instructions: dicts
-8.9%, strings -2.2%, the rest unchanged.

### Short text lives in its value

Every str and bytes took two allocations: the value and its text. Most
strs a program makes are short (a key, a digit string, a word), so
str and bytes values now have a size of their own, 16 bytes longer than
a number's, and keep text shorter than that in the same allocation, as
CPython's compact strings do. `text_new` makes every str, bytes and
bytearray of a known length; a bytearray, which resizes in place, keeps
its text apart. The one in-place growth of a str, `s += t` on an
unshared `s`, moves short text out before it reallocates. Instructions:
bigint -4.6%, strings -3.0%, dicts -2.0%, fib -0.8%, loop +0.3%, the
rest within 0.4%.

### A call without locals keeps its environment

An environment was kept at its call's depth only when it had a local,
since the kept one's first key tells its scope's address from a later
scope's. One without locals holds nothing of its scope, so it is kept
too, and a call to a function with neither parameters nor locals no
longer allocates and frees a whole value. Instructions: a loop of
`f()` -12% per call; fib +0.3%, the rest unchanged.

### Values live in pools

A released value waited in a spare list of 64 per size; past that, and
for every value a growing program keeps, the system allocator served
it, about 350 instructions per `l.append(i)` of a new int. Values are
now carved from 16 KiB pools, each of one size class and aligned to its
size so that a value's address names its pool, as CPython's pymalloc
does. A pool keeps its released values in its own free list and goes
back to the system once all are released, unless it is the last of its
size with room. The 64 spares stay in front of the pools, as an
allocator's thread cache: the steady churn of temporary numbers never
reaches a pool. The size class comes from a table instead of a branch
and a mask. Instructions: sort -15.7%, dicts -13.0%, bigint -5.1%, fib
-1.7%, classes -1.1%, generators and loop -0.6%, nbody -0.4%, strings
+0.4%; peak memory of the sort program 83.4 to 80.5 MiB, the others
unchanged. Unlike the unbounded spare list left out below, the pools
keep a released value near its neighbours. On the M2 sort took 167.9
→ 150.3 ms (-10.5%), strings 152.5 → 149.7 ms (-1.9%), dicts 99.8 →
100.4 ms (+0.6%).

### A loop steps its iterator directly

A `for` loop took each item through `iter_at`, which dispatches on the
iterable's type to read a list in place or step an iterator. A loop's
iterable keeps its type, so a loop over an iterator or a generator now
calls `iterator_next` itself, and `iterator_next` tries a range, the
most common iterator a loop steps, before the list iterator. The
iterator itself still holds the position, since Python code may hold it
and step it too. Instructions: dicts -0.9%, nbody -0.6%, the rest 0% to
-0.5%.

### Numbers stay off the value list

Every value was linked into its context's list of values, which the
cycle collector walks and context destruction frees, and unlinked when
released: four pointer writes for each temporary number. A small int or
a float reaches no other value and owns no storage, so, as CPython's
collector does not track them, they now stay off the list. They still
count as live values. A collection never marks them, and garbage it
frees releases the ones it holds. Context destruction, which can no
longer find them, frees every pool whole, so the pools are listed too.
Instructions: dicts -1.5%, nbody -1.2%, loop and sort -1.0%, classes
and generators -0.6%, fib +0.1%; a collection walks only the values
that can form cycles.

### A release inlines its common case

`spy_release`, called at more than a thousand places, held both the
decrement and the work of freeing a value and its edges, so the compiler
never inlined it: every release of a value that stayed alive paid a
call. It is now the decrement and a test, which the compiler inlines
within `spy.c`, as CPython's `Py_DECREF` is a macro; `release_dead`,
out of line, frees. The text section grows by 30.8 KB (4%).

| Program | Instructions | M2 time |
| --- | ---: | ---: |
| loop | -10.1% | 440.6 → 365.6 ms (-17.0%) |
| nbody | -7.5% | 438.4 → 379.4 ms (-13.5%) |
| classes | -6.8% | 201.5 → 182.8 ms (-9.3%) |
| generators | -6.3% | 241.3 → 215.2 ms (-10.8%) |
| fib | -5.5% | 73.1 → 69.1 ms (-5.6%) |
| strings | -4.3% | |
| dicts | -4.6% | |
| sort | -2.8% | |
| bigint | -1.7% | |

### Arithmetic on numbers skips the dispatch

An operator whose operands were found on the fast path checked that they
were two machine ints or two floats and then called `binary`, which
checked their types again on its way to `integer_binary` and `spy_int`;
`x += 1` went through `inplace` and `binary` too. `number_fast`, inline,
now computes `+`, `-` and `*` on two machine ints, with the overflow
checks `integer_binary` uses, and `+`, `-`, `*` and `/` by a nonzero
divisor on two floats. It serves the operator fast path, the general
binary operator and augmented assignment alike. Where the caller owns
the operands, a float result still takes the place of a dying one; the
fast path, which borrows its operands, always makes a new float.

| Program | Instructions | M2 time |
| --- | ---: | ---: |
| loop | -11.7% | 366.4 → 332.1 ms (-9.4%) |
| fib | -7.8% | 68.7 → 69.0 ms (+0.4%) |
| generators | -6.2% | 216.3 → 205.9 ms (-4.8%) |
| nbody | -5.9% | 382.0 → 355.8 ms (-6.8%) |
| classes | -4.6% | 183.5 → 175.0 ms (-4.6%) |
| strings, dicts, sort, bigint | -1.0% to -1.9% | |

### A test of two numbers makes no bool

`if n < 2` evaluated the comparison to a bool, retained it, asked
`spy_truth` for its truth and released it. `condition`, which serves
`if`, `while`, `elif`, `assert` and pattern guards, now answers a single
comparison on the operator fast path with `number_order` when both
operands are machine ints or floats, without a value. The operator fast
path and `comparison` share `number_order` for the same case.

| Program | Instructions | M2 time |
| --- | ---: | ---: |
| fib | -10.3% | 66.1 → 60.3 ms (-8.8%) |
| loop | -8.6% | 333.0 → 283.1 ms (-15.0%) |
| generators | -1.6% | 208.9 → 201.4 ms (-3.6%) |
| dicts | +0.3% | |
| the rest | 0% | |

### Hot sites make numbers inline

`spy_int` and `spy_float` are public and called from almost two hundred
places, so the compiler keeps them out of line. Their bodies are now
`int_value` and `float_value`, inline, which the arithmetic of
`number_fast` and the range iterator call directly; every other caller
still calls the public functions. Instructions: nbody -2.5%, loop
-1.8%, fib -1.3%, the rest -0.3% to -0.9%; the text section grows by
2.3 KB.

### Any single comparison is tested without a bool

The test of a comparison skipped the bool only when both operands were
on the operator fast path. `if i % 3 == 0` evaluates `i % 3` first, so
it still made a bool. `condition` now evaluates both operands of any
single comparison itself, compares two numbers with `number_order`, and
leaves the rest to `comparison` and `spy_truth` as before. Instructions:
loop -12.2%, fib +0.6%, the rest within 0.3%.

### A store takes its target's operands at hand

`o.x = v` and `l[i] = v` ticked and then evaluated `o`, `l` and `i`
through `eval`; `b[3] -= x` evaluated `b` and `3` the same way. As on
the operator fast path, a literal or name is now taken as it is while
tick has only the line to record, and held across the store, which may
run a `__setattr__` or `__setitem__` that unbinds it. Instructions:
nbody -3.2%, strings -0.8%, classes -0.6%, loop +0.2%, the rest 0%;
per iteration, a loop of `o.x = i` -9% and one of `l[1] = i` -18%.

### A call knows its arguments are plain

Every call looked at the kind of each argument to decide whether up to
eight plain positional ones could go on the C stack. The compiler now
marks such calls `F_PLAIN_CALL` once, and a literal or name argument is
taken as it is while tick has only the line to record, as an operator's
operands are. Instructions: strings -1.1%, classes -0.7%, fib -0.5%,
dicts and bigint -0.4%, the rest within 0.2%.

### A kept environment serves any function of its depth

A call's depth keeps the environment of the last function that returned
there, but only a call of that same function took it again. `acc.add(step)`
and `acc.dot(step)` alternate at one depth, so every `dot` call built a
fresh environment and freed it. A kept environment of another function
now takes the new one's keys in place of its own, which also covers a
released scope whose address was taken again. The small-map scan of
`env_find`, which reads an instance's two or three attributes, is now
inline, and indexed maps take an out-of-line probe. Instructions: classes
-2.4%, fib +0.2%, the rest within 0.1%. Wall time was within the noise of
a busy machine.

### An attribute takes its name at hand

`self.x` evaluated `self` through a second `eval`. The attribute case now
takes a name's value along the fast path while tick has only the line to
record, held across the lookup, which may run a `__getattr__` that unbinds
it. Unlike the attempt on the operator fast path (below), only attribute
nodes pay for the test. Instructions: classes -2.0%, the rest 0%; a loop
of `y = o.x` from 257 to 239 per iteration.

### A quiet tick is one comparison

Whether a tick has nothing to do but record its line was three tests: no
pending error, no attention (callbacks queued or steps counted), and the
running unit's filename already copied. The context now remembers the
unit whose ticks are quiet: the slow tick sets it once it has copied the
filename and found nothing waiting, and queueing a callback, setting a
step limit, a trace function or any change of the copied filename clears
it. The test is the pending error and one comparison, on every statement
and every operand taken at hand. Instructions: generators -1.5%, loop
-1.4%, nbody -1.0%, fib -0.7%, the rest -0.2% to -0.6%. Wall time on
the M2 (15 runs): classes -4.2%, nbody -3.4%, the rest within 1%, but
generators +2.9%, although a clang build runs 2.8% fewer instructions
there too. Placing the field beside `error_type`, aligning functions and
reordering the test did not recover it; the cause is not found.

### Machine ints divide on the fast path

`%` and `//` on two machine ints went through `binary` and the general
integer dispatch, although `i % 7` is as common in loops as `i + 1`. The
number fast path now floors them itself: C's truncated quotient, moved
down by one when the remainder's sign differs from the divisor's, which
also moves the remainder by the divisor. A zero divisor and
`-2**63 // -1`, whose quotient leaves the machine range, still take the
general path. The division spec test gained the four sign cases and the
64-bit edges, on both operators and their augmented forms. Instructions:
loop -10.7%, sort -5.0%, generators -4.9%, dicts -2.3%, classes -1.6%,
strings -1.4%, nbody +0.3%, fib +0.2%. Wall time: loop -11.0%,
generators -4.6%, sort -2.6%, dicts -2.1%, the rest within 1%.

### Any comparison of two numbers skips the dispatch

An operator whose operands are not literals or names, as in
`x % 2 == 0`, misses the operator fast path and is evaluated in full.
Its comparison went to `comparison` even when both sides were machine
ints or floats. Each link of a comparison chain now asks `number_order`
first, as the fast path and `condition` do. Instructions: generators
-0.9%, the rest 0%.

### A dict read goes straight to its entries

`d[k]` on an exact dict passed the list, range and class tests of
`get_index` and asked `builtin_base` before reaching the dictionary.
Hashing a str whose hash was already kept still entered the recursion
guard and the general hash switch, and every probe retained the
candidate key and checked afterwards that no comparison callback had
moved it. An exact dict now comes right after the list case, a kept str
hash is returned at once, and a probe that finds the key itself or two
exact str values decides without the guard, since no code can run. A
loop of `x = d["a"]` fell from 564 to 452 instructions per iteration.
Instructions: strings -1.2%, dicts -0.7%, the rest 0%.

### The machine loads leaves itself

The first step toward bytecode (above). A literal or name the generator
machine pushed went through `BC_EVAL` and so through `eval`; `BC_LOAD`
now takes it along the fast path, falling back to `eval` when the path
misses. The machine also keeps its instruction array in a local rather
than reloading it through the program each step. Instructions:
generators -2.2%, the rest 0%. Wall time: generators 142.8 -> 139.2 ms
(-2.5%).

### Comparisons become machine steps

With leaves loaded by `BC_LOAD`, each node kind was measured as machine
instructions in place of a whole `BC_EVAL`, alone and together, on
generators. Comparisons alone saved 0.1%; binary operators, unary
operators, attributes and indexes changed nothing alone, and all of them
together cost 2.3%: `x % 2` as one `BC_EVAL` takes its operands at hand
on `eval`'s operator fast path, while three machine steps each pay the
loop's fixed work of about 20 instructions. So comparisons now compile
to machine steps and the rest stay whole until the loop is cheaper. The
machine's `BC_BINARY` and `BC_COMPARE` also try the number fast paths
first, as `eval` does. Instructions: generators -0.1%, the rest 0%.

### A function reads its module's globals directly

`fib` inside `fib` missed the remembered local and went to `name_outer`,
which walked from the function's environment to the module's dictionary
and there found the remembered entry: about 41 instructions, call and
loop included, for a lookup that already knew its answer. `name_fast`
now tries that entry itself when the node was last found outside the
running scope and the function's parent is an exact dictionary, the
module's globals. Builtins and closures keep the walk. Asking whether a
scope's locals are ordered is now an inline test, with the ordering out
of line. Instructions: fib -4.3%, strings -0.8%, classes -0.6%, the rest
within 0.2%. A method's parent is its class's cell environment, which
binds only dunder names such as `__class__`; `name_outer` now looks past
it to the module's remembered entry first (classes -0.6%; doing so in
`name_fast` cost fib 0.6%, every name read paying the test). Wall time: fib 44.3 -> 41.8 ms (-5.8%), strings -1.3%, nbody
+0.3% and +1.9% in two runs.

### The machine operates on leaves in one step

A walker node that is not a leaf costs about 100 instructions, half of
them `eval`'s entry and exit; a machine step costs about 25. The walker's
advantage is taking literal and name operands at hand. `BC_OPERATE` gives
the machine the same: an operator the compiler marks `F_OPERATOR`, a
comparison included, is one step that takes its operands along the fast
path and falls back to `operate` or `eval` as `eval` does. `operate`,
`operator_fast` and the machine-int helpers are now marked always inline:
with a second caller the compiler stopped inlining them into `eval`, and
fib and classes took 1% more instructions. Instructions: generators
-4.7%, the rest within 0.2%. Wall time: generators 142.5 -> 131.9 ms
(-7.4%), the rest 0% to -1.3%.

### A Python call skips the general dispatch

A call node with plain positional arguments whose callee is a Python
function went through `call_keywords`: the context check, the keyword
check, a second guard of the C stack, a cascade of type tests and
`call_result`. It now calls `call_function` itself and keeps only the
error normalization; the stack stays guarded by `eval`, which every node
of the body passes. Forcing `call_function` inline at both sites made
classes 0.4% to 1% slower on the M2, so the compiler chooses. Instructions:
fib -2.1%, the rest within 0.2%. Wall time: fib 42.4 -> 39.7 ms (-6.3%),
classes -0.4% to -1.2%; generators, loop and dicts within their noise.

### A scope keeps its own environments

Environments were kept one per call depth, so `add` and `dot`, which
alternate at one depth, re-keyed the kept environment on every call:
releasing one key per local and retaining the other scope's. Each scope
now keeps up to four environments, chained through their parent field, in
a list of its own. A kept environment always carries its scope's keys, so
taking one is a pop, and the frame stack holds no environments. Freeing a
unit drops its scopes' lists; the context's release drops every unit's
lists before its values. A recursion takes back the environment its last
returned call left, as before. Instructions: classes -3.1%, fib -1.9%,
generators and sort -0.3%, the rest within 0.1%. Wall time: classes
116.5 -> 109.8 ms (-5.8%), strings -2.0%, fib -1.7%, generators -1.5%,
loop -0.5%. Inlining the list's release into `free_value` cost every
program two instructions per freed value, so it stays out of line.

### An environment remembers it holds its scope's keys

Before keeping an environment, its release compared every key with its
scope's symbol keys, since a deleted and rebound local may come back in
another position. `open_locals` now marks the environment it fills with
those keys, and removing any entry clears the mark; appending one changes
the length, which is checked as before. The flag fills padding after
`odd_keys`, so values keep their size. Instructions: classes -1.4%, fib
-1.2%, sort -0.2%, the rest within 0.01%. Wall time: fib -1.5%, classes
-1.3%, sort -0.6%.

### A method object calls its function directly

`call_with_self` puts the instance before the arguments, for a method
object and for `__init__` after `object.__new__`. It then went through
`call_keywords` a second time, repeating the context check, the keyword
check, the stack guard and the type cascade its caller had just done. A
Python function now goes to `call_function`, as a call node's does.
Moving the same test into a helper shared with `eval_call` cost fib 0.3%,
so each keeps its own. Instructions: classes -0.7%, the rest unchanged.
Wall time: classes -1.0%.

### Built text starts at 32 bytes; short text lives in its value

`join`, `replace`, `upper`, f-strings and `str()` build their result in a
`Buffer`, which grew from 8 bytes by doubling: a 40-byte line took four
reallocations. The first append now takes 32 bytes. Doubling from 8 gives
the same capacities from 16 bytes up, so only shorter results would hold
more, and those are now copied into the value's own short-text room, as
`spy_string` stores them, and the buffer is freed. `str()` and `repr()` of
a machine int write the digits on the C stack and make the str directly.
Starting at 64 bytes saved more on `strings` but kept 29 MB more for 900,000
short strings. Peak memory for a list of 300,000 each of `str(i)`, `f"{i}"`
and `s.upper()` went from 129 MB to 119 MB. Instructions: dicts -5.5%,
strings -4.5%, the rest within 0.03%. Wall time: strings 130.2 -> 123.4 ms
(-5.2%), dicts 75.0 -> 71.1 ms (-5.1%), sort within noise.

### A called name is taken at hand

`fib(n - 1)` evaluated `fib` through `eval`, although its arguments
already took a name or literal as it is. A plain call of a name now
reads it along `name_fast` while tick has only the line to record. A
method's global, past its class cell environment, misses that path and
paid for both lookups (classes +0.3%), so the call node carries
`F_NAMED_CALLEE` until its first miss, as an operator drops
`F_OPERATOR`. Instructions: fib -1.9%, dicts -0.4%, classes and bigint
-0.3%, the rest within 0.1%. Wall time, beside a running fuzzer: fib
-3.1%, classes -1.9%, dicts unchanged.

### A class call tests the builtin types once

`type.__call__` compared the class with ten builtin types that have
constructors of their own before trying a native constructor or a plain
`__init__`, so `Vec(x, y)` and `str(i)` paid ten comparisons. Those types,
like every builtin type without a native constructor, are marked 2 in
their flags, which never change, so one test of the mark now guards the
comparisons. Checking `plain_init`'s cache first instead saved classes as
much but cost dicts 0.3%. Instructions: dicts -0.6%, classes -0.5%,
bigint -0.4%, nbody -0.2%, the rest within 0.1%. Wall time: dicts -2.6%,
nbody -0.8%, classes -0.7%.

### A machine test's bool is its truth

`while i < n` and `if x % 2 == 0` in a generator compile to a
`BC_OPERATE` step and a conditional jump, which asked `spy_truth` about
the bool the comparison had just made. A test's step now hands the
jump the bool's truth, as `BC_EVAL` does for a test it evaluates.
Instructions: generators -1.2%, the rest unchanged. Wall time within
the noise (generators +0.1%, fib -0.2%).

### A call operand skips a second eval

In `fib(n - 1) + fib(n - 2)`, `eval` of the sum guarded the C stack and
set the evaluation environment, then evaluated each call through `eval`
again, which did both a second time before reaching `eval_call`. A
binary operator with a call operand is now marked when
compiled, and while tick has only the line to record, its call operands
record their line and go to `eval_call` directly. The stack stays
guarded: the operator's own `eval` guards each level, so a recursion
through `f(n - 1) + 1` with the recursion limit raised to 10^7 still ends
in a RecursionError. Testing each operand's kind without the mark cost
nbody 0.3%; with it, nbody takes 0.1% more instructions and the same
wall time. Instructions: fib -5.7%, dicts -1.1%, strings -0.8%, classes
-0.6%, sort +0.07%, nbody +0.14%. Wall time: fib 36.4 -> 34.4 ms (-5.6%),
dicts -4.2%, strings and classes -0.3%, sort and nbody unchanged.

### An attribute operand skips a second eval

`self.x + other.x` evaluated each attribute through `eval` after the
sum's own `eval`. The mark is now `F_DIRECT_OPERAND`, and covers an
attribute of a name too: the name is read along `name_fast`, retained
across the read, since a property may delete it, and passed to
`node_attribute`. Descriptors and `__getattr__` run as calls, which
guard the stack themselves. Instructions: classes -7.8%, fib, dicts and
strings +0.05%, the rest unchanged. Wall time: classes 107.3 -> 95.3 ms
(-11.2%), fib -0.7% to -1.1%, strings -0.8%, dicts -0.2% in a second run
(+1.4% in the first).

### An append that fits does not call grow

Every `append` to a text buffer called `grow`, which returned at once
when the text fitted. The capacity is now compared in `append`, so
`grow` runs only to reallocate. Instructions: strings -1.0%, bigint
-0.3%, the rest unchanged. Wall time: strings -0.6%, fib -0.7%, nbody
and bigint within the noise (bigint 6.0 -> 6.1 ms, sd 0.1, in 60 runs).

### A machine test is one step

A generator's `while i < n` or `if x % 2 == 0` was two machine steps: a
`BC_OPERATE` that pushed a bool and a `BC_FALSE` that popped it and
jumped. When `emit` is asked for a `BC_FALSE` right after a test's
`BC_OPERATE`, it turns that step into `BC_TEST`, which operates and
jumps; a comparison of two numbers decides without making a bool. Every
test step is now fused, so the bool truth that `BC_OPERATE` handed the
jump (the entry before last) is gone. Instructions: generators -3.0%, the
rest unchanged. Wall time: generators 132.4 -> 125.2 ms (-5.5%), loop
-0.3%. nbody, which runs no machine code, measured 2.2% slower in three
runs; built with `-falign-functions=64`, the two trees ran nbody in
238.0 and 238.2 ms and generators in 133.1 and 126.2 ms, so the
difference is where the M2 build places code, not work. Aligning every
function cost 0.5% to 1% elsewhere, so the build does not.

### A machine assignment skips the statement dispatch

`i += 1` in a generator is a `BC_EXEC` step, which ran
`execute_statements` for one statement: a second tick and the statement
switch before `assign`. The step now calls `assign` itself, through an
out-of-line `assign_step`, with `assign` forced inline so that
`execute_statements` keeps it inline too; a plain second call site had
stopped that (loop +3.4%, nbody +2.6%). The first measurement of this
form ran nbody 2% to 3% slower on the M2 with gcc's counts unchanged,
and was left out; after the fused test step moved the code again, the
same change ran nbody 2.7% faster, as code placement decides.
Instructions: generators -1.8%, dicts -0.2%, classes -0.1%, the rest
unchanged. Wall time: generators 137.9 -> 120.0 ms (-13%), nbody -2.7%,
strings and sort -0.8%, the rest within 0.6%.

### Hot functions start on a cache line

Three changes in a row moved nbody's wall time by 2% to 3% on the M2
without changing its instructions, in either direction: clang does not
place functions in source order, so a change in the generator machine
moved the walker's hot loops relative to cache lines and branch
predictor sets. `eval`, `execute_statements`, `condition`, `eval_call`,
`call_function` and `run_machine` are now `HOT`, aligned to 64 bytes, so
each keeps its own placement whatever changes around it. Alone it is
neutral: every program within 0.6% of before but sort (+1.6%, its
instructions unchanged); under gcc it adds 0.1% to 0.3% to most programs'
instructions. With it, fusing a leaf yield (the next entry) measured
nbody +0.2%, where the same change had measured +2% to +3% without it;
but the change after that still moved nbody, strings and classes 1% to
2% with their instructions unchanged, so it steadies placement only in
part. Aligning every function cost 0.5% to 1%, and aligning every block
that is not fallen into (`-mllvm -align-all-nofallthru-blocks`) evened
nbody between trees but cost strings 3%.

### A leaf yield is one step

`yield i` was a `BC_LOAD` that pushed `i` and a `BC_YIELD` that popped
it. A yield of a name or literal now compiles to one `BC_YIELD` with
`arg` 1, which reads its operand along the fast path, keeping the yield
node so that its line is the one recorded. The fusion is made where the
yield is compiled, not in `emit`: a conditional's jump may target the
yield's own position. Instructions: generators -3.4%, the rest
unchanged. Wall time: generators 120.6 -> 114.7 ms (-4.9%), the rest
within 1%.

### A yield statement drops what is sent

`yield i` as a statement was followed by a `BC_POP` of the value its
resumption pushed. A yield statement now compiles to a `BC_YIELD` with
`arg` bit 2, which marks the machine `drop`, and its resumption pushes
nothing. Instructions: generators -4.1%, the rest identical. Wall time:
generators 114.6 -> 109.7 ms (-4.2%), fib -3.3%; nbody +1.7%, strings
+2% and classes +1% in three runs each, with their instructions
identical: code placement again.

### Keys of one kind sort without dispatch

Every comparison of a sort went through `plain_less`, which tests both
keys' types, and then tested for a pending error. As CPython's
`list.sort` does, a sort now looks at its keys once: when all are small
ints, all floats, or all tuples of small ints, its comparisons read the
numbers directly and no comparison can raise. Other keys compare as
before. The order is the one `<` gives, ties keep their order, and the
merge itself is unchanged. Instructions: sort -23.8% (969.4 → 739.0 M),
the rest unchanged. On the M2 sort took 137.2 → 121.3 ms (-11.6%;
CPython 127.7 ms). Inlining a copy of the merge for each kind saved
more instructions (-28.9%) but made sorting tuples 50% slower on the
M2, so one merge function tests the kind at each comparison, a branch
that is always predicted.

### An unpacking reads a tuple or list in place

`a, b = t` made a list, took an iterator of `t` and appended each item,
ticking for each, before storing the targets: 59 ns an assignment on the
M2, against CPython's 2.5 ns. As CPython's `UNPACK_SEQUENCE` does, an
exact tuple or list with an item for each target and no starred target
is now read in place. Its items are held first, since storing a target
can run code that changes a list being unpacked; every other value is
unpacked as before, with the same errors. A target tuple given a tuple
display of as many items, `a, b = b, a`, evaluates the items and stores
them without making the tuple at all, which nothing could see; the
parser marks such assignments.

Two million assignments in a loop on the M2: `a, b = t` 145 → 54 ms,
`a, b = b, a` 207 → 51 ms (an empty loop takes 26.5 ms). Instructions of
the programs, which seldom unpack: +0.2% at most. Wall time averaged
over eight code layouts: generators -1.7%, nbody +0.7%, fib +0.6%, the
rest within 0.5%.

### A method without arguments names itself only for an error

`str.upper`, `str.isdigit` and the other methods that take no arguments
formatted their name, `"str.upper"`, with `snprintf` on every call, for
the error they would raise if given arguments. The name is now formatted
only when there are arguments or keywords to refuse. Two million calls
of `s.upper()` on the M2: 238 → 110 ms (an empty loop takes 26.5 ms).
Wall time averaged over eight code layouts: strings -3.7%, the rest
within 0.2%.

### `in` searches a list or tuple in place

`x in l` asked whether the list's type overrides `__contains__`, took an
iterator and stepped it, comparing each item. An exact list or tuple is
now searched by index, as CPython's `list_contains` does: each item is
held across its comparison, which may change the list, and the length
is read again for the next item. The comparison, its errors and the step
counted per item are those of the iterator's loop. Two million `3 in l`
over a three-item list on the M2: 129 → 80 ms (CPython 73.5 ms). Wall
time averaged over eight code layouts: every program within 0.4%.

### A builtin class call names itself only for an error

`str(i)`, `int(s)`, `dict(...)` and the other builtin class calls looked
up the class's `__name__` on every call, for the error they would raise
if given keywords they do not take; `__new__` looked it up again for its
receiver checks. The class itself is now passed along, and its name is
read only when an error is raised. Instructions: dicts -5.4%, bigint
-4.0%, nbody -1.7%. Two million `str(i)` on the M2: 126 → 107 ms. Wall
time averaged over eight code layouts: dicts -3.2%, nbody -1.2%,
strings -0.8%, the rest within 0.4%.

### A free variable is remembered in its enclosing environment

A function reading a name its enclosing function binds looked the name
up in the enclosing scope's symbols and then in its environment, on every
read. The read now remembers the entry's position and the symbol's key,
as reads of locals do; only environments of that scope hold the key, so
a matching key at that position is the binding the lookup would find,
in whichever call of the enclosing function made it. The check sits in
the out-of-line part of the lookup: inlined, it slowed every program by
up to 1%. Two million calls of a closure returning a free variable on
the M2: 102 → 86 ms. Wall time averaged over eight code layouts: every
program within 0.5%.

### A list, tuple or range iterates without a protocol search

Taking an iterator asked whether its source was an iterator already, an
instance of a builtin subclass, or a value whose type dispatches special
methods, and then checked it against every iterable kind. An exact list,
tuple or range is none of these (a subclass's instance is an instance),
so it now gets its iterator first. Two million `iter(t)` on the M2:
125 → 114 ms; `[k for k in range(3)]`: 499 → 480 ms. Wall time averaged
over eight code layouts: nbody -1.5%, strings -1.1%, the rest within
0.5%.

### A comprehension reuses its environment

A list, set or dict comprehension made a fresh environment for its
variables on every run, entries and keys included, and freed it with the
general walk over a generator's edges. It now takes and returns one the
way a function call does: when only the run held it, the environment
keeps its storage and keys for the next run, up to four for each
comprehension. One a closure captured is freed as before. Two million
`[k for k in range(3)]` on the M2: 472 → 446 ms. `release_locals` now
has two callers and is marked inline: left to the compiler, it was
called out of line and fib took 1.6% longer. Wall time averaged over
eight code layouts: strings -0.7%, the rest within 0.5%.

### A growing buffer moves through the spare blocks

Released blocks of up to 256 bytes wait in per-size spare lists, but a
block resized between those sizes went to `realloc`, which never takes
from them. A buffer that starts small and grows, as `join` and an
f-string's do, left its last block on a larger size's list each time,
and fresh allocations seldom came for it: `strings` held 8 MiB of such
blocks at its end. A resize to or from a small size now takes the new
block from the spare lists and returns the old one there; only a resize
between two large sizes calls `realloc`. Peak memory of `strings`:
11.7 → 3.1 MiB. Wall time averaged over eight code layouts: strings
-6.8%, the rest within 0.5%.

### A machine step keeps its place in a local

The machine read and wrote `m->pc` in memory on every step, and every
step ran the release of its two owned operands, although most own none.
The program counter is now a local of `run_machine`, written back only
where `machine_unwind` or `finish_delegate` reads it and where the
generator suspends, and the steps that own no operand (`BC_EVAL`,
`BC_OPERATE`, `BC_LOAD`, `BC_EXEC`, `BC_JUMP`) continue past the
release. Instructions: generators -1.2%, strings -0.2%, sort -0.1%, the
rest unchanged; on the machine micro-benchmark of a `while` loop that
holds a `yield`, about 1.6 instructions a step. Wall time averaged over
eight code layouts: generators -2.7%, the rest within 1%.

### A machine jump reads a bool's truth

A test whose comparison has an operand that is not a leaf, such as
`x % 2 == 0`, compiles to `BC_COMPARE` and then `BC_FALSE`, and
`BC_FALSE` asked `spy_truth` for the truth of the bool the comparison
left. It now reads a bool's value itself, as `BC_TEST` does.
Instructions: generators -1.5% (GCC) and -1.6% (clang), the rest
unchanged. Wall time averaged over eight code layouts: generators -3.4%,
the rest within 0.6%.

### A negated number is a constant

`-1` is a unary minus applied to the literal `1`, and the walker
negated it, allocating a new number, each time it ran. CPython folds a
negated number into one constant when it compiles. The compiler now does
too: after the literals get their values, a `-` whose operand has a
constant (a number, or a negation already folded) gets the negated value
as its own constant, so it is a leaf the fast paths read in place. A
function looping 300,000 times over `if i == -1:` took 22% fewer
instructions and 27% less time on the M2. The bench programs use negative
numbers only while setting up, so their instructions are unchanged; their
wall time averaged over eight code layouts is within 0.6%.

### A float power from a positive base skips the dispatch

`d2 ** 0.5` in nbody went through `binary`, about 400 instructions with
`pow` itself, because the number fast path left powers out: a negative
base may need a complex result and a zero base may divide by zero. A
positive finite base with a finite exponent has neither case; its power
is `pow`, and an infinite result is an overflow. The fast path now takes
that case and leaves an overflow, and every other power, to `binary`.
Instructions: nbody -3.4% (GCC -3.3%), the rest unchanged. Wall time
averaged over eight code layouts: nbody -3.1%, the rest within 0.7%.

### A dying number returns to its spare list directly

Ints and floats are made by `number_new`, which takes a spare value and
leaves it off the list of values the collector walks. When one died,
`release_dead` still sent it through `free_value`, which tests for weak
references, unlinks a listed value, switches on the type and looks up the
size class. A number without big-integer digits that is not listed (one
`number_new` made; neither ints nor floats take weak references) now
goes straight back to its spare list. Instructions (clang): loop and
nbody -5.6%, generators -3.2%, classes -2.4%, dicts -1.9%, sort -1.7%,
strings -1.1%, bigint -0.6%, fib unchanged (its numbers are cached small
ints). Wall time averaged over eight code layouts: nbody -6.5%, loop
-3.0%, classes -2.6%, generators -1.9%, sort -1.2%, the rest within
0.6%.

### Two strs concatenate before the operator dispatch

`"k" + str(i)` reached `text_concat` through `binary`'s tests for
special methods, templates, set views, formatting and numbers, then
`sequence_binary`'s for sets, dictionaries and bytes: about 100
instructions before the copy. Two exact strs joined by `+` now take
`text_concat` right after the exact float and int cases. Placed first,
ahead of the number cases, the test cost bigint 0.2%; at the top of
`sequence_binary` it saved a quarter as much. Instructions (clang):
dicts -2.9%, bigint -0.2%, the rest unchanged. Wall time averaged over
eight code layouts: dicts -1.6%, the rest within 0.6%, except sort
(-1.7%) and classes, which does not run `binary` (+0.4%; +1.2% on a busier
machine, where shifting the code after `binary` by the same 192 bytes
alone measured +0.3%).

### A Python call enters and leaves its frame inline

A plain call made four C calls besides running its body: `kept_env`,
`open_locals`, `enter_frame` and `leave_frame`, each saving and
restoring registers for a few loads and stores. Each now has an inline
fast path, and what is rare moves to a function of its own: reaching the
recursion limit or growing the frame array (`frame_room`), a trace, an
error or a frame object on the way out (`leave_traced_frame`), and a new
environment's keys (`new_locals`). Leaving tests `watch`, which every
trace or profile function sets, instead of both settings. Instructions
(gcc): fib -5.4%, generators -4.2%, classes -2.6%. Wall time averaged
over eight code layouts: fib -9.2%, generators -5.0%, classes -3.8%, the
rest within 0.5% except dicts, which makes no Python call and runs the
same instructions (821.2 M), +0.5% to +0.6% in three runs from the code
that follows the call path moving; aligning `store_slow`, the one hot
unaligned function it runs there, did not change it.

### Each hot machine step dispatches the next

The instruction machine chose every step at one `switch`, at the top of
its loop. One indirect jump stood for every pair of steps, so the
processor predicted the next step from the shared history of all of
them. Built with GCC or clang, every step now has a label, and the
frequent ones (loads, operators, tests, stores, jumps, `BC_NEXT`) end by
jumping straight to the next step's label, through a table built from
the same list as the step enumeration, when the tick has only a line to
record. A step that ends any other way, or a tick with work, goes back
to the loop as before; other compilers keep the `switch`. What runs, and
in what order, is unchanged.

Wall time fell much more than instructions, which is the misprediction
going: instructions (M2 counters) generators -3.4%, strings and sort
-0.6%, the rest unchanged. Wall time averaged over eight code layouts:
generators -10.9% (-8.8% and -7.8% in two earlier runs), strings -2.5%,
sort -1.5%, fib -1.0%; loop +0.5% and classes +0.9% run the same
instructions, which only placement moves.

### A call statement skips eval's other cases

A call on its own as a statement, as an assignment's value or as what a
`return` returns went through `eval`, which tests for a literal, a name and
an operator before it reaches the call, and saves every register its other
cases use. While the tick has only the line to record, such a call now takes
the stack guard, the evaluating environment and the line itself and goes to
`eval_call`. Two rare helpers inlined into the statement loop,
`display_value` and `raise_assertion`, are out of line: the constant keys
they built were set up on every entry to the loop, twelve instructions with
clang. Instructions (M2 counters): classes -2.1%, loop -1.6%, fib, generators
and sort -1.4%, nbody +0.1%; a loop calling `f(i)` -4.4%. Wall time averaged
over eight code layouts: classes -2.9%, loop -2.1%, generators -1.6%, sort
-1.4%, the rest within 0.3%.

### Hot paths stay out of large functions

A call into a large function saves every register its rarest case uses
before its first test. Four common paths paid for that without needing the
function: an `if` whose test is false and that has no `else` ran
`execute_statements` over no statements; `return` of a literal or a name
went through `eval`; a loop took the next item of a range, list or tuple
iterator through `iterator_next`, whose fast paths come before its many
other kinds; and storing a local released a dying int or float through
`release_dead`. Each now stays in its caller: the empty branch is skipped,
the leaf is read in place while the tick has only a line to record,
`iterator_fast` is an inline function that `iterator_next` and both loops
share, and the local store returns the number to its spare list. Instructions
(M2 counters): fib -3.1%, dicts -2.2%, nbody -1.8%, loop -1.2%, strings
-1.1%; an empty `for i in range(n)` -17%. Wall time averaged over eight code
layouts: fib -3.3%, loop -2.3%, dicts -1.7%, strings -1.3%, classes -1.2%;
bigint +1.1% at 6 ms with the same instructions, nbody and generators +0.1%.

### An attribute is an operand at hand

An operator whose operands are literals, names or an index of those takes
them as they are, without `eval`. `self.x + other.x` did not qualify, so
each attribute went through `eval` and the large `eval_inner`. An
attribute of a name now qualifies when the name holds a plain instance
whose class leaves the read to the instance's own entries, the answer the
attribute node already remembers for `node_attribute`; the entry's value
is borrowed, and `operate` holds both operands before any method runs.
The attribute test comes after the literal and name tests, so the other
operands pay nothing; an earlier try that read `self` directly inside
`eval` saved classes 1.0% and cost every other program up to 0.5% more
instructions. Instructions (M2 counters): classes -5.3%, the rest
within 0.2%. Wall time averaged over eight code layouts: classes -2.1%,
bigint -1.4% at 6 ms, the rest within 0.4% (strings read +1.2% once and
+0.3%/-0.2% with the order swapped).

### A profile-guided build

`make CC=clang CONFIG_PGO=y` builds the engine twice: once instrumented,
to run the specification tests, and once with the profile they leave,
which tells clang which branches are taken and which functions are hot.
The profile comes from the specification tests, so the bench programs
do not train their own build. The engine and its behavior are the same;
the default build is unchanged.

Wall time on the M2 (median of 15 runs), against CPython 3.15 built
the default way (`-O3`) and with `--enable-optimizations --with-lto`
(PGO and LTO, as release builds of CPython are):

| Program | spy `-O2` | spy PGO | CPython `-O3` | CPython PGO+LTO |
| --- | ---: | ---: | ---: | ---: |
| startup | 2.0 ms | 1.9 ms | 10.9 ms | 10.5 ms |
| fib | 33.4 ms | 28.0 ms | 30.1 ms | 25.0 ms |
| loop | 153 ms | 156 ms | 385 ms | 319 ms |
| nbody | 235 ms | 219 ms | 233 ms | 183 ms |
| strings | 120 ms | 103 ms | 112 ms | 86.3 ms |
| dicts | 67.3 ms | 62.3 ms | 90.9 ms | 66.5 ms |
| sort | 123 ms | 118 ms | 128 ms | 113 ms |
| classes | 89.8 ms | 79.3 ms | 97.7 ms | 70.9 ms |
| generators | 108 ms | 84.8 ms | 109 ms | 89.4 ms |
| bigint | 5.7 ms | 5.6 ms | 11.8 ms | 11.2 ms |

A profile helps CPython about as much as spy: against CPython's own
optimized build, spy's is faster on startup, loop, bigint, dicts and
generators and 4% to 20% slower on sort, fib, classes, strings and
nbody. Only loop, a module-level `while`, is slower with the profile
(+2%); the specification tests do not run such a loop hot.

## Tried and left out

- **A builtin found past the module's dictionary without the walk.**
  When a function's global name was remembered missing from the module's
  dictionary, checking the builtins dictionary's remembered entry first
  saved about 50 instructions per `len` or `range` lookup, but two
  million `len(l)` on the M2 took only 0.8% less time.
- **An augmented item assignment reads the list in place.** `b[3] -= x`
  took the old item and stored the new one through `get_index` and
  `set_index`; reading and replacing the slot inline cut nbody's
  instructions by 4.7%, but on the M2 nbody was unchanged (+0.3%) and
  classes took 2% longer.
- **A dying container frees its numbers and strings at once.**
  `release_edge` queued every item of a dying list for the loop of
  `release_dead`, which asks each whether it needs a finalizer; freeing
  a number or string as soon as its count reached zero cut classes'
  instructions by 1.3% and sort's by 0.5%, but on the M2 nbody took
  1.4% longer and loop 0.9%, averaged over eight code layouts.
- **A machine truth cleared only by the tests that read it.** `known`,
  the truth a `BC_SHORT` jump hands to the test it lands on, was copied
  and cleared on every machine step. Clearing it only in `BC_FALSE`,
  `BC_SHORT` and the error path cut generators' instructions by 1.1%, but
  its M2 wall time, averaged over eight code layouts, did not fall
  (+0.1% and +1.1% in two runs).
- **A quiet tick without the error test.** If setting an error also
  cleared `quiet_unit`, `quiet` could compare the unit alone and skip the
  test for a pending error. Instructions fell on every program (1-2%, fib
  -2.1% built with clang), but on the M2 fib took 1.6-3% longer, nbody
  1-3% and classes 2%, with the same results when every function was
  aligned to 64 bytes and when main was timed against a copy of itself.

- **Function bodies on the machine, toward calls without C recursion.**
  A plain `def` body was compiled to machine steps, expanding every
  statement and expression that holds a call, so that a call could
  become a machine step that pushes a frame instead of recursing in C.
  Run through `call_keywords`, which builds an argument tuple, fib took
  2.1 times the walker's instructions, classes 1.25 and nbody 1.11. With
  a direct call step that takes the arguments from the machine's stack
  (still recursing), fib took 1.245 times, classes 1.11 and nbody 1.05.
  Entering the machine for each call (taking a machine, setting up
  `run_machine`, unwinding the return and releasing the machine) was
  about 40 M of fib(25)'s 277 M instructions. A flat call removes that
  entry and the C recursion, about 75 instructions a call in function
  prologues, but leaves fib at about 237 M against the walker's 219 M
  before any frame push and pop. Flat calls wait for a machine step that
  costs well under the walker's node.

  A second prototype (2026-11, branch `experiment-flat-calls`) built
  them: a plain `def` body that holds a call compiles to machine steps,
  and a call to such a function pushes a frame onto a per-context pool
  and continues in the same `run_machine` loop; a return pops it. Every
  spec test passed. Callgrind counted fib 5.0% fewer instructions,
  classes 1.0% more and nbody the same, but M2 wall time, walker against
  flat calls in one binary, was fib +2.3% and classes +3% after the
  frame switch was trimmed from +12%. A machine loop without calls ties
  the walker, so the cost is in switching frames and entering and
  leaving the machine, not in dispatching steps. It found two bugs,
  fixed separately: a suspended `with` body called `__exit__` at the
  body's line, and a dict subclass's views did not hold the instance.

  Retried on threaded dispatch (2026-11-06), with calls, returns and frame
  switches dispatching their next step: in one binary, walker against
  flat, fib took 31.9 against 32.0 ms with 620 M against 505 M
  instructions (IPC 5.97 against 4.95), classes 91.4 against 94.6 ms.
  A linear recursion (`g(n - 1) + 1`, 50 deep, 20,000 times) took 77.0
  against 52.2 ms, 32% less, and there the walker's IPC is the low one
  (4.70): past the processor's return-address stack, a C return
  mispredicts. In fib's binary recursion every return lands on either
  the second call or the addition, so the flat return's indirect jump
  mispredicts instead, while C returns at depth below 30 do not. Calls
  that kept C recursion but ran bodies on the machine were slower on fib
  (33.7 ms) and classes (92.5 ms). classes loses because its loop runs at
  module level on the walker, so each method call enters the machine
  afresh. Flat calls pay once callers run on the machine as well.

  A call costs more than the steps around it either way. Per iteration
  of a loop in a function, against CPython 3.15 (`-O3`) on the M2:
  `f(i)` 694 against 301 instructions (81 against 41 cycles), `p.x` 249
  against 60, `if i < 0` 178 against 94; `x = x + i` 250 against 408.
  A flat call that runs every body on the machine still took about 500.

- **Locals in slots.** A local is already read as a slot: a name node
  remembers its entry's index and checks only that the entry still holds
  its symbol's key. Guarding a slot by the environment's scope and its
  `keyed` flag instead costs the same loads and comparisons; dropping
  the guard altogether, which `exec` of a function's code over a
  dictionary forbids, would save about 15 of fib's 900 instructions a
  call. Opening a kept environment already writes only the values.

- **Call arguments taken as direct operands.** Evaluating a call's
  arguments through `eval_operand`, as a binary operator's are, cost fib
  0.7% and classes 0.4%: arguments are mostly names, literals and
  arithmetic, and each paid the two extra kind tests.

- **A one-comparison stack guard.** Keeping the stack's floor instead of
  its top made `deeper` one unsigned comparison: 0.2% to 0.6% fewer
  instructions on most programs, but fib 2.1% to 3.3% slower on the M2 in
  two runs, and classes and generators no faster.

- **An if's branch in the same statement loop.** Keeping up to eight
  statements to resume after a branch in a local array, instead of
  running the branch through a nested `execute`, cost `nbody` 1.1% and
  most other programs 0.2% to 0.5%; only `loop` gained (0.5%). The array
  and the resume test weigh on every block the loop runs.

- **Keeping every freed value for reuse.** Released values beyond 64 go
  back to `malloc`. With no limit, `dicts` took 21% longer and `sort`
  9% longer on the M2: a long last-in-first-out list hands back memory
  that has left the cache, and the system allocator is fast.
- **A separate function for the slow part of `eval`.** `eval` has
  `eval_inner` inlined, so its fast paths (a literal, a local name) pay
  for saving the registers the slow part uses. Moving everything past the
  fast paths into a separate function added 1% to 2.5% instead.
- **A third allocation size for numbers.** Ints and floats fit 64 bytes
  with the smaller header. Choosing among three sizes made the allocator
  too large to inline into `spy_int` and `spy_float`, and forcing it
  inline slowed the other callers: `sort` gained 6% but `nbody`, `loop`
  and `generators` lost 3% to 10%.
- **`-O3`.** Within 1% of `-O2` on every program but `generators` (-5.6%),
  so the build keeps `-O2`. Measured again later, averaged over eight
  code layouts: sort -1.4%, classes and fib -0.9%, nbody +0.8%,
  generators +0.3%; still no clear gain for a larger engine.
