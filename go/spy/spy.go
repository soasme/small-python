// Package spy embeds Small Python, a small Python 3.15 engine written in
// C11, in a Go program.
//
// The engine is compiled from source by cgo, so there is nothing to install
// beyond a C compiler. A [Runtime] owns one engine context; every [Value]
// holds a reference into it, which the garbage collector releases.
//
//	rt, err := spy.New()
//	if err != nil {
//		return err
//	}
//	defer rt.Close()
//	rt.Define("add", func(rt *spy.Runtime, args spy.Args) (any, error) {
//		var a, b int
//		if err := args.Scan(&a, &b); err != nil {
//			return nil, err
//		}
//		return a + b, nil
//	})
//	n, err := spy.As[int](rt.Eval("add(40, 2)"))
//
// The engine runs in this process, so it is only as trustworthy as its C
// code. To run untrusted code, use package worker, which runs each runtime
// in its own sandboxed process.
package spy

/*
#cgo CFLAGS: -std=c11 -w
#cgo LDFLAGS: -lm
#cgo linux LDFLAGS: -ldl
#include <stdint.h>
#include <stdlib.h>
#include "spy.h"
#include "spy-std.h"

void spy_go_bind(SPYContext *, uintptr_t);
uintptr_t spy_go_runtime(SPYContext *);
SPYValue *spy_go_native(SPYContext *, const char *, uintptr_t);
int spy_go_new_module(SPYContext *, const char *);
void spy_go_set_output(SPYContext *, int);
void spy_go_set_loader(SPYContext *, int);
void spy_go_set_policy(SPYContext *, int);
*/
import "C"

import (
	"errors"
	"fmt"
	"io"
	"os"
	"runtime/cgo"
	"strings"
	"sync"
	"unsafe"
)

// Version is the engine version, as spy.h defines it.
const Version = C.SPY_VERSION

// ErrClosed is returned by every operation on a closed runtime.
var ErrClosed = errors.New("spy: the runtime is closed")

// ErrRunning is Close's error inside one of the runtime's callbacks.
var ErrRunning = errors.New("spy: cannot close the runtime while it runs a host function")

// Func is a host function. It receives the runtime it runs in and the
// call's arguments; its result converts as by [Runtime.ToValue], and its
// error raises an exception (see [Raise]).
type Func func(rt *Runtime, args Args) (any, error)

// A Runtime is one independent engine context. It is not safe for
// concurrent use; inside a host function, the runtime it receives is the
// same one.
type Runtime struct {
	ctx     *C.SPYContext
	self    cgo.Handle
	output  io.Writer
	loader  func(name string) (source string, ok bool)
	policy  func(event string, args []*Value) error
	modules map[string]func(rt *Runtime, module *Value) error

	// The callbacks running; the engine runs beneath them.
	callbacks int

	// Values the garbage collector dropped, released on the next call.
	mu       sync.Mutex
	released []*C.SPYValue
	closed   bool
}

// New returns a runtime with the standard module sys.
func New() (*Runtime, error) {
	rt, err := NewBare()
	if err != nil {
		return nil, err
	}
	if C.spy_std_init(rt.ctx) != 0 {
		err := rt.take()
		rt.Close()
		return nil, err
	}
	return rt, nil
}

// NewBare returns a runtime with only the language core and its builtins.
func NewBare() (*Runtime, error) {
	ctx := C.spy_context_new()
	if ctx == nil {
		return nil, &Exception{Type: "MemoryError", Message: "cannot create a context"}
	}
	rt := &Runtime{ctx: ctx, modules: map[string]func(*Runtime, *Value) error{}}
	rt.self = cgo.NewHandle(rt)
	C.spy_go_bind(ctx, C.uintptr_t(rt.self))
	rt.SetOutput(os.Stdout)
	return rt, nil
}

