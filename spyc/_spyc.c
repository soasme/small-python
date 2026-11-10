/* _spyc: the host services spyc's Python code runs on (docs/build.md 9).
 * spyc registers this C module in its own executable, as any program spyc
 * builds may register one: files and directories, the compiler and the
 * programs spyc runs, and the cleanup a failed or interrupted build owes
 * (docs/build.md 2.1). spyc's own code calls each function with the
 * positional arguments it names; their types are checked, their count is
 * not.
 *
 * The files a build began to write are listed here, outside Python, so a
 * signal handler can remove them: the output, the metafile, the dependency
 * rule, and the temporary C file. The list only ever lists too much while
 * it changes, so the handler, interrupting a change, at worst removes a
 * file twice. */
#if !defined(_XOPEN_SOURCE)
#define _XOPEN_SOURCE 700
#endif
#include "spy-module.h"

#include <dirent.h>
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#ifndef _WIN32
#include <spawn.h>
#include <sys/wait.h>

extern char **environ;
#endif

/* The compiler and link flags of spyc's build, and where make install puts
 * spy.h and the libraries. */
#ifndef CONFIG_CC
#define CONFIG_CC "cc"
#endif
#ifndef CONFIG_PREFIX
#define CONFIG_PREFIX "/usr/local"
#endif

static char *written[4];
static volatile sig_atomic_t written_len, compiler;

static void discard(void) {
    for (; written_len; written_len--) unlink(written[written_len - 1]);
}
static void interrupted(int sig) {
#ifndef _WIN32
    if (compiler) { kill(-compiler, sig); waitpid(compiler, NULL, 0); kill(-compiler, SIGKILL); }
#endif
    discard();
    signal(sig, SIG_DFL);
    raise(sig);
}
static int wrote(const char *path) {
    char *copy = malloc(strlen(path) + 1);
    if (!copy) return -1;
    written[written_len] = strcpy(copy, path);
    written_len++;
    return 0;
}
/* Forget PATH, whose file is gone or is kept: copy before the list shrinks. */
static void drop(const char *path) {
    for (sig_atomic_t i = written_len; i-- > 0;)
        if (!strcmp(written[i], path)) {
            char *gone = written[i];
            written[i] = written[written_len - 1];
            written_len--;
            free(gone);
            return;
        }
}

static const char *text(SPYContext *c, SPYValue *v) { return spy_as_string(c, v, NULL); }
static SPYValue *string(SPYContext *c, const char *s) { return spy_string(c, s, strlen(s)); }
static SPYValue *os_error(SPYContext *c, const char *what, const char *path, int error) {
    char message[4200];
    snprintf(message, sizeof message, "cannot %s %s: %s", what, path, strerror(error));
    return spy_error(c, "OSError", message);
}
/* Each function's parameters, of which it reads ARGV: spyc passes the
 * arguments each names, and no keywords. */
#define PARAMETERS SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data
#define UNUSED (void)argc; (void)kw; (void)data

