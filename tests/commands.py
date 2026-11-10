"""spyc's commands: run, build, test, clean and version (docs/build.md 2.3).

Each case runs spyc in a fresh directory and checks what it prints, the
status it returns, and the cache it leaves in .spyc. A stand-in compiler,
first on PATH under the compiler's name, makes the executables of the
failure cases; SpyCache.tla models the cache's steps.
"""

import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
SPYC = str(ROOT / "bin" / "spyc")
VERSION = next(line.split('"')[1] for line in (ROOT / "spy.h").read_text().splitlines() if "define SPY_VERSION" in line)


def spyc(directory, *args, status=0, env=None, spyc=SPYC):
    result = subprocess.run([spyc, *args], cwd=directory, capture_output=True, text=True,
                            env={**os.environ, **(env or {})}, timeout=120)
    assert result.returncode == status, (args, result)
    return result


def cache(directory):
    return sorted(path.name for path in (directory / ".spyc").iterdir()) if (directory / ".spyc").exists() else []


def files(directory, tree):
    for name, text in tree.items():
        (directory / name).parent.mkdir(parents=True, exist_ok=True)
        (directory / name).write_text(text, encoding="utf-8")


def fresh():
    return tempfile.TemporaryDirectory(prefix="spyc commands ")


with fresh() as temp:
    (Path(temp) / "one.py").write_text("print(1)\n", encoding="utf-8")
    COMPILER = spyc(temp, "-v", "one.py").stdout.split()[0]
    assert "/" not in COMPILER, f"spyc runs {COMPILER} by path; build it with a compiler found on PATH"


def stand_in(directory, program):
    """A compiler on PATH that writes PROGRAM as the executable, or fails."""
    (directory / "bin").mkdir(exist_ok=True)
    script = '#!/bin/sh\nwhile [ "$1" != -o ]; do shift; done\n'
    script += "exit 1\n" if program is None else f"cat > \"$2\" <<'EOF'\n{program}EOF\nchmod +x \"$2\"\n"
    (directory / "bin" / COMPILER).write_text(script, encoding="utf-8")
    (directory / "bin" / COMPILER).chmod(0o755)
    return {"PATH": f"{directory / 'bin'}{os.pathsep}{os.environ['PATH']}"}


# version, and the usage errors of the commands that take no arguments.
with fresh() as temp:
    assert spyc(temp, "version").stdout == f"spyc {VERSION}\n"
    for args in (["version", "x"], ["clean", "x"]):
        assert "usage:" in spyc(temp, *args, status=2).stderr
print("spyc version passed")

# spyc build is spyc: the same C file, the same executable.
with fresh() as temp:
    directory = Path(temp)
    files(directory, {"app.py": "import helper\nprint(helper.x)\n", "helper.py": "x = 7\n"})
    spyc(directory, "-e", "-o", "bare.c", "app.py")
    spyc(directory, "build", "-e", "-o", "verb.c", "app.py")
    assert (directory / "bare.c").read_bytes() == (directory / "verb.c").read_bytes()
    spyc(directory, "build", "-o", "app", "app.py")
    assert subprocess.run(["./app"], cwd=directory, capture_output=True, text=True).stdout == "7\n"
    assert "usage:" in spyc(directory, "build", status=2).stderr
    assert not cache(directory)
print("spyc build passed")

