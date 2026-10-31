package worker_test

import (
	"errors"
	"math"
	"math/big"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"runtime"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/soasme/small-python/go/spy"
	"github.com/soasme/small-python/go/worker"
)

// The tests and examples run the worker the repository's Makefile builds
// (make spy-worker), found on $PATH as an installed one would be.
func TestMain(m *testing.M) {
	root, _ := filepath.Abs("../..")
	os.Setenv("PATH", root+string(os.PathListSeparator)+os.Getenv("PATH"))
	os.Exit(m.Run())
}

func start(t *testing.T, opts worker.Options) *worker.Runtime {
	t.Helper()
	rt, err := worker.New(opts)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { rt.Close() })
	return rt
}

func equal(t *testing.T, got, want any) {
	t.Helper()
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %#v, want %#v", got, want)
	}
}

func eval(t *testing.T, rt *worker.Runtime, source string) any {
	t.Helper()
	v, err := rt.Eval(source)
	if err != nil {
		t.Fatalf("%s: %v", source, err)
	}
	return v
}

func exception(t *testing.T, err error) *worker.Exception {
	t.Helper()
	var e *worker.Exception
	if !errors.As(err, &e) {
		t.Fatalf("not an exception: %v", err)
	}
	return e
}

func lost(err error) bool {
	var w *worker.WorkerError
	var timeout *worker.TimeoutError
	return errors.As(err, &w) || errors.As(err, &timeout)
}

func TestEvaluatesAndConverts(t *testing.T) {
	rt := start(t, worker.Options{})
	equal(t, rt.Version(), spy.Version)
	equal(t, eval(t, rt, "6 * 7"), int64(42))
	two64, _ := new(big.Int).SetString("10000000000000000", 16)
	equal(t, eval(t, rt, "2 ** 64"), two64)
	equal(t, eval(t, rt, "-2 ** 63"), int64(math.MinInt64))
	equal(t, eval(t, rt, "1j + 0.5"), complex(0.5, 1))
	equal(t, eval(t, rt, "'\\udc80x'"), "\xed\xb2\x80x")
	equal(t, eval(t, rt, "[None, True, b'a', bytearray(b'b'), (1,), {1: 'x'}, {2}, frozenset()]"), []any{
		nil, true, []byte("a"), worker.ByteArray("b"), worker.Tuple{int64(1)},
		worker.Dict{{int64(1), "x"}}, worker.Set{int64(2)}, worker.FrozenSet{},
	})
	if err := rt.Set("big", new(big.Int).Neg(two64)); err != nil {
		t.Fatal(err)
	}
	equal(t, eval(t, rt, "big == -2 ** 64"), true)
	if err := rt.Set("s", "\xed\xb2\x80"); err != nil {
		t.Fatal(err)
	}
	equal(t, eval(t, rt, "s == '\\udc80'"), true)
	equal(t, exception(t, rt.Set("s", "\xff")).Type, "UnicodeEncodeError")
	if err := rt.Set("m", map[string]any{"b": uint64(math.MaxUint64), "a": []any{1.5}}); err != nil {
		t.Fatal(err)
	}
	equal(t, eval(t, rt, "repr(m)"), "{'a': [1.5], 'b': 18446744073709551615}")
}

func TestGlobals(t *testing.T) {
	rt := start(t, worker.Options{})
	if err := rt.Set("x", 1); err != nil {
		t.Fatal(err)
	}
	v, ok, err := rt.Get("x")
	equal(t, []any{v, ok, err}, []any{int64(1), true, nil})
	v, _, _ = rt.Get("len")
	if _, ok := v.(*worker.Object); !ok {
		t.Fatalf("len is %#v", v)
	}
	if err := rt.Delete("x"); err != nil {
		t.Fatal(err)
	}
	v, ok, err = rt.Get("x")
	equal(t, []any{v, ok, err}, []any{nil, false, nil})
	equal(t, exception(t, rt.Delete("x")).Type, "KeyError")
}

func TestExceptionsCarryTheirPlace(t *testing.T) {
	rt := start(t, worker.Options{})
	e := exception(t, rt.Exec("x = 1\nraise ValueError('bad')"))
	equal(t, []any{e.Type, e.Message, e.Line}, []any{"ValueError", "bad", int64(2)})
	repr, _ := rt.Repr(e.Object)
	equal(t, repr, "ValueError('bad')")
}

