#include "fuzz_common.h"
#include "spy-std.h"

#include <stdlib.h>
#include <string.h>

/* Enough for real programs, small enough that a loop ends within a second. */
#define FUZZ_STEP_LIMIT 100000

static int discard(void *data, const char *s, size_t n) {
    (void)data; (void)s; (void)n;
    return 0;
}

SPYContext *fuzz_context_new(void) {
    SPYContext *c = spy_context_new();
    if (!c) return NULL;
    spy_set_output(c, discard, NULL);
    spy_set_step_limit(c, FUZZ_STEP_LIMIT);
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
