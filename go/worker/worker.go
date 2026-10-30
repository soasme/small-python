// Package worker runs untrusted Python from Go.
//
// Each [Runtime] starts one spy-worker process, which owns a Small Python
// context and seals itself under the operating system's sandbox before it
// runs any code, and speaks the worker protocol (docs/packaging/protocol.md)
// over its standard input and output. Values cross by copy; anything else
// stays in the worker and is reached through an [*Object] handle. A crash, a
// protocol violation, or an expired timeout loses the worker, and the
// runtime with it.
//
//	rt, err := worker.New(worker.Options{Timeout: 5 * time.Second})
//	if err != nil {
//		return err
//	}
//	defer rt.Close()
//	rt.Define("greet", func(rt *worker.Runtime, args []any, kwargs map[string]any) (any, error) {
//		if name, ok := args[0].(string); ok && len(args) == 1 {
//			return "hello " + name, nil
//		}
//		return nil, worker.Raise("TypeError", "greet(name)")
//	})
//	v, err := rt.Eval("greet('spy')") // "hello spy"
//
// Values cross as Go values: nil (None), bool, int64 or *big.Int (int),
// float64, complex128, string, []byte, ByteArray, []any (list), Tuple, Set,
// FrozenSet, Dict, *Object, and *Function. Sending also accepts the other
// integer and float types and map[string]any, in sorted key order. Sets and
// dicts are kept as sequences, so the parent never hashes what the worker
// sends. A string holding a lone surrogate keeps its three-byte form.
package worker

import (
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sync"
	"time"
)

// Tuple, Set, and FrozenSet are those engine types; a list is []any.
type (
	Tuple     []any
	Set       []any
	FrozenSet []any
	ByteArray []byte
)

// A Dict is a dict's items, in order.
type Dict []Item

// An Item is one key and value of a Dict.
type Item struct {
	Key, Value any
}

// What a runtime shares with its objects: where they queue their release.
type shared struct {
	mu       sync.Mutex
	released []uint64
	ended    bool
}

func (s *shared) release(id uint64) {
	s.mu.Lock()
	if !s.ended {
		s.released = append(s.released, id)
	}
	s.mu.Unlock()
}

// An Object is a handle to an engine value held by the worker. Operate on
// it with the runtime's methods. The worker releases it with the next
// message after the garbage collector finds it unreachable.
type Object struct {
	id     uint64
	shared *shared
}

func newObject(id uint64, s *shared) *Object {
	o := &Object{id, s}
	runtime.AddCleanup(o, s.release, id)
	return o
}

func (o *Object) String() string {
	return fmt.Sprintf("Object(%d)", o.id)
}

// A Function is a host function registered with a runtime, as a value to
// pass into it.
type Function struct {
	id     uint64
	name   string
	shared *shared
}

func (f *Function) String() string {
	return fmt.Sprintf("Function(%q)", f.name)
}

// An Exception is an engine exception that escaped, or one a host function
// raises.
type Exception struct {
	// Type is the class name, qualified by its module unless it is a builtin.
	Type string
	// Message is the text CPython's traceback shows after the type.
	Message  string
	Filename string
	Line     int64
	// Object is the exception itself, when the worker could send it.
	Object *Object
	// Cause is the host function's error the exception was raised for, if
	// it escaped unchanged.
	Cause error
}

func (e *Exception) Error() string {
	if e.Message == "" {
		return e.Type
	}
	return e.Type + ": " + e.Message
}

func (e *Exception) Unwrap() error {
	return e.Cause
}

// Raise returns an exception for a host function to raise: the engine
// raises the builtin class typ, or RuntimeError when there is none.
func Raise(typ, message string) error {
	return &Exception{Type: typ, Message: message}
}

// A WorkerError reports that the worker was lost: it crashed, broke the
// protocol, or was ended.
type WorkerError struct {
	Message string
	// State is the worker's exit, when it exited on its own.
	State *os.ProcessState
}

func (e *WorkerError) Error() string {
	return e.Message
}

// A TimeoutError reports that an operation ran past the runtime's timeout;
// the worker was ended.
type TimeoutError struct {
	Timeout time.Duration
}

func (e *TimeoutError) Error() string {
	return fmt.Sprintf("the operation exceeded the timeout of %v", e.Timeout)
}

