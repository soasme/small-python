/* Allocation failure, SQLite style: each program runs once per allocation it
 * makes with exactly that allocation failing, then once per allocation with
 * it and every later one failing, as when memory stays exhausted. Every run
 * must end cleanly, in a result or an exception, and free everything it
 * allocated: the engine frees through this counter, so a leak is seen per
 * run, not only at exit.
 * Run it under make sanitize so a bad cleanup path is also reported.
 *
 * usage: tests/oom [FILE...]  (each file a program; none: the built-in set) */
#define _XOPEN_SOURCE 700
#if defined(__APPLE__)
#define _DARWIN_C_SOURCE
#endif
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void *oom_malloc(size_t);
void *oom_calloc(size_t, size_t);
void *oom_realloc(void *, size_t);
void *oom_aligned_alloc(size_t, size_t);
void oom_free(void *);
char *oom_realpath(const char *, char *);

/* The engine's own headers first, so the renaming reaches only its code. */
#include <complex.h>
#include <ctype.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdarg.h>
#define malloc oom_malloc
#define calloc oom_calloc
#define realloc oom_realloc
#define aligned_alloc oom_aligned_alloc
#define free oom_free
#define realpath oom_realpath
#include "../spy.c"
#include "../spy-std.c"
#undef malloc
#undef calloc
#undef realloc
#undef aligned_alloc
#undef free
#undef realpath

/* count: allocations so far; fail: the first that fails (0: none), and with
 * lasting every one after it; live: blocks not yet freed. */
static size_t count, fail, live;
static int lasting;

static int fails(void) { return ++count == fail || (lasting && fail && count > fail); }
void *oom_malloc(size_t n) {
    if (fails()) return NULL;
    void *p = malloc(n ? n : 1);
    if (p) live++;
    return p;
}
void *oom_calloc(size_t k, size_t n) {
    if (fails()) return NULL;
    void *p = calloc(k ? k : 1, n ? n : 1);
    if (p) live++;
    return p;
}
void *oom_realloc(void *p, size_t n) {
    if (!p) return oom_malloc(n);
    if (fails()) return NULL;
    return realloc(p, n ? n : 1);
}
void *oom_aligned_alloc(size_t alignment, size_t n) {
    if (fails()) return NULL;
    void *p = aligned_alloc(alignment, n);
    if (p) live++;
    return p;
}
void oom_free(void *p) {
    if (!p) return;
    live--;
    free(p);
}
char *oom_realpath(const char *path, char *resolved) {
    char *real = realpath(path, resolved);
    if (!real || resolved) return real;
    char *copy = oom_malloc(strlen(real) + 1);
    if (copy) strcpy(copy, real);
    free(real);
    return copy;
}

static int discard(void *data, const char *s, size_t n) {
    (void)data; (void)s; (void)n;
    return 0;
}

/* One run of source with allocation `fail` failing; the allocations it made. */
static size_t run(const char *source, const char *name, int *status) {
    count = 0;
    live = 0;
    SPYContext *c = spy_context_new();
    *status = -1;
    if (c) {
        spy_set_output(c, discard, NULL);
        spy_set_step_limit(c, 1000000);
        *status = spy_std_init(c) || spy_exec(c, source, name);
        spy_clear_error(c);
        spy_collect(c);
        spy_context_free(c);
    }
    if (live) {
        fprintf(stderr, "%s: %zu blocks leaked when allocation %zu of %zu failed\n", name, live, fail, count);
        exit(1);
    }
    return count;
}

