#ifndef SPY_STD_H
#define SPY_STD_H

#include "spy.h"

#ifdef __cplusplus
extern "C" {
#endif

/* The standard layer, like QuickJS's quickjs-libc: the modules sys, gc,
 * weakref, _weakref, types, itertools, collections (with collections.abc),
 * _thread, and _typing, registered with spy_new_module through the public API
 * and built on the engine's _spy primitives. The core (spy.c) provides the
 * language and its builtins; hosts that want these modules link spy-std.c,
 * as the spy command does. Both return 0, or -1 with an error set. */
int spy_std_init_module(SPYContext *, const char *name);
int spy_std_init(SPYContext *);

#ifdef __cplusplus
}
#endif
#endif
