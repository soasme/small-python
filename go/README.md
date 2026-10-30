# Small Python for Go

Embed [Small Python](https://github.com/soasme/small-python), a small Python
3.15 engine written in C11, in Go.

```sh
go get github.com/soasme/small-python/go
```

| Package | Role |
|---|---|
| [`spy`](spy) | The engine in your process, compiled from source by cgo. For trusted code and the lowest overhead. |
| [`worker`](worker) | The engine in a sandboxed `spy-worker` process, spoken to over pipes. For untrusted code. Pure Go. |

```go
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

```go
rt, err := worker.New(worker.Options{Timeout: 5 * time.Second, MemoryLimit: 64 << 20})
if err != nil {
	return err
}
defer rt.Close()
v, err := rt.Eval("sum(range(10))") // int64(45)
```

`spy` needs cgo and a C11 compiler; on Windows, MinGW-w64 GCC, since MSVC
lacks C11 complex numbers. `worker` needs the `spy-worker` executable, which
`make install` in the repository puts on `$PATH`; `Options.Worker` names
another. The Unicode and Python licenses of the tables the engine carries
are in `licenses/`. See `docs/packaging/go.md` in the repository.
