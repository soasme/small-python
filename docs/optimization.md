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

## Tried and left out

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
  so the build keeps `-O2`.
