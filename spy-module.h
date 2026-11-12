/* Generated from spy.h by tools/api.py; run make api-reference after editing
 * spy.h. */
#ifndef SPY_MODULE_H
#define SPY_MODULE_H

#include "spy.h"

#ifdef __cplusplus
extern "C" {
#endif

/* == Native modules ==
 * A native module is a shared library defining one module, which a host
 * loads with spy_std_load_native (spy-std.h), as the spy command loads
 * NAME.so (NAME.dll on Windows) found beside its sources. Its source includes
 * this header and marks the module's init, a SPYModuleInit named spy_init_
 * and the module's last name, with SPY_MODULE:
 *
 *     SPY_MODULE int spy_init_fib(SPYContext *c, SPYValue *module) { ... }
 *
 * Compiled with SPY_SHARED_MODULE defined, the library calls spy.h through
 * the table its host sets in spy_module, so it needs no symbol from the
 * engine and loads into statically linked hosts too. Without it, the same
 * source is a C module that a host links and registers with spy_new_module. */

/* Every spy.h function. Entries are only appended, so a module runs on any
 * compatible engine (manual 3.4.8) as new as its header or newer. */
typedef struct SPYModuleAPI {
    const char *(*spy_version)(void);
    SPYContext *(*spy_context_new)(void);
    void (*spy_context_free)(SPYContext *);
    void (*spy_set_opaque)(SPYContext *, void *);
    void *(*spy_get_opaque)(const SPYContext *);
    SPYValue *(*spy_eval)(SPYContext *, const char *source, const char *filename);
    int (*spy_exec)(SPYContext *, const char *source, const char *filename);
    SPYValue *(*spy_eval_interactive)(SPYContext *, const char *source, const char *filename);
    void (*spy_set_optimize)(SPYContext *, int level);
    SPYValue *(*spy_get_global)(SPYContext *, const char *);
    int (*spy_set_global)(SPYContext *, const char *, SPYValue *);
    int (*spy_define)(SPYContext *, const char *, SPYNative, void *);
    SPYValue *(*spy_native)(SPYContext *, const char *, SPYNativeKeywords, void *, void (*release)(void *));
    SPYValue *(*spy_call)(SPYContext *, SPYValue *, size_t, SPYValue *const *);
    SPYValue *(*spy_call_keywords)(SPYContext *, SPYValue *, size_t, SPYValue *const *, SPYValue *);
    SPYValue *(*spy_retain)(SPYValue *);
    void (*spy_release)(SPYValue *);
    SPYType (*spy_type)(const SPYValue *);
    SPYValue *(*spy_none)(SPYContext *);
    SPYValue *(*spy_bool)(SPYContext *, int);
    SPYValue *(*spy_int)(SPYContext *, int64_t);
    SPYValue *(*spy_float)(SPYContext *, double);
    SPYValue *(*spy_string)(SPYContext *, const char *, size_t);
    SPYValue *(*spy_bytes)(SPYContext *, const void *, size_t);
    SPYValue *(*spy_list)(SPYContext *);
    SPYValue *(*spy_tuple)(SPYContext *, size_t, SPYValue *const *);
    SPYValue *(*spy_dict)(SPYContext *);
    int (*spy_list_append)(SPYContext *, SPYValue *, SPYValue *);
    SPYValue *(*spy_get_item)(SPYContext *, SPYValue *, SPYValue *);
    int (*spy_set_item)(SPYContext *, SPYValue *, SPYValue *, SPYValue *);
    SPYValue *(*spy_get_attr)(SPYContext *, SPYValue *, const char *);
    int (*spy_set_attr)(SPYContext *, SPYValue *, const char *, SPYValue *);
    SPYValue *(*spy_iter)(SPYContext *, SPYValue *);
    SPYValue *(*spy_next)(SPYContext *, SPYValue *);
    int (*spy_as_int)(SPYContext *, SPYValue *, int64_t *);
    int (*spy_as_float)(SPYContext *, SPYValue *, double *);
    const char *(*spy_as_string)(SPYContext *, SPYValue *, size_t *);
    const unsigned char *(*spy_as_bytes)(SPYContext *, SPYValue *, size_t *);
    int (*spy_truth)(SPYContext *, SPYValue *);
    SPYValue *(*spy_repr)(SPYContext *, SPYValue *);
    SPYValue *(*spy_str)(SPYContext *, SPYValue *);
    const char *(*spy_error_type)(const SPYContext *);
    const char *(*spy_error_message)(const SPYContext *);
    const char *(*spy_error_filename)(const SPYContext *);
    size_t (*spy_error_line)(const SPYContext *);
    const char *(*spy_error_display)(SPYContext *);
    void (*spy_clear_error)(SPYContext *);
    SPYValue *(*spy_error)(SPYContext *, const char *type, const char *message);
    SPYValue *(*spy_raise)(SPYContext *, SPYValue *);
    SPYValue *(*spy_error_value)(SPYContext *);
    void (*spy_set_module_loader)(SPYContext *, SPYModuleLoader, void *);
    int (*spy_new_module)(SPYContext *, const char *, SPYModuleInit);
    int (*spy_init_primitives)(SPYContext *, SPYValue *);
    int (*spy_exec_module)(SPYContext *, SPYValue *, const char *source, const char *filename);
    void (*spy_set_output)(SPYContext *, SPYWrite, SPYFlush, void *);
    void (*spy_set_error_output)(SPYContext *, SPYWrite, SPYFlush, void *);
    void (*spy_set_input)(SPYContext *, SPYReadLine, void *);
    int (*spy_mount)(SPYContext *, const char *directory, const char *path, int flags);
    void (*spy_set_policy)(SPYContext *, SPYPolicy, void *);
    int (*spy_policy_check)(SPYContext *, const char *event, SPYValue *args);
    size_t (*spy_memory_used)(const SPYContext *);
    void (*spy_set_interrupt)(SPYContext *, SPYInterrupt, void *);
    int (*spy_set_limit)(SPYContext *, int limit, size_t value);
    size_t (*spy_get_limit)(const SPYContext *, int limit);
    int (*spy_stopped)(const SPYContext *);
    size_t (*spy_steps_used)(const SPYContext *);
    size_t (*spy_collect)(SPYContext *);
    size_t (*spy_live_values)(const SPYContext *);
    int (*spy_set_argv)(SPYContext *, size_t argc, const char *const *argv, size_t orig_argc, const char *const *orig_argv);
    int (*spy_paused)(const SPYContext *);
    SPYValue *(*spy_resume)(SPYContext *);
    SPYValue *(*spy_callk)(SPYContext *, SPYValue *callee, size_t argc, SPYValue *const *argv, SPYContinuation k, SPYValue *state);
} SPYModuleAPI;
/* The table's functions in its order, for the host that fills it. */
#define SPY_MODULE_FUNCTIONS(X) \
    X(spy_version) \
    X(spy_context_new) \
    X(spy_context_free) \
    X(spy_set_opaque) \
    X(spy_get_opaque) \
    X(spy_eval) \
    X(spy_exec) \
    X(spy_eval_interactive) \
    X(spy_set_optimize) \
    X(spy_get_global) \
    X(spy_set_global) \
    X(spy_define) \
    X(spy_native) \
    X(spy_call) \
    X(spy_call_keywords) \
    X(spy_retain) \
    X(spy_release) \
    X(spy_type) \
    X(spy_none) \
    X(spy_bool) \
    X(spy_int) \
    X(spy_float) \
    X(spy_string) \
    X(spy_bytes) \
    X(spy_list) \
    X(spy_tuple) \
    X(spy_dict) \
    X(spy_list_append) \
    X(spy_get_item) \
    X(spy_set_item) \
    X(spy_get_attr) \
    X(spy_set_attr) \
    X(spy_iter) \
    X(spy_next) \
    X(spy_as_int) \
    X(spy_as_float) \
    X(spy_as_string) \
    X(spy_as_bytes) \
    X(spy_truth) \
    X(spy_repr) \
    X(spy_str) \
    X(spy_error_type) \
    X(spy_error_message) \
    X(spy_error_filename) \
    X(spy_error_line) \
    X(spy_error_display) \
    X(spy_clear_error) \
    X(spy_error) \
    X(spy_raise) \
    X(spy_error_value) \
    X(spy_set_module_loader) \
    X(spy_new_module) \
    X(spy_init_primitives) \
    X(spy_exec_module) \
    X(spy_set_output) \
    X(spy_set_error_output) \
    X(spy_set_input) \
    X(spy_mount) \
    X(spy_set_policy) \
    X(spy_policy_check) \
    X(spy_memory_used) \
    X(spy_set_interrupt) \
    X(spy_set_limit) \
    X(spy_get_limit) \
    X(spy_stopped) \
    X(spy_steps_used) \
    X(spy_collect) \
    X(spy_live_values) \
    X(spy_set_argv) \
    X(spy_paused) \
    X(spy_resume) \
    X(spy_callk)

/* What a shared module exports beside its init: the version of the header it
 * was built with, and the table its host sets before calling the init. */
typedef struct SPYModuleLink { const char *version; const SPYModuleAPI *api; } SPYModuleLink;

#ifdef SPY_SHARED_MODULE
#if defined(_WIN32)
#define SPY_EXPORT __declspec(dllexport)
#elif defined(__GNUC__)
#define SPY_EXPORT __attribute__((visibility("default")))
#else
#define SPY_EXPORT
#endif
extern SPY_EXPORT SPYModuleLink spy_module;
#define SPY_MODULE SPY_EXPORT SPYModuleLink spy_module = {SPY_VERSION, NULL}; SPY_EXPORT
#define spy_version (spy_module.api->spy_version)
#define spy_context_new (spy_module.api->spy_context_new)
#define spy_context_free (spy_module.api->spy_context_free)
#define spy_set_opaque (spy_module.api->spy_set_opaque)
#define spy_get_opaque (spy_module.api->spy_get_opaque)
#define spy_eval (spy_module.api->spy_eval)
#define spy_exec (spy_module.api->spy_exec)
#define spy_eval_interactive (spy_module.api->spy_eval_interactive)
#define spy_set_optimize (spy_module.api->spy_set_optimize)
#define spy_get_global (spy_module.api->spy_get_global)
#define spy_set_global (spy_module.api->spy_set_global)
#define spy_define (spy_module.api->spy_define)
#define spy_native (spy_module.api->spy_native)
#define spy_call (spy_module.api->spy_call)
#define spy_call_keywords (spy_module.api->spy_call_keywords)
#define spy_retain (spy_module.api->spy_retain)
#define spy_release (spy_module.api->spy_release)
#define spy_type (spy_module.api->spy_type)
#define spy_none (spy_module.api->spy_none)
#define spy_bool (spy_module.api->spy_bool)
#define spy_int (spy_module.api->spy_int)
#define spy_float (spy_module.api->spy_float)
#define spy_string (spy_module.api->spy_string)
#define spy_bytes (spy_module.api->spy_bytes)
#define spy_list (spy_module.api->spy_list)
#define spy_tuple (spy_module.api->spy_tuple)
#define spy_dict (spy_module.api->spy_dict)
#define spy_list_append (spy_module.api->spy_list_append)
#define spy_get_item (spy_module.api->spy_get_item)
#define spy_set_item (spy_module.api->spy_set_item)
#define spy_get_attr (spy_module.api->spy_get_attr)
#define spy_set_attr (spy_module.api->spy_set_attr)
#define spy_iter (spy_module.api->spy_iter)
#define spy_next (spy_module.api->spy_next)
#define spy_as_int (spy_module.api->spy_as_int)
#define spy_as_float (spy_module.api->spy_as_float)
#define spy_as_string (spy_module.api->spy_as_string)
#define spy_as_bytes (spy_module.api->spy_as_bytes)
#define spy_truth (spy_module.api->spy_truth)
#define spy_repr (spy_module.api->spy_repr)
#define spy_str (spy_module.api->spy_str)
#define spy_error_type (spy_module.api->spy_error_type)
#define spy_error_message (spy_module.api->spy_error_message)
#define spy_error_filename (spy_module.api->spy_error_filename)
#define spy_error_line (spy_module.api->spy_error_line)
#define spy_error_display (spy_module.api->spy_error_display)
#define spy_clear_error (spy_module.api->spy_clear_error)
#define spy_error (spy_module.api->spy_error)
#define spy_raise (spy_module.api->spy_raise)
#define spy_error_value (spy_module.api->spy_error_value)
#define spy_set_module_loader (spy_module.api->spy_set_module_loader)
#define spy_new_module (spy_module.api->spy_new_module)
#define spy_init_primitives (spy_module.api->spy_init_primitives)
#define spy_exec_module (spy_module.api->spy_exec_module)
#define spy_set_output (spy_module.api->spy_set_output)
#define spy_set_error_output (spy_module.api->spy_set_error_output)
#define spy_set_input (spy_module.api->spy_set_input)
#define spy_mount (spy_module.api->spy_mount)
#define spy_set_policy (spy_module.api->spy_set_policy)
#define spy_policy_check (spy_module.api->spy_policy_check)
#define spy_memory_used (spy_module.api->spy_memory_used)
#define spy_set_interrupt (spy_module.api->spy_set_interrupt)
#define spy_set_limit (spy_module.api->spy_set_limit)
#define spy_get_limit (spy_module.api->spy_get_limit)
#define spy_stopped (spy_module.api->spy_stopped)
#define spy_steps_used (spy_module.api->spy_steps_used)
#define spy_collect (spy_module.api->spy_collect)
#define spy_live_values (spy_module.api->spy_live_values)
#define spy_set_argv (spy_module.api->spy_set_argv)
#define spy_paused (spy_module.api->spy_paused)
#define spy_resume (spy_module.api->spy_resume)
#define spy_callk (spy_module.api->spy_callk)
#else
#define SPY_MODULE
#endif

#ifdef __cplusplus
}
#endif
#endif
