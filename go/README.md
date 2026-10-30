# Small Python for Go

Run [Small Python](https://github.com/soasme/small-python), a small Python
3.15 engine written in C11, from Go. Each runtime is a separate interpreter
with its own globals and modules. The code it runs sees only what you hand
it: builtins, the functions and modules you define for it, and the
directories you mount. It cannot reach your Go values, files, network, or
environment unless a function of yours does so for it.

```sh
go get github.com/soasme/small-python/go
```

```go
import "github.com/soasme/small-python/go/spy"

rt, err := spy.New()
if err != nil {
	return err
}
defer rt.Close()
rt.Define("add", func(rt *spy.Runtime, args spy.Args) (any, error) {
	var a, b int
	if err := args.Scan(&a, &b); err != nil {
		return nil, err
	}
	return a + b, nil
})
n, err := spy.As[int](rt.Eval("add(40, 2)")) // 42
```

## Contents

1. [Choosing a package](#choosing-a-package)
2. [In-process: `spy`](#in-process-spy): running code, values, host
   functions, modules, output, files, errors, limits, lifetime
3. [Sandboxed: `worker`](#sandboxed-worker): options, values, objects, host
   functions, errors, limits, isolation
4. [Requirements](#requirements)
5. [Development](#development)

## Choosing a package

| | [`spy`](spy) | [`worker`](worker) |
|---|---|---|
| Where the engine runs | in your process, compiled by cgo | in a `spy-worker` process of its own |
| For | code you trust: configuration, rules, plugins you ship | code you do not: users' scripts, code written by a language model |
| An engine crash | crashes your program | fails the operation with `*WorkerError` |
| Values | references (`*Value`) to engine objects | copies, plus `*Object` handles |
| Bounding a run | step limit | step, memory, and time limits |
| Builds with | cgo and a C11 compiler | pure Go; needs the `spy-worker` executable |
| Cost of a call | a C function call | a message over a pipe |

Both run the same engine and the same Python. Start with `worker` when in
doubt; move to `spy` when you trust the code and the overhead matters.

## In-process: `spy`

### Running code

`spy.New` creates a runtime with the standard modules `sys` and `gc`;
`spy.NewBare` creates one with only the language core and its builtins.
`Close` frees it.

```go
rt.Exec("def area(w, h):\n    return w * h")    // run for effects
v, err := rt.Eval("area(3, 4)")                 // the last expression's value
n, err := spy.As[int](rt.Eval("area(3, 4)"))    // ... decoded into a Go type
rt.Set("limit", 10)                             // write a global
limit, err := rt.Get("limit")                   // read one, as a *Value
```

`Eval` and `Exec` use the filename `<string>` in tracebacks. A runtime keeps
its globals between calls, also after an exception.

### Values

A `*Value` is a reference to an engine value. Its methods do what Python
does: `GetAttr`, `SetAttr`, `GetItem`, `SetItem`, `Call`, `CallKeywords`,
`Iter`, `Truth`, `IsNone`, `Repr`, and `Str`. Printing it with `fmt` shows
`str(value)`.

```go
squares, _ := rt.Eval("(n * n for n in range(4))")
for v, err := range squares.Iter() {
	n, err := spy.As[int](v, err)
	...
}
upper, _ := rt.Eval("str.upper")
v, _ := upper.Call("spy")                       // 'SPY'
```

Anything you pass in (`Set`, `SetItem`, `Call`, a host function's result)
converts with `rt.ToValue`; `v.Decode(&x)` and `spy.As[T]` convert out, by
reflection, as `encoding/json` does:

| Go | Python |
|---|---|
| `nil`, a nil pointer | `None` |
| `bool` | `bool` (decoding accepts only a `bool`) |
| any integer type | `int`; out of the Go type's range: `OverflowError` |
| `float32`, `float64` | `float` (decoding also accepts an `int`) |
| `string` | `str` |
| `[]byte` | `bytes` (decoding also accepts `bytearray`) |
| `spy.Tuple` | `tuple` |
| other slices, arrays | `list`; decoding accepts any iterable |
| maps | `dict`, in sorted key order; decoding accepts any mapping |
| structs | `dict` of the exported fields; decoding accepts any mapping |
| pointers | what they point to; `None` decodes to a nil pointer |
| `*spy.Value` | itself |
| `spy.Func` | a builtin function |

Struct fields are named by a `spy:"name"` tag, or by the field name;
`spy:"-"` leaves a field out. Decoding ignores keys no field names.

```go
type User struct {
	Name  string   `spy:"name"`
	Roles []string `spy:"roles"`
}
rt.Set("user", User{Name: "ada", Roles: []string{"dev"}})
u, err := spy.As[User](rt.Eval("user | {'name': user['name'].title()}"))
```

Decoding into an `any` gives `nil`, `bool`, `int64`, `float64`, `string`,
`[]byte`, `[]any` for a list, `spy.Tuple`, `map[any]any` for a dict, and a
`*Value` for anything else. A string holding a lone surrogate, which Python
allows and UTF-8 does not, keeps its three-byte form in the Go string.

### Host functions

A host function is a `spy.Func`: it receives the runtime and the call's
arguments, and returns a result to convert or an error to raise.

```go
rt.Define("greet", func(rt *spy.Runtime, args spy.Args) (any, error) {
	var name string
	if err := args.Scan(&name); err != nil {   // TypeError: expected 1 argument, got 0
		return nil, err
	}
	end := "!"
	if v := args.Keywords["end"]; v != nil {
		if err := v.Decode(&end); err != nil {
			return nil, err
		}
	}
	return "hello " + name + end, nil
})
rt.Eval("greet('spy', end='?')")                // 'hello spy?'
```

`Args.Positional` holds the positional arguments and `Args.Keywords` the
keyword arguments; `Scan` decodes the positional ones after checking their
count. `rt.Function(name, f)` makes the function value without binding a
global, to pass as an argument or a module attribute. A host function may
call back into the engine through the runtime it receives, and may call the
engine values it is given.

### Modules and imports

A runtime imports only builtin modules, the modules you register, and the
sources your loader returns. It never reads the file system to import.

```go
rt.RegisterModule("config", func(rt *spy.Runtime, module *spy.Value) error {
	if err := module.SetAttr("region", "eu"); err != nil {
		return err
	}
	return rt.ExecModule(module, "def describe(): return 'region ' + region", "<config>")
})
rt.SetLoader(func(name string) (string, bool) {
	source, ok := sources[name]
	return source, ok
})
rt.Exec("import config, shapes")
```

`RegisterModule` calls its function on the first import, as QuickJS's
`JS_NewCModule` does. The loader receives module names: for `import pkg.mod`
it is asked for `pkg.mod.__init__` (a package), then `pkg.mod`, then
`pkg.mod.__namespace__` (a namespace package).

### Output

`print` writes to `os.Stdout`. `rt.SetOutput(w)` sends it to any
`io.Writer`; a write error fails the `print`. With `nil`, `print` raises
`OSError`.

```go
var out strings.Builder
rt.SetOutput(&out)
```

### Files

`open()` reaches only the directories you mount, at the engine paths you
choose; everything else raises `PermissionError`.

```go
rt.Mount("/srv/reports", "/data", true)         // read-only at /data
rt.Eval("open('/data/2026.csv').read()")
rt.Eval("open('/data/new.txt', 'w')")           // OSError: read-only file system
```

An empty engine path mounts a directory at its own resolved path. Files need
a POSIX host; on Windows `open()` is unavailable.

### Errors

An exception that escapes into Go is an `*spy.Exception` with its `Type`
(the class name, qualified by its module unless it is a builtin),
`Message`, `Filename`, and `Line`. The runtime clears it and stays usable.

```go
err := rt.Exec("x = 1\nraise ValueError('bad input')")
var e *spy.Exception
if errors.As(err, &e) {
	fmt.Println(e.Type, e.Message, e.Line)      // ValueError bad input 2
}
```

A host function raises by returning an error: `spy.Raise("KeyError",
"missing")`, or any `*spy.Exception`, raises that type with that message;
any other error raises `RuntimeError` with its text. A panic in a host
function, a module function, or the loader never reaches C: it raises
`RuntimeError` (or, in the loader, counts as no source). Exceptions cross by
type name and message, not by identity.

### Limits

`rt.SetStepLimit(n)` bounds the evaluation steps of each top-level `Eval` or
`Exec`; past it the engine raises `RuntimeError` and the runtime stays
usable. It counts work, not memory: `'x' * 10**9` takes few steps. The
in-process engine has no memory limit or timeout; use `worker` for those.
`rt.SetOptimize(1)` and `rt.SetOptimize(2)` act as `python -O` and `-OO`.

### Lifetime and goroutines

You never free a `*Value`. When the garbage collector finds one unreachable,
its reference is queued and released at the runtime's next call; `Collect`
runs the engine's cycle collector. `Close` frees the context and everything
in it; afterwards the runtime and its values return `spy.ErrClosed`.

A runtime is not safe for concurrent use: use it from one goroutine at a
time, or guard it with a mutex. It may move between goroutines. Separate
runtimes are independent and run in parallel.

## Sandboxed: `worker`

```go
import "github.com/soasme/small-python/go/worker"

rt, err := worker.New(worker.Options{Timeout: 5 * time.Second, MemoryLimit: 64 << 20})
if err != nil {
	return err
}
defer rt.Close()
rt.Define("greet", func(rt *worker.Runtime, args []any, kwargs map[string]any) (any, error) {
	if name, ok := args[0].(string); ok && len(args) == 1 {
		return "hello " + name, nil
	}
	return nil, worker.Raise("TypeError", "greet(name)")
})
v, err := rt.Eval("greet('spy')")               // "hello spy"
```

Each runtime starts one `spy-worker` process and talks to it over pipes.
The methods are those of `spy`, plus `Delete`, `Version`, `Pid`, and
`Closed`: `Eval`, `Exec`, `Call`, `Get`, `Set`, `Define`, `Function`,
`RegisterModule`, `Mount`, `Collect`, and `Close`.

### Options

The zero `worker.Options` is the default.

| Field | Default | Meaning |
|---|---|---|
| `Bare` | `false` | leave out the standard modules `sys` and `gc` |
| `StepLimit` | unlimited | evaluation steps per top-level `Eval` or `Exec`; past it, `RuntimeError` in Python |
| `MemoryLimit` | unlimited | bytes the engine may hold; past it, `MemoryError` in Python |
| `Timeout` | none | time one operation may run in the worker; past it, the worker is killed |
| `MessageLimit` | 64 MiB | the largest value that may cross, either direction |
| `Output` | `os.Stdout` | receives printed text |
| `Loader` | none | maps a module name to its source, as in `spy` |
| `Worker` | `spy-worker` on `$PATH` | the worker executable |

### Values

Values cross by copy, as plain Go values:

| Python | Go |
|---|---|
| `None` | `nil` |
| `bool` | `bool` |
| `int` | `int64`, or `*big.Int` beyond 64 bits |
| `float`, `complex` | `float64`, `complex128` |
| `str` | `string` |
| `bytes`, `bytearray` | `[]byte`, `worker.ByteArray` |
| `list`, `tuple` | `[]any`, `worker.Tuple` |
| `set`, `frozenset` | `worker.Set`, `worker.FrozenSet` |
| `dict` | `worker.Dict`, its items in order |
| anything else | `*worker.Object` |

Sending also accepts the other integer, float, and complex types and
`map[string]any`, in sorted key order, and a `*worker.Function`. Sets and
dicts arrive as sequences, so a `dict` with tuple keys still converts; only
values whose type is exactly one of those above are copied, so instances of
subclasses arrive as objects.

### Objects

An `*Object` is a handle to a value the worker keeps. Operate on it through
the runtime: `GetAttr`, `SetAttr`, `GetItem`, `SetItem`, `Len`, `Contains`,
`Iter`, `Next`, `Truth`, `Hash`, `Compare`, `Repr`, `Str`, `Dir`, and `Call`.

```go
rt.Exec("class Counter:\n    n = 0\n    def bump(self, by=1):\n        self.n += by\n        return self.n")
counter, _ := rt.Call("Counter", nil, nil)
bump, _ := rt.GetAttr(counter.(*worker.Object), "bump")
n, _ := rt.Call(bump, nil, map[string]any{"by": 10})   // int64(10)
```

The worker frees the value after the garbage collector finds the handle
unreachable. A handle belongs to its runtime; passing it to another fails
with an error matching `worker.ErrInvalid`.

### Host functions

A host function receives the runtime, the positional arguments, and the
keyword arguments, all converted as above. Through the runtime it may make
nested requests (`Call`, `Get`, object operations), but not `Eval` or
`Exec`. Its result converts back; its error raises:

- an `*Exception` from `worker.Raise(type, message)` raises that builtin
  class, or `RuntimeError` when there is none;
- an `*Exception` that came from this runtime re-raises the original
  exception object;
- any other error raises `RuntimeError` with its text. If that exception
  escapes back to Go, the `*Exception` wraps your error: `errors.Is` finds
  it.

A panic in a host function kills the worker, then keeps panicking.

### Errors

| Error | Meaning | Runtime survives |
|---|---|---|
| `*worker.Exception` | a Python exception: `Type`, `Message`, `Filename`, `Line`, `Object`, `Cause` | yes |
| `*worker.WorkerError` | the worker crashed, broke the protocol, or ended; `State` is its exit | no |
| `*worker.TimeoutError` | the operation ran past `Timeout`; the worker was killed | no |
| matches `worker.ErrInvalid` | misuse: a closed runtime, a value of another runtime, a message over the limit | yes |

Once a runtime is lost, every call returns the same error. Make a new one;
nothing is restarted.

### Limits and safety

| Limit | Set by | When exceeded | Runtime survives |
|---|---|---|---|
| steps | `StepLimit` | `RuntimeError` in Python | yes |
| memory | `MemoryLimit` | `MemoryError` in Python | yes |
| recursion | the engine | `RecursionError` in Python | yes |
| time | `Timeout` | `*TimeoutError`, worker killed | no |
| message size | `MessageLimit` | an `ErrInvalid` error, or the worker is killed if it sends one | yes, or no |

`Timeout` counts only time spent waiting for the worker; time in your host
functions, loader, and output is yours. Prefer `StepLimit` as the bound you
recover from and `Timeout` as the backstop.

The worker starts with an empty environment, `/` as its working directory,
no open files but its pipes and stderr, and in its own process group, and it
dies with your process. Your program checks every message it sends and
kills it at the first malformed one. Before it runs any code, the worker
locks itself down with the operating system's sandbox:

- **Linux**: no new privileges; Landlock limits files to your mounts and
  blocks TCP; seccomp refuses the system calls the engine does not make.
- **macOS**: a sandbox profile that denies everything but your mounts.
- **Windows**: none, and no `open()`.

So mount directories before running code: `Mount` after the first `Eval`,
`Exec`, `Call`, or object operation raises `PermissionError`. Every host
function you define runs with your program's full privileges; keep them
narrow, and validate their arguments.

A runtime is not safe for concurrent use. Separate runtimes are separate
processes.

## Requirements

- Go 1.24 or later.
- `spy`: cgo and a C11 compiler: GCC or Clang; on Windows, MinGW-w64 GCC,
  since MSVC lacks C11 complex numbers. The C sources are part of the
  module, so nothing else is installed.
- `worker`: the `spy-worker` executable. In the repository, `make
  spy-worker` builds it and `make install` puts it on `$PATH`; or set
  `Options.Worker`. Use the worker of the same release as the module.

The engine needs only the C runtime and its math library. The Unicode and
Python licenses of the tables it carries are in `licenses/`.

## Development

In a checkout of the repository:

```sh
make go-vendor      # copy the C sources into go/spy (ignored by git)
make test-go        # go vet and go test, with the spy-worker it builds
```

Edit the C sources at the repository root and run `make go-vendor` again;
the copies are never edited. A release tag `vX.Y.Z` makes the publish
workflow commit the copies and tag the module `go/vX.Y.Z`.

The examples in `example_test.go` of each package run with the tests. The
full specification is
[docs/packaging/go.md](https://github.com/soasme/small-python/blob/main/docs/packaging/go.md),
the worker protocol
[docs/packaging/protocol.md](https://github.com/soasme/small-python/blob/main/docs/packaging/protocol.md),
and the language [the engine manual](https://github.com/soasme/small-python/blob/main/docs/manual.md).
