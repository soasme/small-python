// A hostile worker for tests: answers INIT, then on the next request sends
// the bytes named by the FAKE_WORKER_CASE environment variable.
import { parentPort } from "node:worker_threads";

const CASES = {
  "unknown kind": [0x7f],
  "unknown tag": [0x40, 0x3f],
  "truncated value": [0x40, 0x69, 1],
  "trailing bytes": [0x40, 0x4e, 0x4e],
  "count over message": [0x40, 0x6c, 0x40, 0x42, 0x0f, 0x00],
  "invalid utf-8": [0x40, 0x73, 2, 0, 0, 0, 0xc0, 0x80],
  "non-canonical int": [0x40, 0x49, 3, 0, 0, 0, ...Buffer.from("0x5")],
  "deep nesting": [0x40, ...Array(300).fill([0x6c, 1, 0, 0, 0]).flat(), 0x4e],
  "unknown function": [0x21, 0x69, 99, 0, 0, 0, 0, 0, 0, 0, 0x74, 0, 0, 0, 0, 0x64, 0, 0, 0, 0],
  "parent-only tag": [0x40, 0x70, 1, 0, 0, 0, 0, 0, 0, 0, 0x73, 0, 0, 0, 0],
  "malformed error": [0x41, 0x4e],
};
const which = process.env.FAKE_WORKER_CASE;
if (!(which in CASES) && !["length over limit", "zero length", "exit", "silent"].includes(which))
  throw new Error(`unknown case ${which}`);

parentPort.once("message", ({ inbox }) => {
  const control = new Int32Array(inbox, 0, 2), data = new Uint8Array(inbox, 8);
  const receive = () => {
    while (Atomics.load(control, 0) === 0) Atomics.wait(control, 0, 0);
    Atomics.store(control, 0, 0);
    Atomics.notify(control, 0);
  };
  const send = (payload) => {
    const frame = new Uint8Array(4 + payload.length);
    new DataView(frame.buffer).setUint32(0, payload.length, true);
    frame.set(payload, 4);
    parentPort.postMessage(frame);
  };
  receive();
  send([0x40, 0x73, 5, 0, 0, 0, ...Buffer.from("0.1.0")]);
  receive();
  if (which === "length over limit") parentPort.postMessage(new Uint8Array([0xff, 0xff, 0xff, 0xff]));
  else if (which === "zero length") parentPort.postMessage(new Uint8Array([0, 0, 0, 0]));
  else if (which === "exit") process.exit(5);
  else if (which !== "silent") send(CASES[which]);
  // Stay alive, as a hostile worker would; the runtime must end it.
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0);
});