// ErrInvalid is matched, with errors.Is, by the errors of misuse: a closed
// runtime, a value of another runtime, a message over the limit, Eval in a
// host function.
var ErrInvalid = errors.New("invalid use of the runtime")

type invalid string

func (e invalid) Error() string      { return string(e) }
func (invalid) Is(target error) bool { return target == ErrInvalid }

// A Func is a host function. It receives the runtime, for nested requests,
// and the call's arguments.
type Func func(rt *Runtime, args []any, kwargs map[string]any) (any, error)

// Op is a rich comparison of [Runtime.Compare].
type Op int

const (
	Lt Op = 11 + iota
	Le
	Eq
	Ne
	Gt
	Ge
)

// Options configure a [Runtime]. The zero value is the default.
type Options struct {
	// Bare leaves out the standard modules (sys and gc).
	Bare bool
	// StepLimit bounds the evaluation steps of each top-level Eval or Exec;
	// 0 is unlimited. Exceeding it raises RuntimeError in the engine.
	StepLimit uint64
	// MemoryLimit bounds the bytes the engine may hold; 0 is unlimited.
	// Exceeding it raises MemoryError in the engine.
	MemoryLimit uint64
	// Timeout bounds the time one operation may spend running in the
	// worker, host functions excluded; 0 is unlimited. Exceeding it ends
	// the worker with a *TimeoutError.
	Timeout time.Duration
	// MessageLimit is the largest message in bytes, either direction;
	// 0 means 64 MiB.
	MessageLimit uint32
	// Output receives printed text; nil means os.Stdout.
	Output io.Writer
	// Loader maps a module name to its source, or reports that there is
	// none. For `import pkg.mod` it is asked for pkg.mod.__init__ (a
	// package), then pkg.mod; source for pkg.mod.__namespace__ makes a
	// namespace package.
	Loader func(name string) (source string, ok bool)
	// Worker is the spy-worker executable; empty means the one on $PATH.
	Worker string
}

// A Runtime is one Small Python engine in its own worker process. It is not
// safe for concurrent use. While a host function runs, it receives the
// runtime and may make nested requests (Call, Get, object operations, ...),
// but not Eval or Exec.
type Runtime struct {
	cmd      *exec.Cmd
	to       chan []byte
	from     chan received
	done     chan struct{}
	shared   *shared
	lost     error
	closed   bool
	waited   bool
	timeout  time.Duration
	deadline time.Time
	limit    uint32

	functions []Func
	output    io.Writer
	loader    func(string) (string, bool)
	failure   *failure
	tokens    uint64
	depth     int
	callbacks int
	version   string
}

// The error a callback failed with, and the token naming it.
type failure struct {
	token uint64
	err   error
}

// New starts a worker and waits until it is ready.
func New(opts Options) (*Runtime, error) {
	if opts.Timeout < 0 {
		return nil, invalid("the timeout must not be negative")
	}
	if opts.MessageLimit == 0 {
		opts.MessageLimit = 64 << 20
	}
	if opts.Output == nil {
		opts.Output = os.Stdout
	}
	path := opts.Worker
	if path == "" {
		path = "spy-worker"
	}
	cannot := func(err error) error {
		return &WorkerError{Message: fmt.Sprintf("cannot start the worker: %v", err)}
	}
	cmd := exec.Command(path)
	cmd.Env = []string{}
	cmd.Dir = "/"
	cmd.Stderr = os.Stderr
	cmd.SysProcAttr = sysProcAttr()
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return nil, cannot(err)
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, cannot(err)
	}
	if err := cmd.Start(); err != nil {
		return nil, cannot(err)
	}
	rt := &Runtime{
		cmd:     cmd,
		to:      writer(stdin),
		done:    make(chan struct{}),
		shared:  &shared{},
		timeout: opts.Timeout,
		limit:   opts.MessageLimit,
		output:  opts.Output,
		loader:  opts.Loader,
	}
	rt.from = reader(stdout, opts.MessageLimit, rt.done)
	options := Dict{
		{"std", !opts.Bare},
		{"step_limit", opts.StepLimit},
		{"memory_limit", opts.MemoryLimit},
		{"message_limit", opts.MessageLimit},
	}
	version, err := rt.run(msgInit, options)
	if err != nil {
		return nil, err
	}
	var ok bool
	if rt.version, ok = version.(string); !ok {
		return nil, rt.violation("malformed version")
	}
	return rt, nil
}

