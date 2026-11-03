package io.github.soasme.spy;

/**
 * An engine exception, raised by engine code or by Java.
 *
 * <p>Exceptions cross between Java and the engine by type name and message:
 * one that escapes into Java is copied into a PythonException and cleared,
 * and a host function throwing one raises a new exception of the builtin
 * class it names, with its message. Any other exception a host function
 * throws raises RuntimeError with its message.
 */
public class PythonException extends RuntimeException {
    private static final long serialVersionUID = 1;

    private final String type;
    private final String pythonMessage;
    private final String filename;
    private final long line;

    /** An exception for a host function to throw: the engine raises the builtin class type with message. */
    public PythonException(String type, String message) {
        this(type, message, "", 0);
    }

    PythonException(String type, String message, String filename, long line) {
        super(message.isEmpty() ? type : type + ": " + message);
        this.type = type;
        this.pythonMessage = message;
        this.filename = filename;
        this.line = line;
    }

    /** The class name, qualified by its module unless it is a builtin. */
    public String getType() {
        return type;
    }

    /** The text CPython's traceback shows after the type. */
    public String getPythonMessage() {
        return pythonMessage;
    }

    /** Where the engine raised it, or empty when it was not raised by the engine. */
    public String getFilename() {
        return filename;
    }

    /** The line it was raised at, or 0. */
    public long getLine() {
        return line;
    }
}
