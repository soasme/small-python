package io.github.soasme.spy;

import java.io.IOException;
import java.lang.ref.Cleaner;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentLinkedQueue;

/**
 * One independent Small Python engine context, in this process.
 *
 * <pre>{@code
 * try (Interpreter rt = Interpreter.create()) {
 *     rt.define("add", (r, args) -> args.get(0, Long.class) + args.get(1, Long.class));
 *     long n = rt.eval("add(40, 2)").as(Long.class); // 42
 * }
 * }</pre>
 *
 * <p>The engine runs in the Java process, so it is only as trustworthy as its
 * C code: use it for code you trust, and the {@code small-python-worker}
 * artifact for any other. Operations on a runtime and its values are
 * serialized on the runtime; a host function runs on the thread that
 * called into the engine and may call back into it. Closing frees the
 * context; later operations throw {@link IllegalStateException}.
 */
public final class Interpreter implements AutoCloseable {
    static final Cleaner CLEANER = Cleaner.create();

    private volatile long ctx;
    private Appendable output = System.out;
    private ModuleLoader loader;
    private Policy policy;
    private final Map<String, ModuleInit> modules = new HashMap<>();
    // The callbacks below that are running: the engine is running beneath them.
    private int callbacks;
    // Values the garbage collector found unreachable, released on the next call.
    private final ConcurrentLinkedQueue<Long> released = new ConcurrentLinkedQueue<>();

    private Interpreter(boolean std) {
        ctx = Native.contextNew(this);
        if (ctx == 0) {
            throw new PythonException("MemoryError", "cannot create a context");
        }
        Native.setOutput(ctx, true);
        if (std && Native.stdInit(ctx) != 0) {
            PythonException e = Native.takeError(ctx);
            close();
            throw e;
        }
    }

    /** A runtime with the standard module {@code sys}. */
    public static Interpreter create() {
        return new Interpreter(true);
    }

    /** A runtime with only the language core and its builtins. */
    public static Interpreter createBare() {
        return new Interpreter(false);
    }

    /** The engine version. */
    public static String version() {
        return Native.version();
    }

    /**
     * Frees the context and every value in it. Closing again does nothing.
     * Closing from a host function, module initializer, loader, output, or
     * policy of this runtime throws {@link IllegalStateException}, as the
     * engine is running beneath it.
     */
    @Override
    public synchronized void close() {
        if (callbacks > 0) {
            throw new IllegalStateException("cannot close the runtime while it runs a host function");
        }
        if (ctx != 0) {
            Native.contextFree(ctx);
            ctx = 0;
            released.clear();
        }
    }

    /** Runs source and returns the value of its last expression statement, or None. */
    public synchronized PyObject eval(String source) {
        return wrap(Native.eval(enter(), source(source), "<string>"));
    }

    /** Runs source for its effects. */
    public synchronized void exec(String source) {
        check(Native.exec(enter(), source(source), "<string>"));
    }

    /** Reads a global; {@code NameError} when there is none. */
    public synchronized PyObject get(String name) {
        return wrap(Native.getGlobal(enter(), name(name)));
    }

    /** Converts value as {@link #toValue} does and binds it to a global. */
    public synchronized void set(String name, Object value) {
        long v = ref(value);
        try {
            check(Native.setGlobal(ctx, name(name), v));
        } finally {
            Native.release(v);
        }
    }

    /** A builtin function named name that calls f; the engine keeps f while the function lives. */
    public synchronized PyObject function(String name, HostFunction f) {
        return wrap(Native.function(enter(), name(name), f));
    }

    /** Binds {@link #function} as the global name. */
    public synchronized void define(String name, HostFunction f) {
        set(name, function(name, f));
    }

    /**
     * Makes {@code import name} create a module and call init to fill it, as
     * QuickJS's {@code JS_NewCModule}. Registering a name again replaces init.
     */
    public synchronized void registerModule(String name, ModuleInit init) {
        modules.put(name, init);
        check(Native.newModule(enter(), name(name)));
    }

    /** Runs source with module's namespace as its globals. */
    public synchronized void execModule(PyObject module, String source, String filename) {
        long m = ref(module);
        try {
            check(Native.execModule(ctx, m, source(source), name(filename)));
        } finally {
            Native.release(m);
        }
    }

    /** Sends what engine code prints to out, {@code System.out} by default; with null, print raises OSError. */
    public synchronized void setOutput(Appendable out) {
        Native.setOutput(enter(), out != null);
        output = out;
    }

    /**
     * Maps a module name to its source, or null when there is none. For
     * {@code import pkg.mod} it is asked for {@code pkg.mod.__init__} (a
     * package), then {@code pkg.mod}, then {@code pkg.mod.__namespace__} (a
     * namespace package). With null, only registered modules import.
     */
    public synchronized void setLoader(ModuleLoader loader) {
        Native.setLoader(enter(), loader != null);
        this.loader = loader;
    }

    /** Lets {@code open()} reach directory at the absolute engine path path, or at its own resolved path when path is null. */
    public synchronized void mount(Path directory, String path, boolean readOnly) {
        check(Native.mount(enter(), name(directory.toString()), path == null ? null : name(path), readOnly));
    }

    /**
     * Sets one limit. A spent step, memory or output limit stops the
     * operation with RuntimeError (MemoryError for memory) that no handler
     * catches; the next operation runs normally.
     */
    public synchronized void setLimit(Limit limit, long value) {
        if (value < 0) {
            throw new PythonException("ValueError", "a limit cannot be negative");
        }
        check(Native.setLimit(enter(), limit.ordinal(), value));
    }