// Close frees the context and every value in it. Values of a closed
// runtime return [ErrClosed]. Closing from a host function, module
// initializer, loader, output, or policy of the runtime fails with
// [ErrRunning], as the engine is running beneath it.
func (rt *Runtime) Close() error {
	if rt.callbacks > 0 {
		return ErrRunning
	}
	rt.mu.Lock()
	closed := rt.closed
	rt.closed = true
	rt.released = nil
	rt.mu.Unlock()
	if !closed {
		C.spy_context_free(rt.ctx)
		rt.self.Delete()
	}
	return nil
}

// Eval runs source and returns the value of its last expression statement.
func (rt *Runtime) Eval(source string) (*Value, error) {
	src, err := rt.source(source)
	if err != nil {
		return nil, err
	}
	defer C.free(unsafe.Pointer(src))
	return rt.wrap(C.spy_eval(rt.ctx, src, filename))
}

// Exec runs source for its effects.
func (rt *Runtime) Exec(source string) error {
	src, err := rt.source(source)
	if err != nil {
		return err
	}
	defer C.free(unsafe.Pointer(src))
	return rt.check(C.spy_exec(rt.ctx, src, filename))
}

// Get reads a global.
func (rt *Runtime) Get(name string) (*Value, error) {
	cname, err := rt.name(name)
	if err != nil {
		return nil, err
	}
	defer C.free(unsafe.Pointer(cname))
	return rt.wrap(C.spy_get_global(rt.ctx, cname))
}

// Set converts value as by [Runtime.ToValue] and binds it to a global.
func (rt *Runtime) Set(name string, value any) error {
	v, err := rt.ref(value)
	if err != nil {
		return err
	}
	defer C.spy_release(v)
	cname, err := rt.name(name)
	if err != nil {
		return err
	}
	defer C.free(unsafe.Pointer(cname))
	return rt.check(C.spy_set_global(rt.ctx, cname, v))
}

// Function returns a builtin function named name that calls f. The engine
// keeps f until the function value is freed.
func (rt *Runtime) Function(name string, f Func) (*Value, error) {
	cname, err := rt.name(name)
	if err != nil {
		return nil, err
	}
	defer C.free(unsafe.Pointer(cname))
	return rt.wrap(C.spy_go_native(rt.ctx, cname, C.uintptr_t(cgo.NewHandle(f))))
}

// Define binds [Runtime.Function] as the global name.
func (rt *Runtime) Define(name string, f Func) error {
	fn, err := rt.Function(name, f)
	if err != nil {
		return err
	}
	return rt.Set(name, fn)
}

// RegisterModule makes `import name` create a module and call init to fill
// it, as QuickJS's JS_NewCModule. Registering a name again replaces init.
func (rt *Runtime) RegisterModule(name string, init func(rt *Runtime, module *Value) error) error {
	cname, err := rt.name(name)
	if err != nil {
		return err
	}
	defer C.free(unsafe.Pointer(cname))
	rt.modules[name] = init
	return rt.check(C.spy_go_new_module(rt.ctx, cname))
}

// LoadNative opens the shared library at path, a native module built with
// spy-module.h, and registers it as name, so that `import name` runs its
// init. The policy is asked first, with "dlopen" (name, path). A library
// that fails to load is closed and raises ImportError; one that loads stays
// open for the life of the process. Its code runs outside the policy and
// the limits, with the process's rights.
func (rt *Runtime) LoadNative(name, path string) error {
	cname, err := rt.name(name)
	if err != nil {
		return err
	}
	defer C.free(unsafe.Pointer(cname))
	cpath, err := rt.name(path)
	if err != nil {
		return err
	}
	defer C.free(unsafe.Pointer(cpath))
	return rt.check(C.spy_std_load_native(rt.ctx, cname, cpath))
}

