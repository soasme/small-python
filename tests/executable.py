"""Generated executables run without the Python source or libpython."""

import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent


def build(*sources, binary):
    """The sources with the engine, under the build's flags (a sanitizer build's included)."""
    flags = shlex.split(os.environ.get("CFLAGS", "-O2 -std=c11 -Wall -Wextra -Wpedantic"))
    subprocess.run([*shlex.split(os.environ.get("CC", "cc")), *flags, "-I", str(ROOT), *map(str, sources), str(ROOT / "spy.c"),
                    *shlex.split(os.environ.get("LDFLAGS", "")), "-lm", "-o", str(binary)], check=True)


# A program runs on the bare core unless spyc -M registers standard modules.
PROGRAM = "try:\n    import sys\nexcept ImportError:\n    sys = None\nprint('standalone', sum(range(10)), sys is None)\n"
for options, extra, expected in [([], [], "standalone 45 True\n"),
                                 (["-M", "sys"], [str(ROOT / "spy-std.c")], "standalone 45 False\n")]:
    with tempfile.TemporaryDirectory(prefix="spy executable ") as temp:
        directory = Path(temp)
        source = directory / "hello source.py"
        generated = directory / "hello generated.c"
        binary = directory / "hello program"
        source.write_text(PROGRAM, encoding="utf-8")
        subprocess.run([str(ROOT / "spyc"), "-e", *options, "-o", str(generated), str(source)], check=True)
        build(generated, *extra, binary=binary)
        source.unlink()
        generated.unlink()
        result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, cwd=directory)
        assert result.stdout == expected, result
print("Standalone C generation, compilation, and execution passed")

# Without -e or -c, spyc builds the executable itself, as qjsc does: with its
# build's compiler, against the spy.h and libraries beside it; -v shows the
# command, and the name defaults to a.out (out.c with -e).
for options, library, expected in [([], "libspy.a", "standalone 45 True\n"),
                                   (["-M", "sys"], "libspy-std.a", "standalone 45 False\n")]:
    with tempfile.TemporaryDirectory(prefix="spy executable ") as temp:
        directory = Path(temp)
        source = directory / "hello source.py"
        source.write_text(PROGRAM, encoding="utf-8")
        result = subprocess.run([str(ROOT / "spyc"), "-v", *options, str(source)],
                                cwd=directory, check=True, capture_output=True, text=True)
        assert f"-I {ROOT} " in result.stdout and f" {ROOT / library} " in result.stdout, result.stdout
        subprocess.run([str(ROOT / "spyc"), "-e", str(source)], cwd=directory, check=True)
        assert (directory / "out.c").exists()
        source.unlink()
        result = subprocess.run(["./a.out"], check=True, capture_output=True, text=True, cwd=directory)
        assert result.stdout == expected, result

