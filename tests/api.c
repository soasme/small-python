#include "../spy.h"
#include "../spy-std.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { char text[4096]; size_t len; int flushes, fail_flush; } Output;
static int output(void *data, const char *s, size_t n) {
    Output *o = data;
    if (n >= sizeof(o->text) - o->len) return -1;
    memcpy(o->text + o->len, s, n); o->len += n; o->text[o->len] = 0;
    return 0;
}
static int flush_output(void *data) {
    Output *o = data;
    o->flushes++;
    return o->fail_flush;
}
static SPYValue *twice(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)data;
    int64_t n;
    if (argc != 1) return spy_error(c, "TypeError", "twice expects one argument");
    if (spy_as_int(c, argv[0], &n)) return NULL;
    if (n > INT64_MAX / 2 || n < INT64_MIN / 2) return spy_error(c, "OverflowError", "twice overflow");
    return spy_int(c, n * 2);
}
/* An interrupt that stops the context on its tenth poll. */
static int count_polls(void *data) { return ++*(int *)data == 10; }
/* A host function that calls its argument back into the engine. */
static SPYValue *call_back(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)data;
    if (argc != 1) return spy_error(c, "TypeError", "call_back expects one argument");
    return spy_call(c, argv[0], 0, NULL);
}
static char *loader(void *data, const char *name) {
    int *calls = data;
    (*calls)++;
    if (strcmp(name, "sample")) return NULL;
    const char *source = "answer = 42\ndef add(x):\n    return x + answer\n";
    char *copy = malloc(strlen(source) + 1);
    if (copy) strcpy(copy, source);
    return copy;
}
/* Lines for input(), from a NULL-terminated list. */
static char *read_line(void *data) {
    const char ***lines = data;
    if (!**lines) return NULL;
    char *copy = malloc(strlen(**lines) + 1);
    if (copy) strcpy(copy, *(*lines)++);
    return copy;
}
static int64_t integer(SPYContext *c, SPYValue *v) {
    int64_t n;
    assert(v && !spy_as_int(c, v, &n));
    spy_release(v);
    return n;
}
static void execute(SPYContext *c, const char *source) {
    if (spy_exec(c, source, "api.py")) {
        fprintf(stderr, "api.py:%zu: %s: %s\n", spy_error_line(c), spy_error_type(c), spy_error_message(c));
        abort();
    }
}
/* Mappings can close cycles through class bodies, closures, and exec locals. */
static void namespace_cycles(void) {
    SPYContext *c = spy_context_new();
    assert(c);
    int host = 0;
    assert(!spy_get_opaque(c));
    spy_set_opaque(c, &host);
    assert(spy_get_opaque(c) == &host);
    execute(c,
        "def make():\n"
        "    class Namespace:\n"
        "        def __init__(self): self.data = {}\n"
        "        def __getitem__(self, key): return self.data[key]\n"
        "        def __setitem__(self, key, value): self.data[key] = value\n"
        "        def keys(self): return self.data.keys()\n"
        "    ns = Namespace()\n"
        "    def meta(name, bases, mapping): return type(name, bases, dict(mapping))\n"
        "    def prepare(name, bases): return ns\n"
        "    meta.__prepare__ = prepare\n"
        "    class C(metaclass=meta):\n"
        "        saved = locals()\n"
        "        def read(self): return __class__\n"
        "    assert C().read() is C\n"
        "    ns.data['C'] = C\n"
        "    exec('saved = locals()', {}, ns)\n"
        "    class Meta(type):\n"
        "        def mro(cls): return [cls, object]\n"
        "    class D(metaclass=Meta): pass\n"
        "    D.cycle = D\n"
        "    D.proxy = D.__dict__\n"
        "    values = {}\n"
        "    values['proxy'] = values.keys().mapping\n"
        "    frozen = frozendict(values=values)\n"
        "    values['frozen'] = frozen\n"
        "    values['view'] = frozen.items()\n"
        "    values['iterator'] = iter(frozen)\n");
    execute(c, "make()\n"); /* Initialize lazy builtin descriptors before measuring. */
    spy_collect(c);
    size_t baseline = spy_live_values(c);
    for (int i = 0; i < 50; i++) {
        execute(c, "make()\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
    }
    execute(c, "proxy = {}.keys().mapping\nfor i in range(100000): proxy = type(proxy)(proxy)\n");
    assert(!spy_eval(c, "repr(proxy)", "proxy.py"));
    assert(!strcmp(spy_error_type(c), "RecursionError"));
    spy_clear_error(c);
    assert(!spy_eval(c, "proxy[0]", "proxy.py"));
    assert(!strcmp(spy_error_type(c), "RecursionError"));
    spy_clear_error(c);
    execute(c, "del proxy\n");
    spy_context_free(c);
}
static int released;
static void release_counter(void *data) { released += *(int *)data; }
/* Sums positional arguments and adds the "scale" keyword's value. */
static SPYValue *keyword_sum(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *data) {
    (void)data;
    int64_t total = 0, n;
    for (size_t i = 0; i < argc; i++) {
        if (spy_as_int(c, argv[i], &n)) return NULL;
        total += n;
    }
    if (keywords) {
        SPYValue *key = spy_string(c, "scale", 5), *scale = key ? spy_get_item(c, keywords, key) : NULL;
        spy_release(key);
        if (!scale) return NULL;
        int failed = spy_as_int(c, scale, &n);
        spy_release(scale);
        if (failed) return NULL;
        total += n;
    }
    return spy_int(c, total);
}
static SPYValue *raise_value_error(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *data) {
    (void)argc; (void)argv; (void)keywords; (void)data;
    SPYValue *cls = spy_get_global(c, "ValueError"), *message = spy_string(c, "host failure", 12);
    SPYValue *error = cls && message ? spy_call(c, cls, 1, &message) : NULL;
    spy_release(cls); spy_release(message);
    if (error) spy_raise(c, error);
    spy_release(error);
    return NULL;
}
int main(void) {
    namespace_cycles();
    {
        SPYContext *source = spy_context_new();
        assert(source);
        execute(source, "# coding: latin-1\rtext = '\xc7'\r");
        execute(source, "assert text == '\u00c7'\n");
        execute(source, "\xef\xbb\xbf# coding: utf-8\r\nassert text == '\u00c7'\r\n");
        for (int i = 0; i < 20; i++) {
            assert(spy_exec(source, "# coding: missing\n", "source.py") == -1);
            assert(!strcmp(spy_error_type(source), "SyntaxError"));
            assert(!strcmp(spy_error_filename(source), "source.py"));
            spy_clear_error(source);
            assert(spy_exec(source, "\xef\xbb\xbf# coding: latin-1\n", "source.py") == -1);
            assert(strstr(spy_error_message(source), "BOM"));
            spy_clear_error(source);
        }
        execute(source, "del text\n");
        spy_collect(source);
        spy_context_free(source);
    }
    {
        SPYContext *templates = spy_context_new();
        assert(templates);
        execute(templates,
            "def make():\n"
            "    values = []\n"
            "    template = t'{values!r}'\n"
            "    values.append(template)\n"
            "    values.append(iter(template))\n"
            "    def suspended():\n"
            "        yield t'{values}{(yield 1)}'\n"
            "    generator = suspended()\n"
            "    next(generator)\n"
            "    values.append(generator)\n"
            "    class Name(str): pass\n"
            "    label = Name('cycle')\n"
            "    label.owner = generator\n"
            "    generator.__name__ = label\n"
            "    generator.__qualname__ = label\n");
        execute(templates, "make()\n");
        spy_collect(templates);
        size_t baseline = spy_live_values(templates);
        for (int i = 0; i < 50; i++) {
            execute(templates, "make()\n");
            spy_collect(templates);
            assert(spy_live_values(templates) == baseline);
        }
        spy_context_free(templates);
    }
    {
        /* The core has only builtins until a host registers modules. */
        SPYContext *bare = spy_context_new();
        assert(bare && spy_exec(bare, "import sys", "bare.py") && !strcmp(spy_error_type(bare), "ModuleNotFoundError"));
        assert(spy_exec(bare, "import _spy", "bare_spy.py") && !spy_exec(bare, "import builtins\nopen", "bare_core.py"));
        assert(!spy_std_init_module(bare, "sys") && !spy_exec(bare, "import sys\nassert sys.modules['sys'] is sys", "bare_sys.py"));
        assert(spy_exec(bare, "import gc", "bare_gc.py") && spy_std_init_module(bare, "nope"));
        spy_context_free(bare);
    }
    SPYContext *c = spy_context_new();
    assert(c && !spy_std_init(c));
    Output o = {0};
    spy_set_output(c, output, &o);
    execute(c, "print('hello', 6 * 7)");
    assert(!strcmp(o.text, "hello 42\n"));
    spy_set_flush(c, flush_output);
    execute(c, "print(end='', flush=True)");
    assert(o.flushes == 1);
    o.fail_flush = 1;
    assert(spy_exec(c, "print(flush=True)", "flush.py") == -1);
    assert(!strcmp(spy_error_type(c), "OSError"));
    o.fail_flush = 0;
    spy_clear_error(c);
    /* input() writes its prompt, flushes, and strips the line ending. */
    assert(spy_exec(c, "input()", "input.py") == -1 && !strcmp(spy_error_type(c), "EOFError"));
    const char *lines[] = {"first\n", "second", NULL}, **cursor = lines;
    spy_set_input(c, read_line, &cursor);
    o.len = 0; o.flushes = 0;
    execute(c, "assert input('> ') == 'first'\nassert input() == 'second'\n");
    assert(!strcmp(o.text, "> ") && o.flushes == 3);
    assert(spy_exec(c, "input()", "input.py") == -1 && !strcmp(spy_error_type(c), "EOFError"));
    spy_set_input(c, NULL, NULL);
    assert(!spy_define(c, "twice", twice, NULL));
    assert(integer(c, spy_eval(c, "twice(21)", "api.py")) == 42);
    execute(c, "x = 19");
    assert(integer(c, spy_get_global(c, "x")) == 19);
    assert(integer(c, spy_eval(c, "x + 23", "api.py")) == 42);

    /* Arbitrary integers stay owned Python values; the fixed-width C accessor
     * rejects overflow instead of truncating. Large limbs must be reclaimed. */
    size_t integer_baseline = spy_live_values(c);
    SPYValue *large = spy_eval(c, "2**256 + 17", "integer.py");
    assert(large && spy_type(large) == SPY_INT);
    int64_t narrowed = 42;
    assert(spy_as_int(c, large, &narrowed) == -1 && narrowed == 42);
    assert(!strcmp(spy_error_type(c), "OverflowError"));
    spy_clear_error(c);
    SPYValue *large_repr = spy_repr(c, large);
    size_t repr_len;
    assert(!strcmp(spy_as_string(c, large_repr, &repr_len),
        "115792089237316195423570985008687907853269984665640564039457584007913129639953"));
    spy_release(large_repr); spy_release(large);
    assert(spy_live_values(c) == integer_baseline);
    assert(integer(c, spy_eval(c, "(2**256 + 17) % 2**256", "integer.py")) == 17);
    const unsigned char binary_data[] = {0, 127, 128, 255};
    SPYValue *binary_value = spy_bytes(c, binary_data, sizeof(binary_data));
    size_t binary_len;
    const unsigned char *binary_pointer = spy_as_bytes(c, binary_value, &binary_len);
    assert(binary_pointer && binary_len == sizeof(binary_data));
    assert(!memcmp(binary_pointer, binary_data, binary_len));
    assert(!spy_as_string(c, binary_value, NULL));
    assert(!strcmp(spy_error_type(c), "TypeError"));
    spy_clear_error(c);
    assert(!spy_set_global(c, "binary_value", binary_value));
    spy_release(binary_value);
    execute(c, "assert binary_value == b'\\x00\\x7f\\x80\\xff'\ndel binary_value\n");

    /* Interactive display belongs to statements in this input, not to the
     * function/class code objects it defines. Earlier output survives errors. */
    o.len = 0;
    SPYValue *interactive = spy_eval_interactive(c,
        "1; 2\nfor x in (3, 4):\n    x\ndef f():\n    99\n    return 5\n"
        "class C:\n    88\nf()\nNone\n", "interactive.py");
    assert(interactive); spy_release(interactive);
    assert(!strcmp(o.text, "1\n2\n3\n4\n5\n"));
    assert(integer(c, spy_eval(c, "_", "last.py")) == 5);
    o.len = 0;
    assert(!spy_eval_interactive(c, "6; 1 / 0", "interactive.py"));
    assert(!strcmp(o.text, "6\n"));
    assert(!strcmp(spy_error_type(c), "ZeroDivisionError"));
    spy_clear_error(c);
    execute(c, "f = None\nC = None\n");

    /* Functions and closures outlive their original evaluation's syntax tree. */
    execute(c, "def outer(x):\n    def inner(y):\n        return x + y\n    return inner\nf = outer(40)\n");
    assert(integer(c, spy_eval(c, "f(2)", "later.py")) == 42);
    SPYValue *fn = spy_get_global(c, "f");
    SPYValue *arg = spy_int(c, 3);
    assert(integer(c, spy_call(c, fn, 1, &arg)) == 43);
    spy_release(arg); spy_release(fn);

    /* External references root cycles; dropping the last root makes them garbage. */
    spy_collect(c);
    size_t baseline = spy_live_values(c);
    SPYValue *cycle = spy_list(c);
    assert(cycle && !spy_list_append(c, cycle, cycle));
    assert(spy_collect(c) == 0);
    spy_release(cycle);
    assert(spy_collect(c) == 1);
    assert(spy_live_values(c) == baseline);

    /* Releasing a deep acyclic graph must not consume the native call stack. */
    SPYValue *deep = spy_list(c);
    for (size_t i = 0; i < 20000; i++) {
        SPYValue *parent = spy_list(c);
        assert(parent && !spy_list_append(c, parent, deep));
        spy_release(deep); deep = parent;
    }
    spy_release(deep);
    assert(spy_live_values(c) == baseline);

    SPYValue *left = spy_list(c), *right = spy_list(c), *leaf = spy_int(c, 1);
    assert(left && right && leaf);
    assert(!spy_list_append(c, left, right));
    assert(!spy_list_append(c, right, left));
    assert(!spy_list_append(c, right, leaf));
    spy_release(left); spy_release(right);
    assert(spy_collect(c) == 2);
    assert(integer(c, leaf) == 1);
    assert(spy_live_values(c) == baseline);

    execute(c, "f = None\nouter = None\n");
    spy_collect(c);
    baseline = spy_live_values(c);
    for (int i = 0; i < 100; i++) {
        execute(c, "def outer():\n    a = []\n    a.append(a)\n    def inner():\n        return a\n    return inner\nf = outer()\nf = None\nouter = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
    }

    /* Defaults, bound methods, iterators, and suspended generators all own
     * edges. A cycle through any of them must be collectable. */
    execute(c, "C = None\na = None\nitems = None\ng = None\nmake = None\n");
    spy_collect(c);
    baseline = spy_live_values(c);
    for (int i = 0; i < 50; i++) {
        execute(c, "def make():\n    def inner(): yield 1\n    return inner\n"
                   "a = make()\ng = a()\nitems = a.__code__\nassert items is g.gi_code\n"
                   "g.close()\na = None\nmake = None\nassert g.gi_code is items\n"
                   "g = None\nitems = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "def make():\n"
                   "    class A:\n        def method(self): return __class__\n"
                   "    class B(A): pass\n    class C(A): pass\n    class D(B, C): pass\n"
                   "    a = D()\n    a.cycle = super(B, a)\n    return a\n"
                   "a = make()\nassert a.cycle.method() is a.__class__.__mro__[3]\na = None\nmake = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "def make():\n"
                   "    class D:\n        def __set_name__(self, owner, name):\n"
                   "            self.owner = owner\n            raise ValueError('set name')\n"
                   "    class C:\n        attr = D()\n"
                   "try: make()\nexcept ValueError as a: assert a.__notes__\nmake = None\na = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "def make():\n"
                   "    class C:\n        def __getattribute__(self, name):\n"
                   "            object.__setattr__(self, 'cycle', self)\n            raise ValueError(name)\n"
                   "    a = C()\n    try: a.value\n    except ValueError: pass\n"
                   "make()\nmake = None\n"
                   "a = property(lambda self: 1)\na.__name__ = a\na = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __hash__(self):\n        self.cycle = self\n        raise ValueError('hash')\n"
                   "a = C()\nitems = {}\ntry: items.setdefault(a, a)\nexcept ValueError: pass\n"
                   "a = None\nitems = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "items = {}\nitems['cycle'] = items\ng = items.copy()\n"
                   "assert g.pop('cycle') is items\nitems.clear()\ng = None\nitems = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __new__(cls):\n        a = object.__new__(cls)\n        a.cycle = a\n        return a\n"
                   "    def __init__(self): raise ValueError('initialization')\n"
                   "try: C()\nexcept ValueError: pass\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "def make(x=1, *, y=2): return x, y\n"
                   "make.__defaults__ = (make,)\nmake.__kwdefaults__ = {'y': make}\n"
                   "del make.__defaults__\ndelattr(make, '__kwdefaults__')\n"
                   "assert make.__defaults__ is None\nassert make.__kwdefaults__ is None\nmake = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "g = ValueError('cycle')\ng.__cause__ = g\nassert g.__suppress_context__\ng = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "items = [3, 1, 2]\n"
                   "def make(x):\n    items.append(items)\n    return x\n"
                   "try: items.sort(key=make)\nexcept ValueError: pass\n"
                   "assert items == [1, 2, 3]\nmake = None\nitems = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __eq__(self, other):\n        items.clear()\n        return True\n"
                   "items = [C()]\nitems.remove(None)\nassert items == []\nitems = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "def make(x=1, *, y=2): return x, y\n"
                   "make.__defaults__ = (make,)\nmake.__kwdefaults__ = {'y': make}\n"
                   "assert make() == (make, make)\n"
                   "g = make.__code__\nassert g.co_argcount == 1\n"
                   "make = None\ng = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "def make(x): return x\ng = make.__code__\nmake = None\n");
        SPYValue *code = spy_get_global(c, "g");
        execute(c, "g = None\n");
        spy_collect(c);
        assert(!spy_set_global(c, "g", code));
        spy_release(code);
        execute(c, "assert g.co_name == 'make'\nassert g.co_argcount == 1\ng = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "def make(x):\n    if x == 2: raise ValueError('key')\n    return [x]\n"
                   "try: sorted([3, 2, 1], key=make)\nexcept ValueError: pass\nmake = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __hash__(self): return 0\n"
                   "    def __eq__(self, other):\n        del items[self]\n        return True\n"
                   "items = {C(): 1}\ng = C()\nassert g not in items\n"
                   "items = None\ng = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "g = range(10**100, 10**100 + 10, 3)\nitems = iter(g)\n"
                   "assert next(items) == 10**100\nassert g[-1] == 10**100 + 9\n"
                   "g = g[::-1]\nassert next(items) == 10**100 + 3\n"
                   "g = None\nitems = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __await__(self):\n        value = yield 1\n        yield value\n"
                   "async def make():\n    return [await C() for x in range(2)]\n"
                   "g = make()\nassert g.send(None) == 1\nassert g.send(g) is g\n"
                   "g = None\nmake = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __await__(self):\n        value = yield 1\n        yield value\n"
                   "g = (await C() for x in range(2))\nitems = g.__anext__()\n"
                   "assert next(items) == 1\nassert items.send(g) is g\n"
                   "g = None\nitems = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __await__(self):\n        value = yield 1\n        yield value\n"
                   "async def make():\n    yield await C()\n"
                   "g = make()\nitems = anext(g, [])\nassert items.send(None) == 1\n"
                   "assert items.send(items) is items\n"
                   "g = None\nitems = None\nmake = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __await__(self):\n        value = yield 1\n        yield value\n"
                   "async def make():\n    try: yield 0\n    finally: await C()\n"
                   "g = make()\ntry: next(g.__anext__())\nexcept StopIteration: pass\n"
                   "items = g.aclose()\nassert items.send(None) == 1\nassert items.send(g) is g\n"
                   "g = None\nitems = None\nmake = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def f(self): return self\na = C()\na.method = a.f\na.link = a\n"
                   "items = []\ndef make(value=items): return value\nitems.append(make)\n"
                   "g = (x for x in items)\nitems.append(g)\n"
                   "C = None\na = None\nitems = None\ng = None\nmake = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
    }
    execute(c, "def make(n): return (i+n for i in range(3))\ng = make(40)\n");
    SPYValue *generator = spy_get_global(c, "g");
    execute(c, "g = None\nmake = None\n");
    spy_collect(c);
    assert(!spy_set_global(c, "g", generator));
    spy_release(generator);
    assert(integer(c, spy_eval(c, "next(g)", "resume.py")) == 40);
    spy_collect(c);
    assert(integer(c, spy_eval(c, "next(g)", "resume.py")) == 41);
    execute(c, "assert list(g) == [42]\ng = None\n");
    spy_collect(c);
    assert(spy_live_values(c) == baseline);

    /* Descriptor wrappers and their callable fields are collector edges. */
    for (int i = 0; i < 50; i++) {
        execute(c, "def make(): pass\nmake.cycle = make\ng = staticmethod(make)\ng.cycle = g\n"
                   "g = None\nmake = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "g = {}\nexec('def f(): return 42', g)\ng = None\n"
                   "class C:\n    saved = locals()\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C: pass\nC.static = staticmethod(C)\nC.cls = classmethod(C)\n"
                   "C.prop = property(C(), C(), C(), C())\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "def make():\n    value = []\n    def inner():\n        nonlocal value\n"
                   "        value.append(inner)\n        return value\n    return inner\n"
                   "g = make()\ng()\ng = None\nmake = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
    }
    execute(c, "def make():\n    value = 40\n    def inner():\n        nonlocal value\n"
               "        value += 1\n        return value\n    return inner\ng = make()\n");
    SPYValue *closure = spy_get_global(c, "g");
    execute(c, "g = None\nmake = None\n");
    spy_collect(c);
    assert(integer(c, spy_call(c, closure, 0, NULL)) == 41);
    spy_collect(c);
    assert(integer(c, spy_call(c, closure, 0, NULL)) == 42);
    spy_release(closure); spy_collect(c);
    assert(spy_live_values(c) == baseline);

    int calls = 0;
    /* A suspended function owns operands, iterators, pending exceptions and
     * cleanup callbacks, even when no Python name still reaches its source. */
    for (int i = 0; i < 50; i++) {
        execute(c, "def make():\n    value = yield 1\n    yield [value, (yield 2)]\n"
                   "g = make()\nassert next(g) == 1\nassert g.send(g) == 2\n"
                   "g = None\nmake = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "def make():\n    value = yield 1\n    try:\n        raise ValueError(value)\n"
                   "    finally:\n        value = None\n        yield 2\n"
                   "g = make()\nnext(g)\ng.send(g)\ng = None\nmake = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __enter__(self): return self\n    def __exit__(self, t, v, tb): pass\n"
                   "def make():\n    with C() as value:\n        value.gen = yield 1\n        value = None\n        yield 2\n"
                   "g = make()\nnext(g)\ng.send(g)\ng = None\nmake = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "def make():\n    yield f'{(yield 1):{(yield 2)}}'\n"
                   "g = make()\nnext(g)\ng.send(g)\ng = None\nmake = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "items = []\ng = slice(items)\nitems.append(g)\nitems = None\ng = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __await__(self):\n        value = yield 1\n        yield value\n"
                   "async def make():\n    return await C()\n"
                   "g = make()\nassert g.send(None) == 1\nassert g.send(g) is g\n"
                   "g = None\nmake = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __await__(self):\n        value = yield 1\n        yield value\n"
                   "async def make():\n    return await C()\n"
                   "g = make()\nitems = g.__await__()\nassert next(items) == 1\nassert items.send(items) is items\n"
                   "g = None\nitems = None\nmake = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __await__(self):\n        value = yield 1\n        yield value\n"
                   "    def __aiter__(self): return self\n    async def __anext__(self): return await self\n"
                   "async def make():\n    async for item in C(): pass\n"
                   "g = make()\nassert g.send(None) == 1\nassert g.send(g) is g\n"
                   "g = None\nmake = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __await__(self):\n        value = yield 1\n        yield value\n"
                   "    async def __aenter__(self): return self\n"
                   "    async def __aexit__(self, t, v, tb): return await self\n"
                   "async def make():\n    async with C(): return 42\n"
                   "g = make()\nassert g.send(None) == 1\nassert g.send(g) is g\n"
                   "g = None\nmake = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
        execute(c, "class C:\n    def __await__(self):\n        value = yield 1\n        yield value\n"
                   "    async def __aenter__(self): return self\n"
                   "    async def __aexit__(self, t, v, tb): return await self\n"
                   "async def make():\n    async with C(): raise ValueError('pending')\n"
                   "g = make()\nassert g.send(None) == 1\nassert g.send(g) is g\n"
                   "g = None\nmake = None\nC = None\n");
        spy_collect(c);
        assert(spy_live_values(c) == baseline);
    }
    execute(c, "def make():\n    try:\n        yield 40\n    finally:\n        yield 41\n"
               "g = make()\nassert next(g) == 40\n");
    generator = spy_get_global(c, "g");
    execute(c, "g = None\nmake = None\n");
    spy_collect(c);
    assert(!spy_set_global(c, "g", generator));
    spy_release(generator);
    assert(integer(c, spy_eval(c, "next(g)", "resume.py")) == 41);
    execute(c, "assert next(g, 42) == 42\ng = None\n");
    spy_collect(c);
    assert(spy_live_values(c) == baseline);

    execute(c, "g = {}\nexec('def f(): return 42', g)\nmake = g['f']\ng = None\n");
    closure = spy_get_global(c, "make");
    execute(c, "make = None\n");
    spy_collect(c);
    assert(integer(c, spy_call(c, closure, 0, NULL)) == 42);
    spy_release(closure); spy_collect(c);
    assert(spy_live_values(c) == baseline);

    spy_set_module_loader(c, loader, &calls);
    execute(c, "import sample\nfrom sample import add as plus\nassert sample.answer == 42\nassert plus(1) == 43\n"
               "sample.__dict__['answer'] = 44\nassert sample.answer == 44\n"
               "assert sample.add.__globals__ is sample.__dict__\n");
    assert(calls == 2);
    assert(spy_exec(c, "import missing", "api.py") == -1);
    assert(!strcmp(spy_error_type(c), "ModuleNotFoundError"));
    /* missing.__init__, missing, and missing.__namespace__. */
    assert(calls == 5);

    /* Traceback suggestions preserve the raw exception and never execute
     * candidate source or invoke the module loader. Repeated formatting must
     * release the temporary syntax trees and exceptions it creates. */
    assert(spy_exec(c, "improt sample", "suggestion.py") == -1);
    assert(!strcmp(spy_error_message(c), "invalid syntax"));
    assert(!strcmp(spy_error_display(c), "invalid syntax. Did you mean 'import'?"));
    spy_collect(c);
    size_t display_baseline = spy_live_values(c);
    for (int i = 0; i < 20; i++) {
        assert(!strcmp(spy_error_display(c), "invalid syntax. Did you mean 'import'?"));
        assert(!strcmp(spy_error_type(c), "SyntaxError"));
        assert(!strcmp(spy_error_message(c), "invalid syntax"));
        assert(!strcmp(spy_error_filename(c), "suggestion.py"));
        assert(spy_error_line(c) == 1 && calls == 5);
        spy_collect(c);
        assert(spy_live_values(c) == display_baseline);
    }

    /* -OO: no asserts, __debug__ False, no docstrings; compile(optimize=-1) inherits it. */
    spy_set_optimize(c, 2);
    execute(c, "def documented():\n    'doc'\n    return 1\nassert 0\n"
               "optimized = (__debug__, documented.__doc__, documented(), eval(compile('__debug__', '', 'eval')))");
    spy_set_optimize(c, 0);
    assert(integer(c, spy_eval(c, "optimized == (False, None, 1, False) and __debug__", "optimize.py")) == 1);
    spy_set_step_limit(c, 100);
    assert(spy_exec(c, "while True:\n    pass\n", "loop.py") == -1);
    assert(!strcmp(spy_error_type(c), "RuntimeError"));
    assert(!strcmp(spy_error_filename(c), "loop.py"));
    assert(spy_error_line(c) > 0);
    assert(integer(c, spy_eval(c, "40 + 2", "recovery.py")) == 42);
    /* Calls, loop passes in generators and comprehensions, and source text
     * spend steps; a spent budget fails every handler and finally body. */
    spy_set_step_limit(c, 1000);
    const char *endless[] = {
        "def f(n): return f(n - 1) + f(n - 1) if n else 1\nf(40)",
        "def g():\n    while True:\n        continue\n    yield\nnext(g())",
        "[x for x in iter(int, 1)]",
        "exec('x = 1\\n' * 100000)",
        "caught = 0\ntry:\n    while True: pass\nexcept BaseException:\n    caught = 1\nfinally:\n    caught = 2",
    };
    for (size_t i = 0; i < sizeof(endless) / sizeof(*endless); i++) {
        assert(spy_exec(c, endless[i], "endless.py") == -1);
        assert(!strcmp(spy_error_type(c), "RuntimeError"));
    }
    assert(integer(c, spy_eval(c, "caught", "caught.py")) == 0);
    /* The context tells a stop from the same error raised by the program;
     * a finalizer that became due while stopped runs in the next call. */
    assert(spy_exec(c, "class Dying:\n    def __del__(self): died.append(1)\ndied = []\n"
                       "def f():\n    d = Dying(); d.me = d\n    while True: pass\nf()", "dying.py") == -1);
    assert(spy_stopped(c) == SPY_STOP_STEPS);
    spy_clear_error(c);
    spy_collect(c);
    assert(integer(c, spy_eval(c, "pass\nlen(died)", "died.py")) == 1);
    assert(spy_stopped(c) == 0);
    assert(spy_exec(c, "raise RuntimeError('execution step limit exceeded')", "raised.py") == -1);
    assert(spy_stopped(c) == 0);
    /* Each outermost call, spy_call included, gets the whole budget; a host
     * function calling back shares its caller's. */
    execute(c, "def spin(n):\n    for i in range(n): pass\n    return n");
    SPYValue *spin = spy_get_global(c, "spin"), *six = spy_int(c, 600);
    for (int i = 0; i < 3; i++) assert(integer(c, spy_call(c, spin, 1, &six)) == 600);
    spy_release(spin); spy_release(six);
    assert(!spy_define(c, "call_back", call_back, NULL));
    execute(c, "call_back(lambda: spin(600))");
    assert(spy_exec(c, "spin(600)\ncall_back(lambda: spin(600))", "shared.py") == -1);
    assert(!strcmp(spy_error_type(c), "RuntimeError"));
    /* A large block spends a step per 64 bytes. */
    assert(spy_exec(c, "s = 'a' * 10**6", "produce.py") == -1);
    assert(spy_stopped(c) == SPY_STOP_STEPS);
    spy_set_step_limit(c, 0);
    /* The engine counts the bytes it holds; a memory limit stops the call
     * with a MemoryError no handler sees, and the context stays usable. */
    spy_clear_error(c); spy_collect(c);
    size_t held = spy_memory_used(c);
    execute(c, "big = 'a' * 10**6");
    assert(spy_memory_used(c) > held + 1000000);
    execute(c, "del big");
    spy_collect(c);
    assert(spy_memory_used(c) < held + 100000);
    spy_set_memory_limit(c, held + (8 << 20));
    assert(spy_exec(c, "caught = 0\ntry:\n    x = [0] * 10**7\nexcept MemoryError:\n    caught = 1", "memory.py") == -1);
    assert(!strcmp(spy_error_type(c), "MemoryError") && spy_stopped(c) == SPY_STOP_MEMORY);
    assert(integer(c, spy_eval(c, "caught", "caught.py")) == 0);
    spy_set_memory_limit(c, 0);
    /* The interrupt is polled at least every 4096 steps; it stops the call
     * like a spent budget, and the next call runs normally. */
    int polls = 0;
    spy_set_step_limit(c, 100000);
    spy_set_interrupt(c, count_polls, &polls);
    assert(spy_exec(c, "caught = 0\ntry:\n    while True: pass\nexcept BaseException:\n    caught = 1", "interrupt.py") == -1);
    assert(!strcmp(spy_error_message(c), "execution interrupted") && spy_stopped(c) == SPY_STOP_INTERRUPT);
    assert(polls == 10 && integer(c, spy_eval(c, "caught", "caught.py")) == 0);
    polls = -1000;
    assert(spy_exec(c, "while True: pass", "polled.py") == -1);
    assert(spy_stopped(c) == SPY_STOP_STEPS && polls >= -1000 + 100000 / 4096);
    /* Without a step limit, a native loop over an endless iterator polls. */
    polls = 0;
    spy_set_step_limit(c, 0);
    const char *polled[] = {"sum(iter(int, 1))", "while True: pass", "for x in iter(int, 1): pass", "any(x for x in iter(int, 1))",
                            "[x for x in iter(int, 1)]"};
    for (size_t i = 0; i < sizeof(polled) / sizeof(*polled); i++) {
        polls = 0;
        assert(spy_exec(c, polled[i], "polled.py") == -1 && spy_stopped(c) == SPY_STOP_INTERRUPT);
    }
    spy_set_interrupt(c, NULL, NULL);
    assert(spy_exec(c, "def recurse():\n    return recurse()\nrecurse()", "recursion.py") == -1);
    assert(!strcmp(spy_error_type(c), "RecursionError"));

    /* Parsing must finish before any statement runs. */
    execute(c, "x = 1");
    assert(spy_exec(c, "x = 2\nif:\n", "bad.py") == -1);
    spy_clear_error(c);
    assert(integer(c, spy_get_global(c, "x")) == 1);
    const char *invalid_utf8[] = {"\x80\x80", "\xbf\xbf", "\xc0\x80", "\xed\xa0\x80", "\xf4\x90\x80\x80", "\xe2\x82"};
    for (size_t i = 0; i < sizeof(invalid_utf8) / sizeof(*invalid_utf8); i++) {
        assert(spy_exec(c, invalid_utf8[i], "encoding.py") == -1);
        assert(!strcmp(spy_error_type(c), "SyntaxError"));
        spy_clear_error(c);
    }
    assert(spy_exec(c, "x = 2\n1__0", "bad_literal.py") == -1);
    spy_clear_error(c);
    assert(integer(c, spy_get_global(c, "x")) == 1);
    assert(spy_exec(c, "1 / 0", "zero.py") == -1);
    assert(!strcmp(spy_error_type(c), "ZeroDivisionError"));
    assert(integer(c, spy_eval(c, "42", "ok.py")) == 42);

    SPYValue *tuple = spy_eval(c, "(1, 2)", "tuple.py");
    SPYValue *item = spy_int(c, 3);
    assert(tuple && item && spy_list_append(c, tuple, item) == -1);
    spy_release(tuple); spy_release(item);

    /* Bounded malformed-source stress: exercise parse cleanup and recovery. */
    static const char alphabet[] = "abcfur0123_ @+-*/<>=!()[]{}:;,.\n'\"#\\";
    uint32_t seed = 315;
    spy_set_step_limit(c, 500);
    for (size_t i = 0; i < 5000; i++) {
        char source[80];
        size_t len = i % (sizeof(source) - 1);
        for (size_t j = 0; j < len; j++) {
            seed = seed * 1664525u + 1013904223u;
            source[j] = alphabet[seed % (sizeof(alphabet) - 1)];
        }
        source[len] = 0;
        SPYValue *v = spy_eval(c, source, "fuzz.py");
        spy_release(v); spy_collect(c);
    }
    assert(integer(c, spy_eval(c, "42", "recovered.py")) == 42);
    assert(!spy_string(c, "", SIZE_MAX));
    assert(!strcmp(spy_error_type(c), "MemoryError"));

    /* Built-in modules import without a loader. The collector clears weak
     * references (the engine primitives) to cyclic garbage; callbacks run at
     * the next statement. */
    spy_set_step_limit(c, 0);
    assert(!spy_exec(c, "import _spy\nclass Ref:\n"
                        "    def __init__(self, target, callback): _spy._weak_bind(target, self, callback)\n"
                        "    def __call__(self): return _spy._weak_get(self)\n"
                        "class Node: pass\nseen = []\nn = Node(); n.me = n\n"
                        "wr = Ref(n, seen.append)\ndel n", "weak.py"));
    spy_collect(c);
    assert(!spy_exec(c, "pass\nassert wr() is None and seen == [wr], seen", "weak_check.py"));
    size_t before = spy_live_values(c);
    for (int i = 0; i < 3; i++) {
        assert(!spy_exec(c, "n = Node(); n.me = n; w = Ref(n, lambda r: None); del n, w", "weak_loop.py"));
        spy_collect(c);
    }
    assert(spy_live_values(c) <= before + 8);


    {
        /* Natives with keywords and host data, containers, attributes, iteration,
         * and exception objects. */
        released = 0;
        static int weight = 1;
        SPYValue *native = spy_native(c, "keyword_sum", keyword_sum, &weight, release_counter);
        assert(native && !spy_set_global(c, "keyword_sum", native));
        assert(integer(c, spy_eval(c, "keyword_sum(1, 2, scale=10)", "native.py")) == 13);
        SPYValue *one = spy_int(c, 1), *two = spy_int(c, 2), *pair[] = {one, two};
        SPYValue *tuple = spy_tuple(c, 2, pair), *keywords = spy_dict(c), *scale = spy_string(c, "scale", 5);
        assert(tuple && keywords && scale && !spy_set_item(c, keywords, scale, two));
        SPYValue *sum = spy_call_keywords(c, native, 2, pair, keywords);
        assert(integer(c, sum) == 5);
        assert(integer(c, spy_get_item(c, tuple, one)) == 2);
        assert(integer(c, spy_get_item(c, keywords, scale)) == 2);
        SPYValue *iterator = spy_iter(c, tuple), *item;
        int64_t seen = 0;
        while ((item = spy_next(c, iterator))) seen += integer(c, item);
        assert(seen == 3 && !spy_error_type(c)[0]);
        spy_release(iterator);
        SPYValue *size = spy_get_attr(c, tuple, "count"), *counted = size ? spy_call(c, size, 1, &one) : NULL;
        assert(integer(c, counted) == 1);
        spy_release(size);
        assert(!spy_get_attr(c, tuple, "missing") && !strcmp(spy_error_type(c), "AttributeError"));
        spy_clear_error(c);
        assert(!spy_exec(c, "class Box: pass\nbox = Box()", "box.py"));
        SPYValue *box = spy_get_global(c, "box");
        assert(box && !spy_set_attr(c, box, "value", two));
        assert(integer(c, spy_eval(c, "box.value", "box_value.py")) == 2);
        SPYValue *text = spy_str(c, tuple);
        assert(text && !strcmp(spy_as_string(c, text, NULL), "(1, 2)"));
        spy_release(text); spy_release(box); spy_release(tuple); spy_release(keywords); spy_release(scale);
        spy_release(one); spy_release(two);
        SPYValue *failing = spy_native(c, "failing", raise_value_error, NULL, NULL);
        assert(failing && !spy_call(c, failing, 0, NULL) && !strcmp(spy_error_type(c), "ValueError"));
        SPYValue *error = spy_error_value(c), *args = error ? spy_get_attr(c, error, "args") : NULL;
        assert(args && !strcmp(spy_error_type(c), "ValueError"));
        spy_release(args); spy_release(error); spy_release(failing); spy_clear_error(c);
        assert(!spy_error_value(c));
        assert(!spy_exec(c, "try:\n    keyword_sum('x')\nexcept TypeError:\n    caught = 1", "native_error.py"));
        spy_release(native);
        assert(!spy_exec(c, "del keyword_sum", "native_del.py") && released == 1);
    }

    {
        /* open() reaches only mounts: nothing without one, read-only data
         * at its guest path, and relative paths from the first mount. */
        SPYContext *files = spy_context_new();
        assert(files);
        assert(!spy_exec(files, "try:\n    open('tests/api.c')\nexcept PermissionError as e:\n    assert e.errno == 13\n", "no_mount.py"));
        assert(spy_mount(files, "tests/missing", NULL, 0) == -1 && !strcmp(spy_error_type(files), "OSError"));
        spy_clear_error(files);
        assert(spy_mount(files, "tests", "data", 0) == -1 && !strcmp(spy_error_type(files), "ValueError"));
        spy_clear_error(files);
        assert(!spy_mount(files, "tests", "/data/./", SPY_MOUNT_READ_ONLY));
        assert(!spy_exec(files,
            "with open('/data/api.c') as f:\n    assert f.readline().startswith('#include')\n"
            "assert open('api.c', 'rb').read(8) == b'#include'\n"
            "try:\n    open('/data/new.txt', 'w')\nexcept OSError as e:\n    assert type(e) is OSError and e.strerror, e\n"
            "try:\n    open('/data/../Makefile')\nexcept PermissionError:\n    pass\n", "mounted.py"));
        spy_context_free(files);
    }

    /* Reached by nothing else in make test: gc.get_referents, frame-locals
     * merging, sys's digit limit and breakpoint hook, float.__getformat__,
     * wide and half-float memoryview items, dict-view equality, latin-9, and
     * lazy import. */
    execute(c,
        "import gc, sys\n"
        "class T: pass\n"
        "t = T()\n"
        "holder = [t, 'x']\n"
        "assert t in gc.get_referents(holder) and 'x' in gc.get_referents(holder)\n"
        "def merged():\n"
        "    a = 1\n"
        "    locals_ = sys._getframe().f_locals\n"
        "    both = locals_ | {'b': 2}\n"
        "    locals_ |= {'c': 3}\n"
        "    return both['a'] + both['b'] + locals_['c']\n"
        "assert merged() == 6\n"
        "assert sys._getframe().f_locals.__or__(1) is NotImplemented\n"
        "sys.set_int_max_str_digits(maxdigits=5000)\n"
        "assert sys.get_int_max_str_digits() == 5000\n"
        "sys.set_int_max_str_digits(4300)\n"
        "sys.breakpointhook = lambda *a, **k: ('hooked', a, k)\n"
        "assert breakpoint(1, x=2) == ('hooked', (1,), {'x': 2})\n"
        "del sys.breakpointhook\n"
        "try:\n"
        "    breakpoint()\n"
        "except RuntimeError as e:\n"
        "    assert str(e) == 'lost sys.breakpointhook', e\n"
        "assert float.__getformat__('double').startswith('IEEE')\n"
        "m = memoryview(bytearray(b'\\x01' + bytes(23)))\n"
        "assert m.cast('Q')[0] == 1 and m.cast('L')[0] == 1 and m.cast('N')[0] == 1\n"
        "h = memoryview(bytearray(4)).cast('e')\n"
        "h[0] = 1.5\n"
        "h[1] = -65504.0\n"
        "assert h.tolist() == [1.5, -65504.0]\n"
        "assert {1: 2}.keys() == {1} and {1: 2}.items() == {(1, 2)}\n"
        "assert 'a\\u20ac'.encode('iso8859-15') == b'a\\xa4' and b'\\xa4'.decode('latin9') == '\\u20ac'\n"
        "assert [{1: 2}.keys()] == [{1}]\n"
        "assert type(__lazy_import__('json')).__name__ == 'lazy_import'\n"
        "lazy import gc as lazy_gc\n"
        "assert lazy_gc.collect() >= 0\n");

    SPYContext *other = spy_context_new();
    assert(other);
    SPYValue *foreign = spy_int(other, 3);
    assert(spy_set_global(c, "foreign", foreign) == -1);
    spy_release(foreign); spy_context_free(other);
    spy_context_free(c);
    puts("C API: ownership, closures, cycles, imports, limits, mounts, and recovery passed");
    return 0;
}
