# SLP-315: Python 3.15 Core Language Specification

**Edition:** 2026, revision 2  
**Document identifier:** `SLP-315:2026-draft2`  
**Language baseline:** Python 3.15.0  
**Status:** Project language standard, draft  
**Unicode baseline:** Unicode 17.0.0

This Standard defines the Python 3.15 core language: its source text, grammar,
values, objects, and the semantics of evaluating programs. It is written in the
manner of ECMA-262: the language is described by grammars, by algorithms over
specification values, and by the built-in objects every conforming
implementation provides. No part of this Standard depends on a library module.
The objects that CPython exposes through modules such as `types`, `typing`,
`annotationlib`, or `string.templatelib` are defined here as *intrinsic objects*
of the language. A host may additionally publish them under those module names;
Annex C describes that facade, which is informative.

This is a **project standard** of Small Python. It is not issued or endorsed by
the Python Software Foundation or by Ecma International.

## Contents

1. Scope
2. Conformance
3. Normative References
4. Overview
5. Notational Conventions
6. Python Data Types and Values
7. Abstract Operations
8. Static Semantics of Scopes
9. Executable Code and Execution Contexts
10. Object Behaviours
11. Source Text
12. Lexical Grammar
13. Expressions
14. Simple Statements
15. Compound Statements
16. Functions and Classes
17. Modules and Imports
18. Error Handling
19. The Built-in Namespace
20. Fundamental Objects
21. Exception Objects
22. Numbers
23. Text Processing
24. Binary Data
25. Sequences
26. Mappings and Sets
27. Control Abstraction Objects
28. Reflection Objects
29. Typing Objects

Annexes: A Grammar Summary,
B Host Hooks,
C Library Facades,
D Implementation-Defined Behaviour,
E Changes from Revision 1,
Bibliography.

## 1 Scope

This Standard defines the Python 3.15 core language. It specifies:

- the representation of source text and its decomposition into tokens;
- the syntactic grammar of modules, statements, and expressions;
- the static semantics that classify names and reject invalid programs before
  they run;
- the runtime semantics of every construct of the grammar;
- the object model: identity, types, attribute access, special methods,
  descriptors, metaclasses, and the protocols that connect them;
- the built-in namespace and the intrinsic objects that the language
  constructs produce or that the built-in functions return.

This Standard does not define a standard library. Facilities that need an
operating system — files, processes, clocks, sockets, threads, environment
variables — and modules that a CPython installation provides are outside its
scope, except where Annex B defines the *host hook* through which a language
construct reaches such a facility.

## 2 Conformance

### 2.1 Profiles

A conforming implementation of the **Core** profile shall provide and support
every grammar production, every static and runtime semantic rule, and every
built-in and intrinsic object defined in this Standard, with the behaviour
specified for it.

A conforming implementation of the **Host** profile is a Core implementation
that additionally supplies one or more of the host hooks of Annex B. It shall
document which hooks it supplies. A hook that is not supplied behaves as
Annex B specifies for its absence; an absent hook never makes valid source text
a syntax error.

The **Extension** profile, compatibility with the CPython C API and ABI, is not
defined by this Standard. Core conformance does not imply it.

### 2.2 Requirements

A conforming implementation:

1. shall interpret source text as Unicode code points in accordance with the
   Unicode Standard, version 17.0.0 or later, and identifiers in accordance with
   Unicode Standard Annex #31 as profiled in clause 12.4;
2. shall represent `float` values as IEEE 754-2019 binary64 values and `int`
   values as integers of unbounded magnitude, limited only by available storage;
3. shall preserve, for every construct, the order of evaluation, the number and
   order of calls to user-defined code, the binding of names, the identity of
   objects where this Standard specifies it, and the exceptions raised;
4. shall raise the exception this Standard specifies, of the specified class, and
   with the specified message where an algorithm gives one (5.2.6);
5. shall report exhaustion of a resource — storage, recursion depth, the length
   of a value — by raising the exception specified for it, and never by
   undefined behaviour of the implementation language.

An implementation may provide types, values, objects, functions, and syntax
beyond those described here, except where clause 18.4 forbids an extension.
An implementation-defined facility is one whose behaviour this Standard leaves
to the implementation, which shall document it; Annex D lists them. An
implementation-approximated facility (for example, the timing of finalization)
may differ between runs of the same program.

### 2.3 Normative language

In this Standard, **shall** and **must** express requirements; **may** expresses
permission; **should** expresses a recommendation. Notes and examples are
informative; algorithm steps, grammar, and the text of clauses are normative.

### 2.4 Conformance evidence

A release that claims conformance shall name this document's identifier and
list every known deviation. Small Python checks this Standard against the
implementation with executable TLA+ models (`tests/tla`), each of which names
the clauses it formalizes and is replayed against both a reference oracle and
the implementation; `tests/tla/coverage.txt` maps every clause to its models or
records why no model applies.

## 3 Normative References

The following documents are indispensable for the application of this Standard.

- *The Unicode Standard*, version 17.0.0, including Unicode Standard Annex #15
  (Normalization Forms), Annex #31 (Identifiers and Syntax), and the Unicode
  Character Database.
- IEEE 754-2019, *Standard for Floating-Point Arithmetic*.
- ISO/IEC 10646, *Universal Coded Character Set (UCS)*.
- RFC 3629, *UTF-8, a transformation format of ISO 10646*.

## 4 Overview

### 4.1 Python overview

Python is a dynamically typed, object-oriented language. Every value is an
*object*. Every object has an identity, which never changes during its
lifetime; a *type*, which is itself an object and determines the operations the
object supports; and a value, which may or may not change depending on its type.
Operations on objects — arithmetic, comparison, attribute access, calling,
iteration — are defined by *special methods* looked up on the object's type.

A program is a collection of *modules*. A module's source text is parsed into a
sequence of statements and evaluated in a fresh *namespace*, the module's
globals. Statements bind names in namespaces; functions and classes create new
scopes whose names are resolved lexically (clause 8). Functions are
first-class objects with closures. Generators and coroutines are functions
whose execution can be suspended and resumed. Exceptions transfer control to
the nearest enclosing handler and carry a traceback.

### 4.2 Organization of this Standard

Clauses 5 through 10 define the notation, the specification types, the abstract
operations that the rest of the Standard is written with, the static semantics
of scopes, execution contexts, and the behaviour of objects in general.

Clauses 11 through 18 define the language proper: source text, tokens,
expressions, statements, function and class definitions, modules and imports,
and error handling.

Clauses 19 through 29 define the built-in namespace and the built-in and
intrinsic objects.

### 4.3 Terms and definitions

**object**: a value of the language; an entity with an identity, a type, and a
value.

**type**, **class**: an object that is an instance of `type`. The type of an
object *o* is written Type(*o*) (7.1.1). "Class" and "type" are synonyms.

**instance**: *o* is an instance of class *C* when IsSubclass(Type(*o*), *C*) is
**true**, ignoring `__instancecheck__` unless the text says otherwise.