# A failed or interrupted build leaves nothing behind (docs/build.md 2.1): it
# removes every file it began to write, keeps the files it did not reach, and
# never leaves its temporary C file; SpyBuildOutput.tla models each step.
# Every case starts with an old output, metafile and dependency rule.
def contract(args, status, message, kept, removed, env={}, spyc=ROOT / "spyc", signal_number=None, fake=True):
    with tempfile.TemporaryDirectory(prefix="spy executable ") as temp:
        directory = Path(temp)
        (directory / "tmp").mkdir()
        (directory / "one.py").write_text("print(1)\n", encoding="utf-8")
        for name in ("prog", "prog.c", "m.json", "p.d"):
            (directory / name).write_text("old", encoding="utf-8")
        command = [str(spyc), *args, "one.py"]
        environment = {**os.environ, "TMPDIR": str(directory / "tmp"), **env}
        if signal_number and not fake:
            # The real compiler, interrupted once it runs. A build that ends
            # before the signal arrives tests nothing; the caller runs it again.
            # Interrupted when run directly, clang may leave its own object
            # file in TMPDIR; spyc answers for its own files, not those.
            process = subprocess.Popen(command, cwd=directory, env=environment, stderr=subprocess.PIPE, text=True)
            deadline = time.monotonic() + 30
            while subprocess.run(["pgrep", "-P", str(process.pid)], capture_output=True).returncode:
                if process.poll() is not None:
                    break
                assert time.monotonic() < deadline, "the compiler did not start"
            process.send_signal(signal_number)
            result = subprocess.CompletedProcess(command, process.wait(), "", process.stderr.read())
            if result.returncode == 0:
                return False
        elif signal_number:
            # Interrupted while the compiler runs: a stand-in, first on PATH
            # under the compiler's name, leaves a child that ignores the
            # signal, as a compiler's linker may, writing the output a second
            # later, and exits first. spyc must stop the compiler's whole
            # process group, then kill what the signal did not stop.
            fake = directory / "bin"
            fake.mkdir()
            (fake / COMPILER).write_text('#!/bin/sh\nwhile [ "$1" != -o ]; do shift; done\n'
                                         '(trap "" INT TERM; sleep 1; echo new > "$2") &\n'
                                         'touch "$TMPDIR/../started"; sleep 0.2\n', encoding="utf-8")
            (fake / COMPILER).chmod(0o755)
            environment["PATH"] = f"{fake}{os.pathsep}{environment['PATH']}"
            process = subprocess.Popen(command, cwd=directory, env=environment, stderr=subprocess.PIPE, text=True)
            deadline = time.monotonic() + 30
            while not (directory / "started").exists():
                assert process.poll() is None and time.monotonic() < deadline, "the compiler did not start"
                time.sleep(0.001)
            process.send_signal(signal_number)
            result = subprocess.CompletedProcess(command, process.wait(), "", process.stderr.read())
            (directory / "started").unlink()
            time.sleep(2)  # a compiler left running writes the output by now
        else:
            result = subprocess.run(command, cwd=directory, env=environment, capture_output=True, text=True)
        assert result.returncode == status and message in result.stderr, (args, result)
        left = [path for path in (directory / "tmp").iterdir() if fake or path.name.startswith("spyc.")]
        assert not left, (args, left)
        for name in kept:
            assert (directory / name).read_text(encoding="utf-8") == "old", (args, name)
        for name in removed:
            assert not (directory / name).exists(), (args, name)
        files = [directory / name for name in ("prog", "prog.c", "m.json", "p.d")]
        if status == 0:
            assert all(path.read_bytes() != b"old" for path in files if path.name != "prog.c"), args
        else:
            assert all(not path.exists() or path.read_bytes() == b"old" for path in files), args
        return True


aux = ["--metafile", "m.json", "--deps", "p.d"]
# The compiler spyc runs, as -v prints it; the stand-in must be found on PATH.
with tempfile.TemporaryDirectory(prefix="spy executable ") as temp:
    (Path(temp) / "one.py").write_text("print(1)\n", encoding="utf-8")
    COMPILER = subprocess.run([str(ROOT / "spyc"), "-v", "one.py"], cwd=temp, check=True,
                              capture_output=True, text=True).stdout.split()[0]
    assert "/" not in COMPILER, f"spyc runs {COMPILER} by path; build it with a compiler found on PATH"
with tempfile.TemporaryDirectory(prefix="spy executable ") as temp:
    alone = Path(temp) / "spyc"  # spy.h beside it, but no libspy.a: the link fails
    shutil.copy(ROOT / "spyc", alone)
    shutil.copy(ROOT / "spy.h", Path(temp) / "spy.h")
    for args, status, message, kept, removed, env, spyc in [
        ([*aux, "-o", "prog"], 0, "", [], [], {}, ROOT / "spyc"),
        ([*aux, "-o", "prog"], 1, "cannot write", ["prog", "m.json", "p.d"], [], {"TMPDIR": "/nonexistent"}, ROOT / "spyc"),
        ([*aux, "-o", "prog"], 1, "cannot run", ["prog", "m.json", "p.d"], [], {"PATH": "/nonexistent"}, ROOT / "spyc"),
        ([*aux, "-o", "prog"], 1, "libspy.a", ["m.json", "p.d"], ["prog"], {}, alone),
        (["-e", *aux, "-o", "missing/prog.c"], 1, "cannot write missing/prog.c", ["m.json", "p.d"], [], {}, ROOT / "spyc"),
        (["--metafile", "missing/m.json", "--deps", "p.d", "-o", "prog"], 1, "cannot write missing/m.json", ["p.d"], ["prog"], {}, ROOT / "spyc"),
        (["-e", "--metafile", "missing/m.json", "--deps", "p.d", "-o", "prog.c"], 1, "cannot write missing/m.json", ["p.d"], ["prog.c"], {}, ROOT / "spyc"),
        (["--metafile", "m.json", "--deps", "missing/p.d", "-o", "prog"], 1, "cannot write missing/p.d", [], ["prog", "m.json"], {}, ROOT / "spyc"),
        (["-e", "-c", "-o", "prog"], 2, "usage:", ["prog"], [], {}, ROOT / "spyc"),
    ]:
        contract(args, status, message, kept, removed, env, spyc)
