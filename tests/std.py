"""The sys and gc modules against CPython 3.15 (docs/std.md).

tests/std_probe.py prints what the specification states about each name; it
must print the same under the spy command and under the Python 3.15 running
this script, which should be the pinned oracle.
"""

import difflib
from pathlib import Path
import subprocess
import sys

PROBE = Path(__file__).resolve().parent / "std_probe.py"


def run(command):
    result = subprocess.run([*command, str(PROBE)], capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise SystemExit(f"{command[0]} failed:\n{result.stdout}{result.stderr}")
    return result.stdout


def main():
    if sys.version_info[:2] != (3, 15):
        raise SystemExit("Use the pinned Python 3.15 development oracle")
    expected, actual = run([sys.executable, "-I"]), run([str(Path(sys.argv[1]).resolve())])
    if expected != actual:
        diff = difflib.unified_diff(expected.splitlines(), actual.splitlines(), "CPython", "spy", lineterm="")
        raise SystemExit("sys and gc differ from CPython:\n" + "\n".join(diff))
    print(f"Standard modules: {len(expected.splitlines())} probes of sys and gc match CPython")


if __name__ == "__main__":
    main()
