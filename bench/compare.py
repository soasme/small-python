"""Time the programs in bench/programs on several Python engines.

Usage: python3 bench/compare.py NAME=COMMAND [NAME=COMMAND ...]

The first engine is the reference: another engine's run counts only when its
output matches the reference output exactly. Each cell reports the median wall
time of the runs and the largest peak resident set size, measured per process
with wait4. Mismatched output or a non-zero exit is reported, never timed.
"""

import os
import shlex
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAMS = os.path.join(HERE, "programs")
RUNS = {"startup": 30}
DEFAULT_RUNS = 5


def run(command, path):
    begin = time.perf_counter()
    child = subprocess.Popen(command + [path], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    output = child.stdout.read()
    _, status, usage = os.wait4(child.pid, 0)
    elapsed = time.perf_counter() - begin
    child.stdout.close()
    # macOS reports ru_maxrss in bytes, Linux in kilobytes.
    rss = usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024
    return os.waitstatus_to_exitcode(status), output, elapsed, rss


def measure(command, path, runs, expected):
    times, peak = [], 0
    for _ in range(runs):
        code, output, elapsed, rss = run(command, path)
        if code != 0:
            return "error"
        if expected is not None and output != expected:
            return "wrong"
        times.append(elapsed)
        peak = max(peak, rss)
    median = statistics.median(times)
    shown = f"{median * 1000:.1f} ms" if median < 1 else f"{median:.2f} s"
    return f"{shown}, {peak / 2**20:.1f} MiB"


def main(argv):
    engines = [arg.split("=", 1) for arg in argv]
    if not engines or any(len(e) != 2 for e in engines):
        sys.exit(__doc__)
    names = sorted(f[:-3] for f in os.listdir(PROGRAMS) if f.endswith(".py"))
    print("| Program | " + " | ".join(name for name, _ in engines) + " |")
    print("|---" * (len(engines) + 1) + "|")
    for program in names:
        path = os.path.join(PROGRAMS, program + ".py")
        runs = RUNS.get(program, DEFAULT_RUNS)
        reference = shlex.split(engines[0][1])
        code, expected, _, _ = run(reference, path)
        if code != 0:
            sys.exit(f"{program}: the reference engine failed")
        cells = [measure(shlex.split(command), path, runs, expected)
                 for _, command in engines]
        print(f"| {program} | " + " | ".join(cells) + " |", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
