# Direct source-to-bytecode compilation

The target is one parse of the source that emits executable instructions,
without constructing an executable syntax tree and walking it afterward.
Symbol and label resolution may patch emitted instructions. They must not
reparse the source or traverse an AST. This migration is incomplete.

## Current checkpoint

Constant loads now carry their value as an instruction operand.
The constant path of `BC_LOAD` retains that value onto the machine's operand stack without
calling `eval` or reading the value through an AST node. It shares storage
with branch operands; `Instruction` remains 32 bytes on arm64. The source
unit still owns and traces the constant through its node. Instructions
borrow it, and the executing frame retains the unit.

The compiler recognizes a materialized constant before asking whether its
expression needs machine steps. Name loads keep their existing lookup and
fallback behavior. Source locations, tracing and pause accounting still use
the original node.

This is preparation for a different compiler, not its completion. The parser
still builds `Node` trees. Scope analysis, `compile_expr`, `compile_body`,
metadata queries and several instruction implementations still walk them.
At this stage `BC_EVAL` and `BC_EXEC` still executed trees. No claim of a
single-pass compiler or general speedup follows from this checkpoint.

The second stage records three code properties during parsing: whether the
current function contains a yield, the location of its first valued return
in compiler diagnostic order, and whether a statement writes through a
module or class namespace. Function bodies get their scope record before
binding analysis; binding analysis fills that record and resolves its parent.
Decorators and defaults remain in the enclosing parser context, while
nested function, lambda and class bodies have their own context. Formatted
string fields inherit that context.

This removes the recursive `namespace_bindings` and `check_async_return`
walkers and the generator-detection walk from `compile_generator`. The
return diagnostic still follows binding errors and preserves Python 3.15's
ordering between try suites and handlers. Recording yields before dropping
optimized assertions also fixes generator classification under `-O` and
`-OO`. Symbol binding and instruction emission still traverse trees; this
stage does not claim to have completed the direct compiler.

The third stage gives name loads their own `BC_NAME` instruction. Its
operand holds the spelling and lookup cache; the lookup helpers accept
that record rather than a syntax node. Both constant and name loads now
read their instruction operands directly. A `BC_NAME` cache miss continues on
the machine, including Python namespace lookups and key comparisons,
instead of falling back to `eval`. The instruction still borrows its
source-location node for tracing and diagnostics.

The name record currently lives inside its source node, with the same
ownership and tracing of its cached dictionary key. This extraction adds
no allocation and leaves `Instruction` at 32 bytes and `Node` at 312 bytes
on arm64. Other instructions and the parser still depend on trees. The
next ownership change must move these records into code-owned storage
before those nodes can be removed.

The fourth stage removes tree reads from fused operators. An operator on
operands at hand (a literal, a name, an item of those, or a name's
attribute) compiles to a fused `BC_OPERATE` followed by its plain steps:
the operands' loads and the operator's `BC_BINARY`, `BC_COMPARE` or
`BC_INDEX`. The fused step reads its operands from those loads' operands,
and jumps past them when it computes the result without running Python
code. Otherwise it falls through, and the plain steps evaluate the
operator on the machine. A truth test fuses with the `BC_FALSE` after the
plain steps into `BC_TEST`, sharing its target. Neither step evaluates a
tree or calls Python code, so the machine paths that resumed them after a
call are gone. Literal constants are made when an operand first compiles,
since a comprehension may compile before the pass that makes the rest.
`tests/spec/expressions/operator_operands_once.py` checks that operands
and special methods run once along every fall-through.

The fifth stage applies the same arrangement to assignments. A one-target
assignment to a name or to an item of names and literals, plain or
augmented, whose value is an operand at hand or a fused operator, compiles
to `BC_ASSIGN` followed by its plain steps. The fused step stores into the
name's remembered entry, a list's slot, or a container whose store calls
no Python, and combines augmented numbers natively. Otherwise its plain
steps run; `BC_INPLACE` now tries the same number fast path first. A loop
body consisting of one such assignment runs inside the loop's step, as a
body of one walker step did. These assignments no longer execute their
tree with `BC_EXEC`. A counter's `+=` or `-=` by a literal or name stays
`BC_INCREMENT`. `tests/spec/statements/assignment_operands_once.py`
checks single evaluation along each fall-through.

