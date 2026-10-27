/* Run arbitrary source: lexer, parser, compiler, and runtime together. */
#include "fuzz_common.h"

#include <stdlib.h>

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    SPYContext *c = fuzz_context_new();
    char *source = fuzz_source(data, size);
    if (c && source) spy_exec(c, source, "<fuzz>");
    free(source);
    if (c) fuzz_context_free(c);
    return 0;
}
