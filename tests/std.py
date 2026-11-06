"""The standard modules against CPython 3.15 (docs/standards/std.md).

tests/std_probe.py prints what the specification states about each name of
sys, and tests/thread_probe.py what _thread does; each must print the same
under the spy command and under the Python 3.15 running this script, which
should be the pinned oracle.
"""

import difflib
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROBES = {"sys": HERE / "std_probe.py", "_thread": HERE / "thread_probe.py"}


def run(command, probe):
    result = subprocess.run([*command, str(probe)], capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise SystemExit(f"{command[0]} failed:\n{result.stdout}{result.stderr}")
    return result.stdout


def main():
    if sys.version_info[:2] != (3, 15):
        raise SystemExit("Use the pinned Python 3.15 development oracle")
    counts = []
    for name, probe in PROBES.items():
        expected, actual = run([sys.executable, "-I"], probe), run([str(Path(sys.argv[1]).resolve())], probe)
        if expected != actual:
            diff = difflib.unified_diff(expected.splitlines(), actual.splitlines(), "CPython", "spy", lineterm="")
            raise SystemExit(f"{name} differs from CPython:\n" + "\n".join(diff))
        counts.append(f"{len(expected.splitlines())} of {name}")
    print(f"Standard modules: probes match CPython ({', '.join(counts)})")


if __name__ == "__main__":
    main()