The sixth stage removes `BC_BLOCK`, the step that ran the statements after
a body's last call as one tree. Each statement now compiles to its own
steps. An operator whose left operand is an operator and whose right one
is at hand compiles the left operand's steps, then `BC_STACKED`, which
takes that value from the stack, or `BC_STACKED_TEST` when it is tested;
both fall through to the plain steps as `BC_OPERATE` and `BC_TEST` do.
String and bytes literals load as constants.
`tests/spec/expressions/computed_left_operand.py` reaches both steps'
computed, fall-through and non-bool paths.

The seventh stage compiles arithmetic, unary operators and comparisons
built only from operands at hand to their steps rather than `BC_EVAL`,
and an assignment of such a value to a target at hand to its plain steps
rather than `BC_EXEC`. Literals make their constants when first compiled.
Tuple displays stay a `BC_EVAL`: building one item by item costs more
than evaluating it whole.
`tests/spec/statements/computed_assignment.py` checks their evaluation
order and single evaluation.

The eighth stage loads `True`, `False`, `None` and `...` as constants, so
operators on them fuse, and compiles a condition's `not` to no step: its
`BC_FALSE` jumps on a true operand instead. A list or tuple display without
starred items compiles its items' steps, then `BC_NEW` with the count,
which takes them from the stack. `tests/spec/compound/negated_conditions.py`
and `tests/spec/expressions/display_items_order.py` cover both.

The ninth stage compiles the last statements handed whole to the walker,
a bare `raise`, `pass`, `break`, `continue`, `global` and `nonlocal`, to
steps of their own. With them `BC_EVAL` and `BC_EXEC` are gone: the
specification tests run neither.

The tenth stage removes the tree walker. `eval`, `execute_statements` and
the statement and call evaluators behind them are deleted, so no statement
or general expression runs from its tree. The paths that still reached
them now run on the machine:

- A fused call step (`BC_CALLF`) finds its callee and arguments only
  where no code runs; otherwise its plain steps run, as an operator's do.
  A method call's plain steps read the method before any argument other
  than a literal, so its getter runs before an argument's `NameError`.
- `BC_INCREMENT` and a `return` or `yield` of a name fall back to plain
  steps in the same way.
- `BC_STORE` stores only into a name. Outside a class body and code that
  can pause, an attribute or item of names and literals is stored by a
  fused `BC_STORE_AT`, which reads them from its plain steps (the
  fourteenth stage, below). Every other target is evaluated as steps
  before `BC_SET_TARGET`.
- Every class body, module body, interactive input and `eval` expression
  runs as a machine program. A class's bases and keywords are always
  argument steps. `exec` of a class body's code calls the body on the
  machine.
- A `del` of an attribute or item evaluates its operands as steps.
- A match pattern's value, class and key expressions are compiled as
  ordinary expression steps (the thirteenth stage, below).

Instruction counts (clang -O2 -flto, callgrind, Linux arm64) against 0.9.0
are lower for every benchmark program except `fib`, which is 1.18% higher;
against the ninth stage they are within 0.26%.

The eleventh stage moves compilation into the parse. Everything the
compiler decides is now known when a statement ends, so it no longer
waits for the passes after the parse:

- The parser collects a module's or class body's annotations as it reads
  each annotated assignment, and marks a comprehension asynchronous by
  counting the awaits and `async for` clauses in its own scope. The walks
  of finished bodies that did both are gone.
- A number's value, a negated number's constant and `F_OPERATOR` are set
  as each statement ends, over the nodes parsed since it began.
- Whether a name loads through a mapping, in a class body or in code of
  `exec()` or `eval()` source, is the program's property, not a flag the
  scope walk set.
- The async generator's `return` error, the compiler's one diagnostic,
  is raised beside scope resolution.

