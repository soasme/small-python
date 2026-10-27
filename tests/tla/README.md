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
| `SpecialLookup.tla` | implicit special method calls look up the type (not the instance, nor `__getattribute__`), metaclass methods apply to classes, and replacing or deleting takes effect | yes |
| `Descriptors.tla` | descriptor invocation for every mix of `__get__`, `__set__`, and `__delete__`: instance, class, super, and direct binding, assignment, deletion, and precedence over the instance dictionary | yes |
| `Slots.tla` | `__slots__` with and without `__dict__`, inherited from plain and slotted bases: `__dict__` and `__weakref__`, assignment, unset slots, class variable conflicts, and `__class__` assignment | yes |
| `BasicCustomization.tla` | rich comparison order (a subclass's reflected method first), `NotImplemented` and the identity fallback, `__ne__` inverting `__eq__`, `__hash__` with and without `__eq__`, truth from `__bool__` or `__len__`, and `str()`, `repr()`, and `format(x, "")` falling back to `__repr__` | yes |
| `Metaclasses.tla` | `__mro_entries__` and `__orig_bases__`, the most derived metaclass among the explicit one and the bases', metaclass conflicts, a non-class metaclass, and the `__classcell__` that `type.__new__` fills | yes |
| `InstanceChecks.tla` | `__instancecheck__` and `__subclasscheck__` on a metaclass (and ignored on the class), bool conversion, the exact-type shortcut, tuples of classes, and a bad second argument | yes |
| `ClassGetitem.tla` | `__class_getitem__` (plain or a classmethod) against a metaclass's and an instance's `__getitem__`, unsubscriptable classes, and builtin generic aliases | yes |
| `Containers.tla` | `in` through `__contains__`, `__iter__`, or `__getitem__`; iteration and `__iter__ = None`; `reversed()` through `__reversed__` or `__len__` and `__getitem__`; `__missing__`; and storing without `__setitem__` | yes |
| `NumericProtocol.tla` | binary operator dispatch with reflected methods (a subclass's override first), `NotImplemented`, in-place fallback, and `__index__` against `__int__` | yes |
| `With.tla` | `__enter__` and `__exit__` lookup, a raising `__enter__`, `__exit__` arguments and suppression after a normal end, an exception, or a return, an exception from `__exit__`, and nested managers | yes |
| `Buffers.tla` | `__buffer__` exporters through `memoryview()` and `bytes()`, `__release_buffer__` on release, `with`, and destruction, a non-memoryview result, and resizing an exported bytearray | yes |
| `Annotations.tla` | lazy evaluation of function, class, and local annotations, `__annotate__` formats, unbound and string annotations, annotation scopes, evaluation at most once, and replacing `__annotations__` and `__annotate__` | yes |
| `Generics.tla` | type parameter kinds, bounds, constraints, defaults, and variance; lazy evaluation; visibility through annotation scopes; parameter list syntax errors; and generic classes | yes |
| `TypeAliases.tla` | the `type` statement: lazy, single evaluation of `__value__` (forward and self references), alias attributes, subscription, and read-only attributes | yes |
| `Awaitables.tla` | `await` on coroutines, `__await__` iterators and generators, and non-awaitables; reusing an awaited coroutine; and coroutine `send`, `close`, and `throw` | yes |
| `AsyncFor.tla` | `async for` over async generators and `__aiter__`/`__anext__` classes with `else`, `break`, and exceptions; protocol errors; asynchronous comprehensions; and async constructs outside async functions | yes |
| `AsyncWith.tla` | `async with`: awaited `__aenter__` and `__aexit__`, suppression, raising methods, and protocol errors with their hints | yes |
| `ScopeErrors.tla` | `global` and `nonlocal` after a use, assignment, annotation, or parameter, annotated declared names, both declarations, module and class placement, and missing bindings, with their lines | yes |
| `BuiltinsScope.tla` | builtins lookup through `__builtins__` as a module or a dictionary, shadowing globals, an extended builtins module, restricted `__import__`, and `__builtins__` insertion | yes |
| `DynamicScopes.tla` | `exec()` and `eval()` with default and given namespaces, free variables, `locals()` snapshots, `f_locals` write-through, and class-body `eval()` | yes |
| `Raise.tla` | `raise` with classes, instances, non-exceptions, and bare re-raise, `from` causes and `None`, and implicit `__context__` for raised and failing operations in handlers | yes |
| `CompileModes.tla` | `compile()` in exec, eval, and single modes: what each accepts, its result, values passed to `sys.displayhook`, and bad modes | yes |
| `Imports.tla` | the import system over fixture packages (`Imports.files`): submodules and parents, run-once caching, `sys.modules` entries that are None or replaced, failed and circular imports, regular and namespace packages, module attributes, relative imports, `from ... import *`, and import errors | yes |
| `LazyImports.tla` | lazy imports (PEP 810): placeholders, reification on first use, lazy submodules in `sys.lazy_modules`, where `lazy` is allowed, and `__lazy_modules__` | yes |
| `Future.tla` | future statements: placement, known and historical features, stringized annotations, inheritance by `exec()` and `compile()`, and relative imports of `__future__` | yes |
| `Displays.tla` | list, tuple, set, and dict displays of plain, starred, and double-starred items: evaluation order, first-kept equal elements and keys, last-kept values, and failing items; parenthesized forms and display syntax errors | yes |
| `Comprehensions.tla` | comprehensions and generator expressions of up to three for and if clauses with plain and unpacking elements (PEP 798): nesting, filtering, evaluation order, the eager first iterable, scoping, assignment expressions, and syntax errors | yes |
| `Truth.tla` | truth testing of instances with every kind of `__bool__` and `__len__` (including bad results and `None`), `bool()` of built-in values, and `not`, `and`, and `or` with short-circuiting | yes |
| `Comparisons.tla` | rich comparison dispatch for every operator over classes with all, no, declining, or only `__eq__` methods, unrelated or subclassed (reflected first); chains, identity, built-in sequence, mapping, set, and numeric comparisons, and membership through `__contains__`, iteration, and `__getitem__` | yes |
| `BinaryArith.tla` | binary and augmented operator dispatch over classes with forward, reflected, declining, or in-place methods, unrelated, subclassed (overriding reflected first), or the same; numeric widening, division, modulo, power, unary operators, three-argument `pow()`, and the errors of unsupported operands | yes |
| `Subscripts.tla` | getting, setting, and deleting items with single, comma-separated, starred, and slice subscripts, evaluation order, and the errors and indexing rules of built-in sequences and mappings | yes |
| `SimpleStatements.tla` | chained and unpacking assignments to names, attributes, and items, augmented assignment, and del, with their evaluation order; assignment, annotation, assert, del, and pass cases and the targets the grammar rejects | yes |
| `Conditionals.tla` | if/elif/else chains of every outcome and while loops with break, continue, and else, with the conditions each evaluates; break and continue placement, walrus conditions, and conditional expressions | yes |
| `MatchGuards.tla` | match statements of up to two guarded or unguarded case blocks over literal, capture, value, and group patterns: evaluation order, bindings left by failed guards, and unreachable irrefutable cases | yes |
| `FunctionDefs.tla` | the evaluation order of decorators, defaults, bases, and bodies for every def, lambda, and class of up to three decorators and two defaults or bases; parameter list rules, docstrings and names, lambdas, and assignment expressions | yes |
| `Precedence.tla` | the grouping of every pair of binary arithmetic and bitwise operators and of each unary operator on either side of one, over symbolic operands; boolean operators, comparisons, conditional expressions, lambda, await, and primaries | yes |
| `Sentinels.tla` | `sentinel()` construction and its argument errors, representation, identity and equality, attributes, copying, pickling reduction, `\|` in type expressions, and the type's restrictions | yes |
| `Atoms.tla` | the keyword constants and why they cannot be targets, name evaluation, the type of each kind of literal, negative and complex numbers as operations, literal immutability, and which identities of literals are guaranteed | yes |
| `Grammar.tla` | every compound statement with every form of suite (one-line, semicolon-separated, indented, nested, missing, misindented), and the acceptance or rejection, with its message, of the full grammar's productions | yes |
| `NumberMethods.tla` | `bit_length`, `bit_count`, `to_bytes`, and `from_bytes` computed over boundary integers, every length up to three bytes, byte order, and signedness; the float and complex methods `from_number`, `as_integer_ratio`, `is_integer`, `hex`, and `fromhex` | yes |
| `NumericHash.tla` | the hash of m * 2^e as an int and as a float, positive and negative, from subnormal exponents past the modulus period, in the rotated form the prime 2^61 - 1 gives it; infinities, NaNs, the modulus itself, complex numbers, and equal numbers of different types | yes |
| `Iterators.tla` | every built-in iterator kind over up to two items: `iter()` of an iterator is itself, items in order, StopIteration that stays raised even after the source grows; the protocol's errors, the sequence protocol, `iter(callable, sentinel)`, `next()` defaults, and size changes during iteration | yes |
| `Ranges.tla` | the items, length, ends, reversal, tail slice, membership, and index of every range over small bounds and steps from -2 to 2, derived from r[i] = start + step * i; construction errors, equality and hashing by sequence, huge ranges, and unsupported operations | yes |
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
to a builtin method instead of a method object; `-C` ignored a metaclass's
`__neg__` (and likewise `abs()`, `format()`, item assignment, `divmod()`,
`next()`, and a metaclass's `__getattribute__` and `__getattr__`); a data
descriptor without `__get__` hid a value in the instance dictionary;
`__class__` could not be assigned on a slotted instance, nor between classes
with the same slots; a `__str__`, `__bool__`, `__format__`, `__bytes__`, or
`__init__` returning the wrong type was reported without naming the class,
the method, or the returned type; a metaclass that dropped
`__classcell__` left `__class__` bound instead of raising RuntimeError;
a `__buffer__` exporter's `__release_buffer__` was never called; setting
`__annotations__` kept the old `__annotate__`, and `__annotate__` could be
set to a non-callable or deleted; `TypeVarTuple` lacked `__bound__` and the
variance attributes, type parameters from `*Ts` did not infer variance,
`ParamSpec` had an `evaluate_bound` that CPython 3.15 no longer has;
`async for`, `aiter()`, `with`, and `async with` reported protocol errors
with older messages and no hints; an annotated name could be declared
global or nonlocal, and global with nonlocal was reported at the second
declaration; an error raised by an operation (rather than a raise
statement) in an except handler, a finally block, or `__exit__` lost its
`__context__` once it left the handler; interactive input printed values
itself instead of calling `sys.displayhook`; a None in `sys.modules` was
imported as the module instead of halting the import, and a namespace
package had no `__file__`; `lazy import a.b` imported `a.b` when `a`
was first used (rather than when `a.b` was looked up), and
`__lazy_modules__` was ignored; a relative import from globals without
`__name__` raised ImportError instead of KeyError, with other messages for
a non-string `__name__` or `__package__`; a `**` mapping whose `keys()`
returned a non-iterable was reported with the module of a class defined in
`__main__` or `builtins`; `len()` and truth testing rejected a `__len__`
result with `__index__` and reported other results with other messages;
a `__bool__` or `__contains__` of None was called; `in` with a string
or bytes reported a wrong left operand with other messages; an
unsupported operator on numbers raised spy's own messages, an augmented
assignment's error named the plain operator, `*` named its operands in
swapped order, three-argument `pow()` reported every unsupported case as
needing integers, and `(1+1j) ** 1000000` returned an infinity; an
index too large for a Py_ssize_t was reported as out of range, and
deleting an item from a type without `__delitem__` was worded without
regard to whether the type has sequence methods and the key is an index;
a global deleted in `exec()`'s namespace read as an unbound local,
`sentinel()` refused `repr=` and a new `__module__`, and
`int.from_bytes()`, `bytes()`, and `bytearray()` misreported objects they
cannot convert, and iteration misreported an `__iter__` of None or one
returning a non-iterator, and `range` attributes were writable in message,
`range.index()` worded its miss differently, and `len()` of a huge range
reported a 64-bit limit.
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
