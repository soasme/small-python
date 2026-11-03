#include "fuzz_common.h"
#include "spy-std.h"

#include <stdlib.h>
#include <string.h>

/* Enough for real programs, small enough that a loop ends within a second
 * and memory within -rss_limit_mb under AddressSanitizer. */
#define FUZZ_STEP_LIMIT 100000
#define FUZZ_MEMORY_LIMIT (256 << 20)

static int discard(SPYContext *c, void *data, const char *s, size_t n) {
    (void)c; (void)data; (void)s; (void)n;
    return 0;
}

static int fill(SPYContext *c, SPYValue *module) {
    SPYValue *value = spy_int(c, 1);
    int status = value ? spy_set_attr(c, module, "value", value) : -1;
    spy_release(value);
    return status;
}
/* No module has source; one whose name ends in _c is registered when it is
 * asked for, as a native module's loader does. */
static SPYValue *load(SPYContext *c, void *data, const char *name) {
    size_t len = strlen(name);
    (void)data;
    if (len > 2 && !strcmp(name + len - 2, "_c")) spy_new_module(c, name, fill);
    return NULL;
}

SPYContext *fuzz_context_new(void) {
    SPYContext *c = spy_context_new();
    if (!c) return NULL;
    spy_set_output(c, discard, NULL, NULL);
    spy_set_module_loader(c, load, NULL);
    spy_set_step_limit(c, FUZZ_STEP_LIMIT);
    spy_set_memory_limit(c, FUZZ_MEMORY_LIMIT);
    if (spy_std_init(c)) { spy_context_free(c); return NULL; }
    return c;
}

void fuzz_context_free(SPYContext *c) {
    spy_clear_error(c);
    spy_collect(c);
    spy_context_free(c);
}

char *fuzz_source(const uint8_t *data, size_t size) {
    char *source = malloc(size + 1);
    if (!source) return NULL;
    memcpy(source, data, size);
    source[size] = 0;
    return source;
}
