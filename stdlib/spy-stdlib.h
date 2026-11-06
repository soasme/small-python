#ifndef SPY_STDLIB_H
#define SPY_STDLIB_H

#include "spy.h"

#ifdef __cplusplus
extern "C" {
#endif

/* The C modules of the standard library (stdlib/). A host links one from
 * libNAME.a and registers it with spy_new_module(c, "NAME", spy_init_NAME),
 * as the spy command does with each, or loads NAME.so at run time with
 * spy_std_load_native (spy-std.h). */
int spy_init__thread(SPYContext *, SPYValue *); /* Virtual threads (docs/threads.md). */

#ifdef __cplusplus
}
#endif
#endif
