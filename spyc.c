/* spyc: bundle a Python program and the modules it imports into one C
 * translation unit (docs/build.md). As QuickJS's qjsc, it compiles with the
 * engine (spy.c) so the build parses exactly what the program runs; a normal
 * C compiler then links the result with libspy.a. No shell, compiler, or
 * platform process API is hidden here.
 *
 * Modules are found as CPython's path finder finds them over the search
 * roots, embedded byte for byte, and served at run time by a generated
 * SPYModuleLoader whose keys are the names the engine probes:
 * NAME.__init__ for a package, NAME for a module, NAME.__namespace__ for a
 * namespace package. */
#include "spy.c"
#include "host.h"
#include <dirent.h>

enum { NONE, MODULE, PACKAGE, NAMESPACE, EXTERNAL, REGISTERED };

typedef struct { char **items; size_t len, cap; } Strings;
typedef struct { char *path, *original; const char *kind; int flag; } Import;   /* flag: 1 external, 2 missing */
typedef struct {
    char *name, *path;      /* path: the source file, relative to the working directory */
    int kind, queued;
    Strings locations;      /* where a package's submodules are searched */
    Strings all;            /* a literal __all__ */
    char *source;           /* read once queued; minified with --minify */
    size_t bytes;           /* the size of the file read */
    char *array;            /* the C array of its source in the output */
    Import *imports; size_t imports_len, imports_cap;
} Module;
/* What a scan of one source reports against: its file, or a -D option. */
typedef struct { const char *path, *option; size_t line; Module *owner; } Origin;
typedef struct {
    SPYContext *c;
    Strings roots, externals, registered, aliases, stars;
    Module **modules; size_t len, cap;
    Module **queue; size_t queue_len, queue_cap, queue_at;
    size_t errors, warnings;
    int minify;
} Build;

static void *need(void *p) {
    if (!p) { fputs("spyc: out of memory\n", stderr); exit(1); }
    return p;
}
static char *concat(const char *a, const char *b, const char *c) {
    size_t la = strlen(a), lb = strlen(b), lc = strlen(c);
    char *s = need(malloc(la + lb + lc + 1));
    memcpy(s, a, la); memcpy(s + la, b, lb); memcpy(s + la + lb, c, lc + 1);
    return s;
}
static char *slice(const char *s, size_t n) {
    char *t = need(malloc(n + 1));
    memcpy(t, s, n); t[n] = 0;
    return t;
}
static void push(Strings *list, char *s) {
    if (list->len == list->cap) list->items = need(realloc(list->items, (list->cap = list->cap ? list->cap * 2 : 8) * sizeof(char *)));
    list->items[list->len++] = s;
}
static void free_strings(Strings *list) {
    for (size_t i = 0; i < list->len; i++) free(list->items[i]);
    free(list->items);
}
/* All a module owns but its path, which an entry borrows. */
static void free_module(Module *m) {
    free_strings(&m->locations); free_strings(&m->all);
    free(m->source); free(m->array);
    for (size_t i = 0; i < m->imports_len; i++) free(m->imports[i].path), free(m->imports[i].original);
    free(m->imports);
}
/* NAME or a submodule of it. */
static int under(const char *prefix, const char *name) {
    size_t n = strlen(prefix);
    return !strncmp(prefix, name, n) && (!name[n] || name[n] == '.');
}
static int identifier_text(const char *s, size_t n) {
    if (!n || isdigit((unsigned char)*s)) return 0;
    for (size_t i = 0; i < n; i++)
        if (!isalnum((unsigned char)s[i]) && s[i] != '_' && (unsigned char)s[i] < 128) return 0;
    return 1;
}
static int dotted_name(const char *s) {
    for (const char *dot; ; s = dot + 1) {
        dot = strchr(s, '.');
        if (!identifier_text(s, dot ? (size_t)(dot - s) : strlen(s))) return 0;
        if (!dot) return 1;
    }
}
static void report(Build *b, const Origin *o, const char *format, const char *name, const char *extra) {
    if (o->option) fprintf(stderr, "spyc: error: %s: ", o->option);
    else fprintf(stderr, "%s:%zu: error: ", o->path, o->line);
    fprintf(stderr, format, name, extra);
    fputc('\n', stderr);
    b->errors++;
}

/* The file system, compared by exact spelling as FileFinder compares its
 * directory listing, whatever the file system's case rules. */
static int entry_kind(const char *directory, const char *name) {
    DIR *dir = opendir(*directory ? directory : ".");
    int found = 0;
    for (struct dirent *e; dir && !found && (e = readdir(dir));) found = !strcmp(e->d_name, name);
    if (dir) closedir(dir);
    if (!found) return 0;
    char *path = concat(directory, name, "");
    struct stat info;
    int kind = stat(path, &info) ? 0 : S_ISDIR(info.st_mode) ? 'd' : S_ISREG(info.st_mode) ? 'f' : 0;
    free(path);
    return kind;
}

static Module *find(Build *b, const char *name);
/* FileFinder over each location in turn, keeping namespace portions
 * (PathFinder); locations end in '/' or are empty for the working directory. */
