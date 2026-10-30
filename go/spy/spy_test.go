package spy_test

import (
	"errors"
	"reflect"
	"strings"
	"testing"

	"github.com/soasme/small-python/go/spy"
)

func newRuntime(t *testing.T) *spy.Runtime {
	t.Helper()
	rt, err := spy.New()
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { rt.Close() })
	return rt
}

func eval[T any](t *testing.T, rt *spy.Runtime, source string) T {
	t.Helper()
	v, err := spy.As[T](rt.Eval(source))
	if err != nil {
		t.Fatalf("%s: %v", source, err)
	}
	return v
}

func exception(t *testing.T, err error) *spy.Exception {
	t.Helper()
	var e *spy.Exception
	if !errors.As(err, &e) {
		t.Fatalf("not an exception: %v", err)
	}
	return e
}

func equal[T any](t *testing.T, got, want T) {
	t.Helper()
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("got %#v, want %#v", got, want)
	}
}

func TestEvaluatesAndConverts(t *testing.T) {
	rt := newRuntime(t)
	equal(t, eval[int](t, rt, "6 * 7"), 42)
	equal(t, eval[float64](t, rt, "1 / 4"), 0.25)
	equal(t, eval[float64](t, rt, "2"), 2.0)
	equal(t, eval[string](t, rt, "'spy' * 2"), "spyspy")
	equal(t, eval[[]int](t, rt, "[1, 2, 3]"), []int{1, 2, 3})
	equal(t, eval[[2]any](t, rt, "(1, 'a')"), [2]any{int64(1), "a"})
	equal(t, eval[*int](t, rt, "None"), nil)
	equal(t, eval[map[string]int](t, rt, "{'a': 1, 'b': 2}"), map[string]int{"a": 1, "b": 2})
	equal(t, eval[bool](t, rt, "1 < 2"), true)
	equal(t, eval[[]byte](t, rt, "b'ab'"), []byte("ab"))
	equal(t, eval[string](t, rt, "'\\udc80'"), "\xed\xb2\x80")
	equal(t, eval[[]any](t, rt, "[None, True, 1, 1.5, 's', b'b', (1,), {1: 'x'}]"), []any{
		nil, true, int64(1), 1.5, "s", []byte("b"), spy.Tuple{int64(1)}, map[any]any{int64(1): "x"},
	})
}

func TestReportsExceptions(t *testing.T) {
	rt := newRuntime(t)
	e := exception(t, rt.Exec("x = 1\nraise ValueError('bad')"))
	equal(t, *e, spy.Exception{Type: "ValueError", Message: "bad", Filename: "<string>", Line: 2})
	equal(t, e.Error(), "ValueError: bad")
	equal(t, eval[int](t, rt, "x"), 1)
	for source, want := range map[string]string{"'a'": "TypeError", "1000": "OverflowError", "1 +": "SyntaxError", "a\x00": "SyntaxError"} {
		_, err := spy.As[int8](rt.Eval(source))
		equal(t, exception(t, err).Type, want)
	}
	_, err := spy.As[bool](rt.Eval("1"))
	equal(t, exception(t, err).Type, "TypeError")
}

func TestGlobalsRoundTrip(t *testing.T) {
	rt := newRuntime(t)
	if err := rt.Set("items", []string{"a", "b"}); err != nil {
		t.Fatal(err)
	}
	if err := rt.Set("pair", spy.Tuple{1, 2.5}); err != nil {
		t.Fatal(err)
	}
	equal(t, eval[string](t, rt, "'-'.join(items)"), "a-b")
	equal(t, eval[float64](t, rt, "pair[0] + pair[1]"), 3.5)
	equal(t, eval[string](t, rt, "type(pair).__name__"), "tuple")
	items, _ := rt.Get("items")
	appendTo, _ := items.GetAttr("append")
	if _, err := appendTo.Call("c"); err != nil {
		t.Fatal(err)
	}
	got, _ := spy.As[[]string](rt.Get("items"))
	equal(t, got, []string{"a", "b", "c"})
}

func TestHostFunctions(t *testing.T) {
	rt := newRuntime(t)
	rt.Define("add", func(rt *spy.Runtime, args spy.Args) (any, error) {
		var a, b int
		if err := args.Scan(&a, &b); err != nil {
			return nil, err
		}
		return a + b, nil
	})
	rt.Define("greet", func(rt *spy.Runtime, args spy.Args) (any, error) {
		var name string
		end := "!"
		if err := args.Scan(&name); err != nil {
			return nil, err
		}
		if v := args.Keywords["end"]; v != nil {
			if err := v.Decode(&end); err != nil {
				return nil, err
			}
		}
		return "hello " + name + end, nil
	})
	rt.Define("apply", func(rt *spy.Runtime, args spy.Args) (any, error) {
		return args.Positional[0].Call(args.Positional[1])
	})
	equal(t, eval[int](t, rt, "add(40, 2)"), 42)
	equal(t, eval[string](t, rt, "greet('spy')"), "hello spy!")
	equal(t, eval[string](t, rt, "greet('spy', end='?')"), "hello spy?")
	equal(t, eval[int](t, rt, "apply(lambda n: n * 2, 21)"), 42)
	_, err := rt.Eval("add(1)")
	equal(t, err.Error(), "TypeError: expected 2 arguments, got 1")
	if err := rt.Exec("try:\n    add('a', 1)\nexcept TypeError as e:\n    caught = 'yes'"); err != nil {
		t.Fatal(err)
	}
	equal(t, eval[string](t, rt, "caught"), "yes")
}

