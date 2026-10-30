package spy

/*
#include <stdint.h>
#include <stdlib.h>
#include "spy.h"

SPYValue *spy_go_native(SPYContext *, const char *, uintptr_t);
*/
import "C"

import (
	"cmp"
	"fmt"
	"math"
	"reflect"
	"runtime/cgo"
	"slices"
	"unsafe"
)

// Tuple converts to a tuple, and a tuple decodes to it in an any.
type Tuple []any

// An Exception is an engine exception, raised by engine code or by Go.
//
// Exceptions cross between Go and the engine by type name and message: one
// that escapes into Go is copied into an *Exception and cleared, and a host
// function returning one raises a new exception with the same type name and
// message.
type Exception struct {
	// Type is the class name, qualified by its module unless it is a builtin.
	Type string
	// Message is the text CPython's traceback shows after the type.
	Message string
	// Filename and Line say where it was raised, when it came from the engine.
	Filename string
	Line     int
}

func (e *Exception) Error() string {
	if e.Message == "" {
		return e.Type
	}
	return e.Type + ": " + e.Message
}

// Raise returns an exception for a host function to fail with: the engine
// raises the builtin class typ with message. Any other error a host function
// returns raises RuntimeError with its text.
func Raise(typ, message string) error {
	return &Exception{Type: typ, Message: message}
}

// ToValue converts a Go value into an engine value:
//
//	nil, a nil pointer          None
//	bool                        bool
//	integers                    int (beyond int64: OverflowError)
//	float32, float64            float
//	string                      str
//	[]byte                      bytes
//	Tuple                       tuple
//	other slices and arrays     list
//	maps                        dict, in sorted key order
//	structs                     dict of the exported fields, named by a
//	                            `spy:"name"` tag; `spy:"-"` skips a field
//	pointers                    what they point to
//	*Value                      itself (of this runtime only)
//	Func                        a builtin function
//
// Decoding is the reverse; it accepts an int for a float, any iterable for
// a slice, and any mapping for a map or struct, whose unknown keys it
// ignores. Into an any it gives nil, bool, int64, float64, string, []byte,
// []any for a list, Tuple, and map[any]any for a dict, and a *Value for
// anything else, including dict keys that are not of those scalar types.
func (rt *Runtime) ToValue(x any) (*Value, error) {
	v, err := rt.ref(x)
	if err != nil {
		return nil, err
	}
	return newValue(rt, v), nil
}

// ref converts x into an owned reference.
func (rt *Runtime) ref(x any) (*C.SPYValue, error) {
	if err := rt.enter(); err != nil {
		return nil, err
	}
	return rt.reflectRef(reflect.ValueOf(x))
}

