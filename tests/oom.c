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
    "print(f())\n"
    "D.__set__ = lambda self, obj, value: None\n"
    "a = A()\n"
    "a.__dict__['d'] = 0\n"
    "def g(): return [a.d, getattr(a, 'd'), getattr(a, 'd', 1)]\n"
    "print(g())\n"
    "class N:\n"
    "    def __next__(self):\n"
    "        for i in range(1): pass\n"
    "        raise StopIteration\n"
    "def h(n): return [next(n, 1), [next(N(), 2), list(map(next, [iter([3])]))]]\n"
    "print(h(N()))\n"
    "class M(N):\n"
    "    def __init__(self): self.n = 2\n"
    "    def __iter__(self): return self\n"
    "    def __next__(self):\n"
    "        for i in range(1): pass\n"
    "        if not self.n: raise StopIteration\n"
    "        self.n -= 1\n"
    "        return self.n\n"
    "def k(): return [list(enumerate(M())), [list(zip(M(), [1, 2])), [list(map(abs, M())), next(enumerate(M()), 0)]]]\n"
    "print(k())\n"
    "class W:\n"
    "    def __iter__(self):\n"
    "        for i in range(1): pass\n"
    "        return iter([1, 2])\n"
    "def w(): return [list(zip(W(), [3], W())), [list(map(abs, W())), [list(enumerate(W(), 1)), list(filter(None, W()))]]]\n"
    "print(w())\n"
    "class RV:\n"
    "    def keys(self): return [0, 1]\n"
    "    def __len__(self):\n"
    "        for i in range(1): pass\n"
    "        return 2\n"
    "    def __getitem__(self, i):\n"
    "        if i > 1: raise IndexError\n"
    "        return [i]\n"
    "def rv(): return [list(reversed(RV())), [next(reversed(RV())), sorted(iter(RV())), [next(iter(RV())), next(map(len, [RV()]))], [*iter(RV()), *map(len, [RV()])], [{**RV()}]]]\n"
    "print(rv())\n"
    "class Q:\n"
    "    def __init__(self, v): self.v = v\n"
    "    def __hash__(self): return 1\n"
    "    def __eq__(self, o):\n"
    "        for i in range(1): pass\n"
    "        return self.v == o.v\n"
    "def q(): return [{Q(1): Q(2), Q(3): 4} == {Q(3): 4, Q(1): Q(2)}, {Q(1): (Q(2),)} != {Q(1): (Q(3),)}]\n"
    "print(q())\n"
    "class GA:\n"
    "    def __getattribute__(self, n):\n"
    "        for i in range(1): pass\n"
    "        if n == 'x': raise AttributeError(n)\n"
    "        return object.__getattribute__(self, n)\n"
    "    def __getattr__(self, n):\n"
    "        for i in range(1): pass\n"
    "        return n\n"
    "def ga(o): return [o.x, o.__class__.__name__, o.x.upper()]\n"
    "print(ga(GA()))\n"
    "class CD:\n"
    "    def __get__(self, o, t):\n"
    "        for i in range(1): pass\n"
    "        return [t]\n"
    "class CM(type):\n"
    "    p = property(lambda cls: [cls])\n"
    "class CC(metaclass=CM):\n"
    "    d = CD()\n"
    "def cc(): return [CC.d, [CC.p, getattr(CC, 'd'), hasattr(CC, 'p')]]\n"
    "print(cc())\n",

    "class RE(Exception):\n"
    "    def __init__(self):\n"
    "        for i in range(1): pass\n"
    "        self.x = [i]\n"
    "class RC(Exception):\n"
    "    def __init__(self): self.y = [1]\n"
    "def re():\n"
    "    try: raise RE from RC\n"
    "    except RE as e: return [e.x, e.__cause__.y]\n"
    "print(re())\n",

    "def tg():\n"
    "    try: yield 0\n"
    "    except RE as e: yield e.x\n"
    "g = tg(); next(g)\n"
    "h = tg(); next(h)\n"
    "print(g.throw(RE), h.throw(RE, None))\n",

    "class TL(list):\n"
    "    def __bool__(self):\n"
    "        for i in range(1): pass\n"
    "        return False\n"
    "class TM(type):\n"
    "    def __len__(cls): return 0\n"
    "class TC(metaclass=TM): pass\n"
    "def tt(): return [not TL([1]), bool(TC), TL() or [TC and 1]]\n"
    "print(tt())\n",

    "class OW(int):\n"
    "    def __add__(self, o):\n"
    "        for i in range(1): pass\n"
    "        return [o]\n"
    "    def __radd__(self, o): return NotImplemented\n"
    "class OS(type):\n"
    "    def __lt__(cls, o): return [cls]\n"
    "    def __contains__(cls, x): return x\n"
    "class OT(metaclass=OS): pass\n"
    "def ow(): return [OW(1) + 2, 3 + OW(1), OT < OT, OT > OT, 4 in OT, OT | None, -OW(2)]\n"
    "print(ow())\n",

    "class RS(str):\n"
    "    def __repr__(self):\n"
    "        for i in range(1): pass\n"
    "        return 'RS' + str(i)\n"
    "class RM(type):\n"
    "    def __repr__(cls): return 'RM'\n"
    "class RT(metaclass=RM): pass\n"
    "print([repr([RS('a'), RT]), str({RS('b'): (RT,)})])\n",

    "class IJ(type):\n"
    "    def __instancecheck__(cls, x):\n"
    "        for i in range(1): pass\n"
    "        return [cls.__name__ == 'IB']\n"
    "class IA(metaclass=IJ): pass\n"
    "class IB(metaclass=IJ): pass\n"
    "def ij(): return [isinstance(1, (IA, IB)), isinstance(1, (IA, str)), issubclass(int, (IA, int))]\n"
    "print(ij())\n",

    "class SX:\n"
    "    def __init__(self, v): self.v = v\n"
    "    def __index__(self):\n"
    "        for i in range(1): pass\n"
    "        return self.v\n"
    "def sx(): return [[1, 2, 3, 4][SX(1):SX(3)], 'abcd'[SX(0)::SX(2)], range(9)[SX(2):]]\n"
    "print(sx())\n",

    "class LX:\n"
    "    def __init__(self, v): self.v = v\n"
    "    def __index__(self):\n"
    "        for i in range(1): pass\n"
    "        return self.v\n"
    "def lx():\n"
    "    s = [1, 2, 3]\n"
    "    s[LX(0)] = 7\n"
    "    del s[LX(1)]\n"
    "    s[LX(1)] += 1\n"
    "    s *= LX(2)\n"
    "    s.insert(LX(0), s.pop(LX(1)))\n"
    "    return [s, (0,) * LX(2), LX(1) * 'ab', hex(LX(255)), oct(LX(8)), bin(LX(3)), chr(LX(65)), range(LX(1), LX(5), LX(2)), bytes(LX(2)), bytearray(LX(1))]\n"
    "print(lx())\n",

    "class SK:\n"
    "    def __init__(self, v): self.v = v\n"
    "    def __hash__(self): return 0\n"
    "    def __eq__(self, o):\n"
    "        for i in range(1): pass\n"
    "        return self.v == o.v\n"
    "def sk():\n"
    "    s = {SK(1), SK(2)}\n"
    "    t = set(s)\n"
    "    t.intersection_update([SK(2)])\n"
    "    s.difference_update(SK(v) for v in (1, 3))\n"
    "    return [len(s.union([SK(4)])), len(s.intersection([SK(2), SK(5)])), s.isdisjoint([SK(2)]), s.issuperset([SK(9)]), len(t)]\n"
    "print(sk())\n",

    "class AB:\n"
    "    def __init__(self, b): self.b = b\n"
    "    @property\n"
    "    def __bases__(self):\n"
    "        for i in range(1): pass\n"
    "        return self.b\n"
    "class AI:\n"
    "    def __init__(self, k): self.k = k\n"
    "    @property\n"
    "    def __class__(self):\n"
    "        for i in range(1): pass\n"
    "        return self.k\n"
    "def ab():\n"
    "    a = AB(()); d = AB((AB(()), AB((a,))))\n"
    "    return [issubclass(d, a), issubclass(d, (AB(()), a)), isinstance(AI(d), a), isinstance(AI(d), int), issubclass(*(d, a))]\n"
    "print(ab())\n",

    "class SW:\n"
    "    def __init__(self, v): self.v = v\n"
    "    def __hash__(self): return 1\n"
    "    def __eq__(self, o):\n"
    "        for i in range(1): pass\n"
    "        return self.v == o.v\n"
    "def sw(n):\n"
    "    return {SW(v) for v in range(n)}\n"
    "def walks():\n"
    "    for i in range(1): pass\n"
    "    a = sw(3); b = sw(4); c = sw(9)\n"
    "    d = set(a); d -= b; e = set(a); e ^= b; f = set(a); f &= b\n"
    "    return [len(a | b), len(a & b), len(a - b), len(a ^ b), len(c - a), a <= b, a.isdisjoint(b), len(d), len(e), len(f)]\n"
    "def plain(a, b): return [len(a & b), len(a - b), len(a ^ b), len(a.symmetric_difference(b)), len(a.difference(b))]\n"
    "print(walks(), plain(sw(3), sw(4)), plain(sw(9), sw(1)))\n",

    "class SD:\n"
    "    def __hash__(self): return 1\n"
    "    def __eq__(self, o):\n"
    "        for i in range(1): pass\n"
    "        return False\n"
    "def sd():\n"
    "    a = {SD(), SD()}; b = {SD()}\n"
    "    return [len(a.__or__(b)), len(b.__rsub__(a)), a.__eq__(b), set.__ge__(a, b), a.__ixor__(b) is a, len(a)]\n"
    "print(sd())\n",

    "def st():\n"
    "    a = {SD(), SD()}\n"
    "    b = a.symmetric_difference([SD()])\n"
    "    a.symmetric_difference_update((SD(), SD()))\n"
    "    return [len(a), len(b), a.issubset([SD()]), b.issubset(x for x in b)]\n"
    "print(st())\n",

    "class SS(set): pass\n"
    "def ss():\n"
    "    a = SS([SD(), SD()]); b = {SD()}\n"
    "    c = a | b; a ^= b; d = b == SS([SD()])\n"
    "    return [len(c), len(a), d, b.isdisjoint(a), [1] == type('L', (list,), {})([1])]\n"
    "print(ss())\n",

    "def ch():\n"
    "    a = {SD(), SD()}; b = {SD()}; d = {SD() for i in range(20)}\n"
    "    r = [len(a.union(b, {SD()})), len(a.intersection(b, a | b)), len(frozenset(a).difference(b, {SD()}))]\n"
    "    a.update(b, {SD()}); a.intersection_update(a | b, {*a}); a.difference_update(b, {SD()}); a -= d\n"
    "    return r + [len(a)]\n"
    "print(ch())\n",

    "class BS(set): pass\nclass BD(dict): pass\nclass BT(tuple): pass\n"
    "def bs():\n"
    "    g = lambda n: (SD() for i in range(n))\n"
    "    d = {SD(): 1, SD(): 2}\n"
    "    return [len(BS(g(3))), len(BD((k, 0) for k in g(2))), len(BT(g(2))), len(BD(d)), len(dict(d)), len({**d})]\n"
    "print(bs())\n",

    "class MI:\n"
    "    def __init__(self, *v):\n"
    "        for i in range(1): pass\n"
    "        self.v = v\n"
    "class MB:\n"
    "    def __init__(self, v):\n"
    "        for i in range(1): pass\n"
    "        return v\n"
    "def mc():\n"
    "    r = [p.v for p in map(MI, [1, 2], 'ab')] + [len(list(map(MI, (3,))))]\n"
    "    try: list(map(MB, [None, 1]))\n"
    "    except TypeError as e: r.append(str(e))\n"
    "    return r\n"
    "print(mc())\n",

    "def kd():\n"
    "    a = {SD(), SD()}; d = {SD(): 0, SD(): 1}; f = frozendict(d)\n"
    "    r = [len(a.union(d)), len(a.difference(f)), len(a.intersection(d)), a.isdisjoint(d)]\n"
    "    a.update(f); a.symmetric_difference_update(d); a.difference_update(d)\n"
    "    return r + [len(a)]\n"
    "print(kd())\n",

    "def ms():\n"
    "    x = (SD(), [SD()])\n"
    "    return [x in [(SD(), [SD()]), (1, 2), x], (SD(),) in [(SD(),)], {1: SD()} in [{1: SD()}]]\n"
    "print(ms())\n",

    "class TB:\n"
    "    def __bool__(self): return False\n"
    "    def __str__(self): return 'tb'\n"
    "    def __format__(self, f): return 'f' + f\n"
    "a = [TB(), TB()]\n"
    "print(any(*[a]), all(*(a,)), str(*a[:1]), repr(*[1]), format(*[TB(), 'x']))\n",

    "class TN:\n"
    "    def __set_name__(self, owner, name): owner.n = name\n"
    "class TH:\n"
    "    def __init_subclass__(cls, **kw): cls.kw = kw\n"
    "class TM(type):\n"
    "    def __new__(mcls, name, bases, ns, **kw): return super().__new__(mcls, name, bases, ns, **kw)\n"
    "A = type('A', (TH,), {'x': TN()}, k=1)\n"
    "B = TM('B', (TH,), {'y': TN()}, j=2)\n"
    "print(A.n, A.kw, B.n, B.kw, type.__new__(TM, 'C', (), {'z': TN()}).n)\n",

    "class SP(property): pass\n"
    "class SG:\n"
    "    @SP\n"
    "    def v(self): return 'v'\n"
    "    @SP\n"
    "    def w(self): raise AttributeError('w')\n"
    "    def __getattr__(self, name): return name * 2\n"
    "print(SG().v, SG().w, getattr(SG(), 'v'), super(SP, SG.__dict__['v']).__get__(SG()))\n",

    "def ci():\n"
    "    n = [0]\n"
    "    def f():\n"
    "        n[0] += 1\n"
    "        if n[0] == 9: raise StopIteration\n"
    "        return n[0]\n"
    "    it = iter(f, 4)\n"
    "    r = [x for x in it] + list(it)\n"
    "    n[0] = 0\n"
    "    for x in iter(f, 3): r.append(x)\n"
    "    n[0] = 4\n"
    "    return r + [sum(iter(f, 0)), next(iter(f, 0), 'd')]\n"
    "print(ci())\n",

    "class MI:\n"
    "    def __init__(self, v): self.v = v\n"
    "    def __index__(self):\n"
    "        for _ in (): pass\n"
    "        return self.v\n"
    "def mi():\n"
    "    for _ in (): pass\n"
    "    m = memoryview(bytearray(range(6))).cast('B', (2, 3))\n"
    "    m[MI(1), MI(2)] = 9\n"
    "    m[0, MI(1)] += 5\n"
    "    try: m[MI(4), MI(0)]\n"
    "    except IndexError as e: r = str(e)\n"
    "    return m[MI(1), 2], m.tolist(), r\n"
    "print(mi())\n",

    "class FK:\n"
    "    def __hash__(self): return 1\n"
    "    def __repr__(self):\n"
    "        for _ in (): pass\n"
    "        return 'c\\xe9' + '{}'.format(fl)\n"
    "fl = []\n"
    "def fc():\n"
    "    for _ in (): pass\n"
    "    fl.append(FK())\n"
    "    return '{0}|{1!r:>9}|{0!a}|{k}'.format([FK()], (FK(), 1), k={FK()}), '{x}'.format_map({'x': fl})\n"
    "print(fc())\n",

    "class FN:\n"
    "    def __repr__(self):\n"
    "        for _ in (): pass\n"
    "        return 'f\\xe9'\n"
    "    def __format__(self, spec): return '3'\n"
    "def fn():\n"
    "    for _ in (): pass\n"
    "    return '{0!r:{1}}|{0!a:>{1}}|{k!s:{k}}'.format(FN(), FN(), k=FN())\n"
    "print(fn())\n",

    "class BQ:\n"
    "    def __index__(self): return 66\n"
    "    def __int__(self): return 7\n"
    "    def __float__(self): return 0.5\n"
    "    def __repr__(self): return 'q\\xe9'\n"
    "    def __bytes__(self): return b'qb'\n"
    "class BO(bytes):\n"
    "    def __bytes__(self): return b'no'\n"
    "class BI:\n"
    "    def __index__(self): return 'x'\n"
    "def bq():\n"
    "    for _ in (): pass\n"
    "    try: '%c' % BI()\n"
    "    except TypeError as e: r = str(e)\n"
    "    return b'%d %x %c %.1f %r %a %s %b' % (BQ(), BQ(), BQ(), BQ(), BQ(), BQ(), BQ(), BO(b'o')), b'%(k)c' % {b'k': BQ()}, r\n"
    "print(bq())\n",

    "class BY:\n"
    "    def __init__(self, t): self.t = t\n"
    "    def __index__(self):\n"
    "        try: self.t.append(0)\n"
    "        except BufferError: return 67\n"
    "        return 68\n"
    "    def __bytes__(self): return b'yb'\n"
    "    def __repr__(self): return 'y'\n"
    "def by():\n"
    "    for _ in (): pass\n"
    "    b = bytearray(b'%c %x %s %r')\n"
    "    t = b % (BY(b), BY(b), BY(b), BY(b))\n"
    "    b.append(1)\n"
    "    return t, b\n"
    "print(by())\n",

    "class FV:\n"
    "    def __repr__(self): return 'c\\xe9'\n"
    "def fv():\n"
    "    for _ in (): pass\n"
    "    l = [FV()]; l.append(l)\n"
    "    return '{!r:>{}}|{:{}}|{k!a:^{w}}'.format(l, 12, (FV(),), '', k={FV()}, w=9)\n"
    "print(fv())\n",

    "class RX(type):\n"
    "    def __call__(cls, *a):\n"
    "        if cls.__name__ == 'RS' and not a: return KeyError('k')\n"
    "        return super().__call__(*a)\n"
    "class RE(Exception, metaclass=RX): pass\n"
    "class RS(Exception, metaclass=RX): pass\n"
    "def rx():\n"
    "    for _ in (): pass\n"
    "    out = []\n"
    "    for f in (lambda: RE, lambda: RS):\n"
    "        try: raise f() from RE\n"
    "        except Exception as e: out.append((type(e).__name__, type(e.__cause__).__name__))\n"
    "    return out\n"
    "print(rx())\n",

    "class BN(dict):\n"
    "    def __setitem__(self, k, v): super().__setitem__(k, v)\n"
    "    def __delitem__(self, k):\n"
    "        if k == 'q': raise KeyError(k)\n"
    "        super().__delitem__(k)\n"
    "class BM(type):\n"
    "    @classmethod\n"
    "    def __prepare__(m, n, b): return BN()\n"
    "class BK(metaclass=BM):\n"
    "    def f(self): return 1\n"
    "    class I: pass\n"
    "    a: int = 2\n"
    "    del a\n"
    "    try:\n"
    "        del q\n"
    "    except NameError as e: r = str(e)\n"
    "print(BK().f(), BK.I.__name__, BK.r, 'a' in BK.__dict__)\n",

    "class RO(Exception): pass\n"
    "class RA(Exception):\n"
    "    def __new__(cls, *a): return super().__new__(cls, *a) if a else RO('o')\n"
    "    def __init__(self, *a): self.a = len(a)\n"
    "class RB(RA):\n"
    "    def __init__(self, *a): raise KeyError('b')\n"
    "def rr(k, *c):\n"
    "    try:\n"
    "        if c: raise k from c[0]\n"
    "        raise k\n"
    "    except BaseException as e: return type(e).__name__, getattr(e, '__notes__', None)\n"
    "print(rr(RA), rr(RB), rr(RA, KeyError))\n",

    "class DK:\n"
    "    def __iter__(self): return iter([(1, 2), (3, 4)])\n"
    "class DM:\n"
    "    def keys(self): return ['m']\n"
    "    def __getitem__(self, k): return k\n"
    "class DS(dict): pass\n"
    "d = {}; d.update(DK(), a=1, **{'b': 2})\n"
    "print(dict(DK(), z=0), dict(DM(), m=1), DS(DK(), q=3), d)\n",

    "class PS:\n"
    "    def __str__(self): return 'ps'\n"
    "class PF:\n"
    "    def __init__(self): self.out = []\n"
    "    def write(self, s): self.out.append(s)\n"
    "f = PF()\n"
    "print(*[PS(), 1, PS()], sep='|', file=f)\n"
    "print(*(PS(),), end='', file=f)\n"
    "print(*f.out)\n",

    "class PG(property):\n"
    "    def __get__(self, obj, owner=None): return [super().__get__(obj, owner)]\n"
    "class PH:\n"
    "    @PG\n"
    "    def v(self): return 'v'\n"
    "print(PH().v, property.__get__(PH.__dict__['v'], PH(), PH), PH.__dict__['v'].__get__(None, PH) is PH.__dict__['v'])\n",

    "class TE(Exception):\n"
    "    def __init__(self, *a): super().__init__(*a)\n"
    "def tg():\n"
    "    try:\n"
    "        yield 0\n"
    "    except TE as e:\n"
    "        yield e.args\n"
    "g = tg(); next(g)\n"
    "h = tg(); next(h)\n"
    "print(g.throw(TE, (1, 2), None), h.throw(TE, TE(3), None))\n",

    "class PN:\n"
    "    def __init__(self, v): self.v = v\n"
    "    def __index__(self): return self.v\n"
    "    def __float__(self): return 0.5\n"
    "def pn():\n"
    "    r = ['%d|%x|%5.1f|%s' % (PN(3), PN(30), PN(1), 's')]\n"
    "    r.append('%(k)o' % {'k': PN(8)})\n"
    "    try: '%x' % PN('no')\n"
    "    except TypeError as e: r.append(e)\n"
    "    return r\n"
    "print(pn())\n",

    "class FC:\n"
    "    def __repr__(self): return '\\xe9'\n"
    "    def __str__(self): return 3\n"
    "def fc():\n"
    "    r = ['{0!r}|{0!a:>4}|{x!r:.1}'.format(FC(), x=FC())]\n"
    "    try: '{!s}'.format(FC())\n"
    "    except TypeError as e: r.append(e)\n"
    "    return r\n"
    "print(fc())\n",

    "class AR:\n"
    "    def __repr__(self): return '\\xe9'\n"
    "    def __index__(self): return 1\n"
    "class AB:\n"
    "    def __repr__(self): return 1\n"
    "    def __index__(self): return 'i'\n"
    "def ar():\n"
    "    r = [ascii(AR()), round(2.25, AR()), round(15, AR())]\n"
    "    for f in (lambda: ascii(AB()), lambda: round(1.5, AB())):\n"
    "        try: f()\n"
    "        except TypeError as e: r.append(e)\n"
    "    return r\n"
    "print(ar())\n",

    "class MV:\n"
    "    def __init__(self, n): self.n = n\n"
    "    def __index__(self): return self.n\n"
    "def mv():\n"
    "    b = bytearray(b'abc'); m = memoryview(b); g = m.cast('B', (1, 3))\n"
    "    m[MV(0)] = 65; b[MV(1)] = 66\n"
    "    r = [m[MV(2)], bytes(b), m[MV(0):MV(2)].tobytes()]\n"
    "    for f in (lambda: g[MV(0)], lambda: m[MV(10 ** 30)], lambda: m[MV('x')]):\n"
    "        try: f()\n"
    "        except (NotImplementedError, IndexError, TypeError) as e: r.append(e)\n"
    "    return r\n"
    "print(mv())\n",

    "class RN(Exception):\n"
    "    def __new__(cls): return super().__new__(cls)\n"
    "    def __init__(self): super().__init__('rn')\n"
    "class RI(Exception):\n"
    "    def __new__(cls): return 1\n"
    "def rn():\n"
    "    r = []\n"
    "    for f in (lambda: RN, lambda: RI):\n"
    "        try: raise ValueError from f()\n"
    "        except Exception as e: r.append((e, e.__cause__))\n"
    "        try: raise f()\n"
    "        except Exception as e: r.append(e)\n"
    "    return r\n"
    "print(rn())\n",

    "class NZ(Exception):\n"
    "    def __new__(cls, *a): return super().__new__(cls, *a) if a else KeyError('k')\n"
    "class NY(Exception):\n"
    "    def __new__(cls, *a): return 3 if a else KeyError('y')\n"
    "def nz():\n"
    "    r = []\n"
    "    for k in (NZ, NY):\n"
    "        try: raise k from ValueError\n"
    "        except Exception as e: r.append((e, e.__cause__, getattr(e, '__notes__', None)))\n"
    "    return r\n"
    "print(nz())\n",

    "class NN(dict):\n"
    "    def __setitem__(self, k, v):\n"
    "        if k == self.get('fail'): raise KeyError(k)\n"
    "        super().__setitem__(k, v)\n"
    "    def __getitem__(self, k): return 'n' if k == '__name__' else super().__getitem__(k)\n"
    "class NM(type):\n"
    "    @classmethod\n"
    "    def __prepare__(m, n, b, **kw):\n"
    "        ns = NN(); dict.update(ns, kw); return ns\n"
    "    def __new__(m, n, b, ns, **kw): return super().__new__(m, n, b, dict(ns))\n"
    "class NC(metaclass=NM):\n"
    "    'd'\n"
    "    def f(self): self.a = __class__\n"
    "r = [NC.__module__, NC.__doc__, NC.__static_attributes__]\n"
    "for k in ('__qualname__', '__classcell__'):\n"
    "    try:\n"
    "        class NF(metaclass=NM, fail=k):\n"
    "            def f(self): return __class__\n"
    "    except KeyError as e: r.append(e)\n"
    "print(r)\n",

    "class AO(dict):\n"
    "    def __setitem__(self, k, v): super().__setitem__(k, v)\n"
    "class AM(type):\n"
    "    @classmethod\n"
    "    def __prepare__(m, n, b): return AO()\n"
    "class AC(metaclass=AM):\n"
    "    a = 1\n"
    "    if a: x: int = 2\n"
    "ns = {}\n"
    "try: exec('x: int = 1\\nraise KeyError\\ny: str = 2\\n', ns)\n"
    "except KeyError: pass\n"
    "print(AC.__annotations__, ns['__annotate__'](1), ns['__conditional_annotations__'])\n",

    "class TN(Exception):\n"
    "    def __new__(cls, *a):\n"
    "        return super().__new__(cls, *a) if a else KeyError('k')\n"
    "    def __init__(self, *a): self.a = a\n"
    "def tn():\n"
    "    r = []\n"
    "    try:\n"
    "        while True: r.append((yield))\n"
    "    except BaseException as e: r.append(e)\n"
    "    yield r\n"
    "for v in ((1, 2), None):\n"
    "    g = tn(); next(g)\n"
    "    print(g.throw(TN, v))\n",

    "class PW:\n"
    "    def __init__(self): self.parts = []\n"
    "    def write(self, t): self.parts.append(t)\n"
    "    def flush(self): self.parts.append(0)\n"
    "class PS(str):\n"
    "    def __str__(self): return '+'\n"
    "class PB:\n"
    "    def write(self, t): raise KeyError(t)\n"
    "def pw():\n"
    "    w = PW(); print(1, [2], sep=PS('-'), end='', file=w, flush=True)\n"
    "    try: print('x', file=PB())\n"
    "    except KeyError as e: w.parts.append(e)\n"
    "    return w.parts\n"
    "print(pw())\n",

    "class DP:\n"
    "    def __init__(self, items): self.items = items\n"
    "    def __iter__(self): return iter(self.items)\n"
    "def dp():\n"
    "    d = {0: 0}; d.update(DP([(1, 'a'), 'bc']))\n"
    "    r = [dict(DP([(2, 3), [4, 5]])), d]\n"
    "    for items in ([(1, 2, 3)], [7]):\n"
    "        try: dict(DP(items))\n"
    "        except (TypeError, ValueError) as e: r.append(e)\n"
    "    return r\n"
    "print(dp())\n",

    "class DX:\n"
    "    def __dir__(self): return iter(('q', 'p'))\n"
    "    def __index__(self): return True\n"
    "class DY:\n"
    "    def __dir__(self): return 3\n"
    "    def __index__(self): return 'i'\n"
    "def dx():\n"
    "    r = [dir(DX()), int(DX()), float(DX())]\n"
    "    for f in (dir, int, float):\n"
    "        try: f(DY())\n"
    "        except TypeError as e: r.append(e)\n"
    "    return r\n"
    "print(dx())\n",

    "class CI:\n"
    "    def __init__(self, n): self.n = n\n"
    "    def __iter__(self): return iter(range(self.n)) if self.n else 5\n"
    "def ci2():\n"
    "    r = [[x for x in CI(3)], {x: x for x in CI(2)}, list(x * y for x in CI(2) for y in CI(3))]\n"
    "    try: [x for x in CI(0)]\n"
    "    except TypeError as e: r.append(e)\n"
    "    return r\n"
    "print(ci2())\n",

    "def zc():\n"
    "    n = [0]\n"
    "    def f():\n"
    "        n[0] += 1\n"
    "        if n[0] == 7: raise StopIteration\n"
    "        return n[0]\n"
    "    r = list(zip('abc', iter(f, 3))) + list(enumerate(iter(f, 6)))\n"
    "    n[0] = 4\n"
    "    return r + [z for z in zip(iter(f, 0), [1, 2, 3], 'xy')]\n"
    "print(zc())\n",

    "class MG:\n"
    "    @property\n"
    "    def f(self): return lambda *a: [a]\n"
    "    def __getattr__(self, name): return MI if name == 'i' else lambda *a: (name, a)\n"
    "class MI(list):\n"
    "    def __init__(self, *a): super().__init__(a)\n"
    "class MH:\n"
    "    def __getattribute__(self, name):\n"
    "        if name == 'no': raise AttributeError(name)\n"
    "        return lambda *a: [name, a]\n"
    "def mg():\n"
    "    g = MG(); k = 'k'\n"
    "    try: MH().no(1)\n"
    "    except AttributeError as e: k = e.args\n"
    "    return g.f(1, k), g.h(k, [2]), MH().x(k), g.f(*[3]), g.i(k, 4)\n"
    "print(mg())\n",

    "class AX:\n"
    "    def __iadd__(self, o): return NotImplemented\n"
    "    def __add__(self, o):\n"
    "        for i in range(1): pass\n"
    "        return NotImplemented\n"
    "class RX:\n"
    "    def __radd__(self, o):\n"
    "        for i in range(1): pass\n"
    "        return [o]\n"
    "def ax():\n"
    "    x = AX()\n"
    "    x += RX()\n"
    "    try:\n"
    "        y = AX()\n"
    "        y += 1\n"
    "    except TypeError as e: x.append(str(e))\n"
    "    return len(x)\n"
    "print(ax())\n",

    "class FN:\n"
    "    def __new__(cls, *a, **k):\n"
    "        for i in range(1): pass\n"
    "        return super().__new__(cls)\n"
    "    def __init__(self, *a, **k): self.v = [a, k]\n"
    "def fn(): return [FN(*[1], **{'x': [2]}).v, FN(**{}).v]\n"
    "print(fn())\n",

    "class OI(int):\n"
    "    def __repr__(self):\n"
    "        for i in range(1): pass\n"
    "        return 'o' * self\n"
    "class OM(type):\n"
    "    def __len__(cls): return 2\n"
    "class OC(metaclass=OM): pass\n"
    "def oi(): return [repr(OI(2)), len(OC), str(OI(1))]\n"
    "print(oi())\n",

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
    "def keyed(s): return [repr({1: s}), [str({s}), ['%s' % ({s: [s]},), [frozenset([s]), [frozendict({2: (s,)})]]]]][1:]\n"
    "print(keyed(S()))\n"
    "class Keyed:\n    def __init__(self, k): self.k = k\n    def keys(self): return self.k\n    def __getitem__(self, k): return 1\n"
    "def pairs(s): d = {}; return [dict([(s, 1)]), [d.update(zip([s], [2])), [set(zip([1], [s])), [dict(x for x in [[s, 3]]), [dict(Keyed([s]))]]]]][1:]\n"
    "print(pairs(S()))\n"
    "def adapted(s): return [list(zip(map(str, [s]), 'a')), [list(enumerate(map(str, [s]))), [[x for x in zip([1], map(str, [s]))]]]][1:]\n"
    "print(adapted(S()))\n"
    "S.__lt__ = lambda a, b: [i for i in range(1)][0] == 1\n"
    "def ranked(s): return [sorted({s, S()}), [sorted({s: 1, S(): 2}.keys()), [sorted(iter([s, S()]))]]][1:]\n"
    "print(ranked(S()))\n"
    "def sought(s): l = [1, s]; return [l.index(S()), [l.count(S()), [(s,).index(S()), [l.remove(S())]]]][1:]\n"
    "print(sought(S()))\n"
    "class U(S): pass\n"
    "def under(s): return [s < U(), [S() < U(), [U() > s]]][1:]\n"
    "print(under(S()))\n"
    "def matched(s): return [{1: s} == {1: S()}, [{1: S(), 2: s} != {1: S(), 2: S()}, [{'k': [s]} == {'k': [S()]}]]][1:]\n"
    "def inside(s): return [[{1: s}] == [{1: S()}], [({2: [s]},) != ({2: [S()]},), [[{1: {2: s}}] < [{1: {2: S()}}, 1]]]][1:]\n"
    "print(inside(S()))\n"
    "print(matched(S()))\n",

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
    "async def ag():\n"
    "    for i in range(2): yield [i]\n"
    "async def run():\n"
    "    g = ag()\n"
    "    return [await g.asend(None), [x async for x in ag()], await anext(g)]\n"
    "try:\n"
    "    run().send(None)\n"
    "except StopIteration as e:\n"
    "    print(e.value)\n"
    "async def held():\n"
    "    try: yield [1]\n"
    "    finally: print([2])\n"
    "h = held()\n"
    "try:\n"
    "    h.__anext__().send(None)\n"
    "except StopIteration as e:\n"
    "    print(e.value)\n"
    "del h\n"
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
