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

## Changes

| Change | Suite instructions |
| --- | --- |
| [Releasing a number or string frees it at once](#releasing-a-number-or-string-frees-it-at-once) | -1.6% to -9.7% |
| [A name remembers what it is in its function](#a-name-remembers-what-it-is-in-its-function) | -5.2% (nbody) to +0.4% |

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