static void search(Module *m, const Strings *locations, const char *tail) {
    char *file = concat(tail, ".py", "");
    Strings portions = {0};
    for (size_t i = 0; i < locations->len && !m->kind; i++) {
        const char *d = locations->items[i];
        char *package = concat(d, tail, "/");
        if (entry_kind(d, tail) == 'd' && entry_kind(package, "__init__.py") == 'f') {
            m->kind = PACKAGE; m->path = concat(package, "__init__.py", "");
            push(&m->locations, package);
            break;
        }
        if (entry_kind(d, file) == 'f') { m->kind = MODULE; m->path = concat(d, file, ""); }
        else if (entry_kind(d, tail) == 'd') push(&portions, package), package = NULL;
        free(package);
    }
    if (!m->kind && portions.len) { m->kind = NAMESPACE; m->locations = portions; }
    else { for (size_t i = 0; i < portions.len; i++) free(portions.items[i]); free(portions.items); }
    free(file);
}
static Module *find(Build *b, const char *name) {
    for (size_t i = 0; i < b->len; i++) if (!strcmp(b->modules[i]->name, name)) return b->modules[i];
    Module *m = need(calloc(1, sizeof(Module)));
    m->name = concat(name, "", "");
    if (b->len == b->cap) b->modules = need(realloc(b->modules, (b->cap = b->cap ? b->cap * 2 : 32) * sizeof(Module *)));
    b->modules[b->len++] = m;
    for (size_t i = 0; i < b->externals.len; i++) if (under(b->externals.items[i], name)) m->kind = EXTERNAL;
    for (size_t i = 0; i < b->registered.len; i++) if (!strcmp(b->registered.items[i], name)) m->kind = REGISTERED;
    if (m->kind) return m;
    for (size_t i = 0; i < b->aliases.len; i += 2)
        if (!strcmp(b->aliases.items[i], name)) {
            Module *target = find(b, b->aliases.items[i + 1]);
            if (target->kind == MODULE || target->kind == PACKAGE || target->kind == NAMESPACE) {
                m->kind = target->kind;
                m->path = target->path ? concat(target->path, "", "") : NULL;
                for (size_t j = 0; j < target->locations.len; j++) push(&m->locations, concat(target->locations.items[j], "", ""));
            }
            return m;
        }
    const char *dot = strrchr(name, '.');
    if (!dot) search(m, &b->roots, name);
    else {
        char *parent = slice(name, (size_t)(dot - name));
        Module *p = find(b, parent);
        free(parent);
        if (p->kind == PACKAGE || p->kind == NAMESPACE) search(m, &p->locations, dot + 1);
    }
    return m;
}
static int found(const Module *m) { return m->kind == MODULE || m->kind == PACKAGE || m->kind == NAMESPACE; }

static void record(Module *owner, const char *path, const char *original, const char *kind, int flag) {
    if (!owner) return;
    for (size_t i = 0; i < owner->imports_len; i++) {
        Import *e = &owner->imports[i];
        if (!strcmp(e->path, path) && !strcmp(e->original, original) && e->kind == kind) return;
    }
    if (owner->imports_len == owner->imports_cap)
        owner->imports = need(realloc(owner->imports, (owner->imports_cap = owner->imports_cap ? owner->imports_cap * 2 : 8) * sizeof(Import)));
    owner->imports[owner->imports_len++] = (Import){concat(path, "", ""), concat(original, "", ""), kind, flag};
}
static void enqueue(Build *b, Module *m) {
    if (m->queued) return;
    m->queued = 1;
    if (b->queue_len == b->queue_cap) b->queue = need(realloc(b->queue, (b->queue_cap = b->queue_cap ? b->queue_cap * 2 : 32) * sizeof(Module *)));
    b->queue[b->queue_len++] = m;
}
/* An import of NAME: a required one that does not resolve fails the build
 * with CPython's message; a guarded one, or a from-import name that may be
 * an attribute, is left out. */
static void request(Build *b, const Origin *o, const char *name, int required, const char *kind) {
    Module *m = find(b, name);
    if (m->kind == EXTERNAL || m->kind == REGISTERED) { record(o->owner, name, name, kind, 1); return; }
    if (found(m)) { enqueue(b, m); record(o->owner, m->path ? m->path : name, name, kind, 0); return; }
    if (!required) { if (strcmp(kind, "maybe")) record(o->owner, name, name, kind, 2); return; }
    /* The first part that is missing, or that is a module and not a package. */
    for (const char *dot = strchr(name, '.'); dot; dot = strchr(dot + 1, '.')) {
        char *prefix = slice(name, (size_t)(dot - name));
        Module *p = find(b, prefix);
        int stop = !found(p) || p->kind == MODULE;
        if (stop && found(p)) report(b, o, "No module named '%s'; '%s' is not a package", name, prefix);
        else if (stop) report(b, o, "No module named '%s'%s", prefix, "");
        free(prefix);
        if (stop) return;
    }
    report(b, o, "No module named '%s'%s", name, "");
}

/* The walk of one parsed source: the imports its statements and literal
 * __import__ calls name, where each stands. */
typedef struct { Build *b; Origin origin; const char *package; } Scan;
static int catches_import(Node *handlers) {
    static const char *const names[] = {"ImportError", "ModuleNotFoundError", "Exception", "BaseException"};
    for (Node *h = handlers; h; h = h->next) {
        if (!h->a) return 1;
        for (Node *t = h->a->kind == N_TUPLE ? h->a->args : h->a; t; t = h->a->kind == N_TUPLE ? t->next : NULL)
            for (size_t i = 0; t->kind == N_NAME && i < sizeof(names) / sizeof(*names); i++)
                if (!strcmp(source_name(t), names[i])) return 1;
    }
    return 0;
}
/* The absolute name of a relative import (PEP 328), or NULL with an error
 * reported for a required one. */
