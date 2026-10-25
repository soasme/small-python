#include "spy.h"

#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* The parser owns a tree per source unit. Functions keep that unit and their
 * lexical environment alive. Every edge between values participates in GC. */
enum { V_ENV = SPY_GENERATOR + 1, V_UNIT, V_UNBOUND };
typedef struct Node Node;
typedef struct { SPYValue *key, *value; } Entry;
typedef struct { Node *clause; SPYValue *iterator; } GeneratorLoop;
struct Node {
    int kind, op;
    size_t line;
    char *text;
    Node *a, *b, *c, *args, *next, *allocated;
};
struct SPYValue {
    SPYContext *ctx;
    SPYValue *prev, *next, *pending;
    size_t refs, trial;
    int type, marked;
    union {
        int64_t integer;
        double real;
        struct { char *data; size_t len; } string;
        struct { SPYValue **items; size_t len, cap; } seq;
        struct { Entry *items; size_t len, cap; SPYValue *parent; int flags, native; } map;
        struct { Node *nodes, *body; char *filename; } unit;
        struct { SPYValue *unit, *env, *defaults; Node *def; } function;
        struct { SPYNative call; void *data; } native;
        struct { SPYValue *self; int method; } bound;
        struct { SPYValue *self, *function; } method;
        struct { int64_t start, stop, step; } range;
        struct { SPYValue *source; size_t index, size; int kind, done; int64_t count; } iterator;
        struct {
            SPYValue *env, *unit, *expanded;
            Node *node;
            GeneratorLoop *loops;
            size_t len, cap;
            int running, done;
        } generator;
    } as;
};
struct SPYContext {
    SPYValue *values, *globals, *builtins, *modules, *exception, *handled;
    SPYValue *types[SPY_GENERATOR + 1];
    SPYValue *none, *booleans[2];
    size_t live, steps, step_limit, depth;
    SPYWrite write;
    void *write_data;
    SPYModuleLoader loader;
    void *loader_data;
    char error_type[64], error_message[256], filename[256];
    size_t line;
};
static SPYValue *special_method(SPYContext *, SPYValue *, const char *);
static int subclass(SPYValue *, SPYValue *);

static SPYValue *errorf(SPYContext *c, const char *type, const char *fmt, ...) {
    if (!c->error_type[0]) {
        va_list ap;
        snprintf(c->error_type, sizeof(c->error_type), "%s", type);
        va_start(ap, fmt);
        vsnprintf(c->error_message, sizeof(c->error_message), fmt, ap);
        va_end(ap);
    }
    return NULL;
}
SPYValue *spy_error(SPYContext *c, const char *type, const char *message) {
    return errorf(c, type, "%s", message);
}
const char *spy_error_type(const SPYContext *c) { return c->error_type; }
const char *spy_error_message(const SPYContext *c) { return c->error_message; }
const char *spy_error_filename(const SPYContext *c) { return c->filename; }
size_t spy_error_line(const SPYContext *c) { return c->line; }
void spy_clear_error(SPYContext *c) {
    spy_release(c->exception); c->exception = NULL;
    c->error_type[0] = c->error_message[0] = c->filename[0] = 0;
    c->line = 0;
}
static void *allocate(SPYContext *c, size_t n) {
    void *p = calloc(1, n ? n : 1);
    if (!p) spy_error(c, "MemoryError", "allocation failed");
    return p;
}
static char *copy_text(SPYContext *c, const char *s, size_t n) {
    if (n == SIZE_MAX) { spy_error(c, "MemoryError", "string is too large"); return NULL; }
    char *p = allocate(c, n + 1);
    if (p && n) memcpy(p, s, n);
    return p;
}
static int grow(SPYContext *c, void **p, size_t *cap, size_t n, size_t width) {
    if (n <= *cap) return 0;
    size_t k = *cap ? *cap : 8;
    while (k < n) {
        if (k > SIZE_MAX / 2) goto fail;
        k *= 2;
    }
    if (k > SIZE_MAX / width) goto fail;
    void *q = realloc(*p, k * width);
    if (!q) goto fail;
    *p = q;
    *cap = k;
    return 0;
fail:
    spy_error(c, "MemoryError", "allocation too large");
    return -1;
}
static SPYValue *value_new(SPYContext *c, int type) {
    SPYValue *v = allocate(c, sizeof(*v));
    if (!v) return NULL;
    v->ctx = c;
    v->refs = 1;
    v->type = type;
    v->next = c->values;
    if (v->next) v->next->prev = v;
    c->values = v;
    c->live++;
    return v;
}
SPYValue *spy_retain(SPYValue *v) { if (v) v->refs++; return v; }
typedef void (*Visit)(SPYValue *, void *);
static void edges(SPYValue *v, Visit visit, void *data) {
    size_t i;
    switch (v->type) {
    case SPY_LIST: case SPY_TUPLE:
        for (i = 0; i < v->as.seq.len; i++) visit(v->as.seq.items[i], data);
        break;
    case SPY_DICT: case SPY_MODULE: case V_ENV: case SPY_CLASS: case SPY_INSTANCE: case SPY_SET:
        for (i = 0; i < v->as.map.len; i++) {
            visit(v->as.map.items[i].key, data);
            visit(v->as.map.items[i].value, data);
        }
        if (v->as.map.parent) visit(v->as.map.parent, data);
        break;
    case SPY_FUNCTION:
        visit(v->as.function.unit, data);
        visit(v->as.function.env, data);
        if (v->as.function.defaults) visit(v->as.function.defaults, data);
        break;
    case SPY_BOUND_METHOD: visit(v->as.bound.self, data); break;
    case SPY_ITERATOR: visit(v->as.iterator.source, data); break;
    case SPY_METHOD:
        visit(v->as.method.self, data); visit(v->as.method.function, data); break;
    case SPY_GENERATOR:
        if (v->as.generator.env) visit(v->as.generator.env, data);
        if (v->as.generator.unit) visit(v->as.generator.unit, data);
        if (v->as.generator.expanded) visit(v->as.generator.expanded, data);
        for (i = 0; i < v->as.generator.len; i++) visit(v->as.generator.loops[i].iterator, data);
        break;
    }
}
static void free_value(SPYValue *v) {
    SPYContext *c = v->ctx;
    if (v->prev) v->prev->next = v->next;
    else c->values = v->next;
    if (v->next) v->next->prev = v->prev;
    c->live--;
    switch (v->type) {
    case SPY_STRING: free(v->as.string.data); break;
    case SPY_GENERATOR: free(v->as.generator.loops); break;
    case SPY_LIST: case SPY_TUPLE: free(v->as.seq.items); break;
    case SPY_DICT: case SPY_MODULE: case V_ENV: case SPY_CLASS: case SPY_INSTANCE: case SPY_SET: free(v->as.map.items); break;
    case V_UNIT: {
        Node *n = v->as.unit.nodes;
        while (n) { Node *next = n->allocated; free(n->text); free(n); n = next; }
        free(v->as.unit.filename);
        break;
    }
    }
    free(v);
}
static void release_edge(SPYValue *v, void *data) {
    SPYValue **pending = data;
    if (--v->refs == 0) { v->pending = *pending; *pending = v; }
}
void spy_release(SPYValue *v) {
    SPYValue *pending = NULL;
    if (v) release_edge(v, &pending);
    while (pending) {
        v = pending; pending = v->pending;
        edges(v, release_edge, &pending);
        free_value(v);
    }
}
static void subtract_edge(SPYValue *v, void *unused) { (void)unused; v->trial--; }
typedef struct { SPYValue **items; size_t len; } Work;
static void mark_edge(SPYValue *v, void *data) {
    Work *work = data;
    if (!v->marked) { v->marked = 1; work->items[work->len++] = v; }
}
static void release_live_edge(SPYValue *v, void *unused) {
    (void)unused;
    if (v->marked) v->refs--;
}
size_t spy_collect(SPYContext *c) {
    if (!c->live) return 0;
    Work work = { malloc(c->live * sizeof(SPYValue *)), 0 };
    if (!work.items) return 0;
    for (SPYValue *v = c->values; v; v = v->next) { v->trial = v->refs; v->marked = 0; }
    for (SPYValue *v = c->values; v; v = v->next) edges(v, subtract_edge, NULL);
    for (SPYValue *v = c->values; v; v = v->next) if (v->trial) mark_edge(v, &work);
    for (size_t i = 0; i < work.len; i++) edges(work.items[i], mark_edge, &work);
    free(work.items);
    /* Inspect edges while every dead object still exists, then free storage. */
    for (SPYValue *v = c->values; v; v = v->next)
        if (!v->marked) edges(v, release_live_edge, NULL);
    size_t count = 0;
    for (SPYValue *v = c->values, *next; v; v = next) {
        next = v->next;
        if (!v->marked) { free_value(v); count++; }
    }
    return count;
}
size_t spy_live_values(const SPYContext *c) { return c->live; }
SPYType spy_type(const SPYValue *v) { return (SPYType)v->type; }
SPYValue *spy_none(SPYContext *c) { return spy_retain(c->none); }
SPYValue *spy_int(SPYContext *c, int64_t i) {
    SPYValue *v = value_new(c, SPY_INT);
    if (v) v->as.integer = i;
    return v;
}
SPYValue *spy_bool(SPYContext *c, int i) {
    return spy_retain(c->booleans[!!i]);
}
SPYValue *spy_float(SPYContext *c, double d) {
    SPYValue *v = value_new(c, SPY_FLOAT);
    if (v) v->as.real = d;
    return v;
}
SPYValue *spy_string(SPYContext *c, const char *s, size_t n) {
    SPYValue *v = value_new(c, SPY_STRING);
    if (!v) return NULL;
    v->as.string.data = copy_text(c, s, n);
    if (!v->as.string.data) { spy_release(v); return NULL; }
    v->as.string.len = n;
    return v;
}
SPYValue *spy_list(SPYContext *c) { return value_new(c, SPY_LIST); }
static int same_context(SPYContext *c, SPYValue *v) {
    if (!v || v->ctx != c) { spy_error(c, "ValueError", "value belongs to another context"); return 0; }
    return 1;
}
static int sequence_append(SPYContext *c, SPYValue *v, SPYValue *item) {
    if (!same_context(c, v) || !same_context(c, item)) return -1;
    if (v->type != SPY_LIST && v->type != SPY_TUPLE) {
        spy_error(c, "TypeError", "expected list"); return -1;
    }
    if (grow(c, (void **)&v->as.seq.items, &v->as.seq.cap,
             v->as.seq.len + 1, sizeof(SPYValue *))) return -1;
    v->as.seq.items[v->as.seq.len++] = spy_retain(item);
    return 0;
}
int spy_list_append(SPYContext *c, SPYValue *v, SPYValue *item) {
    if (!same_context(c, v)) return -1;
    if (v->type != SPY_LIST) { spy_error(c, "TypeError", "expected mutable list"); return -1; }
    return sequence_append(c, v, item);
}
static int is_int(SPYValue *v) { return v->type == SPY_INT || v->type == SPY_BOOL; }
static int is_number(SPYValue *v) { return is_int(v) || v->type == SPY_FLOAT; }
int spy_as_int(SPYContext *c, SPYValue *v, int64_t *out) {
    if (!v || !is_int(v)) { spy_error(c, "TypeError", "expected integer"); return -1; }
    *out = v->as.integer;
    return 0;
}
int spy_as_float(SPYContext *c, SPYValue *v, double *out) {
    if (!v || !is_number(v)) { spy_error(c, "TypeError", "expected number"); return -1; }
    *out = is_int(v) ? (double)v->as.integer : v->as.real;
    return 0;
}
const char *spy_as_string(SPYContext *c, SPYValue *v, size_t *n) {
    if (!v || v->type != SPY_STRING) { spy_error(c, "TypeError", "expected string"); return NULL; }
    if (n) *n = v->as.string.len;
    return v->as.string.data;
}
int spy_truth(SPYValue *v) {
    switch (v->type) {
    case SPY_NONE: return 0;
    case SPY_BOOL: case SPY_INT: return v->as.integer != 0;
    case SPY_FLOAT: return v->as.real != 0;
    case SPY_STRING: return v->as.string.len != 0;
    case SPY_LIST: case SPY_TUPLE: return v->as.seq.len != 0;
    case SPY_DICT: case SPY_SET: return v->as.map.len != 0;
    case SPY_RANGE: return v->as.range.step > 0 ? v->as.range.start < v->as.range.stop : v->as.range.start > v->as.range.stop;
    case SPY_INSTANCE: {
        SPYContext *c = v->ctx;
        SPYValue *method = special_method(c, v, "__bool__");
        int boolean = method != NULL;
        if (!method && !c->error_type[0]) method = special_method(c, v, "__len__");
        if (!method) return !c->error_type[0];
        SPYValue *result = spy_call(c, method, 0, NULL);
        spy_release(method);
        if (!result) return 0;
        int truth = 0;
        if (boolean && result->type != SPY_BOOL) spy_error(c, "TypeError", "__bool__ should return bool");
        else if (!boolean && !is_int(result)) spy_error(c, "TypeError", "__len__ should return an integer");
        else if (result->as.integer < 0) spy_error(c, "ValueError", "__len__() should return >= 0");
        else truth = result->as.integer != 0;
        spy_release(result); return truth;
    }
    default: return 1;
    }
}
/* Compare integers against floats without first rounding the integer to double.
 * Returns 2 for unordered (NaN). This also works where long double == double. */
static int numeric_order(SPYValue *a, SPYValue *b) {
    if (is_int(a) && is_int(b)) return a->as.integer < b->as.integer ? -1 : a->as.integer > b->as.integer;
    if (a->type == SPY_FLOAT && b->type == SPY_FLOAT) {
        double x = a->as.real, y = b->as.real;
        return isnan(x) || isnan(y) ? 2 : x < y ? -1 : x > y;
    }
    int reverse = a->type == SPY_FLOAT;
    int64_t i = reverse ? b->as.integer : a->as.integer;
    double d = reverse ? a->as.real : b->as.real;
    if (isnan(d)) return 2;
    int order;
    if (d >= 9223372036854775808.0) order = -1;
    else if (d < -9223372036854775808.0) order = 1;
    else {
        int64_t truncated = (int64_t)d;
        order = i < truncated ? -1 : i > truncated ? 1 : (double)truncated < d ? -1 : (double)truncated > d;
    }
    return reverse ? -order : order;
}
static int equal(SPYValue *a, SPYValue *b, size_t depth) {
    if (a == b) return a->type != SPY_FLOAT || !isnan(a->as.real);
    if (is_int(a) && is_int(b)) return a->as.integer == b->as.integer;
    if (is_number(a) && is_number(b)) {
        return numeric_order(a, b) == 0;
    }
    if (a->type != b->type) return 0;
    switch (a->type) {
    case SPY_NONE: return 1;
    case SPY_STRING:
        return a->as.string.len == b->as.string.len &&
            !memcmp(a->as.string.data, b->as.string.data, a->as.string.len);
    case SPY_DICT: case SPY_SET:
        if (depth > 128) { spy_error(a->ctx, "RecursionError", "recursive comparison"); return 0; }
        if (a->as.map.len != b->as.map.len) return 0;
        for (size_t i = 0; i < a->as.map.len; i++) {
            size_t j;
            for (j = 0; j < b->as.map.len; j++)
                if (equal(a->as.map.items[i].key, b->as.map.items[j].key, depth + 1)) break;
            if (j == b->as.map.len || (a->as.map.items[i].value != b->as.map.items[j].value &&
                !equal(a->as.map.items[i].value, b->as.map.items[j].value, depth + 1))) return 0;
        }
        return 1;
    case SPY_LIST: case SPY_TUPLE:
        if (depth > 128) { spy_error(a->ctx, "RecursionError", "recursive comparison"); return 0; }
        if (a->as.seq.len != b->as.seq.len) return 0;
        for (size_t i = 0; i < a->as.seq.len; i++)
            if (a->as.seq.items[i] != b->as.seq.items[i] && !equal(a->as.seq.items[i], b->as.seq.items[i], depth + 1)) return 0;
        return 1;
    default: return 0;
    }
}
static int hashable(SPYValue *v, size_t depth) {
    if (depth > 128) return 0;
    if (v->type == SPY_LIST || v->type == SPY_DICT || v->type == SPY_SET) return 0;
    if (v->type == SPY_TUPLE)
        for (size_t i = 0; i < v->as.seq.len; i++)
            if (!hashable(v->as.seq.items[i], depth + 1)) return 0;
    return 1;
}
static ptrdiff_t map_find(SPYValue *map, SPYValue *key) {
    for (size_t i = 0; i < map->as.map.len; i++)
        if (equal(map->as.map.items[i].key, key, 0)) return (ptrdiff_t)i;
    return -1;
}
static int map_set(SPYContext *c, SPYValue *map, SPYValue *key, SPYValue *value) {
    if (!hashable(key, 0)) { spy_error(c, "TypeError", "unhashable key"); return -1; }
    ptrdiff_t i = map_find(map, key);
    if (i >= 0) {
        SPYValue *old = map->as.map.items[i].value;
        map->as.map.items[i].value = spy_retain(value);
        spy_release(old);
        return 0;
    }
    if (grow(c, (void **)&map->as.map.items, &map->as.map.cap,
             map->as.map.len + 1, sizeof(Entry))) return -1;
    map->as.map.items[map->as.map.len++] = (Entry){spy_retain(key), spy_retain(value)};
    return 0;
}
static SPYValue *name_local(SPYValue *env, const char *name) {
    for (size_t i = 0; i < env->as.map.len; i++) {
        Entry *e = &env->as.map.items[i];
        if (!strcmp(e->key->as.string.data, name)) return e->value;
    }
    return NULL;
}
static const char *type_name(SPYValue *value) {
    static const char *names[] = {"NoneType", "bool", "int", "float", "str", "list", "tuple", "dict", "function",
        "builtin_function_or_method", "module", "range", "builtin_function_or_method", "iterator", "type", "object", "method", "set", "generator"};
    if (value->type == SPY_INSTANCE) {
        SPYValue *name = name_local(value->as.map.parent, "__name__");
        if (name && name->type == SPY_STRING) return name->as.string.data;
    }
    return value->type <= SPY_GENERATOR ? names[value->type] : "object";
}
static SPYValue *name_get(SPYContext *c, SPYValue *env, const char *name) {
    for (SPYValue *e = env; e; e = e->as.map.parent) {
        SPYValue *v = name_local(e, name);
        if (v) {
            if (v->type == V_UNBOUND) return errorf(c, "UnboundLocalError", "local variable '%s' has no value", name);
            return spy_retain(v);
        }
    }
    return errorf(c, "NameError", "name '%s' is not defined", name);
}
static int name_set(SPYContext *c, SPYValue *env, const char *name, SPYValue *v) {
    SPYValue *key = spy_string(c, name, strlen(name));
    if (!key) return -1;
    int status = map_set(c, env, key, v);
    spy_release(key);
    return status;
}
SPYValue *spy_get_global(SPYContext *c, const char *name) { return name_get(c, c->globals, name); }
int spy_set_global(SPYContext *c, const char *name, SPYValue *v) {
    return same_context(c, v) ? name_set(c, c->globals, name, v) : -1;
}
int spy_define(SPYContext *c, const char *name, SPYNative call, void *data) {
    SPYValue *v = value_new(c, SPY_NATIVE);
    if (!v) return -1;
    v->as.native.call = call;
    v->as.native.data = data;
    int status = name_set(c, c->globals, name, v);
    spy_release(v);
    return status;
}

