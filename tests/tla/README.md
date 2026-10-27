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
| `MRO.tla` | C3 linearization of class hierarchies, duplicate bases, and inconsistent orders | yes |
| `Operators.tla` | dispatch of `+`, `+=`, `==`, `!=`, `<` to special methods: reflected methods, subclass priority, NotImplemented, in-place fallback, default comparisons | yes |
| `Attributes.tla` | getting, setting, and deleting an attribute through data and non-data descriptors, properties, slots, the instance dict, class attributes, and `__getattr__` | yes |
| `Match.tla` | `match` statements of two cases over literal, singleton, capture, wildcard, sequence, star, mapping, class, or, and as patterns | yes |
| `Evaluation.tla` | evaluation order of operands, short-circuiting, chained comparisons, call arguments, displays, and assignment targets | yes |
| `ClassCreation.tla` | the order of `__prepare__`, the class body, metaclass `__new__`/`__init__`, `__set_name__`, `__init_subclass__`, and class decorators | yes |
| `YieldFrom.tla` | delegation with `yield from`: sent values, thrown exceptions, and `close()` reaching the subgenerator, and its return value | yes |
| `AsyncGenerators.tla` | asend/athrow/aclose on async generators, including ignored GeneratorExit and a closed generator | yes |
| `ExceptStar.tla` | `except*` clauses splitting exception groups, re-raising, raising new exceptions, and the shape of what escapes | yes |
| `Iteration.tla` | `for` loops with `break`, `continue`, and `else` over the iterator and sequence protocols, and objects that are not iterable | yes |
| `Super.tla` | cooperative `super()` calls in a diamond hierarchy | yes |
| `Dicts.tla` | dict insertion order under setting, updating, deleting, popping, and re-inserting keys | yes |
| `NumericLiterals.tla` | integer, floating-point, and imaginary literals: prefixes, underscores, leading zeros, and literals running into names | yes |
| `StringLiterals.tla` | string and bytes literals: quotes, prefixes, every escape sequence, raw strings, and adjacent literals | yes |
| `Indentation.tla` | the indentation stack: INDENT/DEDENT, tab stops, TabError, IndentationError, and blank lines | yes |
| `LineStructure.tla` | physical and logical lines, comments, explicit and implicit line joining, and encoding declarations | yes |
| `Identifiers.tla` | names: XID start and continue characters, NFKC normalization, keywords and soft keywords, and `__debug__` | yes |
| `Tokens.tla` | tokens: the longest operator or delimiter, whitespace between tokens, precedence, chained comparisons, and chained assignment | yes |
| `FStrings.tla` | f-strings: doubled braces, fields, `=`, conversions, nested format specifications and their depth limit, and comments | yes |
| `TStrings.tla` | t-strings: the Template's strings and each interpolation's value, expression text, conversion, and format specification | yes |
| `Mangling.tla` | private name mangling in class bodies, methods, parameters, and `global`, and keyword arguments that are not mangled | yes |
| `Singletons.tla` | `None`, `NotImplemented`, and `Ellipsis`: one object each, their truth values, and their types | yes |
| `Objects.tla` | identity, `id()`, aliasing, mutation, unchangeable types, and immutable containers of mutable objects | yes |
| `NumericTypes.tla` | int and bool as infinite two's complement under masks and shifts, numeric reprs (no leading or trailing zeros, exponent form), and read-only complex parts | yes |
| `SeqOps.tla` | sequence indexing, slicing with steps, `in`, `count`, `index`, `+`, `*`, and hashing, over str, tuple, bytes, list, and bytearray | yes |
| `Lists.tla` | item and slice assignment and deletion, `+=`, `*=`, and the mutable sequence methods, over list and bytearray | yes |
| `Sets.tla` | set and frozenset operators, comparisons, mutation, hashing, and equal numbers as one element | yes |
| `FrozenDicts.tla` | `frozendict` construction, order, `|` and `|=`, equality with dict, hashing, and the absent mutating methods | yes |
| `FunctionObjects.tla` | function special attributes: read-only ones, type-checked writes, new defaults and code taking effect, and closures | yes |
| `Methods.tla` | method binding (instance, classmethod, staticmethod, instance attribute), method attributes, and built-in functions and methods | yes |
| `Callables.tla` | calling classes (`__new__`, `__init__`, extra arguments) and instances (`__call__` looked up on the type) | yes |
| `ModuleObjects.tla` | module attributes and namespace, read-only `__dict__`, annotations, and attributes of modules made by the module type | yes |
| `ClassObjects.tla` | class special attributes (bases, layout base, MRO, docs not inherited, annotations, type parameters, static attributes), the read-only namespace view, and class versus instance assignment | yes |
| `CodeObjects.tla` | code attributes (names, parameter counts, local, cell, free, and global names, flags, docstring constant), immutability, `co_lines()`, `co_positions()`, and `replace()` | yes |
| `Frames.tla` | frame attributes of running, finished, and generator frames, the writable trace attributes, and `clear()` | yes |
| `Tracebacks.tla` | traceback chains as handlers unwind (through `finally`, re-raise, and `raise from`), line numbers, writable `tb_next`, and made tracebacks | yes |
| `Slices.tla` | slice attributes, `indices()` against CPython's clamping, subscripts, a zero step or bad bound, equality and hashing, and `slice[float]` | yes |
| `MethodDescriptors.tla` | static and class method objects over functions, builtins, and non-callables: retrieval through classes, instances, and subclasses, calling, and attributes | yes |
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

