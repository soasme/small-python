package io.github.soasme.spy;

/** Fills a registered module on its first import; what it throws fails the import. */
@FunctionalInterface
public interface ModuleInit {
    void init(Interpreter rt, PyObject module) throws Exception;
}