The parser then compiles each function, lambda and class body and each
comprehension as the statement holding it ends, and the module's body as
the parse ends. Compiling `compile()` of the benchmark programs' sources
costs the same number of instructions as before.

The twelfth stage makes statements the unit of emission. A def's or
class's header opens its body's program, and the module's opens at the
parse's start; each simple statement is compiled into the open program as
it ends, and the module holds its last one back until the parse ends,
since an expression there gives the body's value. A compound statement
compiles itself as its clauses are parsed:

- `if` and `elif` emit their test after the condition, their suite as it
  is parsed, and the jump past the rest before the next clause.
- `while` and `for` emit their block and step before the suite, and the
  jump back and the block's end after it.
- `with` enters its items before the suite and exits them after it.
- `match` keeps its subject on the stack and emits each case's pattern and
  guard before the case's suite.
- `try` reads ahead over the token stream to the keywords that follow each
  clause, so it knows before its body whether it has handlers, `except*`
  handlers, an `else` suite or a `finally` block. The `else` suite, parsed
  after the handlers, is placed after them, where the jump past the
  handlers reaches it.

A class body starts its set of conditional annotations in
`class_body_begin`, and a module program begins at its annotation step only
when it has annotations (`Program.entry`), so no body's opening
instructions wait for its end. Expressions are still compiled from their
trees when their statement or clause header ends.

The thirteenth stage compiles match patterns. A case's pattern is a run
of `BC_PATTERN` steps in the order CPython's compiler emits its pattern
opcodes, and the C matchers that walked the pattern tree, with the log
that replayed their Python calls, are deleted:

- Each pattern test leaves a boolean for `BC_FALSE`, whose exit records
  how many values it leaves above the case's slots; a failed case drops
  each depth once, deepest first.
- A case's captures fill one stack slot per name, in first-binding order
  (`pattern_names`), and are stored after the whole pattern matches,
  before the guard. An or-pattern's alternatives bind the same names, so a
  later alternative overwrites a failed one's slots.
- A mapping pattern evaluates its keys, reads `get`, then checks each key
  for a duplicate and looks it up before any sub-pattern; a class pattern
  reads `__match_args__` and every attribute before any sub-pattern. The
  Python calls among these (`get`, getters, `__instancecheck__`,
  `__len__`) are machine calls.

A mixed match program executes 16% fewer instructions than at the twelfth
stage; a failed value sub-pattern of a class pattern costs 4.5% more.

The fourteenth stage, the first part of stage 1 below, moves operands out
of tree links into instructions. A step reads what it executes from its
own fields or from the plain steps after it, and keeps its node only as
its source location:

- Names and attributes are operand records (`NameOperand`,
  `AttributeOperand`) that instructions point to: every name load, store,
  deletion, walrus and keyword argument, and every attribute load, target
  and deletion. An attribute operand keeps its line for a method's lookup.
- A fused step reads its operands from the plain steps that follow it.
  An operator's operation and its operands' shapes are in its arg; an
  assignment, a return, an increment and a store into an attribute or
  item of names (`BC_STORE_AT`) read their names, constants and operator
  from their plain steps.
- A loop's item and an exception handler's name are stored through the
  `BC_STORE` after the loop or match step; an import is a `BC_IMPORT` of
  its record.
- A method call's `BC_CALLN` holds its attribute and says whether its
  object stands in its callee's place; a keyword call's `BC_CALLK` holds a
  tuple of its keywords' names, which its program owns. The call helpers
  below the call step take the method's attribute, not the call's node.
- An unpacking holds its count of targets and its star's index, a tuple
  display its size, a template field its source text and conversion, and
  a comprehension whether its first clause is async.

Against the thirteenth stage (clang -O2, macOS arm64, instructions
retired), `loop` executes 1.5% fewer instructions, `generators` 1.3% and
`nbody` 0.9% fewer; `sort` is 0.02% higher and every other benchmark
program lower.