// ExecModule runs source with module's namespace as its globals.
func (rt *Runtime) ExecModule(module *Value, source, filename string) error {
	m, err := rt.ref(module)
	if err != nil {
		return err
	}
	defer C.spy_release(m)
	src, err := rt.source(source)
	if err != nil {
		return err
	}
	defer C.free(unsafe.Pointer(src))
	file, err := rt.name(filename)
	if err != nil {
		return err
	}
	defer C.free(unsafe.Pointer(file))
	return rt.check(C.spy_exec_module(rt.ctx, m, src, file))
}

// SetOutput sends everything engine code prints to w, os.Stdout by default.
// With a nil w, printing raises OSError.
func (rt *Runtime) SetOutput(w io.Writer) {
	if rt.enter() != nil {
		return
	}
	rt.output = w
	C.spy_go_set_output(rt.ctx, truth(w != nil))
}

// SetLoader maps a module name to its source, or reports that there is
// none. For `import pkg.mod` it is asked for pkg.mod.__init__ (a package),
// then pkg.mod, then pkg.mod.__namespace__ (a namespace package).
func (rt *Runtime) SetLoader(loader func(name string) (source string, ok bool)) {
	if rt.enter() != nil {
		return
	}
	rt.loader = loader
	C.spy_go_set_loader(rt.ctx, truth(loader != nil))
}

// Mount lets open() reach directory at the absolute engine path path, or
// at the directory's own resolved path when path is empty.
func (rt *Runtime) Mount(directory, path string, readOnly bool) error {
	dir, err := rt.name(directory)
	if err != nil {
		return err
	}
	defer C.free(unsafe.Pointer(dir))
	var at *C.char
	if path != "" {
		if at, err = rt.name(path); err != nil {
			return err
		}
		defer C.free(unsafe.Pointer(at))
	}
	var flags C.int
	if readOnly {
		flags = C.SPY_MOUNT_READ_ONLY
	}
	return rt.check(C.spy_mount(rt.ctx, dir, at, flags))
}

// A Limit names one of the bounds SetLimit sets.
type Limit int

const (
	LimitSteps     Limit = C.SPY_LIMIT_STEPS      // steps of each top-level call; 0 is unlimited
	LimitMemory    Limit = C.SPY_LIMIT_MEMORY     // bytes the engine holds; 0 is unlimited
	LimitOutput    Limit = C.SPY_LIMIT_OUTPUT     // bytes each top-level call prints; 0 is unlimited
	LimitRecursion Limit = C.SPY_LIMIT_RECURSION  // Python call depth
	LimitIntDigits Limit = C.SPY_LIMIT_INT_DIGITS // int-str conversion digits; 0 is unlimited
	LimitStack     Limit = C.SPY_LIMIT_STACK      // bytes of C stack the engine may use
)

// SetLimit sets one limit. A spent step, memory or output limit stops the
// call with RuntimeError (MemoryError for memory) that no handler catches.
func (rt *Runtime) SetLimit(limit Limit, value uint) error {
	if err := rt.enter(); err != nil {
		return err
	}
	return rt.check(C.spy_set_limit(rt.ctx, C.int(limit), C.size_t(value)))
}

// Limit returns a limit's current value.
func (rt *Runtime) Limit(limit Limit) uint {
	if rt.enter() != nil {
		return 0
	}
	return uint(C.spy_get_limit(rt.ctx, C.int(limit)))
}

// SetPolicy asks policy before open, a module's first import, exec, eval
// or compile of a string, input, and LoadNative, with the event's name
// ("open", "import", "exec", "input", "dlopen") and arguments. A non-nil
// error refuses: an *Exception raises its type, any other error
// PermissionError. nil removes the policy.
func (rt *Runtime) SetPolicy(policy func(event string, args []*Value) error) {
	if rt.enter() != nil {
		return
	}
	rt.policy = policy
	C.spy_go_set_policy(rt.ctx, truth(policy != nil))
}