// Version returns the engine version the worker reported.
func (rt *Runtime) Version() string {
	return rt.version
}

// Pid returns the worker's process id.
func (rt *Runtime) Pid() int {
	return rt.cmd.Process.Pid
}

// Eval runs source and returns the value of its last expression statement.
func (rt *Runtime) Eval(source string) (any, error) {
	return rt.run(msgEval, source, "<string>")
}

// Exec runs source for its effects.
func (rt *Runtime) Exec(source string) error {
	_, err := rt.run(msgExec, source, "<string>")
	return err
}

// Call calls function: a global name (string), an *Object, or a *Function.
func (rt *Runtime) Call(function any, args []any, kwargs map[string]any) (any, error) {
	return rt.run(msgCall, function, Tuple(args), kwargs)
}

// Get reads a global, falling back to builtins; ok is false when there is
// none.
func (rt *Runtime) Get(name string) (value any, ok bool, err error) {
	value, err = rt.run(msgGet, name)
	if e, isException := err.(*Exception); isException && e.Type == "NameError" {
		return nil, false, nil
	}
	return value, err == nil, err
}

// Set binds a global.
func (rt *Runtime) Set(name string, value any) error {
	_, err := rt.run(msgSet, name, value)
	return err
}

// Delete deletes a global; a KeyError when there is none.
func (rt *Runtime) Delete(name string) error {
	_, err := rt.run(msgDelete, name)
	return err
}

// Function returns a host function as a value to pass into the engine,
// where it becomes a builtin function named name. The runtime keeps f until
// it ends.
func (rt *Runtime) Function(name string, f Func) *Function {
	rt.functions = append(rt.functions, f)
	return &Function{uint64(len(rt.functions)), name, rt.shared}
}

// Define binds a host function as the global name.
func (rt *Runtime) Define(name string, f Func) error {
	return rt.Set(name, rt.Function(name, f))
}

// RegisterModule makes `import name` create a module whose attributes are
// members, then run source in it. Registering a name again replaces it.
func (rt *Runtime) RegisterModule(name string, members map[string]any, source string) error {
	_, err := rt.run(msgModule, name, members, source)
	return err
}

// Mount lets the engine's open() reach a host directory at the absolute
// engine path path, or at its resolved host path when path is empty. Mounts
// are fixed once the worker has run code.
func (rt *Runtime) Mount(directory, path string, readOnly bool) error {
	resolved, err := resolve(directory)
	if err != nil {
		return invalid(fmt.Sprintf("cannot mount '%s': %v", directory, err))
	}
	if path == "" {
		path = resolved
	}
	_, err = rt.run(msgMount, resolved, path, readOnly)
	return err
}

// Collect runs the cycle collector and returns the number of values freed.
func (rt *Runtime) Collect() (int64, error) {
	n, err := rt.run(msgCollect)
	if err != nil {
		return 0, err
	}
	if n, ok := n.(int64); ok {
		return n, nil
	}
	return 0, rt.violation("malformed collect result")
}

// GetAttr is getattr(object, name).
func (rt *Runtime) GetAttr(object *Object, name string) (any, error) {
	return rt.op(1, object, name)
}

// SetAttr is setattr(object, name, value).
func (rt *Runtime) SetAttr(object *Object, name string, value any) error {
	_, err := rt.op(2, object, name, value)
	return err
}

// GetItem is object[key].
func (rt *Runtime) GetItem(object *Object, key any) (any, error) {
	return rt.op(3, object, key)
}

// SetItem is object[key] = value.
func (rt *Runtime) SetItem(object *Object, key, value any) error {
	_, err := rt.op(4, object, key, value)
	return err
}

// Len is len(object).
func (rt *Runtime) Len(object *Object) (int64, error) {
	return result[int64](rt, "length")(rt.op(5, object))
}

// Contains is item in object.
func (rt *Runtime) Contains(object *Object, item any) (bool, error) {
	return result[bool](rt, "membership")(rt.op(6, object, item))
}

// Iter is iter(object).
func (rt *Runtime) Iter(object *Object) (any, error) {
	return rt.op(7, object)
}

// Next is next(object); ok is false at the end.
func (rt *Runtime) Next(object *Object) (value any, ok bool, err error) {
	value, err = rt.op(8, object)
	if e, isException := err.(*Exception); isException && e.Type == "StopIteration" {
		return nil, false, nil
	}
	return value, err == nil, err
}

