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

# C modules (docs/build.md 5.4): NAME.c is compiled into the program and
# registered as NAME before the entry runs, winning over a NAME.py; the
# arguments after -- reach the compiler. The dependency rule names the C file.
ANSWER = """#include "spy-module.h"
SPY_MODULE int spy_init_answer(SPYContext *c, SPYValue *module) {
    SPYValue *value = spy_int(c, ANSWER);
    int status = value ? spy_set_attr(c, module, "value", value) : -1;
    spy_release(value);
    return status;
}
"""
with tempfile.TemporaryDirectory(prefix="spy executable ") as temp:
    directory = Path(temp)
    (directory / "app.py").write_text("import answer, fib\nprint(answer.value, fib.fib(10))\n", encoding="utf-8")
    (directory / "answer.py").write_text("value = 'source'\n", encoding="utf-8")
    (directory / "c modules").mkdir()
    (directory / "c modules/answer.c").write_text(ANSWER, encoding="utf-8")
    shutil.copy(ROOT / "examples/fib.c", directory / "c modules/fib.c")
    modules = ["c modules/answer.c", "c modules/fib.c"]
    result = subprocess.run([str(ROOT / "spyc"), "-v", "--deps", "p.d", "-o", "prog", "app.py", *modules, "--", "-DANSWER=42"],
                            cwd=directory, check=True, capture_output=True, text=True)
    assert " c modules/answer.c c modules/fib.c -DANSWER=42 " in result.stdout, result.stdout
    assert (directory / "p.d").read_text(encoding="utf-8") == "prog: app.py c\\ modules/answer.c c\\ modules/fib.c\n"
    for name in ("app.py", "answer.py"):
        (directory / name).unlink()
    result = subprocess.run(["./prog"], cwd=directory, check=True, capture_output=True, text=True)
    assert result.stdout == "42 55\n", result
    # -e writes the same main; the host compiles the modules with it.
    (directory / "app.py").write_text("import fib\nprint(fib.fib(20))\n", encoding="utf-8")
    subprocess.run([str(ROOT / "spyc"), "-e", "-o", "prog.c", "app.py", "c modules/fib.c"], cwd=directory, check=True)
    build(directory / "prog.c", directory / "c modules/fib.c", binary=directory / "prog")
    result = subprocess.run(["./prog"], cwd=directory, check=True, capture_output=True, text=True)
    assert result.stdout == "6765\n", result
    # A C module that does not compile fails the build, leaving nothing.
    (directory / "broken.c").write_text("this is not C\n", encoding="utf-8")
    (directory / "prog").unlink()
    result = subprocess.run([str(ROOT / "spyc"), "-o", "prog", "app.py", "c modules/fib.c", "broken.c"], cwd=directory, capture_output=True, text=True)
    assert result.returncode == 1 and "broken.c" in result.stderr and not (directory / "prog").exists(), result
    # A module name must be an identifier; -c has no main to register it in,
    # and only executable output runs a compiler for the arguments after --.
    (directory / "prog").write_text("old", encoding="utf-8")
    for args in (["app.py", "fib-2.c"], ["app.py", ".c"], ["-c", "app.py", "c modules/fib.c"], ["-e", "app.py", "--", "-lm"],
                 ["-c", "app.py", "--"], ["-o", "c modules/fib.c", "app.py", "c modules/fib.c"]):
        result = subprocess.run([str(ROOT / "spyc"), *args], cwd=directory, capture_output=True, text=True)
        assert result.returncode == 2 and result.stderr.startswith("usage:"), (args, result)
    assert (directory / "prog").read_text(encoding="utf-8") == "old"
    assert (directory / "c modules/fib.c").read_text(encoding="utf-8") == (ROOT / "examples/fib.c").read_text(encoding="utf-8")
print("C modules passed")

