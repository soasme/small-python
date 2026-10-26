"""Range and slice differential checks, supplementing upstream test_range.py."""

from pathlib import Path
import random
import subprocess
import sys


def main():
    engine = str(Path(sys.argv[1]).resolve())
    rng = random.Random(315)
    expressions = []
    for _ in range(150):
        start = rng.choice([rng.randrange(-30, 30), rng.getrandbits(600) * rng.choice([-1, 1])])
        step = rng.choice([-1, 1]) * rng.choice([rng.randrange(1, 15), rng.getrandbits(500) + 1])
        stop = start + step * rng.randrange(-5, 15) + rng.randrange(-2, 3)
        source = f'range({start}, {stop}, {step})'
        expressions.append(f'print({source}, list({source}), list(reversed({source})))')
        for _ in range(3):
            begin = rng.choice([None, rng.randrange(-20, 20), 10**200, -10**200])
            end = rng.choice([None, rng.randrange(-20, 20), 10**200, -10**200])
            stride = rng.choice([None, 1, -1, 2, -3, 10**150, -10**150])
            expressions.append(f'print({source}[slice({begin}, {end}, {stride})])')
    for _ in range(150):
        length = rng.choice([rng.randrange(30), rng.getrandbits(1000)])
        start = rng.choice([None, rng.randrange(-30, 30), rng.getrandbits(1100), -rng.getrandbits(1100)])
        stop = rng.choice([None, rng.randrange(-30, 30), rng.getrandbits(1100), -rng.getrandbits(1100)])
        step = rng.choice([None, 1, -1, rng.getrandbits(400) + 1, -rng.getrandbits(400) - 1])
        expressions.append(f'print(slice({start}, {stop}, {step}).indices({length}))')
    for offset in [-2**63, 0, 2**63 - 1]:
        for step in [-2**63, -3, -1, 1, 3, 2**63 - 1]:
            source = f'range({offset}, {-offset - 1}, {step})'
            expressions.append(f'r = {source}; print(bool(r), r[:3], r[-3:], next(iter(r), None), next(reversed(r), None))')
    for start in range(0, len(expressions), 20):
        source = '\n'.join(expressions[start:start + 20])
        expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, text=True, timeout=20)
        actual = subprocess.run([engine, '-c', source], capture_output=True, text=True, timeout=20)
        if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
            raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')
    print(f'Ranges: {len(expressions)} large-bound, slicing, and reverse-iteration checks passed')


if __name__ == '__main__':
    main()