func (rt *Runtime) reflectRef(x reflect.Value) (*C.SPYValue, error) {
	c := rt.ctx
	if x.IsValid() && x.CanInterface() {
		switch x := x.Interface().(type) {
		case *Value:
			if x == nil {
				return C.spy_none(c), nil
			}
			if x.rt != rt {
				return nil, Raise("ValueError", "the value belongs to another runtime")
			}
			return C.spy_retain(x.ptr), nil
		case Func:
			cname := C.CString("function")
			defer C.free(unsafe.Pointer(cname))
			return rt.made(C.spy_go_native(c, cname, C.uintptr_t(cgo.NewHandle(x))))
		}
	}
	switch x.Kind() {
	case reflect.Invalid:
		return C.spy_none(c), nil
	case reflect.Pointer, reflect.Interface:
		if x.IsNil() {
			return C.spy_none(c), nil
		}
		return rt.reflectRef(x.Elem())
	case reflect.Bool:
		return rt.made(C.spy_bool(c, truth(x.Bool())))
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		return rt.made(C.spy_int(c, C.int64_t(x.Int())))
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Uintptr:
		if x.Uint() > math.MaxInt64 {
			return nil, overflow()
		}
		return rt.made(C.spy_int(c, C.int64_t(x.Uint())))
	case reflect.Float32, reflect.Float64:
		return rt.made(C.spy_float(c, C.double(x.Float())))
	case reflect.String:
		s := C.CString(x.String())
		defer C.free(unsafe.Pointer(s))
		return rt.made(C.spy_string(c, s, C.size_t(x.Len())))
	case reflect.Slice, reflect.Array:
		if x.Type().Elem().Kind() == reflect.Uint8 {
			bytes := make([]byte, x.Len())
			reflect.Copy(reflect.ValueOf(bytes), x)
			b := C.CBytes(bytes)
			defer C.free(b)
			return rt.made(C.spy_bytes(c, b, C.size_t(x.Len())))
		}
		if x.Type() == reflect.TypeFor[Tuple]() {
			return rt.tuple(x)
		}
		return rt.list(x)
	case reflect.Map:
		keys := x.MapKeys()
		slices.SortFunc(keys, compareKeys)
		return rt.dict(len(keys), func(i int) (string, reflect.Value, reflect.Value) {
			return "", keys[i], x.MapIndex(keys[i])
		})
	case reflect.Struct:
		fields := reflect.VisibleFields(x.Type())
		fields = slices.DeleteFunc(fields, func(f reflect.StructField) bool {
			return !f.IsExported() || f.Anonymous || f.Tag.Get("spy") == "-"
		})
		return rt.dict(len(fields), func(i int) (string, reflect.Value, reflect.Value) {
			return fieldName(fields[i]), reflect.Value{}, x.FieldByIndex(fields[i].Index)
		})
	}
	return nil, Raise("TypeError", fmt.Sprintf("cannot convert %s to a Python value", x.Type()))
}

func (rt *Runtime) made(v *C.SPYValue) (*C.SPYValue, error) {
	if v == nil {
		return nil, rt.take()
	}
	return v, nil
}

func (rt *Runtime) list(x reflect.Value) (*C.SPYValue, error) {
	list, err := rt.made(C.spy_list(rt.ctx))
	if err != nil {
		return nil, err
	}
	for i := range x.Len() {
		item, err := rt.reflectRef(x.Index(i))
		if err == nil {
			err = rt.check(C.spy_list_append(rt.ctx, list, item))
			C.spy_release(item)
		}
		if err != nil {
			C.spy_release(list)
			return nil, err
		}
	}
	return list, nil
}

