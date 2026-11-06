/* Contexts are independent: threads that each own one run at once, sharing
 * nothing but native modules, which they all load at once. Under
 * ThreadSanitizer (make CC=clang SANITIZERS=thread sanitize) any
 * process-global state the engine writes is reported as a race.
 *
 * Each context also loads the native _thread and runs virtual threads of its
 * own; the last of them has not started when its context is freed.
 *
 * usage: tests/threads LIBRARY THREAD   (native modules fib and _thread) */
#include "../spy.h"
#include "../spy-std.h"

#include <pthread.h>
#include <stdio.h>
#include <string.h>

enum { THREADS = 4, ROUNDS = 8 };

static const char program[] =
    "import sys, fib\n"
    "class Node:\n"
    "    def __init__(self, n): self.n = n; self.next = self\n"
    "    def __del__(self): freed.append(self.n)\n"
    "    def __repr__(self): return f'Node({self.n})'\n"
    "def gen(n):\n"
    "    for i in range(n):\n"
    "        yield i * i\n"
    "freed = []\n"
    "nodes = [Node(i) for i in range(100)]\n"
    "d = {str(i): i for i in gen(50)}\n"
    "t = tuple(sorted(d, key=lambda k: -d[k]))\n"
    "big = 7 ** 300 // 3\n"
    "try:\n"
    "    raise ValueError(f'{big % 1000}')\n"
    "except ValueError as e:\n"
    "    text = str(e) + repr(nodes[:2]) + 'é' * 3 + str(1.5e300) + hex(big)[:8]\n"
    "async def co(): return len(t)\n"
    "c = co()\n"
    "try:\n"
    "    c.send(None)\n"
    "except StopIteration as stop:\n"
    "    total = stop.value\n"
    "del nodes\n";
static const char threaded[] =
    "import _thread\n"
    "guard = _thread.allocate_lock()\n"
    "count = [0]\n"
    "def add(n):\n"
    "    for _ in range(n):\n"
    "        with guard:\n"
    "            count[0] += 1\n"
    "    if n > 100:\n"
    "        _thread.start_joinable_thread(lambda: add(100)).join()\n"
    "workers = [_thread.start_joinable_thread(lambda: add(500)) for _ in range(3)]\n"
    "for w in workers:\n"
    "    w.join()\n"
    "never = _thread.allocate_lock()\n"
    "never.acquire()\n"
    "_thread.start_new_thread(never.acquire, ())\n";
static const char *library, *thread_library;

static int discard(SPYContext *c, void *data, const char *s, size_t n) {
    (void)c; (void)data; (void)s; (void)n;
    return 0;
}

static void *work(void *failed) {
    for (int round = 0; round < ROUNDS; round++) {
        SPYContext *c = spy_context_new();
        if (!c || spy_std_init(c) || spy_std_load_native(c, "fib", library)) { *(int *)failed = 1; return NULL; }
        spy_set_output(c, discard, NULL, NULL);
        SPYValue *result = NULL;
        if (spy_exec(c, program, "<thread>") || !spy_collect(c) ||
            !(result = spy_eval(c, "repr((total, len(text), sys.getrecursionlimit(), len(freed), fib.fib(20)))", "<thread>")) ||
            strcmp(spy_as_string(c, result, NULL), "(50, 38, 1000, 100, 6765)")) {
            fprintf(stderr, "thread: %s: %s\n", spy_error_type(c), spy_error_display(c));
            *(int *)failed = 1;
        }
        spy_release(result); result = NULL;
        if (spy_std_load_native(c, "_thread", thread_library) || spy_exec(c, threaded, "<threads>") ||
            !(result = spy_eval(c, "repr((count[0], _thread._count()))", "<threads>")) ||
            strcmp(spy_as_string(c, result, NULL), "(1800, 1)")) {
            fprintf(stderr, "_thread: %s: %s\n", spy_error_type(c), spy_error_display(c));
            *(int *)failed = 1;
        }
        spy_release(result);
        spy_context_free(c);
    }
    return NULL;
}

int main(int argc, char **argv) {
    if (argc != 3) { fputs("usage: tests/threads LIBRARY THREAD\n", stderr); return 2; }
    library = argv[1]; thread_library = argv[2];
    pthread_t threads[THREADS];
    int failed[THREADS] = {0};
    for (int i = 0; i < THREADS; i++)
        if (pthread_create(&threads[i], NULL, work, &failed[i])) { perror("pthread_create"); return 1; }
    int status = 0;
    for (int i = 0; i < THREADS; i++) {
        pthread_join(threads[i], NULL);
        status |= failed[i];
    }
    if (!status) printf("Threads: %d contexts at once, %d rounds each, with Python threads in each, passed\n", THREADS, ROUNDS);
    return status;
}
