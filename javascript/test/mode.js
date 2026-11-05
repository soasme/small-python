// The transport the suite runs on, from SMALL_PYTHON_TEST_MODE (Makefile's
// test-javascript runs all three): "worker", a Worker with JSPI where this
// Node has it; "inbox", a Worker on the SharedArrayBuffer inbox; "thread", no
// Worker, which needs JSPI. Tests that need a Worker pass worker: true.
import { Runtime } from "../index.js";

const mode = process.env.SMALL_PYTHON_TEST_MODE ?? "worker";
if (mode === "inbox") Runtime._jspi = false;
else if (mode === "thread") {
  if (!Runtime._jspi) throw new Error(`thread mode needs WebAssembly JSPI, which Node ${process.version} lacks`);
  const create = Runtime.create;
  Runtime.create = (options = {}) => create.call(Runtime, { worker: false, ...options });
} else if (mode !== "worker") throw new Error(`unknown SMALL_PYTHON_TEST_MODE ${mode}`);
