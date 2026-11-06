"""Measure what _thread costs a user: importing it, starting and joining a
thread, and an uncontended lock.

Usage: python3 bench/threads.py SPY [PYTHON] [ROUNDS]

Each measure is a program that does N operations against the same program
doing none, both run as fresh processes, alternated over ROUNDS rounds
(default 10) of 15 runs each; a cost is the difference of the medians of
the round medians, divided by N. Given PYTHON (the pinned CPython), the
same programs run on it too. Every run's output must match.
"""

import os
import statistics
import subprocess
import sys
import tempfile
import time

PROGRAMS = {
    # name: (operations, the work, done N times)
    "import _thread": (1, "import _thread\n"),
    "start and join a thread": (2000, "import _thread\nfor _ in range(N):\n    _thread.start_joinable_thread(int).join()\n"),
    "acquire and release a free lock": (200000, "import _thread\nl = _thread.allocate_lock()\nfor _ in range(N):\n    l.acquire()\n    l.release()\n"),
}
BASE = "import _thread\n"


def median_ms(command, runs):
    times = []
    for _ in range(runs):
        begin = time.perf_counter()
        result = subprocess.run(command, capture_output=True)
        times.append(time.perf_counter() - begin)
        if result.returncode or result.stdout != b"done\n":
            sys.exit(f"threads bench: {command} failed: {result}")
    return statistics.median(times) * 1000


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    engines = {"spy": os.path.abspath(sys.argv[1])}
    if len(sys.argv) > 2:
        engines["CPython"] = sys.argv[2]
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    with tempfile.TemporaryDirectory() as tmp:
        files = {}
        for name, (n, work) in [("base", (1, BASE)), ("empty", (1, ""))] + list(PROGRAMS.items()):
            path = os.path.join(tmp, f"{len(files)}.py")
            with open(path, "w") as f:
                f.write(f"N = {n}\n{work}print('done')\n")
            files[name] = path
        medians = {(e, p): [] for e in engines for p in files}
        for _ in range(rounds):
            for program, path in files.items():
                for engine, binary in engines.items():
                    medians[engine, program].append(median_ms([binary, path], 15))
        print(f"| Measure | {' | '.join(engines)} |")
        print(f"| --- | {' | '.join('---:' for _ in engines)} |")
        for program, (n, _) in PROGRAMS.items():
            base = "empty" if program == "import _thread" else "base"
            cells = []
            for engine in engines:
                cost = statistics.median(medians[engine, program]) - statistics.median(medians[engine, base])
                cells.append(f"{cost * 1000 / n:.2f} µs" if n > 1 else f"{cost:.2f} ms")
            print(f"| {program} | {' | '.join(cells)} |")


if __name__ == "__main__":
    main()
