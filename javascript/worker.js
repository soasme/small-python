// The Worker of a Runtime: serves the engine (engine.js) over its port.

import { serve } from "./engine.js";

const node = typeof process === "object" && process.versions?.node;
const port = node ? (await import("node:worker_threads")).parentPort : self;

serve((message, transfer) => port.postMessage(message, transfer),
  node ? (fn) => port.on("message", fn) : (fn) => port.addEventListener("message", (event) => fn(event.data)));
