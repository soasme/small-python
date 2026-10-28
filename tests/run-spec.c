/* The conformance driver, as QuickJS's run-test262: it runs one spec test or
 * TLA replay on the bare core. The test host (tests/spec/harness.py) reaches
 * the host facilities it needs through the engine primitives registered as
 * _spy; no library module is registered, so a test cannot depend on one. */
#include "../spy.h"
#include "../host.h"

int main(int argc, char **argv) {
    if (argc != 2) { fputs("usage: run-spec file.py\n", stderr); return 2; }
    FILE *file = fopen(argv[1], "rb");
    if (!file) { perror(argv[1]); return 1; }
    char *source = host_read(file);
    fclose(file);
    if (!source) { fputs("cannot read source\n", stderr); return 1; }
    SPYContext *c = spy_context_new();
    if (!c) { free(source); return 1; }
    spy_set_output(c, host_output, stdout);
    spy_set_flush(c, host_flush);
    spy_set_input(c, host_read_line, stdin);
    spy_set_module_loader(c, host_load_module, ".");
    SPYValue *name = spy_string(c, argv[1], strlen(argv[1]));
    if (name) spy_set_global(c, "__file__", name);
    spy_release(name);
    int status = spy_new_module(c, "_spy", spy_init_primitives) || spy_mount(c, ".", NULL, 0) ? host_exit_status(c) :
        spy_exec(c, source, argv[1]) ? host_exit_status(c) : 0;
    free(source);
    spy_context_free(c);
    return status < 0 ? 1 : status;
}
