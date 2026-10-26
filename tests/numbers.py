"""Deterministic numeric differential checks; upstream suites remain separate."""

from pathlib import Path
import random
import subprocess
import sys
import tempfile


def main():
    engine = str(Path(sys.argv[1]).resolve())
    rng = random.Random(315)
    expressions = []
    for _ in range(700):
        a = rng.getrandbits(rng.randrange(1, 2049)) * rng.choice((-1, 1))
        b = (rng.getrandbits(rng.randrange(1, 2049)) or 1) * rng.choice((-1, 1))
        op = rng.choice(("+", "-", "*", "//", "%", "&", "|", "^", "/", "<", "=="))
        expressions.append(f"({a}) {op} ({b})")
    for _ in range(100):
        a = rng.getrandbits(rng.randrange(1, 300)) * rng.choice((-1, 1))
        b = rng.randrange(0, 300)
        op = rng.choice(("<<", ">>"))
        expressions.append(f"({a}) {op} {b}")
    for _ in range(100):
        a = rng.getrandbits(64) * rng.choice((-1, 1))
        b = rng.randrange(0, 30)
        expressions.append(f"({a}) ** {b}")
    for _ in range(100):
        a = rng.getrandbits(rng.randrange(1, 1100)) * rng.choice((-1, 1))
        expressions.append(f"float({a})")
    for _ in range(150):
        a = rng.getrandbits(200) * rng.choice((-1, 1))
        b = rng.getrandbits(64) * rng.choice((-1, 1))
        modulus = rng.getrandbits(100) * rng.choice((-1, 1))
        expressions.append(f"pow({a}, {b}, {modulus})")
    for _ in range(50):
        a = rng.getrandbits(200) * rng.choice((-1, 1))
        b = rng.getrandbits(100) * rng.choice((-1, 1))
        expressions.append(f"divmod({a}, {b})")
        expressions.append(f"({a}).bit_length(), ({a}).bit_count(), bin({a}), oct({a}), hex({a})")
    expressions.extend([
        "int(1e300)", "int(-1e300)", "float(2**1023 - 2**969)",
        "float(2**1024 - 2**970)", "float(2**1024 - 2**970 - 1)",
        "2**100 / 2**2000", "2**2000 / 2**2000", "-2**1000 >> 3000",
        "(2**100 + 1) > float(2**100)", "(2**100 - 1) < float(2**100)",
        "int(' -0x_1234567890abcdef1234567890abcdef ', 0)",
        "int('1_234_567_890_123_456_789_012_345_678_901_234_567_890')",
        "format(2**256, '+#080x')", "format(-2**256, '0400b')",
        "'%d' % (2**100)", "repr({2**100: 'a', float(2**100): 'b'})",
        "-(-9223372036854775808)", "abs(-9223372036854775808)",
        "pow(base=3, exp=-123, mod=2**100)",
        "int('deadbeef' * 20, base=16)",
        "list(enumerate('abc', 2**100))",
        "list(enumerate('abc', -2**100))",
        "[1, 2, 3][-2**100:2**100]",
        "[1, 2, 3][::2**100]",
        "[1, 2, 3][::-2**100]",
        "[1, 2, 3][2**100]",
        "[1, 2, 3][-2**100]",
        "pow(2, -1, 4)", "pow(0, -1, 1)", "pow(0, -1, -1)",
        "pow(2, 1, 0)", "pow(2, 2**100, 7)",
        "int('9' * 4300).bit_length()", "int('9' * 4301)",
        "int('0' * 4301)", "str(10**4300)", "len(hex(1 << 50000))",
    ])
    for exponent in (1, 53, 1022, 1074, 1075, 1076):
        for numerator in (-7, -3, -1, 0, 1, 3, 7):
            expressions.append(f"{numerator} / 2**{exponent}")
    source = "".join(
        f"try:\n    print({expression})\nexcept Exception as error:\n    print(type(error).__name__)\n"
        for expression in expressions
    )
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp, "numbers.py")
        path.write_text(source)
        expected = subprocess.run([sys.executable, "-I", str(path)], capture_output=True, text=True, timeout=120)
        actual = subprocess.run([engine, str(path)], capture_output=True, text=True, timeout=120)
    if expected.returncode or actual.returncode or expected.stderr or actual.stderr:
        raise AssertionError(f"oracle: {expected.returncode} {expected.stderr}\nengine: {actual.returncode} {actual.stderr}")
    want, got = expected.stdout.splitlines(), actual.stdout.splitlines()
    if len(want) != len(expressions) or len(got) != len(expressions):
        raise AssertionError(f"expected {len(expressions)} results; oracle {len(want)}, engine {len(got)}")
    for expression, left, right in zip(expressions, want, got):
        if left != right:
            raise AssertionError(f"{expression}\nCPython: {left}\nspy: {right}")
    print(f"Numbers: {len(expressions)} arbitrary-integer, conversion, and rounding expressions passed")


if __name__ == "__main__":
    main()
