#ifndef SPY_H
#define SPY_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* == Conventions ==
 * A SPYValue * a function returns is owned: the caller releases it with
 * spy_release. A SPYValue * passed in is borrowed: the callee retains what it
 * keeps. Strings passed in are copied. A function returning SPYValue * fails
 * with NULL, and one returning int fails with -1; either way the context's
 * error is set (Errors). Values belong to one context and never cross to
 * another. Exceptions to these rules are stated where they occur. */

/* == Versions ==
 * The header's version. spy_version returns the library's, so a host can
 * detect a library built from a different header. The header and library
 * are compatible when both are 0.8.0 or later with the same major version,
 * or, before 0.8, the same minor version (docs/manual.md, 3.4.8 Stability). */
#define SPY_VERSION "0.8.0"
const char *spy_version(void);

/* == Types ==
 * Contexts and values are opaque. spy_type reports a value's kind: one of
 * the builtin data types a host converts by content, exactly that type (an
 * instance of a subclass is SPY_OBJECT), or SPY_OBJECT for any other value.
 * The numbers are the engine's own tags, and never change. */
typedef struct SPYContext SPYContext;
typedef struct SPYValue SPYValue;
typedef enum {
    SPY_NONE = 0, SPY_BOOL = 1, SPY_INT = 2, SPY_FLOAT = 3, SPY_STRING = 4, SPY_LIST = 5, SPY_TUPLE = 6,
    SPY_DICT = 7, SPY_OBJECT = 15, SPY_SET = 17, SPY_COMPLEX = 26, SPY_BYTES = 27, SPY_FROZENSET = 35,
    SPY_BYTEARRAY = 36, SPY_FROZENDICT = 44
} SPYType;

/* == Contexts == */

/* A new, independent context, or NULL when memory runs out. Contexts share
 * no mutable state, so different threads may use different contexts; one
 * context is never entered by two threads at once. */
SPYContext *spy_context_new(void);
/* Free a context and every value it still holds. Release external values
 * first; using one afterwards is invalid. */
void spy_context_free(SPYContext *);
/* A host pointer stored with the context, for callbacks such as a module's
 * init to find their host. The context never dereferences or frees it. */
void spy_set_opaque(SPYContext *, void *);
void *spy_get_opaque(const SPYContext *);

/* == Evaluation == */

/* Parse and run source, NUL-terminated encoded bytes (UTF-8 unless declared
 * otherwise), in the context's globals, which persist between calls. A new
 * evaluation clears the previous error. spy_eval returns the final
 * expression's value (or None); spy_exec returns 0. Parsing precedes
 * execution, and a runtime error does not undo earlier assignments. Do not
 * evaluate from a callback running on the same context. */
SPYValue *spy_eval(SPYContext *, const char *source, const char *filename);
int spy_exec(SPYContext *, const char *source, const char *filename);
/* As spy_eval, and display each expression in interactive input through the
 * output callback. Expressions inside functions and class bodies are not
 * displayed. */
SPYValue *spy_eval_interactive(SPYContext *, const char *source, const char *filename);
/* Optimization level, as python -O (1: no asserts, __debug__ is False) and
 * -OO (2: no docstrings either); compile(optimize=-1) uses it. Default 0. */
void spy_set_optimize(SPYContext *, int level);
/* Read or bind a global; a missing name is a NameError. */
SPYValue *spy_get_global(SPYContext *, const char *);
int spy_set_global(SPYContext *, const char *, SPYValue *);

/* == Native functions == */

/* Arguments are borrowed. Return an owned value, or NULL with an error set. */
typedef SPYValue *(*SPYNative)(SPYContext *, size_t, SPYValue *const *, void *);
/* As SPYNative, with keyword arguments as a borrowed dict, or NULL when none. */
typedef SPYValue *(*SPYNativeKeywords)(SPYContext *, size_t, SPYValue *const *, SPYValue *, void *);
/* Bind a builtin function as a global. data belongs to the host and is passed
 * to every call. */
int spy_define(SPYContext *, const char *, SPYNative, void *);
/* A builtin function value. release, if given, runs on data when the value is
 * freed, including during spy_context_free, and when creation fails. */
