package io.github.soasme.spy.worker;

import static io.github.soasme.spy.worker.Wire.CALL;
import static io.github.soasme.spy.worker.Wire.COLLECT;
import static io.github.soasme.spy.worker.Wire.DELETE;
import static io.github.soasme.spy.worker.Wire.EVAL;
import static io.github.soasme.spy.worker.Wire.EXEC;
import static io.github.soasme.spy.worker.Wire.GET;
import static io.github.soasme.spy.worker.Wire.HOST;
import static io.github.soasme.spy.worker.Wire.INIT;
import static io.github.soasme.spy.worker.Wire.LOAD;
import static io.github.soasme.spy.worker.Wire.MODULE;
import static io.github.soasme.spy.worker.Wire.MOUNT;
import static io.github.soasme.spy.worker.Wire.OP;
import static io.github.soasme.spy.worker.Wire.OUTPUT;
import static io.github.soasme.spy.worker.Wire.POLICY;
import static io.github.soasme.spy.worker.Wire.RAISE;
import static io.github.soasme.spy.worker.Wire.RELEASE;
import static io.github.soasme.spy.worker.Wire.RESULT;
import static io.github.soasme.spy.worker.Wire.SET;
import static io.github.soasme.spy.worker.Wire.USAGE;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.ref.Cleaner;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.OptionalInt;
import java.util.Set;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.TimeUnit;

/**
 * One Small Python engine in a spy-worker process of its own, which seals
 * itself under the operating system's sandbox before it runs any code and
 * speaks the worker protocol (docs/packaging/protocol.md) over its standard
 * input and output.
 *
 * <pre>{@code
 * try (Interpreter py = Interpreter.builder().timeout(Duration.ofSeconds(5)).start()) {
 *     py.define("greet", (rt, args, kwargs) -> "hello " + args.get(0));
 *     Object v = py.eval("greet('spy')"); // "hello spy"
 * }
 * }</pre>
 *
 * <p>Values cross by copy as Java values: null (None), Boolean, Long or
 * BigInteger (int), Double, {@link PyComplex}, String, byte[] (bytes),
 * {@link PyByteArray}, List (list), {@link PyTuple}, {@link PySet}, {@link
 * PyFrozenSet}, {@link PyDict}, and {@link PyObject} handles for anything
 * else. Sending also accepts Integer, Short, Byte, Float, Character, arrays,
 * Maps in their iteration order, and {@link PyFunction}. A crash, a protocol
 * violation, or a worker that does not stop at its timeout loses the
 * worker, and the interpreter with it ({@link WorkerException}).
 *
 * <p>Operations are serialized on the interpreter. While a host function
 * runs, it may make nested requests through the interpreter it receives,
 * but not {@code eval} or {@code exec}.
 */
public final class Interpreter implements AutoCloseable {
    static final Cleaner CLEANER = Cleaner.create();

    /** The time past the timeout the worker has to stop an operation itself. */
    private static final long GRACE = TimeUnit.SECONDS.toNanos(1);
    private static final Object END = new Object();
    private static final byte[] CLOSE = new byte[0];

    private final Process process;
    private final BlockingQueue<Object> from = new SynchronousQueue<>();
    private final BlockingQueue<byte[]> to = new ArrayBlockingQueue<>(2);
    private final Thread reader;
    // Handles the garbage collector found unreachable, released with the next message.
    private final ConcurrentLinkedQueue<Long> released = new ConcurrentLinkedQueue<>();
    private volatile boolean ended;

    private final Duration timeout;
    private final long limit;
    private final List<HostFunction> functions = new ArrayList<>();
    private Appendable output;
    private ModuleLoader loader;
    private Policy policy;
    private final String version;

    private RuntimeException lost;
    private boolean closed;
    private long deadline;
    private Failure failure;
    private long tokens;
    private int depth;
    private int callbacks;

    /** The error a callback failed with, and the token naming it. */
    private record Failure(long token, Throwable error) {}

    /** What a request of the worker produced: a value, or the failure of the host's callback. */
    private record Outcome(Object value, Throwable failed) {}

