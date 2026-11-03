package io.github.soasme.spy.worker;

/**
 * An engine exception that escaped, or one a host function throws for the
 * engine to raise: the builtin class it names, or RuntimeError when there is
 * none. When an exception a host function threw escapes, its cause is what
 * the host function threw.
 */
public class PythonException extends RuntimeException {
    private static final long serialVersionUID = 1;

    private final String type;
    private final String pythonMessage;
    private final String filename;
    private final long line;
    private final transient PyObject object;

    /** An exception for a host function to throw. */
    public PythonException(String type, String message) {
        this(type, message, "", 0, null, null);
    }

    PythonException(String type, String message, String filename, long line, PyObject object, Throwable cause) {
        super(message.isEmpty() ? type : type + ": " + message, cause);
        this.type = type;
        this.pythonMessage = message;
        this.filename = filename;
        this.line = line;
        this.object = object;
    }

    /** The class name, qualified by its module unless it is a builtin. */
    public String getType() {
        return type;
    }

    /** The text CPython's traceback shows after the type. */
    public String getPythonMessage() {
        return pythonMessage;
    }

    /** Where the engine raised it, or empty. */
    public String getFilename() {
        return filename;
    }

    /** The line it was raised at, or 0. */
    public long getLine() {
        return line;
    }

    /** The exception object in the worker, or null when it could not be sent or was not raised there. */
    public PyObject getObject() {
        return object;
    }
}
