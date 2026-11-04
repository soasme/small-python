/* A native module: a shared library that spy imports from beside the
 * program (manual 3.2).
 *
 *     cc -shared -fPIC -DSPY_SHARED_MODULE -I. examples/fib.c -o examples/fib.so
 *     ./spy examples/test_fib.py
 *
 * On Windows the library is fib.dll. Without SPY_SHARED_MODULE the same file
 * is a C module that a host links and registers with spy_new_module. */
#include "spy-module.h"

static SPYValue *fib(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *data) {
    int64_t n, a = 0, b = 1;
    (void)data;
    if (argc != 1 || keywords) return spy_error(c, "TypeError", "fib() takes exactly one argument");
    if (spy_as_int(c, argv[0], &n)) return NULL;
    if (n < 0 || n > 92) return spy_error(c, "ValueError", "fib() argument must be in 0..92");
    while (n--) {
        int64_t next = a + b;
        a = b;
        b = next;
    }
    return spy_int(c, a);
}

SPY_MODULE int spy_init_fib(SPYContext *c, SPYValue *module) {
    SPYValue *function = spy_native(c, "fib", fib, NULL, NULL);
    int status = function ? spy_set_attr(c, module, "fib", function) : -1;
    spy_release(function);
    return status;
}
