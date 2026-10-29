/* A raylib host for Flappy Python. It registers a "raylib" C module, as
 * QuickJS hosts register one with JS_NewCModule, installs the module loader
 * spyc -c -N flappy generated, and runs flappy.py from the bundle. Python,
 * the game's modules, its sprite, and (linked statically) raylib all end up
 * in this one executable. */
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

/* Textures and sounds the game loaded, by the index their load returns. */
static Texture2D textures[8];
static size_t texture_count;
static Sound sounds[8];
static size_t sound_count;

static SPYValue *init_window(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; double w, h; const char *title;
    if (args(c, argc, argv, kw, "nns", &w, &h, &title)) return NULL;
    SetConfigFlags(FLAG_MSAA_4X_HINT | FLAG_VSYNC_HINT);
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
    while (texture_count) UnloadTexture(textures[--texture_count]);
    while (sound_count) UnloadSound(sounds[--sound_count]);
    if (IsAudioDeviceReady()) CloseAudioDevice();
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
static SPYValue *is_key_pressed(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; double key;
    return args(c, argc, argv, kw, "n", &key) ? NULL : spy_bool(c, IsKeyPressed((int)key));
}
static SPYValue *is_mouse_button_pressed(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; double button;
    return args(c, argc, argv, kw, "n", &button) ? NULL : spy_bool(c, IsMouseButtonPressed((int)button));
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
/* load_texture(png): a texture from PNG bytes held in memory. */
static SPYValue *load_texture(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; size_t size;
    if (kw || argc != 1) return spy_error(c, "TypeError", "load_texture takes one bytes argument");
    const unsigned char *png = spy_as_bytes(c, argv[0], &size);
    if (!png) return NULL;
    if (texture_count == sizeof textures / sizeof *textures) return spy_error(c, "RuntimeError", "too many textures");
    Image image = LoadImageFromMemory(".png", png, (int)size);
    if (!image.data) return spy_error(c, "ValueError", "not a PNG image");
    Texture2D texture = LoadTextureFromImage(image);
    UnloadImage(image);
    GenTextureMipmaps(&texture);
    SetTextureFilter(texture, TEXTURE_FILTER_TRILINEAR);
    textures[texture_count] = texture;
    return spy_int(c, (int64_t)texture_count++);
}
/* draw_texture(texture, x, y, height, angle): centered on (x, y), scaled to
 * height, turned angle degrees clockwise. */
static SPYValue *draw_texture(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; double index, x, y, height, angle;
    if (args(c, argc, argv, kw, "nnnnn", &index, &x, &y, &height, &angle)) return NULL;
    if (index < 0 || index >= (double)texture_count) return spy_error(c, "ValueError", "no such texture");
    Texture2D t = textures[(size_t)index];
    float h = (float)height, w = h * (float)t.width / (float)t.height;
    DrawTexturePro(t, (Rectangle){0, 0, (float)t.width, (float)t.height}, (Rectangle){(float)x, (float)y, w, h},
                   (Vector2){w / 2, h / 2}, (float)angle, WHITE);
    return spy_none(c);
}

static SPYValue *init_audio_device(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data;
    if (args(c, argc, argv, kw, "")) return NULL;
    InitAudioDevice();
    return spy_none(c);
}
/* load_sound(pcm, rate): a sound from 16-bit mono samples (little-endian). */
static SPYValue *load_sound(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; size_t size; double rate;
    if (kw || argc != 2) return spy_error(c, "TypeError", "load_sound takes the samples and their rate");
    const unsigned char *pcm = spy_as_bytes(c, argv[0], &size);
    if (!pcm || spy_as_float(c, argv[1], &rate)) return NULL;
    if (sound_count == sizeof sounds / sizeof *sounds) return spy_error(c, "RuntimeError", "too many sounds");
    Wave wave = {(unsigned)(size / 2), (unsigned)rate, 16, 1, (void *)pcm};
    sounds[sound_count] = LoadSoundFromWave(wave);
    return spy_int(c, (int64_t)sound_count++);
}
static SPYValue *play_sound(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {
    (void)data; double index;
    if (args(c, argc, argv, kw, "n", &index)) return NULL;
    if (index < 0 || index >= (double)sound_count) return spy_error(c, "ValueError", "no such sound");
    PlaySound(sounds[(size_t)index]);
    return spy_none(c);
}

static const struct { const char *name; SPYNativeKeywords fn; } functions[] = {
    {"init_window", init_window}, {"set_target_fps", set_target_fps},
    {"window_should_close", window_should_close}, {"close_window", close_window},
    {"get_frame_time", get_frame_time}, {"get_random_value", get_random_value},
    {"is_key_pressed", is_key_pressed}, {"is_mouse_button_pressed", is_mouse_button_pressed},
    {"begin_drawing", begin_drawing}, {"end_drawing", end_drawing},
    {"clear_background", clear_background}, {"draw_rectangle", draw_rectangle},
    {"draw_circle", draw_circle}, {"draw_text", draw_text}, {"measure_text", measure_text},
    {"load_texture", load_texture}, {"draw_texture", draw_texture},
    {"init_audio_device", init_audio_device}, {"load_sound", load_sound}, {"play_sound", play_sound},
};
static const struct { const char *name; int value; } constants[] = {
    {"KEY_SPACE", KEY_SPACE}, {"KEY_UP", KEY_UP}, {"KEY_W", KEY_W},
    {"MOUSE_BUTTON_LEFT", MOUSE_BUTTON_LEFT},
};

static int set_owned(SPYContext *c, SPYValue *module, const char *name, SPYValue *v) {
    int status = !v || spy_set_attr(c, module, name, v);
    spy_release(v);
    return status ? -1 : 0;
}
static int raylib_init(SPYContext *c, SPYValue *module) {
    for (size_t i = 0; i < sizeof(functions) / sizeof(*functions); i++)
        if (set_owned(c, module, functions[i].name, spy_native(c, functions[i].name, functions[i].fn, NULL, NULL))) return -1;
    for (size_t i = 0; i < sizeof(constants) / sizeof(*constants); i++)
        if (set_owned(c, module, constants[i].name, spy_int(c, constants[i].value))) return -1;
    return 0;
}

/* The bundle spyc -c -N flappy writes: the entry's source and a loader
 * for every module it imports. */
extern const char spy_flappy[];
char *flappy_load(void *, const char *);

int main(void) {
    SPYContext *c = spy_context_new();
    if (!c) { fputs("cannot start\n", stderr); return 1; }
    spy_set_output(c, host_output, stdout);
    spy_set_flush(c, host_flush);
    spy_set_module_loader(c, flappy_load, NULL);
    int status = spy_new_module(c, "raylib", raylib_init) || spy_exec(c, spy_flappy, "flappy.py") ? host_exit_status(c) : 0;
    if (IsWindowReady()) CloseWindow();
    spy_context_free(c);
    return status < 0 ? 1 : status;
}