// CheckPolicy asks the policy about an event of the host's own, such as a
// network request from a Go function; nil when allowed or no policy is set.
func (rt *Runtime) CheckPolicy(event string, args ...any) error {
	name, err := rt.name(event)
	if err != nil {
		return err
	}
	defer C.free(unsafe.Pointer(name))
	tuple, err := rt.ref(Tuple(args))
	if err != nil {
		return err
	}
	defer C.spy_release(tuple)
	return rt.check(C.spy_policy_check(rt.ctx, name, tuple))
}

// StepsUsed returns the steps the running or last top-level Eval or Exec
// spent; calls spend only while a step limit is set.
func (rt *Runtime) StepsUsed() uint {
	if rt.enter() != nil {
		return 0
	}
	return uint(C.spy_steps_used(rt.ctx))
}

// SetOptimize sets the optimization level, as python -O (1) and -OO (2).
func (rt *Runtime) SetOptimize(level int) {
	if rt.enter() == nil {
		C.spy_set_optimize(rt.ctx, C.int(level))
	}
}

// Collect runs the cycle collector and returns the number of values freed.
func (rt *Runtime) Collect() int {
	if rt.enter() != nil {
		return 0
	}
	return int(C.spy_collect(rt.ctx))
}

var filename = C.CString("<string>")

// enter releases what the garbage collector dropped, before each call into
// the engine.
func (rt *Runtime) enter() error {
	rt.mu.Lock()
	released, closed := rt.released, rt.closed
	rt.released = nil
	rt.mu.Unlock()
	if closed {
		return ErrClosed
	}
	for _, v := range released {
		C.spy_release(v)
	}
	return nil
}

// drop queues v's reference for release; the garbage collector calls it
// on its own goroutine.
func (rt *Runtime) drop(v *C.SPYValue) {
	rt.mu.Lock()
	if !rt.closed {
		rt.released = append(rt.released, v)
	}
	rt.mu.Unlock()
}

// wrap takes an owned engine result, or the pending error.
func (rt *Runtime) wrap(v *C.SPYValue) (*Value, error) {
	if v == nil {
		return nil, rt.take()
	}
	return newValue(rt, v), nil
}

func (rt *Runtime) check(status C.int) error {
	if status != 0 {
		return rt.take()
	}
	return nil
}

// take returns the context's pending error, leaving none.
func (rt *Runtime) take() error {
	e := &Exception{
		Type:     C.GoString(C.spy_error_type(rt.ctx)),
		Message:  C.GoString(C.spy_error_display(rt.ctx)),
		Filename: C.GoString(C.spy_error_filename(rt.ctx)),
		Line:     int(C.spy_error_line(rt.ctx)),
	}
	C.spy_clear_error(rt.ctx)
	if e.Type == "" {
		e.Type = "SystemError"
	}
	return e
}

// raise sets err as the context's pending error and returns NULL for the
// caller: an *Exception keeps its type, any other error is a RuntimeError.
func (rt *Runtime) raise(err error) *C.SPYValue {
	e, ok := err.(*Exception)
	if !ok && !errors.As(err, &e) {
		e = &Exception{Type: "RuntimeError", Message: err.Error()}
	}
	typ, message := C.CString(e.Type), C.CString(e.Message)
	defer C.free(unsafe.Pointer(typ))
	defer C.free(unsafe.Pointer(message))
	return C.spy_error(rt.ctx, typ, message)
}

// name is a C copy of name, for engine names and paths.
func (rt *Runtime) name(name string) (*C.char, error) {
	if err := rt.enter(); err != nil {
		return nil, err
	}
	if strings.IndexByte(name, 0) >= 0 {
		return nil, &Exception{Type: "ValueError", Message: "embedded null character"}
	}
	return C.CString(name), nil
}

func (rt *Runtime) source(source string) (*C.char, error) {
	if err := rt.enter(); err != nil {
		return nil, err
	}
	if strings.IndexByte(source, 0) >= 0 {
		return nil, &Exception{Type: "SyntaxError", Message: "source code string cannot contain null bytes"}
	}
	return C.CString(source), nil
}

func truth(b bool) C.int {
	if b {
		return 1
	}
	return 0
}