**special method**: a method whose name begins and ends with two underscores and
that an operation of the language looks up on the type of an operand (7.3.2).

**namespace**: a mapping from names to objects. Module namespaces and instance
namespaces are `dict` objects.

**intrinsic object**: a built-in object that this Standard requires and that a
program reaches through a language construct or a built-in function, whether or
not it is bound to a name in the built-in namespace. Intrinsics are written
%Name%, for example %FunctionType% or %Template%.

**user code**: code that is not part of the implementation: functions and
methods defined in Python source, and any object whose special methods are such
functions.

**host**: the environment that runs the implementation and supplies the hooks
of Annex B.

## 5 Notational Conventions

### 5.1 Syntactic and lexical grammars

#### 5.1.1 Grammar notation

The lexical grammar (clause 12) has Unicode code points as its terminal symbols
and produces tokens. The syntactic grammar (clauses 13 through 17 and Annex A)
has tokens as its terminal symbols. Both are written as rules of the form

```text
name: alternative_1 | alternative_2 | ...
```

where each alternative is a sequence of items. The items are:

| Notation | Meaning |
| --- | --- |
| `name` | the rule *name* |
| `NAME`, `NUMBER`, `STRING`, `NEWLINE`, `INDENT`, `DEDENT`, `ENDMARKER` | a token of that kind (12.1) |
| `'kw'` | the keyword or operator token spelled *kw* |
| `"kw"` | the soft keyword *kw*: a `NAME` token spelled *kw*, which remains an ordinary name elsewhere (12.4.2) |
| `e1 e2` | *e1* followed by *e2* |
| `e1 \| e2` | ordered choice: *e2* is tried only if *e1* fails |
| `( e )` | grouping |
| `[ e ]`, `e?` | optional |
| `e*`, `e+` | zero or more, one or more repetitions, matched greedily |
| `s.e+` | one or more *e* separated by *s*; same as `e (s e)*` |
| `&e`, `!e` | positive and negative lookahead: succeed if *e* would (would not) match, consuming nothing |
| `~` | commit: if the remaining items of this alternative fail, the rule fails without trying later alternatives |
| `"a"..."z"` | (lexical grammar) any code point from *a* through *z* inclusive |

The syntactic grammar is a parsing expression grammar: a rule matches the
longest input its first succeeding alternative matches, and its alternatives are
not ambiguous. A source text is syntactically valid only if the start rule
(17.6) matches all of its tokens.

#### 5.1.2 Static semantic rules

Some programs that the grammar accepts are invalid. *Early error* rules
(clause 18.2), given with each construct under the heading **Static Semantics:
Early Errors**, state the conditions under which a program shall be rejected
with a `SyntaxError` before any of it is evaluated.

### 5.2 Algorithm conventions

#### 5.2.1 Algorithm steps

The semantics are given as algorithms of numbered steps. Steps run in order.
Sub-steps are indented. A step may name a value with "Let *x* be …", change it
with "Set *x* to …", branch with "If … , then", and loop with "Repeat" or "For
each". Variables are italicized and local to the algorithm that introduces them.

#### 5.2.2 Abstract operations

An *abstract operation* is a named algorithm with parameters, such as
GetAttribute(*obj*, *name*). Abstract operations are not visible to programs.
An algorithm *invokes* an abstract operation by writing its name and arguments.

A *syntax-directed operation* is an abstract operation defined separately for
productions of the grammar. Evaluation of a production, written "the result of
evaluating *Expression*", is the syntax-directed operation **Evaluation**.

#### 5.2.3 Completion records and shorthands

Every abstract operation returns a *Completion Record* (6.2.3): either a
**normal completion** carrying a value, or an **abrupt completion** of type
**raise**, **return**, **break**, or **continue**. An abrupt completion of type
raise carries an exception object.

- "Return *v*" returns a normal completion whose value is *v*.
- "Raise a *C* exception" creates an instance of the exception class *C*, as if
  by calling *C* with no arguments, and returns a raise completion carrying it.
  "Raise a *C* exception ("*text*")" calls *C* with the string *text* as the
  only argument; 5.2.6 governs the text.
- `? Op(args)` means: let *r* be Op(*args*); if *r* is an abrupt completion,
  return *r* from the current algorithm; otherwise use the value of *r*.
- `! Op(args)` asserts that Op(*args*) cannot return an abrupt completion and
  means its value.
- An algorithm step that returns a value without "?" or "!" from an operation
  that may complete abruptly propagates that completion unchanged.

When an algorithm returns a raise completion carrying an exception *e* while
an execution context is running user code, the exception propagates as clause
18.1 specifies: tracebacks are extended and handlers searched.

#### 5.2.4 Calls to user code

"Call *f* with *args*" means ? Call(*f*, *args*) (7.4.1). "Call the special
method *name* of *o* with *args*" means:

1. Let *m* be ? LookupSpecial(*o*, *name*).
2. If *m* is **absent**, the step that used the phrase states what happens.
3. Return ? Call(*m*, *args*).

Wherever this Standard says that an operation calls user code, the order of
those calls and their arguments are observable and normative.

#### 5.2.5 Mathematical values

Algorithms compute with *mathematical values*: exact integers and real numbers
of unbounded size and precision, written in a sans-serif or plain style (`3`,
`0.5`). The mathematical value of an `int` object *i* is ℝ(*i*); of a `float`
object it is the exact real value it represents. Converting a mathematical
value *x* to a `float` rounds it to the nearest binary64 value, ties to even
(IEEE 754 roundTiesToEven), and raises an `OverflowError` exception if the result
would be infinite while *x* is finite, unless the algorithm says otherwise.
floor(*x*) is the greatest integer not greater than *x*; *x* modulo *y* is the
value *r* with the sign of *y* such that *x* − *r* is an integer multiple of *y*.

#### 5.2.6 Exception messages

Where an algorithm raises an exception with a parenthesized *text*, that text is
the exception's message: `str(e)` of the exception *e* is *text*. Within *text*,
an italicized name stands for a value substituted as follows:

- "*tname*(*o*)" is the `__name__` of Type(*o*);
- "*fqname*(*T*)" is the fully qualified name of a type *T*: its
  `__qualname__` if its `__module__` is not a `str` or is `"builtins"` or
  `"__main__"`, and otherwise its `__module__`, `"."`, and its `__qualname__`;
  "*fqname*(*o*)" for an object that is not a type means *fqname*(Type(*o*));
- *repr*(*o*) is the result of ToRepr(*o*) (7.5.6);
- other names are the string form of the named value.

The message texts are normative in the Core profile, so that programs that
inspect `str(e)` behave identically on every conforming implementation. An
implementation may append additional text to a message only where the
algorithm says "*text*, or a message beginning with *text*".

#### 5.2.7 Value notation

