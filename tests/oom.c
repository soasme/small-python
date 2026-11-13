/* Allocation failure, SQLite style: each program runs once per allocation it
 * makes with exactly that allocation failing, then once per allocation with
 * it and every later one failing, as when memory stays exhausted. Every run
 * must end cleanly, in a result or an exception, and free everything it
 * allocated: the engine frees through this counter, so a leak is seen per
 * run, not only at exit.
 * Run it under make sanitize so a bad cleanup path is also reported.
 *
 * usage: tests/oom [--native LIBRARY] [FILE...]
 *   (each file a program; none: the built-in set; LIBRARY: a native module
 *   defining fib, also loaded and imported) */
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
static int fails(void);
#define reuse_fails() fails()
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
/* A native module run() loads as fib when the program imports it, as the
 * spy command's loader does, and a module of source it loads as imported,
 * each when set. */
static const char *native, *imported;
static SPYValue *load(SPYContext *c, void *data, const char *name) {
    if (imported && !strcmp(name, "imported")) return spy_bytes(c, imported, strlen(imported));
    if (native && !strcmp(name, "fib")) spy_std_load_native(c, name, data);
    return NULL;
}

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

static int discard(SPYContext *c, void *data, const char *s, size_t n) {
    (void)c; (void)data; (void)s; (void)n;
    return 0;
}

