/* spy-worker: one Small Python context behind the worker protocol of
 * docs/packaging/protocol.md. The parent trusts nothing this program says;
 * this program trusts the parent and exits with status 3 on a bad message.
 * The same file builds the native worker, which speaks over stdin and stdout,
 * and the WebAssembly worker, which speaks through two imported functions.
 *
 * It is compiled twice. With SPY_WORKER_ENGINE defined it is the engine
 * (spy.c and spy-std.c) with its allocator calls renamed to the counting
 * allocator below, which enforces the memory limit; without, it is the
 * worker itself. */
#if defined(__linux__) && !defined(SPY_WORKER_ENGINE)
#define _GNU_SOURCE /* syscall and O_PATH, for the sandbox */
#elif !defined(_WIN32) && !defined(_XOPEN_SOURCE)
#define _XOPEN_SOURCE 700
#endif
#if defined(__APPLE__) && !defined(_DARWIN_C_SOURCE)
#define _DARWIN_C_SOURCE
#endif
#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#if defined(__unix__) || defined(__APPLE__)
#include <fcntl.h>
#include <signal.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <unistd.h>
#elif defined(_WIN32)
#include <fcntl.h>
#include <io.h>
#include <limits.h>
#endif

void *spy_worker_malloc(size_t);
void *spy_worker_calloc(size_t, size_t);
void *spy_worker_realloc(void *, size_t);
void spy_worker_free(void *);
char *spy_worker_realpath(const char *, char *);

#ifdef SPY_WORKER_ENGINE
/* The engine's own headers, included first so the renaming below reaches
 * only its code. */
#include <complex.h>
#include <ctype.h>
#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdarg.h>
#define malloc spy_worker_malloc
#define calloc spy_worker_calloc
#define realloc spy_worker_realloc
#define free spy_worker_free
#define realpath spy_worker_realpath
#include "spy.c"
#include "spy-std.c"
#else
#include "spy.h"
#include "spy-std.h"

/* The memory limit counts what the engine allocates: every block carries its
 * size. The protocol's own buffers are not counted. */
static size_t memory_used, memory_limit;
typedef union { size_t size; max_align_t align; } Block;

void *spy_worker_malloc(size_t n) {
    if (n > SIZE_MAX - sizeof(Block) || (memory_limit && n > memory_limit - memory_used)) return NULL;
    Block *b = malloc(sizeof(Block) + n);
    if (!b) return NULL;
    b->size = n; memory_used += n;
    return b + 1;
}
void spy_worker_free(void *p) {
    if (!p) return;
    Block *b = (Block *)p - 1;
    memory_used -= b->size;
    free(b);
}
void *spy_worker_calloc(size_t count, size_t size) {
    if (size && count > SIZE_MAX / size) return NULL;
    void *p = spy_worker_malloc(count * size);
    if (p) memset(p, 0, count * size);
    return p;
}
void *spy_worker_realloc(void *p, size_t n) {
    if (!p) return spy_worker_malloc(n);
    Block *b = (Block *)p - 1;
    size_t old = b->size;
    if (n > SIZE_MAX - sizeof(Block) || (memory_limit && n > old && n - old > memory_limit - memory_used)) return NULL;
    Block *grown = realloc(b, sizeof(Block) + n);
    if (!grown) return NULL;
    grown->size = n; memory_used = memory_used - old + n;
    return grown + 1;
}
/* The engine frees what realpath returns, so it must come from the counter. */
char *spy_worker_realpath(const char *path, char *resolved) {
#if defined(__unix__) || defined(__APPLE__)
    char *real = realpath(path, resolved);
    if (!real || resolved) return real;
    size_t n = strlen(real) + 1;
    char *copy = spy_worker_malloc(n);
    if (copy) memcpy(copy, real, n);
    else errno = ENOMEM;
    free(real);
    return copy;
#else
    (void)path; (void)resolved;
    errno = ENOSYS;
    return NULL;
#endif
}

/* Streams: read_bytes fills the buffer or reports the end of input; the
 * protocol never needs a partial read. */
#ifdef __wasm__
__attribute__((import_module("spy"), import_name("read"))) size_t spy_host_read(void *, size_t);
__attribute__((import_module("spy"), import_name("write"))) void spy_host_write(const void *, size_t);
static int read_bytes(void *p, size_t n) {
    for (size_t got; n; p = (char *)p + got, n -= got)
        if (!(got = spy_host_read(p, n))) return -1;
    return 0;
}
static void write_bytes(const void *p, size_t n) { spy_host_write(p, n); }
#else
#ifdef _WIN32 /* The C runtime's names for these calls take an unsigned count. */
#define read(fd, p, n) _read(fd, p, (unsigned)((n) < INT_MAX ? (n) : INT_MAX))
#define write(fd, p, n) _write(fd, p, (unsigned)((n) < INT_MAX ? (n) : INT_MAX))
#endif
static int in_fd = 0, out_fd = 1;
static int read_bytes(void *p, size_t n) {
    while (n) {
        ssize_t got = read(in_fd, p, n);
        if (got < 0 && errno == EINTR) continue;
        if (got <= 0) return -1;
        p = (char *)p + got; n -= (size_t)got;
    }
    return 0;
}
static void write_bytes(const void *p, size_t n) {
    while (n) {
        ssize_t put = write(out_fd, p, n);
        if (put < 0 && errno == EINTR) continue;
        if (put <= 0) exit(0); /* The parent is gone. */
        p = (const char *)p + put; n -= (size_t)put;
    }
}
#endif

enum {
    INIT = 0x01, EVAL, EXEC, CALL, GET, SET, DELETE, MODULE, MOUNT, COLLECT, OP, RELEASE,
    HOST = 0x21, LOAD, OUTPUT,
    RESULT = 0x40, RAISE
};
enum { MAX_DEPTH = 200 };

static _Noreturn void violation(void) { exit(3); }

/* Outgoing messages are built in one buffer; the four length bytes come first. */
typedef struct { unsigned char *data; size_t len, cap; } Buffer;
static size_t message_limit = 64 << 20;

