/* Run a fuzz target once on each file named, without libFuzzer: a corpus
 * replayed under a sanitizer libFuzzer is not built with, such as
 * MemorySanitizer (make fuzz-replay). */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

int main(int argc, char **argv) {
    for (int i = 1; i < argc; i++) {
        FILE *f = fopen(argv[i], "rb");
        if (!f) { perror(argv[i]); return 1; }
        size_t size = 0, cap = 4096;
        uint8_t *data = malloc(cap);
        for (size_t n; data && (n = fread(data + size, 1, cap - size, f)) > 0;) {
            size += n;
            if (size == cap) {
                uint8_t *grown = realloc(data, cap *= 2);
                if (!grown) free(data);
                data = grown;
            }
        }
        fclose(f);
        if (!data) { fputs("replay: out of memory\n", stderr); return 1; }
        LLVMFuzzerTestOneInput(data, size);
        free(data);
    }
    return 0;
}
