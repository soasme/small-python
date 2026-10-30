#include "spy.h"
#include "spy-std.h"
#include "host.h"

#include <string.h>

/* The process status for the pending error, whose traceback, unless it is
 * a SystemExit, sys.excepthook displays as python's would. */
static int exit_status(SPYContext *c) {
    if (strcmp(spy_error_type(c), "SystemExit") && !spy_std_report(c)) return -1;
    return host_exit_status(c);
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
    fputs("usage: spy [--mount dir]... [-O | -OO] [-c source | -i | --version | file.py | -]\n", stderr);
    return 2;
}
int main(int argc, char **argv) {
    /* open() reaches only mounted directories: the current one at its own
     * path unless --mount names others, each mounted at its own path.
     * -O and -OO set the optimization level, as python's do. */
    const char *mounts[64];
    int mount_count = 0, at = 1, optimize = 0;
    for (;;) {
        if (at < argc && !strcmp(argv[at], "--mount")) {
            if (at + 1 >= argc || mount_count == 64) return usage();
            mounts[mount_count++] = argv[at + 1];
            at += 2;
        } else if (at < argc && (!strcmp(argv[at], "-O") || !strcmp(argv[at], "-OO"))) {
            optimize = (int)strlen(argv[at++]) - 1;
        } else break;
    }
    argv[at - 1] = argv[0]; argv += at - 1; argc -= at - 1;
    if (argc == 2 && !strcmp(argv[1], "--version")) { puts("spy " SPY_VERSION); return 0; }
    if (argc > 3 || (argc == 3 && strcmp(argv[1], "-c"))) return usage();
    if (argc == 2 && !strcmp(argv[1], "-c")) return usage();
    SPYContext *c = spy_context_new();
    if (!c) { fputs("cannot create runtime\n", stderr); return 1; }
    spy_set_output(c, host_output, stdout);
    spy_set_flush(c, host_flush);
    spy_set_error_output(c, host_output, stderr);
    spy_set_input(c, host_read_line, stdin);
    spy_set_optimize(c, optimize);
    if (spy_std_init(c)) { host_report(c); spy_context_free(c); return 1; }
    if (!mount_count) mounts[mount_count++] = ".";
    for (int i = 0; i < mount_count; i++)
        if (spy_mount(c, mounts[i], NULL, 0)) {
            fprintf(stderr, "spy: %s\n", spy_error_message(c));
            spy_context_free(c); return 1;
        }
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
                /* The main module records the file it runs, as CPython's does. */
                SPYValue *file_name = from_stdin ? NULL : spy_string(c, filename, strlen(filename));
                if (file_name) spy_set_global(c, "__file__", file_name);
                spy_release(file_name);
                status = spy_exec(c, source, from_stdin ? "<stdin>" : filename) ? exit_status(c) : 0;
                if (status < 0) status = 1;
                free(source);
            }
        }
    }
    free(directory); spy_context_free(c);
    return status;
}