    /** A limit's current value. */
    public synchronized long getLimit(Limit limit) {
        return Native.getLimit(enter(), limit.ordinal());
    }

    /**
     * Asks policy before {@code open} (file, mode), a module's first
     * {@code import} (name), {@code exec}, {@code eval} or {@code compile} of a
     * string ("exec": source), and {@code input} (prompt, if given). With
     * null, everything is allowed.
     */
    public synchronized void setPolicy(Policy policy) {
        Native.setPolicy(enter(), policy != null);
        this.policy = policy;
    }

    /** Asks the policy about an event of the host's own, such as a network request; throws when refused. */
    public synchronized void checkPolicy(String event, Object... args) {
        long tuple = ref(PyTuple.of(args));
        try {
            check(Native.policyCheck(ctx, name(event), tuple));
        } finally {
            Native.release(tuple);
        }
    }

    /** The steps the running or last top-level operation spent; calls spend only while a step limit is set. */
    public synchronized long stepsUsed() {
        return Native.stepsUsed(enter());
    }

    /** Sets the optimization level, as {@code python -O} (1) and {@code -OO} (2). */
    public synchronized void setOptimize(int level) {
        Native.setOptimize(enter(), level);
    }

    /** Runs the cycle collector and returns the number of values freed. */
    public synchronized long collect() {
        return Native.collect(enter());
    }

    /**
     * Converts a Java value into an engine value: null to None; Boolean;
     * Byte, Short, Integer, Long and BigInteger within 64 bits to int;
     * Float and Double to float; String and Character to str; byte[] to
     * bytes; {@link PyTuple} to tuple; other Lists and arrays to list; Maps
     * to dict, in their iteration order; records to a dict of their
     * components; a {@link PyObject} of this runtime to itself; and a
     * {@link HostFunction} to a builtin function.
     */
    public synchronized PyObject toValue(Object x) {
        return new PyObject(this, ref(x));
    }

    // The engine's callbacks (spy-jni.c), on the thread that called into
    // the engine. None throws: a failure becomes the engine's exception.

    long callHost(HostFunction f, long[] argv, long keywords) {
        callbacks++;
        try {
            List<PyObject> positional = new ArrayList<>(argv.length);
            for (long a : argv) {
                positional.add(new PyObject(this, Native.retain(a)));
            }
            Map<String, PyObject> named = new LinkedHashMap<>();
            if (keywords != 0) {
                PyObject dict = new PyObject(this, Native.retain(keywords));
                for (PyObject key : dict) {
                    named.put(key.as(String.class), dict.getItem(key));
                }
            }
            return ref(f.call(this, new Args(positional, named)));
        } catch (Throwable e) {
            raise(e, "RuntimeError");
            return 0;
        } finally {
            callbacks--;
        }
    }

    int initModule(long module) {
        callbacks++;
        try {
            PyObject m = new PyObject(this, Native.retain(module));
            String name = m.getAttr("__name__").as(String.class);
            ModuleInit init = modules.get(name);
            if (init == null) {
                throw new PythonException("ImportError", "no module named '" + name + "'");
            }
            init.init(this, m);
            return 0;
        } catch (Throwable e) {
            raise(e, "RuntimeError");
            return -1;
        } finally {
            callbacks--;
        }
    }

    int write(String text) {
        callbacks++;
        try {
            output.append(text);
            return 0;
        } catch (IOException | RuntimeException e) {
            return -1;
        } finally {
            callbacks--;
        }
    }

    String load(String name) {
        callbacks++;
        try {
            return loader.load(name);
        } catch (Throwable e) {
            raise(e, "RuntimeError");
            return null;
        } finally {
            callbacks--;
        }
    }

    int policy(String event, long args) {
        callbacks++;
        try {
            List<PyObject> items = new ArrayList<>();
            new PyObject(this, Native.retain(args)).forEach(items::add);
            policy.check(event, items);
            return 0;
        } catch (Throwable e) {
            raise(e, "PermissionError");
            return -1;
        } finally {
            callbacks--;
        }
    }

    /** Sets e as the engine's pending error: a PythonException keeps its type, any other has type. */
    private void raise(Throwable e, String type) {
        if (e instanceof PythonException p) {
            Native.raise(ctx, p.getType(), p.getPythonMessage());
        } else {
            Native.raise(ctx, type, e.getMessage() != null ? e.getMessage() : e.toString());
        }
    }

    // Shared by PyObject and the conversions.

    /** The context, after releasing what the garbage collector dropped. */
    long enter() {
        if (ctx == 0) {
            throw new IllegalStateException("the runtime is closed");
        }
        for (Long v; (v = released.poll()) != null; ) {
            Native.release(v);
        }
        return ctx;
    }

    /** Queues v's reference for release; the cleaner calls it on a thread of its own. */
    void drop(long v) {
        if (ctx != 0) {
            released.add(v);
        }
    }

    /** made, as a PyObject. */
    PyObject wrap(long v) {
        return new PyObject(this, made(v));
    }

    /** An owned engine result, or the pending error thrown. */
    long made(long v) {
        if (v == 0) {
            throw Native.takeError(ctx);
        }
        return v;
    }

    void check(int status) {
        if (status != 0) {
            throw Native.takeError(ctx);
        }
    }

    long ref(Object x) {
        enter();
        return Convert.ref(this, ctx, x);
    }

    long context() {
        return ctx;
    }

    static String name(String name) {
        if (name.indexOf('\0') >= 0) {
            throw new PythonException("ValueError", "embedded null character");
        }
        return name;
    }

    private static String source(String source) {
        if (source.indexOf('\0') >= 0) {
            throw new PythonException("SyntaxError", "source code string cannot contain null bytes");
        }
        return source;
    }
}