## Coverage of the standard

`coverage.txt` maps every section of `docs/standards/3_15.md` to the models
that cover it, to `= sections` when its own text is a short introduction to
subsections that are covered, or to `- reason` when it states no behavior of
the Core profile (licenses, history, the glossary, and host services such as
module discovery, which the standard's profile clauses place outside Core).
`TODO: models` marks a section whose planned models are not written yet.
`make tla-coverage` (part of `make test-tla`) checks the map against the
standard's headings.

A section mapped to a model means the model formalizes that section's
behavior for the cases its bounds enumerate, and that the oracle and spy
agree with it on every one of them. It does not mean every sentence of the
section is in the model, and it is not a proof about spy.c.

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

The models found these bugs in spy, since fixed: the lexer reported an
error on a later line before a syntax error on an earlier one (CPython's
lexer runs only as far as the parser reads), accepted a backslash
continuation at the end of the source, and bound a name such as `Ｔrue`
(full-width T) that normalizes to `True`, which CPython cannot compile;
f-string format specifications nested more than two deep were accepted,
a t-string interpolation's expression text kept its comments; assigning
a function's `__code__` and reading its `__builtins__` were missing; bound
built-in methods had `__func__` and the wrong `__module__`; a module's
`__dict__` could be replaced and it had no `__annotate__`; a class with
several bases reported the first as `__base__`, not the one with the layout;
code objects lacked `co_names`, `co_consts`, and `replace()`; a generator
made a new frame object for each `gi_frame` read, and a finished one's frame
reported its `def` line; frames lacked `f_lasti`, the trace attributes, and
`clear()`, and a coroutine's frame had no `f_code`; a slice with a bad bound
and a zero step reported the bound, not the step; `classmethod(abs)` bound
to a builtin method instead of a method object.
Earlier, comprehensions reported an
unbound local of their function as a free variable, finalizers queued while
freeing an object ran after objects that were already waiting, and `str`
length, slicing, and `find()` rescanned the whole string on every call
(which made the replays themselves time out). They also found a mistake in a
first draft of `Generators.tla`: CPython raises RuntimeError when throwing
into a finished coroutine, which the oracle replay caught. Oracle replays
likewise corrected `Evaluation.tla` (`*args` in a call are evaluated before
keyword arguments written earlier) and `AsyncGenerators.tla` (after
`aclose()`, `athrow()` and `aclose()` raise StopAsyncIteration without
running the body).
