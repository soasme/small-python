/* _spyc: the host services spyc's Python code runs on (docs/build.md 9).
 * spyc registers this C module in its own executable, as any program spyc
 * builds may register one: files and directories, the compiler and the
 * programs spyc runs, and the cleanup a failed or interrupted build owes
 * (docs/build.md 2.1). Every function takes positional arguments.
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
/* The first argument as a path, when there are N arguments. */
static const char *path_of(SPYContext *c, size_t argc, SPYValue *const *argv, size_t n) {
    if (argc == n) return n ? text(c, argv[0]) : "";
    spy_error(c, "TypeError", "wrong number of arguments");
    return NULL;
}

/* read(path): the file's bytes, or None. */
static SPYValue *read_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    const char *path = path_of(c, argc, argv, 1);
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
static SPYValue *listdir_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    const char *path = path_of(c, argc, argv, 1);
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
static SPYValue *kind_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    const char *path = path_of(c, argc, argv, 1);
    struct stat info;
    if (!path) return NULL;
    if (stat(path, &info)) return spy_none(c);
    return S_ISDIR(info.st_mode) ? string(c, "d") : S_ISREG(info.st_mode) ? string(c, "f") : spy_none(c);
}
/* write(path, data): write the file, recorded once opened; False if that
 * failed. */
static SPYValue *write_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    size_t n = 0;
    const char *path = path_of(c, argc, argv, 2);
    const unsigned char *bytes = path ? spy_as_bytes(c, argv[1], &n) : NULL;
    if (!bytes) return NULL;
    FILE *f = fopen(path, "wb");
    if (f && wrote(path)) { fclose(f); return spy_error(c, "MemoryError", "allocation failed"); }
    int failed = !f || fwrite(bytes, 1, n, f) != n;
    if (f && fclose(f)) failed = 1;
    return spy_bool(c, !failed);
}
/* done(failed): the build is over; a failed one removes what it wrote. */
static SPYValue *done_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    int failed = argc == 1 ? spy_truth(c, argv[0]) : (spy_error(c, "TypeError", "wrong number of arguments"), -1);
    if (failed < 0) return NULL;
    if (failed) discard();
    while (written_len) drop(written[written_len - 1]);
    return spy_none(c);
}
/* guard(): SIGINT and SIGTERM stop the compiler, remove what the build
 * wrote, and end spyc by the same signal. */
static SPYValue *guard_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    if (!path_of(c, argc, argv, 0)) return NULL;
    signal(SIGINT, interrupted);
    signal(SIGTERM, interrupted);
    return spy_none(c);
}
/* unlink(path), rmdir(path), mkdir(path): None, or the error's text. An
 * unlinked file is forgotten after it is gone. */
static SPYValue *file_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw;
    const char *path = path_of(c, argc, argv, 1);
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
static SPYValue *unsupported(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)argc; (void)argv; (void)kw; (void)data;
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
/* A NULL-terminated copy of a list of str, or NULL with an error set. */
static char **strings(SPYContext *c, SPYValue *list) {
    SPYValue *iterator = spy_iter(c, list), *item;
    size_t n = 0;
    char **items = calloc(1, sizeof(char *));
    while (iterator && items && (item = spy_next(c, iterator))) {
        const char *s = text(c, item);
        char **grown = s ? realloc(items, (n + 2) * sizeof(char *)) : NULL;
        if (grown) items = grown;
        if (grown && (items[n] = malloc(strlen(s) + 1))) { strcpy(items[n++], s); items[n] = NULL; }
        else if (!spy_error_type(c)[0]) spy_error(c, "MemoryError", "allocation failed");
        spy_release(item);
        if (spy_error_type(c)[0]) break;
    }
    spy_release(iterator);
    if (!items) return spy_error(c, "MemoryError", "allocation failed"), NULL;
    if (!spy_error_type(c)[0] && n) return items;
    if (!spy_error_type(c)[0]) spy_error(c, "ValueError", "an empty command");
    for (size_t i = 0; i < n; i++) free(items[i]);
    free(items);
    return NULL;
}
static void free_strings(char **items) {
    for (size_t i = 0; items[i]; i++) free(items[i]);
    free(items);
}
/* temp(data): a new temporary file in TMPDIR, recorded, holding DATA. */
static SPYValue *temp_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    size_t n = 0;
    const unsigned char *bytes = argc == 1 ? spy_as_bytes(c, argv[0], &n) : NULL;
    if (!bytes) return argc == 1 ? NULL : spy_error(c, "TypeError", "wrong number of arguments");
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
/* compile(output, args): run the compiler, ARGS, in its own process group,
 * which an interruption stops as a whole, recording OUTPUT once it runs.
 * True if it exited with 0. */
