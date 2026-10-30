package spy

/*
#include <stdlib.h>
#include "spy.h"
*/
import "C"

import (
	"fmt"
	"iter"
	"runtime"
	"unsafe"
)

// A Value is a reference to an engine value. The garbage collector releases
// it once it is unreachable; it never outlives its runtime's Close.
type Value struct {
	rt  *Runtime
	ptr *C.SPYValue
}

func newValue(rt *Runtime, ptr *C.SPYValue) *Value {
	v := &Value{rt, ptr}
	runtime.AddCleanup(v, rt.drop, ptr)
	return v
}

// Runtime returns the runtime the value belongs to.
func (v *Value) Runtime() *Runtime {
	return v.rt
}

// IsNone reports whether the value is None.
func (v *Value) IsNone() bool {
	return v.rt.enter() == nil && C.spy_type(v.ptr) == C.SPY_NONE
}

// Truth is Python truth, as bool(value).
func (v *Value) Truth() bool {
	return v.rt.enter() == nil && C.spy_truth(v.ptr) != 0
}

// Decode stores the value in the Go value out points to; see
// [Runtime.ToValue] for the correspondence.
func (v *Value) Decode(out any) error {
	if err := v.rt.enter(); err != nil {
		return err
	}
	return v.rt.decode(v.ptr, out)
}

// GetAttr is getattr(value, name).
func (v *Value) GetAttr(name string) (*Value, error) {
	cname, err := v.rt.name(name)
	if err != nil {
		return nil, err
	}
	defer C.free(unsafe.Pointer(cname))
	return v.rt.wrap(C.spy_get_attr(v.rt.ctx, v.ptr, cname))
}

// SetAttr is setattr(value, name, item).
func (v *Value) SetAttr(name string, item any) error {
	i, err := v.rt.ref(item)
	if err != nil {
		return err
	}
	defer C.spy_release(i)
	cname, err := v.rt.name(name)
	if err != nil {
		return err
	}
	defer C.free(unsafe.Pointer(cname))
	return v.rt.check(C.spy_set_attr(v.rt.ctx, v.ptr, cname, i))
}

// GetItem is value[key].
func (v *Value) GetItem(key any) (*Value, error) {
	k, err := v.rt.ref(key)
	if err != nil {
		return nil, err
	}
	defer C.spy_release(k)
	return v.rt.wrap(C.spy_get_item(v.rt.ctx, v.ptr, k))
}

// SetItem is value[key] = item.
func (v *Value) SetItem(key, item any) error {
	k, err := v.rt.ref(key)
	if err != nil {
		return err
	}
	defer C.spy_release(k)
	i, err := v.rt.ref(item)
	if err != nil {
		return err
	}
	defer C.spy_release(i)
	return v.rt.check(C.spy_set_item(v.rt.ctx, v.ptr, k, i))
}

// Call calls the value with positional arguments.
func (v *Value) Call(args ...any) (*Value, error) {
	return v.CallKeywords(args, nil)
}

// CallKeywords calls the value with positional and keyword arguments.
func (v *Value) CallKeywords(args []any, kwargs map[string]any) (*Value, error) {
	argv := make([]*C.SPYValue, 0, len(args))
	defer func() {
		for _, a := range argv {
			C.spy_release(a)
		}
	}()
	for _, arg := range args {
		a, err := v.rt.ref(arg)
		if err != nil {
			return nil, err
		}
		argv = append(argv, a)
	}
	var keywords *C.SPYValue
	if len(kwargs) > 0 {
		var err error
		if keywords, err = v.rt.ref(kwargs); err != nil {
			return nil, err
		}
		defer C.spy_release(keywords)
	} else if err := v.rt.enter(); err != nil {
		return nil, err
	}
	return v.rt.wrap(C.spy_call_keywords(v.rt.ctx, v.ptr, C.size_t(len(argv)), unsafe.SliceData(argv), keywords))
}

// Iter iterates the value as a for loop does, yielding each item or the
// error that ended the iteration.
func (v *Value) Iter() iter.Seq2[*Value, error] {
	return func(yield func(*Value, error) bool) {
		if err := v.rt.enter(); err != nil {
			yield(nil, err)
			return
		}
		it, err := v.rt.wrap(C.spy_iter(v.rt.ctx, v.ptr))
		if err != nil {
			yield(nil, err)
			return
		}
		for {
			if err := v.rt.enter(); err != nil {
				yield(nil, err)
				return
			}
			item := C.spy_next(v.rt.ctx, it.ptr)
			if item == nil && *C.spy_error_type(v.rt.ctx) == 0 {
				return
			}
			value, err := v.rt.wrap(item)
			if !yield(value, err) || err != nil {
				return
			}
		}
	}
}

// Repr is repr(value).
func (v *Value) Repr() (string, error) {
	if err := v.rt.enter(); err != nil {
		return "", err
	}
	return As[string](v.rt.wrap(C.spy_repr(v.rt.ctx, v.ptr)))
}

// Str is str(value).
func (v *Value) Str() (string, error) {
	if err := v.rt.enter(); err != nil {
		return "", err
	}
	return As[string](v.rt.wrap(C.spy_str(v.rt.ctx, v.ptr)))
}

// String is str(value), or a placeholder naming the error.
func (v *Value) String() string {
	s, err := v.Str()
	if err != nil {
		return fmt.Sprintf("<unprintable: %v>", err)
	}
	return s
}

// As decodes the result of an operation into a T, passing its error on:
//
//	n, err := spy.As[int](rt.Eval("6 * 7"))
func As[T any](v *Value, err error) (T, error) {
	var out T
	if err == nil {
		err = v.Decode(&out)
	}
	return out, err
}

// Args are the arguments of a call to a host function.
type Args struct {
	Positional []*Value
	Keywords   map[string]*Value
}

func (rt *Runtime) args(argv []*C.SPYValue, keywords *C.SPYValue) (Args, error) {
	var args Args
	for _, a := range argv {
		args.Positional = append(args.Positional, newValue(rt, C.spy_retain(a)))
	}
	if keywords != nil && C.spy_truth(keywords) != 0 {
		if err := rt.decode(keywords, &args.Keywords); err != nil {
			return args, err
		}
	}
	return args, nil
}

// Scan decodes the positional arguments into dest, one each, after checking
// their count.
func (a Args) Scan(dest ...any) error {
	if len(a.Positional) != len(dest) {
		s := "s"
		if len(dest) == 1 {
			s = ""
		}
		return Raise("TypeError", fmt.Sprintf("expected %d argument%s, got %d", len(dest), s, len(a.Positional)))
	}
	for i, d := range dest {
		if err := a.Positional[i].Decode(d); err != nil {
			return err
		}
	}
	return nil
}