# Archive modules (docs/build.md 5.4): libNAME.a is a compiled C module NAME,
# as a Rust or C library builds it. It links where a C module compiles, after
# the program and before the engine, so the program pulls its init from it and
# it finds the engine's functions. One name is given once, whatever the form.
def archive(directory, name, source, *flags):
    """libNAME.a holding source compiled under the build's flags."""
    flags = [*shlex.split(os.environ.get("CFLAGS", "-O2 -std=c11")), *flags]
    subprocess.run([*shlex.split(os.environ.get("CC", "cc")), *flags, "-I", str(ROOT), "-c", "-o", f"{name}.o", source],
                   cwd=directory, check=True)
    subprocess.run(["ar", "rcs", f"lib{name}.a", f"{name}.o"], cwd=directory, check=True)
    return directory / f"lib{name}.a"


with tempfile.TemporaryDirectory(prefix="spy executable ") as temp:
    directory = Path(temp)
    (directory / "c modules").mkdir()
    (directory / "c modules/answer.c").write_text(ANSWER, encoding="utf-8")
    shutil.copy(ROOT / "examples/fib.c", directory / "c modules/fib.c")
    archive(directory / "c modules", "answer", "answer.c", "-DANSWER=42")
    archive(directory / "c modules", "fib", "fib.c")
    (directory / "app.py").write_text("import answer, fib\nprint(answer.value, fib.fib(10))\n", encoding="utf-8")
    (directory / "answer.py").write_text("value = 'source'\n", encoding="utf-8")
    modules = ["c modules/libanswer.a", "c modules/fib.c"]
    result = subprocess.run([str(ROOT / "spyc"), "-v", "--deps", "p.d", "-o", "prog", "app.py", *modules, "--", "-lm"],
                            cwd=directory, check=True, capture_output=True, text=True)
    assert " -x none c modules/libanswer.a c modules/fib.c -lm " + str(ROOT / "libspy.a") in result.stdout, result.stdout
    assert (directory / "p.d").read_text(encoding="utf-8") == "prog: app.py c\\ modules/libanswer.a c\\ modules/fib.c\n"
    (directory / "answer.py").unlink()
    result = subprocess.run(["./prog"], cwd=directory, check=True, capture_output=True, text=True)
    assert result.stdout == "42 55\n", result
    # -e declares and registers it; the host links the archive.
    (directory / "app.py").write_text("import fib\nprint(fib.fib(20))\n", encoding="utf-8")
    subprocess.run([str(ROOT / "spyc"), "-e", "-o", "prog.c", "app.py", "c modules/libfib.a"], cwd=directory, check=True)
    build(directory / "prog.c", directory / "c modules/libfib.a", binary=directory / "prog")
    result = subprocess.run(["./prog"], cwd=directory, check=True, capture_output=True, text=True)
    assert result.stdout == "6765\n", result
    # An archive without the init fails the link, leaving nothing.
    (directory / "other.c").write_text("int spy_init_other_name(void) { return 0; }\n", encoding="utf-8")
    archive(directory, "other", "other.c")
    (directory / "prog").unlink()
    result = subprocess.run([str(ROOT / "spyc"), "-o", "prog", "app.py", "c modules/libfib.a", "libother.a"],
                            cwd=directory, capture_output=True, text=True)
    assert result.returncode == 1 and "spy_init_other" in result.stderr and not (directory / "prog").exists(), result
    # An archive is named libNAME.a for an identifier NAME; a name comes once,
    # since the linker would take an earlier init and never read the archive.
    (directory / "prog").write_text("old", encoding="utf-8")
    for args in (["app.py", "fib.a"], ["app.py", "c modules/fib.a"], ["app.py", "lib.a"], ["app.py", "li.a"],
                 ["app.py", ".a"], ["app.py", "libfib-2.a"], ["app.py", "c modules/fib.c", "c modules/libfib.a"],
                 ["app.py", "c modules/libfib.a", "c modules/libfib.a"], ["app.py", "c modules/fib.c", "c modules/fib.c"],
                 ["-c", "app.py", "c modules/libfib.a"], ["-o", "c modules/libfib.a", "app.py", "c modules/libfib.a"]):
        result = subprocess.run([str(ROOT / "spyc"), *args], cwd=directory, capture_output=True, text=True)
        assert result.returncode == 2 and result.stderr.startswith("usage:"), (args, result)
    assert (directory / "prog").read_text(encoding="utf-8") == "old"
print("Archive modules passed")

