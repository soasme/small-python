// What the JavaScript package's transports cost a user (docs/benchmark.md):
// creating a runtime, a host-call round trip, an eval round trip, and fib(25)
// in the engine. The three transports alternate over eight rounds, and the
// median of each measure is reported. Run: node bench/javascript.mjs
import { Runtime } from "../javascript/index.js";

const transports = { inbox: { jspi: false, worker: true }, jspi: { jspi: true, worker: true }, thread: { jspi: true, worker: false } };
const jspi = Runtime._jspi;
if (!jspi) throw new Error(`this Node (${process.version}) has no WebAssembly JSPI`);
const now = () => performance.now();

async function measure({ jspi, worker }) {
  Runtime._jspi = jspi;
  let start = now();
  const rt = await Runtime.create({ worker });
  const create = now() - start;
  await rt.define("f", (x) => x + 1);
  start = now();
  await rt.exec("s = 0\nfor i in range(5000):\n    s = f(s)");
  const host = (now() - start) / 5;
  start = now();
  for (let i = 0; i < 2000; i++) await rt.eval("1");
  const evals = (now() - start) / 2;
  start = now();
  if (await rt.eval("(lambda f: f(f, 25))(lambda f, n: n if n < 2 else f(f, n - 1) + f(f, n - 2))") !== 75025)
    throw new Error("fib(25) is wrong");
  const fib = now() - start;
  rt.close();
  return { "create (ms)": create, "host call (µs)": host, "eval (µs)": evals, "fib(25) (ms)": fib };
}

const runs = Object.fromEntries(Object.keys(transports).map((name) => [name, []]));
const names = Object.keys(transports);
for (let round = 0; round < 8; round++)
  for (const name of round % 2 ? [...names].reverse() : names) runs[name].push(await measure(transports[name]));
Runtime._jspi = jspi;

const median = (xs) => [...xs].sort((a, b) => a - b)[xs.length >> 1];
const measures = Object.keys(runs.inbox[0]);
console.log(`| Measure | ${names.join(" | ")} |`);
console.log(`| --- |${names.map(() => " ---: |").join("")}`);
for (const m of measures)
  console.log(`| ${m} | ${names.map((n) => median(runs[n].map((r) => r[m])).toFixed(m.includes("µs") ? 1 : 2)).join(" | ")} |`);