# spyc run: the program gets the entry and the arguments after it, and its
# exit status is spyc's. The executable is cached under the working
# directory; a second run compiles nothing, an edit compiles again and
# replaces its slot's executable, and other arguments get a slot of their own.
with fresh() as temp:
    directory = Path(temp)
    files(directory, {"app.py": "import sys\nprint(sys.argv)\nraise SystemExit(len(sys.argv))\n",
                      "pkg/__init__.py": "", "pkg/__main__.py": "from . import tool\nprint(__name__, tool.x)\n",
                      "pkg/tool.py": "x = 'tool'\n"})
    first = spyc(directory, "run", "-v", "-M", "sys", "app.py", "a", "app.py", "-v", "x.c", status=5)
    assert first.stdout.splitlines()[-1] == "['app.py', 'a', 'app.py', '-v', 'x.c']", first.stdout
    assert COMPILER in first.stdout, first.stdout
    [built] = cache(directory)
    again = spyc(directory, "run", "-v", "-M", "sys", "app.py", "a", "app.py", "-v", "x.c", status=5)
    assert again.stdout == "['app.py', 'a', 'app.py', '-v', 'x.c']\n" and cache(directory) == [built], again
    (directory / "app.py").write_text("import sys\nprint('edited', sys.argv[1:])\n", encoding="utf-8")
    assert spyc(directory, "run", "-v", "-M", "sys", "app.py", "b").stdout.endswith("edited ['b']\n")
    [edited] = cache(directory)
    assert edited != built and edited[:17] == built[:17], (built, edited)
    assert spyc(directory, "run", "-O", "-M", "sys", "app.py").stdout == "edited []\n"
    assert len(cache(directory)) == 2
    # -m runs a package's __main__ with its package set.
    assert spyc(directory, "run", "-m", "pkg", "arg").stdout == "__main__ tool\n"
    # Several runs at once share the cache.
    runs = [subprocess.Popen([SPYC, "run", "-M", "sys", "app.py", str(i)], cwd=directory, stdout=subprocess.PIPE, text=True)
            for i in range(4)]
    assert [run.communicate()[0] for run in runs] == [f"edited ['{i}']\n" for i in range(4)]
    assert all(run.returncode == 0 for run in runs)
    assert not [name for name in cache(directory) if "." in name], cache(directory)
    # A run needs an entry, and has no -o, -e, -c or --.
    for args in ([], ["-o", "p", "app.py"], ["-e", "app.py"], ["-c", "app.py"], ["--", "app.py"], ["-M"]):
        assert "usage:" in spyc(directory, "run", *args, status=2).stderr, args
    # A failed build runs nothing, and leaves no file in the cache.
    files(directory, {"bad.py": "import missing\n"})
    before = cache(directory)
    assert "No module named 'missing'" in spyc(directory, "run", "bad.py", status=1).stderr
    assert cache(directory) == before
print("spyc run passed")

# A C module runs too, and an edit to it compiles again.
with fresh() as temp:
    directory = Path(temp)
    shutil.copy(ROOT / "examples/fib.c", directory / "fib.c")
    files(directory, {"app.py": "import fib\nprint(fib.fib(10))\n"})
    assert spyc(directory, "run", "fib.c", "app.py").stdout == "55\n"
    [built] = cache(directory)
    with open(directory / "fib.c", "a", encoding="utf-8") as f:
        f.write("/* edited */\n")
    assert spyc(directory, "run", "fib.c", "app.py").stdout == "55\n"
    assert cache(directory) != [built] and len(cache(directory)) == 1
print("spyc run with a C module passed")

# The stamp covers spy.h and the libraries: a changed header compiles again.
with fresh() as temp:
    directory = Path(temp)
    tree = directory / "tree"
    tree.mkdir()
    shutil.copy(SPYC, tree / "spyc")
    for name in ("spy.h", "spy-std.h", "libspy.a", "libspy-std.a"):
        shutil.copy(ROOT / name, tree / name)
    files(directory, {"app.py": "print('ok')\n"})
    for _ in range(2):
        assert spyc(directory, "run", "-M", "sys", "app.py", spyc=str(tree / "spyc")).stdout == "ok\n"
    [built] = cache(directory)
    with open(tree / "spy-std.h", "a", encoding="utf-8") as f:
        f.write("/* edited */\n")
    assert spyc(directory, "run", "-M", "sys", "app.py", spyc=str(tree / "spyc")).stdout == "ok\n"
    assert cache(directory) != [built]
print("spyc run's stamp passed")