static char *absolute(Scan *s, int level, const char *name, int required) {
    if (!level) return concat(name, "", "");
    const char *package = s->package;
    size_t parts = package && *package ? 1 : 0;
    for (const char *p = package; parts && *p; p++) parts += *p == '.';
    if (!parts || parts < (size_t)level) {
        if (required) report(s->b, &s->origin, "%s%s", parts ? "attempted relative import beyond top-level package"
                                                             : "attempted relative import with no known parent package", "");
        return NULL;
    }
    size_t keep = strlen(package);
    for (int i = 1; i < level; i++) while (package[--keep] != '.') {}
    char *base = slice(package, keep);
    if (!*name) return base;
    char *full = concat(base, ".", name);
    free(base);
    return full;
}
static void walk(Scan *s, Node *n, int guarded);
static void scan_from(Scan *s, Node *n, int guarded) {
    const char *module = n->a ? source_name(n->a) : "";
    if (!n->op && !strcmp(module, "__future__")) return;
    const char *kind = n->flags & F_LAZY ? "lazy-import" : "from-statement";
    char *base = absolute(s, n->op, module, !guarded);
    if (!base) return;
    request(s->b, &s->origin, base, !guarded, kind);
    if (n->args && n->args->kind == N_STAR) push(&s->b->stars, concat(base, "", ""));
    else for (Node *item = n->args; item; item = item->next) {
        char *name = concat(base, ".", source_name(item->a));
        request(s->b, &s->origin, name, 0, "maybe");
        free(name);
    }
    free(base);
}
/* __import__("a.b", ..., fromlist) with string literals, as the statement. */
static void import_call(Scan *s, Node *n, int guarded) {
    Node *first = n->args, *fromlist = NULL;
    for (Node *arg = n->args; arg; arg = arg->next)
        if (arg->kind == N_KEYWORD && arg->text && !strcmp(arg->text, "fromlist")) fromlist = arg->a;
    if (first && first->next && first->next->next && first->next->next->next && first->next->next->next->kind != N_KEYWORD)
        fromlist = first->next->next->next;
    if (!first || first->kind != N_STRING || !dotted_name(first->text)) {
        fprintf(stderr, "%s:%zu: warning: __import__ of a computed name cannot be bundled; name its modules with -D\n",
                s->origin.path, n->line);
        s->b->warnings++;
        return;
    }
    request(s->b, &s->origin, first->text, !guarded, "dynamic-import");
    for (Node *item = fromlist && (fromlist->kind == N_TUPLE || fromlist->kind == N_LIST) ? fromlist->args : NULL; item; item = item->next)
        if (item->kind == N_STRING && identifier_text(item->text, strlen(item->text))) {
            char *name = concat(first->text, ".", item->text);
            request(s->b, &s->origin, name, 0, "maybe");
            free(name);
        }
}
static void walk(Scan *s, Node *n, int guarded) {
    for (; n; n = n->next) {
        s->origin.line = n->line;
        if (n->kind == N_IMPORT) {
            for (Node *item = n->args; item; item = item->next)
                request(s->b, &s->origin, source_name(item->a), !guarded, n->flags & F_LAZY ? "lazy-import" : "import-statement");
            continue;
        }
        if (n->kind == N_FROM) { scan_from(s, n, guarded); continue; }
        if (n->kind == N_TRY) {
            walk(s, n->a, guarded || catches_import(n->args));
            walk(s, n->args, guarded); walk(s, n->b, guarded); walk(s, n->c, guarded);
            continue;
        }
        if (n->kind == N_CALL && n->a && n->a->kind == N_NAME && !strcmp(source_name(n->a), "__import__")) import_call(s, n, guarded);
        walk(s, n->a, guarded); walk(s, n->b, guarded); walk(s, n->c, guarded);
        walk(s, n->args, guarded); walk(s, n->decorators, guarded); walk(s, n->params, guarded);
    }
}
/* A literal __all__ of a module, for from-imports of *. */
static void literal_all(Module *m, Node *body) {
    for (Node *n = body; n; n = n->next)
        if (n->kind == N_ASSIGN && n->a && n->a->kind == N_NAME && !strcmp(n->a->text, "__all__") && n->b &&
            (n->b->kind == N_LIST || n->b->kind == N_TUPLE))
            for (Node *item = n->b->args; item; item = item->next)
                if (item->kind == N_STRING) push(&m->all, concat(item->text, "", ""));
}
/* --minify (docs/build.md 6.2): the tokens again, each on its line, with
 * one space per indentation level and between two tokens only where they
 * would otherwise lex as one. Comments go, except a #! line and those that
 * name @license or @preserve. The result is UTF-8, so it needs no coding
 * declaration. NULL if the result does not lex to the same tokens. */