func TestHostErrorsAndPanicsBecomeExceptions(t *testing.T) {
	rt := newRuntime(t)
	rt.Define("fail", func(*spy.Runtime, spy.Args) (any, error) { return nil, spy.Raise("KeyError", "missing") })
	rt.Define("wrapped", func(*spy.Runtime, spy.Args) (any, error) { return nil, errors.New("disk on fire") })
	rt.Define("boom", func(*spy.Runtime, spy.Args) (any, error) { panic("boom") })
	if err := rt.Exec("try:\n    fail()\nexcept KeyError:\n    ok = True"); err != nil {
		t.Fatal(err)
	}
	equal(t, eval[bool](t, rt, "ok"), true)
	_, err := rt.Eval("wrapped()")
	equal(t, err.Error(), "RuntimeError: disk on fire")
	_, err = rt.Eval("boom()")
	equal(t, err.Error(), "RuntimeError: a Go callback panicked: boom")
	equal(t, eval[int](t, rt, "1"), 1)
}

func TestOutputLoaderAndModules(t *testing.T) {
	rt := newRuntime(t)
	var printed strings.Builder
	rt.SetOutput(&printed)
	rt.SetLoader(func(name string) (string, bool) { return "WORD = 'hi'\n", name == "greeting" })
	err := rt.RegisterModule("native", func(rt *spy.Runtime, module *spy.Value) error {
		if err := module.SetAttr("answer", 42); err != nil {
			return err
		}
		return rt.ExecModule(module, "double = answer * 2", "<native>")
	})
	if err != nil {
		t.Fatal(err)
	}
	if err := rt.Exec("import greeting, native\nprint(greeting.WORD, native.double)"); err != nil {
		t.Fatal(err)
	}
	equal(t, printed.String(), "hi 84\n")
	equal(t, exception(t, rt.Exec("import nothing")).Type, "ModuleNotFoundError")
}

func TestStdModulesAreOptional(t *testing.T) {
	if err := newRuntime(t).Exec("import sys"); err != nil {
		t.Fatal(err)
	}
	bare, _ := spy.NewBare()
	defer bare.Close()
	if bare.Exec("import sys") == nil {
		t.Fatal("a bare runtime imported sys")
	}
}

func TestStepLimit(t *testing.T) {
	rt := newRuntime(t)
	rt.SetStepLimit(10_000)
	equal(t, exception(t, rt.Exec("while True: pass")).Type, "RuntimeError")
	equal(t, eval[int](t, rt, "1 + 1"), 2)
}

func TestIterationAndItems(t *testing.T) {
	rt := newRuntime(t)
	squares, _ := rt.Eval("(n * n for n in range(4))")
	var got []int
	for v, err := range squares.Iter() {
		n, err := spy.As[int](v, err)
		if err != nil {
			t.Fatal(err)
		}
		got = append(got, n)
	}
	equal(t, got, []int{0, 1, 4, 9})
	d, _ := rt.Eval("{}")
	if err := d.SetItem("k", []int{1, 2}); err != nil {
		t.Fatal(err)
	}
	item, _ := d.GetItem("k")
	equal(t, item.String(), "[1, 2]")
	_, err := d.GetItem("x")
	equal(t, exception(t, err).Type, "KeyError")
	failing, _ := rt.Eval("(1 // 0 for _ in range(1))")
	for _, err := range failing.Iter() {
		equal(t, exception(t, err).Type, "ZeroDivisionError")
	}
}

func TestStructsAndMaps(t *testing.T) {
	type Doc struct {
		Title  string   `spy:"title"`
		Tags   []string `spy:"tags"`
		Rank   *int     `spy:"rank"`
		Secret string   `spy:"-"`
	}
	rt := newRuntime(t)
	doc := Doc{Title: "t", Tags: []string{"a"}, Secret: "s"}
	v, err := rt.ToValue(doc)
	if err != nil {
		t.Fatal(err)
	}
	equal(t, must(v.Repr()), "{'title': 't', 'tags': ['a'], 'rank': None}")
	doc.Secret = ""
	equal(t, must(spy.As[Doc](v, nil)), doc)
	v, _ = rt.ToValue(map[int]string{3: "c", 1: "a", 2: "b"})
	equal(t, must(v.Repr()), "{1: 'a', 2: 'b', 3: 'c'}")
	_, err = spy.As[Doc](rt.Eval("{'title': 1}"))
	equal(t, exception(t, err).Type, "TypeError")
}

func TestValuesOfAnotherRuntimeAreRefused(t *testing.T) {
	a, b := newRuntime(t), newRuntime(t)
	v, _ := a.Eval("[]")
	equal(t, exception(t, b.Set("x", v)).Type, "ValueError")
}

func TestClosedRuntime(t *testing.T) {
	rt, _ := spy.New()
	v, _ := rt.Eval("[]")
	rt.Close()
	if _, err := rt.Eval("1"); err != spy.ErrClosed {
		t.Fatal(err)
	}
	if _, err := v.Repr(); err != spy.ErrClosed {
		t.Fatal(err)
	}
}

func must[T any](v T, err error) T {
	if err != nil {
		panic(err)
	}
	return v
}
