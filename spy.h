#ifndef SPY_H
#define SPY_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SPY_VERSION "0.2.0"

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

/* Arguments are borrowed. Return an owned value, or NULL with an error set. */
typedef SPYValue *(*SPYNative)(SPYContext *, size_t, SPYValue *const *, void *);
/* As SPYNative, with keyword arguments as a borrowed dict, or NULL when none. */
typedef SPYValue *(*SPYNativeKeywords)(SPYContext *, size_t, SPYValue *const *, SPYValue *, void *);
typedef int (*SPYWrite)(void *, const char *, size_t);
typedef int (*SPYFlush)(void *);
/* Return malloc-allocated, NUL-terminated source bytes, or NULL if absent.
 * The runtime decodes encoding declarations and frees source.
 * For a module "pkg.mod", it probes "pkg.mod.__init__" (package) first,
 * then "pkg.mod", then "pkg.mod.__namespace__", where any non-NULL result
 * makes a namespace package (PEP 420) without source. The host controls
 * search paths and source storage. */
typedef char *(*SPYModuleLoader)(void *, const char *);

SPYContext *spy_context_new(void);
/* Release all external values before freeing their context. No shared contexts
 * or values across threads; independent contexts have no global mutable state. */
void spy_context_free(SPYContext *);
/* A host pointer stored with the context, as QuickJS's JS_SetContextOpaque. */
void spy_set_opaque(SPYContext *, void *);
void *spy_get_opaque(const SPYContext *);
void spy_set_output(SPYContext *, SPYWrite, void *);
/* Optional flush for the current output callback; shares its data pointer.
 * Without it the output callback is treated as unbuffered. */
void spy_set_flush(SPYContext *, SPYFlush);
void spy_set_module_loader(SPYContext *, SPYModuleLoader, void *);
/* Return a malloc-allocated, NUL-terminated UTF-8 line for input(), with or
 * without its line ending, or NULL at the end of input (EOFError). Without a
 * reader, input() raises EOFError. */
typedef char *(*SPYReadLine)(void *);
void spy_set_input(SPYContext *, SPYReadLine, void *);
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
/* Zero means unlimited. Budget resets for each top-level evaluation. */
/* open() reaches only host directories mounted with spy_mount, at an absolute
 * path (NULL: the directory's own resolved path); paths are resolved inside
 * the mount, so symbolic links cannot leave it. The first mount is the
 * working directory for relative paths. Without a mount nothing is readable. */
enum { SPY_MOUNT_READ_ONLY = 1 };
int spy_mount(SPYContext *, const char *directory, const char *path, int flags);
void spy_set_step_limit(SPYContext *, size_t);
size_t spy_collect(SPYContext *);
size_t spy_live_values(const SPYContext *);

/* Source is NUL-terminated encoded bytes (UTF-8 unless declared otherwise).
 * eval returns the final expression (or None); exec returns 0 or -1.
 * All returned SPYValue pointers are owned; NULL indicates an error.
 * A new evaluation clears the previous error, but preserves globals. */
SPYValue *spy_eval(SPYContext *, const char *source, const char *filename);
/* Display each expression in interactive input through the output callback.
 * Expressions inside functions and class bodies are not displayed. */
SPYValue *spy_eval_interactive(SPYContext *, const char *source, const char *filename);
int spy_exec(SPYContext *, const char *source, const char *filename);
SPYValue *spy_get_global(SPYContext *, const char *);
int spy_set_global(SPYContext *, const char *, SPYValue *);
int spy_define(SPYContext *, const char *, SPYNative, void *);
SPYValue *spy_call(SPYContext *, SPYValue *, size_t, SPYValue *const *);
/* keywords is a dict of str keys, or NULL. */
SPYValue *spy_call_keywords(SPYContext *, SPYValue *, size_t, SPYValue *const *, SPYValue *);
/* A builtin function value. release, if given, runs on data when the value is
 * freed, including during spy_context_free, and when creation fails. */
SPYValue *spy_native(SPYContext *, const char *, SPYNativeKeywords, void *, void (*release)(void *));

SPYValue *spy_retain(SPYValue *);
void spy_release(SPYValue *);
SPYType spy_type(const SPYValue *);
SPYValue *spy_none(SPYContext *);
SPYValue *spy_bool(SPYContext *, int);
SPYValue *spy_int(SPYContext *, int64_t);
SPYValue *spy_float(SPYContext *, double);
SPYValue *spy_string(SPYContext *, const char *, size_t);
SPYValue *spy_bytes(SPYContext *, const void *, size_t);
SPYValue *spy_list(SPYContext *);
int spy_list_append(SPYContext *, SPYValue *, SPYValue *);
SPYValue *spy_tuple(SPYContext *, size_t, SPYValue *const *);
SPYValue *spy_dict(SPYContext *);
/* Python subscription, attribute access, and iteration. spy_next returns NULL
 * with no error set when the iterator is exhausted. */
SPYValue *spy_get_item(SPYContext *, SPYValue *, SPYValue *);
int spy_set_item(SPYContext *, SPYValue *, SPYValue *, SPYValue *);
SPYValue *spy_get_attr(SPYContext *, SPYValue *, const char *);
int spy_set_attr(SPYContext *, SPYValue *, const char *, SPYValue *);
SPYValue *spy_iter(SPYContext *, SPYValue *);
SPYValue *spy_next(SPYContext *, SPYValue *);
/* Large Python integers raise OverflowError rather than narrowing silently. */
int spy_as_int(SPYContext *, SPYValue *, int64_t *);
int spy_as_float(SPYContext *, SPYValue *, double *);
const char *spy_as_string(SPYContext *, SPYValue *, size_t *);
const unsigned char *spy_as_bytes(SPYContext *, SPYValue *, size_t *);
int spy_truth(SPYValue *);
/* String conversion returns an owned SPY_STRING. */
SPYValue *spy_repr(SPYContext *, SPYValue *);
SPYValue *spy_str(SPYContext *, SPYValue *);

const char *spy_error_type(const SPYContext *);
const char *spy_error_message(const SPYContext *);
/* The error message as CPython's traceback module would display it, with its
 * keyword-typo suggestion for a generic SyntaxError. Valid until the next call. */
const char *spy_error_display(SPYContext *);
const char *spy_error_filename(const SPYContext *);
size_t spy_error_line(const SPYContext *);
void spy_clear_error(SPYContext *);
SPYValue *spy_error(SPYContext *, const char *type, const char *message);
/* The pending exception object (owned), or NULL when no error is set. The
 * error stays set. */
SPYValue *spy_error_value(SPYContext *);
/* Raise an exception instance or class; always returns NULL. */
SPYValue *spy_raise(SPYContext *, SPYValue *);

#ifdef __cplusplus
}
#endif
#endif
