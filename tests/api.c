#include "../spy.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { char text[4096]; size_t len; } Output;
static int output(void *data, const char *s, size_t n) {
    Output *o = data;
    if (n >= sizeof(o->text) - o->len) return -1;
    memcpy(o->text + o->len, s, n); o->len += n; o->text[o->len] = 0;
    return 0;
}
static SPYValue *twice(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)data;
    int64_t n;
    if (argc != 1) return spy_error(c, "TypeError", "twice expects one argument");
    if (spy_as_int(c, argv[0], &n)) return NULL;
    if (n > INT64_MAX / 2 || n < INT64_MIN / 2) return spy_error(c, "OverflowError", "twice overflow");
    return spy_int(c, n * 2);
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
int main(void) {
    SPYContext *c = spy_context_new();
    assert(c);
    Output o = {{0}, 0};
    spy_set_output(c, output, &o);
    execute(c, "print('hello', 6 * 7)");
    assert(!strcmp(o.text, "hello 42\n"));
    assert(!spy_define(c, "twice", twice, NULL));
    assert(integer(c, spy_eval(c, "twice(21)", "api.py")) == 42);
    execute(c, "x = 19");
    assert(integer(c, spy_get_global(c, "x")) == 19);
    assert(integer(c, spy_eval(c, "x + 23", "api.py")) == 42);

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

    int calls = 0;
    spy_set_module_loader(c, loader, &calls);
    execute(c, "import sample\nfrom sample import add as plus\nassert sample.answer == 42\nassert plus(1) == 43\n");
    assert(calls == 1);
    assert(spy_exec(c, "import missing", "api.py") == -1);
    assert(!strcmp(spy_error_type(c), "ModuleNotFoundError"));
    assert(calls == 2);

    spy_set_step_limit(c, 100);
    assert(spy_exec(c, "while True:\n    pass\n", "loop.py") == -1);
    assert(!strcmp(spy_error_type(c), "RuntimeError"));
    assert(!strcmp(spy_error_filename(c), "loop.py"));
    assert(spy_error_line(c) > 0);
    assert(integer(c, spy_eval(c, "40 + 2", "recovery.py")) == 42);
    spy_set_step_limit(c, 0);
    assert(spy_exec(c, "def recurse():\n    return recurse()\nrecurse()", "recursion.py") == -1);
    assert(!strcmp(spy_error_type(c), "RecursionError"));

    /* Parsing must finish before any statement runs. */
    execute(c, "x = 1");
    assert(spy_exec(c, "x = 2\nif:\n", "bad.py") == -1);
    spy_clear_error(c);
    assert(integer(c, spy_get_global(c, "x")) == 1);
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
    static const char alphabet[] = "abc0123_ +-*/<>=!()[]{}:;,.\n'\"#\\";
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

    SPYContext *other = spy_context_new();
    assert(other);
    SPYValue *foreign = spy_int(other, 3);
    assert(spy_set_global(c, "foreign", foreign) == -1);
    spy_release(foreign); spy_context_free(other);
    spy_context_free(c);
    puts("C API: ownership, closures, cycles, imports, limits, and recovery passed");
    return 0;
}
