import assert from "node:assert/strict";
import { afterEach, describe, test } from "node:test";

import { PythonError, Runtime, Timeout, WorkerError } from "../index.js";

const CASES = ["unknown kind", "unknown tag", "truncated value", "trailing bytes", "count over message",
  "invalid utf-8", "non-canonical int", "deep nesting", "unknown function", "parent-only tag", "malformed error",
  "length over limit", "zero length", "exit"];

// Node workers inherit the environment; the fake reads its case from it.
async function withFake(name, timeout, body) {
  const real = Runtime._workerURL;
  Runtime._workerURL = new URL("./fake-worker.js", import.meta.url);
  process.env.FAKE_WORKER_CASE = name;
  try {
    return await body(await Runtime.create({ timeout }));
  } finally {
    Runtime._workerURL = real;
    delete process.env.FAKE_WORKER_CASE;
  }
}

// Runtimes made by a test are closed after it.
const open = [];
const track = (rt) => (open.push(rt), rt);
afterEach(() => { for (const rt of open.splice(0)) rt.close(); });

describe("hostile worker", () => {
  for (const name of CASES)
    test(name, () => withFake(name, 10000, async (rt) => {
      const error = await rt.eval("1").catch((e) => e);
      assert.ok(error instanceof WorkerError && !(error instanceof Timeout), String(error));
      assert.match(error.message, name === "exit" ? /status 5/ : /broke the protocol/);
      assert.ok(rt.closed);
      await assert.rejects(rt.eval("1"), WorkerError);
    }));

  test("silent worker times out", () => withFake("silent", 300, async (rt) => {
    await assert.rejects(rt.eval("1"), Timeout);
  }));
});

describe("limits", () => {
  test("timeout", async () => {
    const rt = await Runtime.create({ timeout: 300 });
    const started = Date.now();
    const error = await rt.exec("while True:\n    pass").catch((e) => e);
    assert.ok(error instanceof Timeout && error instanceof WorkerError);
    assert.ok(Date.now() - started < 5000);
    assert.ok(rt.closed);
    await assert.rejects(rt.eval("1"), Timeout);
  });

  test("timeout excludes host time", async () => {
    const rt = track(await Runtime.create({ timeout: 300 }));
    await rt.define("slow", () => new Promise((r) => setTimeout(r, 200)));
    await rt.exec("for _ in range(4):\n    slow()");
    assert.equal(await rt.eval("1"), 1);
  });

  test("memory limit", async () => {
    const rt = track(await Runtime.create({ memoryLimit: 32 << 20 }));
    assert.equal((await rt.exec("x = 'a' * (64 << 20)").catch((e) => e)).type, "MemoryError");
    await rt.exec("try:\n    chunks = [bytes(1 << 20) for _ in range(100)]\nexcept MemoryError:\n    caught = True");
    assert.equal(await rt.get("caught"), true);
    assert.equal(await rt.eval("len('b' * (8 << 20))"), 8 << 20);
  });

  test("message limit", async () => {
    const rt = track(await Runtime.create({ messageLimit: 1 << 16 }));
    assert.equal((await rt.eval("'x' * (1 << 17)").catch((e) => e)).type, "OverflowError");
    await assert.rejects(rt.set("big", "y".repeat(1 << 17)), RangeError);
    await rt.define("big", () => "z".repeat(1 << 17));
    await assert.rejects(rt.eval("big()"), PythonError);
    assert.equal(await rt.eval("len('x' * 100)"), 100);
  });

  test("large messages cross the inbox in chunks", async () => {
    const rt = track(await Runtime.create());
    const text = "q".repeat(1 << 20);
    await rt.set("t", text);
    assert.equal(await rt.eval("len(t)"), 1 << 20);
    assert.equal(await rt.get("t"), text);
  });

  test("bad options", async () => {
    for (const options of [{ memoryLimit: -1 }, { timeout: 0 }, { messageLimit: 0 }, { stepLimit: 1.5 }])
      await assert.rejects(Runtime.create(options), RangeError);
    await assert.rejects(Runtime.create({ output: 1 }), TypeError);
  });

  test("step limit", async () => {
    const rt = track(await Runtime.create({ stepLimit: 10000 }));
    assert.equal((await rt.exec("while True:\n    pass").catch((e) => e)).type, "RuntimeError");
    assert.equal(await rt.eval("1 + 1"), 2);
  });
});

describe("loss", () => {
  test("a terminated worker", async () => {
    const rt = await Runtime.create();
    const obj = await rt.eval("object()");
    await rt._worker.terminate();
    await assert.rejects(rt.eval("1"), WorkerError);
    await assert.rejects(obj.repr(), WorkerError);
  });

  test("other runtimes survive", async () => {
    const healthy = track(await Runtime.create());
    const doomed = await Runtime.create({ timeout: 100 });
    await assert.rejects(doomed.exec("while True: pass"), Timeout);
    assert.equal(await healthy.eval("6 * 7"), 42);
  });

  test("handles are released", async () => {
    const rt = track(await Runtime.create());
    const count = () => rt.eval("len(__import__('gc').get_objects())");
    for (let i = 0; i < 200; i++) await rt.eval("object()");
    globalThis.gc?.();
    await new Promise((r) => setTimeout(r, 50));
    await rt.eval("1");
    const live = await count();
    for (let i = 0; i < 500; i++) (await rt.eval("object()")).release();
    await rt.eval("1");
    assert.ok(await count() - live < 50);
  });
});