static void put(Buffer *, const char *, ...);
static int merges(const Token *a, const Token *b) {
    static const char *const pairs[] = {"==", "!=", "<>", "<=", ">=", "**", "//", "<<", ">>", "+=", "-=", "*=", "/=",
                                        "%=", "@=", "&=", "|=", "^=", ":=", "->", ".."};
    unsigned char x = (unsigned char)a->start[a->len - 1], y = (unsigned char)*b->start;
    int number = a->kind == T_INT || a->kind == T_FLOAT || a->kind == T_IMAG;
    if ((isalnum(x) || x == '_' || x >= 128 || number) && (isalnum(y) || y == '_' || y >= 128 || (number && y == '.'))) return 1;
    if (a->kind == T_STRING && b->kind == T_STRING) return 1;
    for (size_t i = 0; i < sizeof pairs / sizeof *pairs; i++) if (x == pairs[i][0] && y == pairs[i][1]) return 1;
    return 0;
}
typedef struct { Buffer out; size_t line; int fresh, level, started; } Minified;
/* Down to a line: a new line between statements or inside brackets, else
 * a backslash continuation. */
static void minify_line(Minified *m, size_t line) {
    for (; m->line < line; m->line++, m->started = 0) put(&m->out, m->fresh || m->level ? "\n" : "\\\n");
}
static void minify_comments(Minified *m, const char *text, const char *from, const char *to, size_t line) {
    for (const char *s = from; s < to; s++) {
        if (*s == '\n') line++;
        if (*s != '#') continue;
        size_t n = strcspn(s, "\n");
        char *comment = slice(s, n);
        if ((s == text && s[1] == '!') || strstr(comment, "@license") || strstr(comment, "@preserve")) {
            minify_line(m, line);
            put(&m->out, "%s%s", m->started ? " " : "", comment);
            m->started = 1;
        }
        free(comment);
        s += n - 1;
    }
}
static int same_tokens(const Parser *a, const Parser *b) {
    if (a->len != b->len) return 0;
    for (size_t i = 0; i < a->len; i++) {
        const Token *x = &a->tokens[i], *y = &b->tokens[i];
        if (x->kind != y->kind || x->line != y->line || (x->kind != T_NL && (x->len != y->len || memcmp(x->start, y->start, x->len))))
            return 0;
    }
    return 1;
}
static char *minify(SPYContext *c, const char *source, const char *path) {
    SPYValue *decoded = decode_source(c, source, strlen(source), path);
    if (!decoded) return NULL;
    char *text = need(malloc(decoded->as.string.len + 1)), *end = text;
    for (const char *s = decoded->as.string.data; *s; s++) {
        if (*s == '\r') { *end++ = '\n'; if (s[1] == '\n') s++; }
        else *end++ = *s;
    }
    *end = 0;
    spy_release(decoded);
    Parser before = {.ctx = c}, after = {.ctx = c};
    Minified m = {{.ctx = c}, 1, 1, 0, 0};
    char *result = NULL;
    if (lex(&before, text)) goto done;
    const char *gap = text;
    size_t gap_line = 1, depth = 0;
    for (const Token *t = before.tokens, *last = NULL; ; t++) {
        minify_comments(&m, text, gap, t->kind == T_END ? end : t->start, gap_line);
        if (t->kind == T_END) { minify_line(&m, t->line); break; }
        if (t->kind == T_INDENT) { depth++; continue; }
        if (t->kind == T_DEDENT) { depth--; continue; }
        if (t->kind == T_NL) { m.fresh = 1; gap = t->start; gap_line = t->line; continue; }
        minify_line(&m, t->line);
        if (!m.started && m.fresh) for (size_t i = 0; i < depth; i++) put(&m.out, " ");
        else if (m.started && merges(last, t)) put(&m.out, " ");
        if (append(&m.out, t->start, t->len)) need(NULL);
        for (size_t i = 0; i < t->len; i++) m.line += t->start[i] == '\n';
        m.fresh = 0; m.started = 1; m.level = (int)t->level; last = t;
        gap = t->start + t->len; gap_line = m.line;
    }
    const char *small = m.out.data ? m.out.data : "";
    if (!lex(&after, small) && same_tokens(&before, &after)) result = concat(small, "", "");
done:
    if (c->error_type[0]) spy_clear_error(c);
    mem_free(before.tokens); mem_free(after.tokens); mem_free(m.out.data); free(text);
    return result;
}
/* Read, walk, and with --minify minify the source of m, which has a path. */
static void scan(Build *b, Module *m, const char *package) {
    FILE *file = fopen(m->path, "rb");
    m->source = file ? host_read(file) : NULL;
    if (file) fclose(file);
    if (!m->source) { fprintf(stderr, "spyc: error: cannot read %s\n", m->path); b->errors++; return; }
    m->bytes = strlen(m->source);
    SPYValue *unit = parse(b->c, m->source, m->path);
    if (!unit) {
        fprintf(stderr, "%s:%zu: error: %s\n", m->path, spy_error_line(b->c), spy_error_display(b->c));
        spy_clear_error(b->c);
        b->errors++;
        return;
    }
    Scan s = {b, {m->path, NULL, 0, m}, package};
    walk(&s, unit->as.unit.body, 0);
    literal_all(m, unit->as.unit.body);
    spy_release(unit);
    if (!b->minify) return;
    char *small = minify(b->c, m->source, m->path);
    if (!small) { fprintf(stderr, "%s: error: --minify changed the program's tokens\n", m->path); b->errors++; return; }
    free(m->source);
    m->source = small;
}
/* Visit queued modules until none is left, then the submodules named by the
 * __all__ of modules imported with *, which may queue more. */
