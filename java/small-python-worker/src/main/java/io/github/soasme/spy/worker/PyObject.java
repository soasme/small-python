package io.github.soasme.spy.worker;

import java.util.Arrays;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

/**
 * A handle to an engine value the worker holds. Its methods do what Python
 * does, as requests to the worker. The worker releases the value with the
 * interpreter's next message after the garbage collector finds the handle
 * unreachable. Handles are equal only to themselves.
 */
public final class PyObject implements Iterable<Object> {
    final Interpreter rt;
    final long id;

    PyObject(Interpreter rt, long id) {
        this.rt = rt;
        this.id = id;
        Interpreter.CLEANER.register(this, release(rt, id));
    }

    // Static, so the action does not hold the handle.
    private static Runnable release(Interpreter rt, long id) {
        return () -> rt.drop(id);
    }

    /** The interpreter the value lives in. */
    public Interpreter interpreter() {
        return rt;
    }

    /** {@code getattr(object, name)}. */
    public Object getAttr(String name) {
        return rt.op(1, this, name);
    }

    /** {@code setattr(object, name, value)}. */
    public void setAttr(String name, Object value) {
        rt.op(2, this, name, value);
    }

    /** {@code object[key]}. */
    public Object getItem(Object key) {
        return rt.op(3, this, key);
    }

    /** {@code object[key] = value}. */
    public void setItem(Object key, Object value) {
        rt.op(4, this, key, value);
    }

    /** {@code len(object)}. */
    public long len() {
        return rt.result(rt.op(5, this), Long.class, "length");
    }

    /** {@code item in object}. */
    public boolean contains(Object item) {
        return rt.result(rt.op(6, this, item), Boolean.class, "membership");
    }

    /** Iterates the object as a for loop does, with {@code iter} and {@code next}. */
    @Override
    public Iterator<Object> iterator() {
        return rt.iterate(this);
    }

    /** {@code bool(object)}. */
    public boolean truth() {
        return rt.result(rt.op(9, this), Boolean.class, "truth");
    }

    /** {@code hash(object)}. */
    public long hash() {
        return rt.result(rt.op(10, this), Long.class, "hash");
    }

    /** {@code object < other}, or another rich comparison; its result may be any value. */
    public Object compare(Compare op, Object other) {
        return rt.op(op.op, this, other);
    }

    /** {@code repr(object)}. */
    public String repr() {
        return rt.result(rt.op(17, this), String.class, "repr");
    }

    /** {@code str(object)}. */
    public String str() {
        return rt.result(rt.op(18, this), String.class, "str");
    }

    /** {@code dir(object)}. */
    public List<?> dir() {
        return rt.result(rt.op(19, this), List.class, "dir");
    }

    /** Calls the object with positional arguments. */
    public Object call(Object... args) {
        return rt.callKeywords(this, Arrays.asList(args), Map.of());
    }

    /** Calls the object with positional and keyword arguments. */
    public Object callKeywords(List<?> args, Map<String, ?> kwargs) {
        return rt.callKeywords(this, args, kwargs);
    }

    @Override
    public String toString() {
        return "PyObject(" + id + ")";
    }
}