`None`, `True`, `False`, `NotImplemented`, and `Ellipsis` denote the unique
objects of those names (20.4). **true** and **false** are the specification
Boolean values (6.2.1), not the `bool` objects. **absent** is a specification
value that marks a missing optional argument or the failure of a lookup; it is
never a Python object. A string literal in an algorithm, such as `"__init__"`,
denotes a `str` object with that value.

## 6 Python Data Types and Values

### 6.1 Python language values

#### 6.1.1 Objects

Every value a program manipulates is an object. An object has:

- an **identity**, which is distinct from the identity of every other object
  that exists at the same time and which does not change during the object's
  lifetime. The `is` operator (13.10.4) compares identities; `id` (19.3)
  returns an integer that identifies the object among the objects that exist at
  the same time;
- a **type**, Type(*o*), which is a type object (clause 20.2). The type of an
  object determines its operations. Assigning `__class__` (20.1.4) may change
  the type of an object of a mutable class;
- a **value**. An object whose value can change is *mutable*; otherwise it is
  *immutable*. The immutability of a container refers to the identities of the
  objects it contains, not to their values.

Objects are never explicitly destroyed. An object that a program can no longer
reach may be reclaimed (9.7). An implementation shall not reclaim an object that
is reachable from a root: the running execution contexts and their suspended
callers, the module cache, the built-in namespace, the intrinsics, and any
object the host holds.

#### 6.1.2 Immutable value types and identity

For values of the immutable types `int`, `float`, `complex`, `bool`, `str`,
`bytes`, `tuple`, `frozenset`, `range`, and `NoneType`, an operation that
produces a value may return an existing object equal to the value it would
otherwise create. Whether two such values computed separately are the same
object is implementation-defined, except that `None`, `True`, `False`,
`NotImplemented`, and `Ellipsis` are unique objects and that the empty tuple
returned by `tuple()` is a single object. Programs shall not rely on any other
identity of immutable values.

#### 6.1.3 The standard type hierarchy

The built-in types are organized as follows. Each is specified in the clause
named.

| Category | Types | Clause |
| --- | --- | --- |
| Singletons | `NoneType`, `NotImplementedType`, `ellipsis` | 20.4 |
| Numbers | `int`, `bool`, `float`, `complex` | 22 |
| Text | `str`, `%Template%`, `%Interpolation%` | 23 |
| Binary data | `bytes`, `bytearray`, `memoryview` | 24 |
| Sequences | `list`, `tuple`, `range`, `slice` | 25 |
| Mappings and sets | `dict`, `frozendict`, `set`, `frozenset`, `%MappingProxyType%`, dictionary views | 26 |
| Callables | functions, methods, built-in functions, classes, instances with `__call__` | 16, 28 |
| Control abstraction | generators, coroutines, asynchronous generators, built-in iterators | 27 |
| Modules | `%ModuleType%` | 17.2 |
| Classes and instances | `type`, `object`, `super`, `property`, `staticmethod`, `classmethod` | 20 |
| Exceptions | `BaseException` and its subclasses | 21 |
| Internal objects | code, frame, traceback, cell, and descriptor objects | 28 |
| Typing objects | `%GenericAlias%`, `%UnionType%`, `%TypeVar%`, `%ParamSpec%`, `%TypeVarTuple%`, `%TypeAliasType%` | 29 |

### 6.2 Specification types

Specification types are used only in algorithms. Their values are never Python
objects.

#### 6.2.1 Boolean

The specification Boolean type has the two values **true** and **false**.

#### 6.2.2 List and Record

A List is a finite ordered sequence of values. «*a*, *b*» denotes a List.
A Record is an aggregate of named fields, written { [[Field]]: *value*, … }.

#### 6.2.3 Completion Record

A Completion Record describes the outcome of evaluating a construct or running
an abstract operation.

| Field | Values | Meaning |
| --- | --- | --- |
| [[Type]] | **normal**, **raise**, **return**, **break**, **continue** | how control leaves the construct |
| [[Value]] | an object, **empty** | the result, the returned object, or the raised exception |

NormalCompletion(*v*) is { [[Type]]: **normal**, [[Value]]: *v* }. A completion
whose [[Type]] is not **normal** is *abrupt*. **break** and **continue**
completions never cross a function boundary; Static Semantics (14.10, 14.11)
reject programs in which they would.

#### 6.2.4 Argument List

An Argument List is a Record { [[Positional]]: a List of objects,
[[Keywords]]: a List of (name, object) pairs }, in which the names are `str`
objects and are pairwise distinct. Call sites build Argument Lists
(13.3.4); callees bind them to parameters (7.4.3).

#### 6.2.5 Signature

A Signature describes the parameters of a function.

| Field | Value |
| --- | --- |
| [[PositionalOnly]] | a List of parameter names |
| [[PositionalOrKeyword]] | a List of parameter names |
| [[VarPositional]] | a name, or **absent** |
| [[KeywordOnly]] | a List of parameter names |
| [[VarKeyword]] | a name, or **absent** |
| [[Defaults]] | a List of objects, the defaults of the last positional parameters |
| [[KwDefaults]] | a mapping from keyword-only names to default objects |

#### 6.2.6 Scope Record

A Scope Record is the result of the static analysis of clause 8 for one
function body, class body, module, lambda, comprehension, annotation scope, or
type parameter scope. It has fields [[Kind]], [[Parent]], [[Symbols]] (a mapping
from each name used in the scope to a classification: **local**, **global
explicit**, **global implicit**, **free**, or **cell**), and the flags
[[IsGenerator]], [[IsCoroutine]], and [[NeedsClassCell]].

#### 6.2.7 Code Record

A Code Record is the static description of one executable unit: its Scope
Record, its Signature, its body (a parse tree), its name and qualified name, the
file name and first line number, and its flags. A code object (28.2) wraps a
Code Record.

#### 6.2.8 Frame Record

A Frame Record (9.2) is the dynamic state of one execution of a Code Record:
the code, the globals, the builtins, the local bindings, the cells, the current
position, the exception being handled, and the suspension state.

## 7 Abstract Operations

### 7.1 Type operations

#### 7.1.1 Type ( *o* )

Type(*o*) is the type of the object *o* (6.1.1). It is the object that
`type(o)` (20.2.2) returns and that `o.__class__` returns unless the class of
*o* overrides `__class__`.

#### 7.1.2 IsSubclass ( *A*, *B* )

The abstract operation IsSubclass takes types *A* and *B* and returns **true**
if *B* is an element of *A*.`__mro__` (7.1.4) and **false** otherwise. It
calls no user code. The built-in function `issubclass` (19.3) additionally
consults `__subclasscheck__`.

#### 7.1.3 IsInstance ( *o*, *C* )

IsInstance(*o*, *C*) is IsSubclass(Type(*o*), *C*), or, if that is **false**,
IsSubclass(*cls*, *C*) where *cls* is the result of ? GetAttribute(*o*,
`"__class__"`) when that result is a type. It calls no `__instancecheck__`.

#### 7.1.4 ComputeMRO ( *C* )

