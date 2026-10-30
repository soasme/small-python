/* Contexts are independent: threads that each own one run at once, sharing
 * nothing. Under ThreadSanitizer (make CC=clang SANITIZERS=thread sanitize)
 * any process-global state the engine writes is reported as a race. */
#include "../spy.h"
#include "../spy-std.h"

#include <pthread.h>
#include <stdio.h>
#include <string.h>

enum { THREADS = 4, ROUNDS = 8 };

static const char program[] =
    "import gc, sys\n"
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
    "del nodes\n"
    "gc.collect()\n"
    "result = (total, len(text), sys.getrecursionlimit(), len(freed))\n";

static int discard(void *data, const char *s, size_t n) {
    (void)data; (void)s; (void)n;
    return 0;
}

static void *work(void *failed) {
    for (int round = 0; round < ROUNDS; round++) {
        SPYContext *c = spy_context_new();
        if (!c || spy_std_init(c)) { *(int *)failed = 1; return NULL; }
        spy_set_output(c, discard, NULL);
        SPYValue *result = NULL;
        if (spy_exec(c, program, "<thread>") || !(result = spy_eval(c, "repr(result)", "<thread>")) ||
            strcmp(spy_as_string(c, result, NULL), "(50, 38, 1000, 100)")) {
            fprintf(stderr, "thread: %s: %s\n", spy_error_type(c), spy_error_display(c));
            *(int *)failed = 1;
        }
        spy_release(result);
        spy_context_free(c);
    }
    return NULL;
}

int main(void) {
    pthread_t threads[THREADS];
    int failed[THREADS] = {0};
    for (int i = 0; i < THREADS; i++)
        if (pthread_create(&threads[i], NULL, work, &failed[i])) { perror("pthread_create"); return 1; }
    int status = 0;
    for (int i = 0; i < THREADS; i++) {
        pthread_join(threads[i], NULL);
        status |= failed[i];
    }
    if (!status) printf("Threads: %d contexts at once, %d rounds each, passed\n", THREADS, ROUNDS);
    return status;
}