    /** A builder of interpreters; its defaults are the zero values its methods describe. */
    public static Builder builder() {
        return new Builder();
    }

    /** An interpreter with the defaults of {@link Builder}. */
    public static Interpreter start() {
        return builder().start();
    }

    /** Configures and starts an {@link Interpreter}. */
    public static final class Builder {
        private boolean std = true;
        private long stepLimit, memoryLimit, outputLimit;
        private Duration timeout = Duration.ZERO;
        private long messageLimit = 64 << 20;
        private Appendable output = System.out;
        private ModuleLoader loader;
        private Policy policy;
        private Path worker;

        private Builder() {}

        /** Whether to register the standard modules sys and gc; true by default. */
        public Builder std(boolean std) {
            this.std = std;
            return this;
        }

        /** Bounds the steps of each top-level operation; 0, the default, is unlimited. Exceeding it raises RuntimeError. */
        public Builder stepLimit(long limit) {
            stepLimit = nonNegative(limit);
            return this;
        }

        /** Bounds the bytes the engine may hold; 0, the default, is unlimited. Exceeding it raises MemoryError. */
        public Builder memoryLimit(long limit) {
            memoryLimit = nonNegative(limit);
            return this;
        }

        /** Bounds the bytes each top-level operation may print; 0, the default, is unlimited. */
        public Builder outputLimit(long limit) {
            outputLimit = nonNegative(limit);
            return this;
        }

        /**
         * Bounds the time one operation may run in the worker, host functions
         * excluded; zero, the default, is unlimited. Exceeding it throws
         * {@link OperationTimeoutException}.
         */
        public Builder timeout(Duration timeout) {
            if (timeout.isNegative()) {
                throw new IllegalArgumentException("the timeout must not be negative");
            }
            this.timeout = timeout;
            return this;
        }

        /** The largest message in bytes, either direction, from 1 to 2^32-1; 64 MiB by default. */
        public Builder messageLimit(long limit) {
            if (limit < 1 || limit > 0xffffffffL) {
                throw new IllegalArgumentException("the message limit must be from 1 to 2^32-1");
            }
            messageLimit = limit;
            return this;
        }

        /** Receives printed text; {@code System.out} by default. */
        public Builder output(Appendable output) {
            this.output = output;
            return this;
        }

        /**
         * Maps a module name to its source, or null when there is none; by
         * default there is none. For {@code import pkg.mod} it is asked for
         * {@code pkg.mod.__init__} (a package), then {@code pkg.mod}; source
         * for {@code pkg.mod.__namespace__} makes a namespace package.
         */
        public Builder loader(ModuleLoader loader) {
            this.loader = loader;
            return this;
        }

        /**
         * Asked before the engine opens a file ("open": file, mode), imports a
         * module for the first time ("import": name), executes source text
         * ("exec": source), or reads input ("input": prompt, if given). By
         * default every event is allowed.
         */
        public Builder policy(Policy policy) {
            this.policy = policy;
            return this;
        }

        /** The spy-worker executable to run instead of the one the jar carries. */
        public Builder worker(Path worker) {
            this.worker = worker;
            return this;
        }

        /** Starts the worker and waits until it is ready. */
        public Interpreter start() {
            return new Interpreter(this);
        }

        private static long nonNegative(long limit) {
            if (limit < 0) {
                throw new IllegalArgumentException("a limit must not be negative");
            }
            return limit;
        }
    }

    private Interpreter(Builder b) {
        timeout = b.timeout;
        limit = b.messageLimit;
        output = b.output;
        loader = b.loader;
        policy = b.policy;
        // protocol.md 9: an empty environment, working directory /, and only
        // descriptors 0 to 2, which ProcessBuilder already ensures.
        ProcessBuilder pb = new ProcessBuilder((b.worker != null ? b.worker : WorkerExecutable.path()).toString())
                .directory(new File("/"))
                .redirectError(ProcessBuilder.Redirect.INHERIT);
        pb.environment().clear();
        try {
            process = pb.start();
        } catch (IOException e) {
            throw new WorkerException("cannot start the worker: " + e.getMessage(), OptionalInt.empty());
        }
        reader = daemon("spy-worker reader", () -> read(process.getInputStream()));
        daemon("spy-worker writer", () -> write(process.getOutputStream()));
        PyDict options = PyDict.of(
                "std", b.std,
                "step_limit", b.stepLimit,
                "memory_limit", b.memoryLimit,
                "output_limit", b.outputLimit,
                "policy", b.policy != null,
                "timeout", b.timeout.toNanos() / 1e9,
                "message_limit", b.messageLimit);
        try {
            if (!(run(INIT, options) instanceof String v)) {
                throw violation("malformed version");
            }
            version = v;
        } catch (RuntimeException e) {
            lose(e);
            throw e;
        }
    }

