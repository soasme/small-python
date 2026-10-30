/* Linked into every program of a sanitizer build (make sanitize). The options
 * are compiled in, so they hold in processes started with a cleared
 * environment, such as the packages' worker. Every report is appended to
 * REPORT, opened before main so that a sandboxed worker can still write it;
 * make sanitize fails when REPORT is not empty, whatever a test made of the
 * process's status or output. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <sanitizer/common_interface_defs.h>

/* The native recursion guard measures the real stack, which ASan's fake
 * frames hide. A process sent SIGSEGV dies of it, as the packages' crash tests
 * expect; the test runners fail a program that dies of a signal. Leak checking
 * stops the process's threads with ptrace, which the sealed worker's seccomp
 * filter refuses; the engine it runs is leak-checked in every other program. */
/* Asked before the sanitizer runtime is ready, so uninstrumented, with a raw
 * system call and no intercepted function. */
__attribute__((no_sanitize("address"))) static int worker(void) {
#ifdef __linux__
    static const char name[] = "/spy-worker";
    char path[4096];
    long n = syscall(SYS_readlinkat, AT_FDCWD, "/proc/self/exe", path, sizeof(path));
    long k = (long)sizeof(name) - 1;
    if (n < k) return 0;
    for (long i = 0; i < k; i++) if (path[n - k + i] != name[i]) return 0;
    return 1;
#else
    return 0;
#endif
}
const char *__asan_default_options(void) {
    return worker() ? "detect_stack_use_after_return=0:detect_leaks=0:handle_segv=0"
                    : "detect_stack_use_after_return=0:detect_leaks=1:handle_segv=0";
}
const char *__ubsan_default_options(void) { return "print_stacktrace=1:handle_segv=0"; }
const char *__msan_default_options(void) { return "handle_segv=0"; }

__attribute__((constructor)) static void report_to_file(void) {
    int fd = open(REPORT, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0644);
    if (fd < 0) abort();
    __sanitizer_set_report_fd((void *)(long)fd);
}

#ifdef __linux__
/* AddressSanitizer asks for the alternate signal stack before every call that
 * does not return, such as exit, and treats a failure as its own fatal error.
 * The sealed worker's seccomp filter refuses the call; with no alternate stack
 * in use, report that none is set. */
int sigaltstack(const stack_t *stack, stack_t *old) {
    if (!syscall(SYS_sigaltstack, stack, old)) return 0;
    if (errno != EPERM || stack || !old) return -1;
    *old = (stack_t){.ss_flags = SS_DISABLE};
    return 0;
}
#endif
