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

## 8 Static Semantics of Scopes

Before a module is evaluated, its parse tree is analysed into a tree of Scope
Records (6.2.6). The analysis determines, for every name in every scope, how
the name is resolved at run time (9.3). It calls no user code and depends only
on the source text.

### 8.1 Scopes

A **scope** is created by each of the following:

| Construct | Scope kind |
| --- | --- |
| a module (17.1), or the source of `exec` or `eval` | **module** |
| a `class` definition body | **class** |
| a `def` or `async def` body, or a `lambda` | **function** |
| a comprehension or generator expression (13.2.6) | **comprehension** |
| the annotations of a function, class, or module (16.6) | **annotation** |
| the type parameter list of a generic function, class, or type alias (16.7) | **type parameters** |
| the value of a `type` statement, the bound, constraints, or default of a type parameter | **annotation** |

The scopes form a tree: the *parent* of a scope is the scope whose source text
immediately contains the construct. The scope created by a type parameter list
is the parent of the scope of the function, class, or alias it parameterizes.

A function, comprehension, annotation, or type parameters scope is a
*function-like* scope. A comprehension scope does not create a separate frame
when it is evaluated (13.2.6), but its names are classified as for a function.

### 8.2 Binding occurrences

A name is **bound** in a scope when it occurs in that scope in one of the
following positions, which are its *binding occurrences*:

1. a target of an assignment, augmented assignment, or annotated assignment
   statement (14.2–14.4), including names within target lists, starred
   targets, and parenthesized or bracketed target lists, but not names
   appearing in an attribute reference or subscription target;
