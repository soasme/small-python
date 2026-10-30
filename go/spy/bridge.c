/* The C side of the callbacks: the engine's callback types, adapted to the
 * functions spy.go exports. Handles travel as uintptr_t in the void * slots. */
#include <stdint.h>
#include "spy.h"
#include "_cgo_export.h"

static SPYValue *call(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *f) {
    return goCall(c, argc, (SPYValue **)argv, keywords, (uintptr_t)f);
}

static void release(void *f) {
    goRelease((uintptr_t)f);
}

static int init_module(SPYContext *c, SPYValue *module) {
    return goInit(c, module);
}

static int write_output(void *rt, const char *text, size_t n) {
    return goWrite((uintptr_t)rt, (char *)text, n);
}

static char *load_module(void *rt, const char *name) {
    return goLoad((uintptr_t)rt, (char *)name);
}

void spy_go_bind(SPYContext *c, uintptr_t rt) {
    spy_set_opaque(c, (void *)rt);
}

uintptr_t spy_go_runtime(SPYContext *c) {
    return (uintptr_t)spy_get_opaque(c);
}

SPYValue *spy_go_native(SPYContext *c, const char *name, uintptr_t f) {
    return spy_native(c, name, call, (void *)f, release);
}

int spy_go_new_module(SPYContext *c, const char *name) {
    return spy_new_module(c, name, init_module);
}

void spy_go_set_output(SPYContext *c, int on) {
    spy_set_output(c, on ? write_output : NULL, spy_get_opaque(c));
}

void spy_go_set_loader(SPYContext *c, int on) {
    spy_set_module_loader(c, on ? load_module : NULL, spy_get_opaque(c));
}