A fused call reads its callee and arguments from its plain steps, and
its arg says how they lie there; this costs `fib` 3.5% more instructions
and `classes` 1.2% more, which the tuning after the move off the tree is
to recover. A yield of a name or literal reads its plain step. Functions
bind their arguments through a signature record, an array of parameter
names and kinds, built when the definition is compiled; `code.replace()`
of another signature builds its own.

An instruction carries its source line, not a node: a step without one
runs on the line before it, and a trace function sees no line event for
a step that ticks on its definition's line.

A body's scope is its definition record. It owns the body's programs,
signature, code object, name and docstring, and carries what run time
reads of the definition: its line and first decorator's line, its kind,
generator or comprehension kind, flags, and the scopes of its type
parameters and `__annotate__` function. Functions, generators,
machines and the definition steps keep scopes, not nodes. Annotation
steps carry their names, texts and indexes as operands.

A program owns its operands: the constants it loads, and a copy of each
name and attribute name a step reads, with its lookup cache. Those name
operands, in the order their steps were emitted, with what imports and
match captures bind, are the record of the names its code uses;
`co_names` reads them, not the tree. Until the nodes go, a name is held
twice: compiling 20,000 lines of `x = a.b` executes 10% more
instructions and peaks at 24% more memory.

Every statement is analysed as it is parsed, in the scope of the body
that holds it: a simple statement when its line ends, a compound
statement's header before its suite, a definition's decorators,
defaults, bases and annotations before its body. A module's or class's
annotation is analysed at its statement, in the scope of the
`__annotate__` made at the first annotation and attached to the function
once the body ends. An error at a header takes its statement's whole
source when the statement ends. One walk finds named-expression and
symbol table errors alike, in CPython's order; the first waits for the
end of the parse, so that a parse error anywhere wins over it. Free and
cell names are resolved once each line of module statements is
analysed.

Code objects keep their body's scope, and scopes copy the text they
keep (symbol, parameter, type parameter and static attribute names), so
run time reads no tree. A scope tree owns its scopes. A scope's
definition record is filled as its node is complete, and an async
def's first valued return keeps only its line and span, so resolution
reads no node. Once a line of module statements is compiled, analysed
and resolved, the nodes of the line before it are freed; a line of a
def's, class's or suite's statements is freed as soon as it is compiled
and analysed. The parse keeps only a body's first statement while the
body is open (a module's for its docstring and line; a def's or class's
docstring is read as it compiles), the annotations of a module or class,
which its `__annotate__` compiles when the body ends, and the nodes
owning a root scope (a string annotation's). Compiling 20,000 lines of
`x = a.b` peaks at 26 MB, down from 49 MB, 5,000 small functions at
33 MB, down from 47 MB, and a 20,000-line function and class at 46 MB,
down from 124 MB.

The compiler now emits every expression, statement and pattern in the
order the parser reads it. A step that runs before parts read ahead of it is put
in front of them once they are compiled: a fused operator, call, store,
assignment, increment, yield or return step, a display's or template's
new value, a function's making step, a target list's unpack. Parts that
run in another order are rotated into it: a conditional's test before its
value, positional arguments before keywords, an assignment's value before
its targets, a comprehension's element inside its clauses, a mapping pattern's
keys before its sub-patterns, which sink below its lookups. A rotated or
prefixed range jumps only within itself, so moving it relocates only its
own jumps, and its operands move with it, keeping `co_names` in order. A
value is tested after it compiles (an `and`'s or `or`'s left operand
before the parser has read the operator), and an item operand drops its
own fused step when an operator fuses it. No step's shape depends on
context compiled after it. The programs are the same as before this
change, step for step, for every spec test in both execution modes.

The fourteenth stage emits expressions as the parser completes them. A
simple statement at a body's top opens its program for emission; each
literal and name is compiled as it is read, and an operator, attribute,
subscript, slice, call, display, f-string, conditional, lambda without
defaults or comprehension is compiled when the parser completes it, once its
operands were emitted one after another up to the program's end. A node
so compiled records its steps (`Node.steps_at`, `steps_end`), and
compiling it again is no step.

- A negated number is folded as it is parsed.
- An `and` or `or` emits its left operand's test and branch as the parser
  reads the operator, and patches the branch once the right operand is
  emitted.
- A call stays a plain call until an argument makes it general; then the
  steps the general call takes between its arguments are put in after
  those already emitted, and each later argument is added as it ends.
- An augmented assignment to a name keeps its name's load.
- A dictionary or set display emits its new value at its first item and
  adds each item as it ends; its kind is set at its close.
- A conditional expression emits its test and branch after its value,
  rotates them before it, and patches the jump once the alternative is
  emitted.
- A field's expression in an f-string is parsed by an inner parser that
  emits into the same program; the text before the field is flushed
  before the field is parsed, except before a debug field.

- An assignment keeps what its targets emitted: at the statement's end
  each target's reads become its store (a name's load its store, an
  item's or attribute's read its target step, a display's items
  unpacked), and the value's steps move before them. A `del` makes its
  targets' reads their deletes, and an `assert` emits its branch and the
  jump over its message as its test ends.