func TestHostFunctionsAndNestedRequests(t *testing.T) {
	rt := start(t, worker.Options{})
	rt.Define("add", func(_ *worker.Runtime, args []any, kwargs map[string]any) (any, error) {
		if len(args) == 2 && len(kwargs) == 0 {
			a, aok := args[0].(int64)
			b, bok := args[1].(int64)
			if aok && bok {
				return a + b, nil
			}
		}
		return nil, worker.Raise("TypeError", "add(a, b)")
	})
	// Recursion through the engine and back, several levels deep.
	rt.Define("down", func(rt *worker.Runtime, args []any, _ map[string]any) (any, error) {
		n := args[0].(int64)
		if n == 0 {
			return 0, nil
		}
		below, err := rt.Call("step", []any{n - 1}, nil)
		if err != nil {
			return nil, err
		}
		return below.(int64) + 1, nil
	})
	if err := rt.Exec("def step(n):\n    return down(n)"); err != nil {
		t.Fatal(err)
	}
	equal(t, eval(t, rt, "add(40, 2)"), int64(42))
	equal(t, eval(t, rt, "down(10)"), int64(10))
	_, err := rt.Eval("add('a')")
	equal(t, err.Error(), "TypeError: add(a, b)")
	rt.Define("named", func(_ *worker.Runtime, _ []any, kwargs map[string]any) (any, error) {
		for key := range kwargs {
			return key, nil
		}
		return nil, nil
	})
	equal(t, eval(t, rt, "named(key=1)"), "key")
	rt.Define("nested_eval", func(rt *worker.Runtime, _ []any, _ map[string]any) (any, error) {
		return rt.Eval("1")
	})
	_, err = rt.Eval("nested_eval()")
	equal(t, exception(t, err).Type, "ValueError")
}

func TestHostErrorsComeBackAsTheirCause(t *testing.T) {
	rt := start(t, worker.Options{})
	fire := errors.New("disk on fire")
	rt.Define("fail", func(*worker.Runtime, []any, map[string]any) (any, error) { return nil, fire })
	_, err := rt.Eval("fail()")
	equal(t, exception(t, err).Type, "RuntimeError")
	if !errors.Is(err, fire) {
		t.Fatalf("%v does not wrap its cause", err)
	}
	if err := rt.Exec("try:\n    fail()\nexcept RuntimeError as e:\n    caught = str(e)"); err != nil {
		t.Fatal(err)
	}
	v, _, _ := rt.Get("caught")
	equal(t, v, "disk on fire")
	// An engine exception passing through a host function keeps its identity.
	rt.Define("relay", func(rt *worker.Runtime, _ []any, _ map[string]any) (any, error) {
		return rt.Call("boom", nil, nil)
	})
	if err := rt.Exec("class Boom(Exception): pass\ndef boom(): raise Boom(7)"); err != nil {
		t.Fatal(err)
	}
	if err := rt.Exec("try:\n    relay()\nexcept Boom as e:\n    got = e.args"); err != nil {
		t.Fatal(err)
	}
	v, _, _ = rt.Get("got")
	equal(t, v, worker.Tuple{int64(7)})
}

func TestObjects(t *testing.T) {
	rt := start(t, worker.Options{})
	d := eval(t, rt, "type('D', (dict,), {})(a=1)").(*worker.Object)
	v, _ := rt.GetItem(d, "a")
	equal(t, v, int64(1))
	if err := rt.SetItem(d, "b", 2); err != nil {
		t.Fatal(err)
	}
	n, _ := rt.Len(d)
	equal(t, n, int64(2))
	found, _ := rt.Contains(d, "b")
	truth, _ := rt.Truth(d)
	equal(t, []bool{found, truth}, []bool{true, true})
	_, err := rt.GetItem(d, "zz")
	equal(t, exception(t, err).Type, "KeyError")
	repr, _ := rt.Repr(d)
	equal(t, repr, "{'a': 1, 'b': 2}")
	if err := rt.SetAttr(d, "note", "hi"); err != nil {
		t.Fatal(err)
	}
	v, _ = rt.GetAttr(d, "note")
	equal(t, v, "hi")
	v, _ = rt.Compare(d, worker.Eq, worker.Dict{})
	equal(t, v, false)
	it, _ := rt.Iter(d)
	var keys []any
	for {
		key, ok, err := rt.Next(it.(*worker.Object))
		if err != nil {
			t.Fatal(err)
		}
		if !ok {
			break
		}
		keys = append(keys, key)
	}
	equal(t, keys, []any{"a", "b"})
	f := eval(t, rt, "lambda x, *, y=0: x + y")
	v, _ = rt.Call(f, []any{1}, map[string]any{"y": 2})
	equal(t, v, int64(3))
	other := start(t, worker.Options{})
	if err := other.Set("x", f); !errors.Is(err, worker.ErrInvalid) {
		t.Fatal(err)
	}
}

