"""Measure what native modules cost a user: building one, importing one, and
the probe for NAME.so that every import of a source module now makes.

Usage: python3 bench/native.py [BASELINE_SPY] [ROUNDS]

Three programs run as fresh processes, alternated over ROUNDS rounds
(default 10) of 30 runs each; each reports the median of the round medians:
importing examples/fib.so, importing the same function written in Python,
and importing 200 source modules. Given BASELINE_SPY (a spy built without
native modules), the last also runs on it, so the difference is the probe.
Every run's output must match.
"""

import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES = 200
FIB = '''def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
'''


def median_ms(command, cwd, runs, expected):
    times = []
    for _ in range(runs):
        begin = time.perf_counter()
        result = subprocess.run(command, cwd=cwd, capture_output=True)
        times.append(time.perf_counter() - begin)
        if result.returncode or result.stdout != expected:
            sys.exit(f"native bench: {command} failed or printed something else: {result}")
    return statistics.median(times) * 1000


def main():
    baseline = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else None
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    spy = os.path.join(ROOT, "spy")
    with tempfile.TemporaryDirectory() as temp:
        native, source, many = (os.path.join(temp, name) for name in ("native", "source", "many"))
        for directory in (native, source, many):
            os.mkdir(directory)
        library = os.path.join(native, "fib.so")
        command = ["cc", "-O2", "-shared", "-fPIC", "-DSPY_SHARED_MODULE", "-I", ROOT,
                   os.path.join(ROOT, "examples", "fib.c"), "-o", library]
        builds = []
        for _ in range(7):
            begin = time.perf_counter()
            subprocess.run(command, check=True)
            builds.append(time.perf_counter() - begin)
        with open(os.path.join(source, "fib.py"), "w") as f:
            f.write(FIB)
        for i in range(MODULES):
            with open(os.path.join(many, f"m{i}.py"), "w") as f:
                f.write(f"x = {i}\n")
        program = "import fib\nprint(fib.fib(90))\n"
        for directory in (native, source):
            with open(os.path.join(directory, "main.py"), "w") as f:
                f.write(program)
        with open(os.path.join(many, "main.py"), "w") as f:
            f.write("".join(f"import m{i}\n" for i in range(MODULES)) + f"print(m{MODULES - 1}.x)\n")
        runs = [("import fib.so", [spy, "main.py"], native), ("import fib.py", [spy, "main.py"], source),
                (f"import {MODULES} .py", [spy, "main.py"], many)]
        if baseline:
            runs.append((f"import {MODULES} .py, baseline", [baseline, "main.py"], many))
        expected = {name: subprocess.run(command, cwd=cwd, capture_output=True, check=True).stdout
                    for name, command, cwd in runs}
        if baseline and expected[runs[2][0]] != expected[runs[3][0]]:
            sys.exit("native bench: the baseline printed something else")
        times = {name: [] for name, _, _ in runs}
        for _ in range(rounds):
            for name, command, cwd in runs:
                times[name].append(median_ms(command, cwd, 30, expected[name]))
        print(f"build fib.so (cc -O2)        {statistics.median(builds) * 1000:.1f} ms")
        print(f"size fib.so                  {os.path.getsize(library)} bytes")
        for name, values in times.items():
            print(f"{name:<29}{statistics.median(values):.2f} ms  (rounds {min(values):.2f}-{max(values):.2f})")
        if baseline:
            probe = statistics.median(times[runs[2][0]]) - statistics.median(times[runs[3][0]])
            print(f"probe per source import      {probe * 1000 / MODULES:.2f} us")


if __name__ == "__main__":
    main()
