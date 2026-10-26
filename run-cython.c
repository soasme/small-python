/* Persistent, length-framed evaluation driver for the upstream doctest adapter.
 * Only the adapter uses JSON; the engine itself has no JSON dependency. */
#include "spy.h"
#include "spy-std.h"
#include "host.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { char *text; size_t len; } Output;
typedef struct { int argc; char **argv; } ModulePaths;
static char *load_module(void *data, const char *name) {
    ModulePaths *paths = data;
    size_t len = strlen(name);
    char *module = NULL;
    if (len > 9 && !strcmp(name + len - 9, ".__init__")) {
        module = malloc(len - 8);
        if (!module) return NULL;
        memcpy(module, name, len - 9); module[len - 9] = 0;
    }
    for (int i = 1; i < paths->argc; i += 2) {
        char *source = host_load_module(paths->argv[i + 1], name);
        if (source) { free(module); return source; }
        /* An earlier plain module shadows a later package. The core probes
         * package.__init__ first, then retries the plain module name. */
        if (module) {
            source = host_load_module(paths->argv[i + 1], module);
            if (source) { free(source); break; }
        }
    }
    free(module);
    return NULL;
}
static int capture(void *data, const char *s, size_t n) {
    Output *out = data;
    if (n > SIZE_MAX - out->len - 1) return -1;
    char *next = realloc(out->text, out->len + n + 1);
    if (!next) return -1;
    out->text = next;
    memcpy(out->text + out->len, s, n); out->len += n; out->text[out->len] = 0;
    return 0;
}
static void json_string(const char *s, size_t n) {
    putchar('"');
    for (size_t i = 0; i < n; i++) {
        unsigned char ch = (unsigned char)s[i];
        if (ch == '"' || ch == '\\') { putchar('\\'); putchar(ch); }
        else if (ch < 32) printf("\\u%04x", ch);
        else putchar(ch);
    }
    putchar('"');
}
int main(int argc, char **argv) {
    if (!(argc % 2)) return 2;
    for (int i = 1; i < argc; i += 2) if (strcmp(argv[i], "--module-path")) return 2;
    SPYContext *c = spy_context_new();
    if (!c || spy_std_init(c)) return 1;
    ModulePaths paths = {argc, argv};
    if (argc > 1) spy_set_module_loader(c, load_module, &paths);
    Output out = {0};
    spy_set_output(c, capture, &out);
    spy_set_step_limit(c, 1000000);
    char header[80];
    int status = 0;
    while (fgets(header, sizeof(header), stdin)) {
        size_t n;
        char mode, extra;
        if (sscanf(header, "%c %zu %c", &mode, &n, &extra) != 2 ||
            (mode != 'E' && mode != 'I' && mode != 'M') || n > 16 * 1024 * 1024) { status = 2; break; }
        char *source = malloc(n + 1);
        if (!source) { status = 1; break; }
        if (fread(source, 1, n, stdin) != n) { free(source); status = 2; break; }
        source[n] = 0;
        out.len = 0;
        SPYValue *value;
        if (memchr(source, 0, n)) {
            spy_clear_error(c);
            value = spy_error(c, "SyntaxError", "source code cannot contain null bytes");
        } else value = mode == 'I' ? spy_eval_interactive(c, source, "<upstream>") : spy_eval(c, source, "<upstream>");
        free(source);
        int ok = value && !*spy_error_type(c);
        printf("{\"ok\":%s,\"output\":", ok ? "true" : "false");
        json_string(out.text, out.len);
        fputs(",\"type\":", stdout); json_string(spy_error_type(c), strlen(spy_error_type(c)));
        const char *display = spy_error_display(c);
        fputs(",\"message\":", stdout); json_string(display, strlen(display));
        fputs(",\"filename\":", stdout); json_string(spy_error_filename(c), strlen(spy_error_filename(c)));
        printf(",\"line\":%zu}\n", spy_error_line(c)); fflush(stdout);
        spy_release(value); spy_collect(c);
        /* A failed module setup blocks the group. Do not execute its examples
         * in a namespace that was never initialized. Keep the failure reply. */
        if (mode == 'M' && !ok) break;
    }
    free(out.text); spy_context_free(c);
    return status;
}