/* read(path): the file's bytes, or None. */
static SPYValue *read_native(PARAMETERS) {
    UNUSED;
    const char *path = text(c, argv[0]);
    FILE *f = path ? fopen(path, "rb") : NULL;
    if (!f) return path ? spy_none(c) : NULL;
    char *bytes = NULL;
    size_t len = 0, cap = 0;
    for (size_t n = 1; n;) {
        char *grown = len < cap ? bytes : realloc(bytes, cap = cap ? cap * 2 : 65536);
        if (!grown) break;
        bytes = grown;
        len += n = fread(bytes + len, 1, cap - len, f);
    }
    SPYValue *result = ferror(f) ? spy_none(c) : bytes ? spy_bytes(c, bytes, len) : spy_error(c, "MemoryError", "allocation failed");
    fclose(f);
    free(bytes);
    return result;
}
/* listdir(path): the names in a directory, or None. */
static SPYValue *listdir_native(PARAMETERS) {
    UNUSED;
    const char *path = text(c, argv[0]);
    DIR *dir = path ? opendir(path) : NULL;
    if (!dir) return path ? spy_none(c) : NULL;
    SPYValue *names = spy_list(c);
    for (struct dirent *e; names && (e = readdir(dir));) {
        SPYValue *name = string(c, e->d_name);
        if (!name || spy_list_append(c, names, name)) { spy_release(names); names = NULL; }
        spy_release(name);
    }
    closedir(dir);
    return names;
}
/* kind(path): "d" for a directory, "f" for a regular file, or None. */
static SPYValue *kind_native(PARAMETERS) {
    UNUSED;
    const char *path = text(c, argv[0]);
    struct stat info;
    if (!path) return NULL;
    if (stat(path, &info)) return spy_none(c);
    return S_ISDIR(info.st_mode) ? string(c, "d") : S_ISREG(info.st_mode) ? string(c, "f") : spy_none(c);
}
/* write(path, data): write the file, recorded once opened; False if that
 * failed. */
static SPYValue *write_native(PARAMETERS) {
    UNUSED;
    size_t n = 0;
    const char *path = text(c, argv[0]);
    const unsigned char *bytes = path ? spy_as_bytes(c, argv[1], &n) : NULL;
    if (!bytes) return NULL;
    FILE *f = fopen(path, "wb");
    if (f && wrote(path)) { fclose(f); return spy_error(c, "MemoryError", "allocation failed"); }
    int failed = !f || fwrite(bytes, 1, n, f) != n;
    if (f && fclose(f)) failed = 1;
    return spy_bool(c, !failed);
}
/* done(failed): the build is over; a failed one removes what it wrote. */
static SPYValue *done_native(PARAMETERS) {
    UNUSED;
    int failed = spy_truth(c, argv[0]);
    if (failed < 0) return NULL;
    if (failed) discard();
    while (written_len) drop(written[written_len - 1]);
    return spy_none(c);
}
/* guard(): SIGINT and SIGTERM stop the compiler, remove what the build
 * wrote, and end spyc by the same signal. */
static SPYValue *guard_native(PARAMETERS) {
    UNUSED; (void)argv;
    signal(SIGINT, interrupted);
    signal(SIGTERM, interrupted);
    return spy_none(c);
}
/* unlink(path), rmdir(path), mkdir(path): None, or the error's text. An
 * unlinked file is forgotten after it is gone. */
static SPYValue *file_native(PARAMETERS) {
    (void)argc; (void)kw;
    const char *path = text(c, argv[0]);
    if (!path) return NULL;
    int which = (int)(intptr_t)data;
#ifdef _WIN32
    int failed = which == 0 ? unlink(path) : which == 1 ? rmdir(path) : mkdir(path);
#else
    int failed = which == 0 ? unlink(path) : which == 1 ? rmdir(path) : mkdir(path, 0777);
#endif
    if (!failed && which == 0) drop(path);
    return failed ? string(c, strerror(errno)) : spy_none(c);
}

#ifdef _WIN32
/* As qjsc without CONFIG_CC: the C file is all spyc can give here. */
static SPYValue *unsupported(PARAMETERS) {
    UNUSED; (void)argv;
    return spy_error(c, "OSError", "executable output is not supported on this platform; use -e or -c");
}
#define temp_native unsupported
#define compile_native unsupported
#define rename_native unsupported
#define spawn_native unsupported
#define exec_native unsupported
#define executable_native unsupported
#define pid_native unsupported
#else
/* A command, given as its words each ended by NUL, as a NULL-terminated
 * array in one allocation that free releases, or NULL with an error set. */