# Failures in the cache: a compiler that fails, one interrupted, and an
# executable that cannot run leave no temporary file behind.
with fresh() as temp:
    directory = Path(temp)
    files(directory, {"app.py": "print(1)\n"})
    spyc(directory, "run", "app.py", status=1, env=stand_in(directory, None))
    assert cache(directory) == []
    env = stand_in(directory, "#!/nonexistent/interpreter\n")
    assert "cannot run .spyc/" in spyc(directory, "run", "app.py", status=1, env=env).stderr
    assert len(cache(directory)) == 1
    shutil.rmtree(directory / ".spyc")
    (directory / "bin" / COMPILER).write_text('#!/bin/sh\ntouch started; sleep 30\n', encoding="utf-8")
    for signal_number in (signal.SIGINT, signal.SIGTERM):
        process = subprocess.Popen([SPYC, "run", "app.py"], cwd=directory, env={**os.environ, **env})
        deadline = time.monotonic() + 30
        while not (directory / "started").exists():
            assert process.poll() is None and time.monotonic() < deadline, "the compiler did not start"
            time.sleep(0.001)
        process.send_signal(signal_number)
        assert process.wait() == -signal_number
        (directory / "started").unlink()
        assert cache(directory) == [], cache(directory)
print("spyc run's failures passed")

# spyc test: test_*.py files below each path, in name order, passing over
# hidden directories; a named file is a test whatever its name. A test
# passes when it exits with 0; the summary counts both outcomes.
TESTS = {"tests/test_a.py": "assert 1 + 1 == 2\n", "tests/sub/test_b.py": "assert 1 == 2, 'no'\n",
         "tests/test_c.py": "import missing\n", "tests/helper.py": "assert False\n",
         "tests/.hidden/test_h.py": "assert False\n", "tests/test_d.txt": "", "check.py": "print('named')\n",
         "test_top.py": "import sys\nprint(sys.argv)\n"}
with fresh() as temp:
    directory = Path(temp)
    files(directory, TESTS)
    result = spyc(directory, "test", "tests", status=1)
    assert result.stdout == ("FAIL  tests/sub/test_b.py (exit 1)\nok    tests/test_a.py\n"
                             "FAIL  tests/test_c.py (build)\n1 passed, 2 failed\n"), result
    assert "AssertionError: no" in result.stderr and "No module named 'missing'" in result.stderr, result.stderr
    result = spyc(directory, "test", "-M", "sys", "check.py", "test_top.py", "tests/test_a.py")
    assert result.stdout == "named\nok    check.py\n['test_top.py']\nok    test_top.py\nok    tests/test_a.py\n3 passed, 0 failed\n", result
    result = spyc(directory, "test", status=1)
    assert result.stdout.startswith("FAIL  test_top.py (build)\nFAIL  tests/sub/test_b.py") and "1 passed, 3 failed\n" in result.stdout, result
    assert "spyc: error: no tests in nothing" in spyc(directory, "test", "tests", "nothing", status=1).stderr
    (directory / "empty").mkdir()
    assert "spyc: error: no tests in empty" in spyc(directory, "test", "empty", status=1).stderr
    for args in (["-m", "tests"], ["-o", "p", "tests"], ["-e", "tests"]):
        result = spyc(directory, "test", *args, status=2)
        assert "usage:" in result.stderr and result.stdout == "", (args, result)
    # A C module serves each test.
    shutil.copy(ROOT / "examples/fib.c", directory / "fib.c")
    files(directory, {"fibs/test_fib.py": "import fib\nassert fib.fib(10) == 55\n"})
    assert spyc(directory, "test", "fib.c", "fibs").stdout == "ok    fibs/test_fib.py\n1 passed, 0 failed\n"
    # A test ended by a signal fails with 128 and the signal.
    env = stand_in(directory, "#!/bin/sh\nkill -9 $$\n")
    assert spyc(directory, "test", "-O", "fib.c", "fibs", status=1, env=env).stdout == "FAIL  fibs/test_fib.py (exit 137)\n0 passed, 1 failed\n"
print("spyc test passed")

# spyc clean removes the cache's files and the cache, and keeps a file it
# did not make, failing then.
with fresh() as temp:
    directory = Path(temp)
    spyc(directory, "clean")
    files(directory, {"app.py": "print(1)\n"})
    spyc(directory, "run", "app.py")
    assert cache(directory)
    spyc(directory, "clean")
    assert not (directory / ".spyc").exists()
    spyc(directory, "run", "app.py")
    (directory / ".spyc" / "mine").write_text("kept", encoding="utf-8")
    assert "spyc: error: cannot remove .spyc" in spyc(directory, "clean", status=1).stderr
    assert cache(directory) == ["mine"]
print("spyc clean passed")
