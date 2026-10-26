#ifndef SPY_H
#define SPY_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SPY_VERSION "0.1.0"

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
    SPY_FRAME, SPY_FRAME_LOCALS
} SPYType;

/* Arguments are borrowed. Return an owned value, or NULL with an error set. */
typedef SPYValue *(*SPYNative)(SPYContext *, size_t, SPYValue *const *, void *);
typedef int (*SPYWrite)(void *, const char *, size_t);
typedef int (*SPYFlush)(void *);
/* Return malloc-allocated, NUL-terminated source bytes, or NULL if absent.
 * The runtime decodes encoding declarations and frees source.
 * For a module "pkg.mod", it probes "pkg.mod.__init__" (package) first,
 * then "pkg.mod". The host controls search paths and source storage. */
typedef char *(*SPYModuleLoader)(void *, const char *);

SPYContext *spy_context_new(void);
/* Release all external values before freeing their context. No shared contexts
 * or values across threads; independent contexts have no global mutable state. */
void spy_context_free(SPYContext *);
void spy_set_output(SPYContext *, SPYWrite, void *);
/* Optional flush for the current output callback; shares its data pointer.
 * Without it the output callback is treated as unbuffered. */
void spy_set_flush(SPYContext *, SPYFlush);
void spy_set_module_loader(SPYContext *, SPYModuleLoader, void *);
/* Zero means unlimited. Budget resets for each top-level evaluation. */
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
/* Large Python integers raise OverflowError rather than narrowing silently. */
int spy_as_int(SPYContext *, SPYValue *, int64_t *);
int spy_as_float(SPYContext *, SPYValue *, double *);
const char *spy_as_string(SPYContext *, SPYValue *, size_t *);
const unsigned char *spy_as_bytes(SPYContext *, SPYValue *, size_t *);
int spy_truth(SPYValue *);
/* String conversion returns an owned SPY_STRING. */
SPYValue *spy_repr(SPYContext *, SPYValue *);

const char *spy_error_type(const SPYContext *);
const char *spy_error_message(const SPYContext *);
/* The error message as CPython's traceback module would display it, with its
 * keyword-typo suggestion for a generic SyntaxError. Valid until the next call. */
const char *spy_error_display(SPYContext *);
const char *spy_error_filename(const SPYContext *);
size_t spy_error_line(const SPYContext *);
void spy_clear_error(SPYContext *);
SPYValue *spy_error(SPYContext *, const char *type, const char *message);

#ifdef __cplusplus
}
#endif
#endif
