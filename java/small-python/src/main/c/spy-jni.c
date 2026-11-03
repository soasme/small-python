/* The JNI side of io.github.soasme.spy: the engine's C API, one native
 * method of Native.java each, and the engine's callbacks, which call the
 * owning Interpreter's methods. Values cross as jlong pointers; strings cross as
 * UTF-16, converted here to the engine's UTF-8, where a lone surrogate has
 * its three-byte form (CPython's surrogatepass). */
#include <jni.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "spy.h"
#include "spy-std.h"

#define PTR(x) ((SPYValue *)(intptr_t)(x))
#define CTX(x) ((SPYContext *)(intptr_t)(x))
#define J(p) ((jlong)(intptr_t)(p))
/* The SPYType values Native.java names. */
_Static_assert(SPY_DICT == 7 && SPY_BYTES == 27 && SPY_BYTEARRAY == 36, "update Native.java");

#define NATIVE(name) JNICALL Java_io_github_soasme_spy_Native_##name

static JavaVM *vm;
static jmethodID m_call, m_init, m_write, m_load, m_policy;
static jclass c_exception;
static jmethodID m_exception;

static JNIEnv *env_now(void) {
    JNIEnv *env = NULL;
    (*vm)->GetEnv(vm, (void **)&env, JNI_VERSION_1_8);
    return env;
}

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM *jvm, void *reserved) {
    (void)reserved;
    vm = jvm;
    JNIEnv *env = env_now();
    jclass rt = (*env)->FindClass(env, "io/github/soasme/spy/Interpreter");
    jclass e = (*env)->FindClass(env, "io/github/soasme/spy/PythonException");
    if (!rt || !e) return JNI_ERR;
    m_call = (*env)->GetMethodID(env, rt, "callHost", "(Lio/github/soasme/spy/HostFunction;[JJ)J");
    m_init = (*env)->GetMethodID(env, rt, "initModule", "(J)I");
    m_write = (*env)->GetMethodID(env, rt, "write", "(Ljava/lang/String;)I");
    m_load = (*env)->GetMethodID(env, rt, "load", "(Ljava/lang/String;)Ljava/lang/String;");
    m_policy = (*env)->GetMethodID(env, rt, "policy", "(Ljava/lang/String;J)I");
    c_exception = (*env)->NewGlobalRef(env, e);
    m_exception = (*env)->GetMethodID(env, e, "<init>", "(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;J)V");
    if (!m_call || !m_init || !m_write || !m_load || !m_policy || !c_exception || !m_exception) return JNI_ERR;
    return JNI_VERSION_1_8;
}

/* == Strings == */

/* UTF-8 of a Java string, NUL-terminated, with its length in *n; NULL when
 * memory runs out, with OutOfMemoryError thrown. */
