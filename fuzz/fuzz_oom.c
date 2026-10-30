/* Run arbitrary source with one allocation failing, as tests/oom does for
 * each allocation of a fixed set of programs: the first two bytes pick which
 * of the allocations the program makes after context creation fails, the
 * rest is the program. Every run must end cleanly and free everything it
 * allocated. */
#define main oom_main
#include "../tests/oom.c"
#undef main

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    static size_t from;
    int status;
    if (!from) { fail = 0; from = run("", "<empty>", &status); }
    if (size < 2) return 0;
    char *source = malloc(size - 1);
    if (!source) return 0;
    memcpy(source, data + 2, size - 2);
    source[size - 2] = 0;
    fail = 0;
    size_t total = run(source, "<fuzz>", &status);
    if (total > from) {
        fail = from + 1 + (data[0] | (size_t)data[1] << 8) % (total - from);
        run(source, "<fuzz>", &status);
    }
    free(source);
    return 0;
}