// Truth is bool(object).
func (rt *Runtime) Truth(object *Object) (bool, error) {
	return result[bool](rt, "truth")(rt.op(9, object))
}

// Hash is hash(object).
func (rt *Runtime) Hash(object *Object) (int64, error) {
	return result[int64](rt, "hash")(rt.op(10, object))
}

// Compare is object < other, or another rich comparison.
func (rt *Runtime) Compare(object *Object, op Op, other any) (any, error) {
	return rt.op(int64(op), object, other)
}

// Repr is repr(object).
func (rt *Runtime) Repr(object *Object) (string, error) {
	return result[string](rt, "repr")(rt.op(17, object))
}

// Str is str(object).
func (rt *Runtime) Str(object *Object) (string, error) {
	return result[string](rt, "str")(rt.op(18, object))
}

// Dir is dir(object).
func (rt *Runtime) Dir(object *Object) (any, error) {
	return rt.op(19, object)
}

// result checks the type of an operation's result.
func result[T any](rt *Runtime, what string) func(any, error) (T, error) {
	return func(v any, err error) (T, error) {
		t, ok := v.(T)
		if err == nil && !ok {
			err = rt.violation("malformed " + what)
		}
		return t, err
	}
}

// Closed reports whether the runtime was closed or lost.
func (rt *Runtime) Closed() bool {
	return rt.closed || rt.lost != nil
}

// Close ends the worker: it closes the worker's input, waits a second for
// it to exit, and terminates it otherwise.
func (rt *Runtime) Close() error {
	if rt.closed {
		return nil
	}
	rt.closed = true
	if rt.lost == nil {
		close(rt.to)
		rt.to = nil
		select {
		case <-rt.from:
		case <-time.After(time.Second):
		}
		rt.end()
	}
	return nil
}

func (rt *Runtime) op(op int64, object *Object, operands ...any) (any, error) {
	return rt.run(msgOp, append([]any{op, object}, operands...)...)
}

// run makes one request, top-level or nested; the timeout spans the top
// level.
func (rt *Runtime) run(kind byte, fields ...any) (any, error) {
	if rt.lost != nil {
		return nil, rt.lost
	}
	if rt.closed {
		return nil, invalid("the runtime is closed")
	}
	if (kind == msgEval || kind == msgExec) && rt.callbacks > 0 {
		return nil, invalid("cannot evaluate source while a host function of this runtime is running")
	}
	top := rt.depth == 0
	if top && rt.timeout > 0 {
		rt.deadline = time.Now().Add(rt.timeout)
	}
	rt.depth++
	defer func() {
		rt.depth--
		if top {
			rt.deadline = time.Time{}
		}
	}()
	data, err := message(kind, rt.shared, fields...)
	if err != nil {
		return nil, err
	}
	if len(data)-4 > int(rt.limit) {
		return nil, invalid("message exceeds the limit")
	}
	if err := rt.send(data); err != nil {
		return nil, err
	}
	reply, err := rt.awaitReply()
	if err != nil {
		return nil, err
	}
	values, err := rt.decode(reply, 1)
	if err != nil {
		return nil, err
	}
	if reply[0] == msgRaise {
		return nil, rt.engineError(values[0])
	}
	return values[0], nil
}

func (rt *Runtime) awaitReply() ([]byte, error) {
	for {
		message, err := rt.receive()
		if err != nil {
			return nil, err
		}
		switch message[0] {
		case msgResult, msgRaise:
			return message, nil
		case msgHost, msgLoad, msgOutput:
			if err := rt.serve(message); err != nil {
				return nil, err
			}
		default:
			return nil, rt.violation(fmt.Sprintf("unexpected message kind %#x", message[0]))
		}
	}
}

// send sends data, after a notice of the handles released since the last.
func (rt *Runtime) send(data []byte) error {
	rt.shared.mu.Lock()
	released := rt.shared.released
	rt.shared.released = nil
	rt.shared.mu.Unlock()
	messages := [][]byte{data}
	if len(released) > 0 {
		ids := make(Tuple, len(released))
		for i, id := range released {
			ids[i] = id
		}
		notice, err := message(msgRelease, rt.shared, ids)
		if err != nil {
			return err
		}
		messages = [][]byte{notice, data}
	}
	for _, m := range messages {
		select {
		case rt.to <- m:
		case <-rt.expiry():
			return rt.lose(&TimeoutError{rt.timeout})
		}
	}
	return nil
}

