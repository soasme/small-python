package io.github.soasme.spy;

import java.lang.ref.Reference;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.function.Supplier;

/**
 * A reference to an engine value. The garbage collector releases it once it
 * is unreachable, on the runtime's next operation; it never outlives the
 * runtime's {@link Interpreter#close}. Its methods do what Python does.
 */
public final class PyObject implements Iterable<PyObject> {
    private final Interpreter rt;
    final long ptr;

    PyObject(Interpreter rt, long ptr) {
        this.rt = rt;
        this.ptr = ptr;
        Interpreter.CLEANER.register(this, release(rt, ptr));
    }

    // Static, so the action does not hold the value.
    private static Runnable release(Interpreter rt, long ptr) {
        return () -> rt.drop(ptr);
    }

    /**
     * f's result, on the runtime. The engine borrows ptr until f returns, and
     * a host function it calls may release what the collector dropped, so
     * this value stays reachable until then (tests/tla/SpyJava.tla).
     */
    private <T> T with(Supplier<T> f) {
        synchronized (rt) {
            try {
                return f.get();
            } finally {
                Reference.reachabilityFence(this);
            }
        }
    }

    /** The runtime the value belongs to. */
    public Interpreter runtime() {
        return rt;
    }

    /** Whether the value is None. */
    public boolean isNone() {
        return with(() -> {
            rt.enter();
            return Native.type(ptr) == Native.NONE;
        });
    }

    /** Python truth, as {@code bool(value)}. */
    public boolean truth() {
        return with(() -> {
            int truth = Native.truth(rt.enter(), ptr);
            if (truth < 0) {
                throw Native.takeError(rt.context());
            }
            return truth != 0;
        });
    }

    /**
     * The value decoded into type: Boolean, Long, Integer, Short, Byte,
     * BigInteger, Double, Float, String, byte[] (from bytes or bytearray),
     * {@link PyTuple}, List (from any iterable), Map (from any mapping), a
     * record (from a mapping, by component name, ignoring unknown keys),
     * PyObject, or Object, which gives {@link #toJava}'s result. A record's
     * List and Map components decode their elements by their declared type.
     */
    @SuppressWarnings("unchecked") // a primitive type's Class<T> is that of its box
    public <T> T as(Class<T> type) {
        return with(() -> {
            rt.enter();
            return (T) Convert.decode(rt, ptr, type);
        });
    }

    /**
     * The value as the Java value it naturally maps to: null, Boolean, Long
     * or BigInteger, Double, String, byte[], a List for a list, {@link
     * PyTuple}, and a Map for a dict, with their items converted likewise;
     * this value itself for anything else, including subclasses of those
     * types.
     */
    public Object toJava() {
        return as(Object.class);
    }

    /** {@code getattr(value, name)}. */
    public PyObject getAttr(String name) {
        return with(() -> rt.wrap(Native.getAttr(rt.enter(), ptr, Interpreter.name(name))));
    }

    /** {@code setattr(value, name, item)}. */
    public void setAttr(String name, Object item) {
        with(() -> {
            long i = rt.ref(item);
            try {
                rt.check(Native.setAttr(rt.context(), ptr, Interpreter.name(name), i));
            } finally {
                Native.release(i);
            }
            return null;
        });
    }

    /** {@code value[key]}. */
    public PyObject getItem(Object key) {
        return with(() -> {
            long k = rt.ref(key);
            try {
                return rt.wrap(Native.getItem(rt.context(), ptr, k));
            } finally {
                Native.release(k);
            }
        });
    }

    /** {@code value[key] = item}. */
    public void setItem(Object key, Object item) {
        with(() -> {
            long k = rt.ref(key);
            try {
                long i = rt.ref(item);
                try {
                    rt.check(Native.setItem(rt.context(), ptr, k, i));
                } finally {
                    Native.release(i);
                }
            } finally {
                Native.release(k);
            }
            return null;
        });
    }

    /** Calls the value with positional arguments. */
    public PyObject call(Object... args) {
        return callKeywords(List.of(args), Map.of());
    }

    /** Calls the value with positional and keyword arguments. */
    public PyObject callKeywords(List<?> args, Map<String, ?> kwargs) {
        return with(() -> {
            long[] argv = new long[args.size()];
            long keywords = 0;
            try {
                int n = 0;
                for (Object arg : args) {
                    argv[n++] = rt.ref(arg);
                }
                keywords = kwargs.isEmpty() ? 0 : rt.ref(kwargs);
                return rt.wrap(Native.call(rt.enter(), ptr, argv, keywords));
            } finally {
                for (long a : argv) {
                    Native.release(a);
                }
                Native.release(keywords);
            }
        });
    }

    /** Iterates the value as a for loop does; an exception ending the iteration is thrown from {@code hasNext}. */
    @Override
    public Iterator<PyObject> iterator() {
        PyObject it = with(() -> rt.wrap(Native.iter(rt.enter(), ptr)));
        return new Iterator<>() {
            private PyObject next;
            private boolean done;

            @Override
            public boolean hasNext() {
                return it.with(() -> {
                    if (next == null && !done) {
                        long item = Native.next(rt.enter(), it.ptr);
                        if (item != 0) {
                            next = new PyObject(rt, item);
                        } else {
                            done = true;
                            if (Native.errorPending(rt.context())) {
                                throw Native.takeError(rt.context());
                            }
                        }
                    }
                    return next != null;
                });
            }

            @Override
            public PyObject next() {
                if (!hasNext()) {
                    throw new NoSuchElementException();
                }
                PyObject item = next;
                next = null;
                return item;
            }
        };
    }

    /** {@code repr(value)}. */
    public String repr() {
        return with(() -> rt.wrap(Native.repr(rt.enter(), ptr)).as(String.class));
    }

    /** {@code str(value)}. */
    public String str() {
        return with(() -> rt.wrap(Native.str(rt.enter(), ptr)).as(String.class));
    }

    /** {@code str(value)}, or a placeholder naming why it cannot be had. */
    @Override
    public String toString() {
        try {
            return str();
        } catch (RuntimeException e) {
            return "<unprintable: " + e.getMessage() + ">";
        }
    }
}
