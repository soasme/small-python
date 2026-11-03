package io.github.soasme.spy.worker;

/**
 * Decides whether the engine may perform an event. Returning allows it;
 * throwing refuses it: a {@link PythonException} raises its type, any other
 * exception PermissionError with its message.
 */
@FunctionalInterface
public interface Policy {
    void check(String event, PyTuple args) throws Exception;
}
