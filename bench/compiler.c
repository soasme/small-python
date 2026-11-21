/* Compile separately from executing a reusable code object. Development only. */
#include "../spy.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static int discard(SPYContext *c, void *data, const char *s, size_t n) {
    (void)c; (void)data; (void)s; (void)n;
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 4 || (strcmp(argv[1], "compile") && strcmp(argv[1], "execute"))) {
        fprintf(stderr, "usage: %s compile|execute SOURCE ITERATIONS\n", argv[0]);
        return 2;
    }
    char *end;
    errno = 0;
    unsigned long iterations = strtoul(argv[3], &end, 10);
    if (errno || !iterations || *end || argv[3][0] == '-') return 2;
    FILE *file = fopen(argv[2], "rb");
    if (!file) { perror(argv[2]); return 1; }
    if (fseek(file, 0, SEEK_END)) { fclose(file); return 1; }
    long length = ftell(file);
    if (length < 0 || length > 32 * 1024 * 1024 || fseek(file, 0, SEEK_SET)) { fclose(file); return 1; }
    char *source = malloc((size_t)length + 1);
    if (!source) { fclose(file); return 1; }
    size_t read = fread(source, 1, (size_t)length, file);
    int failed = ferror(file);
    if (fclose(file)) failed = 1;
    if (read != (size_t)length || failed) { free(source); return 1; }
    source[length] = 0;
    SPYContext *c = spy_context_new();
    if (!c) { free(source); return 1; }
    spy_set_output(c, discard, NULL, NULL);
    SPYValue *compiler = spy_eval(c, "compile", "<bench>");
    SPYValue *executor = compiler ? spy_eval(c, "exec", "<bench>") : NULL;
    SPYValue *args[] = {spy_string(c, source, (size_t)length),
                       spy_string(c, argv[2], strlen(argv[2])), spy_string(c, "exec", 4)};
    free(source);
    SPYValue *code = executor && args[0] && args[1] && args[2] ? spy_call(c, compiler, 3, args) : NULL;
    SPYValue *globals = code ? spy_eval(c, "{}", "<bench>") : NULL;
    SPYValue *run_args[] = {code, globals};
    /* Warm up module instruction generation, and validate the program before timing. */
    SPYValue *value = globals ? spy_call(c, executor, 2, run_args) : NULL;
    int status = !value;
    spy_release(value);
    clock_t begin = clock(), finish = begin;
    if (begin == (clock_t)-1) status = 1;
    for (unsigned long i = 0; !status && i < iterations; i++) {
        value = !strcmp(argv[1], "compile") ? spy_call(c, compiler, 3, args) : spy_call(c, executor, 2, run_args);
        status = !value;
        spy_release(value);
    }
    finish = clock();
    if (finish == (clock_t)-1) status = 1;
    if (status) fprintf(stderr, "%s: %s\n", spy_error_type(c), spy_error_message(c));
    else printf("%.9f\n", (double)(finish - begin) / CLOCKS_PER_SEC / iterations);
    spy_release(globals); spy_release(code);
    for (size_t i = 0; i < 3; i++) spy_release(args[i]);
    spy_release(executor); spy_release(compiler);
    spy_context_free(c);
    return status;
}