static void put(Buffer *b, const void *p, size_t n) {
    if (n > b->cap - b->len) {
        size_t cap = b->cap ? b->cap : 256;
        while (cap - b->len < n) {
            if (cap > SIZE_MAX / 2) exit(1);
            cap *= 2;
        }
        unsigned char *grown = realloc(b->data, cap);
        if (!grown) exit(1);
        b->data = grown; b->cap = cap;
    }
    memcpy(b->data + b->len, p, n);
    b->len += n;
}
static void put_byte(Buffer *b, int byte) { unsigned char c = (unsigned char)byte; put(b, &c, 1); }
static void put_u32(Buffer *b, uint32_t n) {
    unsigned char s[4] = {(unsigned char)n, (unsigned char)(n >> 8), (unsigned char)(n >> 16), (unsigned char)(n >> 24)};
    put(b, s, 4);
}
static void put_u64(Buffer *b, uint64_t n) {
    unsigned char s[8];
    for (int i = 0; i < 8; i++) s[i] = (unsigned char)(n >> (8 * i));
    put(b, s, 8);
}
static void put_double(Buffer *b, double d) {
    uint64_t n;
    memcpy(&n, &d, 8);
    put_u64(b, n);
}
static void put_text(Buffer *b, int tag, const char *s, size_t n) {
    put_byte(b, tag);
    put_u32(b, (uint32_t)n);
    put(b, s, n);
}
static void put_str(Buffer *b, const char *s) { put_text(b, 's', s, strlen(s)); }
/* Engine C strings (error details) live in fixed buffers that may cut a
 * character short; send the bytes up to the first sequence that is not UTF-8
 * (lone surrogates included, as the protocol allows). */
static void put_c_text(Buffer *b, const char *text) {
    const unsigned char *s = (const unsigned char *)text;
    size_t n = 0;
    while (s[n]) {
        unsigned char c = s[n];
        size_t len = c < 0x80 ? 1 : c >= 0xC2 && c < 0xE0 ? 2 : c >= 0xE0 && c < 0xF0 ? 3 : c >= 0xF0 && c < 0xF5 ? 4 : 0;
        int valid = len != 0;
        for (size_t i = 1; valid && i < len; i++) valid = (s[n + i] & 0xC0) == 0x80;
        if (valid && len == 3) valid = c != 0xE0 || s[n + 1] >= 0xA0;
        if (valid && len == 4) valid = (c != 0xF0 || s[n + 1] >= 0x90) && (c != 0xF4 || s[n + 1] < 0x90);
        if (!valid) break;
        n += len;
    }
    put_text(b, 's', text, n);
}
static void put_int(Buffer *b, int64_t n) { put_byte(b, 'i'); put_u64(b, (uint64_t)n); }
static void begin(Buffer *b, int kind) { b->len = 0; put_u32(b, 0); put_byte(b, kind); }
static int over_limit(const Buffer *b) { return b->len - 4 > message_limit || b->len - 4 > UINT32_MAX; }
static void send_message(Buffer *b) {
    uint32_t n = (uint32_t)(b->len - 4);
    unsigned char s[4] = {(unsigned char)n, (unsigned char)(n >> 8), (unsigned char)(n >> 16), (unsigned char)(n >> 24)};
    memcpy(b->data, s, 4);
    write_bytes(b->data, b->len);
}

/* Incoming messages are read whole and decoded through a cursor. */
typedef struct { const unsigned char *at, *end; } Cursor;

static unsigned char *read_message(size_t *len) {
    unsigned char s[4];
    if (read_bytes(s, 4)) exit(0);
    size_t n = (size_t)s[0] | (size_t)s[1] << 8 | (size_t)s[2] << 16 | (size_t)s[3] << 24;
    if (!n || n > message_limit) violation();
    unsigned char *data = malloc(n);
    if (!data) exit(1);
    if (read_bytes(data, n)) exit(0);
    *len = n;
    return data;
}
static const unsigned char *take(Cursor *k, size_t n) {
    if ((size_t)(k->end - k->at) < n) violation();
    const unsigned char *p = k->at;
    k->at += n;
    return p;
}
static uint32_t take_u32(Cursor *k) {
    const unsigned char *s = take(k, 4);
    return (uint32_t)s[0] | (uint32_t)s[1] << 8 | (uint32_t)s[2] << 16 | (uint32_t)s[3] << 24;
}
static uint64_t take_u64(Cursor *k) {
    const unsigned char *s = take(k, 8);
    uint64_t n = 0;
    for (int i = 7; i >= 0; i--) n = n << 8 | s[i];
    return n;
}

/* The worker's state: one context, the builtins it relies on, the handles the
 * parent holds, the natives standing for parent functions, registered
 * modules, and the parent failure most recently raised in the engine. */
enum {
    H_INT, H_HEX, H_COMPLEX, H_BYTES, H_BYTEARRAY, H_SET, H_FROZENSET, H_BOOL, H_LEN, H_HASH, H_DIR, H_NEXT, H_ISSUBCLASS,
    H_BUILTINS, H_GLOBALS, H_LT, H_LE, H_EQ, H_NE, H_GT, H_GE, H_CONTAINS, H_COUNT
};
static const char HELPERS[] =
    "(int, hex, complex, bytes, bytearray, set, frozenset, bool, len, hash, dir, next, issubclass,"
    " dict(__import__('builtins').__dict__), globals(),"
    " lambda a, b: a < b, lambda a, b: a <= b, lambda a, b: a == b, lambda a, b: a != b,"
    " lambda a, b: a > b, lambda a, b: a >= b, lambda a, b: a in b)";

typedef struct { uint64_t id; SPYValue *value; } Entry;
static struct {
    SPYContext *c;
    SPYValue *helper[H_COUNT];
    Entry *handles; size_t handles_len, handles_cap, handles_live; uint64_t next_handle;
    Entry *functions; size_t functions_len, functions_cap;
    SPYValue *modules;
    SPYValue *failure; int64_t failure_token;
} w;

static SPYValue *helper_call(int which, size_t argc, SPYValue *const *argv) {
    return spy_call(w.c, w.helper[which], argc, argv);
}

/* Handle ids increase, so the table stays sorted; released entries are
 * compacted away once they are half of it. */
static uint64_t handle_new(SPYValue *value) {
    if (w.handles_len == w.handles_cap) {
        size_t cap = w.handles_cap ? w.handles_cap * 2 : 64;
        Entry *grown = realloc(w.handles, cap * sizeof(*grown));
        if (!grown) exit(1);
        w.handles = grown; w.handles_cap = cap;
    }
    w.handles[w.handles_len++] = (Entry){++w.next_handle, spy_retain(value)};
    w.handles_live++;
    return w.next_handle;
}
static Entry *handle_find(uint64_t id) {
    size_t lo = 0, hi = w.handles_len;
    while (lo < hi) {
        size_t mid = lo + (hi - lo) / 2;
        if (w.handles[mid].id < id) lo = mid + 1; else hi = mid;
    }
    if (lo == w.handles_len || w.handles[lo].id != id || !w.handles[lo].value) violation();
    return &w.handles[lo];
}
static void handle_release(uint64_t id) {
    Entry *e = handle_find(id);
    SPYValue *value = e->value;
    e->value = NULL;
    w.handles_live--;
    if (w.handles_live * 2 < w.handles_len) {
        size_t n = 0;
        for (size_t i = 0; i < w.handles_len; i++) if (w.handles[i].value) w.handles[n++] = w.handles[i];
        w.handles_len = n;
    }
    spy_release(value);
}

