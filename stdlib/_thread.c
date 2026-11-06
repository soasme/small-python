/* _thread: virtual threads, all on the host's system thread, switching only
 * where one would block (docs/threads.md). The module is its Python source,
 * stdlib/_thread.py, embedded in _thread-source.h. Built as it is, it is a
 * C module that a host links and registers with spy_new_module(c,
 * "_thread", spy_init__thread); built with -DSPY_SHARED_MODULE -shared, it
 * is the native module _thread.so (spy-module.h). */
#include "spy-module.h"

#include <stdlib.h>
#include <string.h>

#include "_thread-source.h"

SPY_MODULE int spy_init__thread(SPYContext *c, SPYValue *module) {
    size_t len = 0, count = sizeof(source) / sizeof(*source);
    for (size_t i = 0; i < count; i++) len += strlen(source[i]);
    char *text = malloc(len + 1), *at = text;
    if (!text) { spy_error(c, "MemoryError", "allocation failed"); return -1; }
    for (size_t i = 0; i < count; i++) { size_t n = strlen(source[i]); memcpy(at, source[i], n); at += n; }
    *at = 0;
    int status = spy_exec_module(c, module, text, "<frozen _thread>");
    free(text);
    return status;
}