    private static Thread daemon(String name, Runnable task) {
        Thread thread = new Thread(task, name);
        thread.setDaemon(true);
        thread.start();
        return thread;
    }

    /** The engine version the worker reported. */
    public String version() {
        return version;
    }

    /** The worker's process id. */
    public long pid() {
        return process.pid();
    }

    /** Runs source and returns the value of its last expression statement, or null. */
    public Object eval(String source) {
        return run(EVAL, source, "<string>");
    }

    /** Runs source for its effects. */
    public void exec(String source) {
        run(EXEC, source, "<string>");
    }

    /** Calls a global function by name with positional arguments. */
    public Object call(String function, Object... args) {
        return callKeywords(function, Arrays.asList(args), Map.of());
    }

    /** Calls function, a global name, a {@link PyObject} or a {@link PyFunction}, with positional and keyword arguments. */
    public Object callKeywords(Object function, List<?> args, Map<String, ?> kwargs) {
        return run(CALL, function, new PyTuple(new ArrayList<>(args)), kwargs);
    }

    /** Reads a global, falling back to builtins; NameError when there is none. */
    public Object get(String name) {
        return run(GET, name);
    }

    /** Binds a global. */
    public void set(String name, Object value) {
        run(SET, name, value);
    }

    /** Deletes a global; KeyError when there is none. */
    public void delete(String name) {
        run(DELETE, name);
    }

    /**
     * A host function as a value to pass into the engine, where it becomes a
     * builtin function named name. The interpreter keeps f until it ends.
     */
    public synchronized PyFunction function(String name, HostFunction f) {
        functions.add(f);
        return new PyFunction(this, functions.size(), name);
    }

    /** Binds {@link #function} as the global name. */
    public void define(String name, HostFunction f) {
        set(name, function(name, f));
    }

    /**
     * Makes {@code import name} create a module whose attributes are members,
     * then run source in it; either may be null. Registering a name again
     * replaces it.
     */
    public void registerModule(String name, Map<String, ?> members, String source) {
        run(MODULE, name, members, source);
    }

    /**
     * Lets the engine's {@code open()} reach a host directory at the absolute
     * engine path path, or at its resolved host path when path is null.
     * Mounts are fixed once the worker has run code.
     */
    public void mount(Path directory, String path, boolean readOnly) {
        Path resolved;
        try {
            resolved = directory.toRealPath();
        } catch (IOException e) {
            throw new IllegalArgumentException("cannot mount '" + directory + "': " + e, e);
        }
        if (!Files.isDirectory(resolved)) {
            throw new IllegalArgumentException("cannot mount '" + directory + "': not a directory");
        }
        run(MOUNT, resolved.toString(), path != null ? path : resolved.toString(), readOnly);
    }

    /** Runs the cycle collector and returns the number of values freed. */
    public long collect() {
        return result(run(COLLECT), Long.class, "collect result");
    }

    /** The steps the last operation spent and the bytes the engine holds. */
    public record Usage(long steps, long memory) {}

    /** The steps the last operation spent and the bytes the engine holds now. */
    public Usage usage() {
        if (run(USAGE) instanceof PyTuple t && t.items().size() == 2
                && t.items().get(0) instanceof Long steps && t.items().get(1) instanceof Long memory) {
            return new Usage(steps, memory);
        }
        throw violation("malformed usage result");
    }

    /** Whether the interpreter was closed or lost. */
    public synchronized boolean isClosed() {
        return closed || lost != null;
    }