static char **command(SPYContext *c, SPYValue *words) {
    size_t n = 0, count = 0;
    const unsigned char *bytes = spy_as_bytes(c, words, &n);
    for (size_t i = 0; bytes && i < n; i++) count += !bytes[i];
    char **args = bytes ? malloc((count + 1) * sizeof *args + n) : NULL;
    if (!args) return bytes ? (spy_error(c, "MemoryError", "allocation failed"), NULL) : NULL;
    char *copy = memcpy(args + count + 1, bytes, n);
    for (size_t k = 0; k < count; k++, copy += strlen(copy) + 1) args[k] = copy;
    args[count] = NULL;
    return args;
}
/* temp(data): a new temporary file in TMPDIR, recorded, holding DATA. */
static SPYValue *temp_native(PARAMETERS) {
    UNUSED;
    size_t n = 0;
    const unsigned char *bytes = spy_as_bytes(c, argv[0], &n);
    if (!bytes) return NULL;
    const char *dir = getenv("TMPDIR");
    char path[4096];
    snprintf(path, sizeof path, "%s/spyc.XXXXXX", dir && *dir ? dir : "/tmp");
    int fd = mkstemp(path);
    if (fd < 0) return os_error(c, "write", path, errno);
    if (wrote(path)) { close(fd); unlink(path); return spy_error(c, "MemoryError", "allocation failed"); }
    FILE *f = fdopen(fd, "wb");
    int failed = !f || fwrite(bytes, 1, n, f) != n;
    if (f ? fclose(f) : close(fd)) failed = 1;
    return failed ? os_error(c, "write", path, errno ? errno : EIO) : string(c, path);
}
/* compile(output, command): run the compiler in its own process group,
 * which an interruption stops as a whole, recording OUTPUT once it runs.
 * True if it exited with 0. */
static SPYValue *compile_native(PARAMETERS) {
    UNUSED;
    const char *output = text(c, argv[0]);
    char *copy = output ? malloc(strlen(output) + 1) : NULL, **args = copy ? command(c, argv[1]) : NULL;
    if (!args) { free(copy); return output && !copy ? spy_error(c, "MemoryError", "allocation failed") : NULL; }
    strcpy(copy, output);
    /* Once the compiler runs it writes the output, which a failure removes.
     * Signals wait until both are recorded. */
    sigset_t stops, none;
    sigemptyset(&stops); sigaddset(&stops, SIGINT); sigaddset(&stops, SIGTERM);
    sigemptyset(&none);
    posix_spawnattr_t attributes;
    posix_spawnattr_init(&attributes);
    posix_spawnattr_setflags(&attributes, POSIX_SPAWN_SETPGROUP | POSIX_SPAWN_SETSIGMASK);
    posix_spawnattr_setsigmask(&attributes, &none);
    pid_t pid = 0;
    int code = 0;
    fflush(stdout);
    sigprocmask(SIG_BLOCK, &stops, NULL);
    int error = posix_spawnp(&pid, args[0], NULL, &attributes, args, environ);
    if (!error) { written[written_len] = copy; written_len++; compiler = pid; copy = NULL; }
    sigprocmask(SIG_UNBLOCK, &stops, NULL);
    posix_spawnattr_destroy(&attributes);
    SPYValue *result = error ? os_error(c, "run", args[0], error) : NULL;
    if (!error) {
        int ok = waitpid(pid, &code, 0) == pid && WIFEXITED(code) && !WEXITSTATUS(code);
        compiler = 0;
        result = spy_bool(c, ok);
    }
    free(copy);
    free(args);
    return result;
}
/* rename(source, target): True, or False if it failed. */
static SPYValue *rename_native(PARAMETERS) {
    UNUSED;
    const char *from = text(c, argv[0]), *to = from ? text(c, argv[1]) : NULL;
    return to ? spy_bool(c, !rename(from, to)) : NULL;
}
/* spawn(path, command): run a program and wait for it: its exit status, or
 * 128 and the signal that ended it. */
