"""open() checks: differential file behavior and the mount boundary.

Each differential program runs under CPython and spy in its own fresh
directory, which the spy command mounts by default. The boundary checks run
only under spy: nothing outside a mount is reachable, including through
'..', absolute paths, and symbolic links.
"""

from pathlib import Path
import errno
import os
import subprocess
import sys
import tempfile

CASES = ['\nwith open("f.txt", "w") as f:\n    print(repr(f), f.encoding, f.errors, f.newlines, f.line_buffering, f.mode, f.name, type(f.buffer).__name__, repr(f.buffer), type(f.buffer.raw).__name__, repr(f.buffer.raw))\n    print(f.write("héllo\\nworld\\r\\nend"), f.tell())\nwith open("f.txt", "rb") as f: print(repr(f), f.read())\nwith open("f.txt") as f:\n    print(repr(f.readline()), f.tell(), repr(f.read(3)), f.newlines, list(f))\nwith open("f.txt", newline="") as f: print(f.readlines())\nwith open("f.txt", "r+b") as f: print(repr(f), f.seek(0, 2), f.write(b"!"))\nwith open("f.txt", "ab") as f: print(repr(f))\nwith open("f.txt", "a") as f: print(repr(f), f.tell())\nfor args in [("missing.txt",), ("f.txt", "rw"), ("f.txt", "x"), (".",), ("f.txt", "rb", 0, "utf-8"), ("f.txt", "q"), (3.5,), ("f.txt", "r", -1, "nope")]:\n    try: open(*args)\n    except Exception as e: print(type(e).__name__, e, getattr(e, "errno", None), getattr(e, "filename", None))\nf = open("f.txt"); f.close()\nfor op in [f.read, f.readline, lambda: f.write("x"), lambda: next(f), f.tell]:\n    try: op()\n    except Exception as e: print(type(e).__name__, e)\nprint(f.closed, repr(f))\nf = open("f.txt")\ntry: f.write("x")\nexcept Exception as e: print(type(e).__name__, e, type(e).__mro__)\nprint(open.__name__, type(open))\nf.close()\nprint(OSError(2, "x", "y").__class__.__name__)\n',
         'text = ("aé€😀\\r\\n" * 3000) + "x\\ry\\rz\\n" + "é" * 5000 + "\\r"\nwith open("big.txt", "w", newline="") as f: f.write(text)\nwith open("big.txt", encoding="utf-8") as f:\n    chunks = []\n    while True:\n        s = f.read(7)\n        if not s: break\n        chunks.append(s)\n    print(len("".join(chunks)), "".join(chunks) == text.replace("\\r\\n", "\\n").replace("\\r", "\\n"), f.newlines)\nwith open("big.txt") as f:\n    lines = f.readlines(); print(len(lines), lines[-3:] if len(lines) > 3 else lines, repr(lines[0]))\nwith open("big.txt", newline="") as f:\n    lines = list(f); print(len(lines), repr(lines[0]), repr(lines[-1][-3:]))\nwith open("big.txt", newline="\\r") as f:\n    print(len(list(f)))\nwith open("big.txt") as f:\n    f.readline(); pos = f.tell(); a = f.readline(); f.seek(pos); print(f.readline() == a, pos)\n    f.seek(0); print(repr(f.read(5)), f.tell())\n    print(f.seek(0, 2), repr(f.read()))\nwith open("w.txt", "w", newline="\\r\\n") as f: f.write("a\\nb\\n")\nprint(open("w.txt", "rb").read())\nwith open("w.txt", "w+") as f:\n    f.write("hello\\nworld\\n"); f.seek(0); print(repr(f.readline()), f.tell()); f.write("X"); f.seek(0); print(repr(f.read()))\nwith open("l.txt", "w", encoding="latin-1") as f: f.write("é")\nprint(open("l.txt", "rb").read(), open("l.txt", encoding="latin-1").read())\ntry: open("l.txt", encoding="ascii").read()\nexcept UnicodeDecodeError as e: print("decode error")\nprint(open("l.txt", encoding="utf-8", errors="replace").read())\nwith open("t.txt", "w") as f:\n    print("printed", 1, file=f); f.writelines(["a\\n", "b\\n"])\nprint(open("t.txt").read().splitlines())\nwith open("t.txt", "rb") as f: print(f.readline(), f.read(2), f.tell(), list(f))\nwith open("t.txt", "r+") as f: print(f.truncate(4), f.read())\nprint(open("t.txt").read())\ntry: open("t.txt").write(1)\nexcept Exception as e: print(type(e).__name__, e)\nf = open("t.txt", "w")\ntry: f.write(5)\nexcept TypeError as e: print(e)\nf.close()\ntry:\n    with open("t.txt") as g: g.seek(1, 1)\nexcept Exception as e: print(type(e).__name__, e)\n']

