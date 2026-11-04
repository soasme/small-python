package io.github.soasme.spy;

/**
 * The engine's C API (spy.h), one method each, implemented in spy-jni.c.
 * Contexts and values are pointers; a function that fails returns 0 or -1
 * with the context's error set, as its C counterpart does.
 */
final class Native {
    private Native() {}

    static {
        NativeLibrary.load();
    }

    static native String version();
    static native long contextNew(Interpreter rt);
    static native void contextFree(long ctx);
    static native int stdInit(long ctx);
    static native long eval(long ctx, String source, String filename);
    static native int exec(long ctx, String source, String filename);
    static native int execModule(long ctx, long module, String source, String filename);
    static native long getGlobal(long ctx, String name);
    static native int setGlobal(long ctx, String name, long value);
    static native long function(long ctx, String name, HostFunction f);
    static native int newModule(long ctx, String name);
    static native int loadNative(long ctx, String name, String path);
    static native void setOutput(long ctx, boolean on);
    static native void setLoader(long ctx, boolean on);
    static native void setPolicy(long ctx, boolean on);
    static native int policyCheck(long ctx, String event, long args);
    static native int mount(long ctx, String directory, String path, boolean readOnly);
    static native int setLimit(long ctx, int limit, long value);
    static native long getLimit(long ctx, int limit);
    static native long stepsUsed(long ctx);
    static native void setOptimize(long ctx, int level);
    static native long collect(long ctx);

    static native PythonException takeError(long ctx);
    static native boolean errorPending(long ctx);
    static native void raise(long ctx, String type, String message);

    static native long retain(long v);
    static native void release(long v);
    static native int type(long v);
    static native long none(long ctx);
    static native long bool(long ctx, boolean b);
    static native long integer(long ctx, long n);
    static native long real(long ctx, double x);
    static native long string(long ctx, String s);
    static native long bytes(long ctx, byte[] b);
    static native long list(long ctx);
    static native int listAppend(long ctx, long list, long item);
    static native long tuple(long ctx, long[] items);
    static native long dict(long ctx);
    static native long call(long ctx, long f, long[] args, long keywords);
    static native long getItem(long ctx, long v, long key);
    static native int setItem(long ctx, long v, long key, long item);
    static native long getAttr(long ctx, long v, String name);
    static native int setAttr(long ctx, long v, String name, long item);
    static native long iter(long ctx, long v);
    static native long next(long ctx, long v);
    static native long asInt(long ctx, long v);
    static native double asFloat(long ctx, long v);
    static native String asString(long ctx, long v);
    static native byte[] asBytes(long ctx, long v);
    static native int truth(long ctx, long v);
    static native long repr(long ctx, long v);
    static native long str(long ctx, long v);

    // SPYType values PyObject and the conversions read.
    static final int NONE = 0, BOOL = 1, INT = 2, FLOAT = 3, STRING = 4, LIST = 5, TUPLE = 6, DICT = 7, BYTES = 27,
            BYTEARRAY = 36;
}