2. the target of a `for` loop or `async for` loop, or of a `for` clause of a
   comprehension (only in that comprehension's scope);
3. the name after `as` in a `with` item, an `except` clause, an `import`, or a
   pattern; the capture names of a `match` pattern (15.6);
4. a name defined by `def`, `async def`, or `class`;
5. a name imported by `import` (the first component of a dotted name when there
   is no `as`) or by `from … import`; a `from … import *` binds every public
   name of the module and is permitted only in a module scope;
6. a parameter of a function or lambda; a type parameter (in its type parameters
   scope);
7. the target of a `del` statement;
8. a name declared by a `type` statement;
9. the target of an assignment expression `name := value` (13.12), which binds
   in the nearest enclosing scope that is not a comprehension scope;
10. an annotated name without a value (`x: int`) in a function or class scope.

An *annotated name* is a name that is the target of an annotated assignment
statement in which the target is a single name not enclosed in parentheses.

### 8.3 Declarations

`global` *names* declares each name **global explicit** in the scope that
contains the statement. `nonlocal` *names* declares each name to refer to a
binding in an enclosing function-like scope (8.4 step 2).

#### 8.3.1 Static Semantics: Early Errors

It is a `SyntaxError`, with the stated message, if:

- a name is both a parameter and declared `global` in the same scope: "name
  '*n*' is parameter and global"; or declared `nonlocal`: "name '*n*' is
  parameter and nonlocal";
- a name is bound in a scope before a `global` or `nonlocal` declaration of it
  in that scope, in source order: "name '*n*' is assigned to before global
  declaration" (or "… before nonlocal declaration");
- a name is used (other than bound) before such a declaration: "name '*n*' is
  used prior to global declaration" (or "… prior to nonlocal declaration");
- an annotated name is declared `global` or `nonlocal` in the same scope:
  "annotated name '*n*' can't be global" (or "… can't be nonlocal");
- a name is declared both `global` and `nonlocal` in the same scope: "name '*n*'
  is nonlocal and global";
- a `nonlocal` statement appears in a module scope: "nonlocal declaration not
  allowed at module level";
- a function has two parameters with the same name: "duplicate parameter '*n*'
  in function definition";
- a type parameter list has two parameters with the same name: "duplicate type
  parameter '*n*'".

A `global` declaration in a class scope applies to the class body only; a
`nonlocal` declaration in a class scope refers to an enclosing function scope.

### 8.4 Name classification

For each scope *S* and each name *n* that occurs in *S*, the classification of
*n* in *S* is determined as follows, visiting scopes from the root downward and
then completing the **cell** classification on the way back up.

1. If *n* is declared `global` in *S*, then *n* is **global explicit** in *S*.
2. Else, if *n* is declared `nonlocal` in *S*, then
   1. If no enclosing function-like scope of *S* (stopping at the module scope,
      and skipping class scopes) binds *n* or declares it `nonlocal`, it is a
      `SyntaxError` ("no binding for nonlocal '*n*' found").
   2. If the nearest such binding is a type parameter, it is a `SyntaxError`
      ("nonlocal binding not allowed for type parameter '*n*'").
   3. *n* is **free** in *S*.
3. Else, if *n* is bound in *S*, then *n* is **local** in *S*.
4. Else, if *S* is an annotation or type parameters scope whose parent is a
   class scope *C* (it *can see the class scope*), and *n* is bound in *C* and
   not declared `nonlocal` there, or declared `global` there, then *n* is
   **global implicit** in *S* and is first looked up in the namespace of *C*
   (9.3.3).
5. Else, if an enclosing function-like scope of *S* (skipping class scopes)
   binds *n* and does not declare it `global`, *n* is **free** in *S*.
6. Else, *n* is **global implicit** in *S*. (If the nearest enclosing scope that
   mentions *n* declares it `global`, the effect is the same.)

Then, for every scope *F* in which *n* is **local** and some scope nested in *F*
classifies *n* as **free** with *F* the scope providing the binding, the
classification of *n* in *F* becomes **cell**. In a class scope, a name that is
**free** in the class scope itself is resolved by 9.3.3.

In a module scope every name is **global implicit** or **global explicit**,
and in a class scope a bound name is **local** to the class namespace. Names
in module and class scopes, and in scopes run by `exec` or `eval` with a
separate locals mapping, are looked up through a namespace mapping rather than
through fixed slots (9.3).

### 8.5 The implicit `__class__` cell

If a function scope nested directly in a class scope *C* (possibly through
other function scopes) uses the name `super` or the name `__class__`, then the
class scope *C* has [[NeedsClassCell]] set, `__class__` is a **cell** of *C*,
and it is **free** in each such function and in the scopes between. When the
class object is created (16.4.3), the cell is set to the new class.

### 8.6 Comprehension scopes

Each comprehension or generator expression has its own scope. Its first `for`
clause's iterable expression is evaluated in the enclosing scope and is not part
of the comprehension scope; every other part is. The targets of its `for`
clauses are **local** to the comprehension scope and are never visible outside
it.

An assignment expression in a comprehension binds its target in the nearest
enclosing scope that is not a comprehension; the target is then **free** in the
comprehension (or **global explicit** if that scope is the module scope or
declares it `global`). It is a `SyntaxError` if:

- the target is also an iteration variable of the comprehension: "assignment
  expression cannot rebind comprehension iteration variable '*n*'";
- an inner `for` clause rebinds a name that is an assignment expression target:
  "comprehension inner loop cannot rebind assignment expression target '*n*'";
- the assignment expression occurs in an iterable expression of the
  comprehension: "assignment expression cannot be used in a comprehension
  iterable expression";
- the nearest enclosing non-comprehension scope is a class scope:
  "assignment expression within a comprehension cannot be used in a class
  body"; or a type parameters or annotation scope, with the corresponding
  message ("… in a TypeVar bound", "… in a type alias", "… within the
  definition of a generic").

A comprehension in a class scope cannot see the names bound in the class body,
except in its first iterable, which is evaluated in the class scope.

### 8.7 Restrictions in annotation scopes

It is a `SyntaxError` for a `yield` expression, `yield from` expression,
`await` expression, or assignment expression to appear in an annotation scope or
type parameters scope. The messages are "*what* cannot be used within an
annotation", "*what* cannot be used within a TypeVar bound", "*what* cannot be
used within a type alias", and "*what* cannot be used within the definition of
a generic", where *what* is "yield expression", "await expression", or "named
expression".

### 8.8 Private name mangling

Within a class definition whose name, after removing leading underscores, is
not empty, every identifier *n* that occurs in the class body or in any scope
nested in it — as a name, an attribute name in an attribute reference, a
parameter name, an imported name, or a keyword argument name — and that begins
with two or more underscores and does not end with two or more underscores is
replaced, before any other processing, by MangledName(*class*, *n*): one
underscore, the class name with its leading underscores removed, and *n*. The
names of modules in `import` statements are mangled only in their first
component; names in `from … import` lists are not mangled when they are module
names but are mangled when they are bound names. Mangling does not apply to
string arguments of `getattr`, `setattr`, or `delattr`. Within a type
parameters scope, mangling uses the class that encloses the generic
definition, if any.

## 9 Executable Code and Execution Contexts

### 9.1 Namespaces

A **namespace** maps names to objects. The language uses four kinds:

- the **globals** of a module: the module's `__dict__`, a `dict`;
- the **builtins**: the namespace of the built-in names (clause 19), reached
  from the globals as 9.3.4 specifies;
- the **locals** of a module, class body, or `exec`/`eval` execution: a mapping
  that is not necessarily a `dict` (a class body's locals is the object
  returned by `__prepare__`, 16.4.2);
- the **fast locals** of a function-like scope: fixed slots, one for each name
  classified **local** or **cell**, each either holding an object or unbound,
  and one cell for each name classified **cell** or **free**.

A **cell** is an object (28.6) holding at most one object. A name classified
**cell** or **free** is read and written through its cell. Cells are created
when a frame starts (for **cell** names) and shared with nested functions
through their closures (for **free** names).

### 9.2 Execution contexts

#### 9.2.1 Frames

An **execution context** is a Frame Record (6.2.8), referred to as a *frame*. A
frame has:

| Field | Meaning |
| --- | --- |
| [[Code]] | the Code Record being run |
| [[Globals]] | the globals `dict` |
| [[Builtins]] | the builtins namespace |
| [[Locals]] | the locals mapping (module and class scopes), or the fast locals |
| [[Cells]] | the cells of the **cell** and **free** names |
| [[Back]] | the frame that was running when this frame started, or **null** |
| [[Position]] | the current position within the code, for tracebacks |
| [[HandledException]] | the exception being handled by an `except` clause (9.5), or **null** |
| [[State]] | **created**, **running**, **suspended**, or **completed** |

#### 9.2.2 The execution context stack

The *execution context stack* holds the frames that have started and not
completed and are not suspended. The *running execution context* is the top
of the stack. A call to a function pushes a frame (7.4.2); completing the
function pops it. Resuming a generator or coroutine (27.2) pushes its frame;
suspending it at a `yield` or `await` pops it, preserving its state.

#### 9.2.3 RunFrame ( *frame* )

1. Set *frame*.[[Back]] to the running execution context, push *frame* onto the
   execution context stack, and set *frame*.[[State]] to **running**.
2. Let *result* be the result of evaluating the body of *frame*.[[Code]] in
   *frame*.
3. Pop *frame* from the stack and set *frame*.[[State]] to **completed**.
4. If *result* is a raise completion, add an entry for *frame* to the
   traceback of its exception (18.1.3).
5. Return *result*.

### 9.3 Name resolution

The following operations implement reading, writing, and deleting a name *n*
in the running execution context *frame*, according to the classification of
*n* in the scope of *frame*.[[Code]].

#### 9.3.1 LoadName ( *n* )

| Classification | Behaviour |
| --- | --- |
| **local**, in a function-like scope | if the slot of *n* is unbound, raise an `UnboundLocalError` exception ("cannot access local variable '*n*' where it is not associated with a value"); otherwise return its value |
| **cell** or **free**, in a function-like scope | if the cell is empty, raise an `UnboundLocalError` exception (as above) when *n* is **cell**, or a `NameError` exception ("cannot access free variable '*n*' where it is not associated with a value in enclosing scope") when it is **free**; otherwise return its contents |
| **global explicit** or **global implicit**, in a function-like scope | return ? LoadGlobal(*n*) |
| any, in a module scope, a class scope, or an `exec`/`eval` scope with a locals mapping | return ? LoadFromLocals(*n*) |

LoadFromLocals(*n*):

1. If *n* is **global explicit**, return ? LoadGlobal(*n*).
2. If *n* is **free** in a class scope, return ? LoadClassFree(*n*) (9.3.3).
3. Let *v* be ? GetItem(*frame*.[[Locals]], *n*), treating a `KeyError`
   exception as **absent**. (If [[Locals]] is exactly a `dict`, it is read
   directly.)
4. If *v* is not **absent**, return *v*.
5. Return ? LoadGlobal(*n*).

#### 9.3.2 LoadGlobal ( *n* )

1. If *frame*.[[Globals]] has the key *n*, return its value.
2. Let *v* be the value of *n* in *frame*.[[Builtins]], looked up with GetItem
   if [[Builtins]] is not exactly a `dict`, treating a `KeyError` exception as
   **absent**.
3. If *v* is not **absent**, return *v*.
4. Raise a `NameError` exception ("name '*n*' is not defined", or a message
   beginning with that text), whose `name` attribute is *n*.

#### 9.3.3 LoadClassFree ( *n* )

In a class scope a **free** name, and in an annotation or type parameters
scope that can see a class scope a name that the class binds, is looked up
first in the class namespace:

1. Let *ns* be the class namespace (the locals of the class body, or for an
   annotation scope the class's `__dict__` captured as `__classdict__`).
2. If *ns* has the key *n*, return its value.
3. If *n* is **free**, return the contents of its cell, raising a `NameError`
   as 9.3.1 specifies when the cell is empty.
4. Return ? LoadGlobal(*n*).

#### 9.3.4 BuiltinsOf ( *globals* )

1. If *globals* has the key `"__builtins__"`, let *b* be its value; if *b* is a
   module object, return *b*.`__dict__`; otherwise return *b*.
2. Return the built-in namespace (clause 19).

A frame's builtins are fixed when the frame starts; a function's builtins are
those of its globals at the time the function object was created (16.2).

#### 9.3.5 StoreName ( *n*, *v* ) and DeleteName ( *n* )

StoreName binds *n* to *v*: in the slot or cell of a **local**, **cell**, or
**free** name; in [[Globals]] for a **global explicit** name or any global name
of a function-like scope; and otherwise by ? SetItem(*frame*.[[Locals]], *n*,
*v*).

DeleteName unbinds *n* in the same place. Deleting an unbound slot raises the
`UnboundLocalError` of 9.3.1; deleting an empty cell raises it for a **cell**
name and the `NameError` of 9.3.1 for a **free** name; deleting a name absent
from a namespace mapping raises a `NameError` exception ("name '*n*' is not
defined").

### 9.4 Suspension and resumption

The frame of a generator, coroutine, or asynchronous generator can be
*suspended*: evaluation stops at a `yield` or at an `await` whose awaitable has
not completed, the frame is popped from the execution context stack with its
state preserved, and a value is delivered to the code that resumed it. Resuming
pushes the frame again and continues the evaluation from the point of
suspension with a value, an exception to raise there, or a request to close.
Clause 27 specifies the protocols. A frame is never resumed while it is
running; an attempt raises a `ValueError` exception ("generator already
executing", or "coroutine already executing").

### 9.5 The handled exception

While an `except` clause or `except*` clause runs (15.4), the exception it
handles is the *handled exception* of the frame. The **current handled
exception** is the [[HandledException]] of the nearest frame on the execution
context stack, from the top down, whose value is not **null**; it is `None`
when there is none. It is what a bare `raise` re-raises (14.8) and what an
exception raised inside a handler gets as its `__context__` (18.1.2). When the
`except` clause ends, the previous handled exception is restored. A suspended
generator keeps its handled exception and restores it when resumed.

### 9.6 Recursion limit

Each running Call of a function object, each ToRepr, and each nested evaluation
the implementation counts adds one to the *recursion depth*. When the depth
would exceed the *recursion limit* (Annex D), the operation raises a
`RecursionError` exception ("maximum recursion depth exceeded", or a message
beginning with that text) instead of starting. The implementation shall also
raise `RecursionError` before nesting would exhaust its own resources, so that
deeply nested data structures and parse trees fail safely.

### 9.7 Object lifetime and finalization

An object that is no longer reachable from a root (6.1.1) may be reclaimed.
Before an object whose type defines `__del__` is reclaimed, its `__del__` method
is called, at most once for the object's lifetime, even if `__del__` makes it
reachable again. Objects that are reachable only through reference cycles shall
eventually be reclaimed, including their `__del__` methods. The time at which an
unreachable object is reclaimed, and the order in which a group of unreachable
objects is finalized, are implementation-approximated. An exception that
escapes `__del__` is not propagated; it is reported through the host hook
HostReportUnraisable (Annex B).

### 9.8 Program execution

A program starts when the host runs a module as the main module (17.1): it
creates a module object named `"__main__"`, binds the standard module
attributes (17.2), and evaluates the module's source in its namespace. An
exception that escapes the main module is reported through HostReportException
(Annex B); a `SystemExit` exception is handled as Annex B specifies.

## 10 Object Behaviours

### 10.1 Instances

#### 10.1.1 Instance namespaces

An instance of a class defined by a `class` statement has an *instance
namespace*, a `dict` reachable as its `__dict__` attribute, unless every class
in its MRO that is defined by a `class` statement declares `__slots__` (10.1.2)
and none of them names `__dict__` there. Instances of built-in types have no
instance namespace unless their clause says so; function objects, module
objects, and class objects have one.

The `__dict__` attribute of an instance is a data descriptor (a
%GetSetDescriptorType% object, 28.8) found in the class. Assigning to it
replaces the namespace:

1. If the value is not an instance of `dict` (a subclass is accepted), raise a
   `TypeError` exception ("`__dict__` must be set to a dictionary, not a
   '*tname*(*value*)'").
2. Otherwise the value becomes the instance namespace. GenericGetAttr and
   GenericSetAttr read and write it as a `dict`, without calling methods that
   a subclass overrides.

#### 10.1.2 `__slots__`

If a class body binds `__slots__`, class creation (16.4.3) reserves storage for
the named attributes in each instance instead of (or in addition to) an
instance namespace:

1. If `__slots__` is a `str`, the class has one slot with that name; otherwise
   it is iterated (7.7.3) and every element shall be a `str`, or a `TypeError`
   exception ("`__slots__` items must be strings, not '*tname*(*item*)'") is
   raised.
2. Each name shall be an identifier (12.4), or a `TypeError` exception
   ("`__slots__` must be identifiers") is raised. Names are mangled (8.8).
3. The name `__dict__` requests an instance namespace; it is a `TypeError`
   ("`__dict__` slot disallowed: we already got one") if a base already
   provides one or if it is named twice. The name `__weakref__` requests weak
   reference support and is subject to the corresponding rule ("`__weakref__`
   slot disallowed: we already got one").
4. If a slot name is also bound in the class namespace, raise a `ValueError`
   exception ("'*name*' in `__slots__` conflicts with class variable").
5. For each other name, the class namespace binds the name to a new member
   descriptor (%MemberDescriptorType%, 28.8) that reads, writes, and deletes
   that slot of an instance. Reading or deleting an empty slot raises an
   `AttributeError` exception ("'*tname*(*o*)' object has no attribute
   '*name*'").
6. A class whose base is a built-in type with variable-sized instances (`int`,
   `bytes`, `tuple`) may not declare non-empty slots other than `__dict__` and
   `__weakref__`: "arbitrary `__slots__` not supported for subtype of
   '*base*'" (or "nonempty `__slots__` not supported for subtype of
   '*base*'").

The classes whose instances have slots, or which derive from built-in types,
have an *instance layout*. Two classes have *compatible layouts* when they have
the same slots, in the same order, the same presence of an instance namespace,
and the same built-in base layout. Class creation requires that the bases of a
class have a single most-derived layout ("multiple bases have instance lay-out
conflict").

#### 10.1.3 `__class__` assignment

Assigning to the `__class__` attribute of an object *o* changes Type(*o*):

1. If the value *C* is not a class, raise a `TypeError` exception
   ("`__class__` must be set to a class, not '*tname*(*C*)' object").
2. If neither Type(*o*) nor *C* is a class defined by a `class` statement (or
   a subclass of `%ModuleType%`), raise a `TypeError` exception ("`__class__`
   assignment only supported for mutable types or ModuleType subclasses").
3. If the layouts of Type(*o*) and *C* are not compatible, raise a `TypeError`
   exception ("`__class__` assignment: '*C*.`__name__`' object layout differs
   from '*tname*(*o*)'").
4. Set Type(*o*) to *C*.

### 10.2 Instance creation

#### 10.2.1 Calling a class

Calling a class *C* (that is, Call(*C*, *args*, *kwargs*) where `type.__call__`
is found by 7.4.1 step 3) runs `type.__call__`:

1. If *C* is `type` itself, *args* has one element, and *kwargs* is empty,
   return Type(*args*[0]).
2. If *C* is `type` itself and *args* does not have exactly three elements,
   raise a `TypeError` exception ("type() takes 1 or 3 arguments").
3. Let *new* be LookupInMRO(*C*, `"__new__"`). If *new* is **absent** (the
   class's instances cannot be created by a call), raise a `TypeError`
   exception ("cannot create '*C*.`__name__`' instances").
4. Let *obj* be ? Call(*new*, «*C*» followed by *args*, *kwargs*). (`__new__`
   is a static method; 20.1.5.)
5. If IsSubclass(Type(*obj*), *C*) is **false**, return *obj*.
6. Let *r* be ? CallSpecial(*obj*, `"__init__"`, *args*, *kwargs*).
7. If *r* is not `None`, raise a `TypeError` exception ("`__init__`() should
   return None, not '*tname*(*r*)'").
8. Return *obj*.

#### 10.2.2 `object.__new__` and `object.__init__`

`object.__new__(cls, *args, **kwargs)`:

1. If *cls* is not a class, raise a `TypeError` exception ("object.`__new__`(X):
   X is not a type object (*tname*(*cls*))").
2. If *cls* is not a subclass of `object` whose instances `object.__new__` can
   create (its nearest built-in base is `object`), raise a `TypeError` exception
   ("object.`__new__`(*cls*.`__name__`) is not safe, use
   *base*.`__new__`()").
3. If *args* or *kwargs* is not empty, then
   1. If LookupInMRO(*cls*, `"__new__"`) is not `object.__new__`, raise a
      `TypeError` exception ("object.`__new__`() takes exactly one argument (the
      type to instantiate)").
   2. If LookupInMRO(*cls*, `"__init__"`) is `object.__init__`, raise a
      `TypeError` exception ("*cls*.`__name__`() takes no arguments").
4. If *cls* is abstract (20.2.8), raise a `TypeError` exception ("Can't
   instantiate abstract class *cls*.`__name__` without an implementation for
   abstract method*s* *names*"), where *names* are the sorted names of
   *cls*.`__abstractmethods__`, each quoted with `'` and joined with `", "`.
5. Return a new instance of *cls* with an empty instance namespace (if the
   layout has one) and empty slots.

`object.__init__(self, *args, **kwargs)`:

1. If *args* or *kwargs* is not empty, then
   1. If LookupInMRO(Type(*self*), `"__init__"`) is not `object.__init__`, raise
      a `TypeError` exception ("object.`__init__`() takes exactly one argument
      (the instance to initialize)").
   2. If LookupInMRO(Type(*self*), `"__new__"`) is `object.__new__`, raise a
      `TypeError` exception ("*tname*(*self*).`__init__`() takes exactly one
      argument (the instance to initialize)").
2. Return `None`.

### 10.3 Descriptors

A **descriptor** is an object whose type defines one or more of `__get__`,
`__set__`, and `__delete__`. When a descriptor is found in a class namespace by
attribute lookup, the lookup calls its methods instead of returning it (7.3.5,
7.3.6, 7.3.8). A **data descriptor** defines `__set__` or `__delete__`
(IsDataDescriptor, 7.3.5); it takes precedence over the instance namespace. A
**non-data descriptor** defines only `__get__`; the instance namespace takes
precedence over it.

The call `descr.__get__(instance, owner)` receives `None` as *instance* when
the attribute is looked up on the class *owner*. `__set_name__(owner, name)` is
called on each descriptor when its class is created (16.4.3).

The built-in descriptors are: function objects (16.2.3), which bind to an
instance and produce methods; `staticmethod` and `classmethod` objects (20.6,
20.7); `property` objects (20.5); member and getset descriptors (28.8); and
method, wrapper, and class-method descriptors of built-in types (28.7).

### 10.4 Class objects

#### 10.4.1 Attribute access on classes

`type.__getattribute__` behaves as TypeGetAttr (7.3.6). `type.__setattr__` and
`type.__delattr__` behave as GenericSetAttr on the class namespace, except:

1. A built-in type or other immutable type rejects every assignment and
   deletion: "cannot set '*name*' attribute of immutable type '*T*'" and
   "cannot delete '*name*' attribute of immutable type '*T*'"
   (`TypeError`).
2. The class namespace is read-only through `__dict__`: `C.__dict__` is a
   %MappingProxyType% view (26.6) of it.
3. Setting or deleting an attribute whose name is a special method updates the
   behaviour of the operation that looks it up; LookupInMRO always reads the
   current class namespaces.

#### 10.4.2 Type attributes

A class *C* has the following attributes, defined as data descriptors on
`type` (20.2):

| Attribute | Read | Write |
| --- | --- | --- |
| `__name__` | the class name | a `str` only ("can only assign string to *C*.`__name__`, not '*tname*(*v*)'"), not containing a null character |
| `__qualname__` | the qualified name (16.4.3) | a `str` only ("can only assign string to *C*.`__qualname__`, not '*tname*(*v*)'") |
| `__module__` | `__module__` of the class namespace | any object |
| `__bases__` | the tuple of bases | a non-empty tuple of classes with a compatible layout, creating no cycle; recomputes `__mro__` of *C* and its subclasses |
| `__mro__` | the tuple from ComputeMRO | read-only |
| `__dict__` | a %MappingProxyType% of the namespace | read-only |
| `__doc__` | `__doc__` of the namespace, or `None` | any object |
| `__type_params__` | the tuple of type parameters (16.7) | a tuple |
| `__annotations__`, `__annotate__` | 16.6 | 16.6 |
| `__abstractmethods__` | the set given (absent until set) | any iterable; sets abstractness (20.2.8) |

Assigning `__mro__` or `__dict__`, or deleting them, raises an
`AttributeError` exception ("attribute '*name*' of 'type' objects is not
writable"). Deleting `__name__`, `__qualname__`, `__module__`, `__bases__`,
`__doc__`, or `__type_params__` raises a `TypeError` exception ("cannot delete
'*name*' attribute of type '*C*.`__name__`'"). Deleting `__abstractmethods__`
when it was never set raises an `AttributeError` exception
("`__abstractmethods__`"). A `__name__` containing U+0000 raises a `ValueError`
exception ("type name must not contain null characters").

Assigning `__bases__` performs these checks, in order:

1. If the value is not a tuple, raise a `TypeError` exception ("can only assign
   tuple to *C*.`__name__`.`__bases__`, not *tname*(*v*)").
2. If it is empty, raise a `TypeError` exception ("can only assign non-empty
   tuple to *C*.`__name__`.`__bases__`, not ()").
3. If an element *b* is not a class, raise a `TypeError` exception
   ("*C*.`__name__`.`__bases__` must be tuple of classes, not
   '*tname*(*b*)'").
4. If *C* is an element of the MRO of some element, raise a `TypeError`
   exception ("a `__bases__` item causes an inheritance cycle").
5. If the layout of the new most-derived base differs from the old one, raise a
   `TypeError` exception ("`__bases__` assignment: '*B*' object layout differs
   from '*A*'").
6. Set the bases and recompute the MRO of *C* and of each of its subclasses.

### 10.5 Special method names

The following table lists the special methods that language operations look up
by LookupSpecial (7.3.2) and the clause that uses each.

| Methods | Used by |
| --- | --- |
| `__new__`, `__init__`, `__del__` | instance creation (10.2), finalization (9.7) |
| `__repr__`, `__str__`, `__bytes__`, `__format__` | ToRepr, ToStr, `bytes()`, Format (7.5) |
| `__lt__`, `__le__`, `__eq__`, `__ne__`, `__gt__`, `__ge__` | RichCompare (7.2.4) |
| `__hash__`, `__bool__` | Hash (7.5.7), ToBoolean (7.5.1) |
| `__getattribute__`, `__getattr__`, `__setattr__`, `__delattr__`, `__dir__` | attribute access (7.3), `dir()` |
| `__get__`, `__set__`, `__delete__`, `__set_name__` | descriptors (10.3) |
| `__init_subclass__`, `__prepare__`, `__mro_entries__`, `__class_getitem__` | class creation (16.4) |
| `__instancecheck__`, `__subclasscheck__` | `isinstance`, `issubclass` (19.3) |
| `__call__` | Call (7.4.1) |
| `__len__`, `__length_hint__`, `__getitem__`, `__setitem__`, `__delitem__`, `__missing__`, `__iter__`, `__reversed__`, `__contains__` | containers (7.8), iteration (7.7) |
| the methods of 7.6.1, their reflected and in-place forms | BinaryOp, InPlaceOp (7.6) |
| `__neg__`, `__pos__`, `__abs__`, `__invert__` | UnaryOp (7.6.4) |
| `__complex__`, `__int__`, `__float__`, `__index__` | `complex()`, `int()`, `float()`, ToIndex |
| `__round__`, `__trunc__`, `__floor__`, `__ceil__` | `round()`, and the numeric clauses |
| `__enter__`, `__exit__`, `__aenter__`, `__aexit__` | `with`, `async with` (15.5) |
| `__await__`, `__aiter__`, `__anext__` | `await`, `async for` (13.6, 15.3.2) |
| `__buffer__`, `__release_buffer__` | the buffer protocol (24.4) |
| `__match_args__` (a class attribute) | class patterns (15.6.9) |

A program shall not depend on any other method name being looked up
implicitly.

## 11 Source Text

### 11.1 Source code

*Source text* is a sequence of Unicode code points. It is obtained from the
bytes of a source file by decoding them (11.2), or given directly as a `str`
to `compile`, `exec`, or `eval` (19.3). The code point U+0000 shall not occur in
source text; if it does, a `SyntaxError` exception ("source code string cannot
contain null bytes") is raised.

### 11.2 Source encoding

Source given as bytes (a module file, or a `bytes` argument to `compile`,
`exec`, or `eval`) is decoded as follows.

1. If the bytes begin with the UTF-8 byte order mark EF BB BF, remove it and
   let *bom* be **true**.
2. If the first line, or the second line when the first line is a line
   containing only a comment or only whitespace, contains a comment that matches
   the pattern `coding[=:]\s*([-\w.]+)` (an *encoding declaration*), let *name*
   be the captured name. Otherwise let *name* be `"utf-8"`.
3. Normalize *name*: lowercase it and replace `_` by `-`. If the result is
   `utf-8` or `utf8` or starts with `utf-8-`, the encoding is UTF-8; if it is
   `latin-1`, `latin1`, `iso-8859-1`, `iso8859-1`, `iso-latin-1`, or starts with
   `latin-1-` or `iso-8859-1-`, the encoding is ISO 8859-1; if it is `ascii` or
   `us-ascii`, the encoding is US-ASCII.
4. If *bom* is **true** and the encoding is not UTF-8, raise a `SyntaxError`
   exception ("encoding problem: *canonical* with BOM"), where *canonical* is
   `iso-8859-1` or `ascii`, or the host's canonical name of the encoding.
5. If the encoding is none of these, call the host hook HostDecodeSource
   (Annex B). If the host does not supply the encoding, raise a `SyntaxError`
   exception ("unknown encoding: *name*").
6. Decode the bytes. If they are not valid in the encoding, raise a
   `SyntaxError` exception. When the encoding was not declared, the message is
   "Non-UTF-8 code starting with '\x*hh*' in file *filename* on line *n*, but
   no encoding declared; see https://peps.python.org/pep-0263/ for details",
   where *hh* is the first invalid byte in hexadecimal.

Core implementations shall support the three encodings named in step 3.
Source given as a `str` is not decoded; an encoding declaration in it is a
comment.

### 11.3 Lines

The sequences CR LF, CR, and LF each terminate a *physical line*. When source
text is read from a `str`, these are the only line terminators; other Unicode
line separators are ordinary characters. A *logical line* is a sequence of one
or more physical lines joined by the rules of 12.2; it is terminated by a
`NEWLINE` token.

## 12 Lexical Grammar

The source text is converted into a sequence of tokens. At every point the
longest sequence of code points that forms a token is taken (the "maximal
munch" rule), with the exceptions of 12.6.3 and 12.7.

### 12.1 Tokens

The token kinds are `NAME` (identifiers, keywords, and soft keywords),
`NUMBER`, `STRING` (with the f-string and t-string parts of 12.5.6), the
operators and delimiters of 12.7, `NEWLINE`, `INDENT`, `DEDENT`, and
`ENDMARKER`. Whitespace (U+0020 SPACE, U+0009 TAB, U+000C FORM FEED) separates
tokens and is otherwise ignored, except at the start of a logical line (12.3)
and inside string literals. Whitespace is required between two tokens only if
their concatenation would otherwise be read as a different token.

A code point that cannot begin any token, outside a string literal or comment,
is an error:

- U+0024 `$`, U+003F `?`, and U+0060 `` ` ``: `SyntaxError` ("invalid syntax");
- a printable character that is not part of an operator, identifier, or
  literal: `SyntaxError` ("invalid character '*c*' (U+*XXXX*)");
- a non-printable character (Unicode general categories Cc, Cf, Cs, Co, Cn, Zl,
  Zp, and Zs other than U+0020): `SyntaxError` ("invalid non-printable
  character U+*XXXX*"),

where *XXXX* is the code point in at least four uppercase hexadecimal digits.

### 12.2 Line structure

#### 12.2.1 Comments

A comment starts with a `#` that is not part of a string literal and ends at
the end of the physical line. Comments are ignored, except that an encoding
declaration (11.2) is a comment and that a comment on a line by itself makes the
line blank.

#### 12.2.2 Explicit line joining

A backslash `\` that is not part of a string literal or comment and is followed
by a line terminator joins the physical line with the next one, deleting the
backslash and the terminator. A backslash followed by any other character
outside a string literal raises a `SyntaxError` exception ("unexpected
character after line continuation character"). A backslash at the end of the
source text raises a `SyntaxError` exception ("unexpected EOF while parsing").
A line ending in a backslash cannot carry a comment.

#### 12.2.3 Implicit line joining

Between an opening bracket (`(`, `[`, `{`) and its matching closing bracket,
line terminators, comments, and indentation are ignored: no `NEWLINE`,
`INDENT`, or `DEDENT` token is produced. A closing bracket that does not match
the innermost opening bracket raises a `SyntaxError` exception ("closing
parenthesis '*c*' does not match opening parenthesis '*o*'", with " on line
*n*" appended when the opening bracket is on an earlier line); one with no
opening bracket raises ("unmatched '*c*'"); an opening bracket unmatched at the
end of the source raises ("'*o*' was never closed").

#### 12.2.4 Blank lines

A logical line that contains only whitespace and possibly a comment is blank and
produces no tokens. In interactive input (17.6.2), an entirely blank line
terminates a multi-line statement.

#### 12.2.5 NEWLINE and ENDMARKER

The end of each non-blank logical line produces a `NEWLINE` token. At the end
of the source text, a `NEWLINE` is produced if the last logical line did not
end with one, then the `DEDENT` tokens of 12.3, then `ENDMARKER`.

### 12.3 Indentation

The whitespace at the start of a logical line determines its *indentation*.
Indentation is measured twice:

- *col* counts each space as 1 and advances each tab to the next multiple of 8;
- *altcol* counts each space and each tab as 1.

A form feed resets both to 0. The algorithm keeps a stack of (*col*,
*altcol*) pairs, initially «(0, 0)». At the start of each non-blank logical line,
outside brackets, with measures (*c*, *a*) and stack top (*tc*, *ta*):

1. If *c* = *tc*: if *a* ≠ *ta*, raise a `TabError` exception ("inconsistent use
   of tabs and spaces in indentation"). Produce nothing.
2. If *c* > *tc*: if *a* ≤ *ta*, raise the same `TabError`. Push (*c*, *a*) and
   produce an `INDENT` token.
3. If *c* < *tc*: pop pairs while the top *col* exceeds *c*, producing one
   `DEDENT` token for each. If the new top *col* is not *c*, raise an
   `IndentationError` exception ("unindent does not match any outer indentation
   level"); if it is *c* but its *altcol* is not *a*, raise the `TabError`.

At the end of the source text, one `DEDENT` is produced for each pair on the
stack other than the bottom one.

The parser (not the tokenizer) raises an `IndentationError` exception for an
`INDENT` where no block may begin ("unexpected indent"), for a missing `INDENT`
after a line ending in `:` that begins a block ("expected an indented block
after *construct* on line *n*", where *construct* is, for example,
`'if' statement`, `function definition`, or `class definition`).

### 12.4 Names

#### 12.4.1 Identifiers

```text
identifier:   id_start id_continue*
id_start:     <"_" or a code point with the Unicode property XID_Start>
id_continue:  <id_start, or a code point with the property XID_Continue>
```

The properties are those of the Unicode Character Database of the Unicode
baseline. Every identifier is converted to Normalization Form KC (NFKC) when the
source is parsed; two identifiers are the same if their NFKC forms are equal. A
non-ASCII identifier that is not valid after normalization raises a
`SyntaxError` exception ("invalid character '*c*' (U+*XXXX*)").

#### 12.4.2 Keywords and soft keywords

The following identifiers are *keywords*; they cannot be used as ordinary
names:

```text
False      await      else       import     pass
None       break      except     in         raise
True       class      finally    is         return
and        continue   for        lambda     try
as         def        from       nonlocal   while
assert     del        global     not        with
async      elif       if         or         yield
```

The following are *soft keywords*: `match`, `case`, `_`, `type`, and `lazy`.
They are keywords only in the grammatical contexts of clauses 14.14 (`type`),
14.12 (`lazy`), and 15.6 (`match`, `case`, `_`), and ordinary names elsewhere.
An assignment to a keyword raises a `SyntaxError` exception ("cannot assign to
*keyword*"), and its use as an identifier elsewhere raises ("invalid syntax").

#### 12.4.3 Reserved classes of identifiers

Identifiers of the form `__*__` are reserved for names defined by this Standard
and by implementations. Identifiers beginning with `_` are not imported by
`from module import *` (17.4.3). Identifiers of the form `__*` (not ending in
two underscores) in a class are mangled (8.8).

### 12.5 String and bytes literals

#### 12.5.1 Syntax

```text
stringliteral:   [stringprefix] (shortstring | longstring)
stringprefix:    "r" | "u" | "b" | "br" | "rb" | "f" | "fr" | "rf" | "t" | "tr" | "rt"
                 (any letter may be uppercase)
shortstring:     "'" shortchar* "'" | '"' shortchar* '"'
longstring:      "'''" longchar* "'''" | '"""' longchar* '"""'
shortchar:       <any code point except "\", the line terminators, and the quote>
                 | escapeseq
longchar:        <any code point except "\"> | escapeseq
escapeseq:       "\" <any code point>
```

No whitespace is allowed between the prefix and the quote. A prefix that
combines `u` with any other letter raises a `SyntaxError` exception ("'u' and
'*x*' prefixes are incompatible"), and one that combines two of `b`, `f`, `t`
raises ("'*x*' and '*y*' prefixes are incompatible"), naming the letters in the
order `u`, `r`, `b`, `f`, `t`.

A short string literal that reaches the end of its line raises a `SyntaxError`
exception ("unterminated string literal (detected at line *n*)"); a long string
literal that reaches the end of the source raises ("unterminated triple-quoted
string literal (detected at line *n*)"), where *n* is the line where the
tokenizer stopped. The exception's `lineno` is the line where the literal
starts.

A literal with prefix `b` (in either case, alone or with `r`) is a *bytes
literal* and produces a `bytes` object; it may contain only ASCII code points,
else a `SyntaxError` exception ("bytes can only contain ASCII literal
characters") is raised. A literal with prefix `f` is an *f-string* (12.5.6) and
one with prefix `t` a *t-string* (12.5.7). Any other literal produces a `str`.

#### 12.5.2 Raw literals

In a literal with prefix `r`, a backslash and the code point after it are both
kept; no escape sequence is recognized. A backslash still prevents the
following quote from ending the literal, and a raw literal cannot end with an
odd number of backslashes.

#### 12.5.3 Escape sequences

In a literal without prefix `r`, the following escape sequences are recognized.
Sequences marked *str* are recognized only in `str` literals, not in bytes
literals.

| Sequence | Meaning |
| --- | --- |
| `\` *line terminator* | nothing (the backslash and terminator are removed) |
| `\\`, `\'`, `\"` | the backslash, apostrophe, or quotation mark |
| `\a`, `\b`, `\f`, `\n`, `\r`, `\t`, `\v` | U+0007, U+0008, U+000C, U+000A, U+000D, U+0009, U+000B |
| `\` *ooo* | the code point (or byte) with octal value *ooo*, one to three octal digits |
| `\x` *hh* | the code point (or byte) with hexadecimal value *hh*, exactly two digits |
| `\N{` *name* `}` (*str*) | the code point with that Unicode name or name alias |
| `\u` *xxxx* (*str*) | the code point with hexadecimal value *xxxx*, exactly four digits |
| `\U` *xxxxxxxx* (*str*) | the code point with hexadecimal value *xxxxxxxx*, exactly eight digits, at most 10FFFF |

Errors in escape sequences raise a `SyntaxError` exception whose message is
"(unicode error) '*codec*' codec can't decode bytes in position *i*-*j*:
*reason*", where *codec* is `unicodeescape` for a `str` literal, *i* and *j*
are the positions of the first and last code point of the faulty escape within
the literal's contents, and *reason* is `truncated \xXX escape`, `truncated
\uXXXX escape`, `truncated \UXXXXXXXX escape`, `illegal Unicode character`, or
`unknown Unicode character name`; for a bytes literal the message is "(value
error) invalid \x escape at position *i*".

An octal escape whose value exceeds 0o377 in a `str` literal produces the code
point and issues a `SyntaxWarning` ("\"\\*ooo*\" is an invalid octal escape
sequence. Such sequences will not work in the future. Did you mean \"\\\\*ooo*\"?
A raw string is also an option."). Any other backslash followed by a code
point is kept unchanged (both the backslash and the code point) and issues a
`SyntaxWarning` ("\"\\*c*\" is an invalid escape sequence. Such sequences will
not work in the future. Did you mean \"\\\\*c*\"? A raw string is also an
option."). A compile-time warning is issued through HostWarn (Annex B) with the
file name and line of the literal.

#### 12.5.4 Literal concatenation

Adjacent string literals, separated only by whitespace, comments, or (within
brackets) line terminators, are concatenated at compile time into one literal,
which may combine any prefixes except that bytes literals can be concatenated
only with bytes literals ("cannot mix bytes and nonbytes literals"). A
concatenation that contains an f-string is an f-string; one that contains a
t-string is a t-string, and a t-string may be concatenated only with t-strings
("cannot mix t-string literals with string or bytes literals").

#### 12.5.5 Static Semantics: StringValue

The StringValue of a string literal is the `str` (or `bytes`) whose code points
(or bytes) are those of its contents after escape processing, with the
concatenation of 12.5.4 applied. Equal literals in one code object may evaluate
to the same object.

#### 12.5.6 f-strings

An f-string is a sequence of literal parts and *replacement fields*:

```text
fstring:            fstring_start fstring_part* fstring_end
fstring_part:       fstring_middle | "{{" | "}}" | replacement_field
replacement_field:  "{" annotated_expr ["="] ["!" conversion] [":" format_spec] "}"
annotated_expr:     star_expressions | yield_expr
conversion:         "s" | "r" | "a"
format_spec:        (fstring_middle | "{{" | "}}" | replacement_field)*
```

In the literal parts, `{{` and `}}` denote `{` and `}`, and escape sequences are
processed as in 12.5.3 unless the prefix includes `r`. The expression of a
replacement field is tokenized as ordinary Python source: it may contain
nested string literals using any quote, including the f-string's own quote,
comments when the f-string is triple-quoted or the expression spans lines
within brackets, and backslashes. A `!` or `:` at bracket depth zero within the
expression ends it; `!=` does not. An `=` directly before `!`, `:`, or `}`
(after optional whitespace) makes the field *self-documenting* (13.2.4.3).

A format spec may contain replacement fields, nested at most two levels deep
counting the outer one ("f-string: expressions nested too deeply"). Other
static errors raise a `SyntaxError` exception with these messages:

| Condition | Message |
| --- | --- |
| a `}` in a literal part that is not doubled | f-string: single '}' is not allowed |
| a replacement field not closed by `}` | f-string: expecting '}' |
| a replacement field with no expression | f-string: valid expression required before '}' (or before '!', ':', '=') |
| a conversion other than `s`, `r`, `a` | f-string: invalid conversion character '*c*': expected 's', 'r', or 'a' |
| a `!` with nothing after it | f-string: missing conversion character |
| a lambda or assignment expression not in parentheses | f-string: lambda expressions are not allowed without parentheses (or: invalid syntax) |

#### 12.5.7 t-strings

A t-string has the syntax of an f-string with the prefix `t` and evaluates to a
%Template% object (23.7) instead of a `str`.

### 12.6 Numeric literals

#### 12.6.1 Integer literals

```text
integer:      decinteger | bininteger | octinteger | hexinteger
decinteger:   nonzerodigit (["_"] digit)* | "0"+ (["_"] "0")*
bininteger:   "0" ("b" | "B") (["_"] bindigit)+
octinteger:   "0" ("o" | "O") (["_"] octdigit)+
hexinteger:   "0" ("x" | "X") (["_"] hexdigit)+
nonzerodigit: "1"..."9"
digit:        "0"..."9"
bindigit:     "0" | "1"
octdigit:     "0"..."7"
hexdigit:     digit | "a"..."f" | "A"..."F"
```

The value of an integer literal is the integer it denotes in its base, of
unbounded size; underscores are ignored. There are no negative literals: `-1`
is the unary minus applied to `1`. A decimal integer literal other than zero
with a leading zero raises a `SyntaxError` exception ("leading zeros in decimal
integer literals are not permitted; use an 0o prefix for octal integers").

#### 12.6.2 Floating-point and imaginary literals

```text
floatnumber:   pointfloat | exponentfloat
pointfloat:    [digitpart] fraction | digitpart "."
exponentfloat: (digitpart | pointfloat) exponent
digitpart:     digit (["_"] digit)*
fraction:      "." digitpart
exponent:      ("e" | "E") ["+" | "-"] digitpart
imagnumber:    (floatnumber | digitpart) ("j" | "J")
```

The value of a floating-point literal is the mathematical value it denotes in
decimal, converted to a `float` by rounding to nearest, ties to even, and
yielding an infinity if it overflows (no exception is raised). Leading zeros in
the integer part are permitted. An imaginary literal produces a `complex` with
real part 0.0 and imaginary part the value of the float or digit part.

#### 12.6.3 Literal boundaries

A numeric literal immediately followed by a code point that could continue an
identifier raises a `SyntaxError` exception: "invalid decimal literal", "invalid
hexadecimal literal", "invalid octal literal", or "invalid binary literal"
according to its base; a digit not valid in the base raises "invalid digit '*d*'
in binary literal" (or "… octal literal"); a literal that ends in `_`, or an `_`
not followed by a digit, raises "invalid decimal literal" (or the base's form).
As an exception, when the following identifier is one of the keywords `and`,
`else`, `for`, `if`, `in`, `is`, `not`, or `or`, the literal ends before it and a
`SyntaxWarning` ("invalid decimal literal", or the base's form) is issued
instead.

### 12.7 Operators and delimiters

The following are operator tokens:

```text
+       -       *       **      /       //      %       @
<<      >>      &       |       ^       ~       :=
<       >       <=      >=      ==      !=
```

The following are delimiter tokens:

```text
(       )       [       ]       {       }
,       :       !       .       ;       =       ->
+=      -=      *=      /=      //=     %=      @=
&=      |=      ^=      >>=     <<=     **=
...
```

A sequence of three dots is the `...` token unless it is part of a longer
sequence of dots, which is read three at a time. The `!` token occurs only in
f-strings and t-strings. A `.` followed by a digit begins a floating-point
literal.