typedef struct { SPYContext *ctx; char *data; size_t len, cap; SPYValue *path[128]; size_t depth; } Buffer;
static int append(Buffer *b, const char *s, size_t n) {
    if (n > SIZE_MAX - b->len - 1 || grow(b->ctx, (void **)&b->data, &b->cap, b->len + n + 1, 1)) return -1;
    memcpy(b->data + b->len, s, n);
    b->len += n;
    b->data[b->len] = 0;
    return 0;
}
static int puts_buffer(Buffer *b, const char *s) { return append(b, s, strlen(s)); }
static void format_float(char *out, size_t size, double value) {
    if (!isfinite(value)) { snprintf(out, size, "%g", value); return; }
    char scientific[64], digits[24];
    for (int precision = 0; precision <= 16; precision++) {
        snprintf(scientific, sizeof(scientific), "%.*e", precision, value);
        if (strtod(scientific, NULL) == value) break;
    }
    const char *p = scientific;
    const char *exponent_start = strchr(scientific, 'e');
    if (!exponent_start) { snprintf(out, size, "%g", value); return; }
    size_t at = 0, n = 0;
    if (*p == '-') { out[at++] = *p++; }
    while (p < exponent_start) { if (*p != '.') digits[n++] = *p; p++; }
    if (!n) { snprintf(out, size, "%g", value); return; }
    int exponent = atoi(exponent_start + 1);
    if (exponent < -4 || exponent >= 16) {
        out[at++] = digits[0];
        if (n > 1) { out[at++] = '.'; memcpy(out + at, digits + 1, n - 1); at += n - 1; }
        snprintf(out + at, size - at, "e%+03d", exponent);
    } else if (exponent < 0) {
        out[at++] = '0'; out[at++] = '.';
        for (int i = -1; i > exponent; i--) out[at++] = '0';
        memcpy(out + at, digits, n); at += n; out[at] = 0;
    } else {
        size_t whole = (size_t)exponent + 1;
        for (size_t i = 0; i < whole; i++) out[at++] = i < n ? digits[i] : '0';
        out[at++] = '.';
        if (n > whole) { memcpy(out + at, digits + whole, n - whole); at += n - whole; }
        else out[at++] = '0';
        out[at] = 0;
    }
}
static int format_value(Buffer *b, SPYValue *v, int repr) {
    char num[96];
    switch (v->type) {
    case SPY_NONE: return puts_buffer(b, "None");
    case SPY_BOOL: return puts_buffer(b, v->as.integer ? "True" : "False");
    case SPY_INT:
        snprintf(num, sizeof(num), "%" PRId64, v->as.integer);
        return puts_buffer(b, num);
    case SPY_FLOAT:
        format_float(num, sizeof(num), v->as.real);
        return puts_buffer(b, num);
    case SPY_STRING:
        if (!repr) return append(b, v->as.string.data, v->as.string.len);
        if (puts_buffer(b, "'")) return -1;
        for (size_t i = 0; i < v->as.string.len; i++) {
            unsigned char ch = (unsigned char)v->as.string.data[i];
            const char *escape = ch == '\n' ? "\\n" : ch == '\r' ? "\\r" : ch == '\t' ? "\\t" :
                ch == '\\' ? "\\\\" : ch == '\'' ? "\\'" : NULL;
            if (escape) { if (puts_buffer(b, escape)) return -1; }
            else if (ch < 32 || ch == 127) {
                snprintf(num, sizeof(num), "\\x%02x", ch);
                if (puts_buffer(b, num)) return -1;
            } else if (append(b, (const char *)&ch, 1)) return -1;
        }
        return puts_buffer(b, "'");
    case SPY_LIST: case SPY_TUPLE: case SPY_DICT: case SPY_SET: {
        if (v->type == SPY_SET && !v->as.map.len) return puts_buffer(b, "set()");
        for (size_t i = 0; i < b->depth; i++)
            if (b->path[i] == v) return puts_buffer(b, v->type == SPY_LIST ? "[...]" : v->type == SPY_DICT ? "{...}" : "(...)");
        if (b->depth == 128) { spy_error(b->ctx, "RecursionError", "representation is too deep"); return -1; }
        b->path[b->depth++] = v;
        int dict = v->type == SPY_DICT || v->type == SPY_SET;
        if (puts_buffer(b, dict ? "{" : v->type == SPY_LIST ? "[" : "(")) return -1;
        size_t n = dict ? v->as.map.len : v->as.seq.len;
        for (size_t i = 0; i < n; i++) {
            if (i && puts_buffer(b, ", ")) return -1;
            if (dict) {
                if (format_value(b, v->as.map.items[i].key, 1)) return -1;
                if (v->type == SPY_DICT && (puts_buffer(b, ": ") || format_value(b, v->as.map.items[i].value, 1))) return -1;
            } else if (format_value(b, v->as.seq.items[i], 1)) return -1;
        }
        if (v->type == SPY_TUPLE && n == 1 && puts_buffer(b, ",")) return -1;
        b->depth--;
        return puts_buffer(b, dict ? "}" : v->type == SPY_LIST ? "]" : ")");
    }
    case SPY_FUNCTION: return puts_buffer(b, "<function>");
    case SPY_MODULE: return puts_buffer(b, "<module>");
    case SPY_CLASS: {
        SPYValue *name = name_local(v, "__qualname__"), *module = name_local(v, "__module__");
        if (puts_buffer(b, "<class '")) return -1;
        if (module && strcmp(module->as.string.data, "builtins") &&
            (puts_buffer(b, module->as.string.data) || puts_buffer(b, "."))) return -1;
        return puts_buffer(b, name->as.string.data) || puts_buffer(b, "'>") ? -1 : 0;
    }
    case SPY_INSTANCE: {
        if (++b->ctx->depth > 256) { b->ctx->depth--; spy_error(b->ctx, "RecursionError", "representation nesting limit exceeded"); return -1; }
        SPYValue *method = special_method(b->ctx, v, repr ? "__repr__" : "__str__");
        if (!method && !repr) method = special_method(b->ctx, v, "__repr__");
        if (method) {
            SPYValue *text = spy_call(b->ctx, method, 0, NULL);
            spy_release(method);
            int status = -1;
            if (text && text->type == SPY_STRING) status = append(b, text->as.string.data, text->as.string.len);
            else if (text) spy_error(b->ctx, "TypeError", "string conversion returned a non-string");
            spy_release(text); b->ctx->depth--; return status;
        }
        SPYValue *args = name_local(v, "args");
        int status = 0;
        if (args && args->type == SPY_TUPLE && subclass(v->as.map.parent, name_local(b->ctx->builtins, "BaseException"))) {
            if (repr) {
                status = puts_buffer(b, type_name(v)) || puts_buffer(b, "(");
                for (size_t i = 0; i < args->as.seq.len && !status; i++)
                    status = (i && puts_buffer(b, ", ")) || format_value(b, args->as.seq.items[i], 1);
                if (!status) status = puts_buffer(b, ")");
            } else if (args->as.seq.len) status = format_value(b, args->as.seq.len == 1 ? args->as.seq.items[0] : args,
                args->as.seq.len == 1 && subclass(v->as.map.parent, name_local(b->ctx->builtins, "KeyError")));
        } else {
            SPYValue *module = name_local(v->as.map.parent, "__module__");
            snprintf(num, sizeof(num), " object at %p>", (void *)v);
            status = puts_buffer(b, "<") || puts_buffer(b, module->as.string.data) || puts_buffer(b, ".") || puts_buffer(b, type_name(v)) || puts_buffer(b, num);
        }
        b->ctx->depth--; return status ? -1 : 0;
    }
    case SPY_GENERATOR:
        snprintf(num, sizeof(num), "<generator object <genexpr> at %p>", (void *)v);
        return puts_buffer(b, num);
    case SPY_RANGE:
        snprintf(num, sizeof(num), "range(%" PRId64 ", %" PRId64 ", %" PRId64 ")",
                 v->as.range.start, v->as.range.stop, v->as.range.step);
        return puts_buffer(b, num);
    default: return puts_buffer(b, "<built-in function>");
    }
}
static SPYValue *stringify(SPYContext *c, SPYValue *v, int repr) {
    Buffer b = { .ctx = c };
    SPYValue *result = NULL;
    if (!format_value(&b, v, repr)) result = spy_string(c, b.data ? b.data : "", b.len);
    free(b.data);
    return result;
}
SPYValue *spy_repr(SPYContext *c, SPYValue *v) { return stringify(c, v, 1); }