BOUNDARY = """
def attempt(*args):
    try:
        with open(*args) as f: print("read", f.read().strip())
    except OSError as e: print(type(e).__name__, e.errno)
attempt("sub/in.txt")
attempt("ok.txt")
attempt("../outside/secret.txt")
attempt("OUTSIDE/secret.txt")
attempt("/etc/passwd")
attempt("link.txt")
attempt("outdir/secret.txt")
attempt("sub/../../outside/secret.txt")
attempt("dangling", "w")
attempt(0)
attempt(b"sub/in.txt")
attempt("/")
"""
BOUNDARY_EXPECTED = """read inside
read inside
PermissionError 13
PermissionError 13
PermissionError 13
PermissionError 13
PermissionError 13
PermissionError 13
OSError %d
OSError 9
read inside
PermissionError 13
""" % errno.ELOOP


def run(command, cwd):
    return subprocess.run(command, capture_output=True, text=True, timeout=60, cwd=cwd)


def main():
    if sys.version_info[:2] != (3, 15):
        raise SystemExit('Use the pinned Python 3.15 development oracle')
    engine = str(Path(sys.argv[1]).resolve())
    for source in CASES:
        outputs = []
        for command in ([sys.executable, '-I', '-c', source], [engine, '-c', source]):
            with tempfile.TemporaryDirectory() as directory:
                outputs.append(run(command, directory))
        expected, actual = outputs
        if expected.returncode or actual.returncode or expected.stdout != actual.stdout:
            raise AssertionError(f'{source}\nCPython:\n{expected.stdout}{expected.stderr}\nspy:\n{actual.stdout}{actual.stderr}')
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        box, outside = root / 'box', root / 'outside'
        (box / 'sub').mkdir(parents=True)
        outside.mkdir()
        (outside / 'secret.txt').write_text('secret')
        (box / 'sub' / 'in.txt').write_text('inside')
        os.symlink(outside / 'secret.txt', box / 'link.txt')
        os.symlink(outside, box / 'outdir')
        os.symlink(outside / 'new.txt', box / 'dangling')
        os.symlink('sub/in.txt', box / 'ok.txt')
        actual = run([engine, '-c', BOUNDARY.replace('OUTSIDE', str(outside))], box)
        if actual.returncode or actual.stdout != BOUNDARY_EXPECTED or (outside / 'new.txt').exists():
            raise AssertionError(f'boundary:\n{actual.stdout}{actual.stderr}')
        # --mount replaces the default and mounts each directory at its own path.
        actual = run([engine, '--mount', 'box/sub', '-c',
                      'print(open("in.txt").read())\n'
                      f'try: open({str(box / "ok.txt")!r})\n'
                      'except PermissionError: print("denied")'], root)
        if actual.returncode or actual.stdout != 'inside\ndenied\n':
            raise AssertionError(f'--mount:\n{actual.stdout}{actual.stderr}')
        actual = run([engine, '--mount', 'missing', '-c', '1'], root)
        if actual.returncode != 1 or 'cannot mount' not in actual.stderr:
            raise AssertionError(f'missing mount:\n{actual.stdout}{actual.stderr}')
    print(f'Files: {len(CASES)} differential open() programs, mount boundary, and --mount passed')


if __name__ == '__main__':
    main()
