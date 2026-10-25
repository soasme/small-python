#include "../spy.h"
#include <stdio.h>
#include <time.h>

static int discard(void *data, const char *s, size_t n) {
    (void)data; (void)s; (void)n;
    return 0;
}
int main(void) {
    const size_t iterations = 20000;
    clock_t begin = clock();
    if (begin == (clock_t)-1) return 1;
    for (size_t i = 0; i < iterations; i++) {
        SPYContext *c = spy_context_new();
        if (!c) return 1;
        spy_set_output(c, discard, NULL);
        int status = spy_exec(c, "print('Hello, world!')", "<bench>");
        spy_context_free(c);
        if (status) return 1;
    }
    clock_t end = clock();
    if (end == (clock_t)-1) return 1;
    double us = (double)(end - begin) * 1e6 / CLOCKS_PER_SEC / iterations;
    printf("create + parse + hello (discard output) + destroy: %.2f us CPU time/instance (%zu iterations)\n", us, iterations);
    return 0;
}