/* Engine to parent. Only exact plain types go by content (spy_type reports
 * subclass instances as SPY_INSTANCE); anything else goes as a handle.
 * Returns -1 with an engine error set. */
static int encode(Buffer *b, SPYValue *v, int depth) {
    SPYContext *c = w.c;
    SPYType type = spy_type(v);
    if (depth > MAX_DEPTH) { spy_error(c, "RecursionError", "value is too deeply nested to convert"); return -1; }
    switch (type) {
    case SPY_NONE: put_byte(b, 'N'); return 0;
    case SPY_BOOL: put_byte(b, spy_truth(v) ? 'T' : 'F'); return 0;
    case SPY_INT: {
        int64_t n;
        if (!spy_as_int(c, v, &n)) { put_int(b, n); return 0; }
        spy_clear_error(c);
        SPYValue *text = helper_call(H_HEX, 1, &v);
        size_t len;
        const char *s = text ? spy_as_string(c, text, &len) : NULL;
        if (s) put_text(b, 'I', s, len);
        spy_release(text);
        return s ? 0 : -1;
    }
    case SPY_FLOAT: {
        double d;
        if (spy_as_float(c, v, &d)) return -1;
        put_byte(b, 'f'); put_double(b, d);
        return 0;
    }
    case SPY_COMPLEX: {
        SPYValue *re = spy_get_attr(c, v, "real"), *im = re ? spy_get_attr(c, v, "imag") : NULL;
        double x, y;
        int failed = !im || spy_as_float(c, re, &x) || spy_as_float(c, im, &y);
        spy_release(re); spy_release(im);
        if (failed) return -1;
        put_byte(b, 'c'); put_double(b, x); put_double(b, y);
        return 0;
    }
    case SPY_STRING: {
        size_t len;
        const char *s = spy_as_string(c, v, &len);
        if (!s) return -1;
        put_text(b, 's', s, len);
        return 0;
    }
    case SPY_BYTES: case SPY_BYTEARRAY: {
        size_t len;
        SPYValue *bytes = type == SPY_BYTES ? spy_retain(v) : helper_call(H_BYTES, 1, &v);
        const unsigned char *s = bytes ? spy_as_bytes(c, bytes, &len) : NULL;
        if (s) put_text(b, type == SPY_BYTES ? 'b' : 'B', (const char *)s, len);
        spy_release(bytes);
        return s ? 0 : -1;
    }
    case SPY_LIST: case SPY_TUPLE: case SPY_SET: case SPY_FROZENSET: case SPY_DICT: {
        static const char tags[] = {[SPY_LIST] = 'l', [SPY_TUPLE] = 't', [SPY_SET] = 'S', [SPY_FROZENSET] = 'z', [SPY_DICT] = 'd'};
        put_byte(b, tags[type]);
        size_t at = b->len;
        put_u32(b, 0);
        /* A dict's items are pairs: the key, then the value. */
        SPYValue *items = type == SPY_DICT ? spy_get_attr(c, v, "items") : spy_retain(v);
        SPYValue *pairs = items && type == SPY_DICT ? spy_call(c, items, 0, NULL) : spy_retain(items);
        SPYValue *iterator = pairs ? spy_iter(c, pairs) : NULL, *item;
        spy_release(items); spy_release(pairs);
        if (!iterator) return -1;
        uint32_t count = 0;
        int failed = 0;
        while (!failed && (item = spy_next(c, iterator))) {
            if (type == SPY_DICT)
                for (int64_t i = 0; i < 2 && !failed; i++) {
                    SPYValue *index = spy_int(c, i), *part = index ? spy_get_item(c, item, index) : NULL;
                    failed = !part || encode(b, part, depth + 1);
                    spy_release(index); spy_release(part);
                }
            else failed = encode(b, item, depth + 1);
            spy_release(item);
            if (!failed && (++count == UINT32_MAX || over_limit(b))) {
                spy_error(c, "OverflowError", "message exceeds the limit");
                failed = 1;
            }
        }
        spy_release(iterator);
        if (failed || spy_error_type(c)[0]) return -1;
        memcpy(b->data + at, (unsigned char[4]){(unsigned char)count, (unsigned char)(count >> 8),
                                                 (unsigned char)(count >> 16), (unsigned char)(count >> 24)}, 4);
        return 0;
    }
    default:
        put_byte(b, 'h'); put_u64(b, handle_new(v));
        return 0;
    }
}

/* A native function for each parent function id, made on first sight. */
static SPYValue *host_call(SPYContext *, size_t, SPYValue *const *, SPYValue *, void *);
static SPYValue *function_value(uint64_t id, SPYValue *name) {
    for (size_t i = 0; i < w.functions_len; i++)
        if (w.functions[i].id == id) return spy_retain(w.functions[i].value);
    const char *text = spy_as_string(w.c, name, NULL);
    SPYValue *fn = text ? spy_native(w.c, text, host_call, (void *)(uintptr_t)id, NULL) : NULL;
    if (!fn) return NULL;
    if (w.functions_len == w.functions_cap) {
        size_t cap = w.functions_cap ? w.functions_cap * 2 : 16;
        Entry *grown = realloc(w.functions, cap * sizeof(*grown));
        if (!grown) exit(1);
        w.functions = grown; w.functions_cap = cap;
    }
    w.functions[w.functions_len++] = (Entry){id, spy_retain(fn)};
    return fn;
}

/* Parent to engine. A malformed value ends the worker; a value the engine
 * cannot build (an unhashable key, memory) returns NULL with an error set,
 * after consuming the rest of the value so the message stays in step. */
