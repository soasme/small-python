"""Generated executables run without the Python source or libpython."""

import os
from pathlib import Path
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
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
        subprocess.run(
            [*shlex.split(os.environ.get("CC", "cc")), "-std=c11", "-Wall", "-Wextra", "-Wpedantic", "-O2", "-I", str(ROOT), str(generated), *extra, str(ROOT / "spy.c"), "-lm", "-o", str(binary)],
            check=True,
        )
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
    subprocess.run(
        [*shlex.split(os.environ.get("CC", "cc")), "-std=c11", "-Wall", "-Wextra", "-Wpedantic", "-O2", "-I", str(ROOT), str(host), str(generated), str(ROOT / "spy.c"), "-lm", "-o", str(binary)],
        check=True,
    )
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