static SPYValue *spawn_native(PARAMETERS) {
    UNUSED;
    const char *path = text(c, argv[0]);
    char **args = path ? command(c, argv[1]) : NULL;
    if (!args) return NULL;
    pid_t pid;
    int code = 0;
    fflush(stdout);
    int error = posix_spawn(&pid, path, NULL, NULL, args, environ);
    free(args);
    if (error) return os_error(c, "run", path, error);
    while (waitpid(pid, &code, 0) != pid) {}
    return spy_int(c, WIFEXITED(code) ? WEXITSTATUS(code) : 128 + WTERMSIG(code));
}
/* exec(path, command): run a program in place of spyc. */
static SPYValue *exec_native(PARAMETERS) {
    UNUSED;
    const char *path = text(c, argv[0]);
    char **args = path ? command(c, argv[1]) : NULL;
    if (!args) return NULL;
    fflush(stdout);
    execv(path, args);
    int error = errno;
    free(args);
    return os_error(c, "run", path, error);
}
/* executable(path): whether the file exists and may be run. */
static SPYValue *executable_native(PARAMETERS) {
    UNUSED;
    const char *path = text(c, argv[0]);
    return path ? spy_bool(c, !access(path, X_OK)) : NULL;
}
/* pid(): spyc's process id. */
static SPYValue *pid_native(PARAMETERS) {
    UNUSED; (void)argv;
    return spy_int(c, (int64_t)getpid());
}
#endif

/* fnv(hash, data): FNV-1a over DATA from HASH, as a signed 64-bit int. */
static SPYValue *fnv_native(PARAMETERS) {
    UNUSED;
    int64_t seed;
    size_t n = 0;
    const unsigned char *bytes = spy_as_int(c, argv[0], &seed) ? NULL : spy_as_bytes(c, argv[1], &n);
    if (!bytes) return NULL;
    uint64_t h = (uint64_t)seed;
    for (size_t i = 0; i < n; i++) h = (h ^ bytes[i]) * 0x100000001b3u;
    return spy_int(c, (int64_t)h);
}
/* stderr is unbuffered, so the error output needs no flush. */
static int to_stderr(SPYContext *c, void *data, const char *s, size_t n) {
    (void)c; (void)data;
    return fwrite(s, 1, n, stderr) == n ? 0 : -1;
}
static int set(SPYContext *c, SPYValue *module, const char *name, SPYValue *value) {
    int status = value ? spy_set_attr(c, module, name, value) : -1;
    spy_release(value);
    return status;
}
/* spyc runs on the engine primitives, which this module registers as
 * _spy, with no standard module; its diagnostics go to stderr. */
SPY_MODULE int spy_init__spyc(SPYContext *c, SPYValue *module) {
    static const struct { const char *name; SPYNativeKeywords function; intptr_t data; } functions[] = {
        {"read", read_native, 0}, {"listdir", listdir_native, 0}, {"kind", kind_native, 0},
        {"write", write_native, 0}, {"done", done_native, 0}, {"guard", guard_native, 0},
        {"unlink", file_native, 0}, {"rmdir", file_native, 1}, {"mkdir", file_native, 2},
        {"temp", temp_native, 0}, {"compile", compile_native, 0}, {"rename", rename_native, 0},
        {"spawn", spawn_native, 0}, {"exec", exec_native, 0}, {"executable", executable_native, 0},
        {"pid", pid_native, 0}, {"fnv", fnv_native, 0}};
    spy_set_error_output(c, to_stderr, NULL, NULL);
    int status = spy_new_module(c, "_spy", spy_init_primitives);
    for (size_t i = 0; !status && i < sizeof functions / sizeof *functions; i++)
        status = set(c, module, functions[i].name, spy_native(c, functions[i].name, functions[i].function, (void *)functions[i].data, NULL));
    return status || set(c, module, "cc", string(c, CONFIG_CC)) || set(c, module, "prefix", string(c, CONFIG_PREFIX)) ||
           set(c, module, "version", string(c, spy_version())) ? -1 : 0;
}
