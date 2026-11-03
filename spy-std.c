#include "spy-std.h"
#include "spy-std-modules.h"
#include "spy-module.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#if defined(_WIN32)
#include <windows.h>
#elif !defined(__wasi__)
#include <dlfcn.h>
#endif

static size_t std_find(const char *name) {
    size_t i = 0;
    while (i < sizeof(std_modules) / sizeof(*std_modules) && strcmp(std_modules[i].name, name)) i++;
    return i;
}
/* Run a module's embedded Python source in it; a package also gets __path__.
 * Only standard names are registered with this function, and a module being
 * initialized still has the __name__ the engine created it with. */
static int std_module_init(SPYContext *c, SPYValue *module) {
    SPYValue *name = spy_get_attr(c, module, "__name__");
    const char *text = spy_as_string(c, name, NULL);
    size_t i = std_find(text);
    size_t len = 0;
    for (size_t j = 0; j < std_modules[i].count; j++) len += strlen(std_modules[i].lines[j]);
    char *source = malloc(len + 1), *filename = malloc(strlen(text) + sizeof("<frozen >"));
    int status = -1;
    if (source && filename) {
        char *at = source;
        for (size_t j = 0; j < std_modules[i].count; j++) { size_t n = strlen(std_modules[i].lines[j]); memcpy(at, std_modules[i].lines[j], n); at += n; }
        *at = 0;
        strcpy(filename, "<frozen "); strcat(filename, text); strcat(filename, ">");
        SPYValue *path = std_modules[i].package ? spy_list(c) : NULL;
        status = std_modules[i].package && (!path || spy_set_attr(c, module, "__path__", path)) ? -1 :
            spy_exec_module(c, module, source, filename);
        spy_release(path);
    } else spy_error(c, "MemoryError", "allocation failed");
    free(source); free(filename); spy_release(name);
    return status;
}
/* The standard modules are written on the engine primitives, as _spy. */
int spy_std_init_module(SPYContext *c, const char *name) {
    if (std_find(name) == sizeof(std_modules) / sizeof(*std_modules)) {
        spy_error(c, "ImportError", "no such standard module");
        return -1;
    }
    return spy_new_module(c, "_spy", spy_init_primitives) || spy_new_module(c, name, std_module_init) ? -1 : 0;
}
int spy_std_init(SPYContext *c) {
    for (size_t i = 0; i < sizeof(std_modules) / sizeof(*std_modules); i++)
        if (spy_std_init_module(c, std_modules[i].name)) return -1;
    return 0;
}
/* Report the pending exception through sys.excepthook(type, value,
 * traceback), as CPython's PyErr_Print does (PLS-315 B.4.2). */
int spy_std_report(SPYContext *c) {
    SPYValue *error = spy_error_value(c);
    if (!error) return -1;
    spy_clear_error(c);
    SPYValue *hook = spy_eval(c, "__import__('sys').excepthook", "<excepthook>");
    SPYValue *args[3] = {spy_get_attr(c, error, "__class__"), error, spy_get_attr(c, error, "__traceback__")};
    SPYValue *result = hook && args[0] && args[2] ? spy_call(c, hook, 3, args) : NULL;
    spy_release(result); spy_release(hook); spy_release(args[0]); spy_release(args[2]);
    if (!result) spy_raise(c, error);
    spy_release(error);
    return result ? 0 : -1;
}

/* == Native modules (spy-module.h) == */

#define ENTRY(name) name,
static const SPYModuleAPI module_api = {SPY_MODULE_FUNCTIONS(ENTRY)};
#undef ENTRY

/* Open a shared library, or describe in error why it did not open; find a
 * symbol in it; close it. */