static const char *const programs[] = {
    "x = [i * i for i in range(20)]\n"
    "d = {str(i): i for i in x}\n"
    "s = {i % 7 for i in x}\n"
    "t = tuple(sorted(d, key=lambda k: -d[k]))\n"
    "print(len(x), len(d), len(s), t[:3], f'{x[3]:>5}', 'a,b'.split(','))\n",

    "class A:\n"
    "    def __init__(self, v): self.v = v\n"
    "    def __repr__(self): return f'A({self.v!r})'\n"
    "    def __eq__(self, o): return isinstance(o, A) and o.v == self.v\n"
    "    __hash__ = None\n"
    "class B(A):\n"
    "    def __init__(self, v): super().__init__(v * 2)\n"
    "a = [B(i) for i in range(5)]\n"
    "a.append(a)\n"
    "print(repr(a), A(2) == B(1))\n",

    "def gen(n):\n"
    "    try:\n"
    "        for i in range(n):\n"
    "            yield i\n"
    "    finally:\n"
    "        print('done')\n"
    "g = gen(10)\n"
    "print(next(g), sum(g))\n"
    "def f(*a, k=1, **kw): return a, k, kw\n"
    "print(f(1, 2, k=3, z=4))\n"
    "try:\n"
    "    {}['missing']\n"
    "except KeyError as e:\n"
    "    print(type(e).__name__, e.args)\n"
    "n = 10 ** 40 // 7\n"
    "print(n, hex(n), str(1.5e300), 'é' * 3, b'ab' + b'cd')\n",

    "import asyncio\n" /* fails: no such module in the bare core */
    "print('unreachable')\n",

    "async def co(x):\n"
    "    return x + 1\n"
    "c = co(1)\n"
    "try:\n"
    "    c.send(None)\n"
    "except StopIteration as e:\n"
    "    print(e.value)\n"
    "x: int = 3\n"
    "match [x, {'k': 'v'}]:\n"
    "    case [3, {'k': str() as v}]: print(v)\n"
    "try:\n"
    "    raise ExceptionGroup('g', [ValueError(1), TypeError(2)])\n"
    "except* ValueError as e: print('value', e.exceptions)\n"
    "except* TypeError: print('type')\n",

    /* sys is left to fuzz_oom and tests/oom FILE: importing it makes 5,000
     * allocations, too many to sweep here. */
    "import gc\n"
    "class N:\n"
    "    def __init__(self): self.me = self\n"
    "    def __del__(self): print('gone')\n"
    "n = N()\n"
    "del n\n"
    "print(gc.collect() > 0, gc.get_referents([n := 1]), gc.isenabled())\n",
};

static char *read_file(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); exit(2); }
    size_t len = 0, cap = 4096;
    char *s = malloc(cap);
    for (size_t n; s && (n = fread(s + len, 1, cap - len - 1, f)) > 0;) {
        len += n;
        if (len == cap - 1) {
            char *grown = realloc(s, cap *= 2);
            if (!grown) free(s);
            s = grown;
        }
    }
    fclose(f);
    if (!s) { fputs("oom: out of memory\n", stderr); exit(2); }
    s[len] = 0;
    return s;
}

/* Fail each allocation of source after the first `from`: once, then from
 * there on. */
static size_t check(const char *source, const char *name, size_t from) {
    int status;
    fail = 0;
    size_t total = run(source, name, &status), failed[2] = {0, 0};
    const char *ends = status ? "an exception" : "a result";
    for (lasting = 0; lasting < 2; lasting++)
        for (fail = from + 1; fail <= total; fail++) {
            run(source, name, &status);
            failed[lasting] += status != 0;
        }
    lasting = 0;
    printf("%s (ends in %s): allocations %zu to %zu failed; exceptions: %zu failing once, %zu failing from there on\n",
           name, ends, from + 1, total, failed[0], failed[1]);
    return total;
}

int main(int argc, char **argv) {
    /* The empty program covers creating and freeing a context; the others
     * fail only what they allocate after that. */
    size_t from = check("", "<empty>", 0);
    for (int i = 1; i < argc; i++) {
        char *source = read_file(argv[i]);
        check(source, argv[i], from);
        free(source);
    }
    for (size_t i = 0; argc == 1 && i < sizeof programs / sizeof *programs; i++) {
        char name[32];
        snprintf(name, sizeof name, "<program %zu>", i + 1);
        check(programs[i], name, from);
    }
    return 0;
}
