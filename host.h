#ifndef SLIM_HOST_H
#define SLIM_HOST_H

#include "spy.h"

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

/* Console callbacks and the process status shared by the spy command and
 * the test drivers. */
static inline int host_output(void *data, const char *s, size_t n) {
    return fwrite(s, 1, n, data) == n ? 0 : -1;
}
static inline int host_flush(void *data) { return fflush(data); }
/* One line of standard input for input(), or NULL at its end. */
static inline char *host_read_line(void *data) {
    size_t len = 0, size = 128;
    char *line = malloc(size);
    int ch;
    while (line && (ch = fgetc(data)) != EOF) {
        if (len + 2 > size) {
            char *next = realloc(line, size *= 2);
            if (!next) { free(line); return NULL; }
            line = next;
        }
        line[len++] = (char)ch;
        if (ch == '\n') break;
    }
    if (line && !len) { free(line); return NULL; }
    if (line) line[len] = 0;
    return line;
}
static inline void host_report(SPYContext *c) {
    fprintf(stderr, "%s:%zu: %s: %s\n", spy_error_filename(c), spy_error_line(c),
            spy_error_type(c), spy_error_display(c));
}
/* The process status for the pending error. SystemExit(code) exits with code
 * like CPython: None is success, an int is the status, anything else is
 * printed and fails. Returns -1 for any other error, after reporting it. */
static inline int host_exit_status(SPYContext *c) {
    if (strcmp(spy_error_type(c), "SystemExit")) { host_report(c); return -1; }
    SPYValue *error = spy_error_value(c), *code = error ? spy_get_attr(c, error, "code") : NULL;
    int64_t status = 1;
    if (!code) host_report(c);
    else if (spy_type(code) == SPY_NONE) status = 0;
    else if (spy_type(code) == SPY_INT && !spy_as_int(c, code, &status)) status &= 0xff;
    else {
        SPYValue *text = spy_str(c, code);
        const char *s = text ? spy_as_string(c, text, NULL) : NULL;
        if (s) fprintf(stderr, "%s\n", s);
        spy_release(text); status = 1;
    }
    spy_release(code); spy_release(error);
    return (int)status;
}

#endif
