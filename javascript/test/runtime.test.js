import assert from "node:assert/strict";
import { after, afterEach, before, describe, test } from "node:test";

import { Complex, keywords, PyObject, PythonError, Runtime, WorkerError } from "../index.js";

// Runtimes made by a test are closed after it.
const open = [];
const track = (rt) => (open.push(rt), rt);
afterEach(() => { for (const rt of open.splice(0)) rt.close(); });

describe("values", () => {
  let rt;
  before(async () => { rt = await Runtime.create(); });
  after(() => rt.close());

  test("engine to JavaScript", async () => {
    assert.equal(rt.version, "0.3.0");
    assert.deepEqual(await rt.eval("[None, True, 3, 1.5, 'é', b'\\x00a', bytearray(b'z'), (1,), {2}, frozenset()]"),
      [null, true, 3, 1.5, "é", new Uint8Array([0, 97]), new Uint8Array([122]), [1], new Set([2]), new Set()]);
    assert.deepEqual(await rt.eval("{'a': 1, 2: [3]}"), new Map([["a", 1], [2, [3]]]));
    assert.equal(await rt.eval("2**53 - 1"), Number.MAX_SAFE_INTEGER);
    assert.equal(await rt.eval("2**53"), 2n ** 53n);
    assert.equal(await rt.eval("-2**100"), -(2n ** 100n));
    assert.deepEqual(await rt.eval("1 - 2j"), new Complex(1, -2));
    assert.equal(await rt.eval("'\\ud800'"), "\ud800");
    assert.equal(await rt.eval("'\\U0001f600'"), "😀");
  });

  test("JavaScript to engine", async () => {
    const cases = [
      [null, "None"], [undefined, "None"], [true, "True"], [7, "7"], [-0, "-0.0"], [0.5, "0.5"], [NaN, "nan"],
      [2n ** 70n, String(2n ** 70n)], ["\ud800😀", "'\\ud800😀'"], [new Uint8Array([1]), "b'\\x01'"],
      [[1, [2]], "[1, [2]]"], [new Set([1]), "{1}"], [new Map([[1, "a"]]), "{1: 'a'}"], [{ a: 1 }, "{'a': 1}"],
      [Object.assign(Object.create(null), { b: 2 }), "{'b': 2}"], [new Complex(0, 1), "1j"],
    ];
    for (const [value, expected] of cases) {
      await rt.set("v", value);
      assert.equal(await rt.eval("repr(v)"), expected, String(expected));
    }
  });

  test("unconvertible values", async () => {
    await assert.rejects(rt.set("v", new Date()), TypeError);
    await assert.rejects(rt.set("v", Symbol("s")), TypeError);
    let deep = [];
    for (let i = 0; i < 300; i++) deep = [deep];
    await assert.rejects(rt.set("v", deep), TypeError);
    await assert.rejects(rt.eval("d = []\nfor _ in range(300):\n    d = [d]\nd"), (e) => e.type === "RecursionError");
  });

  test("engine subclasses stay objects", async () => {
    const value = await rt.eval("class D(dict):\n    pass\nD(a=1)");
    assert.ok(value instanceof PyObject);
    assert.equal(await value.getItem("a"), 1);
  });
});

describe("host functions", () => {
  test("define, keywords, async, nesting", async () => {
    const rt = track(await Runtime.create());
    await rt.define("add", (a, b = 10) => a + b);
    assert.equal(await rt.eval("add(1)"), 11);
    assert.equal(await rt.eval("add.__name__"), "add");
    await assert.rejects(rt.eval("add(1, b=2)"), (e) => e.type === "TypeError");
    await rt.define("kw", keywords((a, kw) => [a, kw.scale ?? 1]));
    assert.deepEqual(await rt.eval("kw(1), kw(2, scale=3)"), [[1, 1], [2, 3]]);
    await rt.define("later", async (n) => { await new Promise((r) => setTimeout(r, 5)); return n * 2; });
    assert.equal(await rt.eval("later(21)"), 42);
    await rt.define("apply", (f, n) => f.call([n]));
    assert.equal(await rt.eval("apply(lambda n: -n, 7)"), -7);
    await rt.define("down", (f, n) => (n ? f.call([n - 1]) : 0));
    await rt.exec("def up(n):\n    return down(up, n) + 1");
    assert.equal(await rt.eval("up(20)"), 21);
  });

  test("parallel nested calls from one host function", async () => {
    const rt = track(await Runtime.create());
    await rt.exec("def square(n): return n * n");
    await rt.define("both", async (f) => Promise.all([f.call([3]), f.call([4]), rt.get("square")]).then(([a, b]) => a + b));
    assert.equal(await rt.eval("both(square)"), 25);
  });

  test("exceptions cross both ways", async () => {
    const rt = track(await Runtime.create());
    const original = new TypeError("bad type");
    await rt.define("fail", () => { throw original; });
    await rt.exec("try:\n    fail()\nexcept TypeError as e:\n    caught = repr(e)");
    assert.equal(await rt.get("caught"), "TypeError('bad type')");
    const error = await rt.eval("fail()").catch((e) => e);
    assert.ok(error instanceof PythonError);
    assert.equal(error.type, "TypeError");
    assert.equal(error.cause, original);
    await rt.define("weird", () => { throw 42; });
    assert.equal(await rt.eval("(lambda: weird())()").catch((e) => e.type), "RuntimeError");
    await rt.define("passthrough", (f) => f.call([]));
    await rt.exec("class Mine(Exception): pass\ndef boom(): raise Mine('x')");
    await rt.exec("try:\n    passthrough(boom)\nexcept Mine:\n    kept = True");
    assert.equal(await rt.get("kept"), true);
  });

  test("eval from a host function is refused", async () => {
    const rt = track(await Runtime.create());
    await rt.define("again", () => rt.eval("1"));
    const error = await rt.eval("again()").catch((e) => e);
    assert.match(error.message, /host function/);
  });
});

