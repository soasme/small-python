#include "spy.h"
#include "spy-std.h"
#include "host.h"

#include <string.h>

static int output(void *data, const char *s, size_t n) {
    return fwrite(s, 1, n, data) == n ? 0 : -1;
}
static int flush_output(void *data) { return fflush(data); }
static void report(SPYContext *c) {
    fprintf(stderr, "%s:%zu: %s: %s\n", spy_error_filename(c), spy_error_line(c),
            spy_error_type(c), spy_error_display(c));
}
/* The process status for the pending error. SystemExit(code) exits with code
 * like CPython: None is success, an int is the status, anything else is
 * printed and fails. Returns -1 for any other error, after reporting it. */
static int exit_status(SPYContext *c) {
    if (strcmp(spy_error_type(c), "SystemExit")) { report(c); return -1; }
    SPYValue *error = spy_error_value(c), *code = error ? spy_get_attr(c, error, "code") : NULL;
    int64_t status = 1;
    if (!code) report(c);
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
static int repl(SPYContext *c) {
    char line[4096];
    char *source = NULL;
    size_t len = 0;
    int compound = 0;
    puts("spy " SPY_VERSION " (experimental Python subset; blank line ends a block)");
    for (;;) {
        fputs(len ? "... " : ">>> ", stdout); fflush(stdout);
        if (!fgets(line, sizeof(line), stdin)) break;
        size_t n = strlen(line);
        char *next = realloc(source, len + n + 1);
        if (!next) { free(source); return 1; }
        source = next; memcpy(source + len, line, n + 1); len += n;
        size_t end = n;
        while (end && (line[end - 1] == '\n' || line[end - 1] == '\r' || line[end - 1] == ' ')) end--;
        if (end && line[end - 1] == ':') compound = 1;
        if (compound && end) continue;
        SPYValue *v = spy_eval_interactive(c, source, "<stdin>");
        int status = v ? -1 : exit_status(c);
        spy_release(v); spy_collect(c);
        if (status >= 0) { free(source); return status; }
        len = 0; compound = 0;
    }
    free(source);
    return 0;
}
static int usage(void) {
    fputs("usage: spy [-c source | -i | --version | file.py | -]\n", stderr);
    return 2;
}
int main(int argc, char **argv) {
    if (argc == 2 && !strcmp(argv[1], "--version")) { puts("spy " SPY_VERSION); return 0; }
    if (argc > 3 || (argc == 3 && strcmp(argv[1], "-c"))) return usage();
    if (argc == 2 && !strcmp(argv[1], "-c")) return usage();
    SPYContext *c = spy_context_new();
    if (!c) { fputs("cannot create runtime\n", stderr); return 1; }
    spy_set_output(c, output, stdout);
    spy_set_flush(c, flush_output);
    if (spy_std_init(c)) { report(c); spy_context_free(c); return 1; }
    char *directory = NULL;
    const char *filename = argc == 2 ? argv[1] : "<string>";
    if (argc == 2 && argv[1][0] != '-') {
        const char *slash = strrchr(filename, '/');
        if (slash) {
            size_t n = (size_t)(slash - filename);
            directory = malloc(n + 1);
            if (!directory) { spy_context_free(c); return 1; }
            memcpy(directory, filename, n); directory[n] = 0;
        }
    }
    spy_set_module_loader(c, host_load_module, directory ? (*directory ? directory : "/") : ".");
    int status;
    if (argc == 2 && !strcmp(argv[1], "-i")) status = repl(c);
    else if (argc == 3) {
        status = spy_exec(c, argv[2], "<string>") ? exit_status(c) : 0;
        if (status < 0) status = 1;
    } else if (argc == 2 && argv[1][0] == '-' && strcmp(argv[1], "-")) status = usage();
    else {
        int from_stdin = argc == 1 || !strcmp(argv[1], "-");
        FILE *file = from_stdin ? stdin : fopen(filename, "rb");
        if (!file) { perror(filename); status = 1; }
        else {
            char *source = host_read(file);
            if (!from_stdin) fclose(file);
            if (!source) { fputs("cannot read source (I/O error, NUL byte, or out of memory)\n", stderr); status = 1; }
            else {
                status = spy_exec(c, source, from_stdin ? "<stdin>" : filename) ? exit_status(c) : 0;
                if (status < 0) status = 1;
                free(source);
            }
        }
    }
    free(directory); spy_context_free(c);
    return status;
}
