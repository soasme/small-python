#ifndef SPY_STD_H
#define SPY_STD_H

#include "spy.h"

#ifdef __cplusplus
extern "C" {
#endif

/* The standard layer, like QuickJS's quickjs-libc: the host modules sys, gc,
 * weakref, and _weakref, registered with spy_new_module through the public
 * API and written on the engine primitives, which they register as _spy. The
 * core (spy.c) provides the language and its builtins; hosts that want these
 * modules link spy-std.c, as the spy command does, and register each one or
 * all of them. Both return 0, or -1 with an error set. */
int spy_std_init_module(SPYContext *, const char *name);
int spy_std_init(SPYContext *);

#ifdef __cplusplus
}
#endif
#endif
