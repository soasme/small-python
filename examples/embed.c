#include "spy.h"
#include <stdio.h>

static SPYValue *square(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)data;
    int64_t n;
    if (argc != 1) return spy_error(c, "TypeError", "square expects one integer");
    if (spy_as_int(c, argv[0], &n)) return NULL;
    if (n < -3037000499LL || n > 3037000499LL)
        return spy_error(c, "OverflowError", "square exceeds signed 64-bit range");
    return spy_int(c, n * n);
}
int main(void) {
    SPYContext *c = spy_context_new();
    if (!c) return 1;
    if (spy_define(c, "square", square, NULL)) { spy_context_free(c); return 1; }
    SPYValue *result = spy_eval(c, "square(12)", "<embed>");
    int64_t n;
    int status = !result || spy_as_int(c, result, &n);
    if (status) fprintf(stderr, "%s: %s\n", spy_error_type(c), spy_error_message(c));
    else printf("%lld\n", (long long)n);
    spy_release(result);
    spy_context_free(c);
    return status;
}
