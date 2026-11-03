"""Measure what spyc costs a user: build time, and the start-up and size of
the program it builds against the spy command running the same source.

Usage: python3 bench/spyc.py [ROUNDS]

The program is bench/programs/startup.py. Builds are timed as executables
(the default) and as C (-e). Start-up alternates the two commands over
ROUNDS rounds (default 10) of 30 runs each and reports the median of the
round medians, so a difference is not an artifact of one stretch of time.
Every run's output must match spy's.
"""

import os
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRAM = os.path.join(ROOT, "bench", "programs", "startup.py")


def median_ms(command, runs, expected=None):
    times = []
    for _ in range(runs):
        begin = time.perf_counter()
        result = subprocess.run(command, capture_output=True)
        times.append(time.perf_counter() - begin)
        if result.returncode or (expected is not None and result.stdout != expected):
            sys.exit(f"spyc bench: {command[0]} failed or printed something else")
    return statistics.median(times) * 1000


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    spy, spyc = os.path.join(ROOT, "spy"), os.path.join(ROOT, "spyc")
    expected = subprocess.run([spy, PROGRAM], capture_output=True, check=True).stdout
    with tempfile.TemporaryDirectory() as temp:
        program = os.path.join(temp, "startup")
        build = median_ms([spyc, "-o", program, PROGRAM], 7)
        build_c = median_ms([spyc, "-e", "-o", program + ".c", PROGRAM], 7)
        a, b = [], []
        for _ in range(rounds):
            a.append(median_ms([spy, PROGRAM], 30, expected))
            b.append(median_ms([program], 30, expected))
        print(f"spyc build, executable    {build:.1f} ms")
        print(f"spyc build, C (-e)        {build_c:.1f} ms")
        print(f"start-up, spy startup.py  {statistics.median(a):.2f} ms  (rounds {min(a):.2f}-{max(a):.2f})")
        print(f"start-up, spyc-built      {statistics.median(b):.2f} ms  (rounds {min(b):.2f}-{max(b):.2f})")
        print(f"size, spyc-built          {os.path.getsize(program)} bytes; spy {os.path.getsize(spy)} bytes")


if __name__ == "__main__":
    main()
