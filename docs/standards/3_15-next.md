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
| `&&'t'` | the token *t* is required here: if it is not next, a `SyntaxError` exception ("expected '*t*'") is raised |
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

- U+0024 DOLLAR SIGN, U+003F QUESTION MARK, and U+0060 GRAVE ACCENT:
  `SyntaxError` ("invalid syntax");
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

## 13 Expressions

The grammar of expressions is given in Annex A.6. This clause gives each form
and its evaluation. Unless stated otherwise, the operands of an expression are
evaluated from left to right, each completely before the next, and an abrupt
completion of an operand is the completion of the expression.

### 13.1 Atoms

```text
atom:   NAME | 'True' | 'False' | 'None' | strings | NUMBER
      | (tuple | group | genexp) | (list | listcomp) | (dict | set | dictcomp | setcomp)
      | '...'
group:  '(' (yield_expr | named_expression) ')'
```

#### 13.1.1 Runtime Semantics: Evaluation

- *atom* : NAME — return ? LoadName(the identifier, after mangling) (9.3.1).
- `True`, `False`, `None`, `...` — return the object `True`, `False`, `None`, or
  `Ellipsis`.
- NUMBER — return the value of the literal (12.6): an `int`, a `float`, or a
  `complex`.
- *strings* — 13.2.4.
- *group* — return the result of evaluating the enclosed expression. A
  parenthesized expression is not a tuple unless it contains a comma.

### 13.2 Displays

#### 13.2.1 Tuple and list displays

```text
tuple:  '(' [star_named_expression ',' [star_named_expressions]] ')'
list:   '[' [star_named_expressions] ']'
```