static SPYValue *decode(Cursor *k, int depth) {
    SPYContext *c = w.c;
    if (depth > MAX_DEPTH) violation();
    int tag = *take(k, 1);
    switch (tag) {
    case 'N': return spy_none(c);
    case 'F': case 'T': return spy_bool(c, tag == 'T');
    case 'i': return spy_int(c, (int64_t)take_u64(k));
    case 'I': {
        uint32_t n = take_u32(k);
        const char *s = (const char *)take(k, n);
        SPYValue *args[2] = {spy_string(c, s, n), spy_int(c, 16)};
        SPYValue *v = args[0] && args[1] ? helper_call(H_INT, 2, args) : NULL;
        spy_release(args[0]); spy_release(args[1]);
        return v;
    }
    case 'f': case 'c': {
        double x, y = 0;
        uint64_t n = take_u64(k);
        memcpy(&x, &n, 8);
        if (tag == 'f') return spy_float(c, x);
        n = take_u64(k);
        memcpy(&y, &n, 8);
        SPYValue *args[2] = {spy_float(c, x), spy_float(c, y)};
        SPYValue *v = args[0] && args[1] ? helper_call(H_COMPLEX, 2, args) : NULL;
        spy_release(args[0]); spy_release(args[1]);
        return v;
    }
    case 's': case 'b': case 'B': {
        uint32_t n = take_u32(k);
        const char *s = (const char *)take(k, n);
        if (tag == 's') return spy_string(c, s, n);
        SPYValue *v = spy_bytes(c, s, n);
        if (tag == 'b' || !v) return v;
        SPYValue *array = helper_call(H_BYTEARRAY, 1, &v);
        spy_release(v);
        return array;
    }
    case 'l': case 't': case 'S': case 'z': {
        uint32_t n = take_u32(k);
        if (n > (size_t)(k->end - k->at)) violation();
        SPYValue *list = spy_list(c);
        for (uint32_t i = 0; i < n; i++) {
            SPYValue *item = decode(k, depth + 1);
            if (list && (!item || spy_list_append(c, list, item))) { spy_release(list); list = NULL; }
            spy_release(item);
        }
        if (!list || tag == 'l') return list;
        SPYValue *v;
        if (tag == 't') {
            SPYValue **items = n ? malloc(n * sizeof(*items)) : NULL;
            if (n && !items) exit(1);
            for (uint32_t i = 0; i < n; i++) {
                SPYValue *index = spy_int(c, i);
                items[i] = index ? spy_get_item(c, list, index) : NULL;
                spy_release(index);
            }
            v = spy_tuple(c, n, items);
            for (uint32_t i = 0; i < n; i++) spy_release(items[i]);
            free(items);
        } else v = helper_call(tag == 'S' ? H_SET : H_FROZENSET, 1, &list);
        spy_release(list);
        return v;
    }
    case 'd': {
        uint32_t n = take_u32(k);
        if (n > (size_t)(k->end - k->at) / 2) violation();
        SPYValue *dict = spy_dict(c);
        for (uint32_t i = 0; i < n; i++) {
            SPYValue *key = decode(k, depth + 1), *value = decode(k, depth + 1);
            if (dict && (!key || !value || spy_set_item(c, dict, key, value))) { spy_release(dict); dict = NULL; }
            spy_release(key); spy_release(value);
        }
        return dict;
    }
    case 'h': return spy_retain(handle_find(take_u64(k))->value);
    case 'p': {
        uint64_t id = take_u64(k);
        SPYValue *name = decode(k, depth + 1);
        if (name && spy_type(name) != SPY_STRING) violation();
        SPYValue *fn = name ? function_value(id, name) : NULL;
        spy_release(name);
        return fn;
    }
    default: violation();
    }
}
static SPYValue *decode_type(Cursor *k, SPYType type) {
    SPYValue *v = decode(k, 0);
    if (v && spy_type(v) != type) violation();
    return v;
}
static void finish(Cursor *k) { if (k->at != k->end) violation(); }

/* Replies and requests each build their own message: engine code may run
 * while one is built, and that code may need to send another. */
static void send_raise(void) {
    SPYContext *c = w.c;
    SPYValue *exception = spy_error_value(c);
    int64_t token = exception && exception == w.failure ? w.failure_token : 0;
    Buffer b = {0};
    begin(&b, RAISE);
    put_byte(&b, 'd'); put_u32(&b, 6);
    put_str(&b, "type"); put_c_text(&b, spy_error_type(c));
    put_str(&b, "message"); put_c_text(&b, spy_error_display(c));
    put_str(&b, "filename"); put_c_text(&b, spy_error_filename(c));
    put_str(&b, "line"); put_int(&b, (int64_t)spy_error_line(c));
    put_str(&b, "exception");
    if (exception) { put_byte(&b, 'h'); put_u64(&b, handle_new(exception)); }
    else put_byte(&b, 'N');
    put_str(&b, "token"); put_int(&b, token);
    spy_release(exception);
    spy_clear_error(c);
    spy_release(w.failure); w.failure = NULL;
    send_message(&b);
    free(b.data);
}
static void send_result(SPYValue *v) {
    if (!v) { send_raise(); return; }
    Buffer b = {0};
    begin(&b, RESULT);
    int failed = encode(&b, v, 0);
    if (!failed && over_limit(&b)) { spy_error(w.c, "OverflowError", "message exceeds the limit"); failed = 1; }
    spy_release(v);
    if (failed) send_raise();
    else send_message(&b);
    free(b.data);
}
static void send_status(int status) { send_result(status ? NULL : spy_none(w.c)); }

static SPYValue *field(SPYValue *dict, const char *name) {
    SPYValue *key = spy_string(w.c, name, strlen(name));
    SPYValue *v = key ? spy_get_item(w.c, dict, key) : NULL;
    spy_release(key);
    return v;
}
static int64_t int_field(SPYValue *dict, const char *name) {
    SPYValue *v = field(dict, name);
    int64_t n;
    if (!v || spy_type(v) != SPY_INT || spy_as_int(w.c, v, &n)) violation();
    spy_release(v);
    return n;
}
static SPYValue *builtin(const char *name) { return field(w.helper[H_BUILTINS], name); }

/* Call fn with the items of a tuple, and keywords from a dict or NULL. */
static SPYValue *call_tuple(SPYValue *fn, SPYValue *args, SPYValue *kwargs) {
    SPYContext *c = w.c;
    SPYValue *iterator = spy_iter(c, args), *item, **argv = NULL, *result = NULL;
    size_t argc = 0, cap = 0;
    while (iterator && (item = spy_next(c, iterator))) {
        if (argc == cap) {
            cap = cap ? cap * 2 : 8;
            SPYValue **grown = realloc(argv, cap * sizeof(*grown));
            if (!grown) exit(1);
            argv = grown;
        }
        argv[argc++] = item;
    }
    if (iterator && !spy_error_type(c)[0]) result = spy_call_keywords(c, fn, argc, argv, kwargs);
    spy_release(iterator);
    for (size_t i = 0; i < argc; i++) spy_release(argv[i]);
    free(argv);
    return result;
}

/* Raise the parent's failure in the engine: an engine exception unchanged,
 * or the first builtin exception class among the parent's class names,
 * remembering the failure's token so an escaping exception can name it. */
