package spy_test

import (
	"runtime"
	"testing"
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