1. Let *items* be an empty List.
2. For each element *e*, in order:
   1. If *e* is `*` *expr*: let *v* be the result of evaluating *expr*; if
      GetIterator(*v*) would raise a `TypeError` because *v* is not iterable,
      raise a `TypeError` exception ("Value after * must be an iterable, not
      *tname*(*v*)"); otherwise append the elements of ? IterateToList(*v*) to
      *items*.
   2. Else, append the result of evaluating *e* to *items*.
3. Return a new tuple (or list) whose elements are *items*.

The display `()` evaluates to the empty tuple. A tuple can also be written
without parentheses where an expression list is allowed (13.15).

#### 13.2.2 Set displays

```text
set:  '{' star_named_expressions '}'
```

1. Let *s* be a new empty `set`.
2. For each element *e*, in order: if *e* is `*` *expr*, for each element *x* of
   ? IterateToList(the result of evaluating *expr*), perform ? SetAdd(*s*, *x*);
   otherwise perform ? SetAdd(*s*, the result of evaluating *e*).
3. Return *s*.

`{}` is an empty dictionary, not a set. SetAdd (26.3) keeps an element already
present and does not replace it with an equal one.

#### 13.2.3 Dictionary displays

```text
dict:  '{' [double_starred_kvpairs] '}'
double_starred_kvpair:  '**' bitwise_or | kvpair
kvpair:  expression ':' expression
```

1. Let *d* be a new empty `dict`.
2. For each item, in order:
   1. If the item is *k* `:` *v*: let *key* be the result of evaluating *k*,
      then let *value* be the result of evaluating *v*, and perform
      ? DictSetItem(*d*, *key*, *value*).
   2. If the item is `**` *expr*: let *m* be the result of evaluating *expr*,
      and perform ? DictMerge(*d*, *m*, **false**).
3. Return *d*.

DictSetItem keeps the first key object and replaces the value when an equal key
is already present (26.1). DictMerge(*d*, *m*, *forCall*):

1. If *m* is a `dict` (or `frozendict`), for each (*key*, *value*) of *m* in
   order, perform the step 4 action.
2. Let *keys* be ? GetAttribute(*m*, `"keys"`), treating an `AttributeError`
   as **absent**. If it is **absent**, raise a `TypeError` exception
   ("'*tname*(*m*)' object is not a mapping"), or for a call ("Value after **
   must be a mapping, not *tname*(*m*)" — 13.3.4).
3. For each *key* of ? IterateToList(? Call(*keys*, «»)): let *value* be
   ? GetItem(*m*, *key*) and perform the step 4 action.
4. Action: if *forCall* is **true** and *key* is not a `str`, raise a
   `TypeError` exception ("keywords must be strings"); if *forCall* is **true**
   and *d* already has *key*, raise the duplicate-keyword error of 13.3.4;
   otherwise perform ? DictSetItem(*d*, *key*, *value*).

#### 13.2.4 String literals and f-strings

##### 13.2.4.1 Plain literals

A concatenation of string literals without an f-string or t-string evaluates to
its StringValue (12.5.5).

##### 13.2.4.2 f-strings

An f-string evaluates to a new `str`:

1. Let *parts* be an empty List of strings.
2. For each part, in order:
   1. A literal part appends its text.
   2. A replacement field with expression *e*, conversion *c*, and format spec
      *fs*:
      1. Let *v* be the result of evaluating *e*. (A field whose expression is a
         `yield` expression or a starred expression list evaluates it as in
         13.15.)
      2. If the field is self-documenting (13.2.4.3), append its text.
      3. If *c* is `s`, set *v* to ? ToStr(*v*); if `r`, to ? ToRepr(*v*); if
         `a`, to ? ASCII(*v*) (19.3).
      4. If the field has a format spec, let *spec* be the string formed by
         evaluating the parts of *fs* in the same way (including its nested
         replacement fields); otherwise let *spec* be `""`.
      5. Append ? Format(*v*, *spec*) (7.5.8).
3. Return the concatenation of *parts*.

##### 13.2.4.3 Self-documenting fields

In a replacement field `{`*expr*`=`…`}`, the text of *expr* and the `=`, with
the whitespace around them exactly as written, is inserted before the value. If
the field has neither a conversion nor a format spec, the conversion `r` is
used.

#### 13.2.5 t-strings

A t-string evaluates to a new %Template% object (23.7): its `strings` are the
literal parts (with `""` between adjacent replacement fields and at the ends),
and its `interpolations` are new %Interpolation% objects, one per replacement
field, in order, with `value` the result of evaluating the expression,
`expression` the text of the expression, `conversion` the conversion letter or
`None`, and `format_spec` the evaluated format spec string (or `""`). The
value is not converted or formatted. A self-documenting field adds its text to
the preceding literal part and uses the conversion `r` when it has neither a
conversion nor a format spec.

#### 13.2.6 Comprehensions and generator expressions

```text
listcomp: '[' named_expression for_if_clauses ']'
setcomp:  '{' named_expression for_if_clauses '}'
dictcomp: '{' kvpair for_if_clauses '}' | '{' '**' bitwise_or for_if_clauses '}'
genexp:   '(' (assignment_expression | expression !':=') for_if_clauses ')'
for_if_clauses: for_if_clause+
for_if_clause:  ['async'] 'for' star_targets 'in' ~ disjunction ('if' disjunction)*
```

The element of a list or set comprehension or generator expression may be a
starred expression `*e`, and the element of a dictionary comprehension may be
`**e`; each contributes all items of its value (PEP 798 semantics, as in
13.2.1–13.2.3).

A comprehension is evaluated as follows:

1. Evaluate the iterable of the first `for` clause in the enclosing scope; let
   *it* be ? GetIterator of its value (or ? GetAsyncIterator for `async for`).
2. Create the comprehension's scope (8.6), with its own bindings for its
   targets.
3. For a generator expression, return a new generator object (27.2) whose body
   runs steps 4–5 with *it*, yielding each element instead of collecting it.
4. Run the clauses as nested loops: a `for` clause iterates (7.7.2) over its
   iterator (the clauses after the first evaluate their iterable each time they
   are reached), assigning each item to its targets (14.2); an `if` clause
   continues with the next clause only if ToBoolean of its condition is
   **true**.
5. At the innermost point, evaluate the element and add it to the result: append
   to a list, SetAdd to a set, DictSetItem (key evaluated before value) to a
   dict, or yield it.
6. Return the new list, set, or dict.

A comprehension in an `async def` function that contains `async for` or
`await` is an *asynchronous comprehension*; it is awaited where it occurs. An
asynchronous comprehension outside an asynchronous function raises a
`SyntaxError` exception ("asynchronous comprehension outside of an
asynchronous function"). A generator expression containing `async for` or
`await` creates an asynchronous generator (27.5).

Static Semantics: Early Errors.

- A `yield` or `yield from` expression in a comprehension: "'yield' inside list
  comprehension" (or "set comprehension", "dict comprehension", "generator
  expression").
- A generator expression that is not the sole argument of a call and is not
  parenthesized: "Generator expression must be parenthesized".
- An element `**e` in a list comprehension or generator expression: "cannot
  use dict unpacking in list comprehension" (or "… in generator expression").
  (`{**e for …}` is a dictionary comprehension.)
- An unparenthesized tuple as the element: "did you forget parentheses around
  the comprehension target?".

### 13.3 Primaries

```text
primary:
    | primary '.' NAME
    | primary genexp
    | primary '(' [arguments] ')'
    | primary '[' slices ']'
    | atom
```

#### 13.3.1 Attribute references

`primary.name` evaluates *primary* to *o* and returns ? GetAttribute(*o*,
*name*), with *name* mangled (8.8).

#### 13.3.2 Subscriptions

`primary[slices]` evaluates *primary* to *o*, then the subscript to *key*, and
returns ? GetItem(*o*, *key*). The subscript is:

- a single expression: its value;
- a slice `[lower] ':' [upper] [':' [step]]`: a new `slice` object (25.4)
  whose omitted parts are `None`;
- a comma-separated list, possibly containing slices and starred expressions:
  a new tuple of the values, with starred items expanded as in 13.2.1.

#### 13.3.3 Slicings

A slice is a subscript whose key is a `slice` object; there is no separate
slicing protocol. A sequence's `__getitem__` interprets the slice by the
algorithm SliceIndices (25.4.2).

#### 13.3.4 Calls

```text
arguments:  args [','] &')'
args:  ','.(starred_expression | (assignment_expression | expression !':=') !'=')+ [',' kwargs] | kwargs
kwargs: ','.kwarg_or_starred+ ',' ','.kwarg_or_double_starred+ | ','.kwarg_or_starred+ | ','.kwarg_or_double_starred+
kwarg_or_starred: NAME '=' expression | starred_expression
kwarg_or_double_starred: NAME '=' expression | '**' expression
```

1. Let *f* be the result of evaluating *primary*.
2. Let *args* be an empty List and *kw* a new empty `dict`.
3. For each argument, in source order:
   1. A positional argument *e*: append its value to *args*.
   2. `*e`: let *v* be its value; if *v* is not iterable, raise a `TypeError`
      exception ("Value after * must be an iterable, not *tname*(*v*)");
      append the elements of ? IterateToList(*v*) to *args*.
   3. `name=e`: let *v* be its value; if *kw* has *name*, raise the
      duplicate-keyword error; set *kw*[*name*] to *v*.
   4. `**e`: let *m* be its value; if *m* is not a mapping (has no `keys`),
      raise a `TypeError` exception ("Value after ** must be a mapping, not
      *tname*(*m*)"); otherwise perform ? DictMerge(*kw*, *m*, **true**).
4. Return ? Call(*f*, *args*, the pairs of *kw* in order).

The duplicate-keyword error is a `TypeError` exception ("*FunctionStr*(*f*) got
multiple values for keyword argument '*name*'"). FunctionStr(*f*) is the
function's `__qualname__` (for a bound method, that of its `__func__`), prefixed
by its `__module__` and `"."` when `__module__` is a `str` other than
`"builtins"`, followed by `"()"`; for a built-in function it is its `__name__`
followed by `"()"`; for any other callable it is *repr*(*f*).

Static Semantics: Early Errors. "keyword argument repeated: *name*" if two
`name=` arguments of one call have the same name; "positional argument follows
keyword argument" and "positional argument follows keyword argument unpacking"
and "iterable argument unpacking follows keyword argument unpacking" for the
corresponding orderings; "expression cannot contain assignment, perhaps you
meant \"==\"?" for `f(a.b=1)`.

### 13.4 The `await` expression

```text
await_primary: 'await' primary | primary
```

`await e` is permitted only in the body of an `async def` function (and in
asynchronous comprehensions there): elsewhere it raises a `SyntaxError`
exception ("'await' outside function" at module level, and "'await' outside
async function" in a non-async function).

1. Let *v* be the result of evaluating *e*.
2. Let *it* be ? GetAwaitable(*v*) (7.7.5).
3. Return ? YieldFrom(*it*) (13.16.3), delegating suspension to the awaiting
   coroutine's caller.

### 13.5 The power operator

```text
power: await_primary '**' factor | await_primary
```

The power operator binds more tightly than unary operators on its left and less
tightly than unary operators on its right: `-2 ** 2` is `-(2 ** 2)` and
`2 ** -1` is `2 ** (-1)`. It groups from right to left. `x ** y` returns
? BinaryOp(*x*, *y*, `**`).

### 13.6 Unary arithmetic and bitwise operations

```text
factor: '+' factor | '-' factor | '~' factor | power
```

`-x`, `+x`, and `~x` return ? UnaryOp(*x*, *op*) (7.6.4).

### 13.7 Binary arithmetic operations

```text
term: term '*' factor | term '/' factor | term '//' factor | term '%' factor | term '@' factor | factor
sum:  sum '+' term | sum '-' term | term
```

Each form evaluates its left operand, then its right operand, and returns
? BinaryOp(*left*, *right*, *op*) (7.6.2). Clause 22 specifies the numeric
results, clause 25 sequence concatenation and repetition, and clause 23 the
`%` formatting of strings.

### 13.8 Shifting operations

```text
shift_expr: shift_expr '<<' sum | shift_expr '>>' sum | sum
```

As 13.7, with the operators `<<` and `>>`.

### 13.9 Binary bitwise operations

```text
bitwise_and: bitwise_and '&' shift_expr | shift_expr
bitwise_xor: bitwise_xor '^' bitwise_and | bitwise_and
bitwise_or:  bitwise_or '|' bitwise_xor | bitwise_xor
```

As 13.7, with the operators `&`, `^`, and `|`.

### 13.10 Comparisons

```text
comparison: bitwise_or compare_op_bitwise_or_pair+ | bitwise_or
comp_op: '==' | '!=' | '<' | '<=' | '>' | '>=' | 'in' | 'not' 'in' | 'is' | 'is' 'not'
```

#### 13.10.1 Runtime Semantics: Evaluation

A comparison `a op₁ b op₂ c … opₙ z` is evaluated as follows; each operand is
evaluated at most once.

1. Let *left* be the result of evaluating *a*.
2. For each *opᵢ* and right operand *r*, in order:
   1. Let *right* be the result of evaluating *r*.
   2. Let *result* be ? CompareOp(*left*, *right*, *opᵢ*).
   3. If *i* < *n* and ? ToBoolean(*result*) is **false**, return *result*.
   4. Set *left* to *right*.
3. Return *result*.

CompareOp(*x*, *y*, *op*):

- for `<`, `<=`, `==`, `!=`, `>`, `>=`: ? RichCompare(*x*, *y*, *op*);
- for `in`: `True` if ? Contains(*y*, *x*) (7.8.3) is **true**, else `False`;
- for `not in`: the negation of `in`;
- for `is`: `True` if SameObject(*x*, *y*), else `False`; `is not` negates it.

A comparison with `is` or `is not` where an operand is a literal other than
`None`, `True`, `False`, or `...` issues a `SyntaxWarning` at compile time
("\"is\" with '*type*' literal. Did you mean \"==\"?", or "\"is not\" with
'*type*' literal. Did you mean \"!=\"?").

### 13.11 Boolean operations

```text
disjunction: conjunction ('or' conjunction)+ | conjunction
conjunction: inversion ('and' inversion)+ | inversion
inversion:   'not' inversion | comparison
```

- `not x`: return `False` if ? ToBoolean(*x*) is **true**, and `True` otherwise.
- `x and y`: let *v* be the value of *x*; if ? ToBoolean(*v*) is **false**,
  return *v*; otherwise return the value of *y*.
- `x or y`: let *v* be the value of *x*; if ? ToBoolean(*v*) is **true**,
  return *v*; otherwise return the value of *y*.

### 13.12 Assignment expressions

```text
assignment_expression: NAME ':=' ~ expression
named_expression: assignment_expression | expression !':='
```

`name := e` evaluates *e* to *v*, performs StoreName(*name*, *v*) in the scope
determined by 8.6, and returns *v*. Static Semantics: an unparenthesized
assignment expression is not allowed as an expression statement, as the value
of an assignment or annotated assignment, as a keyword argument value, or as a
default value ("invalid syntax"); its target must be a name ("cannot use
assignment expressions with *what*").

### 13.13 Conditional expressions

```text
expression: disjunction 'if' disjunction 'else' expression | disjunction | lambdef
```

`x if c else y` evaluates *c* first; if ? ToBoolean of its value is **true**, it
returns the value of *x*, and otherwise the value of *y*. The other operand is
not evaluated. A conditional expression without `else` raises a `SyntaxError`
exception ("expected 'else' after 'if' expression").

### 13.14 Lambdas

```text
lambdef: 'lambda' [lambda_params] ':' expression
```

A lambda expression creates a function object (16.2) whose name is
`"<lambda>"`, whose parameters are *lambda_params* (as 16.1 specifies for
`def`, without annotations), and whose body returns the value of
*expression*. It is evaluated as a `def` statement (16.1.2) except that no name
is bound and the function is returned.

### 13.15 Expression lists

```text
star_expressions: star_expression (',' star_expression)+ [','] | star_expression ',' | star_expression
star_expression:  '*' bitwise_or | expression
```

An expression list containing at least one comma, or a starred item, evaluates
to a new tuple as 13.2.1 specifies. A single expression without a comma
evaluates to its value. A starred expression is allowed only in an expression
list, a display, a subscript, or an argument list ("can't use starred
expression here"), and a bare `*e` alone is not an expression list ("can't use
starred expression here").

### 13.16 Yield expressions

```text
yield_expr: 'yield' 'from' expression | 'yield' [star_expressions]
```

A `yield` expression is allowed only in the body of a function (making it a
generator function, or an asynchronous generator function in an `async def`),
or as the sole content of a parenthesized expression in such a body; elsewhere
it raises a `SyntaxError` exception ("'yield' outside function"). In an
`async def` function, `yield from` raises ("'yield from' inside async
function"). In a class body or a function's annotations it raises the errors
of 8.7.

#### 13.16.1 `yield` *expression*

1. Let *v* be the value of the expression list, or `None` if it is omitted.
2. Suspend the running generator frame (9.4), delivering *v* to the code that
   resumed it.
3. When the generator is resumed:
   1. by `__next__` or `send(x)`: return `None` or *x*;
   2. by `throw(e)`: return a raise completion with *e*;
   3. by `close()`: return a raise completion with a new `GeneratorExit`
      exception.

#### 13.16.2 Asynchronous generators

In an asynchronous generator, `yield v` delivers *v* through the awaitable
returned by `__anext__` or `asend` (27.5).

#### 13.16.3 YieldFrom ( *it* )

`yield from e` evaluates *e*, lets *it* be ? GetIterator of its value, and
returns ? YieldFrom(*it*); `await` uses YieldFrom with an awaitable's
iterator.

1. Let *received* be `None` and *mode* be **send**.
2. Repeat:
   1. If *mode* is **send**: if *received* is `None`, let *r* be IteratorStep-like
      Call of `__next__` of *it*; otherwise let *r* be ? CallSpecial(*it*,
      `"send"`, «*received*»), calling the method by ordinary attribute lookup.
   2. If *mode* is **throw** with exception *e*:
      1. If *e* is a `GeneratorExit`: let *close* be the `close` attribute of
         *it*, if any; call it; then return a raise completion with *e*.
      2. Let *throw* be the `throw` attribute of *it*; if there is none, return
         a raise completion with *e*.
      3. Let *r* be Call(*throw*, «*e*»).
   3. If *r* is a raise completion with a `StopIteration` exception *s*, return
      *s*.`value`.
   4. If *r* is any other raise completion, return *r*.
   5. Suspend, delivering the value of *r* to the resumer. When resumed with
      *x* by `send`, set *received* to *x* and *mode* to **send**; when resumed
      by `throw(e)`, set *mode* to **throw** with *e*; when resumed by
      `close()`, set *mode* to **throw** with a new `GeneratorExit`.

### 13.17 Evaluation order

Expressions are evaluated from left to right. In an assignment, the right-hand
side is evaluated before the targets. The following lists the order of
evaluation for some forms, where the numbers give the order:

```text
expr1, expr2, expr3, expr4
(expr1, expr2, expr3, expr4)
{expr1: expr2, expr3: expr4}
expr1 + expr2 * (expr3 - expr4)
expr1(expr2, expr3, *expr4, **expr5)
expr3, expr4 = expr1, expr2
```

### 13.18 Operator precedence

From lowest to highest binding:

| Operators | Description |
| --- | --- |
| `:=` | assignment expression |
| `lambda` | lambda expression |
| `if` – `else` | conditional expression |
| `or` | Boolean OR |
| `and` | Boolean AND |
| `not x` | Boolean NOT |
| `in`, `not in`, `is`, `is not`, `<`, `<=`, `>`, `>=`, `!=`, `==` | comparisons |
| `\|` | bitwise OR |
| `^` | bitwise XOR |
| `&` | bitwise AND |
| `<<`, `>>` | shifts |
| `+`, `-` | addition and subtraction |
| `*`, `@`, `/`, `//`, `%` | multiplication, matrix multiplication, divisions, remainder |
| `+x`, `-x`, `~x` | positive, negative, bitwise NOT |
| `**` | exponentiation (groups right to left; see 13.5) |
| `await x` | await expression |
| `x[…]`, `x(…)`, `x.attr` | subscription, slicing, call, attribute reference |
| `(…)`, `[…]`, `{…}`, literals | binding or parenthesized expression, displays |

## 14 Simple Statements

```text
simple_stmts: simple_stmt !';' NEWLINE | ';'.simple_stmt+ [';'] NEWLINE
```

Several simple statements may share a logical line, separated by `;`. They are
executed in order; an abrupt completion of one ends the line.

### 14.1 Expression statements

An expression statement evaluates its expression list (13.15) and discards the
value, except in interactive input (17.6.2), where a value other than `None` is
passed to the host hook HostDisplay (Annex B). An expression statement that is
a bare `yield` expression is the yield of 13.16.

### 14.2 Assignment statements

```text
assignment: (star_targets '=')+ (yield_expr | star_expressions) !'='
star_targets: star_target !',' | star_target (',' star_target)* [',']
star_target: '*' (!'*' star_target) | target_with_star_atom
target_with_star_atom: t_primary '.' NAME !t_lookahead | t_primary '[' slices ']' !t_lookahead | star_atom
star_atom: NAME | '(' target_with_star_atom ')' | '(' [star_targets_tuple_seq] ')' | '[' [star_targets_list_seq] ']'
```

#### 14.2.1 Runtime Semantics: Evaluation

1. Let *v* be the value of the right-hand side.
2. For each target list, from left to right, perform ? AssignTarget(*target*,
   *v*).

#### 14.2.2 AssignTarget ( *target*, *v* )

1. If *target* is a name, perform ? StoreName(*name*, *v*) (9.3.5).
2. If *target* is `primary.name`: evaluate *primary* to *o*, then perform
   ? SetAttribute(*o*, *name*, *v*).
3. If *target* is `primary[subscript]`: evaluate *primary* to *o*, then the
   subscript to *key* (13.3.2), then perform ? SetItem(*o*, *key*, *v*).
4. If *target* is a parenthesized or bracketed target list *t₁*, …, *tₙ*:
   perform ? UnpackTargets(the targets, *v*).

UnpackTargets(*targets*, *v*):

1. Let *k* be the number of targets, and let *s* be the index of the starred
   target, if any.
2. If GetIterator(*v*) would fail because *v* is not iterable, raise a
   `TypeError` exception ("cannot unpack non-iterable *tname*(*v*) object").
3. Let *it* be ? GetIterator(*v*).
4. If there is no starred target:
   1. Take *k* items from *it* with IteratorStep. If it is exhausted after *j*
      < *k* items, raise a `ValueError` exception ("not enough values to unpack
      (expected *k*, got *j*)").
   2. If ? IteratorStep(*it*) is not **done**, raise a `ValueError` exception
      ("too many values to unpack (expected *k*, got *n*)") when *v* is a list
      or tuple of length *n*, and ("too many values to unpack (expected *k*)")
      otherwise.
5. If there is a starred target at index *s*:
   1. Take *s* items; then collect all remaining items into a new list *rest*.
   2. If fewer than *k* − 1 items were obtained in total, raise a `ValueError`
      exception ("not enough values to unpack (expected at least *k* − 1, got
      *j*)").
   3. The last *k* − 1 − *s* items of *rest* are removed from it and become the
      items of the targets after the starred one; the starred target receives
      the list *rest*.
6. Assign the items to the targets from left to right with AssignTarget.

Static Semantics: Early Errors. "multiple starred expressions in assignment";
"starred assignment target must be in a list or tuple" for a lone starred
target; "cannot assign to *what*" for a target that is a literal, call,
operator expression, or other non-target expression, where *what* names it
(for example `literal`, `function call`, `expression`, `True`, `None`,
`__debug__`, `f-string expression`), with " here. Maybe you meant '==' instead
of '='?" appended when the target is a comparison-like expression in a
statement; "cannot assign to *keyword*" for a keyword.

### 14.3 Augmented assignment statements

```text
augassign: '+=' | '-=' | '*=' | '@=' | '/=' | '%=' | '&=' | '|=' | '^=' | '<<=' | '>>=' | '**=' | '//='
```

`target op= expr`, where *target* is a single name, attribute reference, or
subscription:

1. If *target* is `primary.name` or `primary[subscript]`, evaluate *primary*
   (and the subscript) once.
2. Let *old* be the current value of the target (? LoadName, ? GetAttribute, or
   ? GetItem).
3. Let *v* be the value of *expr*.
4. Let *new* be ? InPlaceOp(*old*, *v*, *op*) (7.6.3).
5. Store *new* in the target (? StoreName, ? SetAttribute, or ? SetItem), using
   the objects evaluated in step 1.

Static Semantics: a target that is a list, tuple, or other expression raises
"'*what*' is an illegal expression for augmented assignment".

### 14.4 Annotated assignment statements

```text
assignment: NAME ':' expression ['=' annotated_rhs]
          | ('(' single_target ')' | single_subscript_attribute_target) ':' expression ['=' annotated_rhs]
```

1. If the target is an attribute reference or subscription, evaluate its
   *primary* (and subscript) for its side effects, even without a value.
2. If there is a value, evaluate it to *v* (a tuple when it is an unparenthesized
   expression list) and perform ? AssignTarget(*target*, *v*).
3. The annotation is not evaluated. In a module or class scope, the annotation
   of a simple name target is recorded for the scope's `__annotate__` function
   (16.6). In a function scope, the annotation is never evaluated, and the
   target name is classified **local** (8.2).

Static Semantics: "only single target (not list) can be annotated" and
"only single target (not tuple) can be annotated".

### 14.5 The `assert` statement

```text
assert_stmt: 'assert' expression [',' expression]
```

`assert e` and `assert e, m`:

1. If the implementation runs with assertions disabled (Annex D), do nothing.
2. If ? ToBoolean(the value of *e*) is **true**, return.
3. If *m* is present, raise `AssertionError` called with the value of *m*;
   otherwise raise `AssertionError` with no arguments.

The value of `__debug__` (19.1) is `True` exactly when assertions are enabled.
An assertion whose test is a non-empty parenthesized tuple issues a compile-time
`SyntaxWarning` ("assertion is always true, perhaps remove parentheses?").

### 14.6 The `pass` statement

`pass` does nothing.

### 14.7 The `del` statement

```text
del_stmt: 'del' del_targets &(';' | NEWLINE)
```

Each target is deleted from left to right: a name by ? DeleteName (9.3.5); an
attribute reference by ? DeleteAttribute (7.3.9); a subscription by
? DeleteItem (7.8.2); a parenthesized or bracketed target list by deleting
each of its elements. Static Semantics: "cannot delete *what*" for other
expressions, including starred ones ("cannot delete starred").

### 14.8 The `raise` statement

```text
raise_stmt: 'raise' expression ['from' expression] | 'raise'
```

1. If there is no expression:
   1. Let *e* be the current handled exception (9.5). If it is `None`, raise a
      `RuntimeError` exception ("No active exception to reraise").
   2. Return a raise completion with *e*, keeping its traceback.
2. Let *e* be ? MakeException(the value of the first expression).
3. If there is a `from` clause, let *c* be the value of its expression:
   1. If *c* is `None`, set *cause* to `None`.
   2. Else let *cause* be ? MakeException(*c*), raising a `TypeError` exception
      ("exception causes must derive from BaseException") if *c* is neither an
      exception class nor an exception instance.
   3. Set *e*.`__cause__` to *cause* and *e*.`__suppress_context__` to `True`.
4. Return a raise completion with *e* (18.1).

MakeException(*x*):

1. If *x* is a class that is a subclass of `BaseException`, let *r* be ? Call(*x*,
   «»); if *r* is not an instance of `BaseException`, raise a `TypeError`
   exception ("calling *repr*(*x*) should have returned an instance of
   BaseException, not *repr*(Type(*r*))"); return *r*.
2. If *x* is an instance of `BaseException`, return *x*.
3. Raise a `TypeError` exception ("exceptions must derive from BaseException").

### 14.9 The `return` statement

`return [expr]` returns a **return** completion whose value is the value of
*expr*, or `None`. Clause 15.4 specifies how `finally` clauses run on the way
out. Static Semantics: "'return' outside function". In a generator,
`return v` ends the iteration with `StopIteration(v)` (27.2); in an
asynchronous generator a `return` with a value raises ("'return' with value in
async generator").

### 14.10 The `break` statement

`break` returns a **break** completion, which ends the nearest enclosing `for`
or `while` loop (15.2, 15.3). Static Semantics: "'break' outside loop" when the
statement is not within a loop of the same function or class body.

### 14.11 The `continue` statement

`continue` returns a **continue** completion, which starts the next iteration of
the nearest enclosing loop. Static Semantics: "'continue' not properly in loop".

A `return`, `break`, or `continue` statement that would leave a `finally`
block issues a compile-time `SyntaxWarning` ("'return' in a 'finally' block",
and likewise for `break` and `continue`).

### 14.12 The `import` statement

```text
import_stmt: ["lazy"] import_name | ["lazy"] import_from
import_name: 'import' dotted_as_names
import_from: 'from' ('.' | '...')* dotted_name 'import' import_from_targets
           | 'from' ('.' | '...')+ 'import' import_from_targets
import_from_targets: '(' import_from_as_names [','] ')' | import_from_as_names !',' | '*'
```

The forms of the `import` statement and their evaluation are specified in clause
17.4, and the `lazy` form in 17.5.

### 14.13 Future statements

A *future statement* is a `from __future__ import` *features* statement that
appears before any other statement of a module, other than its docstring, blank
lines, comments, and other future statements. The features `nested_scopes`,
`generators`, `division`, `absolute_import`, `with_statement`,
`print_function`, `unicode_literals`, `barry_as_FLUFL`, `generator_stop`, and
`annotations` are recognized. All but `annotations` and `barry_as_FLUFL` have
no effect. `annotations` makes every annotation in the module be evaluated as
the string of its source text (16.6.4). `barry_as_FLUFL` makes `<>` the
inequality operator and `!=` a syntax error.

A future statement is also an ordinary import of the `__future__` module (17.4),
which the host provides; when the host has no such module, the statement binds
nothing and is not an error.

Static Semantics: "from `__future__` imports must occur at the beginning of the
file"; "future feature *name* is not defined"; and `braces`: "not a chance".

### 14.14 The `global` and `nonlocal` statements

`global` and `nonlocal` are declarations (8.3). At run time they do nothing.

### 14.15 The `type` statement

```text
type_alias: "type" NAME [type_params] '=' expression
```

`type Name[params] = value` creates a %TypeAliasType% object (29.6) named
`Name` whose type parameters are *params* (16.7) and whose value is computed by
evaluating *value* lazily, in an annotation scope, the first time its
`__value__` attribute is read. It binds the alias to *Name* with StoreName.

## 15 Compound Statements

```text
block: NEWLINE INDENT statements DEDENT | simple_stmts
```

A compound statement's *block* is either an indented sequence of statements or
one line of simple statements after the colon. Evaluating a block evaluates its
statements in order and returns the first abrupt completion, or a normal
completion when all complete normally.

### 15.1 The `if` statement

```text
if_stmt: 'if' named_expression ':' block (elif_stmt | [else_block])
elif_stmt: 'elif' named_expression ':' block (elif_stmt | [else_block])
else_block: 'else' &&':' block
```

The conditions are evaluated in order until one for which ToBoolean is
**true**; its block is evaluated. If none is, the `else` block, if any, is
evaluated.

### 15.2 The `while` statement

```text
while_stmt: 'while' named_expression ':' block [else_block]
```

1. Repeat:
   1. If ? ToBoolean(the value of the condition) is **false**, evaluate the
      `else` block, if any, and return its completion.
   2. Let *r* be the result of evaluating the block.
   3. If *r* is a **break** completion, return a normal completion.
   4. If *r* is a **continue** completion or normal, continue.
   5. Return *r*.

### 15.3 The `for` statement

```text
for_stmt: 'for' star_targets 'in' ~ star_expressions ':' block [else_block]
        | 'async' 'for' star_targets 'in' ~ star_expressions ':' block [else_block]
```

#### 15.3.1 Runtime Semantics: Evaluation

1. Let *it* be ? GetIterator(the value of the expression list).
2. Repeat:
   1. Let *v* be ? IteratorStep(*it*).
   2. If *v* is **done**, evaluate the `else` block, if any, and return its
      completion.
   3. Perform ? AssignTarget(*target*, *v*).
   4. Let *r* be the result of evaluating the block.
   5. If *r* is a **break** completion, return a normal completion.
   6. If *r* is a **return** or **raise** completion, return *r*.

The target remains bound to the last value assigned after the loop. Changing
the iterated object during the loop affects the iteration only as its
iterator's clause specifies (for a `list`, 25.1.5).

#### 15.3.2 The `async for` statement

`async for` is permitted only in an `async def` function ("'async for' outside
async function"). It obtains *it* by ? GetAsyncIterator (7.7.4), and each step
awaits (13.4) the result of calling `__anext__` of *it*; a
`StopAsyncIteration` exception from that await ends the loop as **done**. The
result of `__anext__` must be awaitable ("'async for' received an invalid
object from `__anext__`: *tname*(*r*)").

### 15.4 The `try` statement

```text
try_stmt: 'try' &&':' block finally_block
        | 'try' &&':' block except_block+ [else_block] [finally_block]
        | 'try' &&':' block except_star_block+ [else_block] [finally_block]
except_block: 'except' expression ['as' NAME] ':' block
            | 'except' expressions ':' block
            | 'except' ':' block
except_star_block: 'except' '*' expression ['as' NAME] ':' block
                 | 'except' '*' expressions ':' block
finally_block: 'finally' &&':' block
```

#### 15.4.1 Runtime Semantics: Evaluation of `try` … `except`

1. Let *r* be the result of evaluating the `try` block.
2. If *r* is a raise completion with exception *e*, then
   1. For each `except` clause, in order:
      1. If the clause has no expression, it matches.
      2. Otherwise let *t* be the value of its expression (a tuple when it is an
         unparenthesized list of expressions). If *t* is a class, or a tuple,
         possibly nested, of classes, any of which is not a subclass of
         `BaseException`, raise a `TypeError` exception ("catching classes that
         do not inherit from BaseException is not allowed"); the clause matches
         if IsInstance(*e*, *c*) is **true** for *t* or for some class in *t*.
      3. If the clause matches:
         1. If it has `as` *name*, perform StoreName(*name*, *e*).
         2. Make *e* the handled exception of the frame (9.5), saving the
            previous one.
         3. Let *h* be the result of evaluating the clause's block.
         4. Restore the previous handled exception.
         5. If it has `as` *name*, perform DeleteName(*name*), ignoring an
            unbound name. (This breaks the reference cycle through the
            traceback.)
         6. Set *r* to *h* and go to step 4.
   2. No clause matched: go to step 4 with *r* unchanged.
3. If *r* is a normal completion and there is an `else` block, set *r* to the
   result of evaluating it.
4. If there is a `finally` block, perform FinallyBlock(*r*) and return its
   result; otherwise return *r*.

An exception raised while a handler runs gets the handled exception as its
`__context__` (18.1.2).

#### 15.4.2 FinallyBlock ( *r* )

1. Save *r*. If *r* is a raise completion, its exception is the handled
   exception while the `finally` block runs.
2. Let *f* be the result of evaluating the `finally` block.
3. If *f* is abrupt, return *f* (the saved completion is discarded, and a saved
   exception becomes the `__context__` of a new one).
4. Return *r*.

#### 15.4.3 `except*`

A `try` statement with `except*` clauses handles exception groups (21.4):

1. Let *r* be the result of evaluating the `try` block. If it is not a raise
   completion, continue as in 15.4.1 step 3.
2. Let *e* be its exception. If *e* is not an exception group, let *e* be a new
   `ExceptionGroup` (or `BaseExceptionGroup` if *e* is not an `Exception`) with
   message `""` and the single exception *e*, which is marked *naked*.
3. Let *rest* be *e* and *excs* be an empty List.
4. For each `except*` clause, in order, while *rest* is not `None`:
   1. Let *t* be the value of its expression. If *t* is or contains a subclass
      of `BaseExceptionGroup`, raise a `TypeError` exception ("catching
      ExceptionGroup with except* is not allowed. Use except instead."). If it
      contains a non-exception class, raise the `TypeError` of 15.4.1.
   2. Let (*match*, *rest*) be ? *rest*.`split`(*t*) (21.4.3).
   3. If *match* is not `None`: bind it to the `as` name, make it the handled
      exception, and evaluate the block. If the block raises an exception *x*,
      append *x* to *excs*. (A bare `raise` re-raises *match*.)
5. If *rest* is not `None`, append it to *excs*.
6. If *excs* is empty, the exception is handled: go to step 10.
7. If *e* was naked, propagate *excs*[0] and go to step 10.
8. Let *reraised* be the elements of *excs* that have the same `__traceback__`,
   `__cause__`, `__context__`, and `__notes__` as *e* (they are parts of *e*
   produced by `split`), and *raised* the others, in order. Let *group* be the
   projection of *e* onto the leaf exceptions of *reraised*: the subgroup of *e*
   (21.4.3) containing exactly those leaves, keeping *e*'s nesting, or `None`.
9. If *raised* is empty, propagate *group* (if it is `None`, the exception is
   handled). Otherwise append *group*, if not `None`, to *raised*; propagate the
   only element of *raised* if it has one, and otherwise a new `ExceptionGroup`
   with message `""` and the elements of *raised*.
10. The `else` block does not run when the `try` block raised. Run the
    `finally` block as 15.4.2.

Static Semantics: Early Errors. "cannot have both 'except' and 'except*' on
the same 'try'"; "expected one or more exception types" for `except*:`;
"'break', 'continue' and 'return' cannot appear in an except* block"; "default
'except:' must be last"; "multiple exception types must be parenthesized when
using 'as'"; "expected 'except' or 'finally' block" for a `try` with neither.

### 15.5 The `with` statement

```text
with_stmt: 'with' '(' ','.with_item+ ','? ')' ':' block
         | 'with' ','.with_item+ ':' block
         | 'async' 'with' '(' ','.with_item+ ','? ')' ':' block
         | 'async' 'with' ','.with_item+ ':' block
with_item: expression 'as' star_target &(',' | ')' | ':') | expression
```

#### 15.5.1 Runtime Semantics: Evaluation

A `with` statement with several items behaves as nested `with` statements, one
item each. For one item `with m as t: block`:

1. Let *manager* be the value of *m*.
2. Let *ctx* be ? EnterContext(*manager*) (7.9.1).
3. If there is a target, perform AssignTarget(*t*, *ctx*.[[Value]]); if it
   completes abruptly, set *r* to that completion and go to step 5.
4. Let *r* be the result of evaluating the block.
5. If *r* is a raise completion with exception *e*:
   1. Let *x* be ? Call(*ctx*.[[Exit]], «Type(*e*), *e*, *e*.`__traceback__`»),
      with *e* as the handled exception.
   2. If ? ToBoolean(*x*) is **true**, return a normal completion (the
      exception is suppressed).
   3. Return *r*.
6. Otherwise, perform ? Call(*ctx*.[[Exit]], «`None`, `None`, `None`»), and
   return *r* (a **return**, **break**, or **continue** completion still
   leaves the block after `__exit__` runs).

#### 15.5.2 The `async with` statement

`async with` is permitted only in an `async def` function ("'async with'
outside async function"). It uses AsyncEnterContext (7.9.1): it awaits the
result of `__aenter__()` and of `__aexit__(…)` at the points where `with` calls
`__enter__` and `__exit__`.

### 15.6 The `match` statement

```text
match_stmt: "match" subject_expr ':' NEWLINE INDENT case_block+ DEDENT
subject_expr: star_named_expression ',' star_named_expressions? | named_expression
case_block: "case" patterns guard? ':' block
guard: 'if' named_expression
```

#### 15.6.1 Runtime Semantics: Evaluation

1. Let *subject* be the value of the subject expression (a tuple if it has a
   comma).
2. For each case block, in order:
   1. Let *bindings* be an empty List of (name, value) pairs.
   2. If ? MatchPattern(*pattern*, *subject*, *bindings*) is **true**:
      1. Perform StoreName for each pair of *bindings*, in order.
      2. If there is a guard and ? ToBoolean(its value) is **false**, continue
         with the next case block.
      3. Return the result of evaluating the block.
   3. Otherwise, names bound by a partially successful match may have been
      stored (implementation-defined, Annex D); continue.
3. Return a normal completion.

Static Semantics: Early Errors. An irrefutable case pattern (a capture pattern
or wildcard, possibly in an or-pattern) that is not the last case: "name capture
'*n*' makes remaining patterns unreachable" or "wildcard makes remaining
patterns unreachable". An irrefutable alternative of an or-pattern that is not
the last alternative: "alternative patterns bind different names" when they
bind different names, and the corresponding "makes remaining patterns
unreachable" message otherwise. A name bound twice in one pattern: "multiple
assignments to name '*n*' in pattern". Two starred sub-patterns in one sequence
pattern: "multiple starred names in sequence pattern". Two literal keys of a
mapping pattern that are equal: "mapping pattern checks duplicate key (*repr*)".
A keyword attribute repeated in a class pattern: "attribute name repeated in
class pattern: *name*".

#### 15.6.2 Patterns

```text
patterns: open_sequence_pattern | pattern
pattern: as_pattern | or_pattern
as_pattern: or_pattern 'as' pattern_capture_target
or_pattern: '|'.closed_pattern+
closed_pattern: literal_pattern | capture_pattern | wildcard_pattern | value_pattern
              | group_pattern | sequence_pattern | mapping_pattern | class_pattern
```

MatchPattern(*p*, *subject*, *bindings*) returns **true** or **false**, or
completes abruptly:

- **as pattern** `p as name`: if MatchPattern(*p*, …) is **true**, append
  (*name*, *subject*) and return **true**.
- **or pattern** `p₁ | … | pₙ`: try each alternative in order with a fresh List;
  for the first that matches, append its bindings and return **true**. All
  alternatives bind the same names.
- **literal pattern**: a number, string, or complex literal (`a + bj`, `a - bj`,
  `-a`): return ? RichCompareBool(*subject*, *value*, `==`). `None`, `True`,
  and `False`: return SameObject(*subject*, the constant).
- **capture pattern** `name`: append (*name*, *subject*); return **true**.
- **wildcard pattern** `_`: return **true**.
- **value pattern** `a.b.c`: evaluate the dotted name and return
  ? RichCompareBool(*subject*, *value*, `==`).
- **group pattern** `(p)`: MatchPattern(*p*, …).
- **sequence pattern**: 15.6.3. **mapping pattern**: 15.6.4. **class
  pattern**: 15.6.5.

A complex literal pattern requires a real number on the left of `+`/`-` ("real
number required in complex literal") and an imaginary number on the right
("imaginary number required in complex literal").

#### 15.6.3 Sequence patterns

`[p₁, …, pₙ]`, `(p₁, …, pₙ)`, or `p₁, …, pₙ`, with at most one star pattern
`*name` or `*_`:

1. If *subject* is not a *sequence for matching*, return **false**: its type is
   `list`, `tuple`, `range`, `memoryview`, or a subclass, or a class designated
   a sequence by the host (Annex C), and is not `str`, `bytes`, `bytearray`, or
   a subclass of them.
2. Let *len* be ? Length(*subject*).
3. Without a star pattern: if *len* ≠ *n*, return **false**; otherwise match each
   *pᵢ* against ? GetItem(*subject*, *i*) in order, returning **false** at the
   first failure.
4. With a star pattern at index *s*: if *len* < *n* − 1, return **false**; match
   the patterns before the star against the first items, the patterns after it
   against the last items, and bind the star name (unless `_`) to a new list of
   the items between, in order of the patterns.
5. Return **true**.

#### 15.6.4 Mapping patterns

`{k₁: p₁, …, kₙ: pₙ, **rest}`:

1. If *subject* is not a *mapping for matching* (a `dict`, `frozendict`, or
   %MappingProxyType%, a subclass of these, or a class designated a mapping by
   the host), return **false**.
2. If *n* > 0 and ? Length(*subject*) < *n*, return **false**.
3. Let *get* be ? GetAttribute(*subject*, `"get"`). Evaluate each key *kᵢ* in
   order (literals and value patterns). If two evaluated keys are equal, raise a
   `ValueError` exception ("mapping pattern checks duplicate key (*repr*(*k*))").
4. For each key *k*, in order: let *v* be ? Call(*get*, «*k*, *missing*»), where
   *missing* is a fresh object; if *v* is *missing*, return **false**.
5. Match each *pᵢ* against its value in order, returning **false** at the first
   failure.
6. If `**rest` is present, bind *rest* to a new `dict` with all items of
   *subject* except the matched keys.
7. Return **true**.

#### 15.6.5 Class patterns

`C(p₁, …, pₙ, a₁=q₁, …, aₘ=qₘ)`:

1. Evaluate the name or dotted name *C* to *cls*. If *cls* is not a class, raise
   a `TypeError` exception ("class pattern must refer to a class").
2. If ? IsInstance(*subject*, *cls*) (with `__instancecheck__`, 19.3) is
   **false**, return **false**.
3. If *n* + *m* = 0, return **true**.
4. Let *seen* be an empty set if *n* > 0 and *n* + *m* > 1, and **absent**
   otherwise.
5. If *n* > 0:
   1. Let *ma* be the `__match_args__` attribute of *cls*, if it has one.
   2. If *ma* exists and is not exactly a tuple, raise a `TypeError` exception
      ("*cls*.`__name__`.`__match_args__` must be a tuple (got
      *tname*(*ma*))").
   3. If *ma* does not exist and *cls* is a *self-matching* class (`bool`,
      `bytearray`, `bytes`, `dict`, `float`, `frozendict`, `frozenset`, `int`,
      `list`, `set`, `str`, `tuple`, or a subclass that does not define
      `__match_args__`), the allowed count is 1 and the single positional
      sub-pattern matches *subject* itself; otherwise the allowed count is the
      length of *ma* (0 if absent).
   4. If *n* exceeds the allowed count, raise a `TypeError` exception
      ("*cls*.`__name__`() accepts *a* positional sub-pattern*s* (*n* given)").
   5. For each *i* < *n* (when not self-matching): let *name* be *ma*[*i*]; if it
      is not exactly a `str`, raise a `TypeError` exception ("`__match_args__`
      elements must be strings (got *tname*(*name*))"); perform
      ClassAttr(*name*).
6. For each keyword *aⱼ*, perform ClassAttr(*aⱼ*).
7. Match the sub-patterns against the attribute values obtained, positional
   ones first, in order, returning **false** at the first failure.
8. Return **true**.

ClassAttr(*name*): if *seen* is not **absent** and contains *name*, raise a
`TypeError` exception ("*cls*.`__name__`() got multiple sub-patterns for
attribute *repr*(*name*)"); add *name* to *seen*; let *v* be ? GetAttribute(*subject*,
*name*), and if it raises `AttributeError`, return **false** from the class
pattern. All attributes are obtained before any sub-pattern is matched.
