/* A raylib host for Small Python: the game is pong.py, and this file only
 * registers a "raylib" C module, as a QuickJS host would with JS_NewCModule. */
#include "spy.h"
#include "host.h"

#include <raylib.h>
#include <stdarg.h>

/* Convert positional arguments by format: 'n' number (double), 's' string,
 * 'c' color, an (r, g, b) or (r, g, b, a) sequence of integers. */
static int args(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, const char *format, ...) {
    if (kw || argc != strlen(format)) { spy_error(c, "TypeError", "wrong number of arguments"); return -1; }
    va_list out;
    va_start(out, format);
    int status = 0;
    for (size_t i = 0; !status && i < argc; i++) {
        if (format[i] == 'n') status = spy_as_float(c, argv[i], va_arg(out, double *));
        else if (format[i] == 's') status = !(*va_arg(out, const char **) = spy_as_string(c, argv[i], NULL));
        else {
            Color *color = va_arg(out, Color *);
            unsigned char rgba[4] = {0, 0, 0, 255};
            SPYValue *it = spy_iter(c, argv[i]), *v;
            size_t n = 0;
            status = !it;
            while (!status && (v = spy_next(c, it))) {
                int64_t x;
                status = n == 4 || spy_as_int(c, v, &x) || x < 0 || x > 255;
                if (!status) rgba[n++] = (unsigned char)x;
                spy_release(v);
            }
            if (!status && (spy_error_type(c)[0] || n < 3)) status = 1;
            if (status && !spy_error_type(c)[0]) spy_error(c, "ValueError", "color must be 3 or 4 integers in 0..255");
            spy_release(it);
            *color = (Color){rgba[0], rgba[1], rgba[2], rgba[3]};
        }
    }
    va_end(out);
    return status ? -1 : 0;
}

static SPYValue *init_window(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; double w, h; const char *title;
    if (args(c, argc, argv, kw, "nns", &w, &h, &title)) return NULL;
    InitWindow((int)w, (int)h, title);
    return spy_none(c);
}
static SPYValue *set_target_fps(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; double fps;
    if (args(c, argc, argv, kw, "n", &fps)) return NULL;
    SetTargetFPS((int)fps);
    return spy_none(c);
}
static SPYValue *window_should_close(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data;
    return args(c, argc, argv, kw, "") ? NULL : spy_bool(c, WindowShouldClose());
}
static SPYValue *close_window(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data;
    if (args(c, argc, argv, kw, "")) return NULL;
    CloseWindow();
    return spy_none(c);
}
static SPYValue *get_frame_time(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data;
    return args(c, argc, argv, kw, "") ? NULL : spy_float(c, GetFrameTime());
}
static SPYValue *get_random_value(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; double lo, hi;
    return args(c, argc, argv, kw, "nn", &lo, &hi) ? NULL : spy_int(c, GetRandomValue((int)lo, (int)hi));
}
static SPYValue *is_key_down(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; double key;
    return args(c, argc, argv, kw, "n", &key) ? NULL : spy_bool(c, IsKeyDown((int)key));
}
static SPYValue *is_key_pressed(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; double key;
    return args(c, argc, argv, kw, "n", &key) ? NULL : spy_bool(c, IsKeyPressed((int)key));
}
static SPYValue *begin_drawing(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data;
    if (args(c, argc, argv, kw, "")) return NULL;
    BeginDrawing();
    return spy_none(c);
}
static SPYValue *end_drawing(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data;
    if (args(c, argc, argv, kw, "")) return NULL;
    EndDrawing();
    return spy_none(c);
}
static SPYValue *clear_background(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; Color color;
    if (args(c, argc, argv, kw, "c", &color)) return NULL;
    ClearBackground(color);
    return spy_none(c);
}
static SPYValue *draw_rectangle(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; double x, y, w, h; Color color;
    if (args(c, argc, argv, kw, "nnnnc", &x, &y, &w, &h, &color)) return NULL;
    DrawRectangleRec((Rectangle){(float)x, (float)y, (float)w, (float)h}, color);
    return spy_none(c);
}
static SPYValue *draw_circle(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; double x, y, r; Color color;
    if (args(c, argc, argv, kw, "nnnc", &x, &y, &r, &color)) return NULL;
    DrawCircleV((Vector2){(float)x, (float)y}, (float)r, color);
    return spy_none(c);
}
static SPYValue *draw_text(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; const char *text; double x, y, size; Color color;
    if (args(c, argc, argv, kw, "snnnc", &text, &x, &y, &size, &color)) return NULL;
    DrawText(text, (int)x, (int)y, (int)size, color);
    return spy_none(c);
}
static SPYValue *measure_text(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; const char *text; double size;
    return args(c, argc, argv, kw, "sn", &text, &size) ? NULL : spy_int(c, MeasureText(text, (int)size));
}

static const struct { const char *name; SPYNativeKeywords fn; } functions[] = {
    {"init_window", init_window}, {"set_target_fps", set_target_fps},
    {"window_should_close", window_should_close}, {"close_window", close_window},
    {"get_frame_time", get_frame_time}, {"get_random_value", get_random_value},
    {"is_key_down", is_key_down}, {"is_key_pressed", is_key_pressed},
    {"begin_drawing", begin_drawing}, {"end_drawing", end_drawing},
    {"clear_background", clear_background}, {"draw_rectangle", draw_rectangle},
    {"draw_circle", draw_circle}, {"draw_text", draw_text}, {"measure_text", measure_text},
};
static const struct { const char *name; int value; } keys[] = {
    {"KEY_W", KEY_W}, {"KEY_S", KEY_S}, {"KEY_UP", KEY_UP}, {"KEY_DOWN", KEY_DOWN},
    {"KEY_SPACE", KEY_SPACE}, {"KEY_P", KEY_P},
};

static int set_owned(SPYContext *c, SPYValue *module, const char *name, SPYValue *v) {
    int status = !v || spy_set_attr(c, module, name, v);
    spy_release(v);
    return status ? -1 : 0;
}
static int raylib_init(SPYContext *c, SPYValue *module) {
    for (size_t i = 0; i < sizeof(functions) / sizeof(*functions); i++)
        if (set_owned(c, module, functions[i].name, spy_native(c, functions[i].name, functions[i].fn, NULL, NULL))) return -1;
    for (size_t i = 0; i < sizeof(keys) / sizeof(*keys); i++)
        if (set_owned(c, module, keys[i].name, spy_int(c, keys[i].value))) return -1;
    return 0;
}

int main(int argc, char **argv) {
    const char *filename = argc > 1 ? argv[1] : "pong.py";
    FILE *file = fopen(filename, "rb");
    if (!file) { perror(filename); return 1; }
    char *source = host_read(file);
    fclose(file);
    SPYContext *c = source ? spy_context_new() : NULL;
    if (!c) { free(source); fputs("cannot start\n", stderr); return 1; }
    spy_set_output(c, host_output, stdout);
    spy_set_flush(c, host_flush);
    int status = spy_new_module(c, "raylib", raylib_init) || spy_exec(c, source, filename) ? host_exit_status(c) : 0;
    if (IsWindowReady()) CloseWindow();
    free(source);
    spy_context_free(c);
    return status < 0 ? 1 : status;
}