describe("runtime", () => {
  test("errors", async () => {
    const rt = track(await Runtime.create());
    const error = await rt.exec("x = 1\nraise ValueError('bad')", "prog.py").catch((e) => e);
    assert.equal(String(error), "ValueError: bad");
    assert.equal(error.filename, "prog.py");
    assert.equal(error.lineno, 2);
    assert.ok(error.exception instanceof PyObject);
    assert.deepEqual(await error.exception.get("args"), ["bad"]);
    assert.equal((await rt.get("nope").catch((e) => e)).type, "NameError");
    assert.equal((await rt.eval("1 +").catch((e) => e)).type, "SyntaxError");
    assert.equal((await rt.eval("a\0").catch((e) => e)).type, "SyntaxError");
  });

  test("globals and calls", async () => {
    const rt = track(await Runtime.create());
    await rt.set("config", { retries: 3 });
    await rt.exec("count = config['retries'] * 2");
    assert.equal(await rt.get("count"), 6);
    await rt.delete("count");
    assert.equal((await rt.delete("count").catch((e) => e)).type, "KeyError");
    assert.deepEqual(await rt.call("sorted", [[3, 1, 2]], { reverse: true }), [3, 2, 1]);
  });

  test("objects", async () => {
    const rt = track(await Runtime.create());
    const c = await rt.eval("class C:\n    n = 1\n    def bump(self, by=1):\n        self.n += by\n        return self.n\nC()");
    assert.equal(await (await c.get("bump")).call([], { by: 5 }), 6);
    await c.set("n", 100);
    assert.equal(await c.get("n"), 100);
    const items = await rt.eval("[1, 2]");
    assert.deepEqual(items, [1, 2]);
    const list = await rt.eval("class L(list): pass\nL([1, 2])");
    assert.equal(await list.len(), 2);
    assert.equal(await list.has(2), true);
    await list.setItem(0, 9);
    assert.equal(await list.getItem(0), 9);
    assert.equal(await list.compare("==", [9, 2]), true);
    assert.equal(await list.bool(), true);
    assert.equal(await list.repr(), "[9, 2]");
    assert.ok((await list.dir()).includes("append"));
    const seen = [];
    for await (const x of list) seen.push(x);
    assert.deepEqual(seen, [9, 2]);
    assert.equal((await (await rt.eval("object()")).hash().then((h) => typeof h)), "number");
    list.release();
    await assert.rejects(list.len(), TypeError);
    const other = await Runtime.create();
    await assert.rejects(other.set("x", c), TypeError);
    other.close();
  });

  test("modules and loader", async () => {
    const sources = { greeting: "WORD = 'hi'", "pkg.__init__": "", "pkg.mod": "X = 2" };
    const rt = track(await Runtime.create({ loader: async (name) => sources[name] ?? null }));
    await rt.registerModule("web", { get: (url) => `<${url}>`, TIMEOUT: 30 }, "def title(u): return get(u).upper()");
    assert.equal(await rt.eval("import web\nweb.title('a')"), "<A>");
    assert.equal(await rt.eval("import greeting\ngreeting.WORD"), "hi");
    assert.equal(await rt.eval("import pkg.mod\npkg.mod.X"), 2);
    assert.equal((await rt.exec("import nowhere").catch((e) => e)).type, "ModuleNotFoundError");
  });

  test("output", async () => {
    const chunks = [];
    const rt = track(await Runtime.create({ output: (text) => { chunks.push(text); } }));
    await rt.exec("print('total:', 3)\nprint('done', end='')");
    assert.equal(chunks.join(""), "total: 3\ndone");
    const broken = track(await Runtime.create({ output: () => { throw new Error("no"); } }));
    const original = console.error;
    console.error = () => {};
    try {
      assert.equal((await broken.exec("print('x')").catch((e) => e)).type, "OSError");
    } finally {
      console.error = original;
    }
  });

  test("std option", async () => {
    const rt = track(await Runtime.create());
    await rt.exec("import sys, gc");
    const bare = track(await Runtime.create({ std: false }));
    assert.equal((await bare.exec("import sys").catch((e) => e)).type, "ModuleNotFoundError");
  });

  test("operations queue in order", async () => {
    const rt = track(await Runtime.create());
    await rt.exec("log = []");
    await Promise.all([1, 2, 3, 4].map((n) => rt.exec(`log.append(${n})`)));
    assert.deepEqual(await rt.get("log"), [1, 2, 3, 4]);
  });

  test("close", async () => {
    const rt = await Runtime.create();
    const obj = await rt.eval("object()");
    rt.close();
    rt.close();
    assert.ok(rt.closed);
    await assert.rejects(rt.eval("1"), /closed/);
    await assert.rejects(obj.repr(), /closed/);
    assert.ok(!(await rt.eval("1").catch((e) => e) instanceof WorkerError));
  });
});
