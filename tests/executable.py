"""Generated executables run without the Python source or libpython."""

import os
from pathlib import Path
import shlex
import subprocess
import tempfile

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
        subprocess.run([str(ROOT / "spyc"), *options, "-o", str(generated), str(source)], check=True)
        build(generated, *extra, binary=binary)
        source.unlink()
        generated.unlink()
        result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, cwd=directory)
        assert result.stdout == expected, result
print("Standalone C generation, compilation, and execution passed")

# spyc -c writes only the source, named after the input, for a host's main.
HOST = """#include "spy.h"
#include <stdio.h>
extern const char spy_hello_source[];
static SPYValue *answer(SPYContext *c, size_t argc, SPYValue *const *argv, void *data) {
    (void)argc; (void)argv; (void)data;
    return spy_int(c, 42);
}
static int output(void *p, const char *s, size_t n) { return fwrite(s, 1, n, p) == n ? 0 : -1; }
int main(void) {
    SPYContext *c = spy_context_new();
    if (!c) return 1;
    spy_set_output(c, output, stdout);
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

# The spy command's process status, reports, input(), and usage, as python's.
for args, stdin, status, stdout, stderr in [
    (["-c", "raise SystemExit(3)"], "", 3, "", ""),
    (["-c", "raise SystemExit('bye')"], "", 1, "", "bye\n"),
    (["-c", "raise SystemExit()"], "", 0, "", ""),
    (["-c", "1/0"], "", 1, "", 'Traceback (most recent call last):\n  File "<string>", line 1, in <module>\n'
                               "ZeroDivisionError: division by zero\n"),
    (["-c", "print(input('> '), flush=True)"], "abc\n", 0, "> abc\n", ""),
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
    result = subprocess.run([str(ROOT / "spyc"), "--analyze", "-o", str(Path(temp) / "main.c"), str(source)],
                            capture_output=True, text=True, check=True)
    assert [line.rsplit(None, 1) for line in result.stderr.splitlines()[1:]] == [
        [" " * 4 + str(helper), "18"], [" " * 4 + str(source), "14"]], result.stderr
print("spyc --analyze passed")