// expiry fires at the deadline, or never without one.
func (rt *Runtime) expiry() <-chan time.Time {
	if rt.deadline.IsZero() {
		return nil
	}
	return time.After(time.Until(rt.deadline))
}

func (rt *Runtime) receive() ([]byte, error) {
	select {
	case r := <-rt.from:
		switch {
		case r.message != nil:
			return r.message, nil
		case r.violation != "":
			return nil, rt.violation(r.violation)
		}
		return nil, rt.exited()
	case <-rt.expiry():
		return nil, rt.lose(&TimeoutError{rt.timeout})
	}
}

func (rt *Runtime) decode(message []byte, n int) ([]any, error) {
	values, err := decode(message, rt.shared, n)
	if err != nil {
		return nil, rt.violation(err.Error())
	}
	return values, nil
}

// Losing the worker (protocol.md 8).

func (rt *Runtime) violation(what string) error {
	return rt.lose(&WorkerError{Message: "the worker broke the protocol: " + what})
}

func (rt *Runtime) exited() error {
	rt.waited = true
	rt.cmd.Wait()
	state := rt.cmd.ProcessState
	return rt.lose(&WorkerError{Message: "the worker ended: " + state.String(), State: state})
}

func (rt *Runtime) lose(err error) error {
	if rt.lost == nil {
		rt.lost = err
		rt.end()
	}
	return rt.lost
}

func (rt *Runtime) end() {
	rt.shared.mu.Lock()
	rt.shared.ended = true
	rt.shared.released = nil
	rt.shared.mu.Unlock()
	if rt.to != nil {
		close(rt.to)
		rt.to = nil
	}
	close(rt.done)
	if !rt.waited {
		rt.waited = true
		rt.cmd.Process.Kill()
		rt.cmd.Wait()
	}
	rt.functions = nil
	rt.failure = nil
	rt.output = nil
	rt.loader = nil
}

// engineError is the exception of a worker's RAISE.
func (rt *Runtime) engineError(raised any) error {
	fields := map[string]any{}
	dict, _ := raised.(Dict)
	for _, item := range dict {
		key, _ := item.Key.(string)
		if _, seen := fields[key]; seen {
			return rt.violation("malformed error")
		}
		fields[key] = item.Value
	}
	e := &Exception{}
	var token int64
	exception, hasException := fields["exception"]
	ok := len(fields) == 6 && hasException &&
		(exception == nil || take(&e.Object, exception)) &&
		take(&e.Type, fields["type"]) && take(&e.Message, fields["message"]) &&
		take(&e.Filename, fields["filename"]) && take(&e.Line, fields["line"]) &&
		take(&token, fields["token"])
	if !ok {
		return rt.violation("malformed error")
	}
	if rt.failure != nil && int64(rt.failure.token) == token {
		e.Cause = rt.failure.err
	}
	rt.failure = nil
	return e
}

// take stores x in dst if it is a T.
func take[T any](dst *T, x any) bool {
	t, ok := x.(T)
	*dst = t
	return ok
}

// Requests from the worker.

func (rt *Runtime) serve(request []byte) error {
	started := time.Now()
	rt.callbacks++
	value, failed, err := rt.dispatch(request)
	rt.callbacks--
	if !rt.deadline.IsZero() {
		rt.deadline = rt.deadline.Add(time.Since(started))
	}
	if rt.lost != nil {
		return rt.lost
	}
	if err != nil {
		return err
	}
	var reply []byte
	if failed == nil {
		reply, failed = message(msgResult, rt.shared, value)
		if failed == nil && len(reply)-4 > int(rt.limit) {
			failed = invalid("message exceeds the limit")
		}
	}
	if failed != nil {
		if reply, err = message(msgRaise, rt.shared, rt.failureOf(failed)); err != nil {
			return err
		}
	}
	return rt.send(reply)
}