func TestReleasedHandlesAreFreed(t *testing.T) {
	rt := start(t, worker.Options{})
	if err := rt.Exec("freed = []\nclass Box:\n    def __del__(self): freed.append(1)"); err != nil {
		t.Fatal(err)
	}
	for range 100 {
		eval(t, rt, "Box()")
	}
	for range 50 {
		runtime.GC()
		if _, err := rt.Collect(); err != nil {
			t.Fatal(err)
		}
		if eval(t, rt, "len(freed)") == int64(100) {
			return
		}
	}
	t.Fatalf("freed %v of 100", eval(t, rt, "len(freed)"))
}

func TestOutputAndLoader(t *testing.T) {
	var printed strings.Builder
	rt := start(t, worker.Options{
		Output: &printed,
		Loader: func(name string) (string, bool) { return "WORD = 'hi'", name == "hello" },
	})
	if err := rt.RegisterModule("native", map[string]any{"answer": 42}, "double = answer * 2"); err != nil {
		t.Fatal(err)
	}
	if err := rt.Exec("import hello, native\nprint(hello.WORD, native.double)"); err != nil {
		t.Fatal(err)
	}
	equal(t, printed.String(), "hi 84\n")
}

func TestLimits(t *testing.T) {
	rt := start(t, worker.Options{StepLimit: 10_000, MemoryLimit: 16 << 20})
	equal(t, exception(t, rt.Exec("while True: pass")).Type, "RuntimeError")
	equal(t, exception(t, rt.Exec("x = 'a' * (64 << 20)")).Type, "MemoryError")
	equal(t, eval(t, rt, "1 + 1"), int64(2))
}

func TestTimeoutStopsTheOperationButNotWhileTheHostRuns(t *testing.T) {
	rt := start(t, worker.Options{Timeout: 300 * time.Millisecond})
	rt.Define("slow", func(*worker.Runtime, []any, map[string]any) (any, error) {
		time.Sleep(500 * time.Millisecond)
		return nil, nil
	})
	eval(t, rt, "slow()")
	started := time.Now()
	var timeout *worker.TimeoutError
	if err := rt.Exec("while True: pass"); !errors.As(err, &timeout) {
		t.Fatal(err)
	}
	if time.Since(started) > 5*time.Second {
		t.Fatal("the timeout took too long")
	}
	if rt.Closed() {
		t.Fatal("a timed-out runtime is closed")
	}
	equal(t, eval(t, rt, "1"), int64(1))
}

func TestACrashedWorkerIsLost(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("signals are POSIX")
	}
	for _, signal := range []string{"SEGV", "ABRT", "KILL"} {
		rt := start(t, worker.Options{})
		pid := strconv.Itoa(rt.Pid())
		rt.Define("crash", func(*worker.Runtime, []any, map[string]any) (any, error) {
			return nil, exec.Command("kill", "-"+signal, pid).Run()
		})
		_, err := rt.Eval("crash() or [0 for _ in range(10**9)]")
		var w *worker.WorkerError
		if !errors.As(err, &w) || w.State == nil || w.State.ExitCode() != -1 {
			t.Fatalf("%s: %v", signal, err)
		}
		if _, err := rt.Eval("1"); !lost(err) {
			t.Fatal(err)
		}
	}
}

func TestAPanickingHostFunctionLosesTheWorker(t *testing.T) {
	rt := start(t, worker.Options{})
	rt.Define("boom", func(*worker.Runtime, []any, map[string]any) (any, error) { panic("boom") })
	func() {
		defer func() {
			if recover() == nil {
				t.Fatal("the panic was swallowed")
			}
		}()
		rt.Eval("boom()")
	}()
	if _, err := rt.Eval("1"); !lost(err) {
		t.Fatal(err)
	}
}

func TestCloseIsGraceful(t *testing.T) {
	rt := start(t, worker.Options{})
	if err := rt.Close(); err != nil {
		t.Fatal(err)
	}
	if _, err := rt.Eval("1"); !errors.Is(err, worker.ErrInvalid) {
		t.Fatal(err)
	}
}

func TestTheWorkerIsSandboxedOnceCodeRuns(t *testing.T) {
	if runtime.GOOS != "darwin" {
		t.Skip("the macOS sandbox")
	}
	rt := start(t, worker.Options{})
	if err := rt.Mount(os.TempDir(), "/data", true); err != nil {
		t.Fatal(err)
	}
	eval(t, rt, "1")
	equal(t, exception(t, rt.Mount(os.TempDir(), "/more", true)).Type, "PermissionError")
}
