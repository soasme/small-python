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
    SPY_ITERATOR, SPY_CLASS, SPY_INSTANCE, SPY_METHOD, SPY_SET, SPY_GENERATOR
} SPYType;

/* Arguments are borrowed. Return an owned value, or NULL with an error set. */
typedef SPYValue *(*SPYNative)(SPYContext *, size_t, SPYValue *const *, void *);
typedef int (*SPYWrite)(void *, const char *, size_t);
/* Return malloc-allocated source; the runtime frees it after parsing. */
typedef char *(*SPYModuleLoader)(void *, const char *);

SPYContext *spy_context_new(void);
/* Release all external values before freeing their context. No shared contexts
 * or values across threads; independent contexts have no global mutable state. */
void spy_context_free(SPYContext *);
void spy_set_output(SPYContext *, SPYWrite, void *);
void spy_set_module_loader(SPYContext *, SPYModuleLoader, void *);
/* Zero means unlimited. Budget resets for each top-level evaluation. */
void spy_set_step_limit(SPYContext *, size_t);
size_t spy_collect(SPYContext *);
size_t spy_live_values(const SPYContext *);

/* eval returns the final expression (or None); exec returns 0 or -1.
 * All returned SPYValue pointers are owned; NULL indicates an error.
 * A new evaluation clears the previous error, but preserves globals. */
SPYValue *spy_eval(SPYContext *, const char *source, const char *filename);
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
SPYValue *spy_list(SPYContext *);
int spy_list_append(SPYContext *, SPYValue *, SPYValue *);
int spy_as_int(SPYContext *, SPYValue *, int64_t *);
int spy_as_float(SPYContext *, SPYValue *, double *);
const char *spy_as_string(SPYContext *, SPYValue *, size_t *);
int spy_truth(SPYValue *);
/* String conversion returns an owned SPY_STRING. */
SPYValue *spy_repr(SPYContext *, SPYValue *);

const char *spy_error_type(const SPYContext *);
const char *spy_error_message(const SPYContext *);
const char *spy_error_filename(const SPYContext *);
size_t spy_error_line(const SPYContext *);
void spy_clear_error(SPYContext *);
SPYValue *spy_error(SPYContext *, const char *type, const char *message);

#ifdef __cplusplus
}
#endif
#endif
