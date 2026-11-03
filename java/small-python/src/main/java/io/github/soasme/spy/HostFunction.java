package io.github.soasme.spy;

/**
 * A function of the host, called by engine code. Its result converts as by
 * {@link Interpreter#toValue}; what it throws raises an engine exception (see
 * {@link PythonException}).
 */
@FunctionalInterface
public interface HostFunction {
    Object call(Interpreter rt, Args args) throws Exception;
}
