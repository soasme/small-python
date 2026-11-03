package io.github.soasme.spy.worker;

import java.util.OptionalInt;

/**
 * The worker was lost (protocol.md 8): it crashed, broke the protocol, did
 * not stop at its timeout, or a host function threw an Error. Every later
 * operation of the runtime throws the same exception.
 */
public class WorkerException extends RuntimeException {
    private static final long serialVersionUID = 1;

    private final transient OptionalInt exitStatus;

    WorkerException(String message, OptionalInt exitStatus) {
        super(message);
        this.exitStatus = exitStatus;
    }

    /** The worker's exit status, when it exited on its own; on Unix 128 plus the signal that ended it. */
    public OptionalInt exitStatus() {
        return exitStatus;
    }
}
