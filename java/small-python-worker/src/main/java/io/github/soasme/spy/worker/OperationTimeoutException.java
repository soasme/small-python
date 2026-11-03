package io.github.soasme.spy.worker;

import java.time.Duration;

/**
 * An operation ran past the runtime's timeout. The engine stopped it and the
 * runtime stays open, unless the worker did not stop within the grace
 * period: then it is lost, and its later operations throw this again.
 */
public class OperationTimeoutException extends RuntimeException {
    private static final long serialVersionUID = 1;

    OperationTimeoutException(Duration timeout) {
        super("the operation exceeded the timeout of " + timeout.toMillis() + " ms");
    }
}
