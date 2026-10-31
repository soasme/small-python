package worker_test

import (
	"errors"
	"fmt"
	"time"

	"github.com/soasme/small-python/go/worker"
)

func Example() {
	rt, err := worker.New(worker.Options{Timeout: 5 * time.Second, MemoryLimit: 64 << 20})
	if err != nil {
		panic(err)
	}
	defer rt.Close()
	rt.Define("greet", func(rt *worker.Runtime, args []any, kwargs map[string]any) (any, error) {
		if name, ok := args[0].(string); ok && len(args) == 1 {
			return "hello " + name, nil
		}
		return nil, worker.Raise("TypeError", "greet(name)")
	})
	v, err := rt.Eval("greet('spy')")
	fmt.Println(v, err)
	// Output: hello spy <nil>
}

func ExampleRuntime_Eval() {
	rt, _ := worker.New(worker.Options{})
	defer rt.Close()
	v, _ := rt.Eval("[1, 2.5, 'three', (4,), {'five': None}, 2 ** 64]")
	fmt.Printf("%#v\n", v.([]any)[:5])
	fmt.Println(v.([]any)[5])
	// Output:
	// []interface {}{1, 2.5, "three", worker.Tuple{4}, worker.Dict{worker.Item{Key:"five", Value:interface {}(nil)}}}
	// 18446744073709551616
}

func ExampleObject() {
	rt, _ := worker.New(worker.Options{})
	defer rt.Close()
	rt.Exec("class Counter:\n    def __init__(self): self.n = 0\n    def bump(self, by=1):\n        self.n += by\n        return self.n")
	counter, _ := rt.Call("Counter", nil, nil)
	bump, _ := rt.GetAttr(counter.(*worker.Object), "bump")
	rt.Call(bump, nil, nil)
	n, _ := rt.Call(bump, nil, map[string]any{"by": 10})
	field, _ := rt.GetAttr(counter.(*worker.Object), "n")
	fmt.Println(n, field)
	// Output: 11 11
}

func ExampleOptions() {
	rt, _ := worker.New(worker.Options{StepLimit: 100_000, Timeout: time.Second})
	defer rt.Close()
	err := rt.Exec("while True: pass")
	fmt.Println(err.(*worker.Exception).Type, rt.Closed())
	v, _ := rt.Eval("1 + 1")
	fmt.Println(v)
	// Output:
	// RuntimeError false
	// 2
}

func ExampleTimeoutError() {
	rt, _ := worker.New(worker.Options{Timeout: 200 * time.Millisecond})
	defer rt.Close()
	err := rt.Exec("while True: pass")
	var timeout *worker.TimeoutError
	fmt.Println(errors.As(err, &timeout), rt.Closed())
	// Output: true false
}

func ExampleException() {
	rt, _ := worker.New(worker.Options{})
	defer rt.Close()
	failed := errors.New("disk on fire")
	rt.Define("save", func(*worker.Runtime, []any, map[string]any) (any, error) { return nil, failed })
	_, err := rt.Eval("save()")
	var e *worker.Exception
	fmt.Println(errors.As(err, &e), e.Type, errors.Is(err, failed))
	// Output: true RuntimeError true
}
