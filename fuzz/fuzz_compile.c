/* Compile arbitrary bytes with compile() without running them: the source
 * decoder, lexer, parser, and compiler. The first byte picks the mode. */
#include "fuzz_common.h"

#include <string.h>

static const char *const modes[] = {"exec", "eval", "single"};

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (!size) return 0;
    SPYContext *c = fuzz_context_new();
    if (!c) return 0;
    SPYValue *compile = spy_eval(c, "compile", "<fuzz>");
    SPYValue *args[3] = {
        spy_bytes(c, data + 1, size - 1),
        spy_string(c, "<fuzz>", 6),
        spy_string(c, modes[data[0] % 3], strlen(modes[data[0] % 3])),
    };
    if (compile && args[0] && args[1] && args[2]) spy_release(spy_call(c, compile, 3, args));
    for (int i = 0; i < 3; i++) spy_release(args[i]);
    spy_release(compile);
    fuzz_context_free(c);
    return 0;
}