static SPYValue *compile_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    const char *output = path_of(c, argc, argv, 2);
    char *copy = output ? malloc(strlen(output) + 1) : NULL, **args = copy ? strings(c, argv[1]) : NULL;
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
    free_strings(args);
    return result;
}
/* rename(source, target): True, or False if it failed. */
static SPYValue *rename_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    const char *from = path_of(c, argc, argv, 2), *to = from ? text(c, argv[1]) : NULL;
    return to ? spy_bool(c, !rename(from, to)) : NULL;
}
/* spawn(path, args): run a program and wait for it: its exit status, or
 * 128 and the signal that ended it. */
static SPYValue *spawn_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    const char *path = path_of(c, argc, argv, 2);
    char **args = path ? strings(c, argv[1]) : NULL;
    if (!args) return NULL;
    pid_t pid;
    int code = 0;
    fflush(stdout);
    int error = posix_spawn(&pid, path, NULL, NULL, args, environ);
    free_strings(args);
    if (error) return os_error(c, "run", path, error);
    while (waitpid(pid, &code, 0) != pid) {}
    return spy_int(c, WIFEXITED(code) ? WEXITSTATUS(code) : 128 + WTERMSIG(code));
}
/* exec(path, args): run a program in place of spyc. */
static SPYValue *exec_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    const char *path = path_of(c, argc, argv, 2);
    char **args = path ? strings(c, argv[1]) : NULL;
    if (!args) return NULL;
    fflush(stdout);
    execv(path, args);
    int error = errno;
    free_strings(args);
    return os_error(c, "run", path, error);
}
/* executable(path): whether the file exists and may be run. */
static SPYValue *executable_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    const char *path = path_of(c, argc, argv, 1);
    return path ? spy_bool(c, !access(path, X_OK)) : NULL;
}
/* pid(): spyc's process id. */
static SPYValue *pid_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    return path_of(c, argc, argv, 0) ? spy_int(c, (int64_t)getpid()) : NULL;
}
#endif

/* fnv(hash, data): FNV-1a over DATA from HASH, as a signed 64-bit int. */
static SPYValue *fnv_native(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)kw; (void)data;
    int64_t seed;
    size_t n = 0;
    if (argc != 2) return spy_error(c, "TypeError", "wrong number of arguments");
    const unsigned char *bytes = spy_as_int(c, argv[0], &seed) ? NULL : spy_as_bytes(c, argv[1], &n);
    if (!bytes) return NULL;
    uint64_t h = (uint64_t)seed;
    for (size_t i = 0; i < n; i++) h = (h ^ bytes[i]) * 0x100000001b3u;
    return spy_int(c, (int64_t)h);
}
static int to_stderr(SPYContext *c, void *data, const char *s, size_t n) {
    (void)c; (void)data;
    return fwrite(s, 1, n, stderr) == n ? 0 : -1;
}
static int flush_stderr(SPYContext *c, void *data) { (void)c; (void)data; return fflush(stderr); }
static int set(SPYContext *c, SPYValue *module, const char *name, SPYValue *value) {
    int status = value ? spy_set_attr(c, module, name, value) : -1;
    spy_release(value);
    return status;
}
/* spyc's diagnostics go to stderr. A program spyc 0.10 or later builds
 * sets that up in its main; the release that builds spyc may not. */
SPY_MODULE int spy_init__spyc(SPYContext *c, SPYValue *module) {
    spy_set_error_output(c, to_stderr, flush_stderr, NULL);
    static const struct { const char *name; SPYNativeKeywords function; intptr_t data; } functions[] = {
        {"read", read_native, 0}, {"listdir", listdir_native, 0}, {"kind", kind_native, 0},
        {"write", write_native, 0}, {"done", done_native, 0}, {"guard", guard_native, 0},
        {"unlink", file_native, 0}, {"rmdir", file_native, 1}, {"mkdir", file_native, 2},
        {"temp", temp_native, 0}, {"compile", compile_native, 0}, {"rename", rename_native, 0},
        {"spawn", spawn_native, 0}, {"exec", exec_native, 0}, {"executable", executable_native, 0},
        {"pid", pid_native, 0}, {"fnv", fnv_native, 0}};
    for (size_t i = 0; i < sizeof functions / sizeof *functions; i++)
        if (set(c, module, functions[i].name, spy_native(c, functions[i].name, functions[i].function, (void *)functions[i].data, NULL)))
            return -1;
    return set(c, module, "cc", string(c, CONFIG_CC)) || set(c, module, "prefix", string(c, CONFIG_PREFIX)) ||
           set(c, module, "version", string(c, spy_version())) ? -1 : 0;
}
