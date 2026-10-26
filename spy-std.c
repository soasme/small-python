#include "spy-std.h"
#include "spy-std-modules.h"

#include <stdlib.h>
#include <string.h>

static size_t std_find(const char *name) {
    size_t i = 0;
    while (i < sizeof(std_modules) / sizeof(*std_modules) && strcmp(std_modules[i].name, name)) i++;
    return i;
}
/* Run a module's embedded Python source in it; a package also gets __path__. */
static int std_module_init(SPYContext *c, SPYValue *module) {
    SPYValue *name = spy_get_attr(c, module, "__name__");
    const char *text = name ? spy_as_string(c, name, NULL) : NULL;
    size_t i = text ? std_find(text) : sizeof(std_modules) / sizeof(*std_modules);
    if (i == sizeof(std_modules) / sizeof(*std_modules)) {
        spy_release(name);
        if (!spy_error_type(c)[0]) spy_error(c, "ImportError", "unknown standard module");
        return -1;
    }
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
int spy_std_init_module(SPYContext *c, const char *name) {
    if (std_find(name) == sizeof(std_modules) / sizeof(*std_modules)) {
        spy_error(c, "ImportError", "no such standard module");
        return -1;
    }
    return spy_new_module(c, name, std_module_init);
}
int spy_std_init(SPYContext *c) {
    for (size_t i = 0; i < sizeof(std_modules) / sizeof(*std_modules); i++)
        if (spy_new_module(c, std_modules[i].name, std_module_init)) return -1;
    return 0;
}