func (rt *Runtime) tuple(x reflect.Value) (*C.SPYValue, error) {
	items := make([]*C.SPYValue, 0, x.Len())
	defer func() {
		for _, item := range items {
			C.spy_release(item)
		}
	}()
	for i := range x.Len() {
		item, err := rt.reflectRef(x.Index(i))
		if err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return rt.made(C.spy_tuple(rt.ctx, C.size_t(len(items)), unsafe.SliceData(items)))
}

// dict builds a dict of n pairs; pair returns a key as a string or a value.
func (rt *Runtime) dict(n int, pair func(int) (string, reflect.Value, reflect.Value)) (*C.SPYValue, error) {
	dict, err := rt.made(C.spy_dict(rt.ctx))
	if err != nil {
		return nil, err
	}
	for i := range n {
		name, key, item := pair(i)
		if !key.IsValid() {
			key = reflect.ValueOf(name)
		}
		err := rt.setItem(dict, key, item)
		if err != nil {
			C.spy_release(dict)
			return nil, err
		}
	}
	return dict, nil
}

func (rt *Runtime) setItem(dict *C.SPYValue, key, item reflect.Value) error {
	k, err := rt.reflectRef(key)
	if err != nil {
		return err
	}
	defer C.spy_release(k)
	i, err := rt.reflectRef(item)
	if err != nil {
		return err
	}
	defer C.spy_release(i)
	return rt.check(C.spy_set_item(rt.ctx, dict, k, i))
}

// compareKeys orders map keys: numbers and strings by value, others by
// their printed form.
func compareKeys(a, b reflect.Value) int {
	switch a.Kind() {
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		return cmp.Compare(a.Int(), b.Int())
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Uintptr:
		return cmp.Compare(a.Uint(), b.Uint())
	case reflect.Float32, reflect.Float64:
		return cmp.Compare(a.Float(), b.Float())
	case reflect.String:
		return cmp.Compare(a.String(), b.String())
	}
	return cmp.Compare(fmt.Sprint(a), fmt.Sprint(b))
}

func fieldName(f reflect.StructField) string {
	if name := f.Tag.Get("spy"); name != "" {
		return name
	}
	return f.Name
}

func overflow() error {
	return Raise("OverflowError", "int out of range for the Go type")
}

// decode stores v in what out points to.
func (rt *Runtime) decode(v *C.SPYValue, out any) error {
	p := reflect.ValueOf(out)
	if p.Kind() != reflect.Pointer || p.IsNil() {
		return Raise("TypeError", fmt.Sprintf("cannot decode into %T, which is not a pointer", out))
	}
	return rt.decodeInto(v, p.Elem())
}

func (rt *Runtime) decodeInto(v *C.SPYValue, out reflect.Value) error {
	c := rt.ctx
	typ := C.spy_type(v)
	switch out.Type() {
	case reflect.TypeFor[*Value]():
		out.Set(reflect.ValueOf(newValue(rt, C.spy_retain(v))))
		return nil
	case reflect.TypeFor[any]():
		x, err := rt.natural(v)
		if err == nil && x != nil {
			out.Set(reflect.ValueOf(x))
		} else if err == nil {
			out.SetZero()
		}
		return err
	}
	switch out.Kind() {
	case reflect.Pointer:
		if typ == C.SPY_NONE {
			out.SetZero()
			return nil
		}
		if out.IsNil() {
			out.Set(reflect.New(out.Type().Elem()))
		}
		return rt.decodeInto(v, out.Elem())
	case reflect.Bool:
		if typ != C.SPY_BOOL {
			return Raise("TypeError", "expected bool")
		}
		out.SetBool(C.spy_truth(v) != 0)
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		var n C.int64_t
		if C.spy_as_int(c, v, &n) != 0 {
			return rt.take()
		}
		if out.OverflowInt(int64(n)) {
			return overflow()
		}
		out.SetInt(int64(n))
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64, reflect.Uintptr:
		var n C.int64_t
		if C.spy_as_int(c, v, &n) != 0 {
			return rt.take()
		}
		if n < 0 || out.OverflowUint(uint64(n)) {
			return overflow()
		}
		out.SetUint(uint64(n))
	case reflect.Float32, reflect.Float64:
		var x C.double
		if C.spy_as_float(c, v, &x) != 0 {
			return rt.take()
		}
		out.SetFloat(float64(x))
	case reflect.String:
		var n C.size_t
		s := C.spy_as_string(c, v, &n)
		if s == nil {
			return rt.take()
		}
		// Lone surrogates keep their three-byte forms: a Go string holds them.
		out.SetString(C.GoStringN(s, C.int(n)))
	case reflect.Slice:
		if out.Type().Elem().Kind() == reflect.Uint8 && (typ == C.SPY_BYTES || typ == C.SPY_BYTEARRAY) {
			var n C.size_t
			b := C.spy_as_bytes(c, v, &n)
			if b == nil {
				return rt.take()
			}
			out.SetBytes(C.GoBytes(unsafe.Pointer(b), C.int(n)))
			return nil
		}
		out.Set(reflect.MakeSlice(out.Type(), 0, 0))
		return rt.each(v, func(item *C.SPYValue) error {
			out.Set(reflect.Append(out, reflect.New(out.Type().Elem()).Elem()))
			return rt.decodeInto(item, out.Index(out.Len()-1))
		})
	case reflect.Array:
		n := 0
		err := rt.each(v, func(item *C.SPYValue) error {
			if n++; n > out.Len() {
				return nil
			}
			return rt.decodeInto(item, out.Index(n-1))
		})
		if err == nil && n != out.Len() {
			return Raise("ValueError", fmt.Sprintf("expected %d items, got %d", out.Len(), n))
		}
		return err
	case reflect.Map:
		out.Set(reflect.MakeMap(out.Type()))
		return rt.pairs(v, func(key, item *C.SPYValue) error {
			k, i := reflect.New(out.Type().Key()).Elem(), reflect.New(out.Type().Elem()).Elem()
			if err := rt.decodeInto(key, k); err != nil {
				return err
			}
			if err := rt.decodeInto(item, i); err != nil {
				return err
			}
			out.SetMapIndex(k, i)
			return nil
		})
	case reflect.Struct:
		fields := map[string]reflect.StructField{}
		for _, f := range reflect.VisibleFields(out.Type()) {
			if f.IsExported() && !f.Anonymous && f.Tag.Get("spy") != "-" {
				fields[fieldName(f)] = f
			}
		}
		return rt.pairs(v, func(key, item *C.SPYValue) error {
			var name string
			if err := rt.decodeInto(key, reflect.ValueOf(&name).Elem()); err != nil {
				return err
			}
			f, ok := fields[name]
			if !ok {
				return nil
			}
			return rt.decodeInto(item, out.FieldByIndex(f.Index))
		})
	default:
		return Raise("TypeError", fmt.Sprintf("cannot decode into %s", out.Type()))
	}
	return nil
}

// natural is v as the Go value an any receives.
func (rt *Runtime) natural(v *C.SPYValue) (any, error) {
	var out reflect.Value
	switch C.spy_type(v) {
	case C.SPY_NONE:
		return nil, nil
	case C.SPY_BOOL:
		out = reflect.New(reflect.TypeFor[bool]())
	case C.SPY_INT:
		out = reflect.New(reflect.TypeFor[int64]())
	case C.SPY_FLOAT:
		out = reflect.New(reflect.TypeFor[float64]())
	case C.SPY_STRING:
		out = reflect.New(reflect.TypeFor[string]())
	case C.SPY_BYTES:
		out = reflect.New(reflect.TypeFor[[]byte]())
	case C.SPY_LIST:
		out = reflect.New(reflect.TypeFor[[]any]())
	case C.SPY_TUPLE:
		out = reflect.New(reflect.TypeFor[Tuple]())
	case C.SPY_DICT:
		dict := map[any]any{}
		err := rt.pairs(v, func(key, item *C.SPYValue) error {
			k, err := rt.natural(key)
			if err == nil && k != nil && !reflect.TypeOf(k).Comparable() {
				k = newValue(rt, C.spy_retain(key))
			}
			if err != nil {
				return err
			}
			dict[k], err = rt.natural(item)
			return err
		})
		return dict, err
	default:
		return newValue(rt, C.spy_retain(v)), nil
	}
	err := rt.decodeInto(v, out.Elem())
	return out.Elem().Interface(), err
}

// each calls f with each item of the iterable v, borrowed.
func (rt *Runtime) each(v *C.SPYValue, f func(*C.SPYValue) error) error {
	it, err := rt.made(C.spy_iter(rt.ctx, v))
	if err != nil {
		return err
	}
	defer C.spy_release(it)
	for {
		item := C.spy_next(rt.ctx, it)
		if item == nil {
			if *C.spy_error_type(rt.ctx) == 0 {
				return nil
			}
			return rt.take()
		}
		err := f(item)
		C.spy_release(item)
		if err != nil {
			return err
		}
	}
}

// pairs calls f with each key of the mapping v and its item, borrowed.
func (rt *Runtime) pairs(v *C.SPYValue, f func(key, item *C.SPYValue) error) error {
	return rt.each(v, func(key *C.SPYValue) error {
		item, err := rt.made(C.spy_get_item(rt.ctx, v, key))
		if err != nil {
			return err
		}
		defer C.spy_release(item)
		return f(key, item)
	})
}
