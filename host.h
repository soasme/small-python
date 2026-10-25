#ifndef SLIM_HOST_H
#define SLIM_HOST_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

/* C11 stream reader: also works for pipes, where seeking is unavailable. */
static char *host_read(FILE *file) {
    size_t len = 0, cap = 4096;
    char *source = malloc(cap);
    if (!source) return NULL;
    for (;;) {
        size_t n = fread(source + len, 1, cap - len - 1, file);
        len += n;
        if (ferror(file)) { free(source); return NULL; }
        if (feof(file)) break;
        if (len == cap - 1) {
            if (cap > SIZE_MAX / 2) { free(source); return NULL; }
            cap *= 2;
            char *next = realloc(source, cap);
            if (!next) { free(source); return NULL; }
            source = next;
        }
    }
    source[len] = 0;
    /* Python source may not contain NUL bytes. */
    for (size_t i = 0; i < len; i++) if (!source[i]) { free(source); return NULL; }
    return source;
}

#endif