- A lambda's body emits into the lambda's own program, which its scope
  holds from the start; its return compiles after it.
- A comprehension emits its clauses, but its first iterable, into its
  own program: a later clause's iterable is rotated before its target,
  the loop's opening and next-item steps go between, and an `if`
  clause's branch follows its test. At the comprehension's end the
  element's steps move from the enclosing program to its own, after the
  clauses' openings, and the clauses close innermost first. A dictionary
  or set display that becomes a comprehension drops the new value it
  emitted at its first item. In a class body, whose program loads names
  differently, a display whose first item has a `for` ahead emits that
  item into the comprehension's program from the start, and the clauses'
  openings are rotated before it at the end.
- A def's decorators and defaults, a class's decorators, its
  `__build_class__` step and its bases and keywords, a `with`
  statement's items and their targets' stores, an `except` clause's
  types and a `match` statement's subject emit into the enclosing program
  as they are parsed. A generic class's bases and keywords emit into the
  program of its type parameters' frame, and a case's guard into a
  program of its own, appended after the case's pattern.
- An annotated assignment's target becomes its store as a plain
  assignment's does; without a value, an attribute's or item's primary
  and key are evaluated and popped.
- An expression whose steps are needed later, elsewhere, is parsed apart:
  it emits into a program of its own, which the parse holds until the
  code compiling it appends those steps (`apart_take`), or frees on an
  error. A function's, class's or module's annotations, a type
  parameter's bound or default, a type alias's value and a match
  pattern's literals, dotted names and classes are parsed apart; each
  `__annotate__` or lazy-value function's program is made from them as
  the function is. Under `from __future__ import annotations` a
  function's annotations become strings, each parsed apart as a
  constant. A lambda or comprehension inside an annotation that no code
  evaluates (a function local's, or one that is a string) gets no program.

No spec test and no module of CPython's `Lib` compiles an expression
from its nodes any more: every expression's steps are those emitted as
it was parsed. A statement's own steps (an expression statement's pop,
a def's making step and store, a class's call) are still laid out from
its node when the next statement begins.

The test of an `if`, `elif` or `while` header and the iterable of a `for`
header are emitted the same way, after a statement the body held back and
a `while`'s block step. An expression statement, assignment, `del`, `assert`,
`yield`, `return` or `raise` keeps its steps when its operands' run from where it began to
the program's end; otherwise it undoes every step it emitted, clears its
nodes' marks and compiles at its end as before. The programs are the
same, step for step, in both execution modes for every spec test except
programs that a compile error discards, which now hold the steps their
statements emitted before the error.