The method resolution order of a class *C* with bases *B*₁, …, *B*ₙ is the C3
linearization of *C*. The abstract operation ComputeMRO takes a class *C* and
returns a List of classes or a raise completion.

1. If *C* has no bases (only `object` has none), return «*C*».
2. Let *seqs* be the List «L(*B*₁), …, L(*B*ₙ), «*B*₁, …, *B*ₙ»», where L(*B*)
   is the List *B*.`__mro__`.
3. Let *result* be «*C*».
4. Repeat:
   1. Remove every empty List from *seqs*. If *seqs* is empty, return *result*.
   2. Let *head* be **absent**. For each *s* in *seqs*, in order: if the first
      element *h* of *s* is not an element of the tail (all but the first
      element) of any List in *seqs*, set *head* to *h* and stop.
   3. If *head* is **absent**, raise a `TypeError` exception ("Cannot create a
      consistent method resolution order (MRO) for bases *names*"), where
      *names* joins the `__name__` of each *B*ᵢ, in order, with `", "`.
   4. Append *head* to *result*, and remove *head* from the front of every List
      in *seqs* that begins with it.

If two bases are the same class, ComputeMRO is not reached: class creation
raises a `TypeError` exception ("duplicate base class *name*").

A metaclass may override the method `mro` (20.2.6); class creation calls
`type(C).mro(C)` and stores the result, converted to a tuple, as
`C.__mro__`. The `__mro__` of a class does not change unless its `__bases__`
are assigned.

### 7.2 Testing and comparison operations

#### 7.2.1 IsCallable ( *o* )

IsCallable(*o*) returns **true** if LookupInMRO(Type(*o*), `"__call__"`)
(7.3.1) is not **absent**, and **false** otherwise.

#### 7.2.2 SameObject ( *a*, *b* )

SameObject(*a*, *b*) returns **true** if *a* and *b* are the same object and
**false** otherwise.

#### 7.2.3 ReflectedComparison ( *op* )

| *op* | `<` | `<=` | `==` | `!=` | `>` | `>=` |
| --- | --- | --- | --- | --- | --- | --- |
| method | `__lt__` | `__le__` | `__eq__` | `__ne__` | `__gt__` | `__ge__` |
| reflected | `__gt__` | `__ge__` | `__eq__` | `__ne__` | `__lt__` | `__le__` |

#### 7.2.4 RichCompare ( *v*, *w*, *op* )

The abstract operation RichCompare takes objects *v* and *w* and a comparison
operator *op* and returns an object or a raise completion.

1. Let *m* be the method name of *op* and *r* its reflected name (7.2.3).
2. Let *checkedReflected* be **false**.
3. If Type(*v*) is not Type(*w*) and IsSubclass(Type(*w*), Type(*v*)) is
   **true**, then
   1. Set *checkedReflected* to **true**.
   2. Let *res* be ? CallSpecial(*w*, *r*, «*v*»).
   3. If *res* is not `NotImplemented`, return *res*.
4. Let *res* be ? CallSpecial(*v*, *m*, «*w*»).
5. If *res* is not `NotImplemented`, return *res*.
6. If *checkedReflected* is **false**, then
   1. Let *res* be ? CallSpecial(*w*, *r*, «*v*»).
   2. If *res* is not `NotImplemented`, return *res*.
7. If *op* is `==`, return `True` if SameObject(*v*, *w*) and `False` otherwise.
8. If *op* is `!=`, return `False` if SameObject(*v*, *w*) and `True` otherwise.
9. Raise a `TypeError` exception ("'*op*' not supported between instances of
   '*tname*(*v*)' and '*tname*(*w*)'").

CallSpecial(*x*, *name*, *args*) is defined in 7.3.3; it returns
`NotImplemented` when *x* has no method *name*. Every type inherits
`__eq__`, `__ne__`, `__lt__`, `__le__`, `__gt__`, and `__ge__` from `object`
(20.1.3), so step 6 also runs when *v* and *w* have the same type.

#### 7.2.5 RichCompareBool ( *v*, *w*, *op* )

1. If *op* is `==` and SameObject(*v*, *w*) is **true**, return **true**.
2. If *op* is `!=` and SameObject(*v*, *w*) is **true**, return **false**.
3. Return ? ToBoolean(? RichCompare(*v*, *w*, *op*)).

Steps 1 and 2 make containers treat an object as equal to itself even when its
`__eq__` says otherwise (for example a NaN). Membership tests, `index`, `count`,
`remove`, container equality, and dictionary key lookup use RichCompareBool;
the `==` operator uses RichCompare.

### 7.3 Attribute and special method operations

#### 7.3.1 LookupInMRO ( *T*, *name* )

The abstract operation LookupInMRO takes a type *T* and a string *name*. For
each class *B* in *T*.`__mro__`, in order: if the namespace of *B* (its
`__dict__`) has the key *name*, return the value bound to it. If none has, return
**absent**. LookupInMRO calls no user code; the class namespaces are read
directly.

#### 7.3.2 LookupSpecial ( *o*, *name* )

Special methods are looked up on the type of an object, never on the object
itself.

1. Let *T* be Type(*o*).
2. Let *f* be LookupInMRO(*T*, *name*).
3. If *f* is **absent**, return **absent**.
4. If *f* is a function object (16.2), return a bound method (28.4) of *f* and
   *o*.
5. Let *get* be LookupInMRO(Type(*f*), `"__get__"`).
6. If *get* is **absent**, return *f*.
7. Return ? Call(*get*, «*f*, *o*, *T*»).

An instance attribute with the name of a special method, and a
`__getattribute__` method, have no effect on LookupSpecial.

#### 7.3.3 CallSpecial ( *o*, *name*, *args* )

1. Let *m* be ? LookupSpecial(*o*, *name*).
2. If *m* is **absent**, return `NotImplemented`.
3. Return ? Call(*m*, *args*).

A special method bound to `None` in a class namespace is found by LookupSpecial
and called, so the call raises a `TypeError` exception ("'NoneType' object is
not callable"), except where a clause says that a `None` value means the
operation is unsupported: `__hash__` (7.5.7), `__iter__` (7.7.1),
`__contains__` (7.8.3), `__bool__` (7.5.1), `__reversed__` (19.3), and the
`__class_getitem__` of a class (7.8.1).

#### 7.3.4 GetAttribute ( *o*, *name* )

The abstract operation GetAttribute implements `o.name` and `getattr(o, name)`.

1. If Type(*name*) is not a subclass of `str`, raise a `TypeError` exception
   ("attribute name must be string, not '*tname*(*name*)'").
2. Let *ga* be LookupSpecial(*o*, `"__getattribute__"`). (Every type inherits
   one from `object`.)
3. Let *result* be Call(*ga*, «*name*»).
4. If *result* is a raise completion whose exception is an instance of
   `AttributeError`, then
   1. Let *getattr* be ? LookupSpecial(*o*, `"__getattr__"`).
   2. If *getattr* is not **absent**, return ? Call(*getattr*, «*name*»).
5. Return *result*.

#### 7.3.5 GenericGetAttr ( *o*, *name* )

GenericGetAttr is the behaviour of `object.__getattribute__`.

1. Let *T* be Type(*o*).
2. Let *descr* be LookupInMRO(*T*, *name*).
3. Let *get* be **absent**.
4. If *descr* is not **absent**, then
   1. Set *get* to LookupInMRO(Type(*descr*), `"__get__"`).
   2. If *get* is not **absent** and IsDataDescriptor(*descr*) is **true**,
      return ? Call(*get*, «*descr*, *o*, *T*»).
5. If *o* has an instance namespace *d* (20.1.2) and *d* has the key *name*,
   return the value bound to *name* in *d*.
6. If *get* is not **absent**, return ? Call(*get*, «*descr*, *o*, *T*»).
7. If *descr* is not **absent**, return *descr*.
8. Raise an `AttributeError` exception ("'*tname*(*o*)' object has no attribute
   '*name*'"), whose `name` attribute is *name* and whose `obj` attribute is
   *o*.

IsDataDescriptor(*d*) is **true** if LookupInMRO(Type(*d*), `"__set__"`) or
LookupInMRO(Type(*d*), `"__delete__"`) is not **absent**.

Step 5 reads the instance namespace directly: a `dict` subclass's
`__getitem__` is not called.

#### 7.3.6 TypeGetAttr ( *C*, *name* )

TypeGetAttr is the behaviour of `type.__getattribute__`, used when *C* is a
class.

1. Let *M* be Type(*C*).
2. Let *metaAttr* be LookupInMRO(*M*, *name*), and *metaGet* be **absent**.
3. If *metaAttr* is not **absent**, then
   1. Set *metaGet* to LookupInMRO(Type(*metaAttr*), `"__get__"`).
   2. If *metaGet* is not **absent** and IsDataDescriptor(*metaAttr*) is
      **true**, return ? Call(*metaGet*, «*metaAttr*, *C*, *M*»).
4. Let *attr* be LookupInMRO(*C*, *name*).
5. If *attr* is not **absent**, then
   1. Let *localGet* be LookupInMRO(Type(*attr*), `"__get__"`).
   2. If *localGet* is not **absent**, return ? Call(*localGet*, «*attr*,
      `None`, *C*»).
   3. Return *attr*.
6. If *metaGet* is not **absent**, return ? Call(*metaGet*, «*metaAttr*, *C*,
   *M*»).
7. If *metaAttr* is not **absent**, return *metaAttr*.
8. Raise an `AttributeError` exception ("type object '*C*.`__name__`' has no
   attribute '*name*'").

#### 7.3.7 SetAttribute ( *o*, *name*, *value* )

SetAttribute implements `o.name = value` and `setattr`. It calls
CallSpecial(*o*, `"__setattr__"`, «*name*, *value*») after the check of
7.3.4 step 1. `object.__setattr__` behaves as GenericSetAttr.

#### 7.3.8 GenericSetAttr ( *o*, *name*, *value* )

The argument *value* is an object, or **absent** for deletion.

1. Let *T* be Type(*o*).
2. Let *descr* be LookupInMRO(*T*, *name*).
3. If *descr* is not **absent**, then
   1. If *value* is **absent**, let *f* be LookupInMRO(Type(*descr*),
      `"__delete__"`); otherwise let *f* be LookupInMRO(Type(*descr*),
      `"__set__"`).
   2. If *f* is not **absent**, then
      1. If *value* is **absent**, perform ? Call(*f*, «*descr*, *o*»).
      2. Else, perform ? Call(*f*, «*descr*, *o*, *value*»).
      3. Return `None`.
   3. If *value* is **absent** and IsDataDescriptor(*descr*) is **true**,
      raise an `AttributeError` exception ("__delete__").
   4. If *value* is not **absent** and IsDataDescriptor(*descr*) is **true**,
      raise an `AttributeError` exception ("__set__").
4. If *o* has no instance namespace, then
   1. If *descr* is not **absent**, raise an `AttributeError` exception
      ("'*tname*(*o*)' object attribute '*name*' is read-only").
   2. Raise an `AttributeError` exception ("'*tname*(*o*)' object has no
      attribute '*name*' and no `__dict__` for setting new attributes").
5. Let *d* be the instance namespace of *o*.
6. If *value* is **absent**, then
   1. If *d* has no key *name*, raise an `AttributeError` exception
      ("'*tname*(*o*)' object has no attribute '*name*'").
   2. Remove *name* from *d*.
7. Else, bind *name* to *value* in *d*.
8. Return `None`.

#### 7.3.9 DeleteAttribute ( *o*, *name* )

DeleteAttribute implements `del o.name` and `delattr`. It calls
CallSpecial(*o*, `"__delattr__"`, «*name*») after the check of 7.3.4 step 1.
`object.__delattr__` behaves as GenericSetAttr(*o*, *name*, **absent**).

### 7.4 Call operations

#### 7.4.1 Call ( *f*, *args* [ , *kwargs* ] )

The abstract operation Call takes a callable *f*, a List of positional
arguments *args*, and optionally a List *kwargs* of (name, object) pairs with
distinct names, and returns an object or a raise completion.

1. If *f* is a function object (16.2), return ? CallFunction(*f*, *args*,
   *kwargs*).
2. If *f* is a built-in function or method (28.5), return the result of its
   algorithm, which binds *args* and *kwargs* as 7.4.4 specifies.
3. Let *call* be LookupInMRO(Type(*f*), `"__call__"`).
4. If *call* is **absent**, raise a `TypeError` exception ("'*tname*(*f*)'
   object is not callable").
5. Return ? Call(the result of binding *call* to *f* as in 7.3.2 steps 4–7,
   *args*, *kwargs*).

The recursion depth (9.6) increases by one for the duration of each Call of a
function object.

#### 7.4.2 CallFunction ( *f*, *args*, *kwargs* )

1. Let *code* be the Code Record of *f*.
2. Let *frame* be a new Frame Record (9.2) for *code*, whose globals are
   *f*.`__globals__`, whose builtins are BuiltinsOf(*f*.`__globals__`) (9.3.4),
   and whose cells for the free variables of *code* are the cells of
   *f*.`__closure__`, in order.
3. Perform ? BindArguments(*f*, *frame*, *args*, *kwargs*).
4. For each name *n* of *code* that is classified **cell** and is a parameter,
   move the parameter's value into a new cell.
5. If *code* is a generator, coroutine, or asynchronous generator code, return
   a new generator (27.2), coroutine (27.4), or asynchronous generator (27.5)
   object that owns *frame*, without running any of the body.
6. Let *result* be RunFrame(*frame*) (9.2.3).
7. If *result*.[[Type]] is **return**, return *result*.[[Value]].
8. If *result*.[[Type]] is **normal**, return `None`.
9. Return *result* (a raise completion).

#### 7.4.3 BindArguments ( *f*, *frame*, *args*, *kwargs* )

Let *sig* be the Signature of *f*'s code, *P* the List of its positional
parameters (positional-only, then positional-or-keyword), *qn* the
`__qualname__` of *f* followed by `"()"`, and *defaults* and *kwdefaults*
*f*.`__defaults__` and *f*.`__kwdefaults__`.

1. Let *n* be the number of elements of *args* and *k* the number of elements
   of *P*.
2. For *i* from 0 to min(*n*, *k*) − 1, bind *P*[*i*] to *args*[*i*].
3. If *sig*.[[VarPositional]] is not **absent**, bind it to a new tuple of the
   elements *args*[*k*], …, *args*[*n* − 1] (the empty tuple if *n* ≤ *k*).
4. If *sig*.[[VarKeyword]] is not **absent**, bind it to a new empty `dict`
   *extra*.
5. For each pair (*name*, *value*) in *kwargs*, in order:
   1. If *name* is a positional-or-keyword or keyword-only parameter, then
      1. If it is already bound, raise a `TypeError` exception ("*qn* got
         multiple values for argument '*name*'").
      2. Bind it to *value*.
   2. Else, if *sig*.[[VarKeyword]] is not **absent**, set *extra*[*name*] to
      *value*. (A positional-only name is collected here too.)
   3. Else,
      1. Let *posAsKw* be the List of the names in *kwargs*, in order, that are
         positional-only parameters.
      2. If *posAsKw* is not empty, raise a `TypeError` exception ("*qn* got
         some positional-only arguments passed as keyword arguments:
         '*names*'"), where *names* joins *posAsKw* with `", "`.
      3. Raise a `TypeError` exception ("*qn* got an unexpected keyword argument
         '*name*'", or a message beginning with that text).
6. If *n* > *k* and *sig*.[[VarPositional]] is **absent**, raise a `TypeError`
   exception as TooManyPositional(*qn*, *sig*, *n*, *kwargs*) describes.
7. Let *d* be the number of elements of *defaults*. For each parameter *p* of
   *P* at index *i* that is not bound: if *i* ≥ *k* − *d*, bind *p* to
   *defaults*[*i* − (*k* − *d*)]; otherwise append *p* to a List *missing*.
8. If *missing* is not empty, raise a `TypeError` exception ("*qn* missing *m*
   required positional argument*s*: *list*") as MissingArguments specifies.
9. For each keyword-only parameter *p* that is not bound: if *kwdefaults* has
   the key *p*, bind *p* to *kwdefaults*[*p*]; otherwise append *p* to
   *missing*.
10. If *missing* is not empty, raise a `TypeError` exception ("*qn* missing *m*
    required keyword-only argument*s*: *list*").

MissingArguments formats *list*: one name is `'a'`; two are `'a' and 'b'`;
three or more are `'a', 'b', and 'c'`; *s* is empty when *m* is 1 and `s`
otherwise.

TooManyPositional formats the message "*qn* takes *expected* positional
argument*s* but *given* *were*":

- *expected* is *k* if *f* has no defaults for positional parameters, and
  otherwise "from *k* − *d* to *k*"; *s* is empty when *expected* is exactly 1;
- *given* is *n*; it is followed by " positional argument*s* (and *j*
  keyword-only argument*s*)" when *j*, the number of keyword-only parameters
  bound by *kwargs*, is positive;
- *were* is `was given` if *n* is 1 and *j* is 0, and `were given` otherwise.

Static Semantics guarantee that the names of a Signature are distinct.

#### 7.4.4 Argument binding of built-in functions

A built-in function or method has a Signature given in its clause, written in
the form `name(a, /, b=default, *, c)`. Its arguments are bound as in 7.4.3,
except that the messages use the function's name without its owner where the
clause says so, and that a built-in function whose Signature contains no
keyword parameters raises a `TypeError` exception ("*name*() takes no keyword
arguments") when *kwargs* is not empty.

### 7.5 Type conversion

#### 7.5.1 ToBoolean ( *o* )

ToBoolean implements truth testing (`if`, `while`, `not`, `and`, `or`,
conditional expressions, comprehension conditions, `bool()`).

1. If *o* is `True`, return **true**. If *o* is `False` or `None`, return
   **false**.
2. Let *m* be ? LookupSpecial(*o*, `"__bool__"`).
3. If *m* is not **absent**, then
   1. If *m* is `None`, raise a `TypeError` exception ("'*tname*(*o*)' cannot
      be interpreted as a boolean").
   2. Let *r* be ? Call(*m*, «»).
   3. If *r* is `True`, return **true**; if *r* is `False`, return **false**.
   4. Raise a `TypeError` exception ("*fqname*(*o*).`__bool__`() must return a
      bool, not *tname*(*r*)").
4. Let *len* be ? LookupSpecial(*o*, `"__len__"`).
5. If *len* is not **absent**, return **true** if ? Length(*o*) is not 0 and
   **false** otherwise.
6. Return **true**.

#### 7.5.2 Length ( *o* )

1. Let *m* be ? LookupSpecial(*o*, `"__len__"`).
2. If *m* is **absent**, raise a `TypeError` exception ("object of type
   '*tname*(*o*)' has no len()").
3. Let *r* be ? ToIndex(? Call(*m*, «»)).
4. If ℝ(*r*) < 0, raise a `ValueError` exception ("`__len__`() should return >=
   0").
5. If ℝ(*r*) exceeds the maximum index size (Annex D), raise an `OverflowError`
   exception ("cannot fit 'int' into an index-sized integer").
6. Return the exact `int` with value ℝ(*r*) (a `bool` or subclass result is
   converted).

#### 7.5.3 ToIndex ( *o* )

ToIndex implements `operator.index` semantics: it converts an object that
represents an integer without loss.

1. If Type(*o*) is `int` or a subclass of `int`, return *o*.
2. Let *m* be ? LookupSpecial(*o*, `"__index__"`).
3. If *m* is **absent**, raise a `TypeError` exception ("'*tname*(*o*)' object
   cannot be interpreted as an integer").
4. Let *r* be ? Call(*m*, «»).
5. If Type(*r*) is `int`, return *r*.
6. If Type(*r*) is a strict subclass of `int`, issue a `DeprecationWarning`
   ("*fqname*(*o*).`__index__`() must return an int, not *tname*(*r*). The ability to
   return an instance of a strict subclass of int is deprecated, and may be
   removed in a future version of Python.") and return *r*.
7. Raise a `TypeError` exception ("*fqname*(*o*).`__index__`() must return an
   int, not *tname*(*r*)").

The phrase "issue a warning" invokes the host hook HostWarn (Annex B).

#### 7.5.4 ToIndexSize ( *o* )

1. Let *i* be ? ToIndex(*o*).
2. If ℝ(*i*) is outside the index-size range (Annex D), raise an
   `OverflowError` exception ("cannot fit 'int' into an index-sized integer").
3. Return ℝ(*i*).

Subscripting sequences, `range` arguments, repetition counts, and other
indices use ToIndexSize. Where a clause says an index is *clamped*, an
out-of-range value is replaced by the nearest bound instead.

#### 7.5.5 ToStr ( *o* )

ToStr implements `str(o)` for a single argument.

1. If Type(*o*) is `str`, return *o*.
2. Let *m* be ? LookupSpecial(*o*, `"__str__"`). (Every type inherits one; the
   inherited `object.__str__` calls ToRepr.)
3. Let *r* be ? Call(*m*, «»).
4. If Type(*r*) is not a subclass of `str`, raise a `TypeError` exception
   ("*fqname*(*o*).`__str__`() must return a str, not *tname*(*r*)").
5. Return *r*.

#### 7.5.6 ToRepr ( *o* )

1. Let *m* be ? LookupSpecial(*o*, `"__repr__"`).
2. If the current execution context is already computing the repr of a
   container that is *o* (a recursive repr), the clause for that container
   says what is returned instead.
3. Let *r* be ? Call(*m*, «»).
4. If Type(*r*) is not a subclass of `str`, raise a `TypeError` exception
   ("*fqname*(*o*).`__repr__`() must return a str, not *tname*(*r*)").
5. Return *r*.

ToRepr increases the recursion depth (9.6) while it runs.

#### 7.5.7 Hash ( *o* )

1. Let *m* be ? LookupSpecial(*o*, `"__hash__"`).
2. If *m* is **absent** or `None`, raise a `TypeError` exception ("unhashable
   type: '*tname*(*o*)'").
3. Let *r* be ? Call(*m*, «»).
4. If Type(*r*) is not a subclass of `int`, raise a `TypeError` exception
   ("`__hash__` method should return an integer").
5. Let *h* be the hash of the integer ℝ(*r*) as 22.1.9 specifies (for an *r*
   within the hash range this is ℝ(*r*) itself).
6. If *h* is −1, set *h* to −2.
7. Return *h*.

A class that defines `__eq__` but not `__hash__` has `__hash__` set to `None`
in its namespace by class creation (16.4.4).

#### 7.5.8 Format ( *o*, *spec* )

1. If Type(*spec*) is not a subclass of `str`, raise a `TypeError` exception
   ("format() argument 2 must be str, not *tname*(*spec*)").
2. Let *r* be ? CallSpecial(*o*, `"__format__"`, «*spec*»).
3. If Type(*r*) is not a subclass of `str`, raise a `TypeError` exception
   ("*fqname*(*o*).`__format__`() must return a str, not *tname*(*r*)").
4. Return *r*.

### 7.6 Operator dispatch

#### 7.6.1 Binary operator method names

| Operator | Method | Reflected | In-place | Symbol in messages |
| --- | --- | --- | --- | --- |
| `+` | `__add__` | `__radd__` | `__iadd__` | `+` |
| `-` | `__sub__` | `__rsub__` | `__isub__` | `-` |
| `*` | `__mul__` | `__rmul__` | `__imul__` | `*` |
| `@` | `__matmul__` | `__rmatmul__` | `__imatmul__` | `@` |
| `/` | `__truediv__` | `__rtruediv__` | `__itruediv__` | `/` |
| `//` | `__floordiv__` | `__rfloordiv__` | `__ifloordiv__` | `//` |
| `%` | `__mod__` | `__rmod__` | `__imod__` | `%` |
| `divmod` | `__divmod__` | `__rdivmod__` | — | `divmod()` |
| `**` | `__pow__` | `__rpow__` | `__ipow__` | `** or pow()` |
| `<<` | `__lshift__` | `__rlshift__` | `__ilshift__` | `<<` |
| `>>` | `__rshift__` | `__rrshift__` | `__irshift__` | `>>` |
| `&` | `__and__` | `__rand__` | `__iand__` | `&` |
| `^` | `__xor__` | `__rxor__` | `__ixor__` | `^` |
| `\|` | `__or__` | `__ror__` | `__ior__` | `\|` |

#### 7.6.2 BinaryOp ( *x*, *y*, *op* [ , *z* ] )

The abstract operation BinaryOp takes operands *x* and *y*, an operator *op*
of 7.6.1, and for `**` with three arguments a modulus *z*, and returns an object
or a raise completion. Let *m* and *r* be the method and reflected names of *op*,
and *extra* be «*z*» if *z* is present and «» otherwise.

1. Let *X* be Type(*x*) and *Y* be Type(*y*).
2. Let *fx* be LookupInMRO(*X*, *m*).
3. Let *ry* be **absent**. If *Y* is not *X*, set *ry* to LookupInMRO(*Y*, *r*).
4. If *ry* is not **absent**, IsSubclass(*Y*, *X*) is **true**, and *ry* is not
   the same object as LookupInMRO(*X*, *r*), then
   1. Let *res* be ? CallSpecial(*y*, *r*, «*x*» followed by *extra*).
   2. If *res* is not `NotImplemented`, return *res*.
   3. Set *ry* to **absent**.
5. If *fx* is not **absent**, then
   1. Let *res* be ? CallSpecial(*x*, *m*, «*y*» followed by *extra*).
   2. If *res* is not `NotImplemented`, return *res*.
6. If *ry* is not **absent**, then
   1. Let *res* be ? CallSpecial(*y*, *r*, «*x*» followed by *extra*).
   2. If *res* is not `NotImplemented`, return *res*.
7. If *z* is present, raise a `TypeError` exception ("unsupported operand
   type(s) for ** or pow(): '*tname*(*x*)', '*tname*(*y*)', '*tname*(*z*)'").
8. Raise a `TypeError` exception ("unsupported operand type(s) for *sym*:
   '*tname*(*x*)' and '*tname*(*y*)'"), where *sym* is the symbol of *op*.

The built-in numeric, sequence, and set types define their operator methods so
that they return `NotImplemented` for operands they do not support; this is how
`1 + 2.0` reaches `float.__radd__`. The methods of the modulus *z* are never
consulted.

For the `+` and `*` operators, when step 8 would be reached and *x* (or, for
`*`, *y*) supports the sequence concatenation or repetition protocol of a
built-in sequence type, the sequence clause specifies the result; for example
`[1] + (2,)` raises "can only concatenate list (not "tuple") to list".

#### 7.6.3 InPlaceOp ( *x*, *y*, *op* )

InPlaceOp implements augmented assignment (14.3).

1. Let *i* be the in-place method name of *op*.
2. If LookupInMRO(Type(*x*), *i*) is not **absent**, then
   1. Let *res* be ? CallSpecial(*x*, *i*, «*y*»).
   2. If *res* is not `NotImplemented`, return *res*.
3. Let *res* be BinaryOp(*x*, *y*, *op*).
4. If *res* is a raise completion created by step 8 of BinaryOp, replace its
   message by "unsupported operand type(s) for *sym*=: '*tname*(*x*)' and
   '*tname*(*y*)'".
5. Return *res*.

#### 7.6.4 UnaryOp ( *x*, *op* )

| Operator | Method | Symbol |
| --- | --- | --- |
| `-` | `__neg__` | `unary -` |
| `+` | `__pos__` | `unary +` |
| `~` | `__invert__` | `unary ~` |
| `abs()` | `__abs__` | `abs()` |

1. Let *m* be ? LookupSpecial(*x*, the method of *op*).
2. If *m* is **absent**, raise a `TypeError` exception ("bad operand type for
   *sym*: '*tname*(*x*)'").
3. Return ? Call(*m*, «»).

### 7.7 Iteration

#### 7.7.1 GetIterator ( *o* )

1. Let *m* be ? LookupSpecial(*o*, `"__iter__"`).
2. If *m* is `None`, raise a `TypeError` exception ("'*tname*(*o*)' object is
   not iterable").
3. If *m* is not **absent**, then
   1. Let *it* be ? Call(*m*, «»).
   2. If LookupInMRO(Type(*it*), `"__next__"`) is **absent**, raise a
      `TypeError` exception ("*fqname*(*o*).`__iter__`() must return an
      iterator, not *tname*(*it*)").
   3. Return *it*.
4. If LookupSpecial(*o*, `"__getitem__"`) is not **absent**, return a new
   sequence iterator (27.1.2) over *o*.
5. Raise a `TypeError` exception ("'*tname*(*o*)' object is not iterable").

#### 7.7.2 IteratorStep ( *it* )

IteratorStep advances an iterator. It returns an object, or **done** when the
iterator is exhausted.

1. Let *m* be LookupSpecial(*it*, `"__next__"`).
2. If *m* is **absent**, raise a `TypeError` exception ("'*tname*(*it*)' object
   is not an iterator").
3. Let *r* be Call(*m*, «»).
4. If *r* is a raise completion whose exception is an instance of
   `StopIteration`, return **done**.
5. Return ? *r*.

#### 7.7.3 IterateToList ( *o* )

1. Let *it* be ? GetIterator(*o*).
2. Let *values* be an empty List.
3. Repeat: let *v* be ? IteratorStep(*it*); if *v* is **done**, return *values*;
   append *v* to *values*.

#### 7.7.4 GetAsyncIterator ( *o* )

1. Let *m* be ? LookupSpecial(*o*, `"__aiter__"`).
2. If *m* is **absent**, raise a `TypeError` exception ("'async for' requires an
   object with `__aiter__` method, got *tname*(*o*)").
3. Let *it* be ? Call(*m*, «»).
4. If LookupInMRO(Type(*it*), `"__anext__"`) is **absent**, raise a `TypeError`
   exception ("'async for' received an object from `__aiter__` that does not
   implement `__anext__`: *tname*(*it*)").
5. Return *it*.

#### 7.7.5 GetAwaitable ( *o* )

GetAwaitable implements the operand of `await` (13.6).

1. If *o* is a coroutine object (27.4), or a generator object whose code is
   marked as an iterable coroutine (27.4.5), return *o*.
2. Let *m* be ? LookupSpecial(*o*, `"__await__"`).
3. If *m* is **absent**, raise a `TypeError` exception ("'*tname*(*o*)' object
   can't be awaited").
4. Let *it* be ? Call(*m*, «»).
5. If *it* is a coroutine object, raise a `TypeError` exception ("`__await__`()
   returned a coroutine").
6. If LookupInMRO(Type(*it*), `"__next__"`) is **absent**, raise a `TypeError`
   exception ("*fqname*(*o*).`__await__`() must return an iterator, not
   *tname*(*it*)").
7. Return *it*.

### 7.8 Container operations

#### 7.8.1 GetItem ( *o*, *key* )

1. Let *m* be ? LookupSpecial(*o*, `"__getitem__"`).
2. If *m* is not **absent**, return ? Call(*m*, «*key*»).
3. If *o* is a class, then
   1. Let *cg* be ? GetAttribute(*o*, `"__class_getitem__"`) if *o* has that
      attribute (via LookupInMRO), and **absent** otherwise.
   2. If *cg* is `None`, raise a `TypeError` exception ("type '*o*.`__name__`'
      is not subscriptable").
   3. If *cg* is not **absent**, return ? Call(*cg*, «*key*»).
   4. Raise a `TypeError` exception ("type '*o*.`__name__`' is not
      subscriptable").
4. Raise a `TypeError` exception ("'*tname*(*o*)' object is not
   subscriptable").

#### 7.8.2 SetItem ( *o*, *key*, *value* ) and DeleteItem ( *o*, *key* )

SetItem calls CallSpecial(*o*, `"__setitem__"`, «*key*, *value*»); if the
method is **absent** it raises a `TypeError` exception ("'*tname*(*o*)' object
does not support item assignment"). DeleteItem calls `__delitem__` with «*key*»
and otherwise raises a `TypeError` exception ("'*tname*(*o*)' object does not
support item deletion").

#### 7.8.3 Contains ( *container*, *item* )

Contains implements `item in container`.

1. Let *m* be ? LookupSpecial(*container*, `"__contains__"`).
2. If *m* is `None`, raise a `TypeError` exception ("'*tname*(*container*)'
   object is not a container").
3. If *m* is not **absent**, return ? ToBoolean(? Call(*m*, «*item*»)).
4. If LookupSpecial(*container*, `"__iter__"`) and
   LookupSpecial(*container*, `"__getitem__"`) are both **absent**, raise a
   `TypeError` exception ("argument of type '*tname*(*container*)' is not a
   container or iterable").
5. Let *it* be ? GetIterator(*container*).
6. Repeat:
   1. Let *v* be ? IteratorStep(*it*).
   2. If *v* is **done**, return **false**.
   3. If ? RichCompareBool(*v*, *item*, `==`) is **true**, return **true**.

### 7.9 Context management

#### 7.9.1 EnterContext ( *manager* )

1. Let *exit* be ? LookupSpecial(*manager*, `"__exit__"`).
2. If *exit* is **absent**, raise MissingContextMethod(*manager*, `"__exit__"`).
3. Let *enter* be ? LookupSpecial(*manager*, `"__enter__"`).
4. If *enter* is **absent**, raise MissingContextMethod(*manager*,
   `"__enter__"`).
5. Let *value* be ? Call(*enter*, «»).
6. Return the Record { [[Exit]]: *exit*, [[Value]]: *value* }.

MissingContextMethod(*manager*, *name*) is a `TypeError` exception
("'*fqname*(*manager*)' object does not support the context manager protocol
(missed *name* method)"). If the type of *manager* has both `__aenter__` and
`__aexit__`, the message continues with " but it supports the asynchronous
context manager protocol. Did you mean to use 'async with'?".

The asynchronous form, AsyncEnterContext, used by `async with` (15.5.2),
looks up `__aexit__` and then `__aenter__`, and its messages read "does not
support the asynchronous context manager protocol (missed *name* method)",
continuing with " but it supports the context manager protocol. Did you mean
to use 'with'?" when the type has both `__enter__` and `__exit__`.
