// The engine side of a Runtime: instantiates spy-worker.wasm and runs its
// main loop, which waits in read() for the next bytes from the Runtime. The
// module reaches nothing but these imports (javascript.md section 2). It runs
// in a Worker (worker.js) or, with JSPI, on the Runtime's own thread.

class Exit extends Error {
  constructor(code) { super(`exit ${code}`); this.code = code; }
}

/**
 * Serve one Runtime: `post(message, transfer)` sends to it, and `listen(fn)`
 * delivers each message from it. The first message starts the engine; with an
 * inbox the engine blocks on it, without one it suspends through JSPI until
 * the next message arrives.
 */
export function serve(post, listen) {
  let start = null;
  const chunks = [];
  let wake = null;
  listen((data) => {
    if (!start) {
      start = data;
      run(data, post, chunks, (resolve) => { wake = resolve; });
    } else {
      chunks.push(data);
      if (wake) { const resolve = wake; wake = null; resolve(); }
    }
  });
}

async function run({ module, pages, maximum, inbox }, post, chunks, waitChunk) {
  const memory = new WebAssembly.Memory({ initial: pages, maximum });
  const bytes = () => new Uint8Array(memory.buffer);
  const view = () => new DataView(memory.buffer);

  // Runtime to engine. With an inbox: wait for a chunk, copy what fits, hand
  // the inbox back once the chunk is used up. Without: suspend until a
  // message is posted, then copy what fits.
  let read;
  if (inbox) {
    const control = new Int32Array(inbox, 0, 2), data = new Uint8Array(inbox, 8);
    let position = 0;
    read = (pointer, capacity) => {
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
    };
  } else {
    read = new WebAssembly.Suspending(async (pointer, capacity) => {
      while (!chunks.length) await new Promise(waitChunk);
      const chunk = chunks[0], n = Math.min(capacity, chunk.length);
      bytes().set(chunk.subarray(0, n), pointer);
      if (n === chunk.length) chunks.shift();
      else chunks[0] = chunk.subarray(n);
      return n;
    });
  }
  // Engine to Runtime: post a copy.
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

  try {
    const instance = new WebAssembly.Instance(module, imports);
    const main = inbox ? instance.exports._start : WebAssembly.promising(instance.exports._start);
    await main();
    post({ exit: 0 });
  } catch (e) {
    post(e instanceof Exit ? { exit: e.code } : { trap: String(e) });
  }
}