SPYValue *spy_native(SPYContext *, const char *, SPYNativeKeywords, void *, void (*release)(void *));
/* Call any callable with borrowed positional arguments and, for
 * spy_call_keywords, a dict of str keys or NULL. */
SPYValue *spy_call(SPYContext *, SPYValue *, size_t, SPYValue *const *);
SPYValue *spy_call_keywords(SPYContext *, SPYValue *, size_t, SPYValue *const *, SPYValue *);

/* == Values == */

/* Add or drop a reference; both accept NULL. spy_retain returns its
 * argument. */
SPYValue *spy_retain(SPYValue *);
void spy_release(SPYValue *);
SPYType spy_type(const SPYValue *);
/* Constructors. spy_string takes UTF-8 text and spy_bytes any bytes; both
 * copy them. spy_tuple retains its items. */
SPYValue *spy_none(SPYContext *);
SPYValue *spy_bool(SPYContext *, int);
SPYValue *spy_int(SPYContext *, int64_t);
SPYValue *spy_float(SPYContext *, double);
SPYValue *spy_string(SPYContext *, const char *, size_t);
SPYValue *spy_bytes(SPYContext *, const void *, size_t);
SPYValue *spy_list(SPYContext *);
SPYValue *spy_tuple(SPYContext *, size_t, SPYValue *const *);
SPYValue *spy_dict(SPYContext *);
/* Append to a list (not a tuple), retaining the item. */
int spy_list_append(SPYContext *, SPYValue *, SPYValue *);
/* Python subscription, attribute access and iteration. spy_next returns NULL
 * with no error set when the iterator is exhausted. */
SPYValue *spy_get_item(SPYContext *, SPYValue *, SPYValue *);
int spy_set_item(SPYContext *, SPYValue *, SPYValue *, SPYValue *);
SPYValue *spy_get_attr(SPYContext *, SPYValue *, const char *);
int spy_set_attr(SPYContext *, SPYValue *, const char *, SPYValue *);
SPYValue *spy_iter(SPYContext *, SPYValue *);
SPYValue *spy_next(SPYContext *, SPYValue *);
/* Read a number into *out, or fail with TypeError. spy_as_int raises
 * OverflowError for an integer outside int64_t rather than narrowing it. */
int spy_as_int(SPYContext *, SPYValue *, int64_t *);
int spy_as_float(SPYContext *, SPYValue *, double *);
/* The text of a str (UTF-8) or the contents of a bytes, borrowed from the
 * value and valid while it lives; its length goes to the size_t pointer,
 * which may be NULL. NULL with TypeError for any other type. */
const char *spy_as_string(SPYContext *, SPYValue *, size_t *);
const unsigned char *spy_as_bytes(SPYContext *, SPYValue *, size_t *);
/* Python truth, through __bool__ and __len__: 1 or 0, or -1 when a method
 * fails. */
int spy_truth(SPYContext *, SPYValue *);
/* repr() and str(), as an owned SPY_STRING. */
SPYValue *spy_repr(SPYContext *, SPYValue *);
SPYValue *spy_str(SPYContext *, SPYValue *);

/* == Errors == */

/* The pending error: its exception type name and message (empty strings when
 * none), and where it was raised. The strings belong to the context and stay
 * valid until the error changes. */
const char *spy_error_type(const SPYContext *);
const char *spy_error_message(const SPYContext *);
const char *spy_error_filename(const SPYContext *);
size_t spy_error_line(const SPYContext *);
/* The error message as CPython's traceback module would display it, with its
 * keyword-typo suggestion for a generic SyntaxError. Valid until the next call. */
const char *spy_error_display(SPYContext *);
void spy_clear_error(SPYContext *);
/* Set an error of the named exception type, unless one is pending; always
 * returns NULL. */
SPYValue *spy_error(SPYContext *, const char *type, const char *message);
/* Raise an exception instance or class (borrowed); always returns NULL. */
SPYValue *spy_raise(SPYContext *, SPYValue *);
/* The pending exception object (owned), or NULL when no error is set. The
 * error stays set. */
