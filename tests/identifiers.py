"""Check source identifiers and NFKC normalization with pinned Unicode 17."""

from pathlib import Path
import random
import subprocess
import sys
import unicodedata


def main():
    if sys.version_info[:3] != (3, 15, 0) or unicodedata.unidata_version != '17.0.0':
        raise SystemExit('Run with the pinned Python 3.15.0 oracle')
    engine = str(Path(sys.argv[1]).resolve())
    names = []
    for code in range(0x110000):
        char = chr(code)
        if char.isidentifier():
            names.append(char)
        if ('v' + char).isidentifier():
            names.append('v' + char)
    rng = random.Random(315)
    marks = [chr(code) for code in range(0x110000)
             if unicodedata.combining(chr(code)) and ('v' + chr(code)).isidentifier()]
    for _ in range(2000):
        names.append(rng.choice(['A', 'v', 'ά', 'Å', 'Å', '각', '가', 'क']) + ''.join(rng.choices(marks, k=4)))
    names.extend(['𝔘𝔫𝔦𝔠𝔬𝔡𝔢', 'µ', 'μ', 'ﬀ', 'x\U000e0100', 'ｉｆ', 'ｄｅｆ', 'K', 'A\u030a\u0301'])
    for start in range(0, len(names), 1000):
        batch = names[start:start + 1000]
        source = ''.join(f'{name} = {index}\nprint(globals()[{unicodedata.normalize("NFKC", name)!r}])\n'
                         for index, name in enumerate(batch))
        expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True, timeout=30)
        actual = subprocess.run([engine, '-c', source], capture_output=True, timeout=30)
        if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
            raise AssertionError(f'batch at {start}: oracle={expected.stderr!r}, spy={actual.stderr!r}; '
                                 f'oracle output={expected.stdout[-1000:]!r}, spy output={actual.stdout[-1000:]!r}')
    errors = ['€', '😀', '\u0301', '\u200d', '\ufeff', '\u037a', 'x€', 'x😀']
    for name in errors:
        source = f'compile({(name + " = 1")!r}, "test", "exec")'
        expected = subprocess.run([sys.executable, '-I', '-c', source], capture_output=True)
        actual = subprocess.run([engine, '-c', source], capture_output=True)
        if not expected.returncode or not actual.returncode or b'SyntaxError' not in actual.stderr:
            raise AssertionError((name, expected.stderr, actual.stderr))
    print(f'Identifiers: {len(names)} source/NFKC checks and {len(errors)} invalid identifiers passed')


if __name__ == '__main__':
    main()
