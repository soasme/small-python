#include "../spy.h"
#include "../spy-std.h"
#include "../spy-module.h"

#include <assert.h>
#include <dlfcn.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { char text[4096]; size_t len; int flushes, fail_flush; } Output;
static int output(SPYContext *c, void *data, const char *s, size_t n) {
    (void)c;
    Output *o = data;
    if (n >= sizeof(o->text) - o->len) return -1;
    memcpy(o->text + o->len, s, n); o->len += n; o->text[o->len] = 0;
    return 0;
}
/* fail_flush 1 fails the flush; 2 fails it with the host's own error. */
static int flush_output(SPYContext *c, void *data) {
    Output *o = data;
    o->flushes++;
    if (o->fail_flush == 2) spy_error(c, "BrokenPipeError", "host pipe closed");
    return o->fail_flush;
}
/* Sets the output limit from inside a call. */
static SPYValue *limit_output(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)argc; (void)data;
    int64_t n;
    if (spy_as_int(c, argv[0], &n) || spy_set_limit(c, SPY_LIMIT_OUTPUT, (size_t)n)) return NULL;
    return spy_none(c);
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
/* An interrupt that stops the context at every poll. */
static int always(void *data) { (void)data; return 1; }
/* Resume a paused call until it ends, counting the pauses. */
static SPYValue *run_paused(SPYContext *c, SPYValue *v, int reason, int *pauses) {
    while (!v && spy_paused(c)) {
        assert(spy_paused(c) == reason && !spy_error_type(c)[0]);
        ++*pauses;
        v = spy_resume(c);
    }
    return v;
}
/* A host function that calls its argument back into the engine. */
static SPYValue *call_back(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)data;
    if (argc != 1) return spy_error(c, "TypeError", "call_back expects one argument");
    return spy_call(c, argv[0], 0, NULL);
}
/* Host functions calling back by spy_callk. returned_k gives the call's
 * value as the host function's, counting its runs. */
static int k_runs;
static SPYValue *returned_k(SPYContext *c, SPYValue *result, SPYValue *state) {
    (void)c;
    k_runs++;
    spy_release(state);
    return result;
}
/* call_k(f, *args): f(*args). */
static SPYValue *call_k(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)data;
    if (!argc) return spy_error(c, "TypeError", "call_k expects a callable");
    return spy_callk(c, argv[0], argc - 1, argv + 1, returned_k, NULL);
}
/* twice_k(f, x): f(f(x)), the continuation making the second call with f,
 * its state. */
static SPYValue *again_k(SPYContext *c, SPYValue *result, SPYValue *f) {
    SPYValue *v = result ? spy_callk(c, f, 1, &result, returned_k, NULL) : NULL;
    spy_release(result); spy_release(f);
    return v;
}
static SPYValue *twice_k(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)data;
    if (argc != 2) return spy_error(c, "TypeError", "twice_k expects two arguments");
    return spy_callk(c, argv[0], 1, argv + 1, again_k, spy_retain(argv[0]));
}
/* caught(f): f(), or the name of the exception it raised, which the
 * continuation clears. */
static SPYValue *caught_k(SPYContext *c, SPYValue *result, SPYValue *state) {
    (void)state;
    if (result) return result;
    char name[64];
    snprintf(name, sizeof(name), "%s", spy_error_type(c));
    spy_clear_error(c);
    return spy_string(c, name, strlen(name));
}
static SPYValue *caught(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)data;
    return argc == 1 ? spy_callk(c, argv[0], 0, NULL, caught_k, NULL) : spy_error(c, "TypeError", "caught expects one argument");
}
/* keyword_k(f, x=v): f(v). */
static SPYValue *keyword_k(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *data) {
    (void)data;
    SPYValue *x = spy_string(c, "x", 1), *v = argc == 1 && keywords && x ? spy_get_item(c, keywords, x) : NULL;
    spy_release(x);
    if (!v) return spy_error(c, "TypeError", "keyword_k expects f and x=");
    SPYValue *result = spy_callk(c, argv[0], 1, &v, returned_k, NULL);
    spy_release(v);
    return result;
}
/* Misuses: a value returned over a spy_callk, and a second spy_callk. */
static SPYValue *over_k(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)data;
    SPYValue *left = spy_callk(c, argv[0], argc - 1, argv + 1, returned_k, NULL);
    return left ? left : spy_int(c, 1);
}
static SPYValue *double_k(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)data;
    SPYValue *left = spy_callk(c, argv[0], argc - 1, argv + 1, returned_k, NULL);
    return left ? left : spy_callk(c, argv[0], argc - 1, argv + 1, returned_k, spy_int(c, 2));
}
static int fill_registered(SPYContext *c, SPYValue *module) {
    SPYValue *value = spy_int(c, 7);
    int status = value ? spy_set_attr(c, module, "value", value) : -1;
    spy_release(value);
    return status;
}
static SPYValue *loader(SPYContext *c, void *data, const char *name) {
    int *calls = data;
    (*calls)++;
    if (!strcmp(name, "text")) return spy_string(c, "x = 1", 5);
    if (!strcmp(name, "registered")) { spy_new_module(c, name, fill_registered); return NULL; }
    if (strcmp(name, "sample")) return NULL;
    const char *source = "answer = 42\ndef add(x):\n    return x + answer\n";
    return spy_bytes(c, source, strlen(source));
}
/* Modules whose bodies loop, for imports that pause: looping, and
 * breaking, which raises after its loop, counting its loads in data. */
static SPYValue *looping_loader(SPYContext *c, void *data, const char *name) {
    const char *source = !strcmp(name, "looping") ? "'''Loops.'''\nn = 0\nwhile n < 3000: n += 1\n" :
                         !strcmp(name, "breaking") ? "n = 0\nwhile n < 3000: n += 1\nraise ValueError('broken')\n" : NULL;
    if (source && name[0] == 'b') ++*(int *)data;
    return source ? spy_bytes(c, source, strlen(source)) : NULL;
}
/* A policy that logs each event with its argument count, refuses those named
 * in data, and raises its own error for "custom". */