static char *utf8(JNIEnv *env, jstring s, size_t *n) {
    jsize len = (*env)->GetStringLength(env, s);
    const jchar *u = (*env)->GetStringChars(env, s, NULL);
    char *out = u ? malloc((size_t)len * 3 + 1) : NULL;
    size_t k = 0;
    for (jsize i = 0; out && i < len; i++) {
        uint32_t c = u[i];
        if (c >= 0xd800 && c < 0xdc00 && i + 1 < len && u[i + 1] >= 0xdc00 && u[i + 1] < 0xe000)
            c = 0x10000 + ((c - 0xd800) << 10) + (u[++i] - 0xdc00);
        if (c < 0x80) out[k++] = (char)c;
        else if (c < 0x800) {
            out[k++] = (char)(0xc0 | c >> 6);
            out[k++] = (char)(0x80 | (c & 0x3f));
        } else if (c < 0x10000) {
            out[k++] = (char)(0xe0 | c >> 12);
            out[k++] = (char)(0x80 | (c >> 6 & 0x3f));
            out[k++] = (char)(0x80 | (c & 0x3f));
        } else {
            out[k++] = (char)(0xf0 | c >> 18);
            out[k++] = (char)(0x80 | (c >> 12 & 0x3f));
            out[k++] = (char)(0x80 | (c >> 6 & 0x3f));
            out[k++] = (char)(0x80 | (c & 0x3f));
        }
    }
    if (u) (*env)->ReleaseStringChars(env, s, u);
    if (!out) {
        if (!(*env)->ExceptionCheck(env))
            (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/OutOfMemoryError"), "cannot convert a string");
        return NULL;
    }
    out[k] = 0;
    if (n) *n = k;
    return out;
}

/* A Java string of the engine's UTF-8, whose sequences the engine made. */
static jstring utf16(JNIEnv *env, const char *s, size_t n) {
    jchar *u = malloc((n ? n : 1) * sizeof(jchar));
    if (!u) return NULL;
    const unsigned char *p = (const unsigned char *)s, *end = p + n;
    jsize k = 0;
    while (p < end) {
        uint32_t c = *p++;
        int more = c >= 0xf0 ? 3 : c >= 0xe0 ? 2 : c >= 0xc0 ? 1 : 0;
        c &= more ? 0x3f >> more : 0x7f;
        while (more-- && p < end) c = c << 6 | (*p++ & 0x3f);
        if (c >= 0x10000) {
            u[k++] = (jchar)(0xd800 + ((c - 0x10000) >> 10));
            c = 0xdc00 + ((c - 0x10000) & 0x3ff);
        }
        u[k++] = (jchar)c;
    }
    jstring out = (*env)->NewString(env, u, k);
    free(u);
    return out;
}

/* NULL-safe utf8 for the optional strings of the API. */
static char *utf8_or_null(JNIEnv *env, jstring s) {
    return s ? utf8(env, s, NULL) : NULL;
}

/* == Callbacks == */

static jobject runtime_of(SPYContext *c) {
    return (jobject)spy_get_opaque(c);
}

/* Whether a callback threw instead of returning, which Interpreter's methods
 * never do short of an Error such as OutOfMemoryError: the exception is
 * cleared and raised in the engine as RuntimeError. */
static int threw(JNIEnv *env, SPYContext *c) {
    if (!(*env)->ExceptionCheck(env)) return 0;
    (*env)->ExceptionClear(env);
    spy_error(c, "RuntimeError", "a Java callback failed");
    return 1;
}

static SPYValue *call(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *keywords, void *f) {
    JNIEnv *env = env_now();
    jlongArray args = (*env)->NewLongArray(env, (jsize)argc);
    if (!args) return threw(env, c), NULL;
    for (size_t i = 0; i < argc; i++) {
        jlong a = J(argv[i]);
        (*env)->SetLongArrayRegion(env, args, (jsize)i, 1, &a);
    }
    jlong result = (*env)->CallLongMethod(env, runtime_of(c), m_call, (jobject)f, args, J(keywords));
    (*env)->DeleteLocalRef(env, args);
    return threw(env, c) ? NULL : PTR(result);
}

static void release(void *f) {
    (*env_now())->DeleteGlobalRef(env_now(), (jobject)f);
}

static int init_module(SPYContext *c, SPYValue *module) {
    JNIEnv *env = env_now();
    jint status = (*env)->CallIntMethod(env, runtime_of(c), m_init, J(module));
    return threw(env, c) ? -1 : status;
}

static int write_output(SPYContext *c, void *data, const char *text, size_t n) {
    (void)data;
    JNIEnv *env = env_now();
    jstring s = utf16(env, text, n);
    if (!s) return threw(env, c), -1;
    jint status = (*env)->CallIntMethod(env, runtime_of(c), m_write, s);
    (*env)->DeleteLocalRef(env, s);
    return threw(env, c) ? -1 : status;
}

static SPYValue *load_module(SPYContext *c, void *data, const char *name) {
    (void)data;
    JNIEnv *env = env_now();
    jstring s = utf16(env, name, strlen(name));
    if (!s) return threw(env, c), NULL;
    jstring source = (*env)->CallObjectMethod(env, runtime_of(c), m_load, s);
    (*env)->DeleteLocalRef(env, s);
    if (threw(env, c) || !source) return NULL;
    size_t n;
    char *text = utf8(env, source, &n);
    (*env)->DeleteLocalRef(env, source);
    if (!text) return threw(env, c), NULL;
    SPYValue *v = spy_bytes(c, text, n);
    free(text);
    return v;
}

static int check_policy(SPYContext *c, void *data, const char *event, SPYValue *args) {
    (void)data;
    JNIEnv *env = env_now();
    jstring s = utf16(env, event, strlen(event));
    if (!s) return threw(env, c), -1;
    jint status = (*env)->CallIntMethod(env, runtime_of(c), m_policy, s, J(args));
    (*env)->DeleteLocalRef(env, s);
    return threw(env, c) ? -1 : status;
}

/* == Contexts == */

JNIEXPORT jstring NATIVE(version)(JNIEnv *env, jclass cls) {
    (void)cls;
    return (*env)->NewStringUTF(env, spy_version());
}

JNIEXPORT jlong NATIVE(contextNew)(JNIEnv *env, jclass cls, jobject rt) {
    (void)cls;
    SPYContext *c = spy_context_new();
    jobject ref = c ? (*env)->NewWeakGlobalRef(env, rt) : NULL;
    if (!ref) {
        spy_context_free(c);
        return 0;
    }
    spy_set_opaque(c, ref);
    return J(c);
}

JNIEXPORT void NATIVE(contextFree)(JNIEnv *env, jclass cls, jlong ctx) {
    (void)cls;
    jobject ref = runtime_of(CTX(ctx));
    spy_context_free(CTX(ctx));
    (*env)->DeleteWeakGlobalRef(env, ref);
}

JNIEXPORT jint NATIVE(stdInit)(JNIEnv *env, jclass cls, jlong ctx) {
    (void)env, (void)cls;
    return spy_std_init(CTX(ctx));
}

JNIEXPORT jlong NATIVE(eval)(JNIEnv *env, jclass cls, jlong ctx, jstring source, jstring filename) {
    (void)cls;
    char *s = utf8(env, source, NULL), *f = s ? utf8(env, filename, NULL) : NULL;
    SPYValue *v = f ? spy_eval(CTX(ctx), s, f) : NULL;
    free(s), free(f);
    return J(v);
}

JNIEXPORT jint NATIVE(exec)(JNIEnv *env, jclass cls, jlong ctx, jstring source, jstring filename) {
    (void)cls;
    char *s = utf8(env, source, NULL), *f = s ? utf8(env, filename, NULL) : NULL;
    int status = f ? spy_exec(CTX(ctx), s, f) : -1;
    free(s), free(f);
    return status;
}

JNIEXPORT jint NATIVE(execModule)(JNIEnv *env, jclass cls, jlong ctx, jlong module, jstring source, jstring filename) {
    (void)cls;
    char *s = utf8(env, source, NULL), *f = s ? utf8(env, filename, NULL) : NULL;
    int status = f ? spy_exec_module(CTX(ctx), PTR(module), s, f) : -1;
    free(s), free(f);
    return status;
}

JNIEXPORT jlong NATIVE(getGlobal)(JNIEnv *env, jclass cls, jlong ctx, jstring name) {
    (void)cls;
    char *n = utf8(env, name, NULL);
    SPYValue *v = n ? spy_get_global(CTX(ctx), n) : NULL;
    free(n);
    return J(v);
}

JNIEXPORT jint NATIVE(setGlobal)(JNIEnv *env, jclass cls, jlong ctx, jstring name, jlong v) {
    (void)cls;
    char *n = utf8(env, name, NULL);
    int status = n ? spy_set_global(CTX(ctx), n, PTR(v)) : -1;
    free(n);
    return status;
}

JNIEXPORT jlong NATIVE(function)(JNIEnv *env, jclass cls, jlong ctx, jstring name, jobject f) {
    (void)cls;
    char *n = utf8(env, name, NULL);
    jobject ref = n ? (*env)->NewGlobalRef(env, f) : NULL;
    SPYValue *v = ref ? spy_native(CTX(ctx), n, call, ref, release) : NULL;
    free(n);
    return J(v);
}

JNIEXPORT jint NATIVE(newModule)(JNIEnv *env, jclass cls, jlong ctx, jstring name) {
    (void)cls;
    char *n = utf8(env, name, NULL);
    int status = n ? spy_new_module(CTX(ctx), n, init_module) : -1;
    free(n);
    return status;
}

JNIEXPORT void NATIVE(setOutput)(JNIEnv *env, jclass cls, jlong ctx, jboolean on) {
    (void)env, (void)cls;
    spy_set_output(CTX(ctx), on ? write_output : NULL, NULL, NULL);
}

JNIEXPORT void NATIVE(setLoader)(JNIEnv *env, jclass cls, jlong ctx, jboolean on) {
    (void)env, (void)cls;
    spy_set_module_loader(CTX(ctx), on ? load_module : NULL, NULL);
}

JNIEXPORT void NATIVE(setPolicy)(JNIEnv *env, jclass cls, jlong ctx, jboolean on) {
    (void)env, (void)cls;
    spy_set_policy(CTX(ctx), on ? check_policy : NULL, NULL);
}

JNIEXPORT jint NATIVE(policyCheck)(JNIEnv *env, jclass cls, jlong ctx, jstring event, jlong args) {
    (void)cls;
    char *e = utf8(env, event, NULL);
    int status = e ? spy_policy_check(CTX(ctx), e, PTR(args)) : -1;
    free(e);
    return status;
}

JNIEXPORT jint NATIVE(mount)(JNIEnv *env, jclass cls, jlong ctx, jstring directory, jstring path, jboolean readOnly) {
    (void)cls;
    char *d = utf8(env, directory, NULL), *p = d ? utf8_or_null(env, path) : NULL;
    int status = d && (p || !path) ? spy_mount(CTX(ctx), d, p, readOnly ? SPY_MOUNT_READ_ONLY : 0) : -1;
    free(d), free(p);
    return status;
}

JNIEXPORT jint NATIVE(setLimit)(JNIEnv *env, jclass cls, jlong ctx, jint limit, jlong value) {
    (void)env, (void)cls;
    return spy_set_limit(CTX(ctx), limit, (size_t)value);
}

JNIEXPORT jlong NATIVE(getLimit)(JNIEnv *env, jclass cls, jlong ctx, jint limit) {
    (void)env, (void)cls;
    return (jlong)spy_get_limit(CTX(ctx), limit);
}

JNIEXPORT jlong NATIVE(stepsUsed)(JNIEnv *env, jclass cls, jlong ctx) {
    (void)env, (void)cls;
    return (jlong)spy_steps_used(CTX(ctx));
}

JNIEXPORT void NATIVE(setOptimize)(JNIEnv *env, jclass cls, jlong ctx, jint level) {
    (void)env, (void)cls;
    spy_set_optimize(CTX(ctx), level);
}

JNIEXPORT jlong NATIVE(collect)(JNIEnv *env, jclass cls, jlong ctx) {
    (void)env, (void)cls;
    return (jlong)spy_collect(CTX(ctx));
}

/* == Errors == */

/* The pending error as a PythonException, which clears it. */
JNIEXPORT jobject NATIVE(takeError)(JNIEnv *env, jclass cls, jlong ctx) {
    (void)cls;
    SPYContext *c = CTX(ctx);
    const char *type = spy_error_type(c), *file = spy_error_filename(c);
    jstring t = utf16(env, *type ? type : "SystemError", strlen(*type ? type : "SystemError"));
    jstring f = t ? utf16(env, file, strlen(file)) : NULL;
    const char *display = spy_error_display(c);
    jstring m = f ? utf16(env, display, strlen(display)) : NULL;
    jobject e = m ? (*env)->NewObject(env, c_exception, m_exception, t, m, f, (jlong)spy_error_line(c)) : NULL;
    spy_clear_error(c);
    return e;
}

JNIEXPORT jboolean NATIVE(errorPending)(JNIEnv *env, jclass cls, jlong ctx) {
    (void)env, (void)cls;
    return *spy_error_type(CTX(ctx)) != 0;
}

JNIEXPORT void NATIVE(raise)(JNIEnv *env, jclass cls, jlong ctx, jstring type, jstring message) {
    (void)cls;
    char *t = utf8(env, type, NULL), *m = t ? utf8(env, message, NULL) : NULL;
    spy_error(CTX(ctx), m ? t : "MemoryError", m ? m : "cannot raise the exception");
    free(t), free(m);
}

/* == Values == */

JNIEXPORT jlong NATIVE(retain)(JNIEnv *env, jclass cls, jlong v) {
    (void)env, (void)cls;
    return J(spy_retain(PTR(v)));
}

JNIEXPORT void NATIVE(release)(JNIEnv *env, jclass cls, jlong v) {
    (void)env, (void)cls;
    spy_release(PTR(v));
}

JNIEXPORT jint NATIVE(type)(JNIEnv *env, jclass cls, jlong v) {
    (void)env, (void)cls;
    return spy_type(PTR(v));
}

JNIEXPORT jlong NATIVE(none)(JNIEnv *env, jclass cls, jlong ctx) {
    (void)env, (void)cls;
    return J(spy_none(CTX(ctx)));
}

JNIEXPORT jlong NATIVE(bool)(JNIEnv *env, jclass cls, jlong ctx, jboolean b) {
    (void)env, (void)cls;
    return J(spy_bool(CTX(ctx), b));
}

JNIEXPORT jlong NATIVE(integer)(JNIEnv *env, jclass cls, jlong ctx, jlong n) {
    (void)env, (void)cls;
    return J(spy_int(CTX(ctx), n));
}

JNIEXPORT jlong NATIVE(real)(JNIEnv *env, jclass cls, jlong ctx, jdouble x) {
    (void)env, (void)cls;
    return J(spy_float(CTX(ctx), x));
}

JNIEXPORT jlong NATIVE(string)(JNIEnv *env, jclass cls, jlong ctx, jstring s) {
    (void)cls;
    size_t n;
    char *text = utf8(env, s, &n);
    SPYValue *v = text ? spy_string(CTX(ctx), text, n) : NULL;
    free(text);
    return J(v);
}

JNIEXPORT jlong NATIVE(bytes)(JNIEnv *env, jclass cls, jlong ctx, jbyteArray b) {
    (void)cls;
    jsize n = (*env)->GetArrayLength(env, b);
    jbyte *data = (*env)->GetByteArrayElements(env, b, NULL);
    SPYValue *v = data ? spy_bytes(CTX(ctx), data, (size_t)n) : NULL;
    if (data) (*env)->ReleaseByteArrayElements(env, b, data, JNI_ABORT);
    return J(v);
}

JNIEXPORT jlong NATIVE(list)(JNIEnv *env, jclass cls, jlong ctx) {
    (void)env, (void)cls;
    return J(spy_list(CTX(ctx)));
}

JNIEXPORT jint NATIVE(listAppend)(JNIEnv *env, jclass cls, jlong ctx, jlong list, jlong item) {
    (void)env, (void)cls;
    return spy_list_append(CTX(ctx), PTR(list), PTR(item));
}

/* The pointers of a long[], or NULL with OutOfMemoryError thrown. */
static SPYValue **pointers(JNIEnv *env, jlongArray a, jsize *n) {
    *n = (*env)->GetArrayLength(env, a);
    SPYValue **items = malloc(((size_t)*n + 1) * sizeof *items);
    jlong *p = items ? (*env)->GetLongArrayElements(env, a, NULL) : NULL;
    if (!p) {
        free(items);
        if (!(*env)->ExceptionCheck(env))
            (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/OutOfMemoryError"), "cannot pass the arguments");
        return NULL;
    }
    for (jsize i = 0; i < *n; i++) items[i] = PTR(p[i]);
    (*env)->ReleaseLongArrayElements(env, a, p, JNI_ABORT);
    return items;
}

JNIEXPORT jlong NATIVE(tuple)(JNIEnv *env, jclass cls, jlong ctx, jlongArray items) {
    (void)cls;
    jsize n;
    SPYValue **p = pointers(env, items, &n), *v = p ? spy_tuple(CTX(ctx), (size_t)n, p) : NULL;
    free(p);
    return J(v);
}

JNIEXPORT jlong NATIVE(dict)(JNIEnv *env, jclass cls, jlong ctx) {
    (void)env, (void)cls;
    return J(spy_dict(CTX(ctx)));
}

JNIEXPORT jlong NATIVE(call)(JNIEnv *env, jclass cls, jlong ctx, jlong f, jlongArray args, jlong keywords) {
    (void)cls;
    jsize n;
    SPYValue **p = pointers(env, args, &n);
    SPYValue *v = p ? spy_call_keywords(CTX(ctx), PTR(f), (size_t)n, p, PTR(keywords)) : NULL;
    free(p);
    return J(v);
}

JNIEXPORT jlong NATIVE(getItem)(JNIEnv *env, jclass cls, jlong ctx, jlong v, jlong key) {
    (void)env, (void)cls;
    return J(spy_get_item(CTX(ctx), PTR(v), PTR(key)));
}

JNIEXPORT jint NATIVE(setItem)(JNIEnv *env, jclass cls, jlong ctx, jlong v, jlong key, jlong item) {
    (void)env, (void)cls;
    return spy_set_item(CTX(ctx), PTR(v), PTR(key), PTR(item));
}

JNIEXPORT jlong NATIVE(getAttr)(JNIEnv *env, jclass cls, jlong ctx, jlong v, jstring name) {
    (void)cls;
    char *n = utf8(env, name, NULL);
    SPYValue *r = n ? spy_get_attr(CTX(ctx), PTR(v), n) : NULL;
    free(n);
    return J(r);
}

JNIEXPORT jint NATIVE(setAttr)(JNIEnv *env, jclass cls, jlong ctx, jlong v, jstring name, jlong item) {
    (void)cls;
    char *n = utf8(env, name, NULL);
    int status = n ? spy_set_attr(CTX(ctx), PTR(v), n, PTR(item)) : -1;
    free(n);
    return status;
}

JNIEXPORT jlong NATIVE(iter)(JNIEnv *env, jclass cls, jlong ctx, jlong v) {
    (void)env, (void)cls;
    return J(spy_iter(CTX(ctx), PTR(v)));
}

JNIEXPORT jlong NATIVE(next)(JNIEnv *env, jclass cls, jlong ctx, jlong v) {
    (void)env, (void)cls;
    return J(spy_next(CTX(ctx), PTR(v)));
}

JNIEXPORT jlong NATIVE(asInt)(JNIEnv *env, jclass cls, jlong ctx, jlong v) {
    (void)env, (void)cls;
    int64_t n = 0;
    spy_as_int(CTX(ctx), PTR(v), &n);
    return n;
}

JNIEXPORT jdouble NATIVE(asFloat)(JNIEnv *env, jclass cls, jlong ctx, jlong v) {
    (void)env, (void)cls;
    double x = 0;
    spy_as_float(CTX(ctx), PTR(v), &x);
    return x;
}

JNIEXPORT jstring NATIVE(asString)(JNIEnv *env, jclass cls, jlong ctx, jlong v) {
    (void)cls;
    size_t n;
    const char *s = spy_as_string(CTX(ctx), PTR(v), &n);
    return s ? utf16(env, s, n) : NULL;
}

JNIEXPORT jbyteArray NATIVE(asBytes)(JNIEnv *env, jclass cls, jlong ctx, jlong v) {
    (void)cls;
    size_t n;
    const unsigned char *b = spy_as_bytes(CTX(ctx), PTR(v), &n);
    jbyteArray out = b ? (*env)->NewByteArray(env, (jsize)n) : NULL;
    if (out) (*env)->SetByteArrayRegion(env, out, 0, (jsize)n, (const jbyte *)b);
    return out;
}

JNIEXPORT jint NATIVE(truth)(JNIEnv *env, jclass cls, jlong ctx, jlong v) {
    (void)env, (void)cls;
    return spy_truth(CTX(ctx), PTR(v));
}

JNIEXPORT jlong NATIVE(repr)(JNIEnv *env, jclass cls, jlong ctx, jlong v) {
    (void)env, (void)cls;
    return J(spy_repr(CTX(ctx), PTR(v)));
}

JNIEXPORT jlong NATIVE(str)(JNIEnv *env, jclass cls, jlong ctx, jlong v) {
    (void)env, (void)cls;
    return J(spy_str(CTX(ctx), PTR(v)));
}