#if defined(_WIN32)
static void *library_open(const char *path, char *error, size_t size) {
    HMODULE library = LoadLibraryA(path);
    DWORD code = GetLastError();
    if (!library && !FormatMessageA(FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS, NULL, code, 0, error, (DWORD)size, NULL))
        snprintf(error, size, "%s: error %lu", path, (unsigned long)code);
    return library;
}
static void *library_symbol(void *library, const char *name) {
    FARPROC symbol = GetProcAddress(library, name);
    void *address;
    memcpy(&address, &symbol, sizeof(address));
    return address;
}
static void library_close(void *library) { FreeLibrary(library); }
#elif !defined(__wasi__)
static void *library_open(const char *path, char *error, size_t size) {
    void *library = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!library) snprintf(error, size, "%s", dlerror());
    return library;
}
static void *library_symbol(void *library, const char *name) { return dlsym(library, name); }
static void library_close(void *library) { dlclose(library); }
#else
static void *library_open(const char *path, char *error, size_t size) {
    (void)path;
    snprintf(error, size, "native modules are not supported on this platform");
    return NULL;
}
static void *library_symbol(void *library, const char *name) { (void)library; (void)name; return NULL; }
static void library_close(void *library) { (void)library; }
#endif

/* A module runs on an engine of its header's major version (minor before
 * 1.0) as new as its header or newer, whose table begins with its own. */
static int compatible(const char *built) {
    unsigned b[3], r[3];
    if (sscanf(built, "%u.%u.%u", &b[0], &b[1], &b[2]) != 3 || sscanf(SPY_VERSION, "%u.%u.%u", &r[0], &r[1], &r[2]) != 3) return 0;
    return b[0] == r[0] && (b[0] || b[1] == r[1]) && (b[1] < r[1] || (b[1] == r[1] && b[2] <= r[2]));
}
/* Hand the library this engine's table, once: a library another engine in
 * the process linked keeps that engine's table and cannot load here. */
static int link_table(SPYModuleLink *link) {
    const SPYModuleAPI *expected = NULL;
#if defined(__GNUC__)
    return __atomic_compare_exchange_n(&link->api, &expected, &module_api, 0, __ATOMIC_ACQ_REL, __ATOMIC_ACQUIRE) || expected == &module_api;
#else
    if (!link->api) link->api = &module_api;
    return link->api == &module_api;
#endif
}
int spy_std_load_native(SPYContext *c, const char *name, const char *path) {
    SPYValue *strings[2] = {spy_string(c, name, strlen(name)), spy_string(c, path, strlen(path))};
    SPYValue *args = strings[0] && strings[1] ? spy_tuple(c, 2, strings) : NULL;
    int status = args ? spy_policy_check(c, "dlopen", args) : -1;
    spy_release(strings[0]); spy_release(strings[1]); spy_release(args);
    if (status) return -1;
    const char *last = strrchr(name, '.');
    last = last ? last + 1 : name;
    char error[512], *export = malloc(strlen(last) + sizeof("spy_init_"));
    if (!export) { spy_error(c, "MemoryError", "allocation failed"); return -1; }
    strcpy(export, "spy_init_"); strcat(export, last);
    void *library = library_open(path, error, sizeof(error));
    SPYModuleLink *link = library ? library_symbol(library, "spy_module") : NULL;
    void *symbol = library ? library_symbol(library, export) : NULL;
    SPYModuleInit init;
    memcpy(&init, &symbol, sizeof(init));
    if (!library) status = -1;
    else if (!link) status = snprintf(error, sizeof(error), "dynamic module does not define spy_module (build it with SPY_SHARED_MODULE)");
    else if (!symbol) status = snprintf(error, sizeof(error), "dynamic module does not define module export function (%s)", export);
    else if (!compatible(link->version)) status = snprintf(error, sizeof(error), "dynamic module was built for spy %s, not %s", link->version, SPY_VERSION);
    else if (!link_table(link)) status = snprintf(error, sizeof(error), "dynamic module is linked to another engine in this process");
    free(export);
    if (status) {
        if (library) library_close(library);
        spy_error(c, "ImportError", error);
        return -1;
    }
    if (spy_new_module(c, name, init)) { library_close(library); return -1; }
    return 0;
}