# Interrupted: the compiler's group is stopped and nothing is left.
for signal_number in (signal.SIGINT, signal.SIGTERM):
    contract([*aux, "-o", "prog"], -signal_number, "", ["m.json", "p.d"], ["prog"], signal_number=signal_number)
    # The compiler may end before the signal arrives, and spyc then removes
    # the metafile it began, so only the files' states are checked.
    assert any(contract([*aux, "-o", "prog"], -signal_number, "", [], [], signal_number=signal_number, fake=False)
               for _ in range(10)), "the compiler ended before every signal"
print("Executable output passed")

# spyc -c writes only the source, named after the input, for a host's main.
HOST = """#include "spy.h"
#include <stdio.h>
extern const char spy_hello_source[];
static SPYValue *answer(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)argc; (void)argv; (void)data;
    return spy_int(c, 42);
}
static int output(SPYContext *c, void *p, const char *s, size_t n) { (void)c; return fwrite(s, 1, n, p) == n ? 0 : -1; }
int main(void) {
    SPYContext *c = spy_context_new();
    if (!c) return 1;
    spy_set_output(c, output, NULL, stdout);
    int status = spy_define(c, "answer", answer, NULL) || spy_exec(c, spy_hello_source, "hello.py");
    spy_context_free(c);
    return status;
}
"""
with tempfile.TemporaryDirectory(prefix="spy executable ") as temp:
    directory = Path(temp)
    source, generated, host, binary = (directory / name for name in ("hello source.py", "hello generated.c", "host.c", "host program"))
    source.write_text("print('hosted', answer())\n", encoding="utf-8")
    host.write_text(HOST, encoding="utf-8")
    subprocess.run([str(ROOT / "spyc"), "-c", "-o", str(generated), str(source)], check=True)
    assert "int main" not in generated.read_text(encoding="utf-8")
    build(host, generated, binary=binary)
    source.unlink()
    result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, cwd=directory)
    assert result.stdout == "hosted 42\n", result
    usage = subprocess.run([str(ROOT / "spyc"), "-c", "-M", "sys", "-o", str(generated), str(source)], capture_output=True, text=True)
    assert usage.returncode == 2 and usage.stderr.startswith("usage:"), usage
print("Source-only generation for a host program passed")

repl = subprocess.run(
    [str(ROOT / "spy"), "-i"],
    input="x = 40\nx + 2\ndef double(n):\n    return n * 2\n\ndouble(x)\n",
    capture_output=True, text=True, check=True, timeout=10,
)
assert not repl.stderr, repl.stderr
assert ">>> 42\n" in repl.stdout and ">>> 80\n" in repl.stdout, repl.stdout
print("Interactive globals and multiline function definition passed")

# The spy command's process status, reports, input(), -O, and usage, as python's.
for args, stdin, status, stdout, stderr in [
    (["-c", "raise SystemExit(3)"], "", 3, "", ""),
    (["-c", "raise SystemExit('bye')"], "", 1, "", "bye\n"),
    (["-c", "raise SystemExit()"], "", 0, "", ""),
    (["-c", "1/0"], "", 1, "", 'Traceback (most recent call last):\n  File "<string>", line 1, in <module>\n'
                               "ZeroDivisionError: division by zero\n"),
    (["-c", "print(input('> '), flush=True)"], "abc\n", 0, "> abc\n", ""),
    (["-O", "-c", "assert False; print(__debug__)"], "", 0, "False\n", ""),
    (["-OO", "-c", "def f():\n 'doc'\nprint(f.__doc__)"], "", 0, "None\n", ""),
    (["--bogus"], "", 2, "", "usage:"),
    (["-c"], "", 2, "", "usage:"),
]:
    result = subprocess.run([str(ROOT / "spy"), *args], input=stdin, capture_output=True, text=True, timeout=60)
    assert (result.returncode, result.stdout) == (status, stdout) and result.stderr.startswith(stderr), (args, result)
print("spy exit statuses, error reports, input, and usage passed")

# spyc --analyze lists the output and each input with its size, largest first.
with tempfile.TemporaryDirectory(prefix="spy executable ") as temp:
    source, helper = Path(temp) / "main.py", Path(temp) / "helper.py"
    source.write_text("import helper\n", encoding="utf-8")
    helper.write_text("x = 1\n" * 3, encoding="utf-8")
    result = subprocess.run([str(ROOT / "spyc"), "-e", "--analyze", "-o", str(Path(temp) / "main.c"), str(source)],
                            capture_output=True, text=True, check=True)
    assert [line.rsplit(None, 1) for line in result.stderr.splitlines()[1:]] == [
        [" " * 4 + str(helper), "18"], [" " * 4 + str(source), "14"]], result.stderr
print("spyc --analyze passed")