static void raise_failure(SPYValue *failure) {
    SPYContext *c = w.c;
    int64_t token = int_field(failure, "token");
    SPYValue *exception = field(failure, "raise");
    if (!exception) {
        spy_clear_error(c);
        SPYValue *classes = field(failure, "classes"), *args = field(failure, "args"), *message = field(failure, "message");
        if (!classes || !args || !message || spy_type(classes) != SPY_TUPLE || spy_type(message) != SPY_STRING ||
            (spy_type(args) != SPY_TUPLE && spy_type(args) != SPY_NONE)) violation();
        SPYValue *base = builtin("BaseException"), *iterator = spy_iter(c, classes), *name, *cls = NULL;
        while (base && iterator && !cls && (name = spy_next(c, iterator))) {
            SPYValue *found = spy_get_item(c, w.helper[H_BUILTINS], name), *pair[2] = {found, base};
            SPYValue *is = found && spy_type(found) == SPY_CLASS ? helper_call(H_ISSUBCLASS, 2, pair) : NULL;
            if (is && spy_truth(is)) cls = spy_retain(found);
            spy_release(is); spy_release(found); spy_release(name);
            spy_clear_error(c);
        }
        spy_release(iterator); spy_release(base);
        if (!cls) cls = builtin("RuntimeError");
        if (cls) exception = spy_type(args) == SPY_TUPLE ? call_tuple(cls, args, NULL) : spy_call(c, cls, 1, &message);
        if (!exception && cls) { spy_clear_error(c); exception = spy_call(c, cls, 1, &message); }
        spy_release(cls); spy_release(classes); spy_release(args); spy_release(message);
        if (!exception) return;
    }
    spy_raise(c, exception);
    spy_release(w.failure);
    w.failure = exception;
    w.failure_token = token;
}

static void serve(unsigned char *message, size_t len);

/* Send a request to the parent and wait for its reply, serving the parent's
 * nested requests meanwhile. Returns the reply's value (owned), or NULL with
 * the parent's failure raised in the engine. */
static SPYValue *request(Buffer *b) {
    if (over_limit(b)) { free(b->data); return spy_error(w.c, "OverflowError", "message exceeds the limit"); }
    send_message(b);
    free(b->data);
    for (;;) {
        size_t len;
        unsigned char *message = read_message(&len);
        int kind = message[0];
        if (kind != RESULT && kind != RAISE) { serve(message, len); continue; }
        Cursor k = {message + 1, message + len};
        SPYValue *v = decode(&k, 0);
        finish(&k);
        free(message);
        if (kind == RESULT || !v) return v;
        if (spy_type(v) != SPY_DICT) violation();
        raise_failure(v);
        spy_release(v);
        return NULL;
    }
}

/* Parent functions, output, and the module loader are requests. */
static SPYValue *host_call(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kwargs, void *data) {
    Buffer b = {0};
    begin(&b, HOST);
    put_int(&b, (int64_t)(uintptr_t)data);
    put_byte(&b, 't'); put_u32(&b, (uint32_t)argc);
    for (size_t i = 0; i < argc; i++)
        if (encode(&b, argv[i], 1)) { free(b.data); return NULL; }
    if (kwargs ? encode(&b, kwargs, 0) : (put_byte(&b, 'd'), put_u32(&b, 0), 0)) { free(b.data); return NULL; }
    (void)c;
    return request(&b);
}
/* A failed write is the engine's own OSError; the parent reports why. */
static int output(void *data, const char *s, size_t n) {
    (void)data;
    Buffer b = {0};
    begin(&b, OUTPUT);
    put_text(&b, 's', s, n);
    SPYValue *v = request(&b);
    if (!v) spy_clear_error(w.c);
    spy_release(v);
    return v ? 0 : -1;
}
static char *load(void *data, const char *name) {
    (void)data;
    Buffer b = {0};
    begin(&b, LOAD);
    put_str(&b, name);
    SPYValue *v = request(&b);
    if (!v || spy_type(v) == SPY_NONE) { spy_release(v); return NULL; }
    size_t n;
    const char *s = spy_type(v) == SPY_STRING ? spy_as_string(w.c, v, &n) : NULL;
    if (!s) violation();
    char *copy = spy_worker_malloc(n + 1);
    if (copy) memcpy(copy, s, n + 1);
    else spy_error(w.c, "MemoryError", "out of memory");
    spy_release(v);
    return copy;
}

/* A registered module: its members, then its source with filename <name>. */
static int module_init(SPYContext *c, SPYValue *module) {
    SPYValue *name = spy_get_attr(c, module, "__name__");
    SPYValue *spec = name ? spy_get_item(c, w.modules, name) : NULL;
    SPYValue *zero = spy_int(c, 0), *one = spy_int(c, 1);
    SPYValue *members = spec ? spy_get_item(c, spec, zero) : NULL, *source = spec ? spy_get_item(c, spec, one) : NULL;
    int status = members && source ? 0 : -1;
    if (!status && spy_type(members) == SPY_DICT) {
        SPYValue *items = spy_get_attr(c, members, "items"), *pairs = items ? spy_call(c, items, 0, NULL) : NULL;
        SPYValue *iterator = pairs ? spy_iter(c, pairs) : NULL, *pair;
        status = iterator ? 0 : -1;
        while (!status && (pair = spy_next(c, iterator))) {
            SPYValue *key = spy_get_item(c, pair, zero), *value = key ? spy_get_item(c, pair, one) : NULL;
            const char *attr = value && spy_type(key) == SPY_STRING ? spy_as_string(c, key, NULL) : NULL;
            status = attr ? spy_set_attr(c, module, attr, value) : -1;
            spy_release(key); spy_release(value); spy_release(pair);
        }
        if (spy_error_type(c)[0]) status = -1;
        spy_release(iterator); spy_release(pairs); spy_release(items);
    }
    if (!status && spy_type(source) == SPY_STRING) {
        const char *text = spy_as_string(c, source, NULL), *module_name = spy_as_string(c, name, NULL);
        size_t n = strlen(module_name) + 3;
        char *filename = malloc(n);
        if (!filename) exit(1);
        snprintf(filename, n, "<%s>", module_name);
        status = spy_exec_module(c, module, text, filename);
        free(filename);
    }
    spy_release(name); spy_release(spec); spy_release(zero); spy_release(one);
    spy_release(members); spy_release(source);
    return status;
}

static SPYValue *source_text(SPYValue *source, const char **text) {
    *text = spy_as_string(w.c, source, NULL);
    size_t n;
    spy_as_string(w.c, source, &n);
    if (strlen(*text) != n) return spy_error(w.c, "SyntaxError", "source code string cannot contain null bytes");
    return source;
}

