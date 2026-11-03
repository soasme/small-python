package io.github.soasme.spy.worker;

/** A host function registered with a runtime, as a value to pass into it. */
public final class PyFunction {
    final Interpreter rt;
    final long id;
    final String name;

    PyFunction(Interpreter rt, long id, String name) {
        this.rt = rt;
        this.id = id;
        this.name = name;
    }

    @Override
    public String toString() {
        return "PyFunction(" + name + ")";
    }
}