SPYValue *spy_error_value(SPYContext *);

/* == Modules == */

/* Return the module's source as an owned bytes value, or NULL if absent (or
 * with an error set, which fails the import). The runtime decodes encoding
 * declarations. For a module "pkg.mod", it probes "pkg.mod.__init__"
 * (package) first, then "pkg.mod", then "pkg.mod.__namespace__", where any
 * non-NULL result makes a namespace package (PEP 420) without source. The
 * host controls search paths and source storage. */
typedef SPYValue *(*SPYModuleLoader)(SPYContext *, void *, const char *);
void spy_set_module_loader(SPYContext *, SPYModuleLoader, void *);
/* Register a module. It is found before the loader; its first import
 * creates the module object, with __name__, __package__, and __builtins__
 * set, and calls init to fill it. Init returns 0, or -1 with an error set,
 * which fails the import. A package's init sets
 * __path__; its submodules register under dotted names. Registering a name
 * again replaces its init. spy-std.c registers the standard ones. */
typedef int (*SPYModuleInit)(SPYContext *, SPYValue *);
int spy_new_module(SPYContext *, const char *, SPYModuleInit);
/* A module init that fills the module with engine primitives (the module
 * cache, frames, limits, the handled exception, collection, the weak table,
 * host output, the command line) for host modules written in Python. Programs reach them only
 * where the host registers it: spy_new_module(c, "_spy", spy_init_primitives). */
int spy_init_primitives(SPYContext *, SPYValue *);
/* Execute source with a module's namespace as its globals. */
int spy_exec_module(SPYContext *, SPYValue *, const char *source, const char *filename);

/* == Host services == */

/* Text output (print and sys.stdout), as UTF-8 chunks, and its flush; both
 * receive the data pointer and return 0, or nonzero to fail with OSError
 * unless the callback set an error of its own. Without a write callback print
 * raises OSError; without a flush the output is unbuffered. */
typedef int (*SPYWrite)(SPYContext *, void *, const char *, size_t);
typedef int (*SPYFlush)(SPYContext *, void *);
void spy_set_output(SPYContext *, SPYWrite, SPYFlush, void *);
/* Output for error text (the standard layer's sys.stderr), with its flush;
 * shares the output callbacks until set. */
void spy_set_error_output(SPYContext *, SPYWrite, SPYFlush, void *);
/* Return a line for input() as an owned str, with or without its line ending,
 * or NULL at the end of input (EOFError) or with an error set. Without a
 * reader, input() raises EOFError. */
typedef SPYValue *(*SPYReadLine)(SPYContext *, void *);
void spy_set_input(SPYContext *, SPYReadLine, void *);
/* The program's command lines, which the standard layer gives Python as
 * sys.argv (the script's, argc strings) and sys.orig_argv (the whole one the
 * program was started with), decoded as UTF-8 with surrogateescape and
 * copied. Set them before sys is first imported; until then both are empty
 * lists. Returns 0, or -1 with MemoryError. */
int spy_set_argv(SPYContext *, size_t argc, const char *const *argv, size_t orig_argc, const char *const *orig_argv);
/* open() reaches only host directories mounted with spy_mount, at an absolute
 * path (NULL: the directory's own resolved path); paths are resolved inside
 * the mount, so symbolic links cannot leave it. The first mount is the
 * working directory for relative paths. Without a mount nothing is readable. */
enum { SPY_MOUNT_READ_ONLY = 1 };
int spy_mount(SPYContext *, const char *directory, const char *path, int flags);

/* == Policy ==
 * Asked before a sensitive action, with an event name and a tuple of its
 * arguments. The engine asks for "open" (file, mode), "import" (name, on
 * the module's first load), "exec" (the source string of exec, eval or
 * compile) and "input" (the prompt, if any); hosts ask for their own events
 * with spy_policy_check. Return 0 to allow; nonzero refuses with
 * PermissionError, unless the policy set an error of its own. */