// dispatch serves a request: err is the protocol's, failed the callback's.
func (rt *Runtime) dispatch(request []byte) (value any, failed error, err error) {
	switch request[0] {
	case msgHost:
		fields, err := rt.decode(request, 3)
		if err != nil {
			return nil, nil, err
		}
		id, _ := fields[0].(int64)
		args, isTuple := fields[1].(Tuple)
		kwargs, isDict := keywords(fields[2])
		if id < 1 || id > int64(len(rt.functions)) || !isTuple || !isDict {
			return nil, nil, rt.violation("malformed host call")
		}
		// A panic leaves the worker mid-turn: lose it, then go on panicking.
		defer func() {
			if p := recover(); p != nil {
				rt.lose(&WorkerError{Message: "a host function panicked"})
				panic(p)
			}
		}()
		value, failed = rt.functions[id-1](rt, args, kwargs)
		return value, failed, nil
	case msgLoad:
		fields, err := rt.decode(request, 1)
		if err != nil {
			return nil, nil, err
		}
		name, ok := fields[0].(string)
		if !ok {
			return nil, nil, rt.violation("malformed load")
		}
		if rt.loader != nil {
			if source, ok := rt.loader(name); ok {
				return source, nil, nil
			}
		}
		return nil, nil, nil
	default:
		fields, err := rt.decode(request, 1)
		if err != nil {
			return nil, nil, err
		}
		text, ok := fields[0].(string)
		if !ok {
			return nil, nil, rt.violation("malformed output")
		}
		if _, err := io.WriteString(rt.output, text); err != nil {
			return nil, Raise("OSError", err.Error()), nil
		}
		return nil, nil, nil
	}
}

// resolve returns directory as an absolute path free of symbolic links.
func resolve(directory string) (string, error) {
	resolved, err := filepath.Abs(directory)
	if err == nil {
		resolved, err = filepath.EvalSymlinks(resolved)
	}
	if err != nil {
		return "", err
	}
	if info, err := os.Stat(resolved); err != nil || !info.IsDir() {
		return "", errors.New("not a directory")
	}
	return resolved, nil
}

// keywords converts a dict of str keys.
func keywords(x any) (map[string]any, bool) {
	dict, ok := x.(Dict)
	kwargs := make(map[string]any, len(dict))
	for _, item := range dict {
		key, isString := item.Key.(string)
		ok = ok && isString
		kwargs[key] = item.Value
	}
	return kwargs, ok
}

// failureOf is the failure (protocol.md 7.4) for an error a callback
// returned.
func (rt *Runtime) failureOf(err error) Dict {
	rt.tokens++
	token := rt.tokens
	rt.failure = &failure{token, err}
	var e *Exception
	if errors.As(err, &e) && e.Object != nil && e.Object.shared == rt.shared {
		return Dict{{"raise", e.Object}, {"token", token}}
	}
	class, message := "RuntimeError", err.Error()
	switch {
	case e != nil:
		class, message = e.Type, e.Message
	case errors.Is(err, ErrInvalid):
		class = "ValueError"
	}
	return Dict{{"classes", Tuple{class}}, {"args", nil}, {"message", message}, {"token", token}}
}

// A received frame, a violation, or the end of the stream.
type received struct {
	message   []byte
	violation string
}

// reader reads frames from the worker on a goroutine of its own, so the
// parent can wait for them with a deadline. Lengths are checked before
// allocating.
func reader(from io.Reader, limit uint32, done <-chan struct{}) chan received {
	ch := make(chan received)
	go func() {
		for {
			r := frame(from, limit)
			select {
			case ch <- r:
			case <-done:
				return
			}
			if r.message == nil {
				return
			}
		}
	}()
	return ch
}

func frame(from io.Reader, limit uint32) received {
	var length [4]byte
	if _, err := io.ReadFull(from, length[:]); err != nil {
		return received{}
	}
	n := uint32(length[0]) | uint32(length[1])<<8 | uint32(length[2])<<16 | uint32(length[3])<<24
	if n < 1 || n > limit {
		return received{violation: "message length out of range"}
	}
	message := make([]byte, n)
	if _, err := io.ReadFull(from, message); err != nil {
		return received{}
	}
	return received{message: message}
}

// writer writes to the worker on a goroutine of its own, so a worker that
// stops reading cannot block the parent past its deadline. Closing the
// channel closes the worker's input.
func writer(to io.WriteCloser) chan []byte {
	ch := make(chan []byte, 2)
	go func() {
		defer to.Close()
		for m := range ch {
			if _, err := to.Write(m); err != nil {
				for range ch {
				}
				return
			}
		}
	}()
	return ch
}