The fifteenth stage deletes the compiler from nodes. Over every
specification test, the C API tests, the allocation-failure tests and
all 2,060 files of CPython's `Lib`, a probe build found no expression
compiled from its nodes and no statement compiled from them at its end:
a statement whose steps do not line up as kept is met only once an error
is pending, which discards the program. So `compile_node` emits a node's
own steps only, called as the parser completes the node, its operands'
already emitted; `emit_absent` emits the None of an absent value. An
assignment's targets always become their stores (`target_parsed` no
longer undoes them), a `def`'s decorators and defaults and a class's
header are always those parsed, and the store, target and method-callee
compilers that took nodes are gone. The undos that valid programs
reached go too: a keyword argument's name and an assignment expression's
target are read without emitting a load (`NAME '='`, `NAME ':='`), and a
yield statement adjusts its yield steps in place. Every program is the
same, step for step, as before over those inputs. What still reads a
node is a node's own step (its kind, operator and operands' shapes) and
a statement's own steps at its end: the next stage replaces those reads.

The sixteenth stage removes those reads, so that a node's operands can be
freed as the node completes. A probe build marks a completed node's links
to its operands unreadable (AddressSanitizer manual poisoning) and runs
every specification test; each report is a read that still needs the
tree. What the emitter and the target checks asked of a node's operands
is now computed once, as the node completes, from its operands' own
fields: its summary for the program's mode (`expands`), its analysis
events (`parse_children`), its shape as an operand at hand and as a
fused operator (`operand_shapes`), whether it is arithmetic, and its
facts as an assignment target (`target_facts`): whether it is one, its
error, and the first part each kind of target cannot assign, with that
part's name and span copied. Every program is the same, step for step,
and every target error the same, as before, but for a `del` of more than
255 targets, which the walk it replaces rejected as too deeply nested.

## Remaining stages

1. Emit expressions from the parser, in place of the finished
   statement's or clause header's compile. Collect bindings and
   declaration locations as each scope is parsed; resolve forward local,
   global, nonlocal and cell references by patching instructions. Branches
   use labels, and assignment parsing keeps target descriptors. Deferred
   annotations, comprehension bodies and reordered argument evaluation need
   instruction fragments that can be placed in their execution order.
2. Build code metadata from code records and recorded symbol uses. Remove
   executable tree allocation, scope tree walks and node-based code caches.
   Keep source spans and definition identity without retaining a tree.

