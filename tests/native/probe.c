/* A native module for tests/native.py: it counts its inits, calls back into
 * Python, and keeps data that the engine releases with the context. */
#include "spy-module.h"

#include <stdlib.h>

static int inits;

static SPYValue *count(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *data) {
    (void)argc; (void)argv; (void)keywords; (void)data;
    return spy_int(c, inits);
}
/* call(f, *args, **kwargs) returns f(*args, **kwargs); its error propagates. */
static SPYValue *call(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *data) {
    (void)data;
    if (!argc) return spy_error(c, "TypeError", "call() needs a callable");
    return spy_call_keywords(c, argv[0], argc - 1, argv + 1, keywords);
}

static int add(SPYContext *c, SPYValue *module, const char *name, SPYNativeKeywords function, void *data) {
    SPYValue *value = spy_native(c, name, function, data, free);
    int status = value ? spy_set_attr(c, module, name, value) : -1;
    spy_release(value);
    return status;
}

SPY_MODULE int spy_init_probe(SPYContext *c, SPYValue *module) {
    inits++;
    return add(c, module, "count", count, malloc(1)) || add(c, module, "call", call, NULL) ? -1 : 0;
}