typedef int (*SPYPolicy)(SPYContext *, void *, const char *event, SPYValue *args);
void spy_set_policy(SPYContext *, SPYPolicy, void *);
/* Ask the policy about an event: 0 when allowed or no policy is set, or -1
 * with the error set. */
int spy_policy_check(SPYContext *, const char *event, SPYValue *args);

/* == Limits and collection == */

/* Bytes the engine holds now. */
size_t spy_memory_used(const SPYContext *);
/* Polled at the first call, statement or native iteration after every 4096
 * steps, and inside long multiplication, division, integer formatting and
 * sorting; nonzero stops the context. It must not call into the engine. */
typedef int (*SPYInterrupt)(void *);
void spy_set_interrupt(SPYContext *, SPYInterrupt, void *);
/* Why the last outermost call stopped, or zero. */
enum { SPY_STOP_STEPS = 1, SPY_STOP_MEMORY, SPY_STOP_INTERRUPT, SPY_STOP_OUTPUT };
/* Every limit through one call. STEPS (for each outermost call,
 * docs/metering.md), MEMORY (bytes the engine may hold) and OUTPUT (bytes
 * written to the output and error streams by each outermost call; going over
 * stops it, as a spent budget does) take zero for unlimited. RECURSION
 * (Python call depth, above the current one) and INT_DIGITS (the int-str
 * conversion limit; 0 for unlimited, or at least 640) are the parameters sys
 * can change too. STACK is the bytes of C stack the engine may use (4 MiB by
 * default), for hosts running it on a smaller stack. COLLECTION (2000 by
 * default) is how many values that can form cycles the heap must gain, while
 * the engine's memory doubles, after one collection before the cycle
 * collector runs again at the next statement; zero leaves collection to
 * spy_collect. Returns 0, or -1 with ValueError for an unknown limit or a
 * value out of range. */
enum { SPY_LIMIT_STEPS, SPY_LIMIT_MEMORY, SPY_LIMIT_OUTPUT, SPY_LIMIT_RECURSION, SPY_LIMIT_INT_DIGITS, SPY_LIMIT_STACK,
       SPY_LIMIT_COLLECTION };
int spy_set_limit(SPYContext *, int limit, size_t value);
size_t spy_get_limit(const SPYContext *, int limit);
int spy_stopped(const SPYContext *);
/* Steps the running or last outermost call spent. Calls and native
 * iteration spend only while a limit, an interrupt or a trace is set. */
size_t spy_steps_used(const SPYContext *);
/* Run the cycle collector and return how many unreachable values it freed;
 * count the values alive now. */
size_t spy_collect(SPYContext *);
size_t spy_live_values(const SPYContext *);

/* == Threads ==
 * A context runs one thread of Python code at a time. A host or module that
 * runs several, each on its own system thread, gives each a thread state and
 * lets one system thread at a time use the context, handing it on through
 * a lock or other synchronization. A thread state holds what belongs to one
 * thread: its pending error, running frames, handled exception, C stack
 * measure, and whether it is inside a host call. */
typedef struct SPYThread SPYThread;
/* A thread state with no frame and no error, or NULL with MemoryError. It
 * counts as inside a call, so its calls share the running outermost call's
 * step budget. States still held go with the context in spy_context_free. */
SPYThread *spy_thread_new(SPYContext *);
/* Exchange the context's thread state with the one held in the argument:
 * the thread taking the context swaps its state in, and swaps it out again
 * before another thread takes it. */
void spy_thread_swap(SPYContext *, SPYThread *);
/* Free a state with no running frame, and release what it holds. Not from a
 * release callback during spy_context_free. */
void spy_thread_free(SPYContext *, SPYThread *);
/* Called after every 4096 steps or so, before the engine evaluates the
 * next expression or statement, where it may hand the context to another
 * thread before it returns. A finalizer may run there anyway, so a builtin
 * operation is never interleaved: one that polls finishes first. NULL
 * removes it. Steps are counted while it is set. */
typedef void (*SPYSwitch)(SPYContext *, void *);
void spy_set_switch(SPYContext *, SPYSwitch, void *);

#ifdef __cplusplus
}
#endif
#endif
