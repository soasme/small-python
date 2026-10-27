#ifndef SLIM_HOST_H
#define SLIM_HOST_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <ctype.h>
#include <sys/stat.h>

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

/* The core probes package.__init__ before package, then package.__namespace__
 * for a directory without __init__.py (PEP 420). Search policy stays here. */
static inline char *host_load_module(void *data, const char *name) {
    const char *directory = data;
    size_t prefix = strlen(directory), len = strlen(name);
    static const char namespace_suffix[] = ".__namespace__";
    size_t suffix = sizeof(namespace_suffix) - 1;
    int namespace = len > suffix && !strcmp(name + len - suffix, namespace_suffix);
    if (namespace) len -= suffix;
    if (!len || prefix > SIZE_MAX - len - 5) return NULL;
    char *path = malloc(prefix + len + 5);
    if (!path) return NULL;
    memcpy(path, directory, prefix); path[prefix++] = '/';
    for (size_t i = 0; i < len; i++) {
        unsigned char ch = (unsigned char)name[i];
        if (ch == '.' && i && i + 1 < len && name[i - 1] != '.') path[prefix + i] = '/';
        else if (isalnum(ch) || ch == '_' || ch >= 128) path[prefix + i] = (char)ch;
        else { free(path); return NULL; }
    }
    if (namespace) {
        struct stat info;
        path[prefix + len] = 0;
        int found = !stat(path, &info) && S_ISDIR(info.st_mode);
        free(path);
        return found ? calloc(1, 1) : NULL;
    }
    memcpy(path + prefix + len, ".py", 4);
    FILE *file = fopen(path, "rb");
    free(path);
    if (!file) return NULL;
    char *source = host_read(file);
    fclose(file); return source;
}

#endif
