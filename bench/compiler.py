"""Alternate compiler benchmark executables over rounds; report CPU us per operation.

Build each executable from bench/compiler.c against its engine's libspy.a.
Compilation includes releasing the compiled code. Execution reuses compiled
module code and its namespace; one warmup execution is outside the timer.
Every workload checks its result. Child output is discarded at the host
callback; context creation, source I/O and shutdown are outside the timer.
"""
import argparse
import json
import math
from pathlib import Path
import statistics
import subprocess
import tempfile


def workloads():
    definitions = "\n".join(f"def f{i}(x):\n    return x + {i}" for i in range(64))
    yield "definitions", definitions + "\nassert f63(1) == 64\n"
    body = "\n".join(f"    x += {i}" for i in range(128))
    yield "function_body", "def run(x):\n" + body + "\n    return x\nassert run(1) == 8129\n"
    namespace = "\n".join(f"    a{i} = b{i} = {i}" for i in range(64))
    yield "namespace", "class Values:\n" + namespace + "\nassert Values.a63 == Values.b63 == 63\n"
    yield "names", """value = 7
def zero():
    return 0
def read():
    return zero() + value
def run():
    total = 0
    for i in range(100):
        total += read()
    return total
assert run() == 700
"""
    yield "constants", """def sink(first, x):
    return x
def zero():
    return 0
def run():
    total = 0
    for i in range(100):
        total += sink(zero(), 12345678901234567890)
        total += sink(zero(), 0xabcdef0123456789)
    return total
assert run() == 2472549264011168623500
"""
    yield "closures", """def outer(x):
    def inner(y):
        return x + y
    return inner
assert sum(outer(i)(3) for i in range(100)) == 5250
"""
    yield "branches", """def run():
    total = 0
    for i in range(100):
        if i % 3:
            total += i
        else:
            total -= i
    return total
assert run() == 1584
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("engines", nargs="+", help="NAME=benchmark-executable")
    parser.add_argument("--rounds", type=int, default=7)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.rounds < 3 or args.iterations < 1:
        parser.error("use at least three rounds and one iteration")
    engines = []
    for engine in args.engines:
        name, sep, path = engine.partition("=")
        if not sep or not name or not path or any(name == n for n, _ in engines):
            parser.error("engines must have distinct names and NAME=executable form")
        engines.append((name, str(Path(path).resolve())))
    report = {"rounds": args.rounds, "iterations": args.iterations, "unit": "CPU seconds/operation", "samples": {}}
    print("| Workload | Phase | " + " | ".join(n for n, _ in engines) + " |", flush=True)
    print("|---|---|" + "---:|" * len(engines), flush=True)
    with tempfile.TemporaryDirectory(prefix="spy-compiler-") as directory:
        for workload, source in workloads():
            path = Path(directory) / (workload + ".py")
            path.write_text(source)
            for phase in ("compile", "execute"):
                samples = {name: [] for name, _ in engines}
                for round_index in range(args.rounds):
                    order = engines if round_index % 2 == 0 else engines[::-1]
                    for name, executable in order:
                        result = subprocess.run([executable, phase, str(path), str(args.iterations)],
                                                capture_output=True, text=True, timeout=120)
                        if result.returncode:
                            raise SystemExit(f"{name}/{workload}/{phase} failed: {result.stderr}")
                        elapsed = float(result.stdout)
                        if not math.isfinite(elapsed) or elapsed <= 0:
                            raise SystemExit(f"{name}/{workload}/{phase}: invalid timing {result.stdout!r}")
                        samples[name].append(elapsed)
                report["samples"][workload + "/" + phase] = samples
                cells = [f"{statistics.median(samples[name]) * 1e6:.2f}" for name, _ in engines]
                print(f"| {workload} | {phase} | " + " | ".join(cells) + " |", flush=True)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
