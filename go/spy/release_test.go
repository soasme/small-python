package spy_test

import (
	"reflect"
	"runtime"
	"testing"
	"time"

	"github.com/soasme/small-python/go/spy"
)

func TestDroppedValuesAreReleased(t *testing.T) {
	rt := newRuntime(t)
	if err := rt.Exec("freed = []\nclass Box:\n    def __del__(self): freed.append(1)"); err != nil {
		t.Fatal(err)
	}
	for range 100 {
		if _, err := rt.Eval("Box()"); err != nil {
			t.Fatal(err)
		}
	}
	for range 50 {
		runtime.GC()
		if eval[int](t, rt, "len(freed)") == 100 {
			return
		}
	}
	t.Fatalf("freed %d of 100", eval[int](t, rt, "len(freed)"))
}

// The lambda's Value is unreachable once Call has its pointer; churn
// releases what the collector dropped while the call runs.
func TestAValueOutlivesTheCallsOfItsOwnMethods(t *testing.T) {
	rt := newRuntime(t)
	rt.Define("churn", func(rt *spy.Runtime, _ spy.Args) (any, error) {
		for range 10 {
			runtime.GC()
			time.Sleep(5 * time.Millisecond)
			rt.Collect()
		}
		return nil, nil
	})
	for range 5 {
		f, err := rt.Eval("lambda: (churn(), list(range(3)))[1]")
		if err != nil {
			t.Fatal(err)
		}
		got, err := spy.As[[]int](f.Call())
		if err != nil || !reflect.DeepEqual(got, []int{0, 1, 2}) {
			t.Fatal(got, err)
		}
	}
}
