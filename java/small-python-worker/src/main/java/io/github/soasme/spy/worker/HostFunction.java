package io.github.soasme.spy.worker;

import java.util.List;
import java.util.Map;

/**
 * A function of the host, called by engine code with the call's arguments.
 * Through the runtime it receives it may make nested requests, except
 * {@code eval} and {@code exec}. What it throws raises an engine exception
 * (see {@link PythonException}); an {@link Error} loses the worker and goes
 * on unwinding.
 */
@FunctionalInterface
public interface HostFunction {
    Object call(Interpreter rt, List<Object> args, Map<String, Object> kwargs) throws Exception;
}