/* Object operations (protocol.md 7.3). */
static SPYValue *operate(Cursor *k) {
    SPYContext *c = w.c;
    SPYValue *op = decode_type(k, SPY_INT), *t = decode(k, 0), *result = NULL;
    int64_t which;
    if (!op || !t || spy_as_int(c, op, &which)) violation();
    if (spy_type(t) == SPY_STRING) violation();
    SPYValue *a = which == 1 || which == 2 || which == 3 || which == 4 || which == 6 || (which >= 11 && which <= 16) ? decode(k, 0) : NULL;
    SPYValue *b = which == 2 || which == 4 ? decode(k, 0) : NULL;
    finish(k);
    SPYValue *pair[2] = {t, a}, *flipped[2] = {a, t};
    static const int compare[] = {H_LT, H_LE, H_EQ, H_NE, H_GT, H_GE};
    if ((which == 1 || which == 2) && (!a || spy_type(a) != SPY_STRING)) violation();
    switch (which) {
    case 1: result = spy_get_attr(c, t, spy_as_string(c, a, NULL)); break;
    case 2: result = spy_set_attr(c, t, spy_as_string(c, a, NULL), b) ? NULL : spy_none(c); break;
    case 3: result = spy_get_item(c, t, a); break;
    case 4: result = spy_set_item(c, t, a, b) ? NULL : spy_none(c); break;
    case 5: result = helper_call(H_LEN, 1, &t); break;
    case 6: result = helper_call(H_CONTAINS, 2, flipped); break;
    case 7: result = spy_iter(c, t); break;
    case 8: result = helper_call(H_NEXT, 1, &t); break;
    case 9: result = helper_call(H_BOOL, 1, &t); break;
    case 10: result = helper_call(H_HASH, 1, &t); break;
    case 11: case 12: case 13: case 14: case 15: case 16: result = helper_call(compare[which - 11], 2, pair); break;
    case 17: result = spy_repr(c, t); break;
    case 18: result = spy_str(c, t); break;
    case 19: result = helper_call(H_DIR, 1, &t); break;
    default: violation();
    }
    spy_release(op); spy_release(t); spy_release(a); spy_release(b);
    return result;
}

static int initialized;

/* The worker seals itself under the operating system's sandbox before it
 * first runs engine code; the mounts are fixed from then on. */
static struct Mount { char *directory; int read_only; } *mounts;
static size_t mounts_len;
static int sealed;
static void seal(void);

static void initialize(Cursor *k) {
    SPYContext *c = w.c;
    SPYValue *options = decode_type(k, SPY_DICT);
    finish(k);
    if (!options || initialized) violation();
    SPYValue *std = field(options, "std"), *n = spy_int(c, 0), *count = helper_call(H_LEN, 1, &options);
    int64_t steps = int_field(options, "step_limit"), memory = int_field(options, "memory_limit");
    int64_t limit = int_field(options, "message_limit"), keys;
    if (!std || spy_type(std) != SPY_BOOL || !count || spy_as_int(c, count, &keys) || keys != 4 ||
        steps < 0 || memory < 0 || limit < 1 || (uint64_t)limit > UINT32_MAX) violation();
    initialized = 1;
    memory_limit = (size_t)memory;
    message_limit = (size_t)limit;
    spy_set_step_limit(c, (size_t)steps);
    int failed = spy_truth(std) && spy_std_init(c);
    spy_release(std); spy_release(n); spy_release(count); spy_release(options);
    send_result(failed ? NULL : spy_string(c, SPY_VERSION, strlen(SPY_VERSION)));
}

/* Serve one request from the parent, replying to it, or one notice. */
static void serve(unsigned char *message, size_t len) {
    SPYContext *c = w.c;
    Cursor k = {message + 1, message + len};
    int kind = message[0];
    spy_clear_error(c);
    if (kind != INIT && !initialized) violation();
    if (!sealed && (kind == EVAL || kind == EXEC || kind == CALL || kind == OP)) {
        seal();
        sealed = 1;
    }
    switch (kind) {
    case INIT: initialize(&k); break;
    case EVAL: case EXEC: {
        SPYValue *source = decode_type(&k, SPY_STRING), *filename = decode_type(&k, SPY_STRING);
        finish(&k);
        const char *text, *file = filename ? spy_as_string(c, filename, NULL) : NULL;
        if (!source || !file || !source_text(source, &text)) send_result(NULL);
        else if (kind == EVAL) send_result(spy_eval(c, text, file));
        else send_status(spy_exec(c, text, file));
        spy_release(source); spy_release(filename);
        break;
    }
    case CALL: {
        SPYValue *target = decode(&k, 0), *args = decode_type(&k, SPY_TUPLE), *kwargs = decode_type(&k, SPY_DICT), *fn = target;
        finish(&k);
        if (target && spy_type(target) == SPY_STRING) fn = spy_get_global(c, spy_as_string(c, target, NULL));
        else spy_retain(fn);
        send_result(fn && args && kwargs ? call_tuple(fn, args, kwargs) : NULL);
        spy_release(fn); spy_release(target); spy_release(args); spy_release(kwargs);
        break;
    }
    case GET: case SET: case DELETE: {
        SPYValue *name = decode_type(&k, SPY_STRING), *value = kind == SET ? decode(&k, 0) : NULL;
        finish(&k);
        const char *text = name ? spy_as_string(c, name, NULL) : NULL;
        if (kind == GET) send_result(text ? spy_get_global(c, text) : NULL);
        else if (kind == SET) send_status(!text || !value || spy_set_global(c, text, value));
        else {
            SPYValue *pop = text ? spy_get_attr(c, w.helper[H_GLOBALS], "pop") : NULL;
            SPYValue *removed = pop ? spy_call(c, pop, 1, &name) : NULL;
            spy_release(pop); spy_release(removed);
            send_status(!removed);
        }
        spy_release(name); spy_release(value);
        break;
    }
    case MODULE: {
        SPYValue *name = decode_type(&k, SPY_STRING), *members = decode(&k, 0), *source = decode(&k, 0);
        finish(&k);
        if ((members && spy_type(members) != SPY_DICT && spy_type(members) != SPY_NONE) ||
            (source && spy_type(source) != SPY_STRING && spy_type(source) != SPY_NONE)) violation();
        SPYValue *pair[2] = {members, source}, *spec = name && members && source ? spy_tuple(c, 2, pair) : NULL;
        send_status(!spec || spy_set_item(c, w.modules, name, spec) || spy_new_module(c, spy_as_string(c, name, NULL), module_init));
        spy_release(spec); spy_release(name); spy_release(members); spy_release(source);
        break;
    }
    case MOUNT: {
        SPYValue *directory = decode_type(&k, SPY_STRING), *path = decode_type(&k, SPY_STRING), *read_only = decode_type(&k, SPY_BOOL);
        finish(&k);
        const char *host = directory ? spy_as_string(c, directory, NULL) : NULL;
        int failed = !host || !path || !read_only;
        if (!failed && sealed) failed = !spy_error(c, "PermissionError", "cannot mount after code has run");
        if (!failed) failed = spy_mount(c, host, spy_as_string(c, path, NULL), spy_truth(read_only) ? SPY_MOUNT_READ_ONLY : 0);
        if (!failed) {
            struct Mount *grown = realloc(mounts, (mounts_len + 1) * sizeof(*grown));
            char *copy = malloc(strlen(host) + 1);
            if (!grown || !copy) exit(1);
            mounts = grown;
            mounts[mounts_len++] = (struct Mount){strcpy(copy, host), spy_truth(read_only)};
        }
        send_status(failed);
        spy_release(directory); spy_release(path); spy_release(read_only);
        break;
    }
    case COLLECT:
        finish(&k);
        send_result(spy_int(c, (int64_t)spy_collect(c)));
        break;
    case OP: send_result(operate(&k)); break;
    case RELEASE: {
        SPYValue *ids = decode_type(&k, SPY_TUPLE), *iterator = ids ? spy_iter(c, ids) : NULL, *id;
        finish(&k);
        if (!iterator) exit(1);
        while ((id = spy_next(c, iterator))) {
            int64_t n;
            if (spy_type(id) != SPY_INT || spy_as_int(c, id, &n) || n < 1) violation();
            handle_release((uint64_t)n);
            spy_release(id);
        }
        spy_release(iterator); spy_release(ids);
        break;
    }
    default: violation();
    }
    free(message);
}