static void discover(Build *b, Module *entry) {
    for (size_t done = 0; !b->errors;) {
        while (!b->errors && b->queue_at < b->queue_len) {
            Module *m = b->queue[b->queue_at++];
            const char *dot = strrchr(m->name, '.');
            if (dot) {
                char *parent = slice(m->name, (size_t)(dot - m->name));
                enqueue(b, find(b, parent));
                free(parent);
            }
            if (!m->path) continue;
            char *package = m->kind == PACKAGE ? concat(m->name, "", "") : slice(m->name, dot ? (size_t)(dot - m->name) : 0);
            scan(b, m, package);
            free(package);
        }
        if (b->errors || done == b->stars.len) break;
        for (; done < b->stars.len; done++) {
            Module *base = find(b, b->stars.items[done]);
            Origin o = {NULL, "from-import *", 0, entry};
            for (size_t i = 0; i < base->all.len; i++) {
                char *name = concat(base->name, ".", base->all.items[i]);
                request(b, &o, name, 0, "maybe");
                free(name);
            }
        }
    }
}
/* -D PKG.*: every module and package below PKG, at any depth. */
static void include_all(Build *b, const Origin *o, Module *package) {
    for (size_t i = 0; i < package->locations.len; i++) {
        const char *d = package->locations.items[i];
        DIR *dir = opendir(*d ? d : ".");
        Strings names = {0};
        for (struct dirent *e; dir && (e = readdir(dir));) push(&names, concat(e->d_name, "", ""));
        if (dir) closedir(dir);
        qsort(names.items, names.len, sizeof(char *), (int (*)(const void *, const void *))strcmp);
        for (size_t j = 0; j < names.len; j++) {
            const char *e = names.items[j];
            size_t n = strlen(e);
            int py = n > 3 && !strcmp(e + n - 3, ".py");
            if (!identifier_text(e, py ? n - 3 : n) || (py && n == 11 && !strncmp(e, "__init__", 8))) continue;
            char *stem = slice(e, py ? n - 3 : n), *name = concat(package->name, ".", stem);
            Module *m = find(b, name);
            if (m->kind == MODULE || m->kind == PACKAGE) request(b, o, name, 1, "include");
            if (m->kind == PACKAGE || m->kind == NAMESPACE) include_all(b, o, m);
            free(stem); free(name);
        }
        for (size_t j = 0; j < names.len; j++) free(names.items[j]);
        free(names.items);
    }
}

/* Output, built in memory and written only when the build succeeds. */
static void put(Buffer *out, const char *format, ...) {
    char small[256];
    va_list args;
    va_start(args, format);
    int n = vsnprintf(small, sizeof small, format, args);
    va_end(args);
    char *text = (size_t)n < sizeof small ? small : need(malloc((size_t)n + 1));
    if (text != small) {
        va_start(args, format);
        vsnprintf(text, (size_t)n + 1, format, args);
        va_end(args);
    }
    if (append(out, text, (size_t)n)) need(NULL);
    if (text != small) free(text);
}
static void put_bytes(Buffer *out, const char *s) {
    for (size_t i = 0; s[i]; i++) put(out, i % 24 == 23 ? "%u,\n" : "%u,", (unsigned char)s[i]);
    put(out, "0};\n");
}
/* A C string literal, escaping all but plain ASCII. */
static void put_string(Buffer *out, const char *s) {
    put(out, "\"");
    for (; *s; s++) put(out, isalnum((unsigned char)*s) || *s == '_' || *s == '.' ? "%c" : "\\%03o", (unsigned char)*s);
    put(out, "\"");
}
static void put_json(Buffer *out, const char *s) {
    put(out, "\"");
    for (; *s; s++) put(out, *s == '"' || *s == '\\' ? "\\%c" : (unsigned char)*s < 32 ? "\\u%04x" : "%c", (unsigned char)*s);
    put(out, "\"");
}
static int by_key(const void *x, const void *y) {
    const Module *a = *(Module *const *)x, *b = *(Module *const *)y;
    char *ka = concat(a->name, a->kind == PACKAGE ? ".__init__" : a->kind == NAMESPACE ? ".__namespace__" : "", "");
    char *kb = concat(b->name, b->kind == PACKAGE ? ".__init__" : b->kind == NAMESPACE ? ".__namespace__" : "", "");
    int order = strcmp(ka, kb);
    free(ka); free(kb);
    return order;
}
static int by_size(const void *x, const void *y) {
    size_t a = strlen((*(Module *const *)x)->source), b = strlen((*(Module *const *)y)->source);
    return a < b ? 1 : a > b ? -1 : strcmp((*(Module *const *)x)->path, (*(Module *const *)y)->path);
}
static int write_file(const char *path, const Buffer *data) {
    FILE *f = fopen(path, "wb");
    int failed = !f || fwrite(data->data, 1, data->len, f) != data->len;
    if (f && fclose(f)) failed = 1;
    if (failed) fprintf(stderr, "spyc: error: cannot write %s\n", path);
    return failed;
}
/* A C identifier for an entry: spy_ and its name, as spyc -c names it. */
static char *c_name(const char *entry, int module) {
    const char *base = module ? entry : strrchr(entry, '/') ? strrchr(entry, '/') + 1 : entry;
    char *name = concat("spy_", base, "");
    char *end = module ? name + strlen(name) : name + 4 + strcspn(base, ".");
    *end = 0;
    for (char *p = name + 4; *p; p++) if (!isalnum((unsigned char)*p)) *p = '_';
    return name;
}