// The callbacks of bridge.c. None lets a panic unwind into C.

func runtimeOf(c *C.SPYContext) *Runtime {
	return cgo.Handle(C.spy_go_runtime(c)).Value().(*Runtime)
}

// guard runs a Go callback for the engine, turning its error or panic into
// an engine exception.
func (rt *Runtime) guard(f func() (*C.SPYValue, error)) (result *C.SPYValue) {
	rt.callbacks++
	defer func() {
		rt.callbacks--
		if p := recover(); p != nil {
			result = rt.raise(&Exception{Type: "RuntimeError", Message: fmt.Sprint("a Go callback panicked: ", p)})
		}
	}()
	v, err := f()
	if err != nil {
		return rt.raise(err)
	}
	return v
}

//export goCall
func goCall(c *C.SPYContext, argc C.size_t, argv **C.SPYValue, keywords *C.SPYValue, f C.uintptr_t) *C.SPYValue {
	rt := runtimeOf(c)
	return rt.guard(func() (*C.SPYValue, error) {
		args, err := rt.args(unsafe.Slice(argv, int(argc)), keywords)
		if err != nil {
			return nil, err
		}
		result, err := cgo.Handle(f).Value().(Func)(rt, args)
		if err != nil {
			return nil, err
		}
		return rt.ref(result)
	})
}

//export goRelease
func goRelease(f C.uintptr_t) {
	cgo.Handle(f).Delete()
}

//export goInit
func goInit(c *C.SPYContext, module *C.SPYValue) C.int {
	rt := runtimeOf(c)
	result := rt.guard(func() (*C.SPYValue, error) {
		m := newValue(rt, C.spy_retain(module))
		name, err := As[string](m.GetAttr("__name__"))
		if err != nil {
			return nil, err
		}
		init := rt.modules[name]
		if init == nil {
			return nil, &Exception{Type: "ImportError", Message: fmt.Sprintf("no module named '%s'", name)}
		}
		if err := init(rt, m); err != nil {
			return nil, err
		}
		return C.spy_none(c), nil
	})
	if result == nil {
		return -1
	}
	C.spy_release(result)
	return 0
}

//export goWrite
func goWrite(h C.uintptr_t, text *C.char, n C.size_t) (status C.int) {
	rt := cgo.Handle(h).Value().(*Runtime)
	rt.callbacks++
	defer func() {
		rt.callbacks--
		if recover() != nil {
			status = -1
		}
	}()
	if _, err := rt.output.Write(C.GoBytes(unsafe.Pointer(text), C.int(n))); err != nil {
		return -1
	}
	return 0
}

//export goPolicy
func goPolicy(c *C.SPYContext, event *C.char, args *C.SPYValue) C.int {
	rt := runtimeOf(c)
	result := rt.guard(func() (*C.SPYValue, error) {
		var items []*Value
		for item, err := range newValue(rt, C.spy_retain(args)).Iter() {
			if err != nil {
				return nil, err
			}
			items = append(items, item)
		}
		if err := rt.policy(C.GoString(event), items); err != nil {
			var e *Exception
			if !errors.As(err, &e) {
				e = &Exception{Type: "PermissionError", Message: err.Error()}
			}
			return nil, e
		}
		return C.spy_none(c), nil
	})
	C.spy_release(result)
	return truth(result == nil)
}

//export goLoad
func goLoad(c *C.SPYContext, h C.uintptr_t, name *C.char) (source *C.SPYValue) {
	rt := cgo.Handle(h).Value().(*Runtime)
	rt.callbacks++
	defer func() {
		rt.callbacks--
		if recover() != nil {
			source = nil
		}
	}()
	text, ok := rt.loader(C.GoString(name))
	if !ok {
		return nil
	}
	s := C.CString(text)
	defer C.free(unsafe.Pointer(s))
	return C.spy_bytes(c, unsafe.Pointer(s), C.size_t(len(text)))
}
