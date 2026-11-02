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
 * are compatible when both have the same major version, or, before 1.0, the
 * same minor version (docs/manual.md, 3.4.8 Stability). */
#define SPY_VERSION "0.5.0"
const char *spy_version(void);

/* == Types ==
 * Contexts and values are opaque. spy_type reports a value's kind; new kinds
 * are only ever appended. */
typedef struct SPYContext SPYContext;
typedef struct SPYValue SPYValue;
typedef enum {
    SPY_NONE, SPY_BOOL, SPY_INT, SPY_FLOAT, SPY_STRING, SPY_LIST, SPY_TUPLE,
    SPY_DICT, SPY_FUNCTION, SPY_NATIVE, SPY_MODULE, SPY_RANGE, SPY_BOUND_METHOD,
    SPY_ITERATOR, SPY_CLASS, SPY_INSTANCE, SPY_METHOD, SPY_SET, SPY_GENERATOR, SPY_CODE, SPY_SLICE,
    SPY_STATICMETHOD, SPY_CLASSMETHOD, SPY_PROPERTY, SPY_NOT_IMPLEMENTED, SPY_ELLIPSIS, SPY_COMPLEX, SPY_BYTES,
    SPY_COROUTINE, SPY_COROUTINE_ITERATOR, SPY_ASYNC_GENERATOR,
    SPY_ASYNC_GENERATOR_ASEND, SPY_ASYNC_GENERATOR_ATHROW, SPY_ANEXT_AWAITABLE,
    SPY_SUPER, SPY_FROZENSET, SPY_BYTEARRAY, SPY_DICT_KEYS, SPY_DICT_VALUES, SPY_DICT_ITEMS,
    SPY_TEMPLATE, SPY_INTERPOLATION, SPY_TEMPLATE_ITERATOR, SPY_MAPPINGPROXY, SPY_FROZENDICT, SPY_LAZY_IMPORT,
    SPY_FRAME, SPY_FRAME_LOCALS, SPY_MEMORYVIEW, SPY_SENTINEL, SPY_CELL, SPY_TRACEBACK,
    SPY_MEMBER_DESCRIPTOR, SPY_GETSET_DESCRIPTOR
} SPYType;

/* == Contexts == */

/* A new, independent context, or NULL when memory runs out. Contexts share
 * no mutable state, so different threads may use different contexts; one
 * context is never entered by two threads at once. */
SPYContext *spy_context_new(void);
/* Free a context and every value it still holds. Release external values
 * first; using one afterwards is invalid. */
void spy_context_free(SPYContext *);
/* A host pointer stored with the context, as QuickJS's JS_SetContextOpaque.
 * The context never dereferences or frees it. */
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
/* Python truth, through __bool__ and __len__. A failing method yields 0 with
 * the context's error set. */
int spy_truth(SPYValue *);
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

/* Return malloc-allocated, NUL-terminated source bytes, or NULL if absent.
 * The runtime decodes encoding declarations and frees source.
 * For a module "pkg.mod", it probes "pkg.mod.__init__" (package) first,
 * then "pkg.mod", then "pkg.mod.__namespace__", where any non-NULL result
 * makes a namespace package (PEP 420) without source. The host controls
 * search paths and source storage. */
typedef char *(*SPYModuleLoader)(void *, const char *);
void spy_set_module_loader(SPYContext *, SPYModuleLoader, void *);
/* Register a module, as QuickJS's JS_NewCModule. It is found before the
 * loader; its first import creates the module object, with __name__,
 * __package__, and __builtins__ set, and calls init to fill it. Init returns 0,
 * or -1 with an error set, which fails the import. A package's init sets
 * __path__; its submodules register under dotted names. Registering a name
 * again replaces its init. spy-std.c registers the standard ones. */
typedef int (*SPYModuleInit)(SPYContext *, SPYValue *);
int spy_new_module(SPYContext *, const char *, SPYModuleInit);
/* A module init that fills the module with engine primitives (the module
 * cache, frames, limits, the handled exception, collection, the weak table,
 * host output) for host modules written in Python. Programs reach them only
 * where the host registers it: spy_new_module(c, "_spy", spy_init_primitives). */
int spy_init_primitives(SPYContext *, SPYValue *);
/* Execute source with a module's namespace as its globals. */
int spy_exec_module(SPYContext *, SPYValue *, const char *source, const char *filename);

/* == Host services == */

/* Text output (print and sys.stdout), as UTF-8 chunks; a callback returns 0,
 * or nonzero to fail the write with OSError. Without one, print raises
 * OSError. */
typedef int (*SPYWrite)(void *, const char *, size_t);
void spy_set_output(SPYContext *, SPYWrite, void *);
/* Optional flush for the current output callback; shares its data pointer.
 * Without it the output callback is treated as unbuffered. Setting the
 * output callback clears it. */
typedef int (*SPYFlush)(void *);
void spy_set_flush(SPYContext *, SPYFlush);
/* Output for error text (the standard layer's sys.stderr); shares the output
 * callback until set. */
void spy_set_error_output(SPYContext *, SPYWrite, void *);
/* Return a malloc-allocated, NUL-terminated UTF-8 line for input(), with or
 * without its line ending, or NULL at the end of input (EOFError). Without a
 * reader, input() raises EOFError. */
typedef char *(*SPYReadLine)(void *);
void spy_set_input(SPYContext *, SPYReadLine, void *);
/* open() reaches only host directories mounted with spy_mount, at an absolute
 * path (NULL: the directory's own resolved path); paths are resolved inside
 * the mount, so symbolic links cannot leave it. The first mount is the
 * working directory for relative paths. Without a mount nothing is readable. */
enum { SPY_MOUNT_READ_ONLY = 1 };
int spy_mount(SPYContext *, const char *directory, const char *path, int flags);

/* == Limits and collection == */

/* Steps for each outermost call (docs/metering.md); zero means unlimited. */
void spy_set_step_limit(SPYContext *, size_t);
/* Bytes the engine may hold, and holds now; zero means unlimited. */
void spy_set_memory_limit(SPYContext *, size_t);
size_t spy_memory_used(const SPYContext *);
/* Polled at the first call, statement or native iteration after every 4096
 * steps, and inside long multiplication, division, integer formatting and
 * sorting; nonzero stops the context. It must not call into the engine. */
typedef int (*SPYInterrupt)(void *);
void spy_set_interrupt(SPYContext *, SPYInterrupt, void *);
/* Why the last outermost call stopped, or zero. */
enum { SPY_STOP_STEPS = 1, SPY_STOP_MEMORY, SPY_STOP_INTERRUPT };
int spy_stopped(const SPYContext *);
/* Steps the running or last outermost call spent. Calls and native
 * iteration spend only while a limit, an interrupt or a trace is set. */
size_t spy_steps_used(const SPYContext *);
/* Run the cycle collector and return how many unreachable values it freed;
 * count the values alive now. */
size_t spy_collect(SPYContext *);
size_t spy_live_values(const SPYContext *);

#ifdef __cplusplus
}
#endif
#endif