/* An entry: the __file__ and __package__ it runs with, its C name, and
 * its file, read as a module that names no table entry. */
typedef struct { char *file, *package, *symbol; Module module; } EntryPoint;

static int usage(void) {
    fputs("usage: spyc [options] -o program.c (input.py | -m module)\n"
          "       spyc -c [options] -o modules.c (input.py | -m module)...\n"
          "options: -M module, -I dir, -x module, -D module[.*], -N name, --alias name=target,\n"
          "         -O, -OO, --minify, --metafile file, --deps file, --analyze, -Werror\n", stderr);
    return 2;
}
int main(int argc, char **argv) {
    Build b = {0};
    Strings files = {0}, mains = {0}, includes = {0};
    const char *output = NULL, *metafile = NULL, *deps = NULL, *loader_name = NULL;
    int bare = 0, analyze = 0, werror = 0, optimize = 0, status = 0;
    EntryPoint *list = NULL;
    size_t entries = 0, sources = 0;
    Module **table = NULL, **inputs = NULL;
    char *loader = NULL;
    Buffer out = {0}, meta = {0}, rule = {0};
    for (int i = 1; i < argc; i++) {
        const char *a = argv[i], *value = i + 1 < argc ? argv[i + 1] : NULL;
        int takes = !strcmp(a, "-o") || !strcmp(a, "-m") || !strcmp(a, "-M") || !strcmp(a, "-I") || !strcmp(a, "-x") ||
                    !strcmp(a, "-D") || !strcmp(a, "-N") || !strcmp(a, "--alias") || !strcmp(a, "--metafile") || !strcmp(a, "--deps");
        if (takes && !value) { status = usage(); goto done; }
        if (takes) i++;
        if (!strcmp(a, "-c")) bare = 1;
        else if (!strcmp(a, "--analyze")) analyze = 1;
        else if (!strcmp(a, "-Werror")) werror = 1;
        else if (!strcmp(a, "--minify")) b.minify = 1;
        else if (!strcmp(a, "-O") || !strcmp(a, "-OO")) optimize = (int)strlen(a) - 1;
        else if (!strcmp(a, "-o")) output = value;
        else if (!strcmp(a, "--metafile")) metafile = value;
        else if (!strcmp(a, "--deps")) deps = value;
        else if (!strcmp(a, "-I")) push(&b.roots, strlen(value) && value[strlen(value) - 1] != '/' ? concat(value, "/", "") : concat(value, "", ""));
        else if (!strcmp(a, "-N")) {
            if (!identifier_text(value, strlen(value))) { status = usage(); goto done; }
            loader_name = value;
        } else if (!strcmp(a, "--alias")) {
            const char *equals = strchr(value, '=');
            char *name = equals ? slice(value, (size_t)(equals - value)) : NULL;
            if (!name || !dotted_name(name) || !dotted_name(equals + 1)) { free(name); status = usage(); goto done; }
            push(&b.aliases, name); push(&b.aliases, concat(equals + 1, "", ""));
        } else if (takes) {
            size_t n = strlen(value);
            int star = !strcmp(a, "-D") && n > 2 && !strcmp(value + n - 2, ".*");
            char *name = slice(value, star ? n - 2 : n);
            if (!dotted_name(name)) { free(name); status = usage(); goto done; }
            push(!strcmp(a, "-m") ? &mains : !strcmp(a, "-M") ? &b.registered : !strcmp(a, "-x") ? &b.externals : &includes,
                 star ? concat(name, ".*", "") : concat(name, "", ""));
            free(name);
        } else if (a[0] == '-') { status = usage(); goto done; }
        else push(&files, concat(a, "", ""));
    }
    entries = files.len + mains.len;
    if (!output || !entries || (!bare && entries > 1) || (bare && (b.registered.len || optimize))) { status = usage(); goto done; }
    for (size_t i = 0; i < files.len; i++) if (!strcmp(files.items[i], output)) { status = usage(); goto done; }

    /* The first root is the entry's directory, or the working directory for -m. */
    const char *first = files.len ? files.items[0] : NULL, *slash = first ? strrchr(first, '/') : NULL;
    Strings roots = {0};
    push(&roots, slash ? slice(first, (size_t)(slash - first) + 1) : concat("", "", ""));
    for (size_t i = 0; i < b.roots.len; i++) push(&roots, b.roots.items[i]);
    free(b.roots.items);
    b.roots = roots;
    b.c = need(spy_context_new());

    list = need(calloc(entries, sizeof(EntryPoint)));
    for (size_t i = 0; i < entries && !b.errors; i++) {
        EntryPoint *e = &list[i];
        if (i < files.len) {
            e->module.path = files.items[i];
            const char *base = strrchr(e->module.path, '/');
            e->file = concat(base ? base + 1 : e->module.path, "", "");
            e->symbol = c_name(e->module.path, 0);
            scan(&b, &e->module, NULL);
            continue;
        }
        /* -m runs MODULE, or a package's __main__, with its package set. */
        const char *name = mains.items[i - files.len];
        Origin o = {NULL, "-m", 0, NULL};
        Module *m = find(&b, name);
        char *run = m->kind == PACKAGE ? concat(name, ".__main__", "") : concat(name, "", "");
        Module *target = find(&b, run);
        if (target->kind != MODULE) { report(&b, &o, "No module named '%s'%s", run, ""); free(run); break; }
        const char *dot = strrchr(run, '.');
        e->module.path = target->path;
        e->file = concat(run, ".py", "");
        for (char *p = e->file; *p != '.' || strcmp(p, ".py"); p++) if (*p == '.') *p = '/';
        e->package = slice(run, dot ? (size_t)(dot - run) : 0);
        e->symbol = c_name(name, 1);
        if (*e->package) enqueue(&b, find(&b, e->package));
        scan(&b, &e->module, e->package);
        free(run);
    }
    for (size_t i = 0; i < includes.len && !b.errors; i++) {
        char *option = concat("-D ", includes.items[i], "");
        Origin o = {NULL, option, 0, &list[0].module};
        size_t n = strlen(includes.items[i]);
        if (n > 2 && !strcmp(includes.items[i] + n - 2, ".*")) {
            char *name = slice(includes.items[i], n - 2);
            Module *package = find(&b, name);
            if (package->kind == PACKAGE || package->kind == NAMESPACE) include_all(&b, &o, package);
            else if (found(package)) report(&b, &o, "'%s' is not a package%s", name, "");
            else request(&b, &o, name, 1, "include");
            free(name);
        } else request(&b, &o, includes.items[i], 1, "include");
        free(option);
    }
    if (!b.errors) discover(&b, &list[0].module);
    if (werror && b.warnings) b.errors++;
    if (b.errors) { status = 1; goto done; }

    /* The table, sorted by the keys the loader answers; the inputs, the
 * entries and then the table's other files, each with the C array holding
 * its source. A module that is also an entry shares the entry's array. */
    table = need(calloc(b.len + 1, sizeof(Module *)));
    inputs = need(calloc(b.len + entries, sizeof(Module *)));
    size_t count = 0;
    for (size_t i = 0; i < b.len; i++) if (b.modules[i]->queued && found(b.modules[i])) table[count++] = b.modules[i];
    qsort(table, count, sizeof(Module *), by_key);
    for (size_t i = 0; i < entries; i++) {
        inputs[sources++] = &list[i].module;
        list[i].module.array = concat(bare ? list[i].symbol : "source", "", "");
    }
    for (size_t i = 0; i < count; i++) {
        Module *m = table[i];
        size_t e = 0;
        while (m->path && e < entries && strcmp(list[e].module.path, m->path)) e++;
        if (!m->path) m->array = concat("\"\"", "", "");
        else if (e < entries) m->array = concat(list[e].module.array, "", "");
        else {
            m->array = need(malloc(32));
            snprintf(m->array, 32, "module_%zu", i);
            inputs[sources++] = m;
        }
    }
    loader = loader_name ? concat(loader_name, "_load", "") : concat(list[0].symbol, "_load", "");

    out.ctx = meta.ctx = rule.ctx = b.c;
    if (bare) put(&out, "/* Generated by spyc -c. A host installs %s with spy_set_module_loader\n"
                        " * and runs an entry with spy_exec. */\n#include \"spy.h\"\n#include <stdlib.h>\n#include <string.h>\n", loader);
    else put(&out, "/* Generated by spyc. Link with %s and the C math library. */\n#include \"spy.h\"\n%s"
                   "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n",
             b.registered.len ? "libspy.a, libspy-std.a," : "libspy.a", b.registered.len ? "#include \"spy-std.h\"\n" : "");
    for (size_t i = 0; i < sources; i++) {
        if (i < entries) put(&out, "%sconst char %s[] = {\n", bare ? "" : "static ", inputs[i]->array);
        else put(&out, "static const char %s[] = { /* %s */\n", inputs[i]->array, inputs[i]->path);
        put_bytes(&out, inputs[i]->source);
    }
    put(&out, "static const struct { const char *name, *source; size_t size; } modules[] = {\n");
    for (size_t i = 0; i < count; i++) {
        Module *m = table[i];
        put(&out, "    {");
        put_string(&out, m->name);
        if (m->kind != MODULE) put(&out, " \"%s\"", m->kind == PACKAGE ? ".__init__" : ".__namespace__");
        put(&out, ", %s, sizeof %s},\n", m->array, m->array);
    }
    put(&out, "    {NULL, NULL, 0}\n};\n");
    put(&out, "/* A SPYModuleLoader over the bundled modules: a malloc copy of the\n"
              " * source the engine asks for by name, or NULL. */\n"
              "%schar *%s(void *data, const char *name) {\n"
              "    size_t low = 0, high = sizeof modules / sizeof *modules - 1;\n"
              "    (void)data;\n"
              "    while (low < high) {\n"
              "        size_t middle = low + (high - low) / 2;\n"
              "        int order = strcmp(name, modules[middle].name);\n"
              "        if (!order) {\n"
              "            char *source = malloc(modules[middle].size);\n"
              "            if (source) memcpy(source, modules[middle].source, modules[middle].size);\n"
              "            return source;\n"
              "        }\n"
              "        if (order < 0) high = middle; else low = middle + 1;\n"
              "    }\n"
              "    return NULL;\n}\n", bare ? "" : "static ", bare ? loader : "load");
    if (!bare) {
        EntryPoint *e = &list[0];
        put(&out, "static int output(void *p, const char *s, size_t n) {\n"
                  "    return fwrite(s, 1, n, (FILE *)p) == n ? 0 : -1;\n}\n"
                  "static int flush_output(void *p) { return fflush((FILE *)p); }\n"
                  "static int global(SPYContext *c, const char *name, const char *text) {\n"
                  "    SPYValue *value = spy_string(c, text, strlen(text));\n"
                  "    int status = !value || spy_set_global(c, name, value);\n"
                  "    spy_release(value);\n"
                  "    return status;\n}\n"
                  "int main(void) {\n"
                  "    SPYContext *c = spy_context_new();\n"
                  "    if (!c) return 1;\n");
        for (size_t i = 0; i < b.registered.len; i++)
            put(&out, "    if (spy_std_init_module(c, \"%s\")) return 1;\n", b.registered.items[i]);
        if (optimize) put(&out, "    spy_set_optimize(c, %d);\n", optimize);
        put(&out, "    spy_set_output(c, output, stdout);\n"
                  "    spy_set_flush(c, flush_output);\n"
                  "    spy_set_module_loader(c, load, NULL);\n"
                  "    int status = global(c, \"__file__\", ");
        put_string(&out, e->file);
        put(&out, ");\n");
        if (e->package) {
            /* As python -m: the package is set, and imported first. */
            put(&out, "    if (!status) status = global(c, \"__package__\", ");
            put_string(&out, e->package);
            put(&out, ");\n");
            if (*e->package) {
                char *import = concat("__import__('", e->package, "')");
                put(&out, "    if (!status) {\n        spy_release(spy_eval(c, ");
                put_string(&out, import);
                put(&out, ", \"<spyc>\"));\n        status = spy_error_type(c)[0] != 0;\n    }\n");
                free(import);
            }
        }
        put(&out, "    if (!status) status = spy_exec(c, source, ");
        put_string(&out, e->file);
        put(&out, ");\n"
                  "    if (status) fprintf(stderr, \"%%s:%%zu: %%s: %%s\\n\",\n"
                  "        spy_error_filename(c), spy_error_line(c), spy_error_type(c), spy_error_display(c));\n"
                  "    spy_context_free(c);\n"
                  "    return status ? 1 : 0;\n}\n");
    }

    if (write_file(output, &out)) { status = 1; goto done; }

    if (metafile) {
        put(&meta, "{\n  \"inputs\": {");
        for (size_t i = 0; i < sources; i++) {
            Module *m = inputs[i];
            put(&meta, "%s\n    ", i ? "," : "");
            put_json(&meta, m->path);
            put(&meta, ": {\"bytes\": %zu, \"imports\": [", m->bytes);
            size_t shown = 0;
            for (size_t j = 0; j < m->imports_len; j++) {
                Import *imp = &m->imports[j];
                if (!strcmp(imp->kind, "maybe")) continue;
                put(&meta, "%s\n      {\"path\": ", shown++ ? "," : "");
                put_json(&meta, imp->path);
                put(&meta, ", \"kind\": \"%s\", \"original\": ", imp->kind);
                put_json(&meta, imp->original);
                put(&meta, "%s}", imp->flag == 1 ? ", \"external\": true" : imp->flag == 2 ? ", \"missing\": true" : "");
            }
            put(&meta, "]}");
        }
        put(&meta, "\n  },\n  \"outputs\": {\n    ");
        put_json(&meta, output);
        put(&meta, ": {\"bytes\": %zu, \"entryPoint\": ", out.len);
        put_json(&meta, list[0].module.path);
        put(&meta, ", \"inputs\": {");
        for (size_t i = 0; i < sources; i++) {
            put(&meta, "%s\n      ", i ? "," : "");
            put_json(&meta, inputs[i]->path);
            put(&meta, ": {\"bytesInOutput\": %zu}", strlen(inputs[i]->source));
        }
        put(&meta, "}}\n  }\n}\n");
        if (write_file(metafile, &meta)) { status = 1; goto done; }
    }
    if (deps) {
        put(&rule, "%s:", output);
        for (size_t i = 0; i < sources; i++) {
            put(&rule, " ");
            for (const char *p = inputs[i]->path; *p; p++) put(&rule, *p == ' ' || *p == '#' ? "\\%c" : *p == '$' ? "$$" : "%c", *p);
        }
        put(&rule, "\n");
        if (write_file(deps, &rule)) { status = 1; goto done; }
    }
    if (analyze) {
        /* The inputs, largest in the output first. */
        qsort(inputs, sources, sizeof(Module *), by_size);
        fprintf(stderr, "  %s  %zu bytes\n", output, out.len);
        for (size_t i = 0; i < sources; i++) fprintf(stderr, "    %s  %zu\n", inputs[i]->path, strlen(inputs[i]->source));
    }
done:
    for (size_t i = 0; list && i < entries; i++) {
        free(list[i].file); free(list[i].package); free(list[i].symbol);
        free_module(&list[i].module);
    }
    for (size_t i = 0; i < b.len; i++) {
        free(b.modules[i]->name); free(b.modules[i]->path);
        free_module(b.modules[i]); free(b.modules[i]);
    }
    free(b.modules); free(b.queue); free(list); free(table); free(inputs); free(loader);
    mem_free(out.data); mem_free(meta.data); mem_free(rule.data);
    free_strings(&b.roots); free_strings(&b.externals); free_strings(&b.registered); free_strings(&b.aliases); free_strings(&b.stars);
    free_strings(&files); free_strings(&mains); free_strings(&includes);
    if (b.c) spy_context_free(b.c);
    return status;
}