enum {
    T_END = 256, T_NAME, T_INT, T_FLOAT, T_STRING, T_NL, T_INDENT, T_DEDENT,
    T_EQ, T_NE, T_LE, T_GE, T_POW, T_FLOORDIV, T_LSHIFT, T_RSHIFT,
    T_ADDEQ, T_SUBEQ, T_MULEQ, T_DIVEQ, T_MODEQ, T_WALRUS,
    O_AND, O_OR, O_NOT, O_IN, O_NOTIN, O_IS, O_ISNOT
};
enum {
    N_INT, N_FLOAT, N_STRING, N_NAME, N_NONE, N_BOOL, N_LIST, N_TUPLE, N_DICT,
    N_UNARY, N_BINARY, N_COMPARE, N_CALL, N_INDEX, N_ATTR, N_COND,
    N_EXPR, N_ASSIGN, N_IF, N_WHILE, N_FOR, N_DEF, N_RETURN, N_BREAK,
    N_CONTINUE, N_PASS, N_ASSERT, N_IMPORT, N_FROM, N_STAR, N_COMPREHENSION, N_MAPPING,
    N_CLASS, N_RAISE, N_TRY, N_EXCEPT, N_SET, N_KEYWORD, N_LAMBDA, N_NAMED, N_WITH, N_DELETE
};
enum { P_POSITIONAL, P_POSONLY, P_VARARGS, P_KWONLY, P_KWARGS };
typedef struct { int kind; const char *start; size_t len, line; } Token;
typedef struct {
    SPYContext *ctx;
    Token *tokens;
    size_t len, cap, pos, depth;
    int functions, loops;
    SPYValue *unit;
} Parser;
static int token_add(Parser *p, int kind, const char *s, size_t n, size_t line) {
    if (grow(p->ctx, (void **)&p->tokens, &p->cap, p->len + 1, sizeof(Token))) return -1;
    p->tokens[p->len++] = (Token){kind, s, n, line};
    return 0;
}
static int lex(Parser *p, const char *s) {
    size_t line = 1, indents[128] = {0}, level = 0, brackets = 0;
    char closing[128];
    int bol = 1;
    while (*s) {
        if (bol && !brackets) {
            size_t indent = 0;
            while (*s == ' ' || *s == '\t') {
                if (*s++ == '\t') {
                    p->ctx->line = line;
                    spy_error(p->ctx, "TabError", "tabs in indentation are not supported; use spaces");
                    return -1;
                }
                indent++;
            }
            if (*s && *s != '#' && *s != '\n' && *s != '\r') {
                if (indent > indents[level]) {
                    if (level == 127) goto nesting;
                    indents[++level] = indent;
                    if (token_add(p, T_INDENT, s, 0, line)) return -1;
                } else {
                    while (indent < indents[level]) {
                        level--;
                        if (token_add(p, T_DEDENT, s, 0, line)) return -1;
                    }
                    if (indent != indents[level]) {
                        p->ctx->line = line;
                        spy_error(p->ctx, "IndentationError", "unindent does not match an outer level");
                        return -1;
                    }
                }
            }
            bol = 0;
        }
        if (*s == ' ' || *s == '\t' || *s == '\r') { s++; continue; }
        if (*s == '#') { while (*s && *s != '\n') s++; continue; }
        if (*s == '\\' && (s[1] == '\n' || (s[1] == '\r' && s[2] == '\n'))) {
            s += s[1] == '\r' ? 3 : 2;
            line++;
            continue;
        }
        if (*s == '\n') {
            if (!brackets && p->len && p->tokens[p->len - 1].kind != T_NL &&
                token_add(p, T_NL, s, 1, line)) return -1;
            s++; line++; bol = 1; continue;
        }
        const char *start = s;
        bol = 0;
        int kind = (unsigned char)*s++;
        if (isalpha((unsigned char)*start) || *start == '_') {
            while (isalnum((unsigned char)*s) || *s == '_') s++;
            kind = T_NAME;
        } else if (isdigit((unsigned char)*start) || (*start == '.' && isdigit((unsigned char)*s))) {
            int dot = *start == '.';
            if (*start == '0' && (*s == 'x' || *s == 'X' || *s == 'o' || *s == 'O' || *s == 'b' || *s == 'B')) {
                s++;
                while (isalnum((unsigned char)*s) || *s == '_') s++;
            } else {
                while (isdigit((unsigned char)*s) || *s == '_') s++;
                if (*s == '.' && !dot) { dot = 1; s++; while (isdigit((unsigned char)*s) || *s == '_') s++; }
                if (*s == 'e' || *s == 'E') {
                    dot = 1; s++;
                    if (*s == '+' || *s == '-') s++;
                    while (isdigit((unsigned char)*s) || *s == '_') s++;
                }
            }
            kind = dot ? T_FLOAT : T_INT;
        } else if (*start == '\'' || *start == '"') {
            int quote = *start, triple = s[0] == quote && s[1] == quote;
            if (triple) s += 2;
            for (;;) {
                if (!*s || (!triple && *s == '\n')) {
                    p->ctx->line = line;
                    spy_error(p->ctx, "SyntaxError", "unterminated string literal"); return -1;
                }
                if (*s == quote && (!triple || (s[1] == quote && s[2] == quote))) { s += triple ? 3 : 1; break; }
                if (*s == '\\' && s[1]) { s++; if (*s == '\n') line++; s++; }
                else { if (*s == '\n') line++; s++; }
            }
            kind = T_STRING;
        } else {
            const char *pairs[] = {"==", "!=", "<=", ">=", "**", "//", "<<", ">>", "+=", "-=", "*=", "/=", "%=", ":="};
            const int kinds[] = {T_EQ, T_NE, T_LE, T_GE, T_POW, T_FLOORDIV, T_LSHIFT, T_RSHIFT, T_ADDEQ, T_SUBEQ, T_MULEQ, T_DIVEQ, T_MODEQ, T_WALRUS};
            for (size_t i = 0; i < sizeof(kinds) / sizeof(*kinds); i++)
                if (start[0] == pairs[i][0] && *s == pairs[i][1]) { kind = kinds[i]; s++; break; }
            if (kind == '(' || kind == '[' || kind == '{') {
                if (brackets == 128) goto nesting;
                closing[brackets++] = kind == '(' ? ')' : kind == '[' ? ']' : '}';
            } else if (kind == ')' || kind == ']' || kind == '}') {
                if (!brackets || closing[--brackets] != kind) {
                    p->ctx->line = line;
                    spy_error(p->ctx, "SyntaxError", "mismatched closing delimiter"); return -1;
                }
            } else if (kind < 256 && !strchr("+-*/%~&|^<>=:;.,", kind)) {
                p->ctx->line = line;
                spy_error(p->ctx, "SyntaxError", "unsupported character"); return -1;
            }
        }
        if (token_add(p, kind, start, (size_t)(s - start), line)) return -1;
    }
    if (brackets) { spy_error(p->ctx, "SyntaxError", "unclosed delimiter"); return -1; }
    if (p->len && p->tokens[p->len - 1].kind != T_NL && token_add(p, T_NL, s, 0, line)) return -1;
    while (level--) if (token_add(p, T_DEDENT, s, 0, line)) return -1;
    return token_add(p, T_END, s, 0, line);
nesting:
    p->ctx->line = line;
    spy_error(p->ctx, "SyntaxError", "too many nested blocks or delimiters"); return -1;
}
static Token *peek(Parser *p) { return &p->tokens[p->pos]; }
static int at(Parser *p, int kind) { return peek(p)->kind == kind; }
static int keyword(Parser *p, const char *s) {
    Token *t = peek(p);
    return t->kind == T_NAME && strlen(s) == t->len && !memcmp(s, t->start, t->len);
}
static int take(Parser *p, int kind) { if (!at(p, kind)) return 0; p->pos++; return 1; }
static int take_word(Parser *p, const char *s) { if (!keyword(p, s)) return 0; p->pos++; return 1; }
static Node *syntax(Parser *p, const char *message) {
    p->ctx->line = peek(p)->line;
    spy_error(p->ctx, "SyntaxError", message);
    return NULL;
}
static int expect(Parser *p, int kind, const char *message) {
    if (take(p, kind)) return 1;
    syntax(p, message); return 0;
}
static Node *node(Parser *p, int kind) {
    Node *n = allocate(p->ctx, sizeof(*n));
    if (n) {
        n->kind = kind; n->line = peek(p)->line;
        n->allocated = p->unit->as.unit.nodes;
        p->unit->as.unit.nodes = n;
    }
    return n;
}
static int reserved(Token *t) {
    static const char *words[] = {"False", "None", "True", "and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with", "yield"};
    for (size_t i = 0; i < sizeof(words) / sizeof(*words); i++)
        if (strlen(words[i]) == t->len && !memcmp(words[i], t->start, t->len)) return 1;
    return 0;
}
static Node *identifier(Parser *p) {
    if (!at(p, T_NAME) || reserved(peek(p))) return syntax(p, "expected identifier");
    Node *n = node(p, N_NAME);
    if (!n) return NULL;
    Token *t = peek(p);
    n->text = copy_text(p->ctx, t->start, t->len);
    p->pos++;
    return n->text ? n : NULL;
}
static Node *expression(Parser *, int);
static Node *expression_list(Parser *, int);
static Node *comprehension(Parser *, Node *);
static Node *statements(Parser *);
static Node *suite(Parser *);
static int parameters(Parser *p, Node *n, int close) {
    Node **tail = &n->args;
    int keyword_only = 0, slash = 0, defaults = 0, bare_star = 0;
    while (!at(p, close)) {
        if (take(p, '/')) {
            if (slash || keyword_only || !n->args) { syntax(p, "invalid positional-only marker"); return -1; }
            slash = 1;
            for (Node *arg = n->args; arg; arg = arg->next) arg->op = P_POSONLY;
        } else {
            int kind = keyword_only ? P_KWONLY : P_POSITIONAL;
            if (take(p, T_POW)) kind = P_KWARGS;
            else if (take(p, '*')) {
                if (keyword_only) { syntax(p, "duplicate star parameter"); return -1; }
                keyword_only = 1;
                if (take(p, ',')) { bare_star = 1; continue; }
                kind = P_VARARGS;
            }
            Node *arg = identifier(p);
            if (!arg) return -1;
            for (Node *a = n->args; a; a = a->next)
                if (!strcmp(a->text, arg->text)) { syntax(p, "duplicate argument"); return -1; }
            arg->op = kind;
            if (take(p, '=')) {
                if (kind == P_VARARGS || kind == P_KWARGS) { syntax(p, "variadic parameter cannot have a default"); return -1; }
                if (!(arg->a = expression(p, 0))) return -1;
                if (kind == P_POSITIONAL) defaults = 1;
            } else if (kind == P_POSITIONAL && defaults) { syntax(p, "parameter without a default follows parameter with a default"); return -1; }
            *tail = arg; tail = &arg->next;
            if (kind == P_KWONLY) bare_star = 0;
            if (kind == P_KWARGS) {
                take(p, ',');
                if (!at(p, close)) { syntax(p, "arguments cannot follow var-keyword argument"); return -1; }
                break;
            }
        }
        if (!take(p, ',')) break;
    }
    if (bare_star) { syntax(p, "named arguments must follow bare star"); return -1; }
    return expect(p, close, "expected end of parameters") ? 0 : -1;
}
static int hex_digit(int c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
static Node *string_node(Parser *p) {
    Node *n = node(p, N_STRING);
    if (!n) return NULL;
    Buffer b = { .ctx = p->ctx };
    do {
        Token *t = peek(p);
        size_t quote = t->len >= 6 && t->start[0] == t->start[1] && t->start[1] == t->start[2] ? 3 : 1;
        for (size_t i = quote; i < t->len - quote; i++) {
            char ch = t->start[i];
            if (ch == '\\') {
                ch = t->start[++i];
                if (ch == 'n') ch = '\n';
                else if (ch == 't') ch = '\t';
                else if (ch == 'r') ch = '\r';
                else if (ch == 'a') ch = '\a';
                else if (ch == 'b') ch = '\b';
                else if (ch == 'f') ch = '\f';
                else if (ch == 'v') ch = '\v';
                else if (ch == '\n') continue;
                else if (ch == 'x') {
                    if (i + 2 >= t->len - quote || hex_digit(t->start[i + 1]) < 0 || hex_digit(t->start[i + 2]) < 0) {
                        syntax(p, "invalid hexadecimal escape"); goto fail;
                    }
                    ch = (char)(hex_digit(t->start[i + 1]) * 16 + hex_digit(t->start[i + 2])); i += 2;
                } else if (ch != '\\' && ch != '\'' && ch != '"') {
                    syntax(p, "unsupported string escape"); goto fail;
                }
            }
            if (append(&b, &ch, 1)) goto fail;
        }
        p->pos++;
    } while (at(p, T_STRING));
    n->text = b.data ? b.data : copy_text(p->ctx, "", 0);
    /* Literal length includes embedded NUL characters. */
    if (b.len > INT_MAX) { syntax(p, "string literal too large"); return NULL; }
    n->op = (int)b.len;
    return n->text ? n : NULL;
fail:
    free(b.data); return NULL;
}
static Node *atom(Parser *p) {
    Node *n;
    if (at(p, T_STRING)) return string_node(p);
    if (at(p, T_INT) || at(p, T_FLOAT)) {
        n = node(p, at(p, T_INT) ? N_INT : N_FLOAT);
        if (!n) return NULL;
        Token *t = peek(p);
        n->text = copy_text(p->ctx, t->start, t->len);
        p->pos++;
        return n->text ? n : NULL;
    }
    if (keyword(p, "None") || keyword(p, "True") || keyword(p, "False")) {
        n = node(p, keyword(p, "None") ? N_NONE : N_BOOL);
        if (!n) return NULL;
        n->op = keyword(p, "True"); p->pos++; return n;
    }
    if (at(p, T_NAME)) return identifier(p);
    int open = peek(p)->kind;
    if (open != '(' && open != '[' && open != '{') return syntax(p, "expected expression");
    n = node(p, open == '[' ? N_LIST : open == '{' ? N_DICT : N_TUPLE);
    if (!n) return NULL;
    p->pos++;
    int close = open == '[' ? ']' : open == '{' ? '}' : ')';
    Node **tail = &n->args;
    if (!at(p, close)) {
        do {
            Node *item;
            if (take(p, T_POW)) {
                item = node(p, N_MAPPING);
                if (!item || !(item->a = expression(p, 4))) return NULL;
                if (open != '{') return syntax(p, keyword(p, "for") ?
                    (open == '[' ? "cannot use dict unpacking in list comprehension" : "cannot use dict unpacking in generator expression") : "cannot use dict unpacking here");
            } else if (take(p, '*')) {
                item = node(p, N_STAR);
                if (!item || !(item->a = expression(p, 4))) return NULL;
            } else item = expression(p, 0);
            if (!item) return NULL;
            if ((item->kind == N_STAR || item->kind == N_MAPPING) && keyword(p, "if"))
                return syntax(p, item->kind == N_STAR ?
                    "invalid starred expression. Did you forget to wrap the conditional expression in parentheses?" :
                    "invalid double starred expression. Did you forget to wrap the conditional expression in parentheses?");
            if (item->kind == N_MAPPING && at(p, ':')) return syntax(p, "cannot use dict unpacking in a dictionary key");
            if (open == '{' && item->kind != N_MAPPING && at(p, ':')) {
                if (item->kind == N_STAR) return syntax(p, "cannot use a starred expression in a dictionary key");
                if (n->kind == N_SET) return syntax(p, "invalid set display");
                Node *pair = node(p, N_ASSIGN);
                if (!pair || !expect(p, ':', "expected ':' in dictionary")) return NULL;
                pair->a = item;
                if (at(p, '*')) return syntax(p, "cannot use a starred expression in a dictionary value");
                if (at(p, T_POW)) return syntax(p, "cannot use dict unpacking in a dictionary value");
                pair->b = expression(p, 0);
                if (!pair->b) return NULL;
                item = pair;
            } else if (open == '{' && item->kind != N_MAPPING) {
                if (n->args && n->kind == N_DICT) return syntax(p, "expected ':' in dictionary");
                n->kind = N_SET;
            } else if (open == '{' && n->kind == N_SET) {
                return syntax(p, "cannot use dict unpacking in set display");
            }
            *tail = item; tail = &item->next;
            if (keyword(p, "for")) {
                if (!comprehension(p, n)) return NULL;
                if (at(p, ':') && item->kind == N_MAPPING) return syntax(p, "cannot use dict unpacking here");
                break;
            }
            if (!take(p, ',')) {
                if (open == '(' && n->args == item) {
                    if (item->kind == N_STAR) return syntax(p, "cannot use starred expression here");
                    if (item->kind == N_NAMED) item->op = 1;
                    return expect(p, close, "expected ')'") ? item : NULL;
                }
                break;
            }
        } while (!at(p, close));
    }
    return expect(p, close, "expected closing delimiter") ? n : NULL;
}
static int operator_info(Parser *p, int *width, int *prec) {
    int op = peek(p)->kind;
    *width = 1;
    if (keyword(p, "or")) op = O_OR;
    else if (keyword(p, "and")) op = O_AND;
    else if (keyword(p, "in")) op = O_IN;
    else if (keyword(p, "is")) {
        op = O_IS;
        p->pos++; if (keyword(p, "not")) { op = O_ISNOT; *width = 2; } p->pos--;
    } else if (keyword(p, "not")) {
        p->pos++; int in = keyword(p, "in"); p->pos--;
        if (in) { op = O_NOTIN; *width = 2; }
    }
    switch (op) {
    case O_OR: *prec = 1; break;
    case O_AND: *prec = 2; break;
    case T_EQ: case T_NE: case '<': case '>': case T_LE: case T_GE:
    case O_IN: case O_NOTIN: case O_IS: case O_ISNOT: *prec = 3; break;
    case '|': *prec = 4; break;
    case '^': *prec = 5; break;
    case '&': *prec = 6; break;
    case T_LSHIFT: case T_RSHIFT: *prec = 7; break;
    case '+': case '-': *prec = 8; break;
    case '*': case '/': case T_FLOORDIV: case '%': *prec = 9; break;
    case T_POW: *prec = 11; break;
    default: *prec = -1; break;
    }
    return op;
}
static Node *expression_inner(Parser *p, int min) {
    Node *left;
    if (keyword(p, "lambda")) {
        if (min) return syntax(p, "invalid lambda expression");
        p->pos++;
        left = node(p, N_LAMBDA);
        if (!left || !(left->a = node(p, N_NAME))) return NULL;
        left->a->text = copy_text(p->ctx, "<lambda>", 8);
        if (!left->a->text || parameters(p, left, ':')) return NULL;
        left->b = node(p, N_RETURN);
        if (!left->b || !(left->b->a = expression(p, 0))) return NULL;
        return left;
    } else if (at(p, '+') || at(p, '-') || at(p, '~') || keyword(p, "not")) {
        if (keyword(p, "not") && min > 3) return syntax(p, "invalid 'not' expression");
        left = node(p, N_UNARY);
        if (!left) return NULL;
        left->op = keyword(p, "not") ? O_NOT : peek(p)->kind;
        p->pos++;
        left->a = expression(p, left->op == O_NOT ? 3 : 10);
        if (!left->a) return NULL;
    } else {
        left = atom(p);
        if (!left) return NULL;
        while (at(p, '(') || at(p, '[') || at(p, '.')) {
            int kind = peek(p)->kind;
            Node *n = node(p, kind == '(' ? N_CALL : kind == '[' ? N_INDEX : N_ATTR);
            if (!n) return NULL;
            n->a = left; p->pos++;
            if (kind == '.') {
                n->b = identifier(p);
                if (!n->b) return NULL;
            } else if (kind == '[') {
                n->b = expression(p, 0);
                if (!n->b || !expect(p, ']', "expected ']'")) return NULL;
            } else {
                Node **tail = &n->args;
                int keywords = 0, mapping = 0;
                if (!at(p, ')')) do {
                    Node *arg;
                    if (take(p, '*') || (at(p, T_POW) && (p->pos++, 1))) {
                        int unpack_mapping = p->tokens[p->pos - 1].kind == T_POW;
                        if (!unpack_mapping && mapping) return syntax(p, "iterable unpacking follows keyword unpacking");
                        arg = node(p, unpack_mapping ? N_MAPPING : N_STAR);
                        if (!arg || !(arg->a = expression(p, 0))) return NULL;
                        if (unpack_mapping) { mapping = keywords = 1; }
                    } else {
                        arg = expression(p, 0);
                        if (arg && take(p, '=')) {
                            if (arg->kind != N_NAME) return syntax(p, "keyword cannot be an expression");
                            arg->kind = N_KEYWORD;
                            for (Node *a = n->args; a; a = a->next)
                                if (a->kind == N_KEYWORD && !strcmp(a->text, arg->text)) return syntax(p, "keyword argument repeated");
                            if (!(arg->a = expression(p, 0))) return NULL;
                            keywords = 1;
                        } else if (keywords) return syntax(p, "positional argument follows keyword argument");
                    }
                    if (!arg) return NULL;
                    if (keyword(p, "for")) {
                        if (arg->kind == N_MAPPING) return syntax(p, "cannot use dict unpacking in generator expression");
                        if (arg->kind == N_KEYWORD) return syntax(p, "invalid syntax. Maybe you meant '==' or ':=' instead of '='?");
                        if (n->args)
                            return syntax(p, "generator expression must be parenthesized");
                        Node *generator = node(p, N_TUPLE);
                        if (!generator) return NULL;
                        generator->args = arg;
                        if (!comprehension(p, generator)) return NULL;
                        arg = generator;
                        *tail = arg;
                        break;
                    }
                    *tail = arg; tail = &arg->next;
                    if (!take(p, ',')) break;
                } while (!at(p, ')'));
                if (!expect(p, ')', "expected ')' after arguments")) return NULL;
            }
            left = n;
        }
    }
    for (;;) {
        int width, prec;
        int op = operator_info(p, &width, &prec);
        if (prec < min) break;
        Node *n = node(p, prec == 3 ? N_COMPARE : N_BINARY);
        if (!n) return NULL;
        n->a = left;
        if (prec == 3) {
            Node **tail = &n->args;
            do {
                Node *cmp = node(p, N_BINARY);
                if (!cmp) return NULL;
                cmp->op = op; p->pos += (size_t)width;
                cmp->a = expression(p, 4);
                if (!cmp->a) return NULL;
                *tail = cmp; tail = &cmp->next;
                op = operator_info(p, &width, &prec);
            } while (prec == 3);
        } else {
            n->op = op; p->pos += (size_t)width;
            n->b = expression(p, op == T_POW ? 10 : prec + 1);
            if (!n->b) return NULL;
        }
        left = n;
    }
    if (min == 0 && take_word(p, "if")) {
        Node *n = node(p, N_COND);
        if (!n) return NULL;
        n->a = left; n->b = expression(p, 1);
        if (!n->b || !take_word(p, "else")) return syntax(p, "expected 'else' in conditional expression");
        if (at(p, '*')) return syntax(p, "cannot unpack only part of a conditional expression");
        if (at(p, T_POW)) return syntax(p, "cannot use dict unpacking on only part of a conditional expression");
        n->c = expression(p, 0);
        if (!n->c) return NULL;
        left = n;
    }
    if (min == 0 && take(p, T_WALRUS)) {
        if (left->kind != N_NAME) return syntax(p, "cannot use assignment expressions with this target");
        Node *n = node(p, N_NAMED);
        if (!n) return NULL;
        n->a = left; n->b = expression(p, 0);
        if (!n->b) return NULL;
        if (n->b->kind == N_NAMED && !n->b->op) return syntax(p, "invalid syntax");
        left = n;
    }
    return left;
}
static Node *expression(Parser *p, int min) {
    if (++p->depth > 128) { p->depth--; return syntax(p, "expression is too deeply nested"); }
    Node *n = expression_inner(p, min);
    p->depth--;
    return n;
}
/* Commas belong to the enclosing grammar, not the precedence parser. */
static Node *expression_list(Parser *p, int min) {
    Node *first;
    if (take(p, '*')) {
        first = node(p, N_STAR);
        if (!first || !(first->a = expression(p, 4))) return NULL;
    } else first = expression(p, min);
    if (!first || !take(p, ',')) return first;
    Node *tuple = node(p, N_TUPLE);
    if (!tuple) return NULL;
    tuple->args = first;
    Node **tail = &first->next;
    while (!at(p, T_NL) && !at(p, T_END) && !at(p, ';') && !at(p, '=') &&
           !at(p, ':') && !at(p, ')') && !at(p, ']') && !keyword(p, "in")) {
        Node *item;
        if (take(p, '*')) {
            item = node(p, N_STAR);
            if (!item || !(item->a = expression(p, 4))) return NULL;
        } else item = expression(p, min);
        if (!item) return NULL;
        *tail = item; tail = &item->next;
        if (!take(p, ',')) break;
    }
    return tuple;
}
static int target(Parser *p, Node *n) {
    if (n->kind == N_NAME || n->kind == N_INDEX || n->kind == N_ATTR) return 1;
    if (n->kind == N_STAR) { syntax(p, "starred assignment target must be in a list or tuple"); return 0; }
    if (n->kind == N_COMPREHENSION && n->op == N_TUPLE) { syntax(p, "cannot assign to generator expression"); return 0; }
    if (n->kind != N_TUPLE && n->kind != N_LIST) return 0;
    size_t stars = 0, before = 0;
    for (Node *item = n->args; item; item = item->next) {
        if (item->kind == N_STAR) {
            if (++stars > 1) { syntax(p, "multiple starred expressions in assignment"); return 0; }
            if (before > 255) { syntax(p, "too many expressions in star-unpacking assignment"); return 0; }
            if (!target(p, item->a)) return 0;
        } else if (!target(p, item)) return 0;
        if (!stars) before++;
    }
    return 1;
}
static Node *comprehension(Parser *p, Node *n) {
    if (n->args->next) return syntax(p, "invalid comprehension element");
    n->op = n->kind; n->kind = N_COMPREHENSION;
    Node **tail = &n->a;
    size_t clauses = 0;
    while (take_word(p, "for")) {
        if (++clauses > 128) return syntax(p, "too many comprehension clauses");
        Node *loop = node(p, N_FOR);
        if (!loop || !(loop->args = expression_list(p, 4))) return NULL;
        if (!target(p, loop->args)) return syntax(p, "invalid comprehension target");
        if (!take_word(p, "in") || !(loop->a = expression(p, 1))) return syntax(p, "expected iterable");
        *tail = loop; tail = &loop->b;
        while (take_word(p, "if")) {
            if (++clauses > 128) return syntax(p, "too many comprehension clauses");
            Node *test = node(p, N_IF);
            if (!test || !(test->a = expression(p, 1))) return NULL;
            *tail = test; tail = &test->b;
        }
    }
    return n;
}
static Node *if_statement(Parser *p) {
    Node *n = node(p, N_IF);
    if (!n) return NULL;
    n->a = expression(p, 0);
    if (!n->a || !(n->b = suite(p))) return NULL;
    if (take_word(p, "elif")) {
        if (++p->depth > 128) { p->depth--; return syntax(p, "too many elif clauses"); }
        n->c = if_statement(p); p->depth--;
        if (!n->c) return NULL;
    }
    else if (take_word(p, "else")) { n->c = suite(p); if (!n->c) return NULL; }
    return n;
}
static Node *statement(Parser *p) {
    Node *n;
    if (take_word(p, "with")) {
        n = node(p, N_WITH);
        if (!n) return NULL;
        Node **tail = &n->args;
        do {
            Node *item = node(p, N_ASSIGN);
            if (!item || !(item->a = expression(p, 0))) return NULL;
            if (take_word(p, "as")) {
                item->b = expression(p, 4);
                if (!item->b || !target(p, item->b)) return syntax(p, "invalid with target");
            }
            *tail = item; tail = &item->next;
        } while (take(p, ','));
        n->b = suite(p);
        return n->b ? n : NULL;
    }
    if (take_word(p, "del")) {
        n = node(p, N_DELETE);
        if (!n || !(n->a = expression_list(p, 0))) return NULL;
        if (!target(p, n->a)) return syntax(p, "invalid deletion target");
        /* Starred targets are only meaningful when consuming an iterable. */
        Node *stack[256]; size_t count = 0;
        stack[count++] = n->a;
        while (count) {
            Node *item = stack[--count];
            if (item->kind == N_STAR) return syntax(p, "cannot delete starred");
            if (item->kind == N_LIST || item->kind == N_TUPLE)
                for (Node *child = item->args; child; child = child->next) {
                    if (count == 256) return syntax(p, "deletion target is too deeply nested");
                    stack[count++] = child;
                }
        }
        return n;
    }
    if (take_word(p, "class")) {
        n = node(p, N_CLASS);
        if (!n || !(n->a = identifier(p))) return NULL;
        if (take(p, '(')) {
            Node **tail = &n->args;
            if (!at(p, ')')) do {
                Node *base = expression(p, 0);
                if (!base) return NULL;
                *tail = base; tail = &base->next;
                if (!take(p, ',')) break;
            } while (!at(p, ')'));
            if (!expect(p, ')', "expected ')' after bases")) return NULL;
        }
        int loops = p->loops, functions = p->functions;
        p->loops = p->functions = 0;
        n->b = suite(p);
        p->loops = loops; p->functions = functions;
        return n->b ? n : NULL;
    }
    if (take_word(p, "raise")) {
        n = node(p, N_RAISE);
        if (!n) return NULL;
        if (!at(p, T_NL) && !at(p, ';')) {
            if (!(n->a = expression(p, 0))) return NULL;
            if (take_word(p, "from") && !(n->b = expression(p, 0))) return NULL;
        }
        return n;
    }
    if (take_word(p, "try")) {
        n = node(p, N_TRY);
        if (!n || !(n->a = suite(p))) return NULL;
        Node **tail = &n->args;
        int bare = 0;
        while (take_word(p, "except")) {
            if (bare) return syntax(p, "default except must be last");
            Node *handler = node(p, N_EXCEPT);
            if (!handler) return NULL;
            if (!at(p, ':')) {
                if (!(handler->a = expression(p, 0))) return NULL;
                if (take_word(p, "as") && !(handler->c = identifier(p))) return NULL;
            } else bare = 1;
            if (!(handler->b = suite(p))) return NULL;
            *tail = handler; tail = &handler->next;
        }
        if (take_word(p, "else")) {
            if (!n->args) return syntax(p, "expected except before else");
            if (!(n->b = suite(p))) return NULL;
        }
        if (take_word(p, "finally") && !(n->c = suite(p))) return NULL;
        return n->args || n->c ? n : syntax(p, "expected except or finally");
    }
    if (take_word(p, "if")) return if_statement(p);
    if (keyword(p, "while") || keyword(p, "for")) {
        int is_for = take_word(p, "for");
        if (!is_for) p->pos++;
        n = node(p, is_for ? N_FOR : N_WHILE);
        if (!n) return NULL;
        if (is_for) {
            n->args = expression_list(p, 4);
            if (n->args && !target(p, n->args)) return syntax(p, "invalid loop target");
            if (!n->args || !take_word(p, "in")) return syntax(p, "expected 'in'");
        }
        n->a = is_for ? expression_list(p, 0) : expression(p, 0);
        if (!n->a) return NULL;
        p->loops++; n->b = suite(p); p->loops--;
        if (!n->b) return NULL;
        if (take_word(p, "else")) { n->c = suite(p); if (!n->c) return NULL; }
        return n;
    }
    if (take_word(p, "def")) {
        n = node(p, N_DEF);
        if (!n || !(n->a = identifier(p)) || !expect(p, '(', "expected '('")) return NULL;
        if (parameters(p, n, ')')) return NULL;
        int loops = p->loops; p->loops = 0; p->functions++;
        n->b = suite(p);
        p->functions--; p->loops = loops;
        return n->b ? n : NULL;
    }
    if (take_word(p, "return")) {
        if (!p->functions) return syntax(p, "'return' outside function");
        n = node(p, N_RETURN);
        if (!n) return NULL;
        if (!at(p, T_NL) && !at(p, ';')) { n->a = expression_list(p, 0); if (!n->a || n->a->kind == N_STAR) return syntax(p, "invalid return expression"); }
        if (keyword(p, "for")) return syntax(p, "invalid syntax");
        return n;
    }
    if (keyword(p, "break") || keyword(p, "continue")) {
        if (!p->loops) return syntax(p, "loop control outside loop");
        n = node(p, keyword(p, "break") ? N_BREAK : N_CONTINUE);
        p->pos++; return n;
    }
    if (take_word(p, "pass")) return node(p, N_PASS);
    if (take_word(p, "assert")) {
        n = node(p, N_ASSERT);
        if (!n || !(n->a = expression(p, 0))) return NULL;
        if (take(p, ',')) { n->b = expression(p, 0); if (!n->b) return NULL; }
        return n;
    }
    if (keyword(p, "import") || keyword(p, "from")) {
        int from = take_word(p, "from");
        if (!from) p->pos++;
        n = node(p, from ? N_FROM : N_IMPORT);
        if (!n || !(n->a = identifier(p))) return NULL;
        if (from) {
            if (!take_word(p, "import") || !(n->b = identifier(p))) return syntax(p, "expected imported name");
        }
        if (take_word(p, "as")) { n->c = identifier(p); if (!n->c) return NULL; }
        return n;
    }
    n = node(p, N_EXPR);
    if (!n || !(n->a = expression_list(p, 0))) return NULL;
    int op = peek(p)->kind;
    if (op == '=' || (op >= T_ADDEQ && op <= T_MODEQ)) {
        if (op != '=' && n->a->kind == N_COMPREHENSION && n->a->op == N_TUPLE)
            return syntax(p, "'generator expression' is an illegal expression for augmented assignment");
        if (!target(p, n->a)) return syntax(p, "invalid assignment target");
        if (op != '=' && n->a->kind != N_NAME && n->a->kind != N_INDEX && n->a->kind != N_ATTR)
            return syntax(p, "invalid augmented assignment target");
        p->pos++; n->kind = N_ASSIGN; n->op = op;
        n->b = expression_list(p, 0);
        if (!n->b) return NULL;
        Node **tail = &n->args;
        while (op == '=' && take(p, '=')) {
            if (!target(p, n->b)) return syntax(p, "invalid assignment target");
            *tail = n->b; tail = &n->b->next;
            n->b = expression_list(p, 0);
            if (!n->b) return NULL;
        }
        if (n->b->kind == N_STAR) return syntax(p, "can't use starred expression here");
    }
    if (n->a->kind == N_STAR) return syntax(p, "can't use starred expression here");
    if (n->kind == N_EXPR && n->a->kind == N_NAMED && !n->a->op) return syntax(p, "invalid syntax");
    return n;
}
static Node *line_statements(Parser *p) {
    Node *head = NULL, **tail = &head;
    do {
        Node *n = statement(p);
        if (!n) return NULL;
        *tail = n; tail = &n->next;
        if (n->kind == N_IF || n->kind == N_WHILE || n->kind == N_FOR || n->kind == N_DEF ||
            n->kind == N_CLASS || n->kind == N_TRY || n->kind == N_WITH) return head;
        if (!take(p, ';')) break;
    } while (!at(p, T_NL));
    return expect(p, T_NL, "expected end of statement") ? head : NULL;
}
static Node *suite(Parser *p) {
    if (!expect(p, ':', "expected ':'")) return NULL;
    if (!take(p, T_NL)) return line_statements(p);
    while (take(p, T_NL)) {}
    if (!expect(p, T_INDENT, "expected an indented block")) return NULL;
    if (++p->depth > 128) { p->depth--; return syntax(p, "too many nested blocks"); }
    Node *body = statements(p);
    p->depth--;
    if (!body || !expect(p, T_DEDENT, "expected end of block")) return NULL;
    return body;
}
static Node *statements(Parser *p) {
    Node *head = NULL, **tail = &head;
    while (!at(p, T_END) && !at(p, T_DEDENT)) {
        if (take(p, T_NL)) continue;
        Node *n = line_statements(p);
        if (!n) return NULL;
        *tail = n;
        while (*tail) tail = &(*tail)->next;
    }
    return head;
}
static SPYValue *number_literal(SPYContext *, Node *);
static int target_contains(Node *n, const char *name) {
    if (n->kind == N_NAME) return !strcmp(n->text, name);
    if (n->kind == N_STAR) return target_contains(n->a, name);
    if (n->kind == N_LIST || n->kind == N_TUPLE)
        for (Node *item = n->args; item; item = item->next)
            if (target_contains(item, name)) return 1;
    return 0;
}
static int validate_named(SPYContext *c, Node *n, Node **comps, size_t count, int iterable, int class_scope, size_t depth) {
    if (depth > 256) { spy_error(c, "SyntaxError", "syntax tree is too deeply nested"); return -1; }
    for (; n; n = n->next) {
        if (n->kind == N_NAMED) {
            c->line = n->line;
            if (iterable) spy_error(c, "SyntaxError", "assignment expression cannot be used in a comprehension iterable expression");
            else if (count && class_scope) spy_error(c, "SyntaxError", "assignment expression within a comprehension cannot be used in a class body");
            for (size_t i = 0; i < count && !c->error_type[0]; i++)
                for (Node *clause = comps[i]->a; clause; clause = clause->b)
                    if (clause->kind == N_FOR && target_contains(clause->args, n->a->text))
                        errorf(c, "SyntaxError", "assignment expression cannot rebind comprehension iteration variable '%s'", n->a->text);
            if (c->error_type[0]) return -1;
        }
        if (n->kind == N_COMPREHENSION) {
            if (count == 128) { spy_error(c, "SyntaxError", "too many nested comprehensions"); return -1; }
            comps[count] = n;
            if (validate_named(c, n->args, comps, count + 1, iterable, class_scope, depth + 1)) return -1;
            for (Node *clause = n->a; clause; clause = clause->b)
                if (validate_named(c, clause->a, comps, count + 1, iterable || clause->kind == N_FOR, class_scope, depth + 1)) return -1;
            continue;
        }
        if (n->kind == N_DEF || n->kind == N_LAMBDA || n->kind == N_CLASS) {
            if (validate_named(c, n->args, comps, count, iterable, class_scope, depth + 1)) return -1;
            Node *nested[128];
            if (validate_named(c, n->b, nested, 0, iterable, n->kind == N_CLASS, depth + 1)) return -1;
            continue;
        }
        if (validate_named(c, n->a, comps, count, iterable, class_scope, depth + 1) ||
            validate_named(c, n->b, comps, count, iterable, class_scope, depth + 1) ||
            validate_named(c, n->c, comps, count, iterable, class_scope, depth + 1) ||
            validate_named(c, n->args, comps, count, iterable, class_scope, depth + 1)) return -1;
    }
    return 0;
}
static SPYValue *parse(SPYContext *c, const char *source, const char *filename) {
    SPYValue *unit = value_new(c, V_UNIT);
    if (!unit) return NULL;
    unit->as.unit.filename = copy_text(c, filename, strlen(filename));
    Parser p = { .ctx = c, .unit = unit };
    if (unit->as.unit.filename && !lex(&p, source)) {
        unit->as.unit.body = statements(&p);
        if (!c->error_type[0] && !at(&p, T_END)) syntax(&p, "unexpected indentation");
        Node *comps[128];
        if (!c->error_type[0]) validate_named(c, unit->as.unit.body, comps, 0, 0, 0, 0);
        for (Node *n = unit->as.unit.nodes; n && !c->error_type[0]; n = n->allocated) {
            if (n->kind == N_INT || n->kind == N_FLOAT) {
                c->line = n->line;
                SPYValue *literal = number_literal(c, n);
                spy_release(literal);
            }
        }
    }
    free(p.tokens);
    if (c->error_type[0]) { snprintf(c->filename, sizeof(c->filename), "%s", filename); spy_release(unit); return NULL; }
    return unit;
}

static size_t utf8_width(unsigned char ch) {
    return ch < 128 ? 1 : ch < 224 ? 2 : ch < 240 ? 3 : 4;
}
static size_t string_length(SPYValue *v) {
    size_t n = 0;
    for (size_t i = 0; i < v->as.string.len; i++)
        if (((unsigned char)v->as.string.data[i] & 192) != 128) n++;
    return n;
}
static uint64_t range_length(SPYValue *v) {
    int64_t start = v->as.range.start, stop = v->as.range.stop, step = v->as.range.step;
    if (step > 0) {
        if (start >= stop) return 0;
        return ((uint64_t)stop - (uint64_t)start - 1) / (uint64_t)step + 1;
    }
    if (start <= stop) return 0;
    return ((uint64_t)start - (uint64_t)stop - 1) / (0 - (uint64_t)step) + 1;
}
static SPYValue *special_method(SPYContext *, SPYValue *, const char *);
static SPYValue *call_special(SPYContext *, SPYValue *, const char *, size_t, SPYValue *const *);
static int error_is(SPYContext *, const char *);
static SPYValue *generator_next(SPYContext *, SPYValue *);
enum { I_SEQUENCE, I_ZIP, I_ENUMERATE, I_REVERSED, I_GETITEM, I_CUSTOM };
static int iterable_type(SPYValue *v) {
    return v->type == SPY_LIST || v->type == SPY_TUPLE || v->type == SPY_DICT || v->type == SPY_SET ||
           v->type == SPY_STRING || v->type == SPY_RANGE || v->type == SPY_ITERATOR || v->type == SPY_INSTANCE || v->type == SPY_GENERATOR;
}
static SPYValue *get_iterator(SPYContext *c, SPYValue *source) {
    if (source->type == SPY_ITERATOR || source->type == SPY_GENERATOR) return spy_retain(source);
    if (source->type == SPY_INSTANCE) {
        SPYValue *method = special_method(c, source, "__iter__");
        if (method) {
            SPYValue *iterator = spy_call(c, method, 0, NULL);
            spy_release(method);
            if (!iterator) return NULL;
            if (iterator->type == SPY_ITERATOR || iterator->type == SPY_GENERATOR) return iterator;
            method = special_method(c, iterator, "__next__");
            if (!method) { spy_release(iterator); return spy_error(c, "TypeError", "iter() returned a non-iterator"); }
            spy_release(method);
            return iterator;
        }
        if (c->error_type[0]) return NULL;
        method = special_method(c, source, "__getitem__");
        if (!method) return spy_error(c, "TypeError", "object is not iterable");
        spy_release(method);
    }
    if (!iterable_type(source)) return errorf(c, "TypeError", "'%s' object is not iterable", type_name(source));
    SPYValue *v = value_new(c, SPY_ITERATOR);
    if (v) {
        v->as.iterator.source = spy_retain(source);
        if (source->type == SPY_INSTANCE) v->as.iterator.kind = I_GETITEM;
        if (source->type == SPY_DICT || source->type == SPY_SET) v->as.iterator.size = source->as.map.len;
    }
    return v;
}
static SPYValue *iterator_next(SPYContext *, SPYValue *);
static SPYValue *iter_at(SPYContext *c, SPYValue *v, size_t index) {
    switch (v->type) {
    case SPY_ITERATOR: case SPY_INSTANCE: case SPY_GENERATOR: return iterator_next(c, v);
    case SPY_LIST: case SPY_TUPLE:
        return index < v->as.seq.len ? spy_retain(v->as.seq.items[index]) : NULL;
    case SPY_DICT: case SPY_SET:
        return index < v->as.map.len ? spy_retain(v->as.map.items[index].key) : NULL;
    case SPY_STRING:
        for (size_t i = 0; i < v->as.string.len;) {
            size_t width = utf8_width((unsigned char)v->as.string.data[i]);
            if (width > v->as.string.len - i) width = 1;
            if (!index--) return spy_string(c, v->as.string.data + i, width);
            i += width;
        }
        return NULL;
    case SPY_RANGE: {
        if (index >= range_length(v)) return NULL;
        uint64_t bits = (uint64_t)v->as.range.start + (uint64_t)index * (uint64_t)v->as.range.step;
        /* Avoid implementation-defined unsigned-to-signed conversion. */
        int64_t n = bits <= INT64_MAX ? (int64_t)bits : -1 - (int64_t)(UINT64_MAX - bits);
        return spy_int(c, n);
    }
    default: return spy_error(c, "TypeError", "object is not iterable");
    }
}
static SPYValue *iterator_next(SPYContext *c, SPYValue *v) {
    if (v->type == SPY_GENERATOR) return generator_next(c, v);
    if (v->type == SPY_INSTANCE) {
        SPYValue *result = call_special(c, v, "__next__", 0, NULL);
        if (!result && error_is(c, "StopIteration")) spy_clear_error(c);
        return result;
    }
    if (v->as.iterator.done) return NULL;
    if (++c->depth > 256) { c->depth--; return spy_error(c, "RecursionError", "iterator nesting limit exceeded"); }
    SPYValue *source = v->as.iterator.source, *result = NULL;
    switch (v->as.iterator.kind) {
    case I_SEQUENCE:
        if ((source->type == SPY_DICT || source->type == SPY_SET) && v->as.iterator.size != source->as.map.len) {
            spy_error(c, "RuntimeError", source->type == SPY_DICT ? "dictionary changed size during iteration" : "Set changed size during iteration");
            v->as.iterator.done = 1;
        } else result = iter_at(c, source, v->as.iterator.index++);
        break;
    case I_ZIP:
        if (!source->as.seq.len) break;
        result = value_new(c, SPY_TUPLE);
        if (!result) break;
        for (size_t i = 0; i < source->as.seq.len; i++) {
            SPYValue *item = iterator_next(c, source->as.seq.items[i]);
            if (!item || sequence_append(c, result, item)) {
                spy_release(item); spy_release(result); result = NULL; break;
            }
            spy_release(item);
        }
        break;
    case I_ENUMERATE: {
        SPYValue *item = iterator_next(c, source);
        if (!item) break;
        SPYValue *index = spy_int(c, v->as.iterator.count);
        result = value_new(c, SPY_TUPLE);
        if (!index || !result || sequence_append(c, result, index) || sequence_append(c, result, item)) {
            spy_release(result); result = NULL;
        }
        spy_release(index); spy_release(item);
        if (v->as.iterator.count == INT64_MAX) {
            spy_release(result); result = spy_error(c, "OverflowError", "enumerate index exceeds signed 64-bit limit");
        } else v->as.iterator.count++;
        break;
    }
    case I_REVERSED:
        if (v->as.iterator.index) result = iter_at(c, source, --v->as.iterator.index);
        break;
    case I_GETITEM: {
        if (v->as.iterator.index > INT64_MAX) { spy_error(c, "OverflowError", "sequence index exceeds signed 64-bit limit"); break; }
        SPYValue *index = spy_int(c, (int64_t)v->as.iterator.index++);
        if (index) result = call_special(c, source, "__getitem__", 1, &index);
        spy_release(index);
        if (!result && (error_is(c, "IndexError") || error_is(c, "StopIteration"))) spy_clear_error(c);
        break;
    }
    case I_CUSTOM:
        result = call_special(c, source, "__next__", 0, NULL);
        if (!result && error_is(c, "StopIteration")) spy_clear_error(c);
        break;
    }
    if (!result && !c->error_type[0]) v->as.iterator.done = 1;
    c->depth--;
    return result;
}
static SPYValue *get_index(SPYContext *c, SPYValue *v, SPYValue *key) {
    if (v->type == SPY_INSTANCE) {
        SPYValue *method = special_method(c, v, "__getitem__");
        if (!method) return errorf(c, "TypeError", "'%s' object is not subscriptable", type_name(v));
        SPYValue *result = spy_call(c, method, 1, &key);
        spy_release(method); return result;
    }
    if (v->type == SPY_DICT) {
        if (!hashable(key, 0)) return spy_error(c, "TypeError", "unhashable key");
        ptrdiff_t i = map_find(v, key);
        if (i < 0) return spy_error(c, "KeyError", "key not found");
        return spy_retain(v->as.map.items[i].value);
    }
    int64_t index;
    if (spy_as_int(c, key, &index)) return NULL;
    size_t len;
    if (v->type == SPY_LIST || v->type == SPY_TUPLE) len = v->as.seq.len;
    else if (v->type == SPY_STRING) len = string_length(v);
    else return spy_error(c, "TypeError", "object is not subscriptable");
    if (index < 0 && len <= INT64_MAX) index += (int64_t)len;
    if (index < 0 || (uint64_t)index >= len) return spy_error(c, "IndexError", "index out of range");
    return iter_at(c, v, (size_t)index);
}
static int set_index(SPYContext *c, SPYValue *v, SPYValue *key, SPYValue *item) {
    if (v->type == SPY_INSTANCE) {
        SPYValue *args[] = {key, item};
        SPYValue *result = call_special(c, v, "__setitem__", 2, args);
        int status = result ? 0 : -1;
        spy_release(result); return status;
    }
    if (v->type == SPY_DICT) return map_set(c, v, key, item);
    if (v->type != SPY_LIST) { spy_error(c, "TypeError", "object does not support item assignment"); return -1; }
    int64_t index;
    if (spy_as_int(c, key, &index)) return -1;
    if (index < 0 && v->as.seq.len <= INT64_MAX) index += (int64_t)v->as.seq.len;
    if (index < 0 || (uint64_t)index >= v->as.seq.len) { spy_error(c, "IndexError", "index out of range"); return -1; }
    SPYValue *old = v->as.seq.items[index];
    v->as.seq.items[index] = spy_retain(item);
    spy_release(old);
    return 0;
}
static int int_add(int64_t a, int64_t b, int64_t *r) {
    if ((b > 0 && a > INT64_MAX - b) || (b < 0 && a < INT64_MIN - b)) return -1;
    *r = a + b; return 0;
}
static int int_mul(int64_t a, int64_t b, int64_t *r) {
    if (a > 0 ? (b > 0 ? a > INT64_MAX / b : b < INT64_MIN / a) :
        (a < 0 && (b > 0 ? a < INT64_MIN / b : b < 0 && a < INT64_MAX / b))) return -1;
    *r = a * b; return 0;
}
static SPYValue *integer_binary(SPYContext *c, int op, int64_t a, int64_t b) {
    int64_t r;
    switch (op) {
    case '+': if (int_add(a, b, &r)) goto overflow; break;
    case '-':
        if ((b < 0 && a > INT64_MAX + b) || (b > 0 && a < INT64_MIN + b)) goto overflow;
        r = a - b; break;
    case '*': if (int_mul(a, b, &r)) goto overflow; break;
    case T_FLOORDIV: case '%':
        if (!b) return spy_error(c, "ZeroDivisionError", op == '%' ? "integer modulo by zero" : "division by zero");
        if (a == INT64_MIN && b == -1) { if (op == '%') return spy_int(c, 0); goto overflow; }
        r = op == '%' ? a % b : a / b;
        if (a % b && ((a < 0) != (b < 0))) r += op == '%' ? b : -1;
        break;
    case '&': r = a & b; break;
    case '|': r = a | b; break;
    case '^': r = a ^ b; break;
    case T_LSHIFT:
        if (b < 0) return spy_error(c, "ValueError", "negative shift count");
        if (b >= 64) { if (!a) return spy_int(c, 0); goto overflow; }
        r = a;
        while (b--) if (int_mul(r, 2, &r)) goto overflow;
        break;
    case T_RSHIFT:
        if (b < 0) return spy_error(c, "ValueError", "negative shift count");
        r = b >= 63 ? (a < 0 ? -1 : 0) : (a >= 0 ? a / ((int64_t)1 << b) : -1 - (-(a + 1)) / ((int64_t)1 << b));
        break;
    case T_POW:
        if (b < 0) {
            if (!a) return spy_error(c, "ZeroDivisionError", "zero cannot be raised to a negative power");
            return spy_float(c, pow((double)a, (double)b));
        }
        r = 1;
        while (b) {
            if ((b & 1) && int_mul(r, a, &r)) goto overflow;
            b /= 2;
            if (b && int_mul(a, a, &a)) goto overflow;
        }
        break;
    default: return spy_error(c, "TypeError", "unsupported integer operator");
    }
    return spy_int(c, r);
overflow:
    return spy_error(c, "OverflowError", "integer exceeds this runtime's signed 64-bit limit");
}
static SPYValue *sequence_binary(SPYContext *c, int op, SPYValue *a, SPYValue *b) {
    if (op == '*' && is_int(a)) { SPYValue *tmp = a; a = b; b = tmp; }
    int sequence = a->type == SPY_LIST || a->type == SPY_TUPLE;
    if (op == '+' && a->type == b->type && (sequence || a->type == SPY_STRING)) {
        if (a->type == SPY_STRING) {
            Buffer out = { .ctx = c };
            SPYValue *v = NULL;
            if (!append(&out, a->as.string.data, a->as.string.len) && !append(&out, b->as.string.data, b->as.string.len))
                v = spy_string(c, out.data, out.len);
            free(out.data); return v;
        }
        SPYValue *v = value_new(c, a->type);
        if (!v) return NULL;
        for (size_t i = 0; i < a->as.seq.len; i++) if (sequence_append(c, v, a->as.seq.items[i])) goto seq_fail;
        for (size_t i = 0; i < b->as.seq.len; i++) if (sequence_append(c, v, b->as.seq.items[i])) goto seq_fail;
        return v;
seq_fail:
        spy_release(v); return NULL;
    }
    if (op == '*' && is_int(b) && (sequence || a->type == SPY_STRING)) {
        uint64_t count = b->as.integer < 0 ? 0 : (uint64_t)b->as.integer;
        size_t len = sequence ? a->as.seq.len : a->as.string.len;
        if (!len) count = 0;
        if (count && (count > SIZE_MAX / len || count * len > (size_t)INT_MAX))
            return spy_error(c, "MemoryError", "repeated sequence too large");
        SPYValue *v = value_new(c, a->type);
        if (!v) return NULL;
        if (sequence) {
            for (uint64_t i = 0; i < count; i++) for (size_t j = 0; j < len; j++)
                if (sequence_append(c, v, a->as.seq.items[j])) { spy_release(v); return NULL; }
        } else {
            v->as.string.len = (size_t)count * len;
            v->as.string.data = allocate(c, v->as.string.len + 1);
            if (!v->as.string.data) { spy_release(v); return NULL; }
            for (uint64_t i = 0; i < count; i++) memcpy(v->as.string.data + i * len, a->as.string.data, len);
        }
        return v;
    }
    return spy_error(c, "TypeError", "unsupported operands");
}
static SPYValue *binary(SPYContext *c, int op, SPYValue *a, SPYValue *b) {
    if (a->type == SPY_BOOL && b->type == SPY_BOOL && (op == '&' || op == '|' || op == '^')) {
        int x = (int)a->as.integer, y = (int)b->as.integer;
        return spy_bool(c, op == '&' ? x & y : op == '|' ? x | y : x ^ y);
    }
    if (is_int(a) && is_int(b) && op != '/') return integer_binary(c, op, a->as.integer, b->as.integer);
    if (is_number(a) && is_number(b)) {
        double x, y, r;
        if (spy_as_float(c, a, &x) || spy_as_float(c, b, &y)) return NULL;
        if ((op == '/' || op == T_FLOORDIV || op == '%') && y == 0)
            return spy_error(c, "ZeroDivisionError", "division by zero");
        switch (op) {
        case '+': r = x + y; break;
        case '-': r = x - y; break;
        case '*': r = x * y; break;
        case '/': r = x / y; break;
        case T_FLOORDIV: case '%': {
            double mod = fmod(x, y), div = (x - mod) / y;
            if (mod && ((mod < 0) != (y < 0))) { mod += y; div--; }
            if (op == '%') r = mod ? mod : copysign(0, y);
            else if (div) { r = floor(div); if (div - r > 0.5) r++; }
            else r = copysign(0, x / y);
            break;
        }
        case T_POW:
            if (!x && y < 0) return spy_error(c, "ZeroDivisionError", "zero cannot be raised to a negative power");
            if (x < 0 && floor(y) != y) return spy_error(c, "NotImplementedError", "complex numbers are not implemented");
            r = pow(x, y); break;
        default: return spy_error(c, "TypeError", "unsupported floating-point operator");
        }
        return spy_float(c, r);
    }
    return sequence_binary(c, op, a, b);
}
static SPYValue *comparison(SPYContext *c, int op, SPYValue *a, SPYValue *b) {
    int result;
    if (op == T_EQ || op == T_NE) {
        result = equal(a, b, 0);
        if (c->error_type[0]) return NULL;
        return spy_bool(c, op == T_EQ ? result : !result);
    }
    if (op == O_IS || op == O_ISNOT) {
        result = a == b || (a->type == SPY_NONE && b->type == SPY_NONE) ||
            (a->type == SPY_BOOL && b->type == SPY_BOOL && a->as.integer == b->as.integer);
        return spy_bool(c, op == O_IS ? result : !result);
    }
    if (op == O_IN || op == O_NOTIN) {
        result = 0;
        if (b->type == SPY_DICT || b->type == SPY_SET) {
            if (!hashable(a, 0)) return spy_error(c, "TypeError", "unhashable key");
            result = map_find(b, a) >= 0;
        } else if (b->type == SPY_STRING) {
            if (a->type != SPY_STRING) return spy_error(c, "TypeError", "string membership requires a string");
            if (a->as.string.len <= b->as.string.len)
                for (size_t i = 0; i <= b->as.string.len - a->as.string.len; i++)
                    if (!memcmp(b->as.string.data + i, a->as.string.data, a->as.string.len)) { result = 1; break; }
        } else {
            SPYValue *iterator = get_iterator(c, b);
            if (!iterator) return NULL;
            for (;;) {
                SPYValue *item = iterator_next(c, iterator);
                if (!item) break;
                result = equal(a, item, 0); spy_release(item);
                if (result || c->error_type[0]) break;
                if (c->step_limit && ++c->steps > c->step_limit) { spy_error(c, "RuntimeError", "execution step limit exceeded"); break; }
            }
            spy_release(iterator);
        }
        if (c->error_type[0]) return NULL;
        return spy_bool(c, op == O_IN ? result : !result);
    }
    int order;
    if ((a->type == SPY_LIST || a->type == SPY_TUPLE) && a->type == b->type) {
        if (++c->depth > 256) { c->depth--; return spy_error(c, "RecursionError", "comparison nesting limit exceeded"); }
        size_t len = a->as.seq.len < b->as.seq.len ? a->as.seq.len : b->as.seq.len;
        for (size_t i = 0; i < len; i++) {
            SPYValue *x = a->as.seq.items[i], *y = b->as.seq.items[i];
            if (x == y || equal(x, y, 0)) continue;
            SPYValue *value = c->error_type[0] ? NULL : comparison(c, op, x, y);
            c->depth--; return value;
        }
        c->depth--;
        order = a->as.seq.len < b->as.seq.len ? -1 : a->as.seq.len > b->as.seq.len;
        return spy_bool(c, op == '<' ? order < 0 : op == '>' ? order > 0 : op == T_LE ? order <= 0 : order >= 0);
    }
    if (is_number(a) && is_number(b)) {
        order = numeric_order(a, b);
        if (order == 2) return spy_bool(c, 0);
    } else if (a->type == SPY_STRING && b->type == SPY_STRING) {
        size_t n = a->as.string.len < b->as.string.len ? a->as.string.len : b->as.string.len;
        order = memcmp(a->as.string.data, b->as.string.data, n);
        if (!order) order = a->as.string.len < b->as.string.len ? -1 : a->as.string.len > b->as.string.len;
    } else return spy_error(c, "TypeError", "objects do not support ordering");
    return spy_bool(c, op == '<' ? order < 0 : op == '>' ? order > 0 : op == T_LE ? order <= 0 : order >= 0);
}

enum { M_APPEND, M_POP, M_GET, M_KEYS, M_VALUES, M_ITEMS };
static SPYValue *class_lookup(SPYValue *cls, const char *name) {
    for (; cls; cls = cls->as.map.parent) {
        SPYValue *value = name_local(cls, name);
        if (value) return value;
    }
    return NULL;
}
static int subclass(SPYValue *cls, SPYValue *base) {
    for (; cls && cls->type == SPY_CLASS; cls = cls->as.map.parent)
        if (cls == base) return 1;
    return 0;
}
static SPYValue *bind_method(SPYContext *c, SPYValue *self, SPYValue *function) {
    if (function->type != SPY_FUNCTION) return spy_retain(function);
    SPYValue *method = value_new(c, SPY_METHOD);
    if (method) { method->as.method.self = spy_retain(self); method->as.method.function = spy_retain(function); }
    return method;
}
static SPYValue *special_method(SPYContext *c, SPYValue *v, const char *name) {
    if (v->type != SPY_INSTANCE) return NULL;
    SPYValue *function = class_lookup(v->as.map.parent, name);
    return function ? bind_method(c, v, function) : NULL;
}
static SPYValue *call_special(SPYContext *c, SPYValue *v, const char *name, size_t argc, SPYValue *const *argv) {
    SPYValue *method = special_method(c, v, name);
    if (!method) return errorf(c, "TypeError", "object does not support %s", name);
    SPYValue *result = spy_call(c, method, argc, argv);
    spy_release(method); return result;
}
static int error_is(SPYContext *c, const char *name) {
    if (!strcmp(c->error_type, name)) return 1;
    SPYValue *base = name_local(c->builtins, name);
    return c->exception && base && subclass(c->exception->as.map.parent, base);
}
static SPYValue *attribute(SPYContext *c, SPYValue *v, const char *name) {
    if (!strcmp(name, "__class__")) return spy_retain(v->type == SPY_INSTANCE ? v->as.map.parent : c->types[v->type]);
    if (v->type == SPY_GENERATOR && !strcmp(name, "gi_running")) return spy_bool(c, v->as.generator.running);
    if (v->type == SPY_CLASS || v->type == SPY_INSTANCE) {
        if (!strcmp(name, "__class__") && v->type == SPY_INSTANCE) return spy_retain(v->as.map.parent);
        SPYValue *value = name_local(v, name);
        if (value) return spy_retain(value);
        value = class_lookup(v->as.map.parent, name);
        if (value) return v->type == SPY_INSTANCE ? bind_method(c, v, value) : spy_retain(value);
        return errorf(c, "AttributeError", "object has no attribute '%s'", name);
    }
    if (v->type == SPY_MODULE) {
        SPYValue *item = name_local(v, name);
        return item ? spy_retain(item) : errorf(c, "AttributeError", "module has no attribute '%s'", name);
    }
    int method = -1;
    if (v->type == SPY_LIST) {
        if (!strcmp(name, "append")) method = M_APPEND;
        if (!strcmp(name, "pop")) method = M_POP;
    }
    if (v->type == SPY_DICT) {
        if (!strcmp(name, "get")) method = M_GET;
        if (!strcmp(name, "keys")) method = M_KEYS;
        if (!strcmp(name, "values")) method = M_VALUES;
        if (!strcmp(name, "items")) method = M_ITEMS;
    }
    if (method < 0) return errorf(c, "AttributeError", "object has no attribute '%s'", name);
    SPYValue *bound = value_new(c, SPY_BOUND_METHOD);
    if (bound) { bound->as.bound.self = spy_retain(v); bound->as.bound.method = method; }
    return bound;
}
static SPYValue *bound_call(SPYContext *c, SPYValue *bound, size_t argc, SPYValue *const *argv) {
    SPYValue *self = bound->as.bound.self;
    switch (bound->as.bound.method) {
    case M_APPEND:
        if (argc != 1) break;
        return sequence_append(c, self, argv[0]) ? NULL : spy_none(c);
    case M_POP: {
        if (argc > 1) break;
        int64_t i = -1;
        if (argc && spy_as_int(c, argv[0], &i)) return NULL;
        if (i < 0) i += (int64_t)self->as.seq.len;
        if (i < 0 || (uint64_t)i >= self->as.seq.len) return spy_error(c, "IndexError", "pop index out of range");
        SPYValue *v = self->as.seq.items[i];
        self->as.seq.len--;
        memmove(&self->as.seq.items[i], &self->as.seq.items[i + 1], (self->as.seq.len - (size_t)i) * sizeof(SPYValue *));
        return v;
    }
    case M_GET: {
        if (argc < 1 || argc > 2) break;
        if (!hashable(argv[0], 0)) return spy_error(c, "TypeError", "unhashable key");
        ptrdiff_t i = map_find(self, argv[0]);
        return i >= 0 ? spy_retain(self->as.map.items[i].value) : argc == 2 ? spy_retain(argv[1]) : spy_none(c);
    }
    default: {
        if (argc) break;
        SPYValue *list = spy_list(c);
        if (!list) return NULL;
        for (size_t i = 0; i < self->as.map.len; i++) {
            Entry *e = &self->as.map.items[i];
            SPYValue *item;
            if (bound->as.bound.method == M_ITEMS) {
                item = value_new(c, SPY_TUPLE);
                if (item && (sequence_append(c, item, e->key) || sequence_append(c, item, e->value))) { spy_release(item); item = NULL; }
            } else item = spy_retain(bound->as.bound.method == M_KEYS ? e->key : e->value);
            if (!item || sequence_append(c, list, item)) { spy_release(item); spy_release(list); return NULL; }
            spy_release(item);
        }
        return list;
    }
    }
    return spy_error(c, "TypeError", "wrong number of method arguments");
}
static int set_attribute(SPYContext *c, SPYValue *object, const char *name, SPYValue *value) {
    if (object->type != SPY_INSTANCE && object->type != SPY_CLASS && object->type != SPY_MODULE) {
        spy_error(c, "AttributeError", "object attributes are read-only"); return -1;
    }
    if (!strcmp(name, "__class__")) { spy_error(c, "TypeError", "changing an object's class is not implemented"); return -1; }
    if (object->type == SPY_CLASS && (!strcmp(name, "__name__") || !strcmp(name, "__qualname__") || !strcmp(name, "__module__")) && value->type != SPY_STRING) {
        spy_error(c, "TypeError", "class name and module attributes must be strings"); return -1;
    }
    if (object->type == SPY_INSTANCE && !strcmp(name, "args") &&
        subclass(object->as.map.parent, name_local(c->builtins, "BaseException")) && value->type != SPY_TUPLE) {
        SPYValue *iterator = get_iterator(c, value), *args = value_new(c, SPY_TUPLE);
        if (!iterator || !args) { spy_release(iterator); spy_release(args); return -1; }
        while (!c->error_type[0]) {
            if (c->step_limit && ++c->steps > c->step_limit) { spy_error(c, "RuntimeError", "execution step limit exceeded"); break; }
            SPYValue *item = iterator_next(c, iterator);
            if (!item) break;
            int status = sequence_append(c, args, item);
            spy_release(item);
            if (status) break;
        }
        int status = c->error_type[0] ? -1 : name_set(c, object, name, args);
        spy_release(iterator); spy_release(args); return status;
    }
    return name_set(c, object, name, value);
}

typedef struct { SPYValue *env, *unit; } Frame;
enum { FLOW_NORMAL, FLOW_RETURN, FLOW_BREAK, FLOW_CONTINUE, FLOW_ERROR };
typedef struct { int flow; SPYValue *value; } Result;
static SPYValue *eval(SPYContext *, Frame *, Node *);
static Result execute(SPYContext *, Frame *, Node *);
static SPYValue *call_keywords(SPYContext *, SPYValue *, size_t, SPYValue *const *, SPYValue *);
static SPYValue *builtin_keywords(SPYContext *, size_t, SPYValue *const *, int, SPYValue *);
static int store_target(SPYContext *, Frame *, Node *, SPYValue *);
static int declare_target(SPYContext *, SPYValue *, Node *);
static SPYValue *eval_comprehension(SPYContext *, Frame *, Node *);
static int display_add(SPYContext *c, SPYValue *result, SPYValue *item) {
    if (result->type != SPY_SET) return sequence_append(c, result, item);
    SPYValue *none = spy_none(c);
    if (!none) return -1;
    int status = map_set(c, result, item, none);
    spy_release(none); return status;
}
static int merge_keyword(SPYContext *c, SPYValue *result, SPYValue *key, SPYValue *value) {
    if (map_find(result, key) >= 0) {
        if (key->type == SPY_STRING) errorf(c, "TypeError", "multiple values for keyword argument '%s'", key->as.string.data);
        else spy_error(c, "TypeError", "multiple values for keyword argument");
        return -1;
    }
    return map_set(c, result, key, value);
}
static int extend_container(SPYContext *c, SPYValue *result, SPYValue *source, int keywords) {
    if (result->type == SPY_DICT) {
        if (source->type == SPY_INSTANCE) {
            SPYValue *method = attribute(c, source, "keys");
            if (!method) {
                if (error_is(c, "AttributeError")) {
                    spy_clear_error(c); errorf(c, "TypeError", "'%s' object is not a mapping", type_name(source));
                }
                return -1;
            }
            SPYValue *keys = spy_call(c, method, 0, NULL);
            spy_release(method);
            if (!keys) return -1;
            SPYValue *iterator = get_iterator(c, keys);
            if (!iterator && error_is(c, "TypeError") && !iterable_type(keys)) {
                SPYValue *module = name_local(source->as.map.parent, "__module__");
                spy_clear_error(c);
                errorf(c, "TypeError", "%s.%s.keys() must return an iterable, not %s", module->as.string.data, type_name(source), type_name(keys));
            }
            spy_release(keys);
            if (!iterator) return -1;
            while (!c->error_type[0]) {
                if (c->step_limit && ++c->steps > c->step_limit) { spy_error(c, "RuntimeError", "execution step limit exceeded"); break; }
                SPYValue *key = iterator_next(c, iterator);
                if (!key) break;
                SPYValue *value = get_index(c, source, key);
                int status = value ? (keywords ? merge_keyword(c, result, key, value) : map_set(c, result, key, value)) : -1;
                spy_release(key); spy_release(value);
                if (status) break;
            }
            spy_release(iterator);
            return c->error_type[0] ? -1 : 0;
        }
        if (source->type != SPY_DICT) {
            errorf(c, "TypeError", "'%s' object is not a mapping", type_name(source)); return -1;
        }
        for (size_t i = 0; i < source->as.map.len; i++) {
            Entry *entry = &source->as.map.items[i];
            if (keywords ? merge_keyword(c, result, entry->key, entry->value) : map_set(c, result, entry->key, entry->value)) return -1;
        }
        return 0;
    }
    SPYValue *iterator = get_iterator(c, source);
    if (!iterator && result->type != SPY_SET && !iterable_type(source) && error_is(c, "TypeError")) {
        spy_clear_error(c);
        errorf(c, "TypeError", "Value after * must be an iterable, not %s", type_name(source));
    }
    if (!iterator) return -1;
    for (;;) {
        if (c->step_limit && ++c->steps > c->step_limit) { spy_error(c, "RuntimeError", "execution step limit exceeded"); break; }
        SPYValue *item = iterator_next(c, iterator);
        if (!item) break;
        int status = display_add(c, result, item);
        spy_release(item);
        if (status) break;
    }
    spy_release(iterator);
    return c->error_type[0] ? -1 : 0;
}
static int extend_display(SPYContext *c, SPYValue *result, SPYValue *source) {
    return extend_container(c, result, source, 0);
}
static int tick(SPYContext *c, Frame *f, Node *n) {
    if (c->error_type[0]) return -1;
    c->line = n->line;
    snprintf(c->filename, sizeof(c->filename), "%s", f->unit->as.unit.filename);
    if (c->step_limit && ++c->steps > c->step_limit) {
        spy_error(c, "RuntimeError", "execution step limit exceeded"); return -1;
    }
    return 0;
}
static SPYValue *number_literal(SPYContext *c, Node *n) {
    char *s = copy_text(c, n->text, strlen(n->text));
    if (!s) return NULL;
    size_t j = 0;
    int base = 10;
    if (n->text[0] == '0' && n->text[1]) {
        int ch = tolower((unsigned char)n->text[1]);
        if (ch == 'x' || ch == 'o' || ch == 'b') base = ch == 'x' ? 16 : ch == 'o' ? 8 : 2;
    }
    for (size_t i = 0; n->text[i]; i++) {
        if (n->text[i] == '_') {
            int prev = i ? hex_digit(n->text[i - 1]) : -1;
            int next = hex_digit(n->text[i + 1]);
            if ((!i || prev < 0 || prev >= base) && !(base != 10 && i == 2)) prev = -1;
            else prev = 0;
            if (prev < 0 || next < 0 || next >= base) {
                free(s); return spy_error(c, "SyntaxError", "invalid numeric separator");
            }
        } else s[j++] = n->text[i];
    }
    s[j] = 0;
    char *end;
    SPYValue *v = NULL;
    errno = 0;
    if (n->kind == N_FLOAT) {
        double d = strtod(s, &end);
        if (*end) spy_error(c, "SyntaxError", "invalid floating-point literal");
        else v = spy_float(c, d);
    } else {
        char *digits = s;
        if (s[0] == '0' && s[1]) {
            int ch = tolower((unsigned char)s[1]);
            if (ch == 'x' || ch == 'o' || ch == 'b') { base = ch == 'x' ? 16 : ch == 'o' ? 8 : 2; digits += 2; }
            else for (size_t i = 1; s[i]; i++) if (s[i] != '0') { spy_error(c, "SyntaxError", "leading zeros in decimal literal"); break; }
        }
        int64_t i = strtoll(digits, &end, base);
        if (!*digits || *end) spy_error(c, "SyntaxError", "invalid integer literal");
        else if (errno == ERANGE) spy_error(c, "OverflowError", "integer literal exceeds signed 64-bit limit");
        else if (!c->error_type[0]) v = spy_int(c, i);
    }
    free(s); return v;
}
static SPYValue *make_function(SPYContext *c, Frame *f, Node *n) {
    SPYValue *fn = value_new(c, SPY_FUNCTION);
    if (!fn) return NULL;
    fn->as.function.def = n;
    SPYValue *closure = f->env;
    while (closure->type == V_ENV && closure->as.map.flags == 1) closure = closure->as.map.parent;
    fn->as.function.env = spy_retain(closure);
    fn->as.function.unit = spy_retain(f->unit);
    for (Node *arg = n->args; arg; arg = arg->next) {
        if (!arg->a) continue;
        if (!fn->as.function.defaults) fn->as.function.defaults = value_new(c, SPY_DICT);
        if (!fn->as.function.defaults) break;
        SPYValue *value = eval(c, f, arg->a);
        if (!value) break;
        int status = name_set(c, fn->as.function.defaults, arg->text, value);
        spy_release(value);
        if (status) break;
    }
    if (c->error_type[0]) { spy_release(fn); return NULL; }
    return fn;
}
static SPYValue *eval_inner(SPYContext *c, Frame *f, Node *n) {
    if (tick(c, f, n)) return NULL;
    SPYValue *a = NULL, *b = NULL, *result = NULL;
    switch (n->kind) {
    case N_INT: case N_FLOAT: return number_literal(c, n);
    case N_STRING: return spy_string(c, n->text, (size_t)n->op);
    case N_NONE: return spy_none(c);
    case N_BOOL: return spy_bool(c, n->op);
    case N_NAME: return name_get(c, f->env, n->text);
    case N_LAMBDA: return make_function(c, f, n);
    case N_NAMED: {
        SPYValue *env = f->env;
        while (env->type == V_ENV && env->as.map.flags == 2) env = env->as.map.parent;
        result = eval(c, f, n->b);
        if (result && name_set(c, env, n->a->text, result)) { spy_release(result); result = NULL; }
        return result;
    }
    case N_COMPREHENSION: return eval_comprehension(c, f, n);
    case N_LIST: case N_TUPLE: case N_DICT: case N_SET:
        result = value_new(c, n->kind == N_LIST ? SPY_LIST : n->kind == N_TUPLE ? SPY_TUPLE : n->kind == N_SET ? SPY_SET : SPY_DICT);
        if (!result) return NULL;
        for (Node *item = n->args; item; item = item->next) {
            if (item->kind == N_STAR || item->kind == N_MAPPING) {
                a = eval(c, f, item->a);
                if (!a) goto container_fail;
                if (extend_display(c, result, a)) goto container_fail;
                spy_release(a); a = NULL;
                continue;
            }
            a = eval(c, f, n->kind == N_DICT ? item->a : item);
            if (!a) goto container_fail;
            if (n->kind == N_DICT) {
                b = eval(c, f, item->b);
                if (!b || map_set(c, result, a, b)) goto container_fail;
            } else if (display_add(c, result, a)) goto container_fail;
            spy_release(a); spy_release(b); a = b = NULL;
        }
        return result;
container_fail:
        spy_release(result); result = NULL; break;
    case N_UNARY:
        a = eval(c, f, n->a);
        if (!a) break;
        if (n->op == O_NOT) result = spy_bool(c, !spy_truth(a));
        else if (n->op == '~' && is_int(a)) result = spy_int(c, ~a->as.integer);
        else if ((n->op == '+' || n->op == '-') && is_number(a)) {
            if (is_int(a)) {
                if (n->op == '-' && a->as.integer == INT64_MIN) spy_error(c, "OverflowError", "integer negation overflow");
                else result = spy_int(c, n->op == '-' ? -a->as.integer : a->as.integer);
            } else result = spy_float(c, n->op == '-' ? -a->as.real : a->as.real);
        } else spy_error(c, "TypeError", "unsupported unary operand");
        break;
    case N_BINARY:
        a = eval(c, f, n->a);
        if (!a) break;
        if (n->op == O_AND || n->op == O_OR) {
            int use_left = n->op == O_AND ? !spy_truth(a) : spy_truth(a);
            result = use_left ? spy_retain(a) : eval(c, f, n->b);
        } else {
            b = eval(c, f, n->b);
            if (b) result = binary(c, n->op, a, b);
        }
        break;
    case N_COMPARE:
        a = eval(c, f, n->a);
        if (!a) break;
        for (Node *cmp = n->args; cmp; cmp = cmp->next) {
            b = eval(c, f, cmp->a);
            if (!b) break;
            result = comparison(c, cmp->op, a, b);
            spy_release(a); a = b; b = NULL;
            if (!result || !spy_truth(result) || !cmp->next) break;
            spy_release(result); result = NULL;
        }
        break;
    case N_COND:
        a = eval(c, f, n->b);
        if (a) result = eval(c, f, spy_truth(a) ? n->a : n->c);
        break;
    case N_INDEX:
        a = eval(c, f, n->a);
        if (a) b = eval(c, f, n->b);
        if (b) result = get_index(c, a, b);
        break;
    case N_ATTR:
        a = eval(c, f, n->a);
        if (a) result = attribute(c, a, n->b->text);
        break;
    case N_CALL: {
        a = eval(c, f, n->a);
        if (!a) break;
        SPYValue *args = spy_list(c), *keywords = value_new(c, SPY_DICT);
        if (!args || !keywords) { spy_release(args); spy_release(keywords); break; }
        /* Python evaluates all positional arguments (including * after a
         * keyword) before evaluating the keyword arguments. */
        for (int pass = 0; pass < 2 && !c->error_type[0]; pass++) {
            for (Node *arg = n->args; arg && !c->error_type[0]; arg = arg->next) {
                int keyword = arg->kind == N_KEYWORD || arg->kind == N_MAPPING;
                if (keyword != pass) continue;
                SPYValue *value = eval(c, f, keyword || arg->kind == N_STAR ? arg->a : arg);
                if (!value) break;
                if (arg->kind == N_MAPPING) extend_container(c, keywords, value, 1);
                else if (arg->kind == N_KEYWORD) {
                    SPYValue *key = spy_string(c, arg->text, strlen(arg->text));
                    if (key) merge_keyword(c, keywords, key, value);
                    spy_release(key);
                } else if (arg->kind == N_STAR) extend_display(c, args, value);
                else sequence_append(c, args, value);
                spy_release(value);
            }
        }
        if (!c->error_type[0]) result = call_keywords(c, a, args->as.seq.len, args->as.seq.items, keywords);
        spy_release(args); spy_release(keywords); break;
    }
    default: spy_error(c, "RuntimeError", "invalid expression node"); break;
    }
    spy_release(a); spy_release(b);
    return result;
}
static SPYValue *eval(SPYContext *c, Frame *f, Node *n) {
    if (++c->depth > 256) { c->depth--; return spy_error(c, "RecursionError", "evaluation nesting limit exceeded"); }
    SPYValue *v = eval_inner(c, f, n);
    c->depth--;
    return v;
}

static int declare_name(SPYContext *c, SPYValue *env, const char *name) {
    if (name_local(env, name)) return 0;
    SPYValue *v = value_new(c, V_UNBOUND);
    if (!v) return -1;
    int status = name_set(c, env, name, v);
    spy_release(v);
    return status;
}
static int declare_target(SPYContext *c, SPYValue *env, Node *n) {
    if (n->kind == N_NAME) return declare_name(c, env, n->text);
    if (n->kind == N_STAR) return declare_target(c, env, n->a);
    if (n->kind == N_LIST || n->kind == N_TUPLE)
        for (Node *item = n->args; item; item = item->next)
            if (declare_target(c, env, item)) return -1;
    return 0;
}
static int declare_named(SPYContext *c, SPYValue *env, Node *n) {
    for (; n; n = n->next) {
        if (n->kind == N_NAMED && declare_name(c, env, n->a->text)) return -1;
        if (n->kind == N_DEF || n->kind == N_LAMBDA || n->kind == N_CLASS) {
            if (declare_named(c, env, n->args)) return -1;
            continue;
        }
        if (declare_named(c, env, n->a) || declare_named(c, env, n->b) ||
            declare_named(c, env, n->c) || declare_named(c, env, n->args)) return -1;
    }
    return 0;
}
static int declare_locals(SPYContext *c, SPYValue *env, Node *body) {
    if (declare_named(c, env, body)) return -1;
    for (Node *n = body; n; n = n->next) {
        Node *name = NULL;
        if (n->kind == N_ASSIGN) {
            if (declare_target(c, env, n->a)) return -1;
            for (Node *t = n->args; t; t = t->next)
                if (declare_target(c, env, t)) return -1;
        }
        if (n->kind == N_DELETE && declare_target(c, env, n->a)) return -1;
        if (n->kind == N_WITH) {
            for (Node *item = n->args; item; item = item->next)
                if (item->b && declare_target(c, env, item->b)) return -1;
            if (declare_locals(c, env, n->b)) return -1;
        }
        if (n->kind == N_DEF || n->kind == N_CLASS) name = n->a;
        if (n->kind == N_FOR && declare_target(c, env, n->args)) return -1;
        if (n->kind == N_IMPORT || n->kind == N_FROM) name = n->c ? n->c : n->kind == N_FROM ? n->b : n->a;
        if (name && declare_name(c, env, name->text)) return -1;
        if (n->kind == N_IF || n->kind == N_WHILE || n->kind == N_FOR)
            if (declare_locals(c, env, n->b) || declare_locals(c, env, n->c)) return -1;
        if (n->kind == N_TRY) {
            if (declare_locals(c, env, n->a) || declare_locals(c, env, n->b) || declare_locals(c, env, n->c)) return -1;
            for (Node *h = n->args; h; h = h->next)
                if ((h->c && declare_target(c, env, h->c)) || declare_locals(c, env, h->b)) return -1;
        }
    }
    return 0;
}
static SPYValue *new_instance(SPYContext *c, SPYValue *cls) {
    SPYValue *v = value_new(c, SPY_INSTANCE);
    if (v) v->as.map.parent = spy_retain(cls);
    return v;
}
static SPYValue *new_exception(SPYContext *c, SPYValue *cls, size_t argc, SPYValue *const *argv) {
    SPYValue *v = new_instance(c, cls), *args = value_new(c, SPY_TUPLE);
    if (!v || !args) { spy_release(v); spy_release(args); return NULL; }
    int status = 0;
    for (size_t i = 0; i < argc && !status; i++) status = sequence_append(c, args, argv[i]);
    if (!status) status = name_set(c, v, "args", args);
    spy_release(args);
    if (status) { spy_release(v); return NULL; }
    return v;
}
static int bind_arguments(SPYContext *c, SPYValue *fn, SPYValue *env, size_t argc, SPYValue *const *argv, SPYValue *keywords) {
    Node *def = fn->as.function.def, *rest = NULL;
    size_t index = 0;
    for (Node *arg = def->args; arg; arg = arg->next) {
        if (arg->op == P_KWARGS) { rest = arg; continue; }
        SPYValue *value = NULL;
        if (arg->op == P_VARARGS) {
            value = value_new(c, SPY_TUPLE);
            if (!value) return -1;
            while (index < argc && !c->error_type[0]) sequence_append(c, value, argv[index++]);
        } else {
            SPYValue *keyword = keywords && arg->op != P_POSONLY ? name_local(keywords, arg->text) : NULL;
            if ((arg->op == P_POSITIONAL || arg->op == P_POSONLY) && index < argc) {
                if (keyword) { errorf(c, "TypeError", "%s() got multiple values for argument '%s'", def->a->text, arg->text); return -1; }
                value = spy_retain(argv[index++]);
            } else if (keyword) value = spy_retain(keyword);
            else if (fn->as.function.defaults) value = spy_retain(name_local(fn->as.function.defaults, arg->text));
            if (!value) { errorf(c, "TypeError", "%s() missing required argument: '%s'", def->a->text, arg->text); return -1; }
        }
        int status = name_set(c, env, arg->text, value);
        spy_release(value);
        if (status || c->error_type[0]) return -1;
    }
    if (index < argc) { errorf(c, "TypeError", "%s() got too many positional arguments", def->a->text); return -1; }
    SPYValue *extra = rest ? value_new(c, SPY_DICT) : NULL;
    if (rest && !extra) return -1;
    if (keywords) for (size_t i = 0; i < keywords->as.map.len; i++) {
        Entry *entry = &keywords->as.map.items[i];
        const char *name = entry->key->as.string.data;
        Node *arg;
        for (arg = def->args; arg; arg = arg->next)
            if ((arg->op == P_POSITIONAL || arg->op == P_KWONLY) && !strcmp(arg->text, name)) break;
        if (arg) continue;
        if (extra) { if (map_set(c, extra, entry->key, entry->value)) break; }
        else { errorf(c, "TypeError", "%s() got an unexpected keyword argument '%s'", def->a->text, name); break; }
    }
    if (extra && !c->error_type[0]) name_set(c, env, rest->text, extra);
    spy_release(extra);
    return c->error_type[0] ? -1 : 0;
}
static SPYValue *call_keywords(SPYContext *c, SPYValue *fn, size_t argc, SPYValue *const *argv, SPYValue *keywords) {
    if (!same_context(c, fn)) return NULL;
    for (size_t i = 0; i < argc; i++) if (!same_context(c, argv[i])) return NULL;
    if (keywords) for (size_t i = 0; i < keywords->as.map.len; i++)
        if (keywords->as.map.items[i].key->type != SPY_STRING) return spy_error(c, "TypeError", "keywords must be strings");
    if (++c->depth > 256) { c->depth--; return spy_error(c, "RecursionError", "call nesting limit exceeded"); }
    SPYValue *result = NULL;
    if (fn->type == SPY_NATIVE || fn->type == SPY_BOUND_METHOD) {
        if (keywords && keywords->as.map.len) spy_error(c, "TypeError", "builtin does not accept keyword arguments");
        else result = fn->type == SPY_NATIVE ? fn->as.native.call(c, argc, argv, fn->as.native.data) : bound_call(c, fn, argc, argv);
    }
    else if (fn->type == SPY_METHOD) {
        if (argc >= SIZE_MAX / sizeof(SPYValue *) - 1) spy_error(c, "MemoryError", "too many arguments");
        else {
            SPYValue **args = allocate(c, (argc + 1) * sizeof(*args));
            if (args) {
                args[0] = fn->as.method.self;
                for (size_t i = 0; i < argc; i++) args[i + 1] = argv[i];
                result = call_keywords(c, fn->as.method.function, argc + 1, args, keywords);
                free(args);
            }
        }
    } else if (fn->type == SPY_CLASS) {
        if (fn->as.map.native) {
            result = builtin_keywords(c, argc, argv, fn->as.map.native - 1, keywords);
        } else if (fn->as.map.flags == 2) {
            spy_error(c, "TypeError", "this builtin type cannot be instantiated");
        } else {
        int exception = subclass(fn, name_local(c->builtins, "BaseException"));
        result = exception ? new_exception(c, fn, argc, argv) : new_instance(c, fn);
        SPYValue *init = result ? special_method(c, result, "__init__") : NULL;
        if (init) {
            SPYValue *value = call_keywords(c, init, argc, argv, keywords);
            if (value && value->type != SPY_NONE) spy_error(c, "TypeError", "__init__() should return None");
            spy_release(value); spy_release(init);
        } else if ((!exception && argc) || (keywords && keywords->as.map.len)) spy_error(c, "TypeError", "class takes no arguments");
        if (c->error_type[0]) { spy_release(result); result = NULL; }
        }
    } else if (fn->type == SPY_INSTANCE) {
        SPYValue *method = special_method(c, fn, "__call__");
        if (method) { result = call_keywords(c, method, argc, argv, keywords); spy_release(method); }
        else spy_error(c, "TypeError", "object is not callable");
    }
    else if (fn->type == SPY_FUNCTION) {
        Node *def = fn->as.function.def;
        {
            SPYValue *env = value_new(c, V_ENV);
            if (env) {
                env->as.map.parent = spy_retain(fn->as.function.env);
                if (!bind_arguments(c, fn, env, argc, argv, keywords) && !declare_locals(c, env, def->b)) {
                    Frame frame = { env, fn->as.function.unit };
                    Result r = execute(c, &frame, def->b);
                    if (r.flow == FLOW_RETURN) result = r.value;
                    else { spy_release(r.value); if (r.flow == FLOW_NORMAL) result = spy_none(c); }
                }
                spy_release(env);
            }
        }
    } else spy_error(c, "TypeError", "object is not callable");
    c->depth--;
    if (c->error_type[0]) { spy_release(result); result = NULL; }
    if (!result && !c->error_type[0]) spy_error(c, "RuntimeError", "native function returned NULL without an error");
    return result;
}
SPYValue *spy_call(SPYContext *c, SPYValue *fn, size_t argc, SPYValue *const *argv) {
    return call_keywords(c, fn, argc, argv, NULL);
}
static SPYValue *import_module(SPYContext *c, const char *name) {
    SPYValue *cached = name_local(c->modules, name);
    if (cached) return spy_retain(cached);
    if (!c->loader) return errorf(c, "ModuleNotFoundError", "no loader installed for '%s'", name);
    char *source = c->loader(c->loader_data, name);
    if (!source) return errorf(c, "ModuleNotFoundError", "no module named '%s'", name);
    SPYValue *unit = parse(c, source, name);
    free(source);
    if (!unit) return NULL;
    SPYValue *module = value_new(c, SPY_MODULE);
    SPYValue *module_name = spy_string(c, name, strlen(name));
    if (!module || !module_name) { spy_release(module); spy_release(module_name); spy_release(unit); return NULL; }
    module->as.map.parent = spy_retain(c->builtins);
    if (name_set(c, module, "__name__", module_name) || name_set(c, c->modules, name, module)) {
        spy_release(module_name); spy_release(module); spy_release(unit); return NULL;
    }
    spy_release(module_name);
    Frame frame = {module, unit};
    Result result = execute(c, &frame, unit->as.unit.body);
    spy_release(result.value); spy_release(unit);
    if (result.flow == FLOW_ERROR) {
        /* A failed import must not leave a half-initialized cached module. */
        for (size_t i = 0; i < c->modules->as.map.len; i++) {
            Entry *e = &c->modules->as.map.items[i];
            if (!strcmp(e->key->as.string.data, name)) {
                spy_release(e->key); spy_release(e->value);
                c->modules->as.map.len--;
                memmove(e, e + 1, (c->modules->as.map.len - i) * sizeof(*e));
                break;
            }
        }
        spy_release(module); return NULL;
    }
    return module;
}
static int store_target(SPYContext *c, Frame *f, Node *n, SPYValue *value) {
    if (tick(c, f, n)) return -1;
    if (n->kind == N_NAME) return name_set(c, f->env, n->text, value);
    if (n->kind == N_ATTR) {
        SPYValue *object = eval(c, f, n->a);
        if (!object) return -1;
        int status = set_attribute(c, object, n->b->text, value);
        spy_release(object); return status;
    }
    if (n->kind == N_INDEX) {
        SPYValue *container = eval(c, f, n->a);
        SPYValue *key = container ? eval(c, f, n->b) : NULL;
        int status = key ? set_index(c, container, key, value) : -1;
        spy_release(container); spy_release(key);
        return status;
    }
    size_t count = 0, star = SIZE_MAX;
    for (Node *item = n->args; item; item = item->next) {
        if (item->kind == N_STAR) star = count;
        count++;
    }
    if (!iterable_type(value)) {
        const char *name = value->type == SPY_INT ? "int" : value->type == SPY_FLOAT ? "float" :
                           value->type == SPY_BOOL ? "bool" : value->type == SPY_NONE ? "NoneType" : "object";
        errorf(c, "TypeError", "cannot unpack non-iterable %s object", name);
        return -1;
    }
    SPYValue *items = spy_list(c), *iterator = get_iterator(c, value);
    if (!items || !iterator) { spy_release(items); spy_release(iterator); return -1; }
    for (size_t i = 0; star != SIZE_MAX || i <= count; i++) {
        if (tick(c, f, n)) break;
        SPYValue *item = iterator_next(c, iterator);
        if (!item) break;
        int status = sequence_append(c, items, item);
        spy_release(item);
        if (status) break;
    }
    size_t got = items->as.seq.len, required = count - (star != SIZE_MAX);
    if (!c->error_type[0] && got < required) {
        errorf(c, "ValueError", "not enough values to unpack (expected %s%zu, got %zu)",
               star == SIZE_MAX ? "" : "at least ", required, got);
    } else if (!c->error_type[0] && star == SIZE_MAX && got > count) {
        if (value->type == SPY_LIST || value->type == SPY_TUPLE)
            errorf(c, "ValueError", "too many values to unpack (expected %zu, got %zu)", count, value->as.seq.len);
        else if (value->type == SPY_DICT)
            errorf(c, "ValueError", "too many values to unpack (expected %zu, got %zu)", count, value->as.map.len);
        else errorf(c, "ValueError", "too many values to unpack (expected %zu)", count);
    }
    size_t index = 0;
    for (Node *item = n->args; item && !c->error_type[0]; item = item->next) {
        if (item->kind == N_STAR) {
            SPYValue *rest = spy_list(c);
            if (!rest) break;
            size_t stop = got - (count - star - 1);
            while (index < stop && !sequence_append(c, rest, items->as.seq.items[index])) index++;
            if (!c->error_type[0]) store_target(c, f, item->a, rest);
            spy_release(rest);
        } else store_target(c, f, item, items->as.seq.items[index++]);
    }
    spy_release(items); spy_release(iterator);
    return c->error_type[0] ? -1 : 0;
}
static int comprehension_run(SPYContext *c, Frame *f, Node *n, Node *clause,
                             SPYValue *iterable, SPYValue *result) {
    if (!clause) {
        Node *item = n->args;
        if (item->kind == N_STAR || item->kind == N_MAPPING) {
            SPYValue *source = eval(c, f, item->a);
            if (!source) return -1;
            int status = extend_display(c, result, source);
            spy_release(source);
            return status;
        }
        SPYValue *key = eval(c, f, n->op == N_DICT ? item->a : item);
        if (!key) return -1;
        SPYValue *value = n->op == N_DICT ? eval(c, f, item->b) : NULL;
        int status = n->op == N_DICT ? (value ? map_set(c, result, key, value) : -1) : display_add(c, result, key);
        spy_release(key); spy_release(value);
        return status;
    }
    if (tick(c, f, clause)) return -1;
    if (clause->kind == N_IF) {
        SPYValue *test = eval(c, f, clause->a);
        if (!test) return -1;
        int truth = spy_truth(test); spy_release(test);
        return truth ? comprehension_run(c, f, n, clause->b, NULL, result) : 0;
    }
    SPYValue *value = iterable ? spy_retain(iterable) : eval(c, f, clause->a);
    SPYValue *source = value ? get_iterator(c, value) : NULL;
    spy_release(value);
    if (!source) return -1;
    for (size_t i = 0; !c->error_type[0]; i++) {
        if (tick(c, f, clause)) break;
        SPYValue *item = iter_at(c, source, i);
        if (!item) break;
        int status = store_target(c, f, clause->args, item);
        spy_release(item);
        if (status || comprehension_run(c, f, n, clause->b, NULL, result)) break;
    }
    spy_release(source);
    return c->error_type[0] ? -1 : 0;
}
static SPYValue *eval_comprehension(SPYContext *c, Frame *f, Node *n) {
    /* Only the outer iterable is evaluated in the enclosing scope. */
    SPYValue *source = eval(c, f, n->a->a);
    if (!source) return NULL;
    SPYValue *env = value_new(c, V_ENV);
    SPYValue *result = value_new(c, n->op == N_DICT ? SPY_DICT : n->op == N_SET ? SPY_SET : n->op == N_TUPLE ? SPY_GENERATOR : SPY_LIST);
    if (env && result) {
        env->as.map.flags = 2;
        env->as.map.parent = spy_retain(f->env);
        for (Node *clause = n->a; clause; clause = clause->b)
            if (clause->kind == N_FOR && declare_target(c, env, clause->args)) break;
        Frame frame = { env, f->unit };
        if (!c->error_type[0] && n->op == N_TUPLE) {
            result->as.generator.env = spy_retain(env);
            result->as.generator.unit = spy_retain(f->unit);
            result->as.generator.node = n;
            SPYValue *iterator = get_iterator(c, source);
            if (iterator && !grow(c, (void **)&result->as.generator.loops, &result->as.generator.cap, 1, sizeof(GeneratorLoop))) {
                result->as.generator.loops[0] = (GeneratorLoop){n->a, iterator};
                result->as.generator.len = 1;
            } else spy_release(iterator);
        } else if (!c->error_type[0]) comprehension_run(c, &frame, n, n->a, source, result);
    }
    spy_release(source); spy_release(env);
    if (c->error_type[0]) { spy_release(result); return NULL; }
    return result;
}
static void generator_close(SPYValue *v) {
    while (v->as.generator.len) spy_release(v->as.generator.loops[--v->as.generator.len].iterator);
    spy_release(v->as.generator.expanded); v->as.generator.expanded = NULL;
    spy_release(v->as.generator.env); v->as.generator.env = NULL;
    spy_release(v->as.generator.unit); v->as.generator.unit = NULL;
    v->as.generator.done = 1;
}
static SPYValue *generator_next(SPYContext *c, SPYValue *v) {
    if (v->as.generator.done) return NULL;
    if (v->as.generator.running) return spy_error(c, "ValueError", "generator already executing");
    if (++c->depth > 256) { c->depth--; return spy_error(c, "RecursionError", "generator nesting limit exceeded"); }
    v->as.generator.running = 1;
    Frame f = {v->as.generator.env, v->as.generator.unit};
    Node *n = v->as.generator.node;
    SPYValue *result = NULL;
    while (!c->error_type[0]) {
        if (tick(c, &f, n)) break;
        if (v->as.generator.expanded) {
            result = iterator_next(c, v->as.generator.expanded);
            if (result || c->error_type[0]) break;
            spy_release(v->as.generator.expanded); v->as.generator.expanded = NULL;
        }
        if (!v->as.generator.len) break;
        GeneratorLoop *loop = &v->as.generator.loops[v->as.generator.len - 1];
        SPYValue *item = iterator_next(c, loop->iterator);
        if (!item) {
            spy_release(loop->iterator); v->as.generator.len--;
            continue;
        }
        int status = store_target(c, &f, loop->clause->args, item);
        spy_release(item);
        if (status) break;
        Node *clause = loop->clause->b;
        int rejected = 0;
        while (clause && clause->kind == N_IF) {
            SPYValue *test = eval(c, &f, clause->a);
            if (!test) { rejected = 1; break; }
            int truth = spy_truth(test); spy_release(test);
            if (!truth) { rejected = 1; break; }
            clause = clause->b;
        }
        if (rejected) continue;
        if (clause) {
            SPYValue *value = eval(c, &f, clause->a);
            SPYValue *iterator = value ? get_iterator(c, value) : NULL;
            spy_release(value);
            if (!iterator) break;
            if (grow(c, (void **)&v->as.generator.loops, &v->as.generator.cap, v->as.generator.len + 1, sizeof(GeneratorLoop))) {
                spy_release(iterator); break;
            }
            v->as.generator.loops[v->as.generator.len++] = (GeneratorLoop){clause, iterator};
            continue;
        }
        Node *element = n->args;
        if (element->kind == N_STAR) {
            SPYValue *value = eval(c, &f, element->a);
            if (value) v->as.generator.expanded = get_iterator(c, value);
            spy_release(value);
        } else { result = eval(c, &f, element); break; }
    }
    if (!result) {
        if (error_is(c, "StopIteration")) {
            spy_clear_error(c); spy_error(c, "RuntimeError", "generator raised StopIteration");
        }
        generator_close(v);
    }
    v->as.generator.running = 0; c->depth--;
    return result;
}
static int assign(SPYContext *c, Frame *f, Node *n) {
    if (n->op == '=') {
        SPYValue *value = eval(c, f, n->b);
        if (!value) return -1;
        int status = store_target(c, f, n->a, value);
        for (Node *t = n->args; t && !status; t = t->next) status = store_target(c, f, t, value);
        spy_release(value);
        return status;
    }
    SPYValue *container = NULL, *key = NULL, *old = NULL, *rhs = NULL, *value = NULL;
    int status = -1;
    /* Augmented assignment evaluates the target once, before the RHS. */
    if (n->a->kind == N_INDEX || n->a->kind == N_ATTR) {
        container = eval(c, f, n->a->a);
        if (!container) goto done;
        if (n->a->kind == N_INDEX) {
            key = eval(c, f, n->a->b);
            if (!key) goto done;
        }
    }
    {
        old = container ? (key ? get_index(c, container, key) : attribute(c, container, n->a->b->text)) : name_get(c, f->env, n->a->text);
        if (!old) goto done;
        rhs = eval(c, f, n->b);
        if (!rhs) goto done;
        int ops[] = {'+', '-', '*', '/', '%'};
        if (n->op == T_ADDEQ && old->type == SPY_LIST && (rhs->type == SPY_LIST || rhs->type == SPY_TUPLE)) {
            size_t len = rhs->as.seq.len;
            for (size_t i = 0; i < len; i++) if (sequence_append(c, old, rhs->as.seq.items[i])) goto done;
            value = spy_retain(old);
        } else value = binary(c, ops[n->op - T_ADDEQ], old, rhs);
    }
    if (!value) goto done;
    if (!container) status = name_set(c, f->env, n->a->text, value);
    else if (key) status = set_index(c, container, key, value);
    else status = set_attribute(c, container, n->a->b->text, value);
done:
    spy_release(container); spy_release(key); spy_release(old); spy_release(rhs); spy_release(value);
    return status;
}
static SPYValue *new_class(SPYContext *c, const char *name, SPYValue *base, SPYValue *module) {
    SPYValue *cls = value_new(c, SPY_CLASS), *text = spy_string(c, name, strlen(name));
    if (!cls || !text) { spy_release(cls); spy_release(text); return NULL; }
    cls->as.map.parent = spy_retain(base);
    int status = name_set(c, cls, "__name__", text) || name_set(c, cls, "__qualname__", text) || name_set(c, cls, "__module__", module);
    spy_release(text);
    if (status) { spy_release(cls); return NULL; }
    return cls;
}
static int execute_class(SPYContext *c, Frame *f, Node *n) {
    if (n->args && n->args->next) { spy_error(c, "NotImplementedError", "multiple inheritance is not implemented"); return -1; }
    SPYValue *base = n->args ? eval(c, f, n->args) : spy_retain(name_local(c->builtins, "object"));
    if (!base) return -1;
    if (base->type != SPY_CLASS) { spy_release(base); spy_error(c, "TypeError", "base must be a class"); return -1; }
    if (base->as.map.native || base->as.map.flags == 2) { spy_release(base); spy_error(c, "NotImplementedError", "subclassing builtin types is not implemented"); return -1; }
    SPYValue *module = name_get(c, f->env, "__name__");
    SPYValue *cls = module ? new_class(c, n->a->text, base, module) : NULL;
    spy_release(base); spy_release(module);
    SPYValue *env = cls ? value_new(c, V_ENV) : NULL;
    if (!env) { spy_release(cls); return -1; }
    env->as.map.flags = 1; /* Class namespaces are not method closure scopes. */
    SPYValue *outer = f->env;
    while (outer->type == V_ENV && outer->as.map.flags) outer = outer->as.map.parent;
    env->as.map.parent = spy_retain(outer);
    name_set(c, env, "__module__", name_local(cls, "__module__"));
    name_set(c, env, "__qualname__", name_local(cls, "__qualname__"));
    Frame frame = {env, f->unit};
    Result r = execute(c, &frame, n->b);
    spy_release(r.value);
    if (r.flow == FLOW_NORMAL) {
        for (size_t i = 0; i < env->as.map.len; i++) {
            Entry *entry = &env->as.map.items[i];
            if (map_set(c, cls, entry->key, entry->value)) break;
        }
        if (!c->error_type[0]) name_set(c, f->env, n->a->text, cls);
    }
    spy_release(env); spy_release(cls);
    return c->error_type[0] ? -1 : 0;
}
static SPYValue *raise_value(SPYContext *c, SPYValue *value) {
    SPYValue *exception = value->type == SPY_CLASS ? spy_call(c, value, 0, NULL) : spy_retain(value);
    if (!exception) return NULL;
    if (exception->type != SPY_INSTANCE || !subclass(exception->as.map.parent, name_local(c->builtins, "BaseException"))) {
        spy_release(exception); return spy_error(c, "TypeError", "exceptions must derive from BaseException");
    }
    SPYValue *cls = exception->as.map.parent, *args = name_local(exception, "args");
    SPYValue *message = NULL;
    if (args && args->type == SPY_TUPLE && args->as.seq.len)
        message = stringify(c, args->as.seq.len == 1 ? args->as.seq.items[0] : args,
                            args->as.seq.len == 1 && subclass(cls, name_local(c->builtins, "KeyError")));
    SPYValue *name = name_local(cls, "__qualname__"), *module = name_local(cls, "__module__");
    char type[sizeof(c->error_type)];
    if (module && module->type == SPY_STRING && strcmp(module->as.string.data, "builtins"))
        snprintf(type, sizeof(type), "%s.%s", module->as.string.data, name->as.string.data);
    else snprintf(type, sizeof(type), "%s", name->as.string.data);
    errorf(c, type, "%s", message ? message->as.string.data : "");
    spy_release(c->exception); c->exception = exception;
    spy_release(message);
    return NULL;
}
typedef struct {
    char type[64], message[256], filename[256];
    size_t line;
    SPYValue *value;
} ErrorState;
static ErrorState take_error(SPYContext *c) {
    ErrorState state;
    memcpy(state.type, c->error_type, sizeof(state.type));
    memcpy(state.message, c->error_message, sizeof(state.message));
    memcpy(state.filename, c->filename, sizeof(state.filename));
    state.line = c->line;
    state.value = c->exception; c->exception = NULL;
    spy_clear_error(c);
    if (!state.value && state.type[0]) {
        SPYValue *cls = name_local(c->builtins, state.type);
        if (!cls) cls = name_local(c->builtins, "RuntimeError");
        SPYValue *message = spy_string(c, state.message, strlen(state.message));
        if (message) state.value = new_exception(c, cls, state.message[0] ? 1 : 0, &message);
        spy_release(message);
    }
    return state;
}
static void restore_error(SPYContext *c, ErrorState *state) {
    spy_clear_error(c);
    memcpy(c->error_type, state->type, sizeof(c->error_type));
    memcpy(c->error_message, state->message, sizeof(c->error_message));
    memcpy(c->filename, state->filename, sizeof(c->filename));
    c->line = state->line; c->exception = state->value; state->value = NULL;
}
static int exception_matches(SPYContext *c, SPYValue *exception, SPYValue *type) {
    if (type->type == SPY_TUPLE) {
        for (size_t i = 0; i < type->as.seq.len; i++) {
            int match = exception_matches(c, exception, type->as.seq.items[i]);
            if (match) return match;
        }
        return 0;
    }
    if (type->type != SPY_CLASS || !subclass(type, name_local(c->builtins, "BaseException"))) {
        spy_error(c, "TypeError", "catching classes that do not inherit from BaseException is not allowed"); return -1;
    }
    return subclass(exception->as.map.parent, type);
}
static void delete_name(SPYValue *env, const char *name) {
    for (size_t i = 0; i < env->as.map.len; i++) {
        Entry *entry = &env->as.map.items[i];
        if (strcmp(entry->key->as.string.data, name)) continue;
        spy_release(entry->key); spy_release(entry->value);
        env->as.map.len--;
        memmove(entry, entry + 1, (env->as.map.len - i) * sizeof(*entry));
        return;
    }
}
static int delete_target(SPYContext *c, Frame *f, Node *n) {
    if (n->kind == N_LIST || n->kind == N_TUPLE) {
        for (Node *item = n->args; item; item = item->next)
            if (delete_target(c, f, item)) return -1;
        return 0;
    }
    if (n->kind == N_NAME) {
        SPYValue *value = name_local(f->env, n->text);
        if (!value || value->type == V_UNBOUND) {
            errorf(c, value ? "UnboundLocalError" : "NameError", "name '%s' is not defined", n->text); return -1;
        }
        delete_name(f->env, n->text);
        return f->env != c->globals && f->env->type == V_ENV && !f->env->as.map.flags ? declare_name(c, f->env, n->text) : 0;
    }
    SPYValue *object = eval(c, f, n->a);
    if (!object) return -1;
    if (n->kind == N_ATTR) {
        if (object->type != SPY_INSTANCE && object->type != SPY_CLASS && object->type != SPY_MODULE)
            spy_error(c, "AttributeError", "object attributes are read-only");
        else if (object->type == SPY_CLASS && (!strcmp(n->b->text, "__name__") || !strcmp(n->b->text, "__qualname__") || !strcmp(n->b->text, "__module__")))
            spy_error(c, "TypeError", "cannot delete class name or module attributes");
        else if (!name_local(object, n->b->text)) errorf(c, "AttributeError", "object has no attribute '%s'", n->b->text);
        else delete_name(object, n->b->text);
    } else {
        SPYValue *key = eval(c, f, n->b);
        if (key) {
            if (object->type == SPY_INSTANCE) {
                SPYValue *result = call_special(c, object, "__delitem__", 1, &key);
                spy_release(result);
            } else if (object->type == SPY_DICT) {
                ptrdiff_t index = hashable(key, 0) ? map_find(object, key) : -1;
                if (!hashable(key, 0)) spy_error(c, "TypeError", "unhashable key");
                else if (index < 0) spy_error(c, "KeyError", "key not found");
                else {
                    Entry *entry = &object->as.map.items[index];
                    spy_release(entry->key); spy_release(entry->value);
                    object->as.map.len--;
                    memmove(entry, entry + 1, (object->as.map.len - (size_t)index) * sizeof(*entry));
                }
            } else if (object->type == SPY_LIST) {
                int64_t index;
                if (!spy_as_int(c, key, &index)) {
                    if (index < 0) index += (int64_t)object->as.seq.len;
                    if (index < 0 || (uint64_t)index >= object->as.seq.len) spy_error(c, "IndexError", "list assignment index out of range");
                    else {
                        spy_release(object->as.seq.items[index]); object->as.seq.len--;
                        memmove(&object->as.seq.items[index], &object->as.seq.items[index + 1], (object->as.seq.len - (size_t)index) * sizeof(SPYValue *));
                    }
                }
            } else spy_error(c, "TypeError", "object does not support item deletion");
        }
        spy_release(key);
    }
    spy_release(object);
    return c->error_type[0] ? -1 : 0;
}
static Result execute_with(SPYContext *c, Frame *f, Node *item, Node *body) {
    if (!item) return execute(c, f, body);
    if (++c->depth > 256) { c->depth--; spy_error(c, "RecursionError", "too many context managers"); return (Result){FLOW_ERROR, NULL}; }
    SPYValue *manager = eval(c, f, item->a);
    SPYValue *exit = manager ? special_method(c, manager, "__exit__") : NULL;
    SPYValue *enter = exit ? call_special(c, manager, "__enter__", 0, NULL) : NULL;
    if (!exit && manager && !c->error_type[0]) spy_error(c, "TypeError", "object does not support the context manager protocol");
    spy_release(manager);
    if (!enter) { spy_release(exit); c->depth--; return (Result){FLOW_ERROR, NULL}; }
    int status = item->b ? store_target(c, f, item->b, enter) : 0;
    spy_release(enter);
    Result r = status ? (Result){FLOW_ERROR, NULL} : execute_with(c, f, item->next, body);
    ErrorState error = take_error(c);
    SPYValue *outer = c->handled;
    c->handled = error.value ? spy_retain(error.value) : spy_retain(outer);
    SPYValue *args[] = {error.value ? error.value->as.map.parent : c->none, error.value ? error.value : c->none, c->none};
    SPYValue *result = spy_call(c, exit, 3, args);
    spy_release(exit);
    if (!result) { spy_release(r.value); r = (Result){FLOW_ERROR, NULL}; }
    else if (error.value) {
        int suppress = spy_truth(result);
        if (c->error_type[0]) { spy_release(r.value); r = (Result){FLOW_ERROR, NULL}; }
        else if (suppress) { spy_release(r.value); r = (Result){FLOW_NORMAL, NULL}; }
        else restore_error(c, &error);
    }
    spy_release(result); spy_release(error.value);
    spy_release(c->handled); c->handled = outer;
    c->depth--; return r;
}
static Result execute_try(SPYContext *c, Frame *f, Node *n) {
    Result r = execute(c, f, n->a);
    SPYValue *outer = c->handled;
    if (r.flow == FLOW_ERROR) {
        ErrorState error = take_error(c);
        int caught = 0;
        c->handled = spy_retain(error.value);
        for (Node *h = n->args; h && !c->error_type[0]; h = h->next) {
            SPYValue *type = h->a ? eval(c, f, h->a) : NULL;
            int match = !h->a ? 1 : type && error.value ? exception_matches(c, error.value, type) : -1;
            spy_release(type);
            if (match < 0) break;
            if (!match) continue;
            caught = 1;
            if (h->c) name_set(c, f->env, h->c->text, error.value);
            spy_release(r.value); r = execute(c, f, h->b);
            if (h->c) {
                delete_name(f->env, h->c->text);
                if (f->env != c->globals && f->env->type == V_ENV && !f->env->as.map.flags)
                    declare_name(c, f->env, h->c->text);
            }
            break;
        }
        if (!caught && !c->error_type[0]) restore_error(c, &error);
        spy_release(error.value);
        spy_release(c->handled); c->handled = outer;
        if (c->error_type[0]) { spy_release(r.value); r = (Result){FLOW_ERROR, NULL}; }
    } else if (r.flow == FLOW_NORMAL && n->b) {
        spy_release(r.value); r = execute(c, f, n->b);
    }
    if (n->c) {
        ErrorState error = take_error(c);
        c->handled = error.value ? spy_retain(error.value) : spy_retain(outer);
        Result final = execute(c, f, n->c);
        spy_release(c->handled); c->handled = outer;
        if (final.flow == FLOW_NORMAL) {
            spy_release(final.value);
            if (error.type[0]) restore_error(c, &error);
        } else { spy_release(r.value); r = final; }
        spy_release(error.value);
    }
    return r;
}
static Result execute(SPYContext *c, Frame *f, Node *body) {
    SPYValue *last = NULL;
    for (Node *n = body; n; n = n->next) {
        spy_release(last); last = NULL;
        if (tick(c, f, n)) break;
        switch (n->kind) {
        case N_EXPR: last = eval(c, f, n->a); break;
        case N_ASSIGN: assign(c, f, n); break;
        case N_DELETE: delete_target(c, f, n->a); break;
        case N_WITH: {
            Result r = execute_with(c, f, n->args, n->b);
            if (r.flow != FLOW_NORMAL) return r;
            spy_release(r.value); break;
        }
        case N_CLASS: execute_class(c, f, n); break;
        case N_TRY: {
            Result r = execute_try(c, f, n);
            if (r.flow != FLOW_NORMAL) return r;
            spy_release(r.value); break;
        }
        case N_RAISE: {
            SPYValue *value = n->a ? eval(c, f, n->a) : spy_retain(c->handled);
            SPYValue *cause = n->b && value ? eval(c, f, n->b) : NULL;
            if (value && !c->error_type[0]) {
                if (n->b && cause && cause->type != SPY_NONE && cause->type != SPY_CLASS && cause->type != SPY_INSTANCE)
                    spy_error(c, "TypeError", "exception causes must derive from BaseException");
                else raise_value(c, value);
                if (c->exception && cause) name_set(c, c->exception, "__cause__", cause);
            } else if (!value && !c->error_type[0]) spy_error(c, "RuntimeError", "No active exception to reraise");
            spy_release(value); spy_release(cause); break;
        }
        case N_PASS: break;
        case N_RETURN:
            last = n->a ? eval(c, f, n->a) : spy_none(c);
            return (Result){last ? FLOW_RETURN : FLOW_ERROR, last};
        case N_BREAK: return (Result){FLOW_BREAK, NULL};
        case N_CONTINUE: return (Result){FLOW_CONTINUE, NULL};
        case N_ASSERT: {
            SPYValue *test = eval(c, f, n->a);
            if (test && !spy_truth(test)) {
                SPYValue *msg = n->b ? eval(c, f, n->b) : NULL;
                SPYValue *text = msg ? stringify(c, msg, 0) : NULL;
                if (!c->error_type[0]) spy_error(c, "AssertionError", text ? text->as.string.data : "");
                spy_release(msg); spy_release(text);
            }
            spy_release(test); break;
        }
        case N_DEF: {
            SPYValue *fn = make_function(c, f, n);
            if (!fn) break;
            name_set(c, f->env, n->a->text, fn);
            spy_release(fn); break;
        }
        case N_IF: {
            SPYValue *test = eval(c, f, n->a);
            if (!test) break;
            int truth = spy_truth(test); spy_release(test);
            Result r = execute(c, f, truth ? n->b : n->c);
            if (r.flow != FLOW_NORMAL) return r;
            spy_release(r.value); break;
        }
        case N_WHILE: case N_FOR: {
            SPYValue *value = n->kind == N_FOR ? eval(c, f, n->a) : NULL;
            SPYValue *iterable = value ? get_iterator(c, value) : NULL;
            spy_release(value);
            if (n->kind == N_FOR && !iterable) break;
            int broke = 0;
            for (size_t i = 0; !c->error_type[0]; i++) {
                if (tick(c, f, n)) break;
                SPYValue *item = iterable ? iter_at(c, iterable, i) : eval(c, f, n->a);
                if (!item) break;
                if (!iterable && !spy_truth(item)) { spy_release(item); break; }
                if (iterable) store_target(c, f, n->args, item);
                spy_release(item);
                if (c->error_type[0]) break;
                Result r = execute(c, f, n->b);
                if (r.flow == FLOW_RETURN || r.flow == FLOW_ERROR) { spy_release(iterable); return r; }
                spy_release(r.value);
                if (r.flow == FLOW_BREAK) { broke = 1; break; }
            }
            spy_release(iterable);
            if (!broke && !c->error_type[0]) {
                Result r = execute(c, f, n->c);
                if (r.flow != FLOW_NORMAL) return r;
                spy_release(r.value);
            }
            break;
        }
        case N_IMPORT: case N_FROM: {
            SPYValue *module = import_module(c, n->a->text);
            if (!module) break;
            SPYValue *item = n->kind == N_FROM ? attribute(c, module, n->b->text) : spy_retain(module);
            const char *name = n->c ? n->c->text : n->kind == N_FROM ? n->b->text : n->a->text;
            if (item) name_set(c, f->env, name, item);
            spy_release(item); spy_release(module); break;
        }
        default: spy_error(c, "RuntimeError", "invalid statement node"); break;
        }
        if (c->error_type[0]) { spy_release(last); return (Result){FLOW_ERROR, NULL}; }
    }
    if (c->error_type[0]) { spy_release(last); return (Result){FLOW_ERROR, NULL}; }
    return (Result){FLOW_NORMAL, last};
}

enum { B_PRINT, B_LEN, B_RANGE, B_STR, B_REPR, B_INT, B_FLOAT, B_BOOL,
       B_LIST, B_TUPLE, B_DICT, B_ABS, B_SUM, B_MIN, B_MAX, B_ALL, B_ANY,
       B_ITER, B_NEXT, B_ZIP, B_ENUMERATE, B_REVERSED, B_SET, B_SORTED, B_ORD, B_CHR,
       B_TYPE, B_ISINSTANCE, B_ISSUBCLASS, B_GETATTR, B_SETATTR, B_HASATTR, B_CALLABLE, B_ID };
static SPYValue *value_class(SPYContext *c, SPYValue *value) {
    return value->type == SPY_INSTANCE ? value->as.map.parent : c->types[value->type];
}
static int check_subclass(SPYContext *c, SPYValue *cls, SPYValue *types, size_t depth) {
    if (depth > 128) { spy_error(c, "RecursionError", "class tuple is too deeply nested"); return -1; }
    if (types->type == SPY_TUPLE) {
        for (size_t i = 0; i < types->as.seq.len; i++) {
            int result = check_subclass(c, cls, types->as.seq.items[i], depth + 1);
            if (result) return result;
        }
        return 0;
    }
    if (types->type != SPY_CLASS) { spy_error(c, "TypeError", "second argument must be a type or tuple of types"); return -1; }
    return subclass(cls, types);
}
static int sort_list(SPYContext *c, SPYValue *list) {
    size_t len = list->as.seq.len;
    SPYValue **scratch = allocate(c, len * sizeof(*scratch));
    if (!scratch) return -1;
    /* Stable merge sort. Scratch borrows references; list retains ownership. */
    for (size_t width = 1; width < len && !c->error_type[0]; width *= 2) {
        for (size_t start = 0; start < len; start += width * 2) {
            size_t mid = start + width < len ? start + width : len;
            size_t end = mid + width < len ? mid + width : len;
            size_t left = start, right = mid;
            for (size_t out = start; out < end; out++) {
                int take_right = left == mid;
                if (left < mid && right < end && !c->error_type[0]) {
                    SPYValue *less = comparison(c, '<', list->as.seq.items[right], list->as.seq.items[left]);
                    if (less) take_right = spy_truth(less);
                    spy_release(less);
                }
                scratch[out] = take_right && right < end ? list->as.seq.items[right++] : list->as.seq.items[left++];
            }
        }
        memcpy(list->as.seq.items, scratch, len * sizeof(*scratch));
        if (width > len / 2) break;
    }
    free(scratch); return c->error_type[0] ? -1 : 0;
}
static SPYValue *builtin(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    int id = (int)(intptr_t)data;
    SPYValue *a = argc ? argv[0] : NULL;
    if (id == B_TYPE) {
        if (argc != 1) goto arity;
        return spy_retain(value_class(c, a));
    }
    if (id == B_ISINSTANCE || id == B_ISSUBCLASS) {
        if (argc != 2) goto arity;
        if (id == B_ISSUBCLASS && a->type != SPY_CLASS) return spy_error(c, "TypeError", "issubclass() arg 1 must be a class");
        int result = check_subclass(c, id == B_ISINSTANCE ? value_class(c, a) : a, argv[1], 0);
        return result < 0 ? NULL : spy_bool(c, result);
    }
    if (id == B_GETATTR || id == B_SETATTR || id == B_HASATTR) {
        if (argc < 2 || argc > 3 || (id == B_SETATTR && argc != 3) || (id == B_HASATTR && argc != 2)) goto arity;
        if (argv[1]->type != SPY_STRING) return spy_error(c, "TypeError", "attribute name must be string");
        const char *name = argv[1]->as.string.data;
        if (id == B_SETATTR) {
            return set_attribute(c, a, name, argv[2]) ? NULL : spy_none(c);
        }
        SPYValue *value = attribute(c, a, name);
        if (!value && error_is(c, "AttributeError") && (argc == 3 || id == B_HASATTR)) {
            spy_clear_error(c);
            return id == B_HASATTR ? spy_bool(c, 0) : spy_retain(argv[2]);
        }
        if (value && id == B_HASATTR) { spy_release(value); return spy_bool(c, 1); }
        return value;
    }
    if (id == B_CALLABLE) {
        if (argc != 1) goto arity;
        SPYValue *method = a->type == SPY_INSTANCE ? special_method(c, a, "__call__") : NULL;
        int result = method || a->type == SPY_CLASS || a->type == SPY_FUNCTION || a->type == SPY_NATIVE || a->type == SPY_BOUND_METHOD || a->type == SPY_METHOD;
        spy_release(method); return c->error_type[0] ? NULL : spy_bool(c, result);
    }
    if (id == B_ID) {
        if (argc != 1) goto arity;
        uintptr_t address = (uintptr_t)a;
        if (address > INT64_MAX) return spy_error(c, "OverflowError", "object address exceeds signed 64-bit limit");
        return spy_int(c, (int64_t)address);
    }
    if (id == B_SET || id == B_SORTED) {
        if ((id == B_SET && argc > 1) || (id == B_SORTED && argc != 1)) goto arity;
        SPYValue *v = value_new(c, id == B_SET ? SPY_SET : SPY_LIST);
        if (!v) return NULL;
        if ((argc && extend_display(c, v, a)) || (id == B_SORTED && sort_list(c, v))) { spy_release(v); return NULL; }
        return v;
    }
    if (id == B_ORD) {
        if (argc != 1) goto arity;
        if (a->type != SPY_STRING || string_length(a) != 1) return spy_error(c, "TypeError", "ord() expected a character");
        const unsigned char *s = (const unsigned char *)a->as.string.data;
        size_t width = utf8_width(s[0]);
        if (width > a->as.string.len) return spy_error(c, "UnicodeError", "invalid UTF-8");
        uint32_t n = s[0] & (width == 1 ? 127 : width == 2 ? 31 : width == 3 ? 15 : 7);
        for (size_t i = 1; i < width; i++) n = (n << 6) | (s[i] & 63);
        return spy_int(c, n);
    }
    if (id == B_CHR) {
        int64_t n;
        if (argc != 1) goto arity;
        if (spy_as_int(c, a, &n)) return NULL;
        if (n < 0 || n > 0x10ffff) return spy_error(c, "ValueError", "chr() arg not in range(0x110000)");
        char s[4]; size_t len;
        if (n < 128) { s[0] = (char)n; len = 1; }
        else if (n < 2048) { s[0] = (char)(0xc0 | (n >> 6)); s[1] = (char)(0x80 | (n & 63)); len = 2; }
        else if (n < 65536) { s[0] = (char)(0xe0 | (n >> 12)); s[1] = (char)(0x80 | ((n >> 6) & 63)); s[2] = (char)(0x80 | (n & 63)); len = 3; }
        else { s[0] = (char)(0xf0 | (n >> 18)); s[1] = (char)(0x80 | ((n >> 12) & 63)); s[2] = (char)(0x80 | ((n >> 6) & 63)); s[3] = (char)(0x80 | (n & 63)); len = 4; }
        return spy_string(c, s, len);
    }
    if (id == B_ITER) {
        if (argc != 1) goto arity;
        return get_iterator(c, a);
    }
    if (id == B_NEXT) {
        if (argc < 1 || argc > 2) goto arity;
        if (a->type == SPY_INSTANCE) {
            SPYValue *value = call_special(c, a, "__next__", 0, NULL);
            if (!value && argc == 2 && error_is(c, "StopIteration")) { spy_clear_error(c); return spy_retain(argv[1]); }
            return value;
        }
        if (a->type != SPY_ITERATOR && a->type != SPY_GENERATOR) return spy_error(c, "TypeError", "object is not an iterator");
        SPYValue *value = iterator_next(c, a);
        if (value || c->error_type[0]) return value;
        return argc == 2 ? spy_retain(argv[1]) : spy_error(c, "StopIteration", "");
    }
    if (id == B_ZIP || id == B_ENUMERATE || id == B_REVERSED) {
        if ((id == B_ENUMERATE && (argc < 1 || argc > 2)) || (id == B_REVERSED && argc != 1)) goto arity;
        SPYValue *source;
        if (id == B_ZIP) {
            source = spy_list(c);
            if (!source) return NULL;
            for (size_t i = 0; i < argc; i++) {
                SPYValue *item = get_iterator(c, argv[i]);
                int status = item ? sequence_append(c, source, item) : -1;
                spy_release(item);
                if (status) { spy_release(source); return NULL; }
            }
        } else if (id == B_ENUMERATE) source = get_iterator(c, a);
        else {
            if (a->type != SPY_LIST && a->type != SPY_TUPLE && a->type != SPY_STRING && a->type != SPY_RANGE)
                return spy_error(c, "TypeError", "object is not reversible");
            source = spy_retain(a);
        }
        if (!source) return NULL;
        SPYValue *v = value_new(c, SPY_ITERATOR);
        if (!v) { spy_release(source); return NULL; }
        v->as.iterator.source = source;
        v->as.iterator.kind = id == B_ZIP ? I_ZIP : id == B_ENUMERATE ? I_ENUMERATE : I_REVERSED;
        if (id == B_ENUMERATE && argc == 2 && spy_as_int(c, argv[1], &v->as.iterator.count)) { spy_release(v); return NULL; }
        if (id == B_REVERSED) v->as.iterator.index = a->type == SPY_RANGE ? (size_t)range_length(a) :
            a->type == SPY_STRING ? string_length(a) : a->as.seq.len;
        return v;
    }
    if (id == B_PRINT) {
        Buffer b = { .ctx = c };
        for (size_t i = 0; i < argc; i++) {
            if ((i && puts_buffer(&b, " ")) || format_value(&b, argv[i], 0)) break;
        }
        if (!c->error_type[0] && !puts_buffer(&b, "\n")) {
            if (!c->write) spy_error(c, "OSError", "no output callback installed");
            else if (c->write(c->write_data, b.data, b.len)) spy_error(c, "OSError", "output failed");
        }
        free(b.data);
        return c->error_type[0] ? NULL : spy_none(c);
    }
    if (id == B_RANGE) {
        if (argc < 1 || argc > 3) goto arity;
        int64_t start = 0, stop, step = 1;
        if (spy_as_int(c, argv[argc == 1 ? 0 : 1], &stop)) return NULL;
        if (argc > 1 && spy_as_int(c, argv[0], &start)) return NULL;
        if (argc > 2 && spy_as_int(c, argv[2], &step)) return NULL;
        if (!step) return spy_error(c, "ValueError", "range() step must not be zero");
        SPYValue *v = value_new(c, SPY_RANGE);
        if (v) { v->as.range.start = start; v->as.range.stop = stop; v->as.range.step = step; }
        return v;
    }
    if (id == B_DICT) {
        if (argc > 1) goto arity;
        SPYValue *dict = value_new(c, SPY_DICT);
        if (!dict || !argc) return dict;
        if (a->type == SPY_DICT || (a->type == SPY_INSTANCE && class_lookup(a->as.map.parent, "keys"))) extend_display(c, dict, a);
        else {
            SPYValue *iterator = get_iterator(c, a);
            while (iterator && !c->error_type[0]) {
                if (c->step_limit && ++c->steps > c->step_limit) { spy_error(c, "RuntimeError", "execution step limit exceeded"); break; }
                SPYValue *pair = iterator_next(c, iterator);
                if (!pair) break;
                SPYValue *items = spy_list(c);
                if (items && !extend_display(c, items, pair)) {
                    if (items->as.seq.len != 2) spy_error(c, "ValueError", "dictionary update sequence element must have length 2");
                    else map_set(c, dict, items->as.seq.items[0], items->as.seq.items[1]);
                }
                spy_release(items); spy_release(pair);
            }
            spy_release(iterator);
        }
        if (c->error_type[0]) { spy_release(dict); return NULL; }
        return dict;
    }
    if (id == B_LIST || id == B_TUPLE) {
        if (argc > 1) goto arity;
        SPYValue *v = value_new(c, id == B_LIST ? SPY_LIST : SPY_TUPLE);
        if (!v) return NULL;
        SPYValue *iterator = argc ? get_iterator(c, a) : NULL;
        if (iterator) for (;;) {
            if (c->step_limit && ++c->steps > c->step_limit) { spy_error(c, "RuntimeError", "execution step limit exceeded"); break; }
            SPYValue *item = iterator_next(c, iterator);
            if (!item) break;
            int status = sequence_append(c, v, item); spy_release(item);
            if (status) break;
        }
        spy_release(iterator);
        if (c->error_type[0]) { spy_release(v); return NULL; }
        return v;
    }
    if (id == B_SUM || id == B_ALL || id == B_ANY || id == B_MIN || id == B_MAX) {
        if (!argc || (argc > 1 && id != B_MIN && id != B_MAX && (id != B_SUM || argc != 2))) goto arity;
        SPYValue *result = id == B_SUM ? (argc == 2 ? spy_retain(argv[1]) : spy_int(c, 0)) : NULL;
        int multiple = argc > 1 && (id == B_MIN || id == B_MAX);
        SPYValue *iterator = multiple ? NULL : get_iterator(c, a);
        for (size_t i = 0;; i++) {
            if (c->error_type[0]) break;
            if (c->step_limit && ++c->steps > c->step_limit) { spy_error(c, "RuntimeError", "execution step limit exceeded"); break; }
            SPYValue *item = multiple ? (i < argc ? spy_retain(argv[i]) : NULL) : iterator_next(c, iterator);
            if (!item) break;
            if (id == B_ALL || id == B_ANY) {
                int truth = spy_truth(item); spy_release(item);
                if ((id == B_ALL && !truth) || (id == B_ANY && truth)) { spy_release(iterator); return spy_bool(c, truth); }
            } else if (id == B_SUM) {
                SPYValue *next = result ? binary(c, '+', result, item) : NULL;
                spy_release(result); spy_release(item); result = next;
                if (!result) break;
            } else {
                if (!result) result = spy_retain(item);
                else {
                    SPYValue *cmp = comparison(c, id == B_MIN ? '<' : '>', item, result);
                    if (cmp && spy_truth(cmp)) { spy_release(result); result = spy_retain(item); }
                    spy_release(cmp);
                }
                spy_release(item);
                if (c->error_type[0]) break;
            }
        }
        spy_release(iterator);
        if (c->error_type[0]) { spy_release(result); return NULL; }
        if (id == B_ALL || id == B_ANY) return spy_bool(c, id == B_ALL);
        if (!result) return spy_error(c, "ValueError", "empty sequence");
        return result;
    }
    if (id == B_BOOL) {
        if (argc > 1) goto arity;
        return spy_bool(c, argc && spy_truth(a));
    }
    if (id == B_STR) {
        if (argc > 1) goto arity;
        return argc ? stringify(c, a, 0) : spy_string(c, "", 0);
    }
    if (id == B_INT || id == B_FLOAT) {
        if (argc > 1) goto arity;
        if (!argc) return id == B_INT ? spy_int(c, 0) : spy_float(c, 0);
        if (is_number(a)) {
            if (id == B_FLOAT) return spy_float(c, is_int(a) ? (double)a->as.integer : a->as.real);
            if (is_int(a)) return spy_int(c, a->as.integer);
            if (!isfinite(a->as.real) || a->as.real < -9223372036854775808.0 || a->as.real >= 9223372036854775808.0)
                return spy_error(c, "OverflowError", "float does not fit signed 64-bit integer");
            return spy_int(c, (int64_t)a->as.real);
        }
        if (a->type != SPY_STRING) return spy_error(c, "TypeError", "expected number or string");
        char *end;
        errno = 0;
        double d = 0;
        int64_t i = 0;
        if (id == B_INT) i = strtoll(a->as.string.data, &end, 10);
        else d = strtod(a->as.string.data, &end);
        if (end == a->as.string.data) return spy_error(c, "ValueError", "invalid numeric string");
        while (*end && isspace((unsigned char)*end)) end++;
        if ((size_t)(end - a->as.string.data) != a->as.string.len) return spy_error(c, "ValueError", "invalid numeric string");
        if (id == B_INT && errno == ERANGE) return spy_error(c, "OverflowError", "integer exceeds signed 64-bit limit");
        return id == B_INT ? spy_int(c, i) : spy_float(c, d);
    }
    if (argc != 1) goto arity;
    if (id == B_REPR) return spy_repr(c, a);
    if (id == B_ABS) {
        if (is_int(a)) {
            if (a->as.integer == INT64_MIN) return spy_error(c, "OverflowError", "absolute value overflow");
            return spy_int(c, a->as.integer < 0 ? -a->as.integer : a->as.integer);
        }
        if (a->type == SPY_FLOAT) return spy_float(c, fabs(a->as.real));
        return spy_error(c, "TypeError", "abs() expects a number");
    }
    if (id == B_LEN) {
        uint64_t n;
        if (a->type == SPY_STRING) n = string_length(a);
        else if (a->type == SPY_LIST || a->type == SPY_TUPLE) n = a->as.seq.len;
        else if (a->type == SPY_DICT || a->type == SPY_SET) n = a->as.map.len;
        else if (a->type == SPY_INSTANCE) {
            SPYValue *length = call_special(c, a, "__len__", 0, NULL);
            if (!length) return NULL;
            int64_t value;
            int status = spy_as_int(c, length, &value);
            spy_release(length);
            if (status) return NULL;
            if (value < 0) return spy_error(c, "ValueError", "__len__() should return >= 0");
            return spy_int(c, value);
        }
        else if (a->type == SPY_RANGE) n = range_length(a);
        else return spy_error(c, "TypeError", "object has no len()");
        if (n > INT64_MAX) return spy_error(c, "OverflowError", "length exceeds signed 64-bit limit");
        return spy_int(c, (int64_t)n);
    }
    return spy_error(c, "RuntimeError", "unknown builtin");
arity:
    return spy_error(c, "TypeError", "wrong number of builtin arguments");
}
static SPYValue *builtin_keywords(SPYContext *c, size_t argc, SPYValue *const *argv, int id, SPYValue *keywords) {
    if (keywords && keywords->as.map.len && id != B_DICT) return spy_error(c, "TypeError", "builtin does not accept keyword arguments");
    SPYValue *value = builtin(c, argc, argv, (void *)(intptr_t)id);
    if (value && id == B_DICT && keywords && extend_display(c, value, keywords)) { spy_release(value); return NULL; }
    return value;
}
SPYContext *spy_context_new(void) {
    SPYContext *c = calloc(1, sizeof(*c));
    if (!c) return NULL;
    c->none = value_new(c, SPY_NONE);
    c->booleans[0] = value_new(c, SPY_BOOL);
    c->booleans[1] = value_new(c, SPY_BOOL);
    if (!c->none || !c->booleans[0] || !c->booleans[1]) goto fail;
    c->booleans[1]->as.integer = 1;
    c->builtins = value_new(c, V_ENV);
    c->globals = value_new(c, V_ENV);
    c->modules = value_new(c, SPY_DICT);
    if (!c->builtins || !c->globals || !c->modules) goto fail;
    c->globals->as.map.parent = spy_retain(c->builtins);
    static const char *names[] = {"print", "len", "range", "str", "repr", "int", "float", "bool", "list", "tuple", "dict", "abs", "sum", "min", "max", "all", "any", "iter", "next", "zip", "enumerate", "reversed", "set", "sorted", "ord", "chr", "type", "isinstance", "issubclass", "getattr", "setattr", "hasattr", "callable", "id"};
    for (size_t i = 0; i < sizeof(names) / sizeof(*names); i++) {
        SPYValue *v = value_new(c, SPY_NATIVE);
        if (!v) goto fail;
        v->as.native.call = builtin; v->as.native.data = (void *)(intptr_t)i;
        int status = name_set(c, c->builtins, names[i], v);
        spy_release(v);
        if (status) goto fail;
    }
    static const struct { const char *name, *base; } classes[] = {
        {"object", NULL}, {"BaseException", "object"}, {"Exception", "BaseException"},
        {"SystemExit", "BaseException"}, {"KeyboardInterrupt", "BaseException"}, {"GeneratorExit", "BaseException"},
        {"ArithmeticError", "Exception"}, {"OverflowError", "ArithmeticError"},
        {"ZeroDivisionError", "ArithmeticError"}, {"FloatingPointError", "ArithmeticError"},
        {"AssertionError", "Exception"}, {"AttributeError", "Exception"}, {"BufferError", "Exception"},
        {"EOFError", "Exception"}, {"ImportError", "Exception"}, {"ModuleNotFoundError", "ImportError"},
        {"LookupError", "Exception"}, {"IndexError", "LookupError"}, {"KeyError", "LookupError"},
        {"MemoryError", "Exception"}, {"NameError", "Exception"}, {"UnboundLocalError", "NameError"},
        {"OSError", "Exception"}, {"RuntimeError", "Exception"}, {"NotImplementedError", "RuntimeError"},
        {"RecursionError", "RuntimeError"}, {"StopIteration", "Exception"}, {"StopAsyncIteration", "Exception"},
        {"SyntaxError", "Exception"}, {"IndentationError", "SyntaxError"}, {"TabError", "IndentationError"},
        {"SystemError", "Exception"}, {"TypeError", "Exception"}, {"ValueError", "Exception"},
        {"UnicodeError", "ValueError"}, {"UnicodeDecodeError", "UnicodeError"},
        {"UnicodeEncodeError", "UnicodeError"}, {"UnicodeTranslateError", "UnicodeError"}
    };
    SPYValue *module = spy_string(c, "builtins", 8);
    if (!module) goto fail;
    for (size_t i = 0; i < sizeof(classes) / sizeof(*classes); i++) {
        SPYValue *base = classes[i].base ? name_local(c->builtins, classes[i].base) : NULL;
        SPYValue *cls = new_class(c, classes[i].name, base, module);
        int status = cls ? name_set(c, c->builtins, classes[i].name, cls) : -1;
        spy_release(cls);
        if (status) { spy_release(module); goto fail; }
    }
    static const struct { const char *name; int native; } types[] = {
        {"NoneType", -1}, {"bool", B_BOOL}, {"int", B_INT}, {"float", B_FLOAT}, {"str", B_STR},
        {"list", B_LIST}, {"tuple", B_TUPLE}, {"dict", B_DICT}, {"function", -1}, {"builtin_function_or_method", -1},
        {"module", -1}, {"range", B_RANGE}, {"builtin_function_or_method", -1}, {"iterator", -1},
        {"type", B_TYPE}, {"object", -1}, {"method", -1}, {"set", B_SET}, {"generator", -1}
    };
    for (size_t i = 0; i < sizeof(types) / sizeof(*types); i++) {
        SPYValue *cls = new_class(c, types[i].name, name_local(c->builtins, "object"), module);
        if (!cls) { spy_release(module); goto fail; }
        c->types[i] = cls;
        cls->as.map.native = types[i].native + 1;
        if (types[i].native < 0) cls->as.map.flags = 2;
        if (types[i].native >= 0 && name_set(c, c->builtins, types[i].name, cls)) { spy_release(module); goto fail; }
    }
    spy_release(c->types[SPY_BOOL]->as.map.parent);
    c->types[SPY_BOOL]->as.map.parent = spy_retain(c->types[SPY_INT]);
    spy_release(c->types[SPY_BOUND_METHOD]);
    c->types[SPY_BOUND_METHOD] = spy_retain(c->types[SPY_NATIVE]);
    spy_release(module);
    SPYValue *name = spy_string(c, "__main__", 8);
    if (!name) goto fail;
    int status = name_set(c, c->globals, "__name__", name);
    spy_release(name);
    if (status) goto fail;
    return c;
fail:
    spy_context_free(c); return NULL;
}
void spy_context_free(SPYContext *c) {
    if (!c) return;
    /* Context destruction invalidates every value. Free storage directly so
     * shutdown cannot recurse through an arbitrarily deep object graph. */
    while (c->values) free_value(c->values);
    free(c);
}
void spy_set_output(SPYContext *c, SPYWrite write, void *data) { c->write = write; c->write_data = data; }
void spy_set_module_loader(SPYContext *c, SPYModuleLoader loader, void *data) { c->loader = loader; c->loader_data = data; }
void spy_set_step_limit(SPYContext *c, size_t limit) { c->step_limit = limit; }
SPYValue *spy_eval(SPYContext *c, const char *source, const char *filename) {
    spy_clear_error(c); c->steps = 0;
    SPYValue *unit = parse(c, source, filename ? filename : "<string>");
    if (!unit) return NULL;
    Frame frame = {c->globals, unit};
    Result result = execute(c, &frame, unit->as.unit.body);
    spy_release(unit);
    if (result.flow == FLOW_ERROR) { spy_release(result.value); return NULL; }
    return result.value ? result.value : spy_none(c);
}
int spy_exec(SPYContext *c, const char *source, const char *filename) {
    SPYValue *v = spy_eval(c, source, filename);
    if (!v) return -1;
    spy_release(v);
    return 0;
}
