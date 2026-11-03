package io.github.soasme.spy.worker;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledOnOs;
import org.junit.jupiter.api.condition.OS;
import org.junit.jupiter.api.io.TempDir;

class InterpreterTest {
    private final List<Interpreter> started = new ArrayList<>();

    private Interpreter start(Interpreter.Builder b) {
        Interpreter py = b.start();
        started.add(py);
        return py;
    }

    private Interpreter start() {
        return start(Interpreter.builder());
    }

    @AfterEach
    void close() {
        started.forEach(Interpreter::close);
    }

    private static PythonException raises(Runnable r) {
        return assertThrows(PythonException.class, r::run);
    }

    @Test
    void evaluatesAndConverts() {
        Interpreter py = start();
        assertEquals(System.getProperty("project.version"), py.version());
        assertEquals(42L, py.eval("6 * 7"));
        BigInteger two64 = BigInteger.ONE.shiftLeft(64);
        assertEquals(two64, py.eval("2 ** 64"));
        assertEquals(Long.MIN_VALUE, py.eval("-2 ** 63"));
        assertEquals(new PyComplex(0.5, 1), py.eval("1j + 0.5"));
        assertEquals("\udc80x\uD83D\uDE00", py.eval("'\\udc80x\\U0001F600'"));
        List<?> values = (List<?>) py.eval("[None, True, b'a', bytearray(b'b'), (1,), {1: 'x'}, {2}, frozenset()]");
        assertArrayEquals(new byte[] {'a'}, (byte[]) values.get(2));
        assertEquals(Arrays.asList(null, true), values.subList(0, 2));
        assertEquals(List.of(new PyByteArray(new byte[] {'b'}), PyTuple.of(1L), PyDict.of(1L, "x"), PySet.of(2L),
                PyFrozenSet.of()), values.subList(3, 8));
        py.set("big", two64.negate());
        assertEquals(true, py.eval("big == -2 ** 64"));
        py.set("s", "\udc80");
        assertEquals(true, py.eval("s == '\\udc80'"));
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("b", BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE));
        m.put("a", List.of(1.5f, 'c'));
        py.set("m", m);
        assertEquals("{'b': 18446744073709551615, 'a': [1.5, 'c']}", py.eval("repr(m)"));
        assertEquals("TypeError", raises(() -> py.set("t", new Thread())).getType());
        List<Object> deep = new ArrayList<>();
        deep.add(deep);
        assertEquals("RecursionError", raises(() -> py.set("d", deep)).getType());
    }

    @Test
    void globals() {
        Interpreter py = start();
        py.set("x", 1);
        assertEquals(1L, py.get("x"));
        assertInstanceOf(PyObject.class, py.get("len"));
        py.delete("x");
        assertEquals("NameError", raises(() -> py.get("x")).getType());
        assertEquals("KeyError", raises(() -> py.delete("x")).getType());
    }

    @Test
    void exceptionsCarryTheirPlace() {
        Interpreter py = start();
        PythonException e = raises(() -> py.exec("x = 1\nraise ValueError('bad')"));
        assertEquals("ValueError: bad", e.getMessage());
        assertEquals(2, e.getLine());
        assertEquals("<string>", e.getFilename());
        assertEquals("ValueError('bad')", e.getObject().repr());
    }

    @Test
    void hostFunctionsAndNestedRequests() {
        Interpreter py = start();
        py.define("add", (rt, args, kwargs) -> {
            if (args.size() == 2 && args.get(0) instanceof Long a && args.get(1) instanceof Long b) {
                return a + b;
            }
            throw new PythonException("TypeError", "add(a, b)");
        });
        // Recursion through the engine and back, several levels deep.
        py.define("down", (rt, args, kwargs) -> {
            long n = (Long) args.get(0);
            return n == 0 ? 0L : (Long) rt.call("step", n - 1) + 1;
        });
        py.exec("def step(n):\n    return down(n)");
        assertEquals(42L, py.eval("add(40, 2)"));
        assertEquals(10L, py.eval("down(10)"));
        assertEquals("TypeError: add(a, b)", raises(() -> py.eval("add('a')")).getMessage());
        py.define("named", (rt, args, kwargs) -> String.join(",", kwargs.keySet()));
        assertEquals("key,other", py.eval("named(key=1, other=2)"));
        py.define("nested_eval", (rt, args, kwargs) -> rt.eval("1"));
        assertEquals("ValueError", raises(() -> py.eval("nested_eval()")).getType());
        PyFunction twice = py.function("twice", (rt, args, kwargs) -> (Long) args.get(0) * 2);
        assertEquals(84L, py.callKeywords(twice, List.of(42L), Map.of()));
        assertEquals("twice", ((PyObject) py.eval("lambda f: f")).call(twice) instanceof PyObject f
                ? f.getAttr("__name__") : null);
    }

    @Test
    void hostErrorsComeBackAsTheirCause() {
        Interpreter py = start();
        IOException fire = new IOException("disk on fire");
        py.define("fail", (rt, args, kwargs) -> {
            throw fire;
        });
        PythonException e = raises(() -> py.eval("fail()"));
        assertEquals("RuntimeError", e.getType());
        assertSame(fire, e.getCause());
        py.exec("try:\n    fail()\nexcept RuntimeError as e:\n    caught = str(e)");
        assertEquals("disk on fire", py.get("caught"));
        // An engine exception passing through a host function keeps its identity.
        py.define("relay", (rt, args, kwargs) -> rt.call("boom"));
        py.exec("class Boom(Exception): pass\ndef boom(): raise Boom(7)");
        py.exec("try:\n    relay()\nexcept Boom as e:\n    got = e.args");
        assertEquals(PyTuple.of(7L), py.get("got"));
    }

    @Test
    void objects() {
        Interpreter py = start();
        PyObject d = (PyObject) py.eval("type('D', (dict,), {})(a=1)");
        assertEquals(1L, d.getItem("a"));
        d.setItem("b", 2);
        assertEquals(2, d.len());
        assertTrue(d.contains("b"));
        assertTrue(d.truth());
        assertEquals("KeyError", raises(() -> d.getItem("zz")).getType());
        assertEquals("{'a': 1, 'b': 2}", d.repr());
        assertEquals("{'a': 1, 'b': 2}", d.str());
        d.setAttr("note", "hi");
        assertEquals("hi", d.getAttr("note"));
        assertEquals(false, d.compare(Compare.EQ, PyDict.of()));
        assertEquals(true, d.compare(Compare.NE, PyDict.of()));
        assertTrue(d.dir().contains("note"));
        assertEquals("TypeError", raises(d::hash).getType());
        List<Object> keys = new ArrayList<>();
        d.forEach(keys::add);
        assertEquals(List.of("a", "b"), keys);
        PyObject f = (PyObject) py.eval("lambda x, *, y=0: x + y");
        assertEquals(3L, f.callKeywords(List.of(1), Map.of("y", 2)));
        assertEquals(1L, f.call(1));
        Interpreter other = start();
        assertThrows(IllegalArgumentException.class, () -> other.set("x", f));
    }

    @Test
    void releasedHandlesAreFreed() throws InterruptedException {
        Interpreter py = start();
        py.exec("freed = []\nclass Box:\n    def __del__(self): freed.append(1)");
        for (int i = 0; i < 100; i++) {
            py.eval("Box()");
        }
        for (int i = 0; i < 50 && !py.eval("len(freed)").equals(100L); i++) {
            System.gc();
            Thread.sleep(10);
            py.collect();
        }
        assertEquals(100L, py.eval("len(freed)"));
    }

    @Test
    void outputAndLoader() {
        StringBuilder printed = new StringBuilder();
        Interpreter py = start(Interpreter.builder().output(printed)
                .loader(name -> name.equals("hello") ? "WORD = 'hi'" : null));
        py.registerModule("native", Map.of("answer", 42), "double = answer * 2");
        py.exec("import hello, native\nprint(hello.WORD, native.double)");
        assertEquals("hi 84\n", printed.toString());
        assertEquals("ModuleNotFoundError", raises(() -> py.exec("import nothing")).getType());
    }

    @Test
    void limits() {
        Interpreter py = start(Interpreter.builder().stepLimit(10_000).memoryLimit(16 << 20));
        assertEquals("RuntimeError", raises(() -> py.exec("while True: pass")).getType());
        Interpreter.Usage usage = py.usage();
        assertTrue(usage.steps() > 9_990 && usage.steps() <= 10_000 && usage.memory() > 0, usage.toString());
        assertEquals("MemoryError", raises(() -> py.exec("x = 'a' * (64 << 20)")).getType());
        assertEquals(2L, py.eval("1 + 1"));
        assertThrows(IllegalArgumentException.class, () -> Interpreter.builder().stepLimit(-1));
        assertThrows(IllegalArgumentException.class, () -> start(Interpreter.builder().messageLimit(64)));
        Interpreter small = start(Interpreter.builder().messageLimit(1024));
        assertThrows(IllegalArgumentException.class, () -> small.set("s", "x".repeat(2000)));
        assertEquals(1L, small.eval("1"));
        assertEquals("OverflowError", raises(() -> small.eval("'x' * 2000")).getType());
        assertEquals(1L, small.eval("1"));
    }

    @Test
    void outputLimit() {
        StringBuilder printed = new StringBuilder();
        Interpreter py = start(Interpreter.builder().outputLimit(8).output(printed));
        PythonException e = raises(() -> py.exec("print('1234')\ntry:\n    print('56789')\nexcept BaseException:\n    print('caught')"));
        assertEquals("RuntimeError: output limit exceeded", e.getMessage());
        assertEquals("1234\n", printed.toString());
        py.exec("print('again')");
    }

    @Test
    void policy() {
        List<String> events = new ArrayList<>();
        SecurityException refused = new SecurityException("no files");
        Interpreter py = start(Interpreter.builder().loader(name -> "").policy((event, args) -> {
            events.add(event + args.items());
            switch (event) {
                case "open" -> throw refused;
                case "import" -> throw new PythonException("TypeError", "no modules");
                default -> {}
            }
        }));
        assertEquals(42L, py.eval("eval('6 * 7')"));
        PythonException e = raises(() -> py.exec("open('/etc/passwd')"));
        assertEquals("PermissionError: no files", e.getMessage());
        assertSame(refused, e.getCause());
        assertEquals("TypeError", raises(() -> py.exec("import m")).getType());
        assertEquals(List.of("exec[6 * 7]", "open[/etc/passwd, r]", "import[m]"), events);
    }

    @Test
    void timeoutStopsTheOperationButNotWhileTheHostRuns() {
        Interpreter py = start(Interpreter.builder().timeout(Duration.ofMillis(300)));
        py.define("slow", (rt, args, kwargs) -> {
            Thread.sleep(500);
            return null;
        });
        py.eval("slow()");
        long started = System.nanoTime();
        assertThrows(OperationTimeoutException.class, () -> py.exec("while True: pass"));
        assertTrue(System.nanoTime() - started < 5_000_000_000L, "the timeout took too long");
        assertFalse(py.isClosed());
        assertEquals(1L, py.eval("1"));
    }

    @Test
    @EnabledOnOs({OS.LINUX, OS.MAC})
    void aCrashedWorkerIsLost() throws Exception {
        for (String signal : List.of("SEGV", "ABRT", "KILL")) {
            Interpreter py = start();
            long pid = py.pid();
            py.define("crash", (rt, args, kwargs) -> new ProcessBuilder("kill", "-" + signal, "" + pid).start().waitFor());
            WorkerException e = assertThrows(WorkerException.class,
                    () -> py.eval("crash() or [0 for _ in range(10**9)]"), signal);
            assertTrue(e.exitStatus().isPresent(), signal);
            assertSame(e, assertThrows(WorkerException.class, () -> py.eval("1")));
            assertTrue(py.isClosed());
        }
    }

    @Test
    void anErrorInAHostFunctionLosesTheWorker() {
        Interpreter py = start();
        py.define("boom", (rt, args, kwargs) -> {
            throw new AssertionError("boom");
        });
        assertThrows(AssertionError.class, () -> py.eval("boom()"));
        assertThrows(WorkerException.class, () -> py.eval("1"));
    }

    @Test
    void closeIsGraceful() {
        Interpreter py = start();
        py.close();
        py.close();
        assertTrue(py.isClosed());
        assertThrows(IllegalStateException.class, () -> py.eval("1"));
    }

    @Test
    void aMissingWorkerFailsToStart(@TempDir Path dir) {
        assertThrows(WorkerException.class, () -> Interpreter.builder().worker(dir.resolve("none")).start());
    }

    @Test
    @EnabledOnOs(OS.MAC)
    void theWorkerIsSandboxedOnceCodeRuns(@TempDir Path dir) {
        Interpreter py = start();
        py.mount(dir, "/data", true);
        py.eval("1");
        assertEquals("PermissionError", raises(() -> py.mount(dir, "/more", true)).getType());
    }
}