#if defined(__linux__)
/* Linux: no new privileges; Landlock confines files to the mounts and
 * denies TCP; seccomp allows only the system calls the engine makes and
 * fails every other with EPERM. Each layer the kernel lacks is skipped. */
#include <sys/prctl.h>
#include <sys/syscall.h>

#ifndef __NR_landlock_create_ruleset
#define __NR_landlock_create_ruleset 444
#define __NR_landlock_add_rule 445
#define __NR_landlock_restrict_self 446
#endif
/* The kernel ABIs used here, declared so the worker builds without kernel
 * headers (Alpine) or with old ones (manylinux). */
#ifndef PR_SET_NO_NEW_PRIVS
#define PR_SET_NO_NEW_PRIVS 38
#endif
#ifndef PR_SET_SECCOMP
#define PR_SET_SECCOMP 22
#endif
struct bpf { uint16_t code; uint8_t yes, no; uint32_t k; };
struct bpf_program { unsigned short len; struct bpf *filter; };
enum { BPF_LOAD = 0x20, BPF_JEQ = 0x15, BPF_RETURN = 0x06, SECCOMP_FILTER = 2 };
#define SECCOMP_KILL 0x80000000u
#define SECCOMP_ERRNO 0x00050000u
#define SECCOMP_ALLOW 0x7fff0000u

struct landlock_ruleset { uint64_t fs, net, scoped; };
struct landlock_path { uint64_t allowed; int32_t parent; } __attribute__((packed));
enum {
    LL_VERSION = 1, LL_PATH_BENEATH = 1,
    LL_EXECUTE = 1, LL_WRITE_FILE = 2, LL_READ_FILE = 4, LL_READ_DIR = 8, LL_REMOVE_DIR = 16, LL_REMOVE_FILE = 32,
    LL_MAKE_CHAR = 64, LL_MAKE_DIR = 128, LL_MAKE_REG = 256, LL_MAKE_SOCK = 512, LL_MAKE_FIFO = 1024,
    LL_MAKE_BLOCK = 2048, LL_MAKE_SYM = 4096, LL_REFER = 8192, LL_TRUNCATE = 16384, LL_IOCTL_DEV = 32768
};

static void landlock(void) {
    long abi = syscall(__NR_landlock_create_ruleset, NULL, 0, LL_VERSION);
    if (abi < 1) return;
    uint64_t fs = 8191 | (abi >= 2 ? LL_REFER : 0) | (abi >= 3 ? LL_TRUNCATE : 0) | (abi >= 5 ? LL_IOCTL_DEV : 0);
    struct landlock_ruleset attr = {fs, abi >= 4 ? 3 : 0, 0};
    size_t size = abi >= 6 ? sizeof(attr) : abi >= 4 ? 2 * sizeof(uint64_t) : sizeof(uint64_t);
    int ruleset = (int)syscall(__NR_landlock_create_ruleset, &attr, size, 0);
    if (ruleset < 0) return;
    uint64_t read = LL_READ_FILE | LL_READ_DIR;
    uint64_t write = LL_WRITE_FILE | LL_REMOVE_DIR | LL_REMOVE_FILE | LL_MAKE_DIR | LL_MAKE_REG | (abi >= 3 ? LL_TRUNCATE : 0);
    for (size_t i = 0; i < mounts_len; i++) {
        int fd = open(mounts[i].directory, O_PATH | O_CLOEXEC);
        struct landlock_path rule = {read | (mounts[i].read_only ? 0 : write), fd};
        if (fd < 0 || syscall(__NR_landlock_add_rule, ruleset, LL_PATH_BENEATH, &rule, 0)) exit(1);
        close(fd);
    }
    if (syscall(__NR_landlock_restrict_self, ruleset, 0)) exit(1);
    close(ruleset);
}

#if defined(__x86_64__)
#define AUDIT_ARCH_HERE 0xC000003Eu
#elif defined(__aarch64__)
#define AUDIT_ARCH_HERE 0xC00000B7u
#endif

static void seccomp(void) {
#ifdef AUDIT_ARCH_HERE
    static const int always[] = {
        __NR_read, __NR_write, __NR_readv, __NR_writev, __NR_close, __NR_lseek, __NR_fstat, __NR_fcntl,
        __NR_brk, __NR_mmap, __NR_munmap, __NR_mremap, __NR_madvise, __NR_mprotect,
        __NR_exit, __NR_exit_group, __NR_rt_sigreturn, __NR_rt_sigprocmask, __NR_rt_sigaction,
        __NR_getpid, __NR_gettid, __NR_tgkill, __NR_futex, __NR_sched_yield, __NR_restart_syscall,
        __NR_clock_gettime, __NR_getrandom,
    };
    static const int files[] = {
        __NR_openat, __NR_newfstatat, __NR_readlinkat, __NR_getcwd, __NR_getdents64, __NR_ftruncate,
        __NR_unlinkat, __NR_mkdirat,
#ifdef __NR_statx
        __NR_statx,
#endif
#ifdef __NR_open
        __NR_open, __NR_stat, __NR_lstat, __NR_readlink,
#endif
    };
    enum { ALWAYS = sizeof(always) / sizeof(*always), FILES = sizeof(files) / sizeof(*files) };
    struct bpf program[ALWAYS + FILES + 6];
    size_t n = 0, count = ALWAYS + (mounts_len ? FILES : 0);
    /* seccomp_data: the system call number at offset 0, the architecture at 4. */
    program[n++] = (struct bpf){BPF_LOAD, 0, 0, 4};
    program[n++] = (struct bpf){BPF_JEQ, 1, 0, AUDIT_ARCH_HERE};
    program[n++] = (struct bpf){BPF_RETURN, 0, 0, SECCOMP_KILL};
    program[n++] = (struct bpf){BPF_LOAD, 0, 0, 0};
    for (size_t i = 0; i < count; i++) /* a match jumps to the final ALLOW */
        program[n++] = (struct bpf){BPF_JEQ, (uint8_t)(count - i), 0, (uint32_t)(i < ALWAYS ? always[i] : files[i - ALWAYS])};
    program[n++] = (struct bpf){BPF_RETURN, 0, 0, SECCOMP_ERRNO | EPERM};
    program[n++] = (struct bpf){BPF_RETURN, 0, 0, SECCOMP_ALLOW};
    struct bpf_program filter = {(unsigned short)n, program};
    if (prctl(PR_SET_SECCOMP, SECCOMP_FILTER, &filter) && errno != EINVAL) exit(1);
#endif
}