typedef struct { const char *refuse; char log[256]; } Policy;
static int policy(SPYContext *c, void *data, const char *event, SPYValue *args) {
    Policy *p = data;
    size_t len = strlen(p->log), n = 0;
    SPYValue *iterator = spy_iter(c, args), *item;
    while ((item = spy_next(c, iterator))) { n++; spy_release(item); }
    spy_release(iterator);
    snprintf(p->log + len, sizeof(p->log) - len, "%s/%zu ", event, n);
    if (!strcmp(event, "custom")) { spy_error(c, "ValueError", "custom refusal"); return -1; }
    return strstr(p->refuse, event) != NULL;
}
/* Lines for input(), from a NULL-terminated list. */
static SPYValue *read_line(SPYContext *c, void *data) {
    const char ***lines = data;
    if (!**lines) return NULL;
    const char *line = *(*lines)++;
    if (!strcmp(line, "bytes")) return spy_bytes(c, line, strlen(line));
    return spy_string(c, line, strlen(line));
}
static int64_t integer(SPYContext *c, SPYValue *v) {
    int64_t n;
    assert(v && !spy_as_int(c, v, &n));
    spy_release(v);
    return n;
}
/* Execute source, resuming it when the step budget pauses it. */
static void execute(SPYContext *c, const char *source) {
    SPYValue *v = spy_exec(c, source, "api.py") ? NULL : spy_none(c);
    while (!v && spy_paused(c)) v = spy_resume(c);
    if (!v) {
        fprintf(stderr, "api.py:%zu: %s: %s\n", spy_error_line(c), spy_error_type(c), spy_error_message(c));
        abort();
    }
    spy_release(v);
}
/* OSError(errno, strerror) is the subclass for the host's value of errno. */
static void errno_classes(void) {
    static const struct { int code; const char *name; } classes[] = {
#ifdef EAGAIN
        {EAGAIN, "BlockingIOError"},
#endif
#ifdef EWOULDBLOCK
        {EWOULDBLOCK, "BlockingIOError"},
#endif
#ifdef EALREADY
        {EALREADY, "BlockingIOError"},
#endif
#ifdef EINPROGRESS
        {EINPROGRESS, "BlockingIOError"},
#endif
#ifdef ECHILD
        {ECHILD, "ChildProcessError"},
#endif
#ifdef EPIPE
        {EPIPE, "BrokenPipeError"},
#endif
#ifdef ESHUTDOWN
        {ESHUTDOWN, "BrokenPipeError"},
#endif
#ifdef ECONNABORTED
        {ECONNABORTED, "ConnectionAbortedError"},
#endif
#ifdef ECONNREFUSED
        {ECONNREFUSED, "ConnectionRefusedError"},
#endif
#ifdef ECONNRESET
        {ECONNRESET, "ConnectionResetError"},
#endif
#ifdef EEXIST
        {EEXIST, "FileExistsError"},
#endif
#ifdef ENOENT
        {ENOENT, "FileNotFoundError"},
#endif
#ifdef EISDIR
        {EISDIR, "IsADirectoryError"},
#endif
#ifdef ENOTDIR
        {ENOTDIR, "NotADirectoryError"},
#endif
#ifdef EINTR
        {EINTR, "InterruptedError"},
#endif
#ifdef EACCES
        {EACCES, "PermissionError"},
#endif
#ifdef EPERM
        {EPERM, "PermissionError"},
#endif
#ifdef ESRCH
        {ESRCH, "ProcessLookupError"},
#endif
#ifdef ETIMEDOUT
        {ETIMEDOUT, "TimeoutError"},
#endif
        {0, "OSError"}, {-1, "OSError"},
    };
    SPYContext *c = spy_context_new();
    assert(c);
    for (size_t i = 0; i < sizeof(classes) / sizeof(*classes); i++) {
        char source[128];
        snprintf(source, sizeof(source), "assert type(OSError(%d, 'x')).__name__ == '%s'\n", classes[i].code, classes[i].name);
        execute(c, source);
    }
    spy_context_free(c);
}
/* Mappings can close cycles through class bodies, closures, and exec locals. */
static void namespace_cycles(void) {
    SPYContext *c = spy_context_new();
    assert(c);
    int host = 0;
    assert(!strcmp(spy_version(), SPY_VERSION));
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
/* spy_std_load_native asks the policy before it opens a library, registers
 * the module under any name with the init of its last name, and refuses a
 * library that another engine in the process linked. */
static void native_modules(const char *library) {
    SPYContext *c = spy_context_new();
    assert(c);
    Policy rules = {"dlopen", ""};
    spy_set_policy(c, policy, &rules);
    assert(spy_std_load_native(c, "fib", library) == -1 && !strcmp(spy_error_type(c), "PermissionError"));
    assert(!strcmp(spy_error_message(c), "dlopen is not allowed by the host policy"));
    assert(spy_exec(c, "import fib", "native.py") == -1 && !strcmp(spy_error_type(c), "ModuleNotFoundError"));
    spy_clear_error(c);
    rules.refuse = "";
    assert(!spy_std_load_native(c, "pkg.fib", library) && !spy_std_load_native(c, "fib", library));
    execute(c, "import fib\nassert fib.fib(20) == 6765\n");
    assert(!strcmp(rules.log, "dlopen/2 dlopen/2 dlopen/2 import/1 "));
    assert(spy_std_load_native(c, "fib", "/nonexistent/fib.so") == -1 && !strcmp(spy_error_type(c), "ImportError"));
    assert(strstr(spy_error_message(c), "/nonexistent/fib.so"));
    spy_clear_error(c);

    void *handle = dlopen(library, RTLD_NOW | RTLD_LOCAL);
    SPYModuleLink *link = handle ? dlsym(handle, "spy_module") : NULL;
    assert(link && link->api);
    const SPYModuleAPI *ours = link->api;
    SPYModuleAPI theirs = *ours;
    link->api = &theirs;
    assert(spy_std_load_native(c, "fib", library) == -1 && !strcmp(spy_error_type(c), "ImportError"));
    assert(!strcmp(spy_error_message(c), "dynamic module is linked to another engine in this process"));
    link->api = ours;
    dlclose(handle);
    spy_context_free(c);
}
int main(int argc, char **argv) {
    if (argc != 2) {
        fputs("usage: tests/api LIBRARY   (a native module defining fib, as examples/fib.so)\n", stderr);
        return 2;
    }
    native_modules(argv[1]);
    namespace_cycles();
    errno_classes();
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
        assert(spy_std_init_module(bare, "gc") && spy_std_init_module(bare, "nope"));
        spy_context_free(bare);
    }
    {
        /* sys.argv and sys.orig_argv are copies of the command lines the host
         * set before sys was first imported: each context's own, decoded as
         * UTF-8 with surrogateescape, and empty when none was set. */
        SPYContext *first = spy_context_new(), *second = spy_context_new(), *unset = spy_context_new();
        assert(first && second && unset && !spy_std_init(first) && !spy_std_init(second) && !spy_std_init(unset));
        char program[] = "prog", word[] = "caf\xc3\xa9", raw[] = "\xff\x80";
        const char *const args[] = {program, word, raw, ""};
        assert(!spy_set_argv(first, 1, args, 1, args) && !spy_set_argv(first, 3, args + 1, 4, args) && !spy_set_argv(second, 0, NULL, 0, NULL));
        program[0] = 'X';
        spy_collect(first);
        execute(first, "import sys\nassert sys.orig_argv == ['prog', 'caf\\u00e9', '\\udcff\\udc80', '']\n"
                       "assert sys.argv == sys.orig_argv[1:]\nsys.argv.append(sys.argv)\n");
        execute(second, "import sys\nassert sys.argv == [] and sys.orig_argv == []\n");
        execute(unset, "import sys\nassert sys.argv == [] and sys.orig_argv == []\n");
        /* Set later, it changes only a sys not yet imported. */
        assert(!spy_set_argv(second, 1, args, 1, args));
        execute(second, "import sys\nassert sys.argv == []\n");
        spy_context_free(first); spy_context_free(second); spy_context_free(unset);
    }
    /* A trace function sees each pass of a loop in a generic class's body,
     * and in a body a Python __build_class__ passes to the builtin one. */
    SPYContext *traced = spy_context_new();
    assert(traced && !spy_std_init(traced));
    execute(traced, "import sys\nlines = []\ndef tracer(frame, event, arg):\n"
                    "    if frame.f_code.co_name == 'Generic' and event == 'line': lines.append(frame.f_lineno)\n    return tracer\n"
                    "sys.settrace(tracer)\nclass Generic[T]:\n    for i in range(2):\n        pass\nsys.settrace(None)\n"
                    "assert lines == [7, 8, 9, 8, 9, 8], lines\n"
                    "def builder(func, name, *bases): return __build_class__(func, name, *bases)\n"
                    "space = {'__builtins__': dict(vars(__build_class__.__self__), __build_class__=builder), '__name__': 'built'}\n"
                    "lines.clear()\nsys.settrace(tracer)\nexec('class Generic:\\n    for i in range(2):\\n        pass\\n', space)\n"
                    "sys.settrace(None)\nassert lines == [1, 2, 3, 2, 3, 2], lines\n");
    /* While it traces, a call step (a native decorator, a builtin
     * subclass's construction, a generic class) is made in C. */
    execute(traced, "sys.settrace(tracer)\n@staticmethod\ndef s(): return 1\nclass B(bytearray): pass\nb = B(b'ab')\n"
                    "class I(int): pass\ni = I(5)\nclass G[T]: pass\nsys.settrace(None)\n"
                    "assert s() == 1 and s.__func__.__name__ == 's' and b == b'ab' and i == 5 and G.__type_params__[0].__name__ == 'T'\n");
    spy_context_free(traced);
    SPYContext *c = spy_context_new();
    assert(c && !spy_std_init(c));
    Output o = {0};
    spy_set_output(c, output, NULL, &o);
    execute(c, "print('hello', 6 * 7)");
    assert(!strcmp(o.text, "hello 42\n"));
    /* The final value dies after the last statement, before spy_exec returns;
     * a registered sys reports an unraisable error before it is imported. */
    Output errors = {0};
    spy_set_error_output(c, output, NULL, &errors);
    o.len = 0;
    execute(c, "class Last:\n    def __del__(self):\n        print('finalized')\n        1 / 0\nLast()");
    assert(!strcmp(o.text, "finalized\n"));
    assert(strstr(errors.text, "Exception ignored while calling deallocator <function Last.__del__ at ")
           && strstr(errors.text, "ZeroDivisionError: division by zero\n"));
    /* So does a dead generator's close, from its finally or its yield there. */
    o.len = errors.len = 0;
    execute(c, "def g(again):\n    try:\n        yield 1\n    finally:\n        print('closing')\n        if again: yield 2\n        1 / 0\n"
               "x = g(0)\nnext(x)\ndel x\nprint('after')\nx = g(1)\nnext(x)\nx = None\nprint('end')");
    assert(!strcmp(o.text, "closing\nafter\nclosing\nend\n"));
    assert(strstr(errors.text, "Exception ignored while closing generator <generator object g at ")
           && strstr(errors.text, "ZeroDivisionError: division by zero\n") && strstr(errors.text, "RuntimeError: generator ignored GeneratorExit\n"));
    /* Each stream flushes through its own callback. */
    spy_set_error_output(c, output, flush_output, &errors);
    execute(c, "import sys\nsys.stderr.flush()");
    assert(errors.flushes == 1 && !o.flushes);
    spy_set_error_output(c, NULL, NULL, NULL);
    execute(c, "sys.stderr.flush()");
    spy_set_output(c, output, flush_output, &o);
    execute(c, "print(end='', flush=True)");
    assert(o.flushes == 1);
    o.fail_flush = 1;
    assert(spy_exec(c, "print(flush=True)", "flush.py") == -1);
    assert(!strcmp(spy_error_type(c), "OSError"));
    spy_clear_error(c);
    o.fail_flush = 2;
    assert(spy_exec(c, "print(flush=True)", "flush.py") == -1);
    assert(!strcmp(spy_error_type(c), "BrokenPipeError"));
    o.fail_flush = 0;
    spy_clear_error(c);
    /* input() writes its prompt, flushes, and strips the line ending. */
    assert(spy_exec(c, "input()", "input.py") == -1 && !strcmp(spy_error_type(c), "EOFError"));
    const char *lines[] = {"first\n", "second", "bytes", NULL}, **cursor = lines;
    spy_set_input(c, read_line, &cursor);
    o.len = 0; o.flushes = 0;
    execute(c, "assert input('> ') == 'first'\nassert input() == 'second'\n");
    assert(!strcmp(o.text, "> ") && o.flushes == 3);
    assert(spy_exec(c, "input()", "input.py") == -1 && !strcmp(spy_error_message(c), "input reader returned bytes, not str"));
    spy_clear_error(c);
    assert(spy_exec(c, "input()", "input.py") == -1 && !strcmp(spy_error_type(c), "EOFError"));
    spy_set_input(c, NULL, NULL);
    assert(!spy_define(c, "twice", twice, NULL));
    assert(integer(c, spy_eval(c, "twice(21)", "api.py")) == 42);
    /* exit and quit are the host's (PLS-315 19.4), with site's Quitter messages. */
    static const char *const exits[][2] = {
        {"exit(code=3)", "3"}, {"quit(1, 2)", "Quitter.__call__() takes from 1 to 2 positional arguments but 3 were given"},
        {"exit(x=1)", "Quitter.__call__() got an unexpected keyword argument 'x'"},
        {"exit(1, code=2)", "Quitter.__call__() got multiple values for argument 'code'"}};
    for (size_t i = 0; i < sizeof(exits) / sizeof(*exits); i++)
        assert(spy_exec(c, exits[i][0], "exit.py") && !strcmp(spy_error_message(c), exits[i][1]));
    spy_clear_error(c);
    execute(c, "x = 19");
    assert(integer(c, spy_get_global(c, "x")) == 19);
    assert(integer(c, spy_eval(c, "x + 23", "api.py")) == 42);
    /* spy_truth reports a failing __bool__ as -1 with the error pending. */
    execute(c, "class Failing:\n    def __bool__(self): 1 / 0");
    SPYValue *items[3] = {spy_eval(c, "[0]", "api.py"), spy_eval(c, "[]", "api.py"), spy_eval(c, "Failing()", "api.py")};
    assert(spy_truth(c, items[0]) == 1 && spy_truth(c, items[1]) == 0);
    assert(spy_truth(c, items[2]) == -1 && !strcmp(spy_error_type(c), "ZeroDivisionError"));
    spy_clear_error(c);
    for (size_t i = 0; i < 3; i++) spy_release(items[i]);
    /* spy_type names each builtin data type exactly; a subclass instance and
     * every other value are SPY_OBJECT. */
    static const struct { const char *source; SPYType type; } kinds[] = {
        {"None", SPY_NONE}, {"True", SPY_BOOL}, {"1", SPY_INT}, {"1.5", SPY_FLOAT}, {"1j", SPY_COMPLEX},
        {"'s'", SPY_STRING}, {"b's'", SPY_BYTES}, {"bytearray()", SPY_BYTEARRAY}, {"[]", SPY_LIST},
        {"()", SPY_TUPLE}, {"{}", SPY_DICT}, {"frozendict()", SPY_FROZENDICT}, {"set()", SPY_SET},
        {"frozenset()", SPY_FROZENSET}, {"Failing()", SPY_OBJECT}, {"type('I', (int,), {})(1)", SPY_OBJECT},
        {"len", SPY_OBJECT}, {"int", SPY_OBJECT}, {"iter([])", SPY_OBJECT}, {"int.__dict__", SPY_OBJECT}};
    for (size_t i = 0; i < sizeof(kinds) / sizeof(*kinds); i++) {
        SPYValue *v = spy_eval(c, kinds[i].source, "api.py");
        assert(v && spy_type(v) == kinds[i].type);
        spy_release(v);
    }

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
    /* Its except* clauses split what the clause before left, a new group. */
    execute(c, "class Logged(ExceptionGroup):\n    def split(self, condition):\n        splits.append(condition)\n"
               "        return super().split(condition)\nsplits = []\n");
    o.len = 0;
    interactive = spy_eval_interactive(c, "try:\n    raise Logged('g', [ValueError(1)])\nexcept* KeyError:\n    pass\n"
                                          "except* ValueError:\n    len(splits)\n", "stars.py");
    assert(interactive); spy_release(interactive);
    assert(!strcmp(o.text, "1\n"));
    execute(c, "del Logged, splits\n");
    execute(c, "f = None\nC = None\n");
    /* A repr that imports sys sends the default display to sys.stdout. */
    static const char *const late[][2] = {{"", "late\n"}, {"del sys.stdout\n        ", ""}, {"sys.stdout = None\n        ", ""}};
    for (size_t i = 0; i < sizeof(late) / sizeof(*late); i++) {
        SPYContext *fresh = spy_context_new();
        Output shown = {0};
        char source[160];
        assert(fresh && !spy_std_init(fresh));
        spy_set_output(fresh, output, NULL, &shown);
        snprintf(source, sizeof(source), "class Late:\n    def __repr__(self):\n        import sys\n        %sreturn 'late'\nLate()\n", late[i][0]);
        SPYValue *value = spy_eval_interactive(fresh, source, "late.py");
        assert(i == 1 ? !value && !strcmp(spy_error_message(fresh), "lost sys.stdout") : value != NULL);
        assert(!strcmp(shown.text, late[i][1]));
        spy_release(value); spy_context_free(fresh);
    }

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

    /* Cycles made while a program runs are collected as the heap grows, with
     * their finalizers; with no collection limit they wait for spy_collect. */
    static const char cycles[] =
        "class Node:\n    def __init__(self): self.me = self\n"
        "class Mortal(Node):\n    def __del__(self): ended.append(1)\n"
        "ended = []\nfor i in range(100000):\n    Node()\n    if i % 100 == 0: Mortal()\n";
    assert(spy_get_limit(c, SPY_LIMIT_COLLECTION) == 2000);
    execute(c, cycles);
    assert(spy_live_values(c) < 3 * baseline + 6000);
    execute(c, "assert len(ended) > 900, len(ended)\n");
    assert(!spy_set_limit(c, SPY_LIMIT_COLLECTION, 0) && !spy_get_limit(c, SPY_LIMIT_COLLECTION));
    spy_collect(c);
    execute(c, cycles);
    execute(c, "assert not ended\n");
    assert(spy_collect(c) >= 100000);
    assert(!spy_set_limit(c, SPY_LIMIT_COLLECTION, 2000));
    /* A collection due inside a __del__ waits for it to return, then runs
     * the finalizers it finds and frees what they leave: the garbage cycle
     * holding leaf lets go of it before leaf's last name does. */
    execute(c, "class Holder(Node):\n    def __del__(self): ended.append('holder')\n"
               "class Leaf:\n    def __del__(self): ended.append('leaf')\n"
               "class Busy:\n    def __del__(self):\n        junk = [Node() for i in range(100000)]\n        ended.append('busy')\n"
               "ended = []\nleaf = Leaf()\nh = Holder()\nh.leaf = leaf\ndel h\nBusy()\ndel leaf\n"
               "assert ended == ['busy', 'holder', 'leaf'], ended\n");
    execute(c, "del Node, Mortal, Holder, Leaf, Busy, ended, i\n");
    spy_collect(c);
    assert(spy_live_values(c) == baseline);

    /* Tuples of numbers leave the collector's values; one holding a list
     * stays, so a cycle through it is still found. */
    execute(c, "pairs = [(i, i / 2) for i in range(1000)]\n");
    spy_collect(c);
    assert(spy_live_values(c) >= baseline + 2700);
    execute(c, "del pairs\n");
    spy_collect(c);
    size_t unpaired = spy_live_values(c);
    assert(unpaired == baseline);
    execute(c, "holder = []\nlink = (1, holder)\nholder.append(link)\ndel holder, link\n");
    assert(spy_collect(c) >= 2 && spy_live_values(c) == unpaired);

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
    /* A close the host calls runs in C: a generator yielding there ignored GeneratorExit. */
    execute(c, "def stubborn():\n    try: yield 1\n    finally: yield 2\ns = stubborn()\nnext(s)\nclose = s.close\n");
    SPYValue *close = spy_get_global(c, "close");
    assert(!spy_call(c, close, 0, NULL) && !strcmp(spy_error_message(c), "generator ignored GeneratorExit"));
    spy_clear_error(c);
    spy_release(close);
    execute(c, "del s, close, stubborn\n"); spy_collect(c);

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
    assert(spy_exec(c, "import text", "api.py") == -1);
    assert(!strcmp(spy_error_message(c), "module loader returned str, not bytes"));
    spy_clear_error(c);
    /* A loader may register the module it is asked for instead of returning
     * its source: the import initializes it, with no namespace probe. */
    int probes = calls;
    execute(c, "import registered\nassert registered.value == 7 and not hasattr(registered, '__file__')\n");
    execute(c, "import registered");
    assert(calls == probes + 2);

    /* The policy sees each engine event once, with its arguments; a refusal
     * is PermissionError unless the policy raised its own. */
    assert(!spy_policy_check(c, "custom", NULL));
    Policy rules = {"open input import", ""};
    spy_set_policy(c, policy, &rules);
    execute(c, "exec('y = 1')\nassert eval('y + 1') == 2\ncompile(b'z', 'f', 'exec')\nexec(compile('w = 3', 'f', 'exec'))");
    assert(!strcmp(rules.log, "exec/1 exec/1 exec/1 exec/1 "));
    static const char *const refused[][2] = {
        {"open('data.txt')", "open is not allowed by the host policy"},
        {"input('> ')", "input is not allowed by the host policy"},
        {"import other", "import is not allowed by the host policy"}};
    for (size_t i = 0; i < sizeof(refused) / sizeof(*refused); i++) {
        assert(spy_exec(c, refused[i][0], "policy.py") == -1);
        assert(!strcmp(spy_error_type(c), "PermissionError") && !strcmp(spy_error_message(c), refused[i][1]));
    }
    execute(c, "import sample");
    assert(!strcmp(rules.log, "exec/1 exec/1 exec/1 exec/1 open/2 input/1 import/1 "));
    SPYValue *none = spy_none(c), *args = spy_tuple(c, 1, &none);
    assert(spy_policy_check(c, "custom", args) == -1 && !strcmp(spy_error_type(c), "ValueError"));
    spy_clear_error(c);
    spy_release(args); spy_release(none);
    spy_set_policy(c, NULL, NULL);

    /* The suggestion tokenizes the failing lines as tokenize does: numbers,
     * prefixed, escaped and triple-quoted strings, comments, continuations
     * and non-ASCII names before the typo do not hide it. */
    static const char *const typos[] = {
        "x = 0x1F_A + 1e+5 + 2E-3 + 0o17 + 0b1_0 + .5j; improt sample\n",
        "x = rb'a\\'b' + u\"q\" + '''t\nq''' ; improt sample\n",
        "s = f'{1}' + b'\\\\'; improt sample\n",
        "x = (1,\n2) # comment\nimprot sample\n",
        "x = 1 \\\n+ 2; improt sample\n",
        "s = '''a\\\nb'''\nimprot sample\n",
        "caf\xc3\xa9 = 1; improt sample\n",
        "x = Rb\"q\" + tR'q'; improt sample\n",
        "   \n# leading comment\nimprot sample\n",
    };
    for (size_t i = 0; i < sizeof(typos) / sizeof(*typos); i++) {
        assert(spy_exec(c, typos[i], "suggestion.py") == -1);
        if (strcmp(spy_error_display(c), "invalid syntax. Did you mean 'import'?")) {
            fprintf(stderr, "typo %zu: %s\n", i, spy_error_display(c));
            abort();
        }
        spy_clear_error(c);
    }
    /* A message longer than the context keeps is displayed in full. */
    assert(spy_exec(c, "raise ValueError('x' * 300)", "long.py") == -1);
    assert(strlen(spy_error_message(c)) == 255 && strlen(spy_error_display(c)) == 300);
    spy_clear_error(c);
    char long_message[301];
    memset(long_message, 'y', 300); long_message[300] = 0;
    assert(!spy_error(c, "ValueError", long_message) && !spy_error(c, "KeyError", "later"));
    assert(!strcmp(spy_error_type(c), "ValueError") && strlen(spy_error_message(c)) == 255 && !strcmp(spy_error_display(c), long_message));
    spy_clear_error(c);
    /* A raised exception's message is its str(), taken as the error reaches
     * the host: from a Python __str__, by a value operation, or failing. */
    assert(spy_exec(c, "class Loud(Exception):\n"
                       "    def __str__(self): return 'loud ' + 'x' * 300\n"
                       "class Mute(Exception):\n"
                       "    def __str__(self): raise KeyError\n"
                       "class Shown:\n"
                       "    def __str__(self): raise Loud\n"
                       "raise Loud", "lazy.py") == -1);
    assert(!strcmp(spy_error_type(c), "__main__.Loud") && !strncmp(spy_error_message(c), "loud x", 6) && strlen(spy_error_display(c)) == 305);
    spy_clear_error(c);
    SPYValue *raising = spy_eval(c, "Shown()", "lazy.py");
    assert(raising && !spy_str(c, raising) && !strncmp(spy_error_message(c), "loud x", 6));
    spy_clear_error(c);
    assert(spy_exec(c, "raise Mute", "lazy.py") == -1 && !strcmp(spy_error_message(c), "<exception str() failed>"));
    spy_clear_error(c);
    spy_release(raising);

    /* -OO: no asserts, __debug__ False, no docstrings; compile(optimize=-1) inherits it. */
    spy_set_optimize(c, 2);
    execute(c, "def documented():\n    'doc'\n    return 1\nassert 0\n"
               "optimized = (__debug__, documented.__doc__, documented(), eval(compile('__debug__', '', 'eval')))");
    spy_set_optimize(c, 0);
    assert(integer(c, spy_eval(c, "optimized == (False, None, 1, False) and __debug__", "optimize.py")) == 1);
    /* An error raised after a Python callback returned, on the walker or the
     * machine, is at its caller's line; one raised inside it, at its own. */
    const char *callbacks[] = {
        "class W:\n    def __eq__(self, o): return False\n[W(), 2].index(1)\n",
        "class M:\n    def __eq__(self, o):\n        for _ in (): pass\n        return False\n[M(), 2].index(1)\n",
        "class R:\n    def __eq__(self, o):\n        for _ in (): pass\n        raise KeyError(o)\n[R(), 2].index(1)\n",
    };
    const size_t callback_lines[] = {3, 5, 4};
    for (size_t i = 0; i < sizeof callbacks / sizeof *callbacks; i++) {
        assert(spy_exec(c, callbacks[i], "callback.py") == -1);
        assert(spy_error_line(c) == callback_lines[i]);
        spy_clear_error(c);
    }
    spy_set_limit(c, SPY_LIMIT_STEPS, 100);
    assert(spy_exec(c, "while True:\n    pass\n", "loop.py") == -1);
    assert(!strcmp(spy_error_type(c), "RuntimeError"));
    assert(!strcmp(spy_error_filename(c), "loop.py"));
    assert(spy_error_line(c) > 0);
    assert(integer(c, spy_eval(c, "40 + 2", "recovery.py")) == 42);
    /* Calls, loop passes in generators and comprehensions, and source text
     * spend steps; a spent budget fails every handler and finally body. */
    spy_set_limit(c, SPY_LIMIT_STEPS, 1000);
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
    /* With PAUSE set, a spent budget pauses the call at its next step where
     * only Python frames run, keeping the frames of calls, generators,
     * class calls and comprehensions; each spy_resume runs it on with a
     * fresh budget, to the value an unlimited call gets. */
    spy_clear_error(c);
    assert(spy_set_limit(c, SPY_LIMIT_PAUSE, 2) == -1 && !strcmp(spy_error_type(c), "ValueError"));
    spy_clear_error(c);
    assert(!spy_set_limit(c, SPY_LIMIT_PAUSE, 1) && spy_get_limit(c, SPY_LIMIT_PAUSE) == 1);
    assert(!spy_resume(c) && !strcmp(spy_error_message(c), "no call is paused"));
    const char *paused = "def gen(n):\n    for i in range(n): yield i\n"
                         "class P:\n    def __init__(self, v): self.v = v\n"
                         "def work(n):\n    total = 0\n    for i in gen(n):\n        total += P(i).v + sum([j for j in range(3)])\n    return total\n"
                         "result = 0\nfor k in range(50):\n    result += work(100)\nresult";
    int pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, paused, "paused.py"), SPY_STOP_STEPS, &pauses)) == 262500 && pauses > 20);
    assert(!spy_paused(c) && !spy_stopped(c));
    /* Other calls run while one is paused; they stop rather than pause. */
    pauses = 0;
    SPYValue *v = spy_eval(c, "total = 0\nfor i in range(3000): total += i\ntotal", "first.py");
    assert(!v && spy_paused(c));
    assert(integer(c, spy_eval(c, "40 + 2", "between.py")) == 42);
    assert(spy_exec(c, "while True: pass", "between.py") == -1 && spy_stopped(c) == SPY_STOP_STEPS && spy_paused(c));
    spy_clear_error(c);
    assert(integer(c, run_paused(c, v, SPY_STOP_STEPS, &pauses)) == 4498500 && pauses > 1);
    /* A sort's key calls pause; a pause due inside a host function's call
     * back waits for it to return, within one further budget, and a call
     * needing more stops. */
    execute(c, "def slow(x):\n    for i in range(100): pass\n    return x");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "sorted(range(30), key=slow)[-1]", "sorted.py"), SPY_STOP_STEPS, &pauses)) == 29 && pauses > 1);
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "call_back(lambda: sorted(range(15), key=slow))[-1]", "sorted.py"), SPY_STOP_STEPS, &pauses)) == 14 && pauses == 1);
    assert(!spy_eval(c, "call_back(lambda: sorted(range(30), key=slow))", "sorted.py") && !spy_paused(c) && spy_stopped(c) == SPY_STOP_STEPS);
    spy_clear_error(c);
    /* iter() calls a Python __iter__ on the machine (callk), where it pauses. */
    execute(c, "class Slow:\n    def __iter__(self):\n        for i in range(3000): pass\n        return iter([7])");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "next(iter(Slow()))", "iter.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 1);
    /* So does list()'s length hint, a __len__ and then a __length_hint__. */
    execute(c, "class Sized(Slow):\n    def __len__(self):\n        for i in range(3000): pass\n        raise TypeError\n"
               "    def __length_hint__(self):\n        for i in range(3000): pass\n        return 1");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "list(Sized())[0]", "hint.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 2);
    /* str.join lists its iterator so: its __iter__ again and its __len__. */
    execute(c, "calls = []\nclass Own:\n    items = ['a']\n    def __iter__(self):\n        for i in range(3000): pass\n"
               "        calls.append('iter')\n        return self\n"
               "    def __next__(self):\n        if not self.items: raise StopIteration\n        return self.items.pop()\n"
               "    def __len__(self):\n        for i in range(3000): pass\n        calls.append('len')\n        return 1");
    pauses = 0;
    SPYValue *joined = run_paused(c, spy_eval(c, "''.join(Own()) + ' '.join(calls)", "join.py"), SPY_STOP_STEPS, &pauses);
    assert(joined && !strcmp(spy_as_string(c, joined, NULL), "aiter iter len") && pauses > 2);
    spy_release(joined);
    /* and and or call a Python __bool__ on the machine too; the if that
     * the jump lands on takes the same truth, calling it once. */
    execute(c, "tested = []\nclass Slow:\n    def __bool__(self):\n        for i in range(3000): pass\n"
               "        tested.append(1)\n        return False\n"
               "def shorted():\n    if Slow() and 1: return 0\n    return 7 + len(tested)");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "shorted()", "short.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 1);
    /* set() and frozenset() of a list, and a set display's starred list,
     * call a Python __hash__ on the machine. */
    execute(c, "class Hashed:\n    def __hash__(self):\n        for i in range(3000): pass\n        return 7");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(set([Hashed(), 1])) + len(frozenset((Hashed(),))) + len({*[Hashed()]})", "hashed.py"),
                                 SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So do dict.fromkeys and set.update of a list or a tuple. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(dict.fromkeys([Hashed(), 1])) + len(dict.fromkeys((Hashed(),), 0))", "fromkeys.py"),
                                 SPY_STOP_STEPS, &pauses)) == 3 && pauses > 1);
    execute(c, "updated = {1}");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "updated.update([Hashed()]) or len(updated)", "update.py"), SPY_STOP_STEPS, &pauses)) == 2 &&
           pauses > 0);
    /* Their lookups call a Python __eq__ of a key of the same hash there too. */
    execute(c, "class Alike:\n    def __hash__(self): return 3\n"
               "    def __eq__(self, other):\n        for i in range(3000): pass\n        return True");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(set([Alike(), Alike()])) + len(dict.fromkeys((Alike(), Alike())))", "alike.py"),
                                 SPY_STOP_STEPS, &pauses)) == 2 && pauses > 1);
    /* So do a dict's get and pop and a set's discard. */
    execute(c, "kept = {Alike()}");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "{Alike(): 2}.get(Alike()) + {Alike(): 3}.pop(Alike()) + (kept.discard(Alike()) or len(kept))",
                                             "alike.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 2);
    /* A tuple key hashes its items there, keeping its hash. */
    execute(c, "class Spun:\n    def __hash__(self):\n        for i in range(3000): pass\n        return 4\npair = (1, (Spun(),))");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "{pair: 2}[pair] + {}.get((Spun(), 2), 1)", "tuple.py"),
                                 SPY_STOP_STEPS, &pauses)) == 3 && pauses > 1);
    /* So does hash() of a tuple. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "hash((Spun(), (1, Spun()))) == hash((4, (1, 4)))", "hash.py"), SPY_STOP_STEPS, &pauses)) == 1 &&
           pauses > 1);
    /* And a set or dict.fromkeys of tuples. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(set([(Spun(),), (1, Spun())])) + len(dict.fromkeys([(Spun(), 2)]))", "tuples.py"),
                                 SPY_STOP_STEPS, &pauses)) == 3 && pauses > 2);
    /* A tuple key equal to a stored one compares their items there, its
     * hash just computed or kept. */
    execute(c, "keyed = {(Alike(), 1): 2}\nseen = (Alike(), 1)\nhash(seen)");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "keyed[(Alike(), 1)] + keyed.get((Alike(), 1)) + keyed[seen] + ((Alike(),) in {(Alike(),)})",
                                             "pairs.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 3);
    /* So does a set or dict.fromkeys of equal tuples. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(set([(Alike(),), (Alike(),)])) + len(dict.fromkeys([(1, (Alike(),)), (1, (Alike(),))]))",
                                             "built.py"), SPY_STOP_STEPS, &pauses)) == 2 && pauses > 1);
    /* And a tuple whose hash is kept. */
    execute(c, "held = (Alike(),)\nhash(held)");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "{(Alike(),): 1}.get(held) + len(set([(Alike(),), held]))", "held.py"), SPY_STOP_STEPS,
                                 &pauses)) == 2 && pauses > 1);
    /* So do dict() and dict.update() of pairs, and set() of a zip. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(dict([(Spun(), 1), (2, 3)])) + len({}.update(zip([Spun()], [4])) or 'a') + len(set(zip([Spun()])))", "pairs.py"),
                                 SPY_STOP_STEPS, &pauses)) == 4 && pauses > 1);
    /* So does map(hash) of tuples. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "list(map(hash, [(Spun(),), (1, (Spun(),))])) == [hash((4,)), hash((1, (4,)))]", "maphash.py"),
                                 SPY_STOP_STEPS, &pauses)) == 1 && pauses > 1);
    /* any() and all() of a list, a tuple or a generator call a Python
     * __bool__ or __len__ on the machine. */
    execute(c, "class Falsy:\n    def __bool__(self):\n        for i in range(3000): pass\n        return False\n"
               "class Empty:\n    def __len__(self):\n        for i in range(3000): pass\n        return 0");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "any([Falsy(), 1]) + all((Empty(),)) + any(x for x in [Falsy()])", "truth.py"),
                                 SPY_STOP_STEPS, &pauses)) == 1 && pauses > 2);
    /* map() of str and filter() of None call a Python __str__ and
     * __bool__ on the machine. */
    execute(c, "class Shown:\n    def __str__(self):\n        for i in range(3000): pass\n        return 'x'\n"
               "    def __bool__(self):\n        for i in range(3000): pass\n        return True\n"
               "    def __repr__(self):\n        for i in range(3000): pass\n        return 'r'");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(list(map(str, [Shown(), Shown()]))) + len(list(filter(None, (Shown(),))))", "mapped.py"),
                                 SPY_STOP_STEPS, &pauses)) == 3 && pauses > 2);
    /* So do zip() and enumerate() of such a map. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(list(zip(map(str, [Shown()] * 3), 'abc'))) + len(dict(enumerate(map(str, [Shown()] * 2))))", "adapted.py"),
                                 SPY_STOP_STEPS, &pauses)) == 5 && pauses > 2);
    /* str % values calls a Python __str__ or __repr__ on the machine. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len('%s' % Shown()) + len('%r%a' % (Shown(), 1)) + len('%(k)s' % {'k': Shown()})", "printf.py"),
                                 SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So do a list's or tuple's items' __repr__. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len('%s' % [Shown()]) + len('%s %r' % ((Shown(), 1), [1, Shown()]))", "printl.py"),
                                 SPY_STOP_STEPS, &pauses)) == 3 + 13 && pauses > 1);
    /* And those of a %= target's. */
    execute(c, "def augmented():\n    t = '%s|%r'\n    t %= ([Shown()], {1: Shown()})\n    return len(t)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "augmented()", "augmented.py"), SPY_STOP_STEPS, &pauses)) == 10 && pauses > 1);
    /* And those of a list or tuple item. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(str([1, [Shown()] * 4])) + len(repr(([Shown()] * 4,)))", "nested.py"),
                                 SPY_STOP_STEPS, &pauses)) == 17 + 15 && pauses > 1);
    /* And those of a dict's keys and values or a set's items. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(repr({1: [Shown()] * 4})) + len(str({Shown()})) + len('%s' % (frozendict({2: Shown()}),))", "mapped.py"),
                                 SPY_STOP_STEPS, &pauses)) == 17 + 3 + 18 && pauses > 1);
    /* A container whose item's native __repr__ removes the rest ends its
     * job at once, nested or a % argument. */
    execute(c, "class Popper(dict):\n    def __repr__(self): inner.pop(); return 'p'");
    assert(integer(c, run_paused(c, spy_eval(c, "len(repr([1, inner := [Popper(), Shown()]])) + len('%s' % ((inner := [Popper(), Shown()]),))",
                                             "popped.py"), SPY_STOP_STEPS, &pauses)) == 8 + 3);
    /* A host function's spy_callk runs a Python callee on the machine,
     * where it pauses, then the continuation, which may call again; a
     * call_back's spy_call could not pause. Every call form reaches it. */
    assert(!spy_define(c, "call_k", call_k, NULL) && !spy_define(c, "twice_k", twice_k, NULL) && !spy_define(c, "caught", caught, NULL) &&
           !spy_define(c, "over_k", over_k, NULL) && !spy_define(c, "double_k", double_k, NULL));
    SPYValue *keyword = spy_native(c, "keyword_k", keyword_k, NULL, NULL);
    assert(keyword && !spy_set_global(c, "keyword_k", keyword));
    spy_release(keyword);
    execute(c, "def slower(x):\n    for i in range(3000): pass\n    return x + 1\n"
               "def raising():\n    for i in range(3000): pass\n    raise ValueError\n"
               "def quick(x): return int(x) + 1");
    static const struct { const char *source; int64_t value; int pauses; } calls_k[] = {
        {"call_k(slower, 1)", 2, 1}, {"call_k(slower, len([1]))", 2, 1}, {"call_k(*[slower, 3])", 4, 1},
        {"keyword_k(slower, x=4)", 5, 1}, {"keyword_k(slower, x=len([1, 2]))", 3, 1}, {"twice_k(slower, 5)", 7, 2},
        {"len(caught(raising))", 10, 1}, {"call_k(len, [1, 2])", 2, 0}, {"call_k(call_back, lambda: call_k(quick, 6))", 7, 0}};
    for (size_t i = 0; i < sizeof(calls_k) / sizeof(*calls_k); i++) {
        pauses = 0; k_runs = 0;
        assert(integer(c, run_paused(c, spy_eval(c, calls_k[i].source, "callk.py"), SPY_STOP_STEPS, &pauses)) == calls_k[i].value);
        assert(calls_k[i].pauses ? pauses >= calls_k[i].pauses : pauses == 0);
    }
    assert(!spy_eval(c, "call_back(lambda: slower(slower(0)))", "back.py") && !spy_paused(c) && spy_stopped(c) == SPY_STOP_STEPS);
    spy_clear_error(c);
    /* The continuation's state lives through a pause and a collection. */
    pauses = 0;
    v = spy_eval(c, "def made():\n    def f(x):\n        for i in range(3000): pass\n        return x * 2\n    return f\ntwice_k(made(), 3)", "kept.py");
    while (!v && spy_paused(c)) { spy_collect(c); pauses++; v = spy_resume(c); }
    assert(integer(c, v) == 12 && pauses > 1);
    /* A value or a second spy_callk over a call left drops the call. */
    k_runs = 0;
    assert(!spy_eval(c, "over_k(slower, 1)", "over.py") && !strcmp(spy_error_message(c), "native function returned a value over its spy_callk"));
    spy_clear_error(c);
    assert(!spy_eval(c, "double_k(slower, 1)", "double.py") &&
           !strcmp(spy_error_message(c), "spy_callk called again before its native function returned") && !k_runs);
    spy_clear_error(c);
    /* Off the machine, spy_callk calls at once. */
    SPYValue *quick = spy_get_global(c, "quick"), *one = spy_int(c, 1);
    k_runs = 0;
    assert(integer(c, spy_callk(c, quick, 1, &one, returned_k, spy_int(c, 9))) == 2 && k_runs == 1);
    assert(integer(c, spy_eval(c, "over_k(len, [1])", "over.py")) == 1);
    /* A value of another context fails; nine arguments are called at once. */
    SPYContext *elsewhere = spy_context_new();
    SPYValue *alien = spy_list(elsewhere);
    assert(!spy_callk(c, quick, 1, &alien, returned_k, NULL) && !strcmp(spy_error_message(c), "value belongs to another context"));
    spy_clear_error(c);
    assert(!spy_callk(c, quick, 1, &one, returned_k, alien) && !strcmp(spy_error_message(c), "value belongs to another context"));
    spy_clear_error(c);
    spy_context_free(elsewhere);
    execute(c, "def count(*items): return int(len(items))");
    assert(integer(c, spy_eval(c, "call_k(count, 1, 2, 3, 4, 5, 6, 7, 8, 9)", "nine.py")) == 9);
    spy_release(quick); spy_release(one);
    /* Parsing and compiling source, and charging a body's length on entry,
     * is work bounded by the source: it pauses after, over as many budgets
     * as it takes, in a long program, function, module and exec. */
    char *longer = malloc(3000 * 16 + 64);
    assert(longer);
    size_t at = (size_t)sprintf(longer, "def longest():\n");
    for (int i = 0; i < 3000; i++) at += (size_t)sprintf(longer + at, "    x%d = 1\n", i);
    sprintf(longer + at, "    return 7\nexec('y = 1\\n' * 3000)\nlongest() + y");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, longer, "longer.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 1);
    /* While a call is paused, another's long source stops it, the paused
     * call staying paused; one that fails to compile leaves no pause due. */
    v = spy_eval(c, "total = 0\nfor i in range(3000): total += i\ntotal", "first.py");
    assert(!v && spy_paused(c) == SPY_STOP_STEPS);
    assert(!spy_eval(c, longer, "longer.py") && spy_stopped(c) == SPY_STOP_STEPS && spy_paused(c) == SPY_STOP_STEPS);
    spy_clear_error(c);
    pauses = 0;
    assert(integer(c, run_paused(c, v, SPY_STOP_STEPS, &pauses)) == 4498500 && pauses > 1);
    longer[at] = 0;
    strcat(longer, "    return 7\n)");
    assert(!spy_eval(c, longer, "broken.py") && !strcmp(spy_error_type(c), "SyntaxError") && !spy_paused(c));
    spy_clear_error(c);
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "total = 0\nfor i in range(3000): total += i\ntotal", "first.py"), SPY_STOP_STEPS, &pauses)) == 4498500 &&
           pauses > 1);
    free(longer);
    /* A comprehension over a list or a name pauses in its body. */
    execute(c, "def comprehend():\n    data = list(range(30))\n    return [slow(x) for x in data][-1] + {slow(x) for x in [1, 2]}.pop()");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "comprehend()", "comprehend.py"), SPY_STOP_STEPS, &pauses)) == 30 && pauses > 1);
    /* So do list(), sum() and sorted() of an instance whose __iter__ or
     * __next__ loops, and sorted() of a generator. */
    execute(c, "class Steps:\n    def __init__(self): self.n = 0\n    def __iter__(self): return self\n"
               "    def __next__(self):\n        self.n = slow(self.n + 1)\n        if self.n > 20: raise StopIteration\n        return self.n\n"
               "class Items:\n    def __iter__(self):\n        for i in range(20): yield slow(i)\n"
               "def consume():\n    return len(list(Steps())) + sum(Items()) + sorted(Items())[-1] + sorted(x for x in Items())[0]");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "consume()", "consume.py"), SPY_STOP_STEPS, &pauses)) == 20 + 190 + 19 && pauses > 3);
    /* So does a call's starred argument of a generator or such an instance. */
    execute(c, "def spread(*items): return len(items)\ndef spreads(): return spread(*Items(), *Steps(), *(x for x in Items()))");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "spreads()", "spread.py"), SPY_STOP_STEPS, &pauses)) == 60 && pauses > 3);
    /* So does in, over a generator or such an instance. */
    execute(c, "def member(): return (19 in Items()) + (21 not in Steps()) + (7 in (x for x in Items()))");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "member()", "member.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 3);
    /* A deletion of a dictionary's item is native, and in over an instance
     * whose __iter__ raises TypeError names the instance's type. */
    execute(c, "class Refusing:\n    def __iter__(self):\n        for i in range(2): pass\n        raise TypeError('no')\n"
               "def refused():\n    d = {1: 2, 3: 4}\n    del d[1]\n    try: 1 in Refusing()\n    except TypeError as e: return len(d), str(e)");
    v = spy_eval(c, "refused() == (1, \"argument of type 'Refusing' is not a container or iterable\")", "refused.py");
    assert(v && spy_truth(c, v) == 1);
    spy_release(v);
    /* A dict key's Python __hash__ pauses in a store, an augmented store
     * and a deletion. */
    execute(c, "class Keyed:\n    def __hash__(self):\n        for i in range(1000): pass\n        return 1\n"
               "def keyed():\n    d, k = {}, Keyed()\n    d[k] = 1\n    d[k] += 1\n    total = d[k]\n    del d[k]\n    return total + len(d)");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "keyed()", "keyed.py"), SPY_STOP_STEPS, &pauses)) == 2 && pauses > 3);
    /* So do a display, a store, an augmented store, a deletion and a
     * lookup in a colliding key's Python __eq__. */
    execute(c, "class Same:\n    def __init__(self, n): self.n = n\n    def __hash__(self):\n        for i in range(1000): pass\n        return 1\n"
               "    def __eq__(self, other):\n        for i in range(1000): pass\n        return self.n == other.n\n"
               "def same():\n    d = {Same(1): 1, Same(2): 2}\n    d[Same(2)] += 10\n    d[Same(3)] = 3\n    del d[Same(1)]\n"
               "    return d[Same(2)] + len(d) + (Same(3) in d)");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "same()", "same.py"), SPY_STOP_STEPS, &pauses)) == 15 && pauses > 3);
    /* So do zip and map of generators, in a loop and in a consumer. */
    execute(c, "def zipped():\n    total = 0\n    for i, x in zip(range(20), (x for x in Items())): total += i + x\n"
               "    return total + sum(map(abs, Items()))");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "zipped()", "zipped.py"), SPY_STOP_STEPS, &pauses)) == 380 + 190 && pauses > 3);
    /* So does map of a callable instance or a bound method. */
    execute(c, "class Doubler:\n    def __call__(self, x): return slow(2 * x)\n    def twice(self, x): return slow(x + x)\n"
               "def mapped():\n    d = Doubler()\n    return sum(map(d, range(30))) + sum(map(d.twice, range(30)))");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "mapped()", "mapped.py"), SPY_STOP_STEPS, &pauses)) == 1740 && pauses > 1);
    /* So does exec of interactive input, displaying its values. */
    execute(c, "def single():\n    exec(compile('for i in range(20): slow(i) and None\\n', 's', 'single'), globals())\n    return 1");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "single()", "single.py"), SPY_STOP_STEPS, &pauses)) == 1 && pauses > 1);
    /* So do sort and max keys that are classes, bound methods or callable instances. */
    execute(c, "class Slow:\n    def __init__(self, v): self.v = slow(v)\n    def __lt__(self, other): return self.v < other.v\n"
               "def keyed():\n    d = Doubler()\n    return sorted(range(20), key=d.twice)[0] + max(range(20), key=d) + sorted(range(20), key=Slow)[5]");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "keyed()", "keyed.py"), SPY_STOP_STEPS, &pauses)) == 24 && pauses > 1);
    /* So do dict.get, dict.setdefault and set.add of a key with a Python __hash__. */
    execute(c, "class Hashed:\n    def __hash__(self):\n        for i in range(3000): pass\n        return 1\n"
               "def hashing():\n    d, s = {}, set()\n    for i in range(20):\n        h = Hashed()\n        d.setdefault(h, i)\n"
               "        s.add(Hashed())\n    return d.get(h) + len(d) + len(s)");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "hashing()", "hashing.py"), SPY_STOP_STEPS, &pauses)) == 59 && pauses > 1);
    /* So do a loop and sum() over a class iterated by its Python __getitem__. */
    execute(c, "class Indexed:\n    def __getitem__(self, i):\n        if i >= 20: raise IndexError(i)\n        return slow(i)\n"
               "def indexed():\n    total = sum(Indexed())\n    for x in Indexed(): total += x\n    return total");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "indexed()", "indexed.py"), SPY_STOP_STEPS, &pauses)) == 380 && pauses > 1);
    /* So does a metaclass's Python __prepare__, also for a body that only assigns. */
    execute(c, "class Prepared(type):\n    @classmethod\n    def __prepare__(m, name, bases):\n        for i in range(3000): pass\n        return {'v': name == 'B'}\n"
               "def prepared():\n    class A(metaclass=Prepared): w = v\n    class B(A): w = v + 1\n    return A.w + B.w");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "prepared()", "prepared.py"), SPY_STOP_STEPS, &pauses)) == 2 && pauses > 1);
    /* So do sorted() and max() with keywords of a generator. */
    execute(c, "def keygen():\n    for i in range(4):\n        for j in range(1000): pass\n        yield i\n"
               "def keyed_source():\n    return sorted(keygen(), reverse=True)[0] + max(keygen(), key=lambda v: -v, default=9)");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "keyed_source()", "keyed_source.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 1);
    /* So does a base's Python __mro_entries__. */
    execute(c, "class Entry:\n    def __mro_entries__(self, bases):\n        for i in range(3000): pass\n        return (int,)\n"
               "def entries():\n    class A(Entry()): x = 1\n    class B(list[int]): y = 2\n    return A(A.x + B.y + len(B([0])))");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "entries()", "entries.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 1);
    /* So does an annotated class body that calls. */
    execute(c, "def annotated():\n    class A:\n        x: int = 1\n        for i in range(3000): y = slow(2)\n"
               "    return A.x + A.y + len(A.__annotations__)");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "annotated()", "annotated.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 1);
    /* So does a generic class's body that calls, and its base's __mro_entries__. */
    execute(c, "def generic():\n    class G[T](Entry()):\n        for i in range(3000): y = slow(2)\n"
               "    return G.y + len(G.__type_params__) + issubclass(G, int)");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "generic()", "generic.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 1);
    /* A __class_getitem__ that cannot take the key raises from the subscript. */
    execute(c, "class Arity:\n    def __class_getitem__(cls): return 1\n"
               "def arity():\n    try: return Arity[slow(0)]\n    except TypeError: return 2");
    assert(integer(c, run_paused(c, spy_eval(c, "arity()", "arity.py"), SPY_STOP_STEPS, &pauses)) == 2);
    /* So do dict() and dict.update() of a mapping with a Python keys() and __getitem__. */
    execute(c, "class Mapped:\n    def keys(self): return [slow(i) for i in range(10)]\n    def __getitem__(self, k): return slow(k)\n"
               "class Generated(Mapped):\n    def keys(self):\n        for i in range(10): yield slow(i)\n"
               "def merged():\n    d = dict(Mapped())\n    d.update(Generated())\n    return sum(d.values()) + len(dict(Generated()))");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "merged()", "merged.py"), SPY_STOP_STEPS, &pauses)) == 55 && pauses > 1);
    /* So does a sort of tuples whose tied items compare by Python __eq__ and __lt__. */
    execute(c, "class Tied:\n    def __init__(self, v): self.v = v\n    def __eq__(self, o): return slow(self.v) == o.v\n"
               "    def __lt__(self, o): return slow(self.v) < o.v\n"
               "def tied():\n    ts = sorted([(0, Tied(i % 3)) for i in range(12)])\n    return sum(k * t[1].v for k, t in enumerate(ts))");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "tied()", "tied.py"), SPY_STOP_STEPS, &pauses)) == 98 && pauses > 1);
    /* So do index, count and remove of an item a call gives. */
    execute(c, "found = [Tied(i) for i in range(20)]");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "found.index(Tied(19)) + found.count(Tied(3)) + len(found.remove(Tied(5)) or found)", "found.py"),
                                 SPY_STOP_STEPS, &pauses)) == 39 && pauses > 2);
    /* A tuple key's item whose __eq__ takes no other raises at its lookup. */
    execute(c, "class Lone:\n    def __hash__(self): return 1\n    def __eq__(self): return True");
    assert(!run_paused(c, spy_eval(c, "{(Lone(),): 1}[(Lone(),)]", "lone.py"), SPY_STOP_STEPS, &pauses) &&
           !strcmp(spy_error_type(c), "TypeError"));
    spy_clear_error(c);
    /* So does == of two dicts whose values compare by them. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "({i: Tied(i) for i in range(60)} == {i: Tied(i) for i in range(60)}) + "
                                             "({1: Tied(1)} != {1: Tied(2)}) * 2", "dicteq.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 2);
    /* So does == of two dicts whose keys compare by them. */
    execute(c, "class Keyed(Tied):\n    def __hash__(self): return self.v % 7\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "({Keyed(i): i for i in range(60)} == {Keyed(i): i for i in range(60)}) + "
                                             "({Keyed(1): 1} != {Keyed(8): 1}) * 2", "dictkeys.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 2);
    /* And such dicts inside lists, or lists inside dicts. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "([{i: Tied(i)} for i in range(30)] == [{i: Tied(i)} for i in range(30)]) + "
                                             "({1: [Tied(i) for i in range(30)]} != {1: [Tied(i) for i in range(30)]}) * 2", "nesteq.py"),
                                 SPY_STOP_STEPS, &pauses)) == 1 && pauses > 2);
    /* So does sorted() of a set, a dict or an iterator of them. */
    execute(c, "class Ranked(Tied):\n    def __hash__(self): return self.v\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "sorted({Ranked(i) for i in range(40)})[-1].v + sorted(dict.fromkeys(Ranked(i) for i in range(6)))[0].v + "
                                             "sorted(iter([Ranked(2), Ranked(1)]))[0].v", "ranked.py"), SPY_STOP_STEPS, &pauses)) == 40 && pauses > 2);
    /* So does ordering tuples whose items compare by them. */
    execute(c, "def ordered():\n    a = tuple(Tied(0) for i in range(12)) + (Tied(1),)\n    b = tuple(Tied(0) for i in range(12)) + (Tied(2),)\n"
               "    return (a < b) + (list(a) > list(b)) * 2 + ((a,) < (b,)) * 4");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "ordered()", "ordered.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 1);
    /* So does x < y when y's class subclasses x's and inherits object's __gt__. */
    execute(c, "class Over:\n    def __lt__(self, o):\n        for i in range(3000): pass\n        return i\nclass Under(Over): pass\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "Over() < Under()", "under.py"), SPY_STOP_STEPS, &pauses)) == 2999 && pauses > 1);
    /* So do set operations, their augmented assignments and comparisons
     * whose elements compare by a Python __eq__. */
    execute(c, "class Keyed:\n    def __init__(self, v): self.v = v\n    def __hash__(self): return self.v % 2\n"
               "    def __eq__(self, o): return slow(self.v) == o.v\n"
               "def operated():\n    a = {Keyed(i) for i in range(8)}\n    b = {Keyed(i) for i in range(4, 12)}\n"
               "    a -= b\n    return len(a | b) + len(a & b) * 100 + len(a ^ b) * 10000 + (a < a | b) * 1000000 + (a == b) * 10000000");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "operated()", "operated.py"), SPY_STOP_STEPS, &pauses)) == 1120012 && pauses > 1);
    /* print() pauses in an instance's __str__, writing in order. */
    execute(c, "class Shown:\n    def __str__(self): return str(slow(7))\n"
               "def show():\n    for i in range(10): print(Shown(), i, Shown()); print(Shown(), sep='-', end='')\n    return 1");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "show()", "show.py"), SPY_STOP_STEPS, &pauses)) == 1 && pauses > 1);
    /* repr(), str(), an f-string and print() of a list or tuple pause in
     * an item's __repr__; a native item's removal, also in ascii(), % or
     * str.format, in a nested list or before a nested spec, or an item's
     * error ends the job. */
    execute(c, "class Item:\n    def __repr__(self): return str(slow(7))\n"
               "class Remover:\n    __repr__ = staticmethod(lambda: (shown.pop(), 'r')[1])\n"
               "class Raiser:\n    def __repr__(self): raise KeyError(slow(1))\n"
               "def reprs():\n    global shown\n    out = []\n"
               "    for i in range(5): out += [repr([Item(), i, Item()]), str((Item(),)), f'{[i, Item()]}']\n"
               "    print([Item(), 'x'], (1, Item()))\n"
               "    shown = [Remover(), Item()]\n    out.append(repr(shown))\n"
               "    shown = [Remover(), Item()]\n    print(shown)\n"
               "    shown = [Remover(), Item()]\n    out.append(ascii(shown))\n"
               "    shown = [Remover(), Item()]\n    out.append(repr([1, shown]))\n"
               "    shown = [Remover(), Item()]\n    out.append(f'{[shown]}')\n"
               "    shown = [Remover(), Item()]\n    out.append('%s' % (shown,))\n"
               "    shown = [Remover(), Item()]\n    out.append('%s' % ([shown],))\n"
               "    shown = [Remover(), Item()]\n    out.append('{}'.format([shown]))\n"
               "    shown = [Remover(), Item()]\n    out.append(ascii((lambda: shown)()))\n"
               "    shown = [Remover(), Item()]\n    out.append('{0!s:>{1}}'.format([shown], 9))\n"
               "    shown = [Remover(), Item()]\n    out.append(f'{[shown]!r:>{9}}')\n"
               "    try: repr([Raiser()])\n    except KeyError: out.append('raised')\n"
               "    return len(''.join(out))");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "reprs()", "reprs.py"), SPY_STOP_STEPS, &pauses)) == 5 * 19 + 3 + 3 + 8 + 5 + 3 + 5 + 5 + 3 + 9 + 9 + 6 && pauses > 1);
    /* getattr() pauses in a property's getter, __getattr__, __getattribute__
     * and a descriptor's __get__; their errors, and arity errors, propagate. */
    execute(c, "class Got:\n    @property\n    def p(self): return slow(3)\n"
               "    def __getattr__(self, name):\n        if name == 'gone': raise AttributeError(slow(name))\n        return slow(4)\n"
               "class Narrow:\n    def __getattr__(self): pass\n"
               "class Guard:\n    def __getattribute__(self, name): return slow(5)\n"
               "class Get:\n    def __get__(self, o, t): return slow(6)\n"
               "class Holder:\n    d = Get()\n    own = 1\n    bad = property(lambda: 1)\n"
               "def got():\n    g, total = Got(), 0\n"
               "    for i in range(30): total += getattr(g, 'p') + getattr(g, 'x') + getattr(Guard(), 'y') + getattr(Holder(), 'd') + getattr(Holder(), 'own')\n"
               "    for name, obj in (('gone', g), ('bad', Holder()), ('z', Narrow()), ('missing', Holder())):\n"
               "        try: getattr(obj, name)\n        except (AttributeError, TypeError): total += 100\n"
               "    return total");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "got()", "got.py"), SPY_STOP_STEPS, &pauses)) == 30 * 19 + 400 && pauses > 3);
    /* So does reading a data descriptor that an instance's own entry shadows. */
    execute(c, "class Shadow:\n    def __get__(self, o, t):\n        for i in range(3000): pass\n        return i\n    def __set__(self, o, v): pass\n"
               "class Shadowed:\n    d = Shadow()\nshadowed = Shadowed()\nshadowed.__dict__['d'] = 0\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "shadowed.d + getattr(shadowed, 'd')", "shadow.py"), SPY_STOP_STEPS, &pauses)) == 5998 && pauses > 1);
    /* So does a __getattribute__ before a __getattr__ its AttributeError calls. */
    execute(c, "class Hooked:\n    def __getattribute__(self, n):\n        for i in range(3000): pass\n        raise AttributeError(n)\n"
               "    def __getattr__(self, n):\n        for i in range(3000): pass\n        return i\nhooked = Hooked()\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "hooked.a + hooked.b", "hooked.py"), SPY_STOP_STEPS, &pauses)) == 5998 && pauses > 3);
    /* So does reading a class's descriptor and its metaclass's property. */
    execute(c, "class Spun(type):\n    @property\n    def p(cls):\n        for i in range(3000): pass\n        return i\n"
               "class Classy(metaclass=Spun):\n    d = Shadow()\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "Classy.d + Classy.p + getattr(Classy, 'd')", "classy.py"), SPY_STOP_STEPS, &pauses)) == 8997 && pauses > 2);
    /* So does raising an exception class, and its cause's, with a Python __init__. */
    execute(c, "class Slow(Exception):\n    def __init__(self):\n        for i in range(3000): pass\n        self.i = i\n"
               "class Cause(Exception):\n    def __init__(self):\n        for i in range(3000): pass\n"
               "def raised():\n    try: raise Slow from Cause\n    except Slow as e: return e.i + isinstance(e.__cause__, Cause)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "raised()", "raised.py"), SPY_STOP_STEPS, &pauses)) == 3000 && pauses > 1);
    execute(c, "def caught():\n    try: yield 0\n    except Slow as e: yield e.i\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "(g := caught(), next(g), g.throw(Slow))[2]", "thrown.py"), SPY_STOP_STEPS, &pauses)) == 2999 && pauses > 0);
    /* So does testing the truth of a builtin subclass's instance, or of a class by its metaclass. */
    execute(c, "class Doubt(list):\n    def __bool__(self):\n        for i in range(3000): pass\n        return False\n"
               "class Veil(type):\n    def __len__(cls):\n        for i in range(3000): pass\n        return 0\n"
               "class Hidden(metaclass=Veil): pass\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "(not Doubt([1])) + (not Hidden) + bool(Doubt() or Hidden)", "truth.py"), SPY_STOP_STEPS, &pauses)) == 2 && pauses > 2);
    /* So do their operators, comparisons and in. */
    execute(c, "class Weighed(int):\n    def __add__(self, other):\n        for i in range(3000): pass\n        return i\n"
               "    def __lt__(self, other):\n        for i in range(3000): pass\n        return 1\n"
               "class Scale(type):\n    def __neg__(cls):\n        for i in range(3000): pass\n        return 1\n"
               "    def __contains__(cls, x):\n        for i in range(3000): pass\n        return True\n"
               "class Weights(metaclass=Scale): pass\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "(Weighed(1) + 1) + (Weighed(2) < 3) + -Weights + (5 in Weights)", "weighed.py"), SPY_STOP_STEPS, &pauses)) == 3002 && pauses > 3);
    /* So does the repr of a container of such items. */
    execute(c, "class Shown(str):\n    def __repr__(self):\n        for i in range(3000): pass\n        return 'S'\n"
               "class Lens(type):\n    def __repr__(cls):\n        for i in range(3000): pass\n        return 'L'\n"
               "class Seen(metaclass=Lens): pass\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(repr([Shown('x'), Seen]))", "shown.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 1);
    /* So does isinstance() of a tuple of classes with such a metaclass. */
    execute(c, "class Judge(type):\n    def __instancecheck__(cls, x):\n        for i in range(3000): pass\n        return cls.__name__ == 'B'\n"
               "class A(metaclass=Judge): pass\nclass B(metaclass=Judge): pass\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "isinstance(1, (A, B)) + isinstance(1, (A, str))", "judged.py"), SPY_STOP_STEPS, &pauses)) == 1 && pauses > 2);
    /* So do a slice's parts' __index__. */
    execute(c, "class Mark:\n    def __init__(self, v): self.v = v\n    def __index__(self):\n        for i in range(3000): pass\n        return self.v\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(list(range(10))[Mark(1):Mark(7):Mark(2)])", "marked.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 2);
    /* So do a list store's and deletion's index's __index__. */
    execute(c, "def marks():\n    s = [0, 1, 2]\n    s[Mark(1)] = 5\n    del s[Mark(0)]\n    return s[0]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "marks()", "stored.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 1);
    /* So does a repetition's count's. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len([0] * Mark(4)) + len(Mark(2) * 'ab')", "repeated.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 1);
    /* So do hex()'s and chr()'s. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(hex(Mark(255)) + chr(Mark(65)))", "converted.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 1);
    /* So do range()'s. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(range(Mark(1), Mark(9), Mark(2)))", "ranged.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So do a list's pop()'s and insert()'s. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "[[0, 1, 2].pop(Mark(1)), [3].insert(Mark(0), 4)][0]", "popped.py"), SPY_STOP_STEPS, &pauses)) == 1 && pauses > 1);
    /* So do a str's search bounds. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "'abcabc'.find('c', Mark(3), Mark(6))", "found.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 1);
    /* So do bytes()'s and bytearray()'s. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(bytes(Mark(3)) + bytearray(Mark(2)))", "sized.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 1);
    /* So do a set method's item comparisons by a Python __eq__. */
    execute(c, "class Slow:\n    def __hash__(self): return 0\n"
               "    def __eq__(self, o):\n        for i in range(3000): pass\n        return False\n"
               "def unioned():\n    s = {Slow()}\n    return len(s.union([Slow(), Slow()]))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "unioned()", "unioned.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 1);
    /* So do a set method's several sets and a difference update by a much larger one. */
    execute(c, "def chained():\n    s = {Slow()}\n    t = s.union({Slow()}, {Slow()})\n    s.difference_update({Slow()}, {Slow()})\n"
               "    u = {Slow()}\n    u -= {Slow() for i in range(9)} | {1}\n    return len(t) + len(s) + len(u)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "chained()", "chained.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 3);
    /* So do a set subclass's operators, in-place operators and comparisons. */
    execute(c, "class Sub(set): pass\n"
               "def subs():\n    s = Sub([Slow()])\n    t = {Slow()}\n    u = s | t\n    s &= t\n"
               "    return len(u) + len(s) + (t == Sub([Slow()])) + t.isdisjoint(Sub([Slow()]))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "subs()", "subs.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 3);
    /* So do a set's symmetric difference, its update and issubset of a list. */
    execute(c, "def toggled():\n    s = {Slow()}\n    t = s.symmetric_difference([Slow()])\n    s.symmetric_difference_update([Slow()])\n"
               "    return len(t) + len(s) + s.issubset([Slow()])\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "toggled()", "toggled.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So do a set's operator, in-place and comparison methods called by name. */
    execute(c, "def dunders():\n    s = {Slow()}\n    t = {Slow()}\n    s.__ior__(t)\n"
               "    return len(s.__and__(t)) + len(t.__rsub__(s)) + s.__eq__({Slow(), Slow()}) + set.__le__(t, s)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "dunders()", "dunders.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 3);
    /* So do the __bases__ reads of an abstract issubclass. */
    execute(c, "class Abstract:\n    def __init__(self, b): self.b = b\n"
               "    @property\n    def __bases__(self):\n        for i in range(3000): pass\n        return self.b\n"
               "def abstract():\n    a = Abstract(())\n    return int(issubclass(Abstract((Abstract(()), Abstract((a,)))), a))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "abstract()", "abstract.py"), SPY_STOP_STEPS, &pauses)) == 1 && pauses > 1);
    /* So do a builtin subclass's builds of a generator. */
    execute(c, "class SS(set): pass\nclass DD(dict): pass\nclass LL(list): pass\n"
               "def slows(n):\n    for i in range(n): yield Slow()\n"
               "def built():\n    return len(SS(slows(3))) + len(DD((k, 0) for k in slows(2))) + len(LL(slows(2)))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "built()", "built.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 2);
    /* So do the __init__ calls of a map of a class. */
    execute(c, "class Init:\n    def __init__(self, v):\n        for i in range(3000): pass\n        self.v = v\n"
               "def mapped():\n    return sum(p.v for p in map(Init, [1, 2])) + len(list(map(Init, 'ab')))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "mapped()", "mapped.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 3);
    /* So do a set method's lookups of a dict's keys. */
    execute(c, "def keyed():\n    s = {Slow()}\n    d = {Slow(): 0, Slow(): 1}\n    s.update(d)\n    t = {Slow()}\n"
               "    return len(s) + len(t.difference(d)) + len(t.intersection(d))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "keyed()", "keyed.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 3);
    /* So do an in's comparisons of sequence items. */
    execute(c, "def held():\n    x = (Slow(),)\n    return int(x in [(Slow(),), [x], (Slow(), 1)]) + int([Slow()] not in [[Slow()], (1,)])\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "held()", "held.py"), SPY_STOP_STEPS, &pauses)) == 1 && pauses > 1);
    /* So do a starred builtin call's __bool__ and __str__ calls. */
    execute(c, "class Truthy:\n    def __bool__(self):\n        for i in range(3000): pass\n        return True\n"
               "    def __str__(self):\n        for i in range(3000): pass\n        return 'ab'\n"
               "def starred():\n    a = [Truthy()]\n    return int(any(*[a])) + int(all(*(a,))) + len(str(*a)) + len(format(*[Truthy(), '']))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "starred()", "starred.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 3);
    /* So do the __set_name__ and __init_subclass__ calls of type() and type.__new__. */
    execute(c, "class Named:\n    def __set_name__(self, owner, name):\n        for i in range(3000): pass\n        owner.seen = owner.__dict__.get('seen', 0) + 1\n"
               "class Hooked:\n    def __init_subclass__(cls, **kw):\n        for i in range(3000): pass\n        cls.seen = cls.__dict__.get('seen', 0) + kw['k']\n"
               "class Made(type):\n    def __new__(mcls, name, bases, ns):\n        return super().__new__(mcls, name, bases, ns, k=4)\n"
               "def made():\n    A = type('A', (Hooked,), {'a': Named(), 'b': Named()}, k=1)\n    B = Made('B', (Hooked,), {'a': Named()})\n    return A.seen + B.seen\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "made()", "made.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 4);
    /* So does the getter of a property subclass's instance. */
    execute(c, "class Sub(property): pass\n"
               "class Got:\n    @Sub\n    def v(self):\n        for i in range(3000): pass\n        return 3\n"
               "def got():\n    g = Got()\n    return g.v + getattr(g, 'v')\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "got()", "got.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 1);
    /* So do the calls of a callable iterator's Python function. */
    execute(c, "def ticks():\n    n = [0]\n    def f():\n        for i in range(3000): pass\n        n[0] += 1\n        return n[0]\n    return f\n"
               "def ticked():\n    t = sum(iter(ticks(), 3))\n    for x in iter(ticks(), 2): t += x\n    return t + next(iter(ticks(), 0))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "ticked()", "ticked.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 4);
    /* So does a starred print's __str__ calls. */
    execute(c, "class Shown:\n    def __str__(self):\n        for i in range(3000): pass\n        return 'ab'\n"
               "class Sink:\n    n = 0\n    def write(self, s): Sink.n += len(s)\n"
               "def shown():\n    a = [Shown(), Shown()]\n    print(*a, file=Sink())\n    print(*a, sep='', end='', file=Sink())\n    return Sink.n\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "shown()", "shown.py"), SPY_STOP_STEPS, &pauses)) == 10 && pauses > 3);
    /* So does property.__get__ called for an object. */
    execute(c, "class Wrapped(property):\n    def __get__(self, obj, owner=None):\n        return super().__get__(obj, owner) + 1\n"
               "class Has:\n    @Wrapped\n    def v(self):\n        for i in range(3000): pass\n        return 2\n"
               "def wrapped():\n    h = Has()\n    return h.v + property.__get__(Has.__dict__['v'], h)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "wrapped()", "wrapped.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 1);
    /* So does a throw of a class, its value and a None traceback. */
    execute(c, "class Slowly(Exception):\n    def __init__(self, *a):\n        for i in range(3000): pass\n        super().__init__(*a)\n"
               "def caught():\n    try:\n        yield 0\n    except Slowly as e:\n        yield e.args[0]\n"
               "def thrown():\n    g = caught(); next(g)\n    return g.throw(Slowly, 4, None)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "thrown()", "thrown.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 1);
    /* So do zip and enumerate of a callable iterator of a Python function. */
    execute(c, "def zipped():\n    t = 0\n    for a, b in zip('xyz', iter(ticks(), 3)): t += b\n"
               "    return t + sum(i for i, x in enumerate(iter(ticks(), 2)))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "zipped()", "zipped.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 3);
    /* So does str % of an instance's Python __index__, __int__ or __float__. */
    execute(c, "def percented():\n    return len('%x %d %.1f' % (Listed(), Listed(), Listed()))\n");
    pauses = 0;
    /* So do dir() of a Python __dir__ and int() of a Python __index__. */
    execute(c, "class Listed:\n    def __dir__(self):\n        for i in range(3000): pass\n        return ['b', 'a']\n"
               "    def __index__(self):\n        for i in range(3000): pass\n        return 3\n"
               "def listed():\n    return len(dir(Listed())) + int(Listed()) + int(float(Listed()))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "listed()", "listed.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 2);
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "percented()", "percented.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 2);
    /* And bytes % of a Python __index__ and __bytes__. */
    execute(c, "class Byted:\n    def __bytes__(self):\n        for i in range(3000): pass\n        return b'ab'\n"
               "def byted():\n    return len(b'%x%c%s' % (Listed(), Listed(), Byted()))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "byted()", "byted.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So does str.format of a conversion's Python __repr__ or __str__. */
    execute(c, "class Shown:\n    def __repr__(self):\n        for i in range(3000): pass\n        return 'ab'\n"
               "    __str__ = __repr__\n"
               "def shown():\n    return len('{!r}{!s:>3}{!a}'.format(Shown(), Shown(), Shown()))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "shown()", "shown.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 2);
    /* And with a nested spec after the conversion. */
    execute(c, "def nested():\n    return len('{!r:{}}{!s:>{}}'.format(Shown(), 4, Shown(), 5))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "nested()", "nested.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 2);
    /* So do the Python __index__ of a multi-dimensional memoryview's tuple key. */
    execute(c, "class Cell:\n    def __index__(self):\n        for i in range(3000): pass\n        return 1\n"
               "def gridded():\n    m = memoryview(bytearray(6)).cast('B', (2, 3))\n    m[Cell(), Cell()] = 4\n"
               "    return m[Cell(), 1] + m[1, Cell()]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "gridded()", "gridded.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 3);
    /* And a container field's items' Python __repr__. */
    execute(c, "def contained():\n    return len('{}{!r:>5}{k}'.format([Shown()], (Shown(),), k={Shown()}))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "contained()", "contained.py"), SPY_STOP_STEPS, &pauses)) == 13 && pauses > 2);
    /* And bytearray % of a Python __index__ and __bytes__, the format
     * exported until the job ends. */
    execute(c, "def arrayed():\n    b = bytearray(b'%x%c%s')\n    t = b % (Listed(), Listed(), Byted())\n"
               "    b.append(1)\n    return len(t) + len(b)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "arrayed()", "arrayed.py"), SPY_STOP_STEPS, &pauses)) == 11 && pauses > 2);
    /* And a container field's items' Python __repr__ before a nested spec. */
    execute(c, "def spanned():\n    return len('{!r:>{}}{:{}}'.format([Shown()], 6, (Shown(),), ''))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "spanned()", "spanned.py"), SPY_STOP_STEPS, &pauses)) == 11 && pauses > 2);
    /* And raise of a class, and its cause, whose metaclass has a Python __call__. */
    execute(c, "class Called(type):\n    def __call__(cls, *a):\n        for i in range(3000): pass\n        return super().__call__(*a)\n"
               "class Metaraised(Exception, metaclass=Called): pass\n"
               "def metaraised():\n    try: raise Metaraised from Metaraised\n"
               "    except Metaraised as e: return 7 if type(e.__cause__) is Metaraised else 0\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "metaraised()", "metaraised.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 2);
    /* And super().__call__ in a metaclass's __call__, of a Python __new__ and __init__. */
    execute(c, "class Supered(metaclass=Called):\n    def __new__(cls, *a):\n        for i in range(3000): pass\n        return super().__new__(cls)\n"
               "    def __init__(self, a, b):\n        for i in range(3000): pass\n        self.v = a + b\n"
               "def supered():\n    return Supered(3, 4).v + Supered(*(1, 1)).v\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "supered()", "supered.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 3);
    /* And map() of a class's Python __new__ and __init__, and a method call of one a getter reads. */
    execute(c, "class Newed:\n    def __new__(cls, *a):\n        for i in range(3000): pass\n        return super().__new__(cls)\n"
               "    def __init__(self, a):\n        for i in range(3000): pass\n        self.v = a\n"
               "class Holds:\n    @property\n    def made(self): return Newed\n"
               "def newed():\n    return sum(n.v for n in map(Newed, [1, 2])) + Holds().made(4).v\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "newed()", "newed.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 3);
    /* So does such a call of a class whose Python __new__ makes a
     * subclass's instance, whose __init__, list's or one that is no
     * function, must return None. */
    execute(c, "class InitCall:\n    def __call__(self, *a): return a[0] or None\n"
               "class NewK:\n    def __new__(cls, v):\n        for i in range(3000): pass\n"
               "        return list.__new__(ListK) if isinstance(v, list) else object.__new__(InitK)\n"
               "    def __init__(self, v):\n        for i in range(3000): pass\n"
               "class InitK(NewK):\n    __init__ = InitCall()\n"
               "class ListK(NewK, list):\n    __init__ = list.__init__\n"
               "class HoldsK:\n    @property\n    def made(self): return NewK\n"
               "def newk(v):\n    return len(HoldsK().made([1, 2])) + len(str(HoldsK().made(v)))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "newk(0) > 2", "newk.py"), SPY_STOP_STEPS, &pauses)) == 1 && pauses > 1);
    assert(!run_paused(c, spy_eval(c, "newk(1)", "newk.py"), SPY_STOP_STEPS, &pauses) &&
           !strcmp(spy_error_message(c), "__init__() should return None, not 'int'"));
    spy_clear_error(c);
    /* So does a class body's load of a name by its namespace's Python __getitem__. */
    execute(c, "class Loads(dict):\n    def __getitem__(self, k):\n        for i in range(3000): pass\n        return dict.__getitem__(self, k)\n"
               "class LoadMeta(type):\n    @classmethod\n    def __prepare__(m, n, b): return Loads()\n"
               "def loaded():\n    class K(metaclass=LoadMeta):\n        a = 4\n        b = a + a\n    return K.b\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "loaded()", "loaded.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 2);
    /* So does type.__call__ called unbound with a class. */
    execute(c, "class Unbound(type):\n    def __call__(cls, *a): return type.__call__(cls, *a)\n"
               "class Made(metaclass=Unbound):\n    def __init__(self, v):\n        for i in range(3000): pass\n        self.v = v\n"
               "def unbound():\n    return Made(4).v + type.__call__(Made, 5).v\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "unbound()", "unbound.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 2);
    /* So does a generator's throw of a class, a value and a traceback. */
    execute(c, "class Traced(Exception):\n    def __init__(self, *a):\n        for i in range(3000): pass\n        super().__init__(*a)\n"
               "def traced_gen():\n    try: yield 0\n    except Traced as e:\n        for i in range(3000): pass\n"
               "        yield e.args[0] + (e.__traceback__.tb_next is tb)\n"
               "try: raise ValueError\nexcept ValueError as e: tb = e.__traceback__\n"
               "def traced():\n    g = traced_gen(); next(g)\n    return g.throw(Traced, 6, tb)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "traced()", "traced.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 2);
    /* So does a class body's type statement, stored by its namespace's
     * Python __setitem__ after its type parameters are made. */
    execute(c, "class TypeStore(dict):\n    def __setitem__(self, k, v):\n        for i in range(3000): pass\n"
               "        dict.__setitem__(self, k, v)\n"
               "class TypeMeta(type):\n    @classmethod\n    def __prepare__(m, n, b): return TypeStore()\n"
               "def generics():\n    class K(metaclass=TypeMeta):\n        type A[T, *U, **V] = int\n"
               "    return len(K.A.__type_params__) + len(repr(K.A))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "generics()", "generics.py"), SPY_STOP_STEPS, &pauses)) == 24 && pauses > 2);
    /* So does dir() of a generator __dir__, listed and sorted. */
    execute(c, "class Listed:\n    def __dir__(self):\n        for n in 'cab':\n            for i in range(3000): pass\n"
               "            yield n\n"
               "def listed():\n    return len(''.join(dir(Listed())) + ''.join(dir(Listed())))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "listed()", "listed.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 2);
    /* So do a test and a chain of a comparison whose result has a Python __bool__ or __len__. */
    execute(c, "class Held:\n    def __bool__(self):\n        for i in range(3000): pass\n        return True\n"
               "    def __len__(self):\n        for i in range(3000): pass\n        return 0\n"
               "class Less:\n    def __lt__(self, o): return Held()\n"
               "class Sized:\n    def __len__(self):\n        for i in range(3000): pass\n        return 2\n"
               "class Small:\n    def __lt__(self, o): return Sized()\n"
               "def tested():\n    t = 0\n    if Less() < 1: t += 1\n    if Less() < 1 < 2: t += 2\n    while Small() < 1 < 2 and t < 4: t += 1\n    return t\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "tested()", "tested.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So do isinstance() of a nested tuple and the truth of a check's result. */
    execute(c, "class Checked(type):\n    def __instancecheck__(cls, x):\n        for i in range(3000): pass\n        return Held()\n"
               "class Kept(metaclass=Checked): pass\n"
               "def checked():\n    return isinstance(1, ((str, (Kept,)),)) + isinstance(1, Kept) + issubclass(int, ((int,),))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "checked()", "checked.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 3);
    /* So do exec()'s and eval()'s loads through a locals mapping's Python __getitem__. */
    execute(c, "class Mapped(dict):\n    def __getitem__(self, k):\n        for i in range(3000): pass\n        return dict.__getitem__(self, k)\n"
               "def mapped():\n    m = Mapped(a=1)\n    exec('b = a + a', {}, m)\n    return eval('a + b', {}, m)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "mapped()", "mapped.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 3);
    /* So does a slice's store of a generator's items. */
    execute(c, "def slowly():\n    for k in range(2):\n        for i in range(3000): pass\n        yield k\n"
               "def sliced():\n    a = [0, 1, 2, 3]\n    a[1:3] = slowly()\n    a[::2] = slowly()\n    return len(a) + a[2]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "sliced()", "sliced.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 3);
    /* So do sorted() and max() by a builtin key of a Python __len__. */
    execute(c, "def keyed():\n    s = sorted([Sized(), [1]], key=len)\n    return len(s) + len(max([[], Sized()], key=len))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "keyed()", "keyed.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 3);
    /* So does filter() of a builtin by a Python __len__. */
    execute(c, "def filtered():\n    return len(list(filter(len, [Sized(), '', Sized()]))) + sum(1 for x in filter(len, [Sized()]))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "filtered()", "filtered.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 2);
    /* So do sorted() and max() by a builtin key over an iterator. */
    execute(c, "def iterated():\n    return len(sorted(iter([Sized(), [1]]), key=len)) + len(max(iter((Sized(),)), key=len))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "iterated()", "iterated.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So does a callable iterator's Python __eq__ of its sentinel. */
    execute(c, "class Stop:\n    def __eq__(self, other):\n        for i in range(3000): pass\n        return other == 3\n"
               "def sentinels():\n    it = iter([1, 2, 3, 4])\n    return sum(iter(lambda: next(it), Stop()))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "sentinels()", "sentinels.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 2);
    /* So does a zip of a callable iterator. */
    execute(c, "def zipped():\n    it = iter([1, 2, 3, 4])\n    return sum(a for a, b in zip(iter(lambda: next(it), Stop()), 'abcd'))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "zipped()", "zipped.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 2);
    /* So do a list's slice store and deletion by a Python __index__. */
    execute(c, "class Part:\n    def __index__(self):\n        for i in range(3000): pass\n        return 1\n"
               "def spliced():\n    a = [0, 1, 2, 3]\n    a[Part():3] = [7]\n    del a[:Part()]\n    return len(a) + a[0]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "spliced()", "spliced.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 2);
    /* So does a list's += of a generator. */
    execute(c, "def augmented():\n    a = [1]\n    a += slowly()\n    return len(a)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "augmented()", "augmented.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 2);
    /* So does a slice store of a generator by a Python __index__. */
    execute(c, "def splicegen():\n    a = [0, 1, 2, 3]\n    a[Part():3] = slowly()\n    return len(a) + a[2]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "splicegen()", "splicegen.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 2);
    /* So does a base's property read through super(). */
    execute(c, "class Based:\n    @property\n    def p(self):\n        for i in range(3000): pass\n        return 4\n"
               "class Derived(Based):\n    @property\n    def p(self): return super().p + getattr(super(), 'p')\n"
               "def supered():\n    return Derived().p\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "supered()", "supered.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 2);
    /* So does a generator a sum resumes in its yield from of a list. */
    execute(c, "def delegated():\n    yield 1\n    yield from [2]\n    for i in range(3000): pass\n    yield 3\n"
               "def resumed():\n    return sum(delegated())\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "resumed()", "resumed.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 2);
    /* So does a yield from of a map of a Python function. */
    execute(c, "def doubled(x):\n    for i in range(3000): pass\n    return 2 * x\n"
               "def mapped():\n    yield from map(doubled, [1, 2])\n"
               "def remapped():\n    return sum(mapped())\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "remapped()", "remapped.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 2);
    /* So does a throw into a generator in a yield from of a list. */
    execute(c, "def caught():\n    try:\n        yield from [1, 2]\n    except KeyError:\n        for i in range(3000): pass\n        yield 7\n"
               "def thrown():\n    g = caught()\n    next(g)\n    return g.throw(KeyError())\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "thrown()", "thrown.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 2);
    /* So does closing a dropped generator in a yield from of a list. */
    execute(c, "closings = []\ndef dropping():\n    try:\n        yield from [1, 2]\n    finally:\n        for i in range(3000): pass\n        closings.append(4)\n"
               "def dropped():\n    g = dropping()\n    next(g)\n    del g\n    return closings[0]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "dropped()", "dropped.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So does an exception class's __init__ a throw into it makes. */
    execute(c, "class Made(Exception):\n    def __init__(self, n):\n        for i in range(3000): pass\n        self.n = n\n"
               "def made():\n    try:\n        yield from [1, 2]\n    except Made as e:\n        yield e.n\n"
               "def thrownclass():\n    g = made()\n    next(g)\n    return g.throw(Made, 8)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "thrownclass()", "thrownclass.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 2);
    /* So does an instance's throw a class thrown into its yield from reaches. */
    execute(c, "class Catcher:\n    def __iter__(self): return self\n    def __next__(self): return 1\n"
               "    def throw(self, kind):\n        for i in range(3000): pass\n        return 9 if kind is KeyError else 0\n"
               "def catching():\n    yield from Catcher()\n"
               "def classthrown():\n    g = catching()\n    next(g)\n    return g.throw(KeyError)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "classthrown()", "classthrown.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 2);
    /* So do the Python __eq__ and __len__ a match statement's patterns call. */
    execute(c, "class Equal:\n    def __eq__(self, o):\n        for i in range(3000): pass\n        return o == 1\n"
               "class Sized(list):\n    def __len__(self):\n        for i in range(3000): pass\n        return 2\n"
               "class Values:\n    one = Equal()\n"
               "def matched():\n    match Sized([4, 6]):\n        case Values.one: return 0\n        case [a, b]: return a + b\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "matched()", "matched.py"), SPY_STOP_STEPS, &pauses)) == 10 && pauses > 2);
    /* So does the reflected comparison of a builtin's subclass. */
    execute(c, "class Reflected(set):\n    def __eq__(self, o):\n        for i in range(3000): pass\n        return 11\n"
               "def reflected():\n    return {0} == Reflected({1})\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "reflected()", "reflected.py"), SPY_STOP_STEPS, &pauses)) == 11 && pauses > 2);
    /* So does the Python __hash__ of a builtin's subclass. */
    execute(c, "class Hashed(str):\n    def __hash__(self):\n        for i in range(3000): pass\n        return 3\n"
               "def hashed():\n    return {Hashed('k'): 12}[Hashed('k')]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "hashed()", "hashed.py"), SPY_STOP_STEPS, &pauses)) == 12 && pauses > 2);
    /* So does the keys function an instance holds, merged by dict(). */
    execute(c, "class Held:\n    def __init__(self):\n        def keys():\n            for i in range(3000): pass\n            return [19]\n"
               "        self.keys = keys\n    def __getitem__(self, k): return k\n"
               "def held():\n    return dict(Held())[19]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "held()", "held.py"), SPY_STOP_STEPS, &pauses)) == 19 && pauses > 2);
    /* So does a sort key's reflected __gt__ after its __lt__ declines. */
    execute(c, "class Declined:\n    def __init__(self, v): self.v = v\n    def __lt__(self, o): return NotImplemented\n"
               "    def __gt__(self, o):\n        for i in range(3000): pass\n        return self.v > o.v\n"
               "def declined():\n    return sorted([Declined(2), Declined(1), Declined(3)])[0].v\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "declined()", "declined.py"), SPY_STOP_STEPS, &pauses)) == 1 && pauses > 2);
    /* So does a dict subclass's __missing__ of an absent tuple key. */
    execute(c, "class Absent(dict):\n    def __missing__(self, k):\n        for i in range(3000): pass\n        return len(k)\n"
               "def absent():\n    return Absent()[(1, 2)] + Absent()[((1,), 'a', 3)]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "absent()", "absent.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 2);
    /* So does print's read of a file's write through a Python __getattr__. */
    execute(c, "class Fetching:\n    n = 0\n    def __getattr__(self, name):\n        for i in range(3000): pass\n"
               "        return self.count\n    def count(self, t): Fetching.n += len(t)\n"
               "def fetching():\n    print('ab', 3, file=Fetching(), flush=False)\n    return Fetching.n\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "fetching()", "fetching.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 3);
    /* So does a zip's generator after a str. */
    execute(c, "def slow_items(n):\n    for i in range(n):\n        for j in range(3000): pass\n        yield i\n"
               "def zipped_text():\n    return len(list(zip('abc', slow_items(3)))) + len(dict(zip(b'xy', slow_items(2))))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "zipped_text()", "zipped_text.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 3);
    /* So does a call's ** of a mapping's Python keys and __getitem__. */
    execute(c, "class Spread:\n    def keys(self):\n        for i in range(3000): pass\n        return ['a', 'b']\n"
               "    def __getitem__(self, k):\n        for i in range(3000): pass\n        return len(k) * 10\n"
               "def spread(**kw): return kw['a'] + kw['b'] + len(kw)\n"
               "def spreading():\n    return spread(**Spread())\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "spreading()", "spreading.py"), SPY_STOP_STEPS, &pauses)) == 22 && pauses > 2);
    /* So does a stored key's Python __eq__ that a builtin key's lookup calls. */
    execute(c, "class Stored(int):\n    __hash__ = int.__hash__\n    def __eq__(self, o):\n        for i in range(3000): pass\n"
               "        return int(self) == o\n"
               "def stored():\n    d = {Stored(4): 5}\n    d[4] = 6\n    return d[4] + (4 in d) + (4 in {Stored(4)}) + len({Stored(4), 4})\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "stored()", "stored.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 4);
    /* So does filter()'s Python function over a generator. */
    execute(c, "def odd(x): return x % 2\n"
               "def slow_items_of(n):\n    for i in range(n):\n        for j in range(3000): pass\n        yield i\n"
               "def odd_items():\n    return sum(filter(odd, slow_items_of(6)))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "odd_items()", "odd_items.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 4);
    /* So does str() of an int subclass's Python __repr__, and format()'s with an empty spec. */
    execute(c, "class Shown(int):\n    def __repr__(self):\n        for i in range(3000): pass\n        return 'shown'\n"
               "def shown():\n    return len(str(Shown(1)) + f'{Shown(2)}' + format(Shown(3), '') + '%s' % Shown(4))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "shown()", "shown.py"), SPY_STOP_STEPS, &pauses)) == 20 && pauses > 3);
    /* So does an async generator that its asend's send or next() resumes. */
    execute(c, "async def counting():\n    for i in range(3):\n        for j in range(3000): pass\n        yield i\n"
               "def stepped(op):\n    try: op.send(None)\n    except StopIteration as e: return e.value\n"
               "def asends():\n    g = counting()\n    a = stepped(g.__anext__())\n    b = stepped(g.asend(None))\n"
               "    try: next(g.__anext__())\n    except StopIteration as e: return a + b + e.value + 5\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "asends()", "asends.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 2);
    /* So does the Python __eq__ of an item that bytes or a range is searched for. */
    execute(c, "class Wants:\n    def __eq__(self, other):\n        for i in range(3000): pass\n        return other == b'k'\n"
               "def wanted():\n    return (b'k' in [Wants(), Wants()]) + (range(1) in (Wants(),)) + 3\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "wanted()", "wanted.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 1);
    /* So does a set's, a slice's or a builtin function's. */
    execute(c, "def valued():\n    return ({1} in [Wants()]) + (slice(1) in (Wants(),)) + (len not in [Wants()]) + 6\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "valued()", "valued.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 1);
    /* So does bytes() or bytearray() of an instance's Python __iter__ and __len__, or of a generator. */
    execute(c, "class Byted:\n    def __iter__(self):\n        for i in range(3000): pass\n        return iter([1, 2])\n"
               "    def __len__(self):\n        for i in range(3000): pass\n        return 2\n"
               "def byte_items():\n    for i in range(2):\n        for j in range(3000): pass\n        yield i\n"
               "def byted():\n    return len(bytes(Byted()) + bytearray(Byted()) + bytes(byte_items())) + 3\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "byted()", "byted.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 3);
    /* So does bytearray.extend()'s. */
    execute(c, "def extended():\n    b = bytearray()\n    b.extend(Byted())\n    b.extend(byte_items())\n    return len(b) + 6\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "extended()", "extended.py"), SPY_STOP_STEPS, &pauses)) == 10 && pauses > 2);
    /* So does list.__init__'s, bound or given the list. */
    execute(c, "def inited():\n    l = [9]\n    l.__init__(Byted())\n    k = []\n    list.__init__(k, byte_items())\n"
               "    return len(l) + len(k) + 7\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "inited()", "inited.py"), SPY_STOP_STEPS, &pauses)) == 11 && pauses > 2);
    /* So does bytes.join's, and a loop's bytearray.extend and list.__init__ on a builtin receiver. */
    execute(c, "class Joined:\n    def __iter__(self):\n        for i in range(3000): pass\n        return iter([b'a', b'b'])\n"
               "def joined():\n    n = len(b'-'.join(Joined())) + len(bytes.join(b'', Joined()))\n"
               "    for i in range(2):\n        b = bytearray()\n        b.extend(Byted())\n        [].__init__(Byted())\n        n += len(b)\n"
               "    return n\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "joined()", "joined.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 5);
    /* So does the Python __eq__ of the items an in takes from a generator or a __getitem__ sequence. */
    execute(c, "def eq_items():\n    for i in range(3):\n        yield Wants()\n"
               "class Indexed:\n    def __getitem__(self, i):\n        if i > 1: raise IndexError\n        return Wants()\n"
               "def searched():\n    return (b'k' in eq_items()) + (b'k' in Indexed()) + (b'q' in Indexed()) + 5\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "searched()", "searched.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 2);
    /* So does an in of a list iterator. */
    execute(c, "def iterated():\n    it = iter([1, Wants(), Wants()])\n    return (b'k' in it) + len(list(it)) + 8\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "iterated()", "iterated.py"), SPY_STOP_STEPS, &pauses)) == 10 && pauses > 0);
    /* So does a sequence item's reflected __eq__, after the other's declined. */
    execute(c, "class Declines:\n    def __eq__(self, o): return NotImplemented\n"
               "class Reflects:\n    def __eq__(self, o):\n        for i in range(3000): pass\n        return True\n"
               "def reflected():\n    return ([Declines()] == [Reflects()]) + ({1: Declines()} == {1: Reflects()}) + 9\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "reflected()", "reflected.py"), SPY_STOP_STEPS, &pauses)) == 11 && pauses > 0);
    /* So does the Python __bool__ of a sequence item's __eq__ result. */
    execute(c, "class Truth:\n    def __bool__(self):\n        for i in range(3000): pass\n        return True\n"
               "class Odd:\n    def __eq__(self, o): return Truth()\n"
               "def truths():\n    return ([Odd(), Odd()] == [1, 2]) + ({1: Odd()} == {1: 2}) + 9\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "truths()", "truths.py"), SPY_STOP_STEPS, &pauses)) == 11 && pauses > 1);
    /* And an item's in a search of a list, after the other's declined. */
    execute(c, "def searches():\n    return (Reflects() in [Declines()]) + (1 in [Odd()]) + [Declines(), Odd()].count(Reflects()) + 7\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "searches()", "searches.py"), SPY_STOP_STEPS, &pauses)) == 11 && pauses > 2);
    /* So does the truth of an __eq__ result in a generator's search. */
    execute(c, "def odds():\n    yield 0\n    yield Odd()\n"
               "def generated():\n    return (1 in odds()) + (Odd() in (i for i in [Declines()])) + 9\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "generated()", "generated.py"), SPY_STOP_STEPS, &pauses)) == 11 && pauses > 1);
    /* And of what object's __ne__ and a Python __contains__ returned. */
    execute(c, "class Holds:\n    def __contains__(self, x): return Truth()\n"
               "def results():\n    return (Odd() != 1) + (1 in Holds()) + (1 not in Holds()) + 9\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "results()", "results.py"), SPY_STOP_STEPS, &pauses)) == 10 && pauses > 2);
    /* So do min()'s reflected __gt__ and the truth of its result. */
    execute(c, "class Least:\n    def __init__(self, n): self.n = n\n    def __lt__(self, o): return NotImplemented\n"
               "    def __gt__(self, o):\n        for i in range(3000): pass\n        return Truth()\n"
               "def least():\n    return min([Least(2), Least(1), Least(3)]).n + 9\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "least()", "least.py"), SPY_STOP_STEPS, &pauses)) == 12 && pauses > 1);
    /* And a sort's, ordering a pair by its __lt__ result's __bool__. */
    execute(c, "class Sorts:\n    def __init__(self, n): self.n = n\n    def __lt__(self, o): return Truth()\n"
               "def sorts():\n    return sorted([Sorts(2), Sorts(1)])[0].n + 9\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "sorts()", "sorts.py"), SPY_STOP_STEPS, &pauses)) == 10 && pauses > 0);
    /* And max()'s by a key, the best key's __lt__ reflected. */
    execute(c, "class Keyed:\n    def __init__(self, n): self.n = n\n"
               "    def __lt__(self, o):\n        for i in range(3000): pass\n        return Truth()\n"
               "def keyed():\n    return max([1, 2], key=Keyed) + 9\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "keyed()", "keyed.py"), SPY_STOP_STEPS, &pauses)) == 11 && pauses > 0);
    /* And an in of a dict's values, their Python __eq__ on the machine. */
    execute(c, "def valued_in():\n    return (Reflects() in {1: 2, 3: 4}.values()) + (1 in {5: Odd()}.values()) + 9\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "valued_in()", "valued_in.py"), SPY_STOP_STEPS, &pauses)) == 11 && pauses > 1);
    /* And of a reversed list. */
    execute(c, "def reversed_in():\n    return (Reflects() in reversed([1, 2])) + (1 in reversed((Odd(), 3))) + 9\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "reversed_in()", "reversed_in.py"), SPY_STOP_STEPS, &pauses)) == 11 && pauses > 1);
    /* object.__format__ of an empty spec calls a Python __str__ on the machine. */
    execute(c, "class Formed:\n    def __str__(self):\n        for i in range(3000): pass\n        return 'x'\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(object.__format__(Formed(), '')) + len(object.__format__(Formed(), '') * 2)", "formatted.py"),
                                 SPY_STOP_STEPS, &pauses)) == 3 && pauses > 1);
    /* So does ascii() of a list of such items, their Python __repr__. */
    execute(c, "class Reprs:\n    def __repr__(self):\n        for i in range(3000): pass\n        return '\\xe9'\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(ascii([Reprs(), (Reprs(),)]))", "asciis.py"), SPY_STOP_STEPS, &pauses)) == 15 && pauses > 1);
    /* So does filter()'s iterator's Python __next__. */
    execute(c, "class Slow:\n    def __init__(self): self.n = 0\n    def __iter__(self): return self\n"
               "    def __next__(self):\n        for i in range(3000): pass\n        self.n += 1\n"
               "        if self.n > 3: raise StopIteration\n        return self.n\n"
               "def filtered():\n    return sum(filter(None, Slow())) + 11\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "filtered()", "filtered.py"), SPY_STOP_STEPS, &pauses)) == 17 && pauses > 2);
    /* So does the Python __eq__ of a builtin type's subclass key. */
    execute(c, "class Same(str):\n    __hash__ = str.__hash__\n    def __eq__(self, o):\n        for i in range(3000): pass\n        return str(self) == o\n"
               "def same():\n    return {Same('k'): 16}[Same('k')]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "same()", "same.py"), SPY_STOP_STEPS, &pauses)) == 16 && pauses > 2);
    /* So does a compiled __annotate__'s Python annotation call. */
    execute(c, "def slow(x):\n    for i in range(3000): pass\n    return x\n"
               "def annotated():\n    def f(a: slow(15)): pass\n    return f.__annotations__['a']\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "annotated()", "annotated.py"), SPY_STOP_STEPS, &pauses)) == 15 && pauses > 2);
    /* So does a module's Python __getattr__. */
    execute(c, "def fallback(name):\n    for i in range(3000): pass\n    return len(name)\n"
               "def dynamic():\n    m = type(__build_class__.__self__)('m')\n    m.__getattr__ = fallback\n"
               "    return m.thirteen_long + getattr(m, 'x', 0)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "dynamic()", "dynamic.py"), SPY_STOP_STEPS, &pauses)) == 14 && pauses > 2);
    /* So do ascii() of a Python __repr__ and round() by a Python __index__. */
    execute(c, "class Rounded:\n    def __repr__(self):\n        for i in range(3000): pass\n        return 'ab'\n"
               "    def __index__(self):\n        for i in range(3000): pass\n        return -1\n"
               "def rounded():\n    return len(ascii(Rounded())) + round(1234, Rounded()) + int(round(2.5, Rounded()))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "rounded()", "rounded.py"), SPY_STOP_STEPS, &pauses)) == 1232 && pauses > 2);
    /* So do a module body's annotation names and annotated stores, run with
     * a mapping whose __setitem__ is Python. */
    execute(c, "class Stored(dict):\n    def __setitem__(self, k, v):\n        for i in range(3000): pass\n        dict.__setitem__(self, k, v)\n"
               "def annotated():\n    ns = Stored()\n    exec('x: int = 2\\nif x:\\n    y: str = 3', {}, ns)\n    return len(ns) + ns['x']\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "annotated()", "annotated.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 3);
    /* So does a read of a metaclassed class's __annotations__. */
    execute(c, "def slow_type(t):\n    for i in range(3000): pass\n    return t\nclass Kind(type): pass\n"
               "def metannotated():\n    class Kept(metaclass=Kind):\n        x: slow_type(int)\n        y: slow_type(str)\n"
               "    return len(Kept.__annotations__) + len(Kept.__annotations__)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "metannotated()", "metannotated.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 1);
    /* So do a class body's chained stores and del of a target list through
     * its namespace's Python __setitem__ and __delitem__. */
    execute(c, "class Slots(dict):\n    def __setitem__(self, k, v):\n        for i in range(3000): pass\n        dict.__setitem__(self, k, v)\n"
               "    def __delitem__(self, k):\n        for i in range(3000): pass\n        dict.__delitem__(self, k)\n"
               "class Slotted(type):\n    @classmethod\n    def __prepare__(m, n, b): return Slots()\n"
               "def chained():\n    class K(metaclass=Slotted):\n        a = b = c = 1\n        del a, b\n    return K.c + len([k for k in vars(K) if len(k) == 1])\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "chained()", "chained.py"), SPY_STOP_STEPS, &pauses)) == 2 && pauses > 4);
    /* And a handler's name, stored, then None, then deleted. */
    execute(c, "def handled():\n    class K(metaclass=Slotted):\n        try: 1/0\n        except ZeroDivisionError as e: x = 3\n"
               "    return K.x + ('e' in vars(K))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "handled()", "handled.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 3);
    /* So do an exec()'d module's loop name and del through a locals mapping. */
    execute(c, "def looped():\n    ns = Slots()\n    exec('for i in (1, 2): pass\\nk = 1\\ndel k', {}, ns)\n    return ns['i'] + len(ns)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "looped()", "looped.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 3);
    /* So does a throw of a class and its value into a yield from of a generator. */
    execute(c, "class Slowed(Exception):\n    def __init__(self, *a):\n        for i in range(3000): pass\n        super().__init__(*a)\n"
               "def slowed():\n    try: yield 0\n    except Slowed as e: yield e.args[0]\n"
               "def delegating():\n    yield from slowed()\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "(g := delegating(), next(g), g.throw(Slowed, 5))[2]", "delegated.py"), SPY_STOP_STEPS, &pauses)) == 5 &&
           pauses > 1);
    /* So does such a loop's name of a generator's items. */
    execute(c, "def generated():\n    ns = Slots()\n    exec('for i in (x for x in (1, 2)): pass', {}, ns)\n    return ns['i']\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "generated()", "generated.py"), SPY_STOP_STEPS, &pauses)) == 2 && pauses > 1);
    /* So does a class body's handler left by an exception, which deletes its name. */
    execute(c, "deleted = []\nclass Gone(Slots):\n    def __delitem__(self, k):\n        for i in range(3000): pass\n"
               "        deleted.append(k)\n        dict.__delitem__(self, k)\n"
               "class Going(type):\n    @classmethod\n    def __prepare__(m, n, b): return Gone()\n"
               "def raised():\n    try:\n        class K(metaclass=Going):\n            try: 1/0\n"
               "            except ZeroDivisionError as e: raise KeyError\n    except KeyError: return deleted\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(raised())", "raised.py"), SPY_STOP_STEPS, &pauses)) == 1 && pauses > 2);
    /* So does dict.__getitem__ of a dict subclass's absent key, unbound or through super(), calling its Python __missing__. */
    execute(c, "class Absent(dict):\n    def __missing__(self, k):\n        for i in range(3000): pass\n        return i\n"
               "class Over(Absent):\n    def __getitem__(self, k): return super().__getitem__(k) + 1\n"
               "def missed():\n    d = Over()\n    return d['a'] + dict.__getitem__(d, 'b') + d.__getitem__('c')\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "missed()", "missed.py"), SPY_STOP_STEPS, &pauses)) == 8999 && pauses > 2);
    /* So do a dict subclass's subscript, store and deletion hashing a key by its Python __hash__. */
    execute(c, "class Hashy:\n    def __init__(self, n): self.n = n\n    def __hash__(self):\n        for i in range(3000): pass\n        return self.n\n"
               "def subhashed():\n    d, k = Absent(), Hashy(1)\n    d[k] = 1\n    v = d[k] + d[Hashy(2)]\n    del d[k]\n    return v + len(d)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "subhashed()", "subhashed.py"), SPY_STOP_STEPS, &pauses)) == 3000 && pauses > 4);
    /* So does a throw of the GeneratorExit class into a yield from, closing its delegates. */
    execute(c, "def closing():\n    try: yield 1\n    finally:\n        for i in range(3000): pass\n"
               "def exiting():\n    g = (lambda: (yield from closing()))()\n    next(g)\n"
               "    try: g.throw(GeneratorExit)\n    except GeneratorExit: return 5\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "exiting()", "exiting.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 1);
    /* So does a read through a descriptor whose __get__ is a staticmethod. */
    execute(c, "def slow_get(d, instance, owner):\n    for i in range(3000): pass\n    return i\n"
               "class StaticGet:\n    __get__ = staticmethod(slow_get)\n"
               "class Got:\n    x = StaticGet()\n"
               "def statics():\n    return Got().x + Got.x\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "statics()", "statics.py"), SPY_STOP_STEPS, &pauses)) == 5998 && pauses > 2);
    /* So does an asend's throw into its async generator at a yield. */
    execute(c, "async def athrown():\n    try: yield 1\n    except KeyError:\n        for i in range(3000): pass\n        yield i\n"
               "def asend_thrown():\n    g = athrown()\n    try: next(g.__anext__())\n    except StopIteration: pass\n"
               "    try: g.__anext__().throw(KeyError)\n    except StopIteration as e: return e.value\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "asend_thrown()", "asend_thrown.py"), SPY_STOP_STEPS, &pauses)) == 2999 && pauses > 1);
    /* So do an athrow's and an aclose's first send, throwing into it at a yield. */
    execute(c, "async def athrowing():\n    try: yield 1\n    except BaseException:\n        for i in range(3000): pass\n"
               "        if i: raise\n"
               "def athrows():\n    out = 0\n    for e in (KeyError, None):\n        g = athrowing()\n"
               "        try: next(g.__anext__())\n        except StopIteration: pass\n"
               "        try: (g.athrow(e) if e else g.aclose()).send(None)\n        except (KeyError, StopIteration): out += 1\n"
               "    return out\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "athrows()", "athrows.py"), SPY_STOP_STEPS, &pauses)) == 2 && pauses > 2);
    /* So does memoryview() of an object with a Python __buffer__. */
    execute(c, "class Exporting:\n    def __buffer__(self, flags):\n        for i in range(3000): pass\n"
               "        return memoryview(bytes(i % 256 for i in range(flags)))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "memoryview(Exporting()).nbytes", "exporting.py"), SPY_STOP_STEPS, &pauses)) == 284 && pauses > 1);
    /* So do a view's release() and with block, calling its exporter's Python __release_buffer__. */
    execute(c, "class Releasing(Exporting):\n    def __release_buffer__(self, view):\n        for i in range(3000): pass\n"
               "        released.append(i)\n"
               "released = []\n"
               "def releases():\n    m = memoryview(Releasing())\n    m.release()\n    with memoryview(Releasing()): pass\n"
               "    return sum(released)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "releases()", "releases.py"), SPY_STOP_STEPS, &pauses)) == 5998 && pauses > 2);
    /* So do bytes() and bytearray() of it, copying the view and then releasing it. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(bytes(Releasing())) + len(bytearray(Releasing())) + sum(released)", "copies.py"),
                                 SPY_STOP_STEPS, &pauses)) == 12564 && pauses > 3);
    /* So do a dict subclass's subscript, in and get, comparing keys by a Python __eq__. */
    execute(c, "class Same:\n    def __hash__(self): return 1\n    def __eq__(self, other):\n        for i in range(3000): pass\n"
               "        return other is self\n"
               "class Sub(dict): pass\n"
               "def compares():\n    k = Same()\n    d = Sub({Same(): 1, k: 2})\n    return d[k] + (k in d) + d.get(k)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "compares()", "compares.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 2);
    /* So do an asend's later send and throw while its async generator awaits a generator. */
    execute(c, "class Waits:\n    def __await__(self):\n        try: yield 1\n        except KeyError: pass\n"
               "        for i in range(3000): pass\n        return i\n"
               "async def awaiting():\n    yield await Waits()\n"
               "def awaits_resumed():\n    out = 0\n    for throw in (0, 1):\n        a = awaiting().asend(None)\n        a.send(None)\n"
               "        try: a.throw(KeyError) if throw else a.send(None)\n        except StopIteration as e: out += e.value\n"
               "    return out\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "awaits_resumed()", "awaits_resumed.py"), SPY_STOP_STEPS, &pauses)) == 5998 && pauses > 2);
    /* So do a dict subclass's subscript with a Python __missing__, store and deletion, comparing keys by a Python __eq__. */
    execute(c, "class Absent(dict):\n    def __missing__(self, key): return 1\n"
               "def missing_compares():\n    k = Same()\n    d = Absent({Same(): 1})\n    n = d[k]\n    d[k] = 2\n    d[k] += 1\n"
               "    del d[k]\n    return n + len(d)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "missing_compares()", "missing_compares.py"), SPY_STOP_STEPS, &pauses)) == 2 && pauses > 4);
    /* So do a throw and a close into a yield from of an iterator without those methods. */
    execute(c, "class Methodless:\n    def __iter__(self): return self\n    def __next__(self): return 1\n"
               "def passing():\n    try: yield from Methodless()\n    except BaseException:\n        for i in range(3000): pass\n"
               "        yield i\n"
               "def passes():\n    g = passing(); next(g)\n    n = g.throw(KeyError)\n    g = passing(); next(g)\n"
               "    try: g.close()\n    except RuntimeError: n += 1\n    return n\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "passes()", "passes.py"), SPY_STOP_STEPS, &pauses)) == 3000 && pauses > 2);
    /* So do a set subclass's methods of an iterable, comparing keys by a Python __eq__. */
    execute(c, "class Grown(set): pass\n"
               "def grows():\n    s = Grown([Same()])\n    s.update([Same()])\n    s.difference_update([Same()])\n"
               "    return 10 * len(s) + s.issuperset([Same()]) + len(s.union([Same()]))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "grows()", "grows.py"), SPY_STOP_STEPS, &pauses)) == 23 && pauses > 4);
    /* So does in of a list or tuple whose Python __eq__ item follows a plain instance or a tuple. */
    execute(c, "class Bare: pass\n"
               "def mixes():\n    return (2 in [(), Bare(), Same()]) + 2 * (2 not in ([2], Bare(), Same()))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "mixes()", "mixes.py"), SPY_STOP_STEPS, &pauses)) == 2 && pauses > 2);
    /* So does index of a list or tuple from a start, to a stop too. */
    execute(c, "def bounded():\n    return [1, Same(), 2].index(2, 1) + (Same(), Same(), 2).index(2, -3, 3)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "bounded()", "bounded.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So do a set's methods of a list or its iterator called as another call's argument. */
    execute(c, "def operands():\n    s = {Same()}\n    src, it = [Same()], iter([Same()])\n"
               "    return len(s.union(src)) + len(set.union(s, it))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "operands()", "operands.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So does set.__init__ through super() or unbound, of a list or a generator. */
    execute(c, "class Reset(set):\n    def __init__(self, source): super().__init__(source)\n"
               "def resets():\n    s = Reset([Same(), Same()])\n    t = {1}\n    set.__init__(t, (Same() for i in range(2)))\n"
               "    return len(s) + len(t)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "resets()", "resets.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So does a list or tuple compared with a list or tuple subclass's instance. */
    execute(c, "class Seq(list): pass\nclass Row(tuple): pass\n"
               "def compared():\n    a, r = [Same()], (Same(),)\n"
               "    return (a != Seq([Same()])) + (Seq([Same()]) != a) + (Row(r) != (Same(),)) + ((Same(),) != Row(r))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "compared()", "compared.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So does a dict's merge of a dict into one with keys, by update(), |=, | and **. */
    execute(c, "def merged():\n    d = {Same(): 1}\n    d.update({Same(): 2})\n    d |= {Same(): 3}\n"
               "    return len(d) + len(d | {Same(): 4}) - len({**d, **{Same(): 5}})\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "merged()", "merged.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 2);
    /* So does a class call whose Python __new__ leaves list's or set's __init__ to take a source. */
    execute(c, "class Fresh(list):\n    def __new__(cls, source): return super().__new__(cls)\n"
               "class Pool(set):\n    def __new__(cls, source): return super().__new__(cls)\n"
               "def fresh():\n    return len(Fresh(Same() for i in range(2))) + len(Pool([Same(), Same()]))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "fresh()", "fresh.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So does a metaclass's Python mro() for a class statement, a call of the metaclass and type.__new__. */
    execute(c, "class Ordered(type):\n    def mro(cls):\n        for i in range(3000): pass\n        return type.mro(cls)\n"
               "def ordered():\n    class A(metaclass=Ordered): pass\n"
               "    return len(A.__mro__) + len(Ordered('B', (A,), {}).__mro__) + len(type.__new__(Ordered, 'C', (), {}).__mro__)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "ordered()", "ordered.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 2);
    /* So does an async for's Python __anext__ and an async with's Python __aenter__ and __aexit__. */
    execute(c, "class Ticks:\n    def __init__(self): self.i = 0\n    def __aiter__(self): return self\n"
               "    async def __anext__(self):\n        for i in range(3000): pass\n        self.i += 1\n"
               "        if self.i > 2: raise StopAsyncIteration\n        return self.i\n"
               "    async def __aenter__(self):\n        for i in range(3000): pass\n        return 4\n"
               "    async def __aexit__(self, *a):\n        for i in range(3000): pass\n"
               "async def ticked():\n    n = 0\n    async for i in Ticks(): n += i\n    async with Ticks() as v: n += v\n    return n\n"
               "def run_ticked():\n    try: ticked().send(None)\n    except StopIteration as e: return e.value\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "run_ticked()", "ticked.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 2);
    /* So does an async with's plain Python __aenter__ and __aexit__. */
    execute(c, "class Done:\n    def __await__(self):\n        return 3\n        yield\n"
               "class Plainly:\n    def __aenter__(self):\n        for i in range(3000): pass\n        return Done()\n"
               "    def __aexit__(self, *a):\n        for i in range(3000): pass\n        return Done()\n"
               "async def plainly():\n    async with Plainly() as v: return v\n"
               "def run_plainly():\n    try: plainly().send(None)\n    except StopIteration as e: return e.value\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "run_plainly()", "plainly.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 2);
    /* So does an asynchronous generator expression's Python __aiter__. */
    execute(c, "class Aiters:\n    def __aiter__(self):\n        for i in range(3000): pass\n        return self\n"
               "    async def __anext__(self): raise StopAsyncIteration\n"
               "def aitered():\n    g = (x async for x in Aiters())\n    h = (x async for x in Aiters())\n    return 5\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "aitered()", "aitered.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 1);
    /* So does a builtin sequence's operand's Python reflected method, and its __index__ after it declines. */
    execute(c, "class Rmul:\n    def __init__(self, n): self.n = n\n    def __index__(self): return slower(self.n)\n"
               "    def __rmul__(self, o):\n        for i in range(3000): pass\n        return NotImplemented if self.n else 4\n"
               "def reflected():\n    return ([1] * Rmul(0)) + len((2,) * Rmul(3))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "reflected()", "reflected.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 2);
    /* So does an asynchronous comprehension resumed at an await of its source. */
    execute(c, "class Tick:\n    def __await__(self): yield 1\n"
               "async def ticking():\n    for i in range(2):\n        await Tick()\n        for j in range(3000): pass\n        yield i\n"
               "async def gathered(): return [x async for x in ticking()]\n"
               "def run_gathered():\n    g = gathered(); n = 0\n    try:\n        while True: g.send(None); n += 1\n"
               "    except StopIteration as e: return len(e.value) + n\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "run_gathered()", "gathered.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 1);
    /* So does a slice's indices() of a part or length with a Python __index__, and a subscript after an int subclass's part. */
    execute(c, "class Slow:\n    def __init__(self, n): self.n = n\n    def __index__(self):\n        for i in range(3000): pass\n        return self.n\n"
               "class Sub(int): pass\n"
               "def indexed():\n    a, b, s = slice(Slow(1), Slow(5)).indices(Slow(9))\n    return a + b + s + len([0, 1, 2][Sub(1):Slow(3)])\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "indexed()", "indexed.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 2);
    /* So does len(), bool() and reversed() of a __len__ whose result has a Python __index__. */
    execute(c, "class Measured:\n    def __len__(self): return Slow(2)\n    def __getitem__(self, i): return i\n"
               "def measured():\n    return len(Measured()) + bool(Measured()) + sum(x for x in reversed(Measured()))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "measured()", "measured.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 2);
    /* So does a list's or tuple's subclass's Python __iter__ for list(), sorted() and tuple(). */
    execute(c, "class Walked(list):\n    def __iter__(self):\n        for i in range(3000): pass\n        return iter((1, 2))\n"
               "class Paired(tuple):\n    def __iter__(self):\n        for i in range(3000): pass\n        return iter((3,))\n"
               "def walked():\n    return sum(list(Walked())) + sum(sorted(Walked())) + sum(tuple(Paired()))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "walked()", "walked.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 2);
    /* So do frozendict()'s mapping's Python keys() and __getitem__, and its generator. */
    execute(c, "class Frozen:\n    def keys(self):\n        for i in range(3000): pass\n        return ['a']\n"
               "    def __getitem__(self, k):\n        for i in range(3000): pass\n        return 2\n"
               "def thawed():\n    yield ('b', 3)\n"
               "def frozen():\n    return frozendict(Frozen())['a'] + frozendict(thawed(), c=4)['b']\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "frozen()", "frozen.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 1);
    /* So does a map subclass's Python __next__ for list() and sum(). */
    execute(c, "class Mapped(map):\n    def __next__(self):\n        for i in range(3000): pass\n        return super().__next__()\n"
               "def mapped():\n    return sum(list(Mapped(abs, [-1, -2]))) + sum(Mapped(abs, [3]))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "mapped()", "mapped.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 2);
    /* A dict's ** keeps its keys' hashes: update() never calls their Python __hash__. */
    execute(c, "class Spelled(str):\n    def __hash__(self):\n        for i in range(3000): pass\n        return str.__hash__(self)\n"
               "def spelled():\n    d = {}\n    for i in range(3000): pass\n    d.update(**{Spelled('a'): 1})\n    return d['a']\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "spelled()", "spelled.py"), SPY_STOP_STEPS, &pauses)) == 1 && pauses > 1);
    /* And dict()'s and dict.update()'s of a zip subclass's pairs. */
    execute(c, "class Zipped(zip):\n    def __next__(self):\n        for i in range(3000): pass\n        return super().__next__()\n"
               "def zipped():\n    d = dict(Zipped('a', [1]))\n    d.update(Zipped('b', [2]))\n    return d['a'] + d['b']\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "zipped()", "zipped.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 1);
    /* So does a map's function for its explicit __next__, bound, stored or by super(). */
    execute(c, "def slow(x):\n    for i in range(3000): pass\n    return x\n"
               "class Supered(map):\n    def __next__(self): return super().__next__()\n"
               "def nexted():\n    m = map(slow, [1, 2])\n    w = map(slow, [3]).__next__\n"
               "    return m.__next__() + map.__next__(m) + w() + next(Supered(slow, [4]))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "nexted()", "nexted.py"), SPY_STOP_STEPS, &pauses)) == 10 && pauses > 3);
    /* So does the Python __iter__ of what a mapping's keys() returns, for ** and dict(). */
    execute(c, "class Listed:\n    def __iter__(self):\n        for i in range(3000): pass\n        return iter('ab')\n"
               "class Keyed:\n    def keys(self): return Listed()\n    def __getitem__(self, k): return 1\n"
               "def keyed():\n    return len({**Keyed()}) + len(dict(Keyed()))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "keyed()", "keyed.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 1);
    /* So does an __index__ that in of bytes calls, its error discarded. */
    execute(c, "class Byte:\n    def __init__(self, v): self.v = v\n"
               "    def __index__(self):\n        for i in range(3000): pass\n        return self.v\n"
               "def held():\n    try: Byte('s') in b'a'\n    except TypeError: pass\n"
               "    return (Byte(97) in b'a') + (Byte(98) not in b'a')\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "held()", "held.py"), SPY_STOP_STEPS, &pauses)) == 2 && pauses > 2);
    /* So does a metaclass's __getitem__ that iterating or reversing its class calls. */
    execute(c, "class Indexed(type):\n    def __len__(cls): return 2\n"
               "    def __getitem__(cls, i):\n        for j in range(3000): pass\n"
               "        if i > 1: raise IndexError(i)\n        return i + 1\n"
               "class Classed(metaclass=Indexed): pass\n"
               "def classed():\n    return sum(Classed) + list(reversed(Classed))[0] + sorted(Classed)[1]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "classed()", "classed.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 6);
    /* So does a dead generator's finally after one that closes running nothing. */
    execute(c, "def quiet():\n    yield 1\n"
               "def guarded(out):\n    try: yield 1\n    finally:\n        for i in range(3000): pass\n        out.append(2)\n"
               "def held(out):\n    q = quiet(); next(q)\n    g = guarded(out); next(g)\n    r = quiet(); next(r)\n"
               "def dropped():\n    out = []\n    held(out)\n    return out[0]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "dropped()", "dropped.py"), SPY_STOP_STEPS, &pauses)) == 2 && pauses > 1);
    /* So does a Python __eq__ that a frozenset's augmented assignment calls. */
    execute(c, "class Same:\n    def __init__(self, v): self.v = v\n    def __hash__(self): return 1\n"
               "    def __eq__(self, o):\n        for i in range(3000): pass\n        return self.v == o.v\n"
               "def frozen():\n    a = frozenset([Same(1), Same(2)])\n    a &= {Same(2), Same(3)}\n    return len(a)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "frozen()", "frozen.py"), SPY_STOP_STEPS, &pauses)) == 1 && pauses > 3);
    /* So does the Python __delattr__ or deleter delattr() calls. */
    execute(c, "class Deleting:\n    def __delattr__(self, n):\n        for i in range(3000): pass\n"
               "    p = property(lambda s: 0, None, lambda s: [i for i in range(3000)])\n"
               "def deleted():\n    d = Deleting()\n    delattr(d, 'x')\n    delattr(Deleting.__new__(Deleting), 'p')\n    return 5\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "deleted()", "deleted.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 3);
    /* So does the __index__ of a text method's width or maxsplit, or of int()'s base. */
    execute(c, "class Width:\n    def __index__(self):\n        for i in range(3000): pass\n        return 4\n"
               "def widened():\n    s = 'ab'\n    return len(s.ljust(Width(), '*')) + len('a b c d e'.split(None, Width())) + int('10', Width())\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "widened()", "widened.py"), SPY_STOP_STEPS, &pauses)) == 13 && pauses > 6);
    /* So does one given by keyword, and hex's bytes_per_sep. */
    execute(c, "def keyed():\n    return len('a b c d e'.split(maxsplit=Width())) + len(b'abcdefgh'.hex(':', Width())) + int('10', base=Width())\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "keyed()", "keyed.py"), SPY_STOP_STEPS, &pauses)) == 26 && pauses > 6);
    /* So does a bytearray's index, byte or search bound. */
    execute(c, "def arrayed():\n    ba = bytearray(b'abcd')\n    ba.insert(Width(), Width())\n    ba.append(Width())\n    ba.pop(Width())\n"
               "    return len(ba) * 10 + ba.find(b'd', Width())\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "arrayed()", "arrayed.py"), SPY_STOP_STEPS, &pauses)) == 49 && pauses > 6);
    /* So does an unbound list method's or search's. */
    execute(c, "def unbound():\n    l = [1, 2, 3, 4, 5, 6]\n    list.insert(l, Width(), 9)\n    list.pop(l, Width())\n"
               "    return list.pop(l, Width()) * 10 + str.find('abcdefb', 'b', Width()) + tuple.index((0, 0, 0, 0, 0, 0), 0, Width())\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "unbound()", "unbound.py"), SPY_STOP_STEPS, &pauses)) == 60 && pauses > 6);
    /* So does enumerate()'s start. */
    execute(c, "def counted():\n    return sum(i for i, _ in enumerate('ab', Width())) + sum(i for i, _ in enumerate('a', start=Width())) + list(enumerate('a', Width()))[0][0]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "counted()", "counted.py"), SPY_STOP_STEPS, &pauses)) == 17 && pauses > 6);
    /* So does pow()'s __pow__ given a modulus. */
    execute(c, "class Powered:\n    def __pow__(self, b, m=None):\n        for i in range(3000): pass\n        return b * m\n"
               "def powered():\n    return pow(Powered(), 2, 3) + pow(Powered(), 1, 4) + pow(Powered(), 2, 2)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "powered()", "powered.py"), SPY_STOP_STEPS, &pauses)) == 14 && pauses > 6);
    /* So does complex()'s __float__ or __index__ with no __complex__. */
    execute(c, "class Floated:\n    def __float__(self):\n        for i in range(3000): pass\n        return 2.0\n"
               "def complexed():\n    return int((complex(Floated()) + complex(Floated()) + complex(Width())).real)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "complexed()", "complexed.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 6);
    /* So does the Python __eq__ of a ** keyword's str subclass name. */
    execute(c, "class KwName(str):\n    __hash__ = str.__hash__\n    def __eq__(self, other):\n        for i in range(3000): pass\n"
               "        return str.__eq__(self, other)\n"
               "def kw_bound(a, b=1, **rest):\n    return a + b + len(rest)\n"
               "def kw_named():\n    return kw_bound(**{KwName('b'): 2, KwName('a'): 3, KwName('z'): 0})\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "kw_named()", "kw_named.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 4);
    /* So does the Python __hash__ of a name a function's **kwargs stores. */
    execute(c, "class KwHashed(str):\n    __eq__ = str.__eq__\n    def __hash__(self):\n        for i in range(3000): pass\n"
               "        return str.__hash__(self)\n"
               "def kw_stored(**rest):\n    return len(rest)\n"
               "def kw_hashes():\n    d = {KwHashed('p'): 1, KwHashed('q'): 2}\n    return kw_stored(**d) + kw_stored(**d)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "kw_hashes()", "kw_hashes.py"), SPY_STOP_STEPS, &pauses)) == 4 && pauses > 4);
    /* So does the Python __eq__ of a name a call's ** merges. */
    execute(c, "class KwMerged(str):\n    __hash__ = str.__hash__\n    def __eq__(self, other):\n        for i in range(3000): pass\n"
               "        return str.__eq__(self, other)\n"
               "def kw_merged(**rest):\n    return len(rest)\n"
               "def kw_merges():\n    d = {KwMerged('p'): 1}\n"
               "    try: kw_merged(p=0, **d)\n    except TypeError: pass\n"
               "    try: kw_merged(**{'p': 0}, **d)\n    except TypeError: return 3\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "kw_merges()", "kw_merges.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 1);
    /* So does that of a name a keyword after the ** is merged with. */
    execute(c, "def kw_after():\n    try: kw_merged(**{KwMerged('p'): 1}, q=0, p=0)\n    except TypeError: return kw_merged(**{KwMerged('q'): 1}, p=0)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "kw_after()", "kw_after.py"), SPY_STOP_STEPS, &pauses)) == 2 && pauses > 0);
    /* So does round() given ndigits by keyword. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "round(1234, ndigits=Rounded()) + round(ndigits=Rounded(), number=25)", "rounded_by.py"),
                                 SPY_STOP_STEPS, &pauses)) == 1250 && pauses > 1);
    /* So does a memoryview's or bytearray's item at a Python __index__. */
    execute(c, "class Viewed:\n    def __index__(self):\n        for i in range(3000): pass\n        return 1\n"
               "def viewed():\n    b = bytearray(b'ab'); m = memoryview(b)\n    m[Viewed()] = 5; b[Viewed()] += 1\n"
               "    return m[Viewed()]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "viewed()", "viewed.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 2);
    /* So does a raise of a class whose Python __new__ makes the exception. */
    execute(c, "class Fresh(Exception):\n    def __new__(cls):\n        for i in range(3000): pass\n        return super().__new__(cls)\n"
               "def fresh():\n    try: raise Fresh from Fresh\n    except Fresh as e: return 7 if type(e.__cause__) is Fresh else 0\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "fresh()", "fresh.py"), SPY_STOP_STEPS, &pauses)) == 7 && pauses > 2);
    /* A raise of a class whose __new__ makes another exception raises the
     * class with it, the first __new__ on the machine. */
    execute(c, "class Renewed(Exception):\n    def __new__(cls, *a):\n        if a: return super().__new__(cls, *a)\n"
               "        for i in range(3000): pass\n        return KeyError()\n"
               "def renewed():\n    try: raise Renewed\n    except Renewed as e: return 8 if type(e.args[0]) is KeyError else 0\n"
               "    except KeyError: return 1\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "renewed()", "renewed.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 2);
    /* So do dict() and dict.update() of pairs a Python __iter__ gives. */
    execute(c, "class Paired:\n    def __iter__(self):\n        for i in range(3000): pass\n        return iter([(1, 2), (3, 4)])\n"
               "def paired():\n    d = dict(Paired()); d.update(Paired())\n    return sum(d) + len(d)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "paired()", "paired.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 2);
    /* And with keywords, merged after the pairs. */
    execute(c, "def keyworded():\n    d = dict(Paired(), a=5); d.update(Paired(), **{'b': 6})\n    return sum(d.values())\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "keyworded()", "keyworded.py"), SPY_STOP_STEPS, &pauses)) == 17 && pauses > 2);
    /* So do the Python __new__ and __init__ a raise calls again with an exception of another class. */
    execute(c, "class Renewed(Exception):\n    def __new__(cls, *a):\n        for i in range(3000): pass\n"
               "        return super().__new__(cls, *a) if a else KeyError(i)\n"
               "    def __init__(self, *a):\n        for i in range(3000): pass\n        self.i = i\n"
               "def renewing():\n    try: raise Renewed\n    except Renewed as e: return e.i + e.args[0].args[0]\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "renewing()", "renewing.py"), SPY_STOP_STEPS, &pauses)) == 5998 && pauses > 2);
    /* So do a class body's implicit stores through its namespace's Python __setitem__. */
    execute(c, "class Slowns(dict):\n    def __setitem__(self, k, v):\n        for i in range(3000): pass\n"
               "        super().__setitem__(k, v)\n"
               "class Slowmeta(type):\n    @classmethod\n    def __prepare__(m, n, b): return Slowns()\n"
               "def namespaced():\n    class K(metaclass=Slowmeta): pass\n    return len(K.__qualname__)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "namespaced()", "namespaced.py"), SPY_STOP_STEPS, &pauses)) == 21 && pauses > 3);
    /* So do its def's and del's, through __setitem__ and __delitem__. */
    execute(c, "class Slowdel(Slowns):\n    def __delitem__(self, k):\n        for i in range(3000): pass\n"
               "        super().__delitem__(k)\n"
               "class Delmeta(type):\n    @classmethod\n    def __prepare__(m, n, b): return Slowdel()\n"
               "def bound():\n    class K(metaclass=Delmeta):\n        def f(self): return 7\n        g: int = 1\n        del g\n"
               "    return K().f() + len(K.__dict__) - ('g' in K.__dict__)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "bound()", "bound.py"), SPY_STOP_STEPS, &pauses)) > 7 && pauses > 6);
    /* So does the Python __new__ a generator's throw() of a class calls. */
    execute(c, "class Fresh(Exception):\n    def __new__(cls, *a):\n        for i in range(3000): pass\n"
               "        e = super().__new__(cls, *a); e.i = i; return e\n"
               "def freshly():\n    try: yield 0\n    except Fresh as e: yield e.i + len(e.args)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "(g := freshly(), next(g), g.throw(Fresh, 1))[2]", "fresh.py"), SPY_STOP_STEPS, &pauses)) == 3000 && pauses > 2);
    /* So do print()'s calls of a file's Python write and flush. */
    execute(c, "class Written:\n    def __init__(self): self.n = 0\n"
               "    def write(self, text):\n        for i in range(3000): pass\n        self.n += len(text)\n"
               "    def flush(self):\n        for i in range(3000): pass\n        self.n += 1\n"
               "def written():\n    w = Written(); print('ab', 'c', file=w, flush=True)\n    return w.n\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "written()", "written.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 2);
    /* So does the Python __iter__ a comprehension's first iterable calls. */
    execute(c, "class Iterated:\n    def __iter__(self):\n        for i in range(3000): pass\n        return iter([1, 2])\n"
               "def comprehended():\n    return sum([x for x in Iterated()]) + sum({x for x in Iterated()}) + sum(x for x in Iterated())\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "comprehended()", "comprehended.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 2);
    /* So does a method call whose attribute a Python getter or __getattr__ reads. */
    execute(c, "class Fetched:\n    @property\n    def f(self):\n        for i in range(3000): pass\n        return abs\n"
               "    def __getattr__(self, name):\n        for i in range(3000): pass\n        return len\n"
               "def fetched():\n    g = Fetched(); k = -2\n    return g.f(k) + g.h('ab') + g.f(-1)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "fetched()", "fetched.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 2);
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "int(issubclass(*(Abstract((Abstract(()),)), Abstract(()))))", "abstract.py"), SPY_STOP_STEPS, &pauses)) == 0 && pauses > 1);
    /* So does the __add__ after an __iadd__ that declines. */
    execute(c, "class Declines:\n    def __iadd__(self, o): return NotImplemented\n"
               "    def __add__(self, o):\n        for i in range(3000): pass\n        return i + o\n"
               "def declined():\n    x = Declines()\n    x += 1\n    return x\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "declined()", "declined.py"), SPY_STOP_STEPS, &pauses)) == 3000 && pauses > 0);
    /* So do repr() and len() in a builtin subclass's and a metaclass's methods. */
    execute(c, "class Loud(int):\n    def __repr__(self):\n        for i in range(3000): pass\n        return str(i)\n"
               "class Sized(type):\n    def __len__(cls):\n        for i in range(3000): pass\n        return i\n"
               "class Measured(metaclass=Sized): pass\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "int(repr(Loud(1))) + len(Measured) + round(Loud(2), 1)", "owner.py"), SPY_STOP_STEPS, &pauses)) == 6000 &&
           pauses > 1);
    /* So does a class call with ** arguments in a Python __new__ and __init__. */
    execute(c, "class Fresh:\n    def __new__(cls, **k):\n        for i in range(3000): pass\n        return super().__new__(cls)\n"
               "    def __init__(self, **k):\n        for i in range(3000): pass\n        self.i = i + k['x']\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "Fresh(**{'x': 1}).i", "fresh.py"), SPY_STOP_STEPS, &pauses)) == 3000 && pauses > 1);
    /* So does next() in a Python __next__, also giving its default for a StopIteration. */
    execute(c, "class Stepper:\n    def __init__(self, n): self.n = n\n"
               "    def __next__(self):\n        for i in range(3000): pass\n        if not self.n: raise StopIteration\n        self.n -= 1\n        return i\n"
               "stepper = Stepper(1)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "next(stepper) + next(stepper, 1) + next(Stepper(0), 2)", "next.py"), SPY_STOP_STEPS, &pauses)) == 3002 &&
           pauses > 2);
    /* So do enumerate(), zip() and map() taking items from one, and next() of them. */
    execute(c, "class Steps(Stepper):\n    def __iter__(self): return self\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(list(enumerate(Steps(2)))) + sum(map(abs, Steps(1))) + next(zip(Steps(1), Steps(1)))[1]", "adapt.py"),
                                 SPY_STOP_STEPS, &pauses)) == 2 + 2999 + 2999 && pauses > 4);
    /* So do zip(), map(), enumerate() and filter() calling a Python __iter__. */
    execute(c, "class Walk:\n    def __iter__(self):\n        for i in range(3000): pass\n        return iter([i])\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "list(zip(Walk(), [1]))[0][0] + list(map(abs, Walk()))[0] + list(enumerate(Walk()))[0][1] + "
                                                 "list(filter(None, Walk()))[0]", "walk.py"), SPY_STOP_STEPS, &pauses)) == 4 * 2999 && pauses > 3);
    /* So does reversed() calling a sequence's Python __len__. */
    execute(c, "class Backward:\n    def __len__(self):\n        for i in range(3000): pass\n        return 2\n"
               "    def __getitem__(self, i): return i\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "next(reversed(Backward())) + next(reversed(Backward()))", "backward.py"),
                                 SPY_STOP_STEPS, &pauses)) == 2 && pauses > 1);
    /* So do list() and sorted() asking an iterator over one for its length hint. */
    execute(c, "class Hinted(Backward):\n    def __getitem__(self, i):\n        if i > 1: raise IndexError\n        return i\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "len(sorted(iter(Hinted()))) + len(list(iter(Hinted())))", "hinted.py"),
                                 SPY_STOP_STEPS, &pauses)) == 4 && pauses > 1);
    /* So does next() of an iterator over one, a map or a filter. */
    execute(c, "class Paged:\n    def __getitem__(self, i):\n        for j in range(3000): pass\n        return i + 5\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "next(iter(Paged())) + next(map(slower, [1])) + next(filter(slower, [0]))", "paged.py"),
                                 SPY_STOP_STEPS, &pauses)) == 7 && pauses > 2);
    /* So does an await of an async generator's asend() or __anext__(), and an async for over one. */
    execute(c, "async def ticks(n):\n    for i in range(n): yield slower(i)\n"
               "async def total():\n    s = 0\n    async for i in ticks(2): s += i\n"
               "    g = ticks(2)\n    return s + await g.asend(None) + await anext(g)\n"
               "def finish(co):\n    try: co.send(None)\n    except StopIteration as e: return e.value\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "finish(total())", "ticks.py"), SPY_STOP_STEPS, &pauses)) == 6 && pauses > 3);
    /* So does the close of an unreachable async generator suspended at a yield. */
    execute(c, "async def held(log):\n    try: yield 1\n    finally: log.append(slower(slower(1)))\n"
               "def dropped():\n    log = []\n    g = held(log)\n    finish(g.__anext__())\n    del g\n    log.append(0)\n    return sum(log)\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "dropped()", "held.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 1);
    /* So does a starred iterator over one, or a map, in a display or call. */
    execute(c, "def starred():\n    return len([*map(slower, [1, 2])]) + len((*iter(Hinted()),)) + max(*map(slower, [1, 4]))\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "starred()", "starred.py"), SPY_STOP_STEPS, &pauses)) == 9 && pauses > 2);
    /* So does a dict display merging an instance by its keys() and __getitem__. */
    execute(c, "class Slowmap:\n    def keys(self): return [slower(0), slower(1)]\n    def __getitem__(self, k): return slower(k)\n"
               "def merged():\n    return sum([{**Slowmap()}][0].values())\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "merged()", "merged.py"), SPY_STOP_STEPS, &pauses)) == 5 && pauses > 2);
    /* So does setattr() in a __setattr__, a property's setter and a
     * descriptor's __set__; a plain store and a setter's error are native. */
    execute(c, "class Hook:\n    def __setattr__(self, name, value): object.__setattr__(self, name, slow(value))\n"
               "class Set:\n    def __get__(self, o, t): return o._s\n    def __set__(self, o, value): o._s = slow(value)\n"
               "class Kept:\n    s = Set()\n    @property\n    def p(self): return self._p\n"
               "    @p.setter\n    def p(self, value): self._p = slow(value)\n    narrow = property(lambda self: 1, lambda self: 1)\n"
               "def kept():\n    h, k, total = Hook(), Kept(), 0\n"
               "    for i in range(30):\n        setattr(h, 'x', i); setattr(k, 's', 1); setattr(k, 'p', 2); setattr(k, 'plain', 3)\n"
               "        total += h.x + k.s + k.p + k.plain\n"
               "    try: setattr(k, 'narrow', 1)\n    except TypeError: total += 100\n"
               "    return total");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "kept()", "kept.py"), SPY_STOP_STEPS, &pauses)) == 435 + 30 * 6 + 100 && pauses > 3);
    /* So does a lone == or != of lists or tuples in an __eq__ of their
     * items, pair after pair; an instance operand's __eq__ too. */
    execute(c, "class Eq:\n    def __init__(self, v): self.v = v\n"
               "    def __eq__(self, o):\n        if self.v == 'bad': raise KeyError(o)\n        return slow(self.v) == getattr(o, 'v', o)\n"
               "def equals():\n    total = 0\n"
               "    for i in range(30):\n"
               "        total += ([Eq(i), 1, Eq(2)] == [Eq(i), 1, Eq(2)]) + ((Eq(i), 2) != (Eq(i), 3)) + ([Eq(1), Eq(i)] == [Eq(0), Eq(i)])\n"
               "        total += (Eq(i) == i) + ([1, 2] == [1, 2]) + ((Eq(i), [1]) == (i, [1]))\n"
               "    try: [Eq('bad')] == [1]\n    except KeyError: total += 100\n"
               "    return total");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "equals()", "equals.py"), SPY_STOP_STEPS, &pauses)) == 30 * 5 + 100 && pauses > 3);
    /* print writes to the sys.stdout it began with, which __str__ rebinds. */
    SPYContext *muted = spy_context_new();
    Output shown = {0};
    assert(muted && !spy_std_init(muted) && !spy_set_limit(muted, SPY_LIMIT_PAUSE, 1));
    spy_set_output(muted, output, NULL, &shown);
    execute(muted, "import sys\nclass Mute:\n    def __str__(self):\n        sys.stdout = None\n        return 'm'\n"
                   "def mute():\n    print(Mute(), Mute())\n    print(Mute())\nmute()");
    assert(!strcmp(shown.text, "m m\n"));
    spy_context_free(muted);
    /* A class body that loops pauses inside it. */
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "class Looping:\n    n = 0\n    while n < 3000: n += 1\n    m = slow(n)\nLooping.m", "class.py"),
                                 SPY_STOP_STEPS, &pauses)) == 3000 && pauses > 1);
    /* An import pauses in its module's body; one that raises leaves no
     * module, so the next import runs it again. */
    int loads = 0;
    spy_set_module_loader(c, looping_loader, &loads);
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "def imported():\n    import looping\n    from looping import n\n    return n + len(looping.__doc__)\nimported()",
                                             "import.py"), SPY_STOP_STEPS, &pauses)) == 3006 && pauses > 1);
    pauses = 0;
    v = spy_eval(c, "def failing():\n    for i in range(2):\n        try: import breaking\n        except ValueError as e: error = str(e)\n    return error\nfailing()", "import.py");
    v = run_paused(c, v, SPY_STOP_STEPS, &pauses);
    assert(v && !strcmp(spy_as_string(c, v, NULL), "broken") && loads == 2 && pauses > 1);
    spy_release(v);
    spy_set_module_loader(c, loader, &calls);
    /* Code compiled while calls can pause pauses inside the special
     * methods of operators, subscripts, augmented assignments, target
     * lists, deletions, unary operators, len(), int(), float(), hash(),
     * f-string fields, a with statement's __exit__ and the comparisons of
     * sorts, of in and of a number or a declining instance with an instance. */
    execute(c, "def spin():\n    for i in range(1500): pass\n"
               "class Special:\n    def __add__(self, o): spin(); return 1\n    def __lt__(self, o): spin(); return True\n"
               "    def __getitem__(self, k): spin(); return 2\n    def __setitem__(self, k, v): spin()\n"
               "    def __contains__(self, k): spin(); return True\n    def __format__(self, spec): spin(); return spec\n"
               "    def __repr__(self): spin(); return 'r'\n    def __iadd__(self, o): spin(); return 4\n    def __len__(self): spin(); return 6\n"
               "    def __delitem__(self, k): spin()\n    def __neg__(self): spin(); return 1\n"
               "    def __int__(self): spin(); return 2\n    def __float__(self): spin(); return 3.0\n    def __hash__(self): spin(); return 4\n"
               "    def __enter__(self): return self\n    def __exit__(self, *exc): spin()\n"
               "    def __eq__(self, o): spin(); return self is o\n    def __rmul__(self, k): spin(); return k\n    def __sub__(self, o): spin(); return NotImplemented\n"
               "class Shown:\n    def __str__(self): spin(); return 'str'\n    def __lt__(self, o): spin(); return False\n    def __rsub__(self, o): spin(); return 5\n"
               "def special():\n    p, q = Special(), Shown()\n    t = p + 1\n    u = p < 1\n    w = p[0] + (0 in p)\n    p[0] = 1\n"
               "    p[0] += 1\n    x, p[1] = 0, 1\n    del p[0]\n    r = Special()\n    r += 1\n"
               "    n = -p + int(p) + int(float(p)) + hash(p)\n    with p: pass\n"
               "    s = [Shown(), Shown()]\n    s.sort()\n    n += len(sorted(s, reverse=True)) + (p in [Special(), p]) + 2 * p + (1 > p) + (p - q)\n"
               "    return t + u + w + r + n + len(p) + len(f'{p:ab}{p!r}{q}{q!s:>4}')\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "special()", "special.py"), SPY_STOP_STEPS, &pauses)) == 5 + 4 + 3 + 3 + 4 + 10 + 3 + 6 + 3 + 5 && pauses > 27);
    /* Attribute stores and deletions call a Python setter or deleter on the
     * machine, and delete other attributes at once. */
    execute(c, "class Del:\n    def __delattr__(self, k): spin()\n"
               "class Bad:\n    def __delattr__(self): spin()\n"
               "class Prop:\n    def q(self, v=None): spin()\n    p = property(lambda self: 1, q, q)\n"
               "class Get:\n    def __get__(self, o, t): return 1\n    def __set__(self, o, v): spin()\n    def __delete__(self, o): spin()\n"
               "class Owner:\n    d = Get()\n"
               "def deletes():\n    a, p, o, n = Del(), Prop(), Owner(), 0\n    del a.x\n    p.p = 1\n    del p.p\n    o.d = 1\n    del o.d\n"
               "    o.y = 1\n    del o.y\n    f = deletes\n    f.z = 1\n    del f.z\n"
               "    try:\n        del Bad().x\n    except TypeError:\n        n = 3\n    return n\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "deletes()", "deletes.py"), SPY_STOP_STEPS, &pauses)) == 3 && pauses > 4);
    /* Unpacking, min, max, enumerate and filter take a generator's items
     * on the machine. */
    execute(c, "def slowgen():\n    for i in range(3):\n        spin()\n        yield i\n"
               "def minmax():\n    a, b, c = slowgen()\n    for i, x in enumerate(slowgen()): c += i\n"
               "    return max(slowgen()) + min(filter(None, slowgen())) + c\n");
    pauses = 0;
    assert(integer(c, run_paused(c, spy_eval(c, "minmax()", "minmax.py"), SPY_STOP_STEPS, &pauses)) == 8 && pauses > 9);
    /* A module whose import names are not augmented assignments. */
    assert(integer(c, spy_eval(c, "from __future__ import annotations\nclass A:\n    y: int\nlen(A.__annotations__)", "future.py")) == 1);
    /* A budget spent entering any call of a dict walk stops the walk there. */
    SPYContext *walk = spy_context_new();
    execute(walk, "class W:\n    def __init__(self, v): self.v = v\n    def __hash__(self): return self.v % 3\n"
                  "    def __eq__(self, o):\n        for _ in range(2): pass\n        return self.v == o.v\n"
                  "a, b = {W(i): i for i in range(6)}, {W(i): i for i in range(6)}\n");
    size_t stops = 0;
    for (size_t budget = 1;; budget++) {
        spy_set_limit(walk, SPY_LIMIT_STEPS, budget);
        SPYValue *walked = spy_eval(walk, "{**a} == {**b}", "walked.py");
        if (walked) { assert(integer(walk, walked) == 1); break; }
        assert(!strcmp(spy_error_type(walk), "RuntimeError"));
        spy_clear_error(walk);
        stops++;
    }
    assert(stops > 6);
    spy_context_free(walk);
    /* An interrupt pauses too; spy_exec returns -1 when it pauses. */
    spy_set_limit(c, SPY_LIMIT_STEPS, 0);
    spy_set_interrupt(c, always, NULL);
    assert(spy_exec(c, "n = 0\nwhile n < 10000: n += 1", "interrupted.py") == -1 && spy_paused(c) == SPY_STOP_INTERRUPT);
    spy_set_interrupt(c, NULL, NULL);
    pauses = 0;
    v = run_paused(c, NULL, SPY_STOP_INTERRUPT, &pauses);
    assert(v && pauses == 1);
    spy_release(v);
    assert(integer(c, spy_eval(c, "n", "interrupted.py")) == 10000);
    /* Freeing a context stops its paused call. */
    SPYContext *dropped = spy_context_new();
    spy_set_limit(dropped, SPY_LIMIT_STEPS, 100);
    spy_set_limit(dropped, SPY_LIMIT_PAUSE, 1);
    assert(!spy_eval(dropped, "def f():\n    try:\n        while True: pass\n    finally:\n        print('never')\nf()", "dropped.py") && spy_paused(dropped));
    spy_context_free(dropped);
    /* A spy_callk's call stopped by a limit, or paused and then freed,
     * ends with no continuation. */
    dropped = spy_context_new();
    spy_set_limit(dropped, SPY_LIMIT_STEPS, 100);
    assert(!spy_define(dropped, "call_k", call_k, NULL));
    k_runs = 0;
    assert(spy_exec(dropped, "def f():\n    while True: pass", "dropped.py") == 0);
    assert(!spy_eval(dropped, "call_k(f)", "dropped.py") && spy_stopped(dropped) == SPY_STOP_STEPS && !spy_paused(dropped));
    spy_set_limit(dropped, SPY_LIMIT_PAUSE, 1);
    assert(!spy_eval(dropped, "call_k(f)", "dropped.py") && spy_paused(dropped));
    spy_context_free(dropped);
    assert(!k_runs);
    /* A step's first intrinsic, in a pausing call, loads their module on
     * the machine, spending no budget, and the step runs on: a class's
     * subscript, a union of names at hand, a generic class, a type alias
     * and a generic function. */
    static const char *const firsts[] = {
        "def f():\n    for i in range(300): pass\n    return len(repr(list[int]))",
        "def f(x=int):\n    for i in range(300): pass\n    return len(repr(x | None))",
        "def f():\n    for i in range(300): pass\n    class C[T]: pass\n    return len(C.__type_params__) + 8",
        "def f():\n    for i in range(300): pass\n    type A = int\n    return len(A.__name__) + 8",
        "def f():\n    for i in range(300): pass\n    def g[T](): pass\n    return len(g.__type_params__) + 8",
    };
    for (size_t i = 0; i < sizeof(firsts) / sizeof(*firsts); i++) {
        SPYContext *fresh = spy_context_new();
        assert(fresh && !spy_set_limit(fresh, SPY_LIMIT_STEPS, 100) && !spy_set_limit(fresh, SPY_LIMIT_PAUSE, 1));
        assert(spy_exec(fresh, firsts[i], "firsts.py") == 0);
        pauses = 0;
        assert(integer(fresh, run_paused(fresh, spy_eval(fresh, "f()", "firsts.py"), SPY_STOP_STEPS, &pauses)) == 9 + (i == 1) && pauses > 2);
        spy_context_free(fresh);
    }
    spy_set_limit(c, SPY_LIMIT_PAUSE, 0);
    spy_set_limit(c, SPY_LIMIT_STEPS, 0);
    /* The engine counts the bytes it holds; a memory limit stops the call
     * with a MemoryError no handler sees, and the context stays usable. */
    spy_clear_error(c); spy_collect(c);
    size_t held = spy_memory_used(c);
    execute(c, "big = 'a' * 10**6");
    assert(spy_memory_used(c) > held + 1000000);
    execute(c, "del big");
    spy_collect(c);
    assert(spy_memory_used(c) < held + 100000);
    spy_set_limit(c, SPY_LIMIT_MEMORY, held + (8 << 20));
    assert(spy_exec(c, "caught = 0\ntry:\n    x = [0] * 10**7\nexcept MemoryError:\n    caught = 1", "memory.py") == -1);
    assert(!strcmp(spy_error_type(c), "MemoryError") && spy_stopped(c) == SPY_STOP_MEMORY);
    assert(integer(c, spy_eval(c, "caught", "caught.py")) == 0);
    spy_set_limit(c, SPY_LIMIT_MEMORY, 0);
    /* spy_set_limit sets every limit; output going over its limit stops the
     * call like a spent budget, and the next call writes again. */
    assert(!spy_set_limit(c, SPY_LIMIT_MEMORY, 1 << 30) && spy_get_limit(c, SPY_LIMIT_MEMORY) == 1 << 30);
    assert(!spy_set_limit(c, SPY_LIMIT_MEMORY, 0) && !spy_set_limit(c, SPY_LIMIT_STEPS, 0) && !spy_get_limit(c, SPY_LIMIT_STEPS));
    assert(!spy_set_limit(c, SPY_LIMIT_OUTPUT, 8) && spy_get_limit(c, SPY_LIMIT_OUTPUT) == 8);
    o.len = 0;
    assert(spy_exec(c, "print('1234')\ntry:\n    print('56789')\nexcept BaseException:\n    print('caught')", "output.py") == -1);
    assert(!strcmp(o.text, "1234\n") && spy_stopped(c) == SPY_STOP_OUTPUT);
    assert(!strcmp(spy_error_type(c), "RuntimeError") && !strcmp(spy_error_message(c), "output limit exceeded"));
    o.len = 0;
    execute(c, "import sys\nsys.stdout.write('1234567')");
    assert(!strcmp(o.text, "1234567"));
    /* A limit lowered below what the call printed stops the next write. */
    assert(!spy_define(c, "limit_output", limit_output, NULL) && !spy_set_limit(c, SPY_LIMIT_OUTPUT, 0));
    o.len = 0;
    assert(spy_exec(c, "print('12')\nlimit_output(1)\nprint('3')", "lowered.py") == -1);
    assert(!strcmp(o.text, "12\n") && spy_stopped(c) == SPY_STOP_OUTPUT);
    assert(!spy_set_limit(c, SPY_LIMIT_OUTPUT, 0));
    assert(!spy_set_limit(c, SPY_LIMIT_RECURSION, 40) && spy_get_limit(c, SPY_LIMIT_RECURSION) == 40);
    assert(spy_exec(c, "def down(n): return down(n + 1)\ndown(0)", "recursion.py") == -1 && !strcmp(spy_error_type(c), "RecursionError"));
    assert(integer(c, spy_eval(c, "sys.getrecursionlimit()", "limit.py")) == 40);
    assert(!spy_set_limit(c, SPY_LIMIT_RECURSION, 1000));
    assert(!spy_set_limit(c, SPY_LIMIT_INT_DIGITS, 640) && spy_get_limit(c, SPY_LIMIT_INT_DIGITS) == 640);
    assert(spy_exec(c, "str(10 ** 700)", "digits.py") == -1 && !strcmp(spy_error_type(c), "ValueError"));
    assert(!spy_set_limit(c, SPY_LIMIT_INT_DIGITS, 0));
    execute(c, "assert len(str(10 ** 5000)) == 5001");
    assert(!spy_set_limit(c, SPY_LIMIT_INT_DIGITS, 4300));
    size_t stack = spy_get_limit(c, SPY_LIMIT_STACK);
    assert(stack == 4 << 20 && !spy_set_limit(c, SPY_LIMIT_STACK, 64 << 10) && !spy_set_limit(c, SPY_LIMIT_RECURSION, 100000));
    /* A Python function calling Python functions uses no C stack per call;
     * a recursion through an operator's method, which C calls, does. */
    execute(c, "def depth(n): return depth(n - 1) + 1 if n else 0\nassert depth(50000) == 50000");
    assert(spy_exec(c, "class Down:\n def __add__(self, n): return self + n\nDown() + 1", "stack.py") == -1 &&
           !strcmp(spy_error_type(c), "RecursionError") && !strncmp(spy_error_message(c), "Stack overflow", 14));
    /* So does one through a host function's spy_call, but not its spy_callk. */
    execute(c, "def down_k(n): return call_k(down_k, n - 1) + 1 if n else 0\nassert down_k(20000) == 20000");
    assert(spy_exec(c, "def down_back(n): return call_back(lambda: down_back(n - 1)) + 1 if n else 0\ndown_back(20000)", "stack.py") == -1 &&
           !strcmp(spy_error_type(c), "RecursionError") && !strncmp(spy_error_message(c), "Stack overflow", 14));
    assert(!spy_set_limit(c, SPY_LIMIT_STACK, stack) && !spy_set_limit(c, SPY_LIMIT_RECURSION, 1000));
    spy_clear_error(c);
    static const int bad[][2] = {{SPY_LIMIT_RECURSION, 0}, {SPY_LIMIT_INT_DIGITS, 100}, {SPY_LIMIT_STACK, 0}, {99, 1}};
    for (size_t i = 0; i < sizeof(bad) / sizeof(*bad); i++) {
        assert(spy_set_limit(c, bad[i][0], (size_t)bad[i][1]) == -1 && !strcmp(spy_error_type(c), "ValueError"));
        spy_clear_error(c);
    }
    assert(!spy_get_limit(c, 99));
    /* The interrupt is polled at least every 4096 steps; it stops the call
     * like a spent budget, and the next call runs normally. */
    int polls = 0;
    spy_set_limit(c, SPY_LIMIT_STEPS, 100000);
    spy_set_interrupt(c, count_polls, &polls);
    assert(spy_exec(c, "caught = 0\ntry:\n    while True: pass\nexcept BaseException:\n    caught = 1", "interrupt.py") == -1);
    assert(!strcmp(spy_error_message(c), "execution interrupted") && spy_stopped(c) == SPY_STOP_INTERRUPT);
    assert(polls == 10 && integer(c, spy_eval(c, "caught", "caught.py")) == 0);
    /* Steps used count up to the stop, then restart with the next call. */
    polls = 0;
    assert(spy_exec(c, "while True: pass", "interrupt.py") == -1);
    assert(spy_steps_used(c) > 9 * 4096 && spy_steps_used(c) < 10 * 4096 + 100);
    execute(c, "for i in range(1000): pass");
    assert(spy_steps_used(c) >= 1000 && spy_steps_used(c) < 1100);
    polls = -1000;
    assert(spy_exec(c, "while True: pass", "polled.py") == -1);
    assert(spy_stopped(c) == SPY_STOP_STEPS && polls >= -1000 + 100000 / 4096);
    /* Without a step limit, a native loop over an endless iterator polls. */
    polls = 0;
    spy_set_limit(c, SPY_LIMIT_STEPS, 0);
    const char *polled[] = {"sum(iter(int, 1))", "while True: pass", "for x in iter(int, 1): pass", "any(x for x in iter(int, 1))",
                            "[x for x in iter(int, 1)]"};
    for (size_t i = 0; i < sizeof(polled) / sizeof(*polled); i++) {
        polls = 0;
        assert(spy_exec(c, polled[i], "polled.py") == -1 && spy_stopped(c) == SPY_STOP_INTERRUPT);
    }
    /* Long native operations poll as they go. */
    spy_set_interrupt(c, NULL, NULL);
    execute(c, "big = 7 ** 10**6\nshuffled = [i * 2654435761 % 4000037 for i in range(4 * 10**6)]");
    spy_set_interrupt(c, count_polls, &polls);
    const char *native[] = {"big * big", "big // (1 << 10**6 | 1)", "hex(big)", "sorted(shuffled)"};
    for (size_t i = 0; i < sizeof(native) / sizeof(*native); i++) {
        polls = 5;
        assert(spy_exec(c, native[i], "native.py") == -1 && spy_stopped(c) == SPY_STOP_INTERRUPT && polls == 10);
    }
    execute(c, "del big, shuffled");
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
    spy_set_limit(c, SPY_LIMIT_STEPS, 500);
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
    spy_set_limit(c, SPY_LIMIT_STEPS, 0);
    assert(!spy_exec(c, "import _spy\nclass Ref:\n"
                        "    def __init__(self, target, callback): _spy._weak_bind(target, self, callback)\n"
                        "    def __call__(self): return _spy._weak_get(self)\n"
                        "class Node: pass\nseen = []\nn = Node(); n.me = n\n"
                        "wr = Ref(n, seen.append)\ndel n", "weak.py"));
    spy_collect(c);
    assert(!spy_exec(c, "pass\nassert wr() is None and seen == [wr], seen", "weak_check.py"));
    /* The weakly referenceable types are CPython's. */
    assert(!spy_exec(c, "def gen(): yield\nasync def co(): pass\nasync def agen(): yield\n"
                        "class K:\n    def m(self): pass\n"
                        "c = co()\n"
                        "for target in (Node, gen, {1}, frozenset(), gen(), c, agen(), gen.__code__, _spy, len, K().m, [].append):\n"
                        "    Ref(target, None)\n"
                        "c.close()\n"
                        "for target in (int.__add__, (1).__add__, 1, [], None, (), 'x', object(), range(1), 1.0):\n"
                        "    try: Ref(target, None)\n"
                        "    except TypeError as e: assert str(e) == f\"cannot create weak reference to '{type(target).__name__}' object\", e\n"
                        "    else: raise AssertionError(target)\n"
                        "for primitive, args, message in ((_spy._collect, (1,), 'expected no arguments'), (_spy._tracked, (), 'expected one argument'),\n"
                        "                                  (_spy._collection_limit, (-1,), 'the collection limit must not be negative'),\n"
                        "                                  (_spy._collection_limit, ('x',), \"'str' object cannot be interpreted as an integer\")):\n"
                        "    try: primitive(*args)\n"
                        "    except (TypeError, ValueError) as e: assert str(e) == message, e\n"
                        "    else: raise AssertionError(args)\n"
                        "assert _spy._collection_limit(0) == 2000 and _spy._collection_limit(2000) == 0\n"
                        "tracked = [_spy._tracked(x) for x in ((), (1,), ([],), frozenset(), frozenset({K()}), object(), K(), K, int)]\n"
                        "assert tracked == [False, False, True, False, True, False, True, True, False], tracked\n", "weak_types.py"));
    size_t before = spy_live_values(c);
    for (int i = 0; i < 3; i++) {
        assert(!spy_exec(c, "n = Node(); n.me = n; w = Ref(n, lambda r: None); del n, w", "weak_loop.py"));
        spy_collect(c);
    }
    assert(spy_live_values(c) <= before + 8);
    /* _spy.tokenize, spyc's view of the lexer: the decoded source with its
     * line ends normalized, each token's kind, byte span, line and bracket
     * depth after it, one ENDMARKER, and the lexer's and decoder's errors. */
    assert(!spy_exec(c, "import _spy\n"
                        "text, tokens = _spy.tokenize(b'# coding: latin-1\\r\\nf(\\xe9, 1)\\r', 'k.py')\n"
                        "assert text == b'# coding: latin-1\\nf(\\xc3\\xa9, 1)\\n', text\n"
                        "assert [(k, text[s:e], line, level) for k, s, e, line, level in tokens] == [\n"
                        "    ('NAME', b'f', 2, 0), ('OP', b'(', 2, 1), ('NAME', b'\\xc3\\xa9', 2, 1), ('OP', b',', 2, 1),\n"
                        "    ('NUMBER', b'1', 2, 1), ('OP', b')', 2, 0), ('NEWLINE', b'\\n', 2, 0), ('ENDMARKER', b'', 3, 0)], tokens\n"
                        "kinds = [t[0] for t in _spy.tokenize(b'if x:\\n    y = \\'s\\'\\n', 'k.py')[1]]\n"
                        "assert kinds == ['NAME', 'NAME', 'OP', 'NEWLINE', 'INDENT', 'NAME', 'OP', 'STRING', 'NEWLINE', 'DEDENT', 'ENDMARKER'], kinds\n"
                        "for args, error in (((b'x',), TypeError), (('x', 'k.py'), TypeError), ((b'x', 1), TypeError),\n"
                        "                    ((b'if x:\\n  a\\n b\\n', 'k.py'), IndentationError), ((b'\\xff', 'k.py'), SyntaxError),\n"
                        "                    ((b'# coding: nope\\n', 'k.py'), SyntaxError)):\n"
                        "    try: _spy.tokenize(*args)\n"
                        "    except error: pass\n"
                        "    else: raise AssertionError(args)\n", "tokenize.py"));


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

    /* Reached by nothing else in make test: frame-locals
     * merging, sys's digit limit and breakpoint hook, float.__getformat__,
     * wide and half-float memoryview items, dict-view equality, latin-9, and
     * lazy import. */
    execute(c,
        "import sys\n"
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
        "lazy import sys as lazy_sys\n"
        "assert lazy_sys.maxsize > 0\n");

    SPYContext *other = spy_context_new();
    assert(other);
    SPYValue *foreign = spy_int(other, 3);
    assert(spy_set_global(c, "foreign", foreign) == -1);
    spy_release(foreign); spy_context_free(other);
    spy_context_free(c);
    puts("C API: ownership, closures, cycles, imports, limits, mounts, and recovery passed");
    return 0;
}
