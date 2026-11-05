#include "spy.h"
#include "spy-std.h"
#include "host.h"

#include <string.h>

#ifdef _WIN32
#define NATIVE_SUFFIX ".dll"
#else
#define NATIVE_SUFFIX ".so"
#endif

/* A shared library NAME.so (NAME.dll on Windows) is a native module,
 * found before NAME.py as CPython finds extension modules before sources.
 * Packages, and the __init__ of each, are sources. */
static SPYValue *load_module(SPYContext *c, void *data, const char *name) {
    size_t len = strlen(name);
    int probe = host_ends_with(name, len, ".__init__") || host_ends_with(name, len, ".__namespace__");
    char *path = probe ? NULL : host_module_path(data, name, len, NATIVE_SUFFIX);
    struct stat info;
    int native = path && !stat(path, &info) && S_ISREG(info.st_mode);
    if (native) spy_std_load_native(c, name, path);
    free(path);
    return native ? NULL : host_load_module(c, data, name);
}

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
    fputs("usage: spy [--mount dir]... [-O | -OO] [-c source | file.py | -] [arg]...\n       spy [--mount dir]... [-O | -OO] (-i | --version)\n", stderr);
    return 2;
}
int main(int argc, char **argv) {
    /* sys.orig_argv: the command line as given, before argv is adjusted. */
    const char *const *orig_argv = (const char *const *)argv;
    size_t orig_argc = (size_t)argc;
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
    argv += at - 1; argc -= at - 1;
    if (argc == 2 && !strcmp(argv[1], "--version")) { puts("spy " SPY_VERSION); return 0; }
    /* The arguments after the program are its own. sys.argv starts with the
     * file, "-c" or "-", or is [""] for stdin and the shell, as python's. */
    const char *mode = argc > 1 ? argv[1] : "-";
    int code = !strcmp(mode, "-c"), shell = !strcmp(mode, "-i"), from_stdin = !strcmp(mode, "-");
    if (code ? argc < 3 : shell ? argc > 2 : mode[0] == '-' && !from_stdin) return usage();
    const char *source_text = code ? argv[2] : NULL;
    /* sys.argv: [""] for the shell, the arguments from the program on, and
     * for -c, "-c" then the arguments after the source. */
    size_t script_argc = argc > 1 && !shell ? (size_t)argc - 1 - (size_t)code : 1;
    const char **script_argv = malloc(script_argc * sizeof(*script_argv));
    if (!script_argv) { fputs("cannot create runtime\n", stderr); return 1; }
    script_argv[0] = argc > 1 && !shell ? mode : "";
    for (size_t i = 1; i < script_argc; i++) script_argv[i] = argv[i + 1 + (size_t)code];
    SPYContext *c = spy_context_new();
    if (!c) { free(script_argv); fputs("cannot create runtime\n", stderr); return 1; }
    spy_set_output(c, host_output, host_flush, stdout);
    spy_set_error_output(c, host_output, host_flush, stderr);
    spy_set_input(c, host_read_line, stdin);
    spy_set_optimize(c, optimize);
    int failed = spy_set_argv(c, script_argc, script_argv, orig_argc, orig_argv) || spy_std_init(c);
    free(script_argv);
    if (failed) { host_report(c); spy_context_free(c); return 1; }
    /* The default mount of the working directory is best-effort: a build
     * without file support, or a deleted working directory, runs with
     * nothing mounted, so open raises OSError. */
    int implicit = !mount_count;
    if (implicit) mounts[mount_count++] = ".";
    for (int i = 0; i < mount_count; i++)
        if (spy_mount(c, mounts[i], NULL, 0)) {
            if (implicit) { spy_clear_error(c); break; }
            fprintf(stderr, "spy: %s\n", spy_error_message(c));
            spy_context_free(c); return 1;
        }
    char *directory = NULL;
    const char *filename = code ? "<string>" : from_stdin ? "<stdin>" : mode;
    const char *slash = code || from_stdin || shell ? NULL : strrchr(filename, '/');
    if (slash) {
        size_t n = (size_t)(slash - filename);
        directory = malloc(n + 1);
        if (!directory) { spy_context_free(c); return 1; }
        memcpy(directory, filename, n); directory[n] = 0;
    }
    spy_set_module_loader(c, load_module, directory ? (*directory ? directory : "/") : ".");
    int status;
    if (shell) status = repl(c);
    else if (code) {
        status = spy_exec(c, source_text, "<string>") ? exit_status(c) : 0;
        if (status < 0) status = 1;
    } else {
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
                status = spy_exec(c, source, filename) ? exit_status(c) : 0;
                if (status < 0) status = 1;
                free(source);
            }
        }
    }
    free(directory); spy_context_free(c);
    return status;
}