static void seal(void) {
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)) exit(1);
    landlock();
    seccomp();
}
#elif defined(__APPLE__)
/* macOS: a sandbox profile denying everything but metadata reads, and
 * reading (and writing) beneath the mounts. Declared here: the header marks
 * the function deprecated, though it remains the documented interface. */
int sandbox_init(const char *profile, uint64_t flags, char **error);
static void quote(char **at, const char *s) {
    *(*at)++ = '"';
    for (; *s; s++) {
        if (*s == '"' || *s == '\\') *(*at)++ = '\\';
        *(*at)++ = *s;
    }
    *(*at)++ = '"';
}
static void seal(void) {
    size_t size = 256;
    for (size_t i = 0; i < mounts_len; i++) size += 2 * strlen(mounts[i].directory) + 64;
    char *profile = malloc(size), *at = profile, *error = NULL;
    if (!profile) exit(1);
    at += sprintf(at, "(version 1)(deny default)(allow file-read-metadata)(allow sysctl-read)");
    for (size_t i = 0; i < mounts_len; i++) {
        at += sprintf(at, mounts[i].read_only ? "(allow file-read* (subpath " : "(allow file-read* file-write* (subpath ");
        quote(&at, mounts[i].directory);
        at += sprintf(at, "))");
    }
    if (sandbox_init(profile, 0, &error)) {
        fprintf(stderr, "spy-worker: sandbox: %s\n", error ? error : "failed");
        exit(1);
    }
    free(profile);
}
#else
static void seal(void) {}
#endif

#if !defined(__wasm__) && !defined(_WIN32)
#if defined(__APPLE__)
#include <pthread.h>
#include <sys/event.h>
static void *watch_parent(void *data) {
    pid_t parent = (pid_t)(intptr_t)data;
    int queue = kqueue();
    struct kevent event;
    EV_SET(&event, parent, EVFILT_PROC, EV_ADD, NOTE_EXIT, 0, NULL);
    if (queue < 0 || kevent(queue, &event, 1, NULL, 0, NULL) < 0 || kevent(queue, NULL, 0, &event, 1, NULL) >= 0) _exit(0);
    _exit(0);
}
#endif
/* protocol.md 9: keep the protocol off stdin and stdout, write no core
 * files, and die with the parent. */
static void hygiene(void) {
    in_fd = dup(0); out_fd = dup(1);
    int null = open("/dev/null", O_RDWR);
    if (in_fd < 0 || out_fd < 0 || null < 0 || dup2(null, 0) < 0 || dup2(2, 1) < 0) exit(1);
    close(null);
    struct rlimit none = {0, 0};
    setrlimit(RLIMIT_CORE, &none);
    signal(SIGPIPE, SIG_IGN);
    pid_t parent = getppid();
#if defined(__linux__)
    prctl(PR_SET_PDEATHSIG, SIGKILL);
    if (getppid() != parent) _exit(0);
#elif defined(__APPLE__)
    pthread_t thread;
    if (pthread_create(&thread, NULL, watch_parent, (void *)(intptr_t)parent)) exit(1);
    pthread_detach(thread);
#endif
}
#elif defined(_WIN32)
#include <windows.h>
#include <tlhelp32.h>
static DWORD WINAPI watch_parent(LPVOID parent) {
    WaitForSingleObject(parent, INFINITE);
    _exit(0);
}
/* The parent, unless it has already exited and its id was reused by a
 * process younger than this one. */
static HANDLE open_parent(void) {
    DWORD me = GetCurrentProcessId(), id = 0;
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0), parent;
    PROCESSENTRY32 entry = {.dwSize = sizeof(entry)};
    for (BOOL more = Process32First(snapshot, &entry); more; more = Process32Next(snapshot, &entry))
        if (entry.th32ProcessID == me) id = entry.th32ParentProcessID;
    CloseHandle(snapshot);
    FILETIME born, mine, unused;
    if (!(parent = OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, FALSE, id)) ||
        !GetProcessTimes(parent, &born, &unused, &unused, &unused) ||
        !GetProcessTimes(GetCurrentProcess(), &mine, &unused, &unused, &unused) ||
        CompareFileTime(&born, &mine) > 0) _exit(0);
    return parent;
}
/* protocol.md 9 on Windows: the protocol off stdin and stdout in binary
 * mode, no crash dialogs, and a thread that ends the worker with the parent. */
static void hygiene(void) {
    in_fd = _dup(0); out_fd = _dup(1);
    int null = _open("NUL", _O_RDWR);
    if (in_fd < 0 || out_fd < 0 || null < 0 || _dup2(null, 0) < 0 || _dup2(2, 1) < 0) exit(1);
    _close(null);
    _setmode(in_fd, _O_BINARY); _setmode(out_fd, _O_BINARY);
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
    if (!CreateThread(NULL, 0, watch_parent, open_parent(), 0, NULL)) exit(1);
}
#endif

int main(int argc, char **argv) {
    if (argc == 2 && !strcmp(argv[1], "--version")) { puts(SPY_VERSION); return 0; }
    if (argc > 1) { fputs("usage: spy-worker [--version]\n", stderr); return 2; }
#if !defined(__wasm__)
    hygiene();
#endif
    SPYContext *c = w.c = spy_context_new();
    if (!c) return 1;
    SPYValue *helpers = spy_eval(c, HELPERS, "<spy-worker>");
    for (int i = 0; helpers && i < H_COUNT; i++) {
        SPYValue *index = spy_int(c, i);
        if (!index || !(w.helper[i] = spy_get_item(c, helpers, index))) return 1;
        spy_release(index);
    }
    if (!helpers || !(w.modules = spy_dict(c))) return 1;
    spy_release(helpers);
    spy_set_output(c, output, NULL);
    spy_set_module_loader(c, load, NULL);
    for (;;) {
        size_t len;
        unsigned char *message = read_message(&len);
        if (message[0] >= RESULT) violation();
        serve(message, len);
    }
}
#endif
