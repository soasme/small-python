package io.github.soasme.spy;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class InterpreterTest {
    private final Interpreter py = Interpreter.create();

    @AfterEach
    void close() {
        py.close();
    }

    private <T> T eval(String source, Class<T> type) {
        return py.eval(source).as(type);
    }

    private PythonException raises(Runnable r) {
        return assertThrows(PythonException.class, r::run);
    }

    @Test
    void evaluatesAndConverts() {
        assertEquals(42L, eval("6 * 7", Long.class));
        assertEquals(42, eval("6 * 7", int.class));
        assertEquals(0.25, eval("1 / 4", Double.class));
        assertEquals(2.0, eval("2", Double.class));
        assertEquals("spyspy", eval("'spy' * 2", String.class));
        assertEquals(true, eval("1 < 2", Boolean.class));
        assertArrayEquals(new byte[] {'a', 'b'}, eval("b'ab'", byte[].class));
        assertArrayEquals(new byte[] {'a', 'b'}, eval("bytearray(b'ab')", byte[].class));
        assertEquals("\udc80", eval("'\\udc80'", String.class));
        assertEquals("\uD83D\uDE00", eval("'\\U0001F600'", String.class));
        assertEquals(new BigInteger("18446744073709551616"), eval("2 ** 64", BigInteger.class));
        assertEquals(new BigInteger("-18446744073709551616"), py.eval("-2 ** 64").toJava());
        assertEquals(PyTuple.of(1L, "a"), eval("(1, 'a')", PyTuple.class));
        assertEquals(Arrays.asList(null, true, 1L, 1.5, "s", PyTuple.of(1L), Map.of(1L, "x")),
                py.eval("[None, True, 1, 1.5, 's', (1,), {1: 'x'}]").toJava());
        assertEquals(List.of(0L, 1L, 4L), eval("(n * n for n in range(3))", List.class));
        assertTrue(py.eval("None").isNone());
        assertEquals(null, eval("None", Long.class));
        assertEquals("TypeError", raises(() -> eval("None", long.class)).getType());
        assertTrue(py.eval("object()").toJava() instanceof PyObject);
    }

    @Test
    void reportsExceptions() {
        PythonException e = raises(() -> py.exec("x = 1\nraise ValueError('bad')"));
        assertEquals("ValueError", e.getType());
        assertEquals("bad", e.getPythonMessage());
        assertEquals("<string>", e.getFilename());
        assertEquals(2, e.getLine());
        assertEquals("ValueError: bad", e.getMessage());
        assertEquals(1L, eval("x", Long.class));
        assertEquals("TypeError", raises(() -> eval("'a'", Byte.class)).getType());
        assertEquals("OverflowError", raises(() -> eval("1000", Byte.class)).getType());
        assertEquals("OverflowError", raises(() -> eval("2 ** 64", Long.class)).getType());
        assertEquals("SyntaxError", raises(() -> py.eval("1 +")).getType());
        assertEquals("SyntaxError", raises(() -> py.eval("a\0")).getType());
        assertEquals("ValueError", raises(() -> py.get("a\0")).getType());
        assertEquals("TypeError", raises(() -> eval("1", Boolean.class)).getType());
        assertEquals("NameError", raises(() -> py.get("missing")).getType());
    }

    @Test
    void globalsRoundTrip() {
        py.set("items", List.of("a", "b"));
        py.set("pair", PyTuple.of(1, 2.5));
        py.set("big", BigInteger.valueOf(Long.MIN_VALUE));
        assertEquals("a-b", eval("'-'.join(items)", String.class));
        assertEquals(3.5, eval("pair[0] + pair[1]", Double.class));
        assertEquals("tuple", eval("type(pair).__name__", String.class));
        assertEquals(true, eval("big == -2 ** 63", Boolean.class));
        assertEquals("OverflowError", raises(() -> py.set("big", BigInteger.ONE.shiftLeft(63))).getType());
        assertEquals("TypeError", raises(() -> py.set("t", new Thread())).getType());
        py.get("items").getAttr("append").call("c");
        assertEquals(List.of("a", "b", "c"), py.get("items").as(List.class));
        py.set("s", "\udc80\uD83D\uDE00");
        assertEquals(true, eval("s == '\\udc80\\U0001F600'", Boolean.class));
    }

    @Test
    void hostFunctions() {
        py.define("add", (rt, args) -> args.get(0, Long.class) + args.get(1, Long.class));
        py.define("greet", (rt, args) -> "hello " + args.get(0, String.class) + args.keyword("end", String.class, "!"));
        py.define("apply", (rt, args) -> args.positional().get(0).call(args.positional().get(1)));
        assertEquals(42L, eval("add(40, 2)", Long.class));
        assertEquals("hello spy!", eval("greet('spy')", String.class));
        assertEquals("hello spy?", eval("greet('spy', end='?')", String.class));
        assertEquals(42L, eval("apply(lambda n: n * 2, 21)", Long.class));
        assertEquals("TypeError: expected at least 2 arguments, got 1", raises(() -> py.eval("add(1)")).getMessage());
        py.exec("try:\n    add('a', 1)\nexcept TypeError as e:\n    caught = 'yes'");
        assertEquals("yes", eval("caught", String.class));
        PyObject f = py.function("twice", (rt, args) -> args.get(0, Long.class) * 2);
        assertEquals(10L, f.call(5).as(Long.class));
    }

    @Test
    void hostErrorsBecomeExceptions() {
        py.define("fail", (rt, args) -> {
            throw new PythonException("KeyError", "missing");
        });
        py.define("wrapped", (rt, args) -> {
            throw new IOException("disk on fire");
        });
        py.define("boom", (rt, args) -> {
            throw new StackOverflowError();
        });
        py.exec("try:\n    fail()\nexcept KeyError:\n    ok = True");
        assertEquals(true, eval("ok", Boolean.class));
        assertEquals("RuntimeError: disk on fire", raises(() -> py.eval("wrapped()")).getMessage());
        assertEquals("RuntimeError: java.lang.StackOverflowError", raises(() -> py.eval("boom()")).getMessage());
        assertEquals(1L, eval("1", Long.class));
    }

    @Test
    void outputLoaderAndModules() {
        StringBuilder printed = new StringBuilder();
        py.setOutput(printed);
        py.setLoader(name -> name.equals("greeting") ? "WORD = 'hi'\n" : null);
        py.registerModule("native", (rt, module) -> {
            module.setAttr("answer", 42);
            rt.execModule(module, "double = answer * 2", "<native>");
        });
        py.exec("import greeting, native\nprint(greeting.WORD, native.double, '\\udc80')");
        assertEquals("hi 84 \udc80\n", printed.toString());
        assertEquals("ModuleNotFoundError", raises(() -> py.exec("import nothing")).getType());
        py.setLoader(name -> {
            throw new PythonException("ImportError", "the loader is broken");
        });
        assertEquals("ImportError: the loader is broken", raises(() -> py.exec("import other")).getMessage());
        py.setOutput(null);
        assertEquals("OSError", raises(() -> py.exec("print(1)")).getType());
    }

    @Test
    void stdModulesAreOptional() {
        py.exec("import sys");
        try (Interpreter bare = Interpreter.createBare()) {
            assertEquals("ModuleNotFoundError", raises(() -> bare.exec("import sys")).getType());
        }
        assertEquals(System.getProperty("project.version"), Interpreter.version());
    }

    @Test
    void limits() {
        py.setLimit(Limit.STEPS, 10_000);
        assertEquals("RuntimeError", raises(() -> py.exec("while True: pass")).getType());
        long used = py.stepsUsed();
        assertTrue(used > 9_990 && used <= 10_000, "steps used " + used);
        assertEquals(2L, eval("1 + 1", Long.class));
        py.setLimit(Limit.STEPS, 0);
        StringBuilder out = new StringBuilder();
        py.setOutput(out);
        py.setLimit(Limit.OUTPUT, 4);
        assertEquals(4, py.getLimit(Limit.OUTPUT));
        assertEquals("output limit exceeded", raises(() -> py.exec("print('hello')")).getPythonMessage());
        assertEquals("", out.toString());
        assertEquals("ValueError", raises(() -> py.setLimit(Limit.INT_DIGITS, 100)).getType());
    }

    @Test
    void iterationAndItems() {
        List<Long> got = new ArrayList<>();
        for (PyObject v : py.eval("(n * n for n in range(4))")) {
            got.add(v.as(Long.class));
        }
        assertEquals(List.of(0L, 1L, 4L, 9L), got);
        PyObject d = py.eval("{}");
        d.setItem("k", List.of(1, 2));
        assertEquals("[1, 2]", d.getItem("k").toString());
        assertEquals("KeyError", raises(() -> d.getItem("x")).getType());
        assertFalse(py.eval("[]").truth());
        PyObject failing = py.eval("(1 // 0 for _ in range(1))");
        assertEquals("ZeroDivisionError", raises(() -> failing.iterator().hasNext()).getType());
        PyObject f = py.eval("lambda x, *, y=0: x + y");
        assertEquals(3L, f.callKeywords(List.of(1), Map.of("y", 2)).as(Long.class));
    }

    record Doc(String title, List<String> tags, Integer rank, int count, Map<String, Long> extra) {}

    @Test
    void recordsAndMaps() {
        Doc doc = new Doc("t", List.of("a"), null, 3, Map.of("x", 1L));
        PyObject v = py.toValue(doc);
        assertEquals("{'title': 't', 'tags': ['a'], 'rank': None, 'count': 3, 'extra': {'x': 1}}", v.repr());
        assertEquals(doc, v.as(Doc.class));
        assertEquals(new Doc("only", null, null, 0, null), eval("{'title': 'only', 'unknown': 1}", Doc.class));
        assertEquals("{1: 'a', 2: 'b', 3: 'c'}", py.toValue(new TreeMap<>(Map.of(3, "c", 1, "a", 2, "b"))).repr());
        assertEquals("TypeError", raises(() -> eval("{'title': 1}", Doc.class)).getType());
    }

    @Test
    void valuesOfAnotherInterpreterAreRefused() {
        try (Interpreter other = Interpreter.create()) {
            PyObject v = other.eval("[]");
            assertEquals("ValueError", raises(() -> py.set("x", v)).getType());
        }
    }

    @Test
    void closedInterpreter() {
        Interpreter rt = Interpreter.create();
        PyObject v = rt.eval("[]");
        rt.close();
        rt.close();
        assertThrows(IllegalStateException.class, () -> rt.eval("1"));
        assertThrows(IllegalStateException.class, v::repr);
    }

    @Test
    void releasedValuesAreFreed() throws InterruptedException {
        py.exec("freed = []\nclass Box:\n    def __del__(self): freed.append(1)");
        for (int i = 0; i < 100; i++) {
            py.eval("Box()");
        }
        for (int i = 0; i < 50 && eval("len(freed)", Long.class) < 100; i++) {
            System.gc();
            Thread.sleep(10);
        }
        assertEquals(100L, eval("len(freed)", Long.class));
    }

    @Test
    void policy() {
        List<String> events = new ArrayList<>();
        py.setPolicy((event, args) -> {
            events.add(event + "/" + args.size());
            switch (event) {
                case "exec" -> throw new SecurityException("no exec here");
                case "net.fetch" -> throw new PythonException("ConnectionRefusedError", "blocked host");
                default -> {}
            }
        });
        assertEquals("PermissionError: no exec here", raises(() -> py.exec("exec('1')")).getMessage());
        assertEquals("ConnectionRefusedError", raises(() -> py.checkPolicy("net.fetch", "https://example.com")).getType());
        py.checkPolicy("storage.save");
        assertEquals(List.of("exec/1", "net.fetch/1", "storage.save/0"), events);
        py.setPolicy(null);
        py.exec("exec('1')");
    }

    @Test
    void mounts(@TempDir Path dir) throws IOException {
        Files.writeString(dir.resolve("note.txt"), "from the host");
        py.mount(dir, "/data", true);
        assertEquals("from the host", eval("open('/data/note.txt').read()", String.class));
        assertEquals("OSError", raises(() -> py.exec("open('/data/new.txt', 'w')")).getType());
        assertEquals("PermissionError", raises(() -> py.exec("open('/etc/hosts')")).getType());
    }

    @Test
    void threadsTakeTurns() throws InterruptedException {
        py.define("bump", (rt, args) -> rt.eval("n + 1"));
        py.exec("n = 0");
        List<Thread> threads = new ArrayList<>();
        for (int t = 0; t < 4; t++) {
            Thread thread = new Thread(() -> {
                for (int i = 0; i < 250; i++) {
                    py.exec("n = bump()");
                }
            });
            thread.start();
            threads.add(thread);
        }
        for (Thread t : threads) {
            t.join();
        }
        assertEquals(1000L, eval("n", Long.class));
    }
}
