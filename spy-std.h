#ifndef SPY_STD_H
#define SPY_STD_H

#include "spy.h"

#ifdef __cplusplus
extern "C" {
#endif

/* The standard layer: the host modules sys and gc, registered with
 * spy_new_module through the public API and written on the engine
 * primitives, which they register as _spy. The
 * core (spy.c) provides the language and its builtins; hosts that want these
 * modules link spy-std.c, as the spy command does, and register each one or
 * all of them. Both return 0, or -1 with an error set. */
int spy_std_init_module(SPYContext *, const char *name);
int spy_std_init(SPYContext *);
/* Report the pending exception through sys.excepthook, which writes its
 * traceback display to sys.stderr; returns 0 and clears the error, or -1
 * with the error kept when there is no hook to call or the hook fails. */
int spy_std_report(SPYContext *);
/* Load the shared library at path as the native module name (spy-module.h)
 * and register it with spy_new_module, so that importing name, from a loader
 * or later, runs its init. The policy is asked first, with "dlopen" (name,
 * path). Returns 0, or -1 with an error set: PermissionError (or the policy's
 * own error), or ImportError for a library that does not open, is not a
 * native module, or was built for an incompatible engine. A library that
 * failed is closed; one that loaded is never closed, as its code may run as
 * long as the process does. */
int spy_std_load_native(SPYContext *, const char *name, const char *path);

#ifdef __cplusplus
}
#endif
#endif
