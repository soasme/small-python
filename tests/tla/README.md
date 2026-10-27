# TLA+ specifications

Formal models of parts of the Python 3.15 language, model-checked with TLC
and tied to real implementations by replaying them.

| Spec | Models | Replayed |
|---|---|---|
| `Generators.tla` | next/send/throw/close on generators and coroutines, including re-entry, ignored GeneratorExit, and finished objects | yes |
| `Exceptions.tla` | try/except/else/finally and with, under return, break, continue, raise, and bare raise, with `__context__` chains | yes |
| `Scopes.tla` | local, global, nonlocal, free, and class-scope name resolution, late binding, comprehension scopes | yes |
| `IntArith.tla` | int `+ - * // % divmod ** << >> & \| ^`, unary `- ~ abs`: floor division, remainder signs, two's complement bitwise operations | yes |
| `Calls.tla` | binding arguments to positional-only, positional-or-keyword, `*args`, keyword-only, and `**kw` parameters with defaults | yes |
| `Unpacking.tla` | assignment to target lists with starred and nested targets | yes |
| `GC.tla` | reference-count destruction, `__del__` at most once (PEP 442), resurrection, and `gc.collect()` of cycles | yes |
| `SpyGC.tla` | spy's own memory manager (`spy_release`, `finalize_later`, `weak_callbacks`, `collect_once`, `spy_collect`), run in lockstep with `GC.tla` | no; checked against `GC.tla` |

Each `NAME.tla` has a `NAME.cfg` naming its invariants and properties, which
restate what the Language Reference says (the finally clause always runs, a
finished generator stays finished, nothing reachable is freed, and so on).
`make test-tla` (after `make tla-tools`, which needs `curl` and a Java runtime;
set `JAVA` to choose one) runs `tests/tla_check.py`, which:

1. Runs TLC over the whole state space of every model.
2. For a model with a `NAME.replay.py`, dumps TLC's state graph and builds
   walks from the initial states that together take every transition. The
   replay script performs each step on real Python objects (calling the
   generator, running the program, assigning the variable) and compares the
   result with the model's next state.
3. Runs the replay on the pinned CPython 3.15 oracle, which must pass and so
   validates the model, then on spy, which must pass to conform to it.

## What this does and does not show

TLC checks the models exhaustively, but only within their bounds: two
iterations of a generator, programs of the stated shapes, two or three
objects with two attribute slots. The replay shows spy and CPython agree
with the model on every transition of that bounded space. Neither is a proof
that spy.c is correct: the C code is not verified against the models, and
behavior outside them is covered by the other test suites.

`SpyGC.tla` goes one level lower. It models the algorithm spy.c implements,
reference counts, the pending stack, the finalization queue, and trial
deletion included, and TLC checks that after every step it has the same
heap and makes the same `__del__` calls as the language model, that it never
touches freed memory or frees a referenced object, and that its counts are
exact between statements. That this model matches spy.c is established by
reading the code; the function names in the spec point at it.

`SpyGC.cfg` checks two objects so `make test-tla` stays quick; setting
`Obj = {"a", "b", "p"}` checks three (about 4.75 million states). With three
objects, TLC rejects each of these deliberate breakages of the algorithm: the
earlier `spy_collect` that did not run finalizers before collecting again; a
collector that freed what a waiting finalizer could reach; finalizing an
object twice; releasing an assignment's old value before retaining the new
one; miscounting references from garbage into live objects; and freeing an
object's slots in the other order. Depth-first finalization order (a
grandchild's `__del__` before its parent's sibling's) takes four objects and
is outside these bounds.

The models found three bugs in spy, since fixed: comprehensions reported an
unbound local of their function as a free variable, finalizers queued while
freeing an object ran after objects that were already waiting, and `str`
length, slicing, and `find()` rescanned the whole string on every call
(which made the replays themselves time out). They also found a mistake in a
first draft of `Generators.tla`: CPython raises RuntimeError when throwing
into a finished coroutine, which the oracle replay caught.