Scope analysis moves into the parse through an analysis log, the
counterpart of emission. Each use, binding, declaration and check that
the symbol-table walk makes becomes an event: its kind, the name's text,
the scope it applies to, and the source span and line an error reports.
Events hold no node. At a statement's end the parser replays them into
the scopes in order, with the binding rules and diagnostics the walk has
now, so the first error is still the first in the walk's order. The log
has the emission stack's operations: a mark and a rollback for a parse
that backtracks or a statement that recompiles, a rotation where the
symbol table visits in another order than the source (targets before
values, a conditional's test before its branches, a dictionary's keys
before its values, a definition's name after its defaults), and a move
of a range of events to another scope, as a comprehension's element
moves to the comprehension's program. A name records a use when it
completes, in no particular scope: the scope that takes it, the walk's
or a later construct's, is where it is used. A construct that consumes
the name as a target (an assignment, `for`, `with`, `except`, `import`,
pattern or `del`) ignores that use and binds it.

The move is made in two steps, each checked by dumping every scope's
symbols, flags and order with the first analysis error over the
specification tests and CPython's `Lib`, before and after. First the
walk records events and replays them, with no change in behaviour. Then
each construct records its own events as it is parsed, and the walk
skips what was recorded, until no statement is walked and `scope_visit`
is gone.

The first step is done. While `analyse_statements` walks a statement,
`c->events` collects its symbol steps: a binding (`scope_bind`), a
global a named expression adds in the scopes it passes, a mark of a
scope's symbols and the move that follows it (`scope_later`), an
annotated assignment's target and annotation, and a type parameter.
Checks that read no symbol, scope creation and the node count stay in
the walk. The replay follows the walk, so an error in a replayed step
is reported before one the walk stopped at, which the walk met later.
A walk that now goes on past a binding error makes more scopes for a
statement that does not compile; no other scope changes. Over the 1,147
specification tests the dumps of every scope's symbols, flags and order
and the tests' output are the same before and after but for those
failing compiles, and so are the 2,060 files of CPython's `Lib`
compiled with `compile`.

The second step has begun. A `global` or `nonlocal` declaration and an
`import` record their events as they are parsed, an import's errors
among them; so do a name, a constant, and an operator, comparison,
attribute, subscription, slice, display, starred item or call whose
parts recorded theirs, and a simple statement other than a docstring.
The parts' ranges, which together run to the end of the log, are put
in the order the walk visits them: a call's keyword arguments after its
positional ones, a conditional's test before its branches, a
dictionary's keys before its values. Every node inside a recorded one
is recorded, so only the outermost range is taken, and the stale ranges
of the nodes inside are never read. The parser keeps each recorded node's range of the log, and
the walk takes a range in the place it would have visited the node.
Since the walk no longer descends a long run of prefix operators, the
parser counts the run toward its depth limit, as CPython's does.

Statements record theirs too: an assignment, `for`, `with`, `except`
and `del` bind their targets (a name's recorded use becomes its
binding), around the marks that move the targets' symbols after the
value's; a header records as soon as it is parsed, before its body. A
def or class records its name, defaults, decorators and bases, and the
parser makes its scope, and the hidden scope of its type parameters,
where the walk would have; a type alias records likewise. A range may
enter a scope: `EV_ENTER` makes a lambda's, comprehension's,
annotation function's or string annotation's scope in the scope it is
taken in, at the point the walk would, or enters a scope the parser
made, and an event of no scope belongs to the innermost entered scope.
Effects the walk has on scopes as it goes are events run at take time,
in the walk's order: a class's static attribute stored through `self`
(`EV_STATIC`), the checks of an `await`, `yield`, asynchronous
comprehension clause or mapping pattern (`EV_CHECK`), a named
expression's checks and binding (`EV_NAMED`), where a comprehension's
iterables and clauses are (`EV_ITERABLE`, `EV_CLAUSE`), an annotated
assignment's annotation (`EV_WITHIN`, `EV_ANNOTATE`), and a generic's
table of type parameters, once their bounds' scopes exist
(`EV_GENERIC`), each one function the walk called too.

The second step is done: every statement records its analysis as it
is parsed, and `scope_visit` and the walk's helpers are gone.
`analyse_statements` takes each statement's range in its scope, running
the take-time events and recording the rest for the replay, in the
order the walk visited them. Before the walk was deleted, a build that
stopped on any statement left to it compiled all 2,060 files of
CPython's `Lib` and ran the 1,147 specification tests without stopping.

Each stage must preserve Python 3.15 semantics and report its own measured
cost. Compiling every operation in the existing pausing mode is not an
acceptable substitute for this work: it changes the runtime costs without
removing the AST compiler.

## Evidence required

Before changing each stage, identify the affected cases in these groups:

- Binding order and diagnostics: reads before later assignments, `global`
  and `nonlocal`, class cells, private names, annotations, comprehension
  scopes, invalid syntax and competing errors.
- Execution order: short circuits, comparison chains, decorators, defaults,
  keyword and starred arguments, assignment targets and exception cleanup.
- Lifetime and suspension: constants, closures, code identity, source spans,
  collection during callbacks, suspended generators, coroutines and async
  generators, tracing, pause/resume and allocation failures.
- Cost: compilation and release, execution of already compiled code,
  end-to-end benchmarks, executable size and retained memory. Alternate old
  and new executables over rounds; do not report noisy differences as wins.

`tests/spec/execution/constant_lifetime.py` and the `ConstantLoads` TLA+
model exercise the checkpoint's constant lifetime through functions,
generators and coroutines. The model replays are semantic checks; they do
not prove the instruction representation. The full spec and model suites,
C API tests, allocation-failure tests and sanitizer runs remain required.
Platform claims require native checks on that platform.

The 2026-11-22 checkpoint passed 1,040 specification tests on macOS arm64,
with no invalid tests on the pinned Python 3.15.2 oracle, and all 157 TLA+
models. The C API and metering probes passed. Allocation-failure tests
passed all 205 programs, imports and intrinsic initialization. The same
1,040 specification tests passed with Clang 18 AddressSanitizer and
UndefinedBehaviorSanitizer on native Linux arm64 in Docker. That run
exposed an existing zero-argument cleanup path that computed `NULL + 0`;
the checkpoint also guards that empty range. The full allocation-failure
run preceded that guard; specification, API, metering and sanitizer checks
used it.

A separate Clang coverage build ran the new lifetime test: the instruction
constant branch ran 23 times and its name branch ran 119 times. This is
targeted coverage, not complete engine coverage.

On the same Linux arm64 copy, `make fuzz FUZZ_SECONDS=600` passed all four
targets: eval, compile and spyc ran for 620 seconds each, and allocation
failure ran for 602 seconds. `make fuzz-replay` then passed all four targets
under MemorySanitizer against the 4,090 retained corpus files. Both runs
used the source fingerprint recorded in the benchmark report. Full
`make sanitize` targets, ThreadSanitizer and full engine coverage have not
been completed for this checkpoint; the checks above do not establish them.

The parser-property stage passed 1,041 specification tests, all 158 TLA+
models, the C API and metering probes, and all 205 allocation-failure
programs plus intrinsic initialization on macOS arm64. All 33 standalone
build tests passed, with their oracle checks. The new function-scope test
fails on the saved pre-change engine's optimized generator classification
and passes on this engine and the pinned oracle. Its `FunctionScopes`
model checks 128 states and replays 64 transitions, including optimized
assertions, nested function bodies and yields in defaults.

The same 1,041 specification tests passed under Clang 18 AddressSanitizer
and UndefinedBehaviorSanitizer on native Linux arm64. The longer fuzz,
replay and full sanitizer runs for this second stage are not yet complete.
Its alternating compilation measurements are 0.9–2.0% lower; end-to-end
execution changes range from 0.7% faster to 1.0% slower. These small, mixed
execution differences do not establish a general runtime improvement.

The name-operand stage passed the 1,041 existing specification tests and
the added `name_operands.py` test on macOS arm64, including their pinned
oracle checks. All 1,042 tests also passed on native Linux arm64 under
AddressSanitizer and UndefinedBehaviorSanitizer. The new tests cover shared
code with different globals, invalidated name caches, closure rebinding,
collection during key and truth callbacks, and suspended-frame lifetime.
The updated `DynamicScopes` model checks 44 states and replays 22
transitions; all 158 models passed. The native C API and metering probes,
all 205 allocation-failure programs and intrinsic initialization, and all
33 standalone-build tests passed. The worker binding suite passed 127
tests, with its one Windows-only test skipped; it required running outside
the outer macOS sandbox so the worker could initialize its own sandbox.

The name-operand stage's longer fuzz and replay checks and its final
alternating performance comparison are still pending. Preliminary timings
while verification jobs were running are not used to establish a
performance difference. The source for these completed checks is `spy.c`
SHA-256 `68d514dc8cd32b1aa7a9153d79f15d1bceaa01130f2223119c3a99d0fe75febb`.

`bench/compiler.c` and `bench/compiler.py` measure compilation separately
from repeated execution. See [benchmark.md](benchmark.md) for the method
and results. The compilation measurement includes parsing, the
generation of every body's instructions during the parse, scope analysis
and code release. The instructions still come from a syntax tree, so this
is not yet a measurement of one-pass source-to-bytecode compilation.

## Design source

QuickJS at the revision in `tests/upstream.json`,
`7d1c13c5d8f8c6b32893786ed35cdcebd88194d2`, was inspected for its parser and
compiler organization. In `quickjs.c`, `js_parse_expr_binary` emits
operations during parsing, `emit_push_const` records constant-pool indices,
and `js_create_function` runs `resolve_variables` and `resolve_labels` over
the emitted code. This informs the design; Python's binding, annotation and
comprehension semantics still require their own implementation. Its license
is retained in [licenses/quickjs.txt](licenses/quickjs.txt).