# The program's command line is sys.argv, decoded as UTF-8 with
# surrogateescape, and open reaches the working directory, as under spy.
with tempfile.TemporaryDirectory(prefix="spy executable ") as temp:
    directory = Path(temp)
    (directory / "app.py").write_text("import sys\nprint(sys.argv == sys.orig_argv, sys.argv is not sys.orig_argv, sys.argv)\n"
                                      "with open(sys.argv[1]) as f:\n    print(f.read())\n", encoding="utf-8")
    (directory / "data file").write_text("contents", encoding="utf-8")
    subprocess.run([str(ROOT / "spyc"), "-M", "sys", "-o", "prog", "app.py"], cwd=directory, check=True)
    result = subprocess.run([b"./prog", b"data file", "é".encode(), b"\xff", b""], cwd=directory, capture_output=True)
    assert result.stdout == "True True ['./prog', 'data file', 'é', '\\udcff', '']\ncontents\n".encode(), result
    # Outside the working directory nothing is reachable.
    result = subprocess.run(["./prog", "../data file"], cwd=directory, capture_output=True, text=True)
    assert result.returncode == 1 and "Error" in result.stderr, result
    # Without a working directory the mount fails or reaches nothing, and the
    # program still runs.
    (directory / "gone").mkdir()
    (directory / "app.py").write_text("import sys\nprint(sys.argv[1:])\nopen('x')\n", encoding="utf-8")
    subprocess.run([str(ROOT / "spyc"), "-M", "sys", "-o", "prog", "app.py"], cwd=directory, check=True)
    result = subprocess.run("cd gone && rmdir ../gone && ../prog arg", shell=True, cwd=directory, capture_output=True, text=True)
    assert result.returncode == 1 and result.stdout == "['arg']\n" and "Error: " in result.stderr, result
print("Command line and working directory passed")

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
    (["-i", "x"], "", 2, "", "usage:"),
    (["--version", "x"], "", 2, "", "usage:"),
    # The program's arguments follow it into sys.argv.
    (["-c", "import sys; print(sys.argv)", "a", "-b", "", "-c"], "", 0, "['-c', 'a', '-b', '', '-c']\n", ""),
    (["-", "q", "--version"], "import sys; print(sys.argv)", 0, "['-', 'q', '--version']\n", ""),
    ([], "import sys; print(sys.argv)", 0, "['']\n", ""),
    # sys.orig_argv is the whole command line, options included.
    (["--mount", ".", "-OO", "-c", "import sys; print(sys.orig_argv[1:])", "a"], "", 0,
     "['--mount', '.', '-OO', '-c', 'import sys; print(sys.orig_argv[1:])', 'a']\n", ""),
    (["-", "q"], "import sys; print(sys.orig_argv[1:])", 0, "['-', 'q']\n", ""),
]:
    result = subprocess.run([str(ROOT / "spy"), *args], input=stdin, capture_output=True, text=True, timeout=60)
    assert (result.returncode, result.stdout) == (status, stdout) and result.stderr.startswith(stderr), (args, result)
with tempfile.TemporaryDirectory(prefix="spy argv ") as temp:
    script = Path(temp) / "args.py"
    script.write_text("import sys; print(sys.argv, sys.orig_argv[1:])\n", encoding="utf-8")
    result = subprocess.run([str(ROOT / "spy"), "-O", str(script), "-i", b"caf\xc3\xa9", b"\xff"],
                            capture_output=True, text=True, check=True)
    assert result.stdout == f"[{str(script)!r}, '-i', 'café', '\\udcff'] ['-O', {str(script)!r}, '-i', 'café', '\\udcff']\n", result
    shell = subprocess.run([str(ROOT / "spy"), "-i"], input="import sys\nsys.orig_argv[1:]\n", capture_output=True, text=True, check=True)
    assert ">>> ['-i']\n" in shell.stdout, shell
    shell = subprocess.run([str(ROOT / "spy"), "-i"], input="import sys\nsys.argv\n", capture_output=True, text=True, check=True)
    assert ">>> ['']\n" in shell.stdout, shell
print("spy exit statuses, error reports, input, arguments, and usage passed")

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
