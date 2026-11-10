/* Bundle arbitrary programs with spyc: import discovery, the module search,
 * --minify, and the generated C, metafile, and dependency rule. spyc's
 * main, compiled as spyc_main, runs its Python over this engine. The input
 * is a small tree, split at each line "#--": the entry main.py, then a.py,
 * pkg/__init__.py, and pkg/b.py. The first byte picks the options. */
#define _XOPEN_SOURCE 700
#if defined(__APPLE__)
#define _DARWIN_C_SOURCE
#endif
#include <ftw.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

int spyc_main(int argc, char **argv);

static const char *const files[] = {"main.py", "a.py", "pkg/__init__.py", "pkg/b.py"};

static void write_text(const char *dir, const char *name, const uint8_t *data, size_t size) {
    char path[512];
    snprintf(path, sizeof path, "%s/%s", dir, name);
    FILE *f = fopen(path, "wb");
    if (!f) return;
    fwrite(data, 1, size, f);
    fclose(f);
}

static int remove_entry(const char *path, const struct stat *st, int flag, struct FTW *ftw) {
    (void)st; (void)flag; (void)ftw;
    return remove(path);
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (!size) return 0;
    int options = data[0];
    data++, size--;
    char dir[] = "/tmp/fuzz_spyc.XXXXXX";
    if (!mkdtemp(dir)) return 0;
    char path[512];
    snprintf(path, sizeof path, "%s/pkg", dir);
    mkdir(path, 0700);
    for (size_t i = 0; i < sizeof files / sizeof *files; i++) {
        const uint8_t *cut = NULL;
        for (size_t j = 0; j + 4 <= size && !cut; j++)
            if ((j == 0 || data[j - 1] == '\n') && !memcmp(data + j, "#--", 3) && data[j + 3] == '\n') cut = data + j;
        size_t n = cut && i + 1 < sizeof files / sizeof *files ? (size_t)(cut - data) : size;
        write_text(dir, files[i], data, n);
        data += n, size -= n;
        if (size >= 4) data += 4, size -= 4;
    }
    char entry[512], output[512], meta[512], deps[512];
    snprintf(entry, sizeof entry, "%s/main.py", dir);
    snprintf(output, sizeof output, "%s/out.c", dir);
    snprintf(meta, sizeof meta, "%s/meta.json", dir);
    snprintf(deps, sizeof deps, "%s/out.d", dir);
    char *argv[16] = {"spyc"};
    int argc = 1;
    if (options & 1) argv[argc++] = "--minify";
    argv[argc++] = options & 2 ? "-c" : "-e";
    if (options & 4) argv[argc++] = "-O";
    if (options & 8) argv[argc++] = "-Werror";
    if (options & 16) { argv[argc++] = "-D"; argv[argc++] = "pkg.*"; }
    if (options & 32) { argv[argc++] = "-x"; argv[argc++] = "a"; }
    argv[argc++] = "--metafile"; argv[argc++] = meta;
    argv[argc++] = "--deps"; argv[argc++] = deps;
    argv[argc++] = "-o"; argv[argc++] = output;
    argv[argc++] = entry;
    argv[argc] = NULL;
    /* spyc's output is the fuzzer's noise. */
    FILE *out = freopen("/dev/null", "w", stdout);
    (void)out;
    spyc_main(argc, argv);
    nftw(dir, remove_entry, 8, FTW_DEPTH | FTW_PHYS);
    return 0;
}