    /** Ends the worker: closes its input, waits a second for it to exit, and terminates it otherwise. */
    @Override
    public synchronized void close() {
        if (closed) {
            return;
        }
        closed = true;
        if (lost == null) {
            to.offer(CLOSE);
            try {
                long until = System.nanoTime() + TimeUnit.SECONDS.toNanos(1);
                for (Object r; (r = from.poll(until - System.nanoTime(), TimeUnit.NANOSECONDS)) != null && r != END; ) {
                    // A message the closed worker still sent: ignored.
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            end();
        }
    }

    // Object operations (protocol.md 7.3), for PyObject.

    Object op(int op, PyObject target, Object... operands) {
        Object[] fields = new Object[operands.length + 2];
        fields[0] = (long) op;
        fields[1] = target;
        System.arraycopy(operands, 0, fields, 2, operands.length);
        return run(OP, fields);
    }

    <T> T result(Object value, Class<T> type, String what) {
        if (!type.isInstance(value)) {
            throw violation("malformed " + what);
        }
        return type.cast(value);
    }

    Iterator<Object> iterate(PyObject target) {
        PyObject it = result(op(7, target), PyObject.class, "iterator");
        return new Iterator<>() {
            private Object next;
            private boolean has, done;

            @Override
            public boolean hasNext() {
                if (!has && !done) {
                    try {
                        next = op(8, it);
                        has = true;
                    } catch (PythonException e) {
                        done = true;
                        if (!e.getType().equals("StopIteration")) {
                            throw e;
                        }
                    }
                }
                return has;
            }

            @Override
            public Object next() {
                if (!hasNext()) {
                    throw new NoSuchElementException();
                }
                has = false;
                return next;
            }
        };
    }

    /** Queues a handle's release; the cleaner calls it on a thread of its own. */
    void drop(long id) {
        if (!ended) {
            released.add(id);
        }
    }

    // Requests (protocol.md 6).

    /** Makes one request, top-level or nested; the timeout spans the top level. */
    private synchronized Object run(byte kind, Object... fields) {
        if (lost != null) {
            throw lost;
        }
        if (closed) {
            throw new IllegalStateException("the interpreter is closed");
        }
        if ((kind == EVAL || kind == EXEC) && callbacks > 0) {
            throw new IllegalStateException("cannot evaluate source while a host function of this interpreter is running");
        }
        boolean top = depth == 0;
        if (top && !timeout.isZero()) {
            deadline = System.nanoTime() + timeout.toNanos() + GRACE;
        }
        depth++;
        try {
            byte[] data = Wire.message(kind, this, fields);
            if (data.length - 4 > limit) {
                throw new IllegalArgumentException("message exceeds the limit");
            }
            send(data);
            byte[] reply = awaitReply();
            Object value = decode(reply, 1)[0];
            if (reply[0] == RAISE) {
                throw engineError(value);
            }
            return value;
        } finally {
            depth--;
            if (top) {
                deadline = 0;
            }
        }
    }

    private byte[] awaitReply() {
        while (true) {
            byte[] message = receive();
            switch (message[0]) {
                case RESULT, RAISE -> {
                    return message;
                }
                case HOST, LOAD, OUTPUT, POLICY -> {
                    if (message[0] == POLICY && policy == null) {
                        throw violation("unexpected message kind 0x24");
                    }
                    serve(message);
                }
                default -> throw violation(String.format("unexpected message kind 0x%02x", message[0]));
            }
        }
    }

    /** Sends data, after a notice of the handles released since the last message. */
    private void send(byte[] data) {
        List<Object> ids = new ArrayList<>();
        for (Long id; (id = released.poll()) != null; ) {
            ids.add(id);
        }
        try {
            if (!ids.isEmpty()) {
                offer(Wire.message(RELEASE, this, new PyTuple(ids)));
            }
            offer(data);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw lose(new WorkerException("interrupted while sending to the worker", OptionalInt.empty()));
        }
    }

    private void offer(byte[] message) throws InterruptedException {
        if (deadline == 0) {
            to.put(message);
        } else if (!to.offer(message, deadline - System.nanoTime(), TimeUnit.NANOSECONDS)) {
            throw lose(new OperationTimeoutException(timeout));
        }
    }

    private byte[] receive() {
        Object r;
        try {
            r = deadline == 0 ? from.take() : from.poll(deadline - System.nanoTime(), TimeUnit.NANOSECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw lose(new WorkerException("interrupted while waiting for the worker", OptionalInt.empty()));
        }
        if (r == null) {
            throw lose(new OperationTimeoutException(timeout));
        } else if (r instanceof byte[] message) {
            return message;
        } else if (r instanceof Wire.Violation v) {
            throw violation(v.getMessage());
        }
        return exited();
    }

    private Object[] decode(byte[] message, int n) {
        try {
            return Wire.decode(message, this, n);
        } catch (Wire.Violation v) {
            throw violation(v.getMessage());
        }
    }

    // Losing the worker (protocol.md 8).

    private RuntimeException violation(String what) {
        return lose(new WorkerException("the worker broke the protocol: " + what, OptionalInt.empty()));
    }

    private byte[] exited() {
        int status;
        try {
            status = process.waitFor();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw lose(new WorkerException("interrupted while waiting for the worker", OptionalInt.empty()));
        }
        throw lose(new WorkerException("the worker ended with exit status " + status, OptionalInt.of(status)));
    }

    private RuntimeException lose(RuntimeException e) {
        if (lost == null) {
            lost = e;
            end();
        }
        return lost;
    }

    private void end() {
        ended = true;
        released.clear();
        to.clear();
        to.offer(CLOSE);
        reader.interrupt();
        process.destroyForcibly();
        try {
            process.waitFor();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        functions.clear();
        failure = null;
        output = null;
        loader = null;
        policy = null;
    }

    /** The exception of a worker's RAISE. */
    private RuntimeException engineError(Object raised) {
        Map<Object, Object> fields = new LinkedHashMap<>();
        for (PyDict.Item item : raised instanceof PyDict d ? d.items() : List.<PyDict.Item>of()) {
            if (fields.put(item.key(), item.value()) != null || fields.size() > 7) {
                throw violation("malformed error");
            }
        }
        Set<String> keys = Set.of("type", "message", "filename", "line", "exception", "token", "stop");
        Object exception = fields.get("exception");
        if (!new HashSet<>(fields.keySet()).equals(keys)
                || !(exception == null || exception instanceof PyObject)
                || !(fields.get("type") instanceof String type) || !(fields.get("message") instanceof String message)
                || !(fields.get("filename") instanceof String filename) || !(fields.get("line") instanceof Long line)
                || !(fields.get("token") instanceof Long token) || !(fields.get("stop") instanceof String stop)) {
            throw violation("malformed error");
        }
        Failure f = failure;
        failure = null;
        if (stop.equals("timeout")) {
            return new OperationTimeoutException(timeout);
        }
        Throwable cause = f != null && f.token() == token ? f.error() : null;
        return new PythonException(type, message, filename, line, (PyObject) exception, cause);
    }

    // Requests from the worker.

    private void serve(byte[] request) {
        long started = System.nanoTime();
        Outcome outcome;
        callbacks++;
        try {
            outcome = dispatch(request);
        } finally {
            callbacks--;
            if (deadline != 0) {
                deadline += System.nanoTime() - started;
            }
        }
        if (lost != null) {
            throw lost;
        }
        Throwable failed = outcome.failed();
        byte[] reply = null;
        if (failed == null) {
            try {
                reply = Wire.message(RESULT, this, outcome.value());
                if (reply.length - 4 > limit) {
                    failed = new IllegalArgumentException("message exceeds the limit");
                }
            } catch (PythonException | IllegalArgumentException e) {
                failed = e;
            }
        }
        if (failed != null) {
            reply = Wire.message(RAISE, this, failureOf(failed, request[0] == POLICY ? "PermissionError"
                    : request[0] == OUTPUT ? "OSError" : "RuntimeError"));
        }
        send(reply);
    }

    /** Serves a request: a protocol violation throws, a callback's failure is the outcome's. */
    private Outcome dispatch(byte[] request) {
        try {
            switch (request[0]) {
                case HOST -> {
                    Object[] fields = decode(request, 3);
                    Map<String, Object> kwargs = new LinkedHashMap<>();
                    boolean ok = fields[2] instanceof PyDict d;
                    for (PyDict.Item item : ok ? ((PyDict) fields[2]).items() : List.<PyDict.Item>of()) {
                        ok &= item.key() instanceof String;
                        kwargs.put(String.valueOf(item.key()), item.value());
                    }
                    if (!(fields[0] instanceof Long id) || id < 1 || id > functions.size()
                            || !(fields[1] instanceof PyTuple args) || !ok) {
                        throw violation("malformed host call");
                    }
                    return new Outcome(functions.get((int) (long) id - 1).call(this, args.items(), kwargs), null);
                }
                case LOAD -> {
                    if (!(decode(request, 1)[0] instanceof String name)) {
                        throw violation("malformed load");
                    }
                    return new Outcome(loader != null ? loader.load(name) : null, null);
                }
                case POLICY -> {
                    Object[] fields = decode(request, 2);
                    if (!(fields[0] instanceof String event) || !(fields[1] instanceof PyTuple args)) {
                        throw violation("malformed policy event");
                    }
                    policy.check(event, args);
                    return new Outcome(null, null);
                }
                default -> {
                    if (!(decode(request, 1)[0] instanceof String text)) {
                        throw violation("malformed output");
                    }
                    output.append(text);
                    return new Outcome(null, null);
                }
            }
        } catch (WorkerException | OperationTimeoutException e) {
            if (lost != null) {
                throw lost;
            }
            return new Outcome(null, e);
        } catch (Exception e) {
            return new Outcome(null, e);
        } catch (Error e) {
            // An Error leaves the worker mid-turn: lose it, then go on unwinding.
            lose(new WorkerException("a host function threw " + e, OptionalInt.empty()));
            throw e;
        }
    }

    /** The failure (protocol.md 7.4) for what a callback threw. */
    private PyDict failureOf(Throwable error, String otherwise) {
        long token = ++tokens;
        failure = new Failure(token, error);
        if (error instanceof PythonException p && p.getObject() != null && p.getObject().rt == this) {
            return PyDict.of("raise", p.getObject(), "token", token);
        }
        String type = otherwise;
        String message = error.getMessage() != null ? error.getMessage() : error.toString();
        if (error instanceof PythonException p) {
            type = p.getType();
            message = p.getPythonMessage();
        } else if (error instanceof IllegalArgumentException || error instanceof IllegalStateException) {
            type = "ValueError";
        }
        return PyDict.of("classes", PyTuple.of(type), "args", null, "message", message, "token", token);
    }

    // The threads that move bytes, so the interpreter can wait for the
    // worker with a deadline.

    /** Reads frames, checking each length against the limit before allocating. */
    private void read(InputStream in) {
        try (in) {
            while (true) {
                byte[] length = in.readNBytes(4);
                if (length.length < 4) {
                    break;
                }
                long n = (length[0] & 0xff) | (length[1] & 0xff) << 8 | (length[2] & 0xff) << 16
                        | (long) (length[3] & 0xff) << 24;
                if (n < 1 || n > limit) {
                    from.put(new Wire.Violation("message length out of range"));
                    return;
                }
                byte[] message = in.readNBytes((int) n);
                if (message.length < n) {
                    break;
                }
                from.put(message);
            }
            from.put(END);
        } catch (IOException e) {
            try {
                from.put(END);
            } catch (InterruptedException ended) {
                // The interpreter ended.
            }
        } catch (InterruptedException e) {
            // The interpreter ended.
        }
    }

    /** Writes messages until CLOSE, which closes the worker's input; after a failed write it discards them. */
    private void write(OutputStream out) {
        boolean broken = false;
        try (out) {
            for (byte[] m; (m = to.take()) != CLOSE; ) {
                if (!broken) {
                    try {
                        out.write(m);
                        out.flush();
                    } catch (IOException e) {
                        broken = true;
                    }
                }
            }
        } catch (IOException | InterruptedException e) {
            // The worker is gone; the reader reports it.
        }
    }
}
