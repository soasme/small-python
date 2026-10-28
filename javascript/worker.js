// The Worker side of a Runtime: instantiates spy-worker.wasm and runs its
// main loop, which blocks in read() until the main thread fills the inbox.
// The module reaches nothing but these imports (javascript.md section 2).

const node = typeof process === "object" && process.versions?.node;
const port = node ? (await import("node:worker_threads")).parentPort : self;
const post = (message, transfer) => port.postMessage(message, transfer);

class Exit extends Error {
  constructor(code) { super(`exit ${code}`); this.code = code; }
}

function start({ module, pages, maximum, inbox }) {
  const memory = new WebAssembly.Memory({ initial: pages, maximum });
  const control = new Int32Array(inbox, 0, 2), data = new Uint8Array(inbox, 8);
  let position = 0;
  const bytes = () => new Uint8Array(memory.buffer);
  const view = () => new DataView(memory.buffer);

  // Main to worker: wait for a chunk, copy what fits, hand the inbox back
  // once the chunk is used up.
  function read(pointer, capacity) {
    while (Atomics.load(control, 0) === 0) Atomics.wait(control, 0, 0);
    const n = Math.min(capacity, control[1] - position);
    bytes().set(data.subarray(position, position + n), pointer);
    position += n;
    if (position === control[1]) {
      position = 0;
      Atomics.store(control, 0, 0);
      Atomics.notify(control, 0);
    }
    return n;
  }
  // Worker to main: post a copy.
  function write(pointer, length) {
    const chunk = bytes().slice(pointer, pointer + length);
    post(chunk, [chunk.buffer]);
  }

  // WASI: diagnostics on stderr, clocks, exit; everything else is refused.
  const ENOSYS = 52, EBADF = 8, ESPIPE = 70;
  const decoder = new TextDecoder();
  const wasi = {
    args_sizes_get(count, size) { view().setUint32(count, 0, true); view().setUint32(size, 0, true); return 0; },
    args_get() { return 0; },
    clock_time_get(id, precision, out) {
      const ns = id === 0 ? BigInt(Date.now()) * 1000000n : BigInt(Math.round(performance.now() * 1e6));
      view().setBigUint64(out, ns, true);
      return 0;
    },
    fd_write(fd, iovs, count, written) {
      if (fd !== 1 && fd !== 2) return EBADF;
      let total = 0, text = "";
      for (let i = 0; i < count; i++) {
        const at = view().getUint32(iovs + 8 * i, true), n = view().getUint32(iovs + 8 * i + 4, true);
        text += decoder.decode(bytes().subarray(at, at + n), { stream: true });
        total += n;
      }
      if (text) console.error(text.replace(/\n$/, ""));
      view().setUint32(written, total, true);
      return 0;
    },
    fd_fdstat_get(fd, out) {
      if (fd > 2) return EBADF;
      bytes().fill(0, out, out + 24);
      view().setUint8(out, 2);
      return 0;
    },
    fd_seek() { return ESPIPE; },
    fd_close(fd) { return fd > 2 ? EBADF : 0; },
    proc_exit(code) { throw new Exit(code); },
  };
  const imports = { env: { memory }, spy: { read, write }, wasi_snapshot_preview1: {} };
  for (const { module: name, name: field, kind } of WebAssembly.Module.imports(module))
    if (name === "wasi_snapshot_preview1" && kind === "function")
      imports.wasi_snapshot_preview1[field] = wasi[field] ?? (() => ENOSYS);

  const instance = new WebAssembly.Instance(module, imports);
  try {
    instance.exports._start();
    post({ exit: 0 });
  } catch (e) {
    post(e instanceof Exit ? { exit: e.code } : { trap: String(e) });
  }
}

if (node) port.once("message", start);
else port.addEventListener("message", (event) => start(event.data), { once: true });
