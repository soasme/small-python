"""Compare every Unicode code point with the pinned Python 3.15 oracle."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unicodedata


def main():
    if sys.version_info[:3] != (3, 15, 0) or unicodedata.unidata_version != "17.0.0":
        raise SystemExit("Run with the pinned Python 3.15.0 oracle")
    engine = str(Path(sys.argv[1]).resolve())
    source = """
for code in range(0x110000):
    value = chr(code)
    print(repr(value), ascii(value), value.isprintable(), ord(value), value.isidentifier(), ('A' + value).isidentifier())
    print(ascii(value.lower()), ascii(value.upper()), ascii(value.title()), ascii(value.casefold()), ascii(value.swapcase()),
          value.isalpha(), value.isdecimal(), value.isdigit(), value.isnumeric(), value.isspace(), value.isalnum(),
          value.isupper(), value.islower(), value.istitle(), ascii(('A' + value + '\u03a3').lower()), ascii(('A\u03a3' + value).lower()))
"""
    actual = subprocess.run([engine, "-c", source], capture_output=True, timeout=600)
    if actual.returncode or actual.stderr:
        raise AssertionError(actual.stderr.decode("utf-8", "replace"))
    lines = actual.stdout.split(b"\n")
    assert lines.pop() == b""
    assert len(lines) == 2 * 0x110000, len(lines)
    for code in range(0x110000):
        value = chr(code)
        expected = f"{value!r} {ascii(value)} {value.isprintable()} {code} {value.isidentifier()} {('A' + value).isidentifier()}".encode()
        if lines[2 * code] != expected:
            raise AssertionError(f"U+{code:04X}: {lines[2 * code]!r} != {expected!r}")
        expected = " ".join(map(str, (ascii(value.lower()), ascii(value.upper()), ascii(value.title()), ascii(value.casefold()),
            ascii(value.swapcase()), value.isalpha(), value.isdecimal(), value.isdigit(), value.isnumeric(), value.isspace(),
            value.isalnum(), value.isupper(), value.islower(), value.istitle(), ascii(('A' + value + '\u03a3').lower()),
            ascii(('A\u03a3' + value).lower())))).encode()
        if lines[2 * code + 1] != expected:
            raise AssertionError(f"U+{code:04X}: {lines[2 * code + 1]!r} != {expected!r}")
    check_names(engine)
    print("Unicode 17.0.0: repr, ascii, isprintable, chr/ord, identifier start/continue, case mappings, final sigma, "
          "and character classes passed for all 1,114,112 code points; "
          "every character name and alias resolves through \\N{...}")


def check_names(engine):
    names = [(code, unicodedata.name(chr(code))) for code in range(0x110000) if unicodedata.name(chr(code), None)]
    for line in (Path(__file__).resolve().parent.parent / "tools" / "NameAliases.txt").read_text().splitlines():
        if line and not line.startswith("#"):
            code, alias, _ = line.split(";")
            names.append((int(code, 16), alias))
    source = "for name in %r:\n    print(ord(eval('\"\\\\N{' + name + '}\"')))\n" % [name.lower() for _, name in names]
    with tempfile.NamedTemporaryFile("w", suffix=".py") as script:
        script.write(source)
        script.flush()
        actual = subprocess.run([engine, script.name], capture_output=True, timeout=3600)
    if actual.returncode or actual.stderr:
        raise AssertionError(actual.stderr.decode("utf-8", "replace"))
    for (code, name), line in zip(names, actual.stdout.split(b"\n"), strict=False):
        if int(line) != code:
            raise AssertionError(f"\\N{{{name}}}: {int(line):04X} != {code:04X}")
    if actual.stdout.count(b"\n") != len(names):
        raise AssertionError("missing name lookups")


if __name__ == "__main__":
    main()