/* One run of source with allocation `fail` failing; the allocations it made. */
static size_t run(const char *source, const char *name, int *status) {
    count = 0;
    live = 0;
    SPYContext *c = spy_context_new();
    *status = -1;
    if (c) {
        spy_set_output(c, discard, NULL, NULL);
        spy_set_limit(c, SPY_LIMIT_STEPS, 1000000);
        if (native || imported) spy_set_module_loader(c, load, (void *)native);
        const char *const args[] = {"prog", "caf\xc3\xa9", "\xff"};
        *status = spy_set_argv(c, 3, args, 3, args) || spy_std_init(c) || spy_exec(c, source, name);
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
    "class D:\n"
    "    def __get__(self, obj, owner): return owner.__name__\n"
    "class A:\n"
    "    d = D()\n"
    "def f(): return A().d\n"
    "print(f())\n",

    "class G:\n"
    "    def __getattr__(self, k):\n"
    "        for i in range(1): pass\n"
    "        return k\n"
    "def f():\n"
    "    for i in range(1): pass\n"
    "    return G().missing\n"
    "print(f())\n",

    "class K:\n"
    "    def __hash__(self): return 0\n"
    "    def __eq__(self, other):\n"
    "        for i in range(1): pass\n"
    "        return False\n"
    "def f():\n"
    "    for i in range(1): pass\n"
    "    return len({K()} | {K(), K()})\n"
    "print(f())\n",

    "class E:\n"
    "    def __mro_entries__(self, bases):\n"
    "        for i in range(1): pass\n"
    "        return (object,)\n"
    "class C(E()):\n"
    "    for i in range(1): pass\n"
    "print(C.__orig_bases__)\n",

    "x = [i * i for i in range(20)]\n"
    "d = {str(i): i for i in x}\n"
    "s = {i % 7 for i in x}\n"
    "t = tuple(sorted(d, key=lambda k: -d[k]))\n"
    "pairs = [(i, (i, 0.5)) for i in range(3)]\n" /* Sealed at shutdown. */
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
    "class Q:\n"
    "    def __eq__(self, o):\n"
    "        for i in range(1): pass\n"
    "        return False\n"
    "q = [1, Q()]\n"
    "def eqs(a, b): return [len(a), a == b, [len(a), a == b, [len(a), a == b, [len(a), a == b, [len(a), a == b, [len(a), a == b]]]]]][1:]\n"
    "def same(a): return a\n"
    "def finds(a): return [len(a), same(a).count(1), [len(a), same(a).count(1), [len(a), same(a).count(1), [len(a), "
    "same(a).count(1), [len(a), same(a).count(1), [len(a), same(a).count(1), [len(a), same(a).count(1), [len(a), same(a).count(1), "
    "[len(a), same(a).count(1), [len(a), same(a).count(1), [len(a), same(a).count(1), [len(a), same(a).count(1), [len(a), "
    "same(a).count(1), [len(a), same(a).count(1), [len(a), same(a).count(1), [len(a), same(a).count(1), [len(a), same(a).count(1), "
    "[len(a), same(a).count(1), [len(a), same(a).count(1), [len(a), same(a).count(1), [len(a), same(a).count(1), [len(a), "
    "same(a).count(1), [len(a), same(a).count(1), [same(a).count(1)]]]]]]]]]]]]]]]]]]]]]]]][1:]\n"
    "class L:\n"
    "    def __lt__(self, o):\n"
    "        for i in range(1): pass\n"
    "        return False\n"
    "def mins(r): return [len(r), min(same(r)) is r[0], [len(r), min(same(r)) is r[0], [len(r), "
    "min(same(r)) is r[0], [len(r), min(same(r)) is r[0], [len(r), min(same(r)) is r[0], [len(r), "
    "min(same(r)) is r[0], [len(r), min(same(r)) is r[0], [len(r), min(same(r)) is r[0], [len(r), "
    "min(same(r)) is r[0], [len(r), min(same(r)) is r[0], [len(r), min(same(r)) is r[0], [len(r), "
    "min(same(r)) is r[0], [len(r), min(same(r)) is r[0], [len(r), min(same(r)) is r[0], [len(r), "
    "min(same(r)) is r[0], [min(same(r)) is r[0]]]]]]]]]]]]]]]]][1:]\n"
    "print(repr(a), A(2) == B(1), [Q() in q, Q() in q, Q() in q, Q() in q, Q() in q, Q() in q], eqs(q, [1, Q()]), finds(q), (lambda: mins([L(), L()]))())\n",

    /* Lookups, stores and str.format jobs on the machine, deeper and deeper. */
    "class K:\n"
    "    def __hash__(s): return 1\n"
    "    def __eq__(s, o):\n"
    "        for i in range(1): pass\n"
    "        return NotImplemented\n"
    "class F:\n"
    "    def __format__(s, spec):\n"
    "        for i in range(1): pass\n"
    "        return 'f' + spec\n"
    "d = {K(): 1}\n"
    "def look(d): return [K() in d, [K() in d, [K() in d, [K() in d, [K() in d, [K() in d, [K() in d, [K() in d]]]]]]]][1:]\n"
    "def fmt(f): return ['{}{x}'.format(f, x=f), ['{:{}}'.format(f, f), ['{0.f}'.format(f), ['{:{}}'.format(f, f), "
    "['{}'.format(f), ['{:{}}'.format(f, f), ['{}'.format(f)]]]]]]][1:]\n"
    "F.f = F()\n"
    "e = {}\n"
    "e[K()] = 1\n"
    "e[K()] = 2\n"
    "print(look(d), fmt(F()), len(e), len({K(), K()}))\n",

    /* Conversions map() and filter() call on the machine, deeper and deeper. */
    "class S:\n"
    "    def __str__(s):\n"
    "        for i in range(1): pass\n"
    "        return 's'\n"
    "    def __bool__(s):\n"
    "        for i in range(1): pass\n"
    "        return True\n"
    "def conv(s): return [list(map(str, [s])), [list(filter(None, [s])), [list(map(str, [s])), [list(filter(None, [s])), "
    "[list(map(str, [s])), [list(filter(None, [s])), [list(map(str, [s])), [len(list(filter(None, [s])))]]]]]]]][1:]\n"
    "print(conv(S()))\n"
    "def pct(s): return ['%s' % s, ['%r|%s' % (s, 1), ['%(k)a' % {'k': s}, ['%5s' % (s,), ['%s%s' % (s, s), ['%-3r' % s]]]]]][1:]\n"
    "S.__repr__ = S.__str__\n"
    "print(pct(S()))\n"
    "S.__hash__ = lambda s: [i for i in range(1)][0]\n"
    "def keys(s): return [dict.fromkeys([s]), [dict.fromkeys((1, s), 0), [len(dict.fromkeys([s, s])), [dict.fromkeys([s, 2])[s]]]]][1:]\n"
    "print(keys(S()))\n"
    "def grow(s): t = {0}; return [t.update([s]), [t.update((1, s)), [t.update([s, 2]), [len(t)]]]][1:]\n"
    "print(grow(S()))\n"
    "S.__eq__ = lambda s, o: [i for i in range(1)][0] == 0\n"
    "def same(s): return [set([s, S()]), [dict.fromkeys((S(), s), 1), [frozenset([S(), S(), S()]), [len({*[s, S()]})]]]][1:]\n"
    "print(same(S()))\n"
    "def find(s): d, t = {s: 1}, {s}; return [d.get(S()), [d.setdefault(S()), [t.add(S()), [t.discard(S()), [d.pop(S()), [t.add(s), [t.remove(S())]]]]]]][1:]\n"
    "print(find(S()))\n"
    "def keyed(s): t = (1, (s,)); return [{t: 1}, [{(s, 2): 0}[s, 2], [{}.get((s,)), [(s, s) in {1}, [{(s,), (2, s)}]]]]][1:]\n"
    "print(keyed(S()))\n"
    "def hashed(s): return [hash((s,)), [hash((1, (s, 2))), [hash(((s,), s))]]][1:]\n"
    "print(hashed(S()))\n"
    "def built(s): return [set([(s,)]), [frozenset([(1, (s,))]), [dict.fromkeys([(s, 2)]), [len({*[(s,), (2, s)]})]]]][1:]\n"
    "print(built(S()))\n"
    "def paired(s): d = {(s, 1): 2}; return [d[(S(), 1)], [(S(), 1) in d, [d.get((S(), 1)), [{(S(),), (s,)}, [{(s,)} == {(S(),)}]]]]][1:]\n"
    "print(paired(S()))\n"
    "def gathered(s): return [set([(s,), (S(),)]), [dict.fromkeys([(1, (s,)), (1, (S(),))]), [len({*[(S(), 2), (s, 2)]})]]][1:]\n"
    "print(gathered(S()))\n"
    "def held(s): t = (s,); hash(t); return [{(S(),): 1}.get(t), [set([(S(),), t]), [{(S(),)}.add(t)]]][1:]\n"
    "print(held(S()))\n"
    "def mapped(s): return [list(map(hash, [(s,)])), [[h for h in map(hash, [(1, (s,))])], [sum(map(hash, [(s, 2)]))]]][1:]\n"
    "print(mapped(S()))\n"
    "def listed(s): return ['%s' % [s], ['%r|%s' % ((s, 1), [2, s]), ['%(k)a' % {'k': [s]}]]][1:]\n"
    "print(listed(S()))\n"
    "def nested(s): return [repr([1, [s]]), [str(([s], (s,))), ['%s' % [[s]]]]][1:]\n"
    "print(nested(S()))\n"
    "class Keyed:\n    def __init__(self, k): self.k = k\n    def keys(self): return self.k\n    def __getitem__(self, k): return 1\n"
    "def pairs(s): d = {}; return [dict([(s, 1)]), [d.update(zip([s], [2])), [set(zip([1], [s])), [dict(x for x in [[s, 3]]), [dict(Keyed([s]))]]]]][1:]\n"
    "print(pairs(S()))\n"
    "def adapted(s): return [list(zip(map(str, [s]), 'a')), [list(enumerate(map(str, [s]))), [[x for x in zip([1], map(str, [s]))]]]][1:]\n"
    "print(adapted(S()))\n",

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
    "except* TypeError: print('type')\n"
    "try:\n"
    "    raise KeyError(3)\n"
    "except* KeyError as e: print('naked', e.exceptions)\n",

    "class A:\n"
    "    __x = 1\n"
    "    y = t'{__x!r:>3} {(__x)}'\n"
    "print(A.y.strings, A.y.interpolations[0].expression)\n"
    "print([i for i in range(2 ** 70, 2 ** 70 + 2)], list(enumerate('ab', 2 ** 70)))\n",

    /* A backtracking parse that clears a failed allocation's error still
     * fails; functions rebuilt from code, generators and lazy imports. */
    "def outer(a, /, b, *c, d, **e):\n"
    "    def inner(): return a + b + len(c) + d + len(e) + g\n"
    "    return inner\n"
    "g = 1\n"
    "fn = outer(1, 2, 3, d=4, f=5)\n"
    "F = type(fn)\n"
    "copy = F(fn.__code__, globals(), 'copy', None, fn.__closure__, None)\n"
    "print(copy(), fn.__code__.co_freevars, outer.__code__.co_names, outer.__code__.co_varnames)\n"
    "class K:\n"
    "    def m(self, __p): return __p\n"
    "print(K().m(3), {1: 2, 3: 4}.popitem())\n"
    "l = [1, 2, 3]; l[1:2] = list(range(40)); print(len(l))\n"
    "print('a,b'.partition(','), 'ab'.rpartition('x'), divmod(7.5, 2), divmod(7, 2))\n"
    "def gen():\n"
    "    try:\n"
    "        x = yield 1\n"
    "        yield x\n"
    "    except ValueError as e:\n"
    "        yield repr(e)\n"
    "it = gen(); next(it); print(it.send(5))\n"
    "it = gen(); next(it)\n"
    "try:\n"
    "    raise ValueError('v')\n"
    "except ValueError as e:\n"
    "    print(it.throw(ValueError, 'w', e.__traceback__))\n"
    "class M:\n"
    "    def __enter__(self): return self\n"
    "    def __exit__(self, *a): return False\n"
    "def wg():\n"
    "    with M() as m:\n"
    "        yield m\n"
    "print(next(wg()) is not None)\n"
    "class I(int): pass\n"
    "print(I(5) + 1)\n"
    "lazy from _spy import _tracked, _collect\n"
    "print(_tracked([]))\n",

    /* sys is left to fuzz_oom and tests/oom FILE: importing it makes 5,000
     * allocations, too many to sweep here. */
    "from _spy import _collect\n"
    "class N:\n"
    "    def __init__(self): self.me = self\n"
    "    def __del__(self): print('gone')\n"
    "n = N()\n"
    "del n\n"
    "print(_collect() > 0)\n",

    /* Cleanup after a value or block the context reuses fails. */
    "print({1: 2}.popitem(), list(range(10**30, 10**30 + 2)), t\"a{1}b\".strings)\n"
    "def diff(a, b, *, c=1): return a - b\n"
    "swapped = type(diff)(diff.__code__.replace(co_varnames=(\"b\", \"a\", \"c\")), {}, \"s\", (1, 2), None, {\"c\": 3})\n"
    "print(swapped(10, 1), swapped(a=10, b=1))\n"
    "def outer():\n"
    "    x = 1\n"
    "    def f(): return (len, lambda: x)\n"
    "    return f\n"
    "f = outer()\n"
    "print(f.__code__.co_freevars, f.__code__.co_names, type(f)(f.__code__, {}, None, None, f.__closure__)())\n"
    "class M:\n"
    "    def __enter__(self): return 5\n"
    "    def __exit__(self, *a): return False\n"
    "def g():\n"
    "    with M() as m:\n"
    "        yield m\n"
    "it = g()\n"
    "next(it)\n"
    "try: raise ValueError('v')\n"
    "except ValueError as e: tb = e.__traceback__\n"
    "try: it.throw(ValueError, ValueError('w'), tb)\n"
    "except ValueError as e: print(e)\n"
    "class L(list): pass\n"
    "print(L([1]))\n"
    "lazy from _spy import _tracked\n"
    "print(_tracked([]))\n"
    "from _spy import _setting\n"
    "_setting('coroutine_origin_tracking_depth', 2)\n"
    "async def co(): return 1\n"
    "c = co()\n"
    "print(c.cr_origin is not None)\n"
    "c.close()\n",
    /* iter() of an instance enters its Python __iter__ from C (callk);
     * co_names walks a comprehension's later clauses. */
    "class I:\n"
    "    def __iter__(self):\n"
    "        for i in range(1): pass\n"
    "        return iter([1])\n"
    "def f():\n"
    "    for i in range(1): pass\n"
    "    return next(iter(I()))\n"
    "print(f())\n"
    "def g(): return [x for x in a for y in x.b if y.c]\n"
    "print(g.__code__.co_names)\n",
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

/* Fail each allocation of source after the first `from`, up to the first
 * `upto` (0: all): once, then from there on. */
static size_t check(const char *source, const char *name, size_t from, size_t upto) {
    int status;
    fail = 0;
    size_t total = run(source, name, &status), failed[2] = {0, 0};
    if (upto && upto < total) total = upto;
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
    const char *library = NULL;
    if (argc > 2 && !strcmp(argv[1], "--native")) { library = argv[2]; argv += 2; argc -= 2; }
    /* The empty program covers creating and freeing a context; the others
     * fail only what they allocate after that. */
    size_t from = check("", "<empty>", 0, 0);
    native = library;
    if (native) check("import fib\nprint(fib.fib(30))\n", "<native>", from, 0);
    native = NULL;
    imported = "'''A module of source.'''\nvalue = [i * i for i in range(3)]\n";
    if (argc == 1) check("import imported\nfrom imported import value\nprint(imported.value is value)\n", "<import>", from, 0);
    imported = NULL;
    for (int i = 1; i < argc; i++) {
        char *source = read_file(argv[i]);
        check(source, argv[i], from, 0);
        free(source);
    }
    for (size_t i = 0; argc == 1 && i < sizeof programs / sizeof *programs; i++) {
        char name[32];
        snprintf(name, sizeof name, "<program %zu>", i + 1);
        check(programs[i], name, from, 0);
    }
    /* The intrinsics make 22,000 allocations when first used; the first are
     * the module they run in. */
    if (argc == 1) check("print(list[int])\n", "<intrinsics>", from, from + 400);
    return 0;
}
