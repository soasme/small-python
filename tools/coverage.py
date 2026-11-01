#!/usr/bin/env python3
"""Require every line of the engine to run under the tests.

    tools/coverage.py LCOV FILE...

LCOV is llvm-cov's lcov export of make coverage. Each FILE must have every
instrumented line executed; the lines that are not are listed under their
functions, and the exit status is nonzero.
"""

import bisect
import sys
from pathlib import Path


def load(lcov):
    """{file name: (sorted [(line, function)], {line: count})}"""
    files, current = {}, None
    for line in Path(lcov).read_text().splitlines():
        tag, _, value = line.partition(":")
        if tag == "SF":
            current = files.setdefault(Path(value).name, ([], {}))
        elif tag == "FN" and current:
            number, name = value.split(",", 1)
            current[0].append((int(number), name.rsplit(":", 1)[-1]))
        elif tag == "DA" and current:
            number, count = value.split(",")[:2]
            current[1][int(number)] = current[1].get(int(number), 0) + int(count)
    for functions, _ in files.values():
        functions.sort()
    return files


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__.strip())
    files, failed = load(sys.argv[1]), 0
    for name in sys.argv[2:]:
        if name not in files:
            print(f"{name}: no coverage data")
            failed += 1
            continue
        functions, counts = files[name]
        missed = sorted(line for line, count in counts.items() if not count)
        print(f"{name}: {len(counts) - len(missed)}/{len(counts)} lines")
        starts = [start for start, _ in functions]
        for line in missed:
            at = bisect.bisect_right(starts, line) - 1
            print(f"  {name}:{line} {functions[at][1] if at >= 0 else ''}")
        failed += bool(missed)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
