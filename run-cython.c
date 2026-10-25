/* Persistent, length-framed evaluation driver for the upstream doctest adapter.
 * Only the adapter uses JSON; the engine itself has no JSON dependency. */
#include "spy.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { char *text; size_t len; } Output;
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
int main(void) {
    SPYContext *c = spy_context_new();
    if (!c) return 1;
    Output out = {0};
    spy_set_output(c, capture, &out);
    spy_set_step_limit(c, 100000);
    char header[80];
    int status = 0;
    while (fgets(header, sizeof(header), stdin)) {
        size_t n;
        char mode, extra;
        if (sscanf(header, "%c %zu %c", &mode, &n, &extra) != 2 ||
            (mode != 'E' && mode != 'I') || n > 16 * 1024 * 1024) { status = 2; break; }
        char *source = malloc(n + 1);
        if (!source) { status = 1; break; }
        if (fread(source, 1, n, stdin) != n) { free(source); status = 2; break; }
        source[n] = 0;
        out.len = 0;
        SPYValue *value;
        if (memchr(source, 0, n)) {
            spy_clear_error(c);
            value = spy_error(c, "SyntaxError", "source code cannot contain null bytes");
        } else value = spy_eval(c, source, "<upstream>");
        free(source);
        if (value && mode == 'I' && spy_type(value) != SPY_NONE) {
            SPYValue *repr = spy_repr(c, value);
            if (repr) {
                size_t len;
                const char *s = spy_as_string(c, repr, &len);
                if (capture(&out, s, len) || capture(&out, "\n", 1)) spy_error(c, "MemoryError", "capturing output");
                spy_release(repr);
            }
        }
        printf("{\"ok\":%s,\"output\":", value && !*spy_error_type(c) ? "true" : "false");
        json_string(out.text, out.len);
        fputs(",\"type\":", stdout); json_string(spy_error_type(c), strlen(spy_error_type(c)));
        fputs(",\"message\":", stdout); json_string(spy_error_message(c), strlen(spy_error_message(c)));
        puts("}"); fflush(stdout);
        spy_release(value); spy_collect(c);
    }
    free(out.text); spy_context_free(c);
    return status;
}
