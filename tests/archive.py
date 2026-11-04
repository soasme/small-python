"""Smoke-test a staged release archive: each shipped tool runs from it alone.

usage: archive.py DIR

DIR holds what a release archive ships (tools/archive.sh). Each tool runs
from DIR, in an empty directory: spy runs a program and imports a native
module built with the platform's compiler from spy-module.h, spy-worker
reports the engine's version, and spyc builds a program that registers sys,
from the headers and libraries beside it. Where spyc cannot build executables
(Windows), it must say so, and its C output must build with the platform's
compiler instead.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

archive = Path(sys.argv[1]).resolve()
exe = ".exe" if os.name == "nt" else ""
shipped = [f"spy{exe}", f"spyc{exe}", f"spy-worker{exe}", "spy.h", "spy-std.h", "spy-module.h", "libspy.a", "libspy-std.a",
           "LICENSE", "README.md", "licenses/python.txt", "licenses/unicode.txt", "licenses/quickjs.txt"]
missing = [name for name in shipped if not (archive / name).is_file()]
assert not missing, f"{archive.name} lacks {missing}"


def run(*args, cwd):
    return subprocess.run([str(arg) for arg in args], cwd=cwd, capture_output=True, text=True, timeout=300)


with tempfile.TemporaryDirectory() as temp:
    directory = Path(temp)
    result = run(archive / f"spy{exe}", "-c", "print(sum(range(10)))", cwd=directory)
    assert (result.returncode, result.stdout) == (0, "45\n"), result
    (directory / "twice.c").write_text(
        '#include "spy-module.h"\n'
        "static SPYValue *twice(SPYContext *c, size_t argc, SPYValue *const *argv, SPYValue *kw, void *data) {\n"
        "    int64_t n;\n"
        "    (void)argc; (void)kw; (void)data;\n"
        "    return spy_as_int(c, argv[0], &n) ? NULL : spy_int(c, 2 * n);\n"
        "}\n"
        "SPY_MODULE int spy_init_twice(SPYContext *c, SPYValue *module) {\n"
        '    SPYValue *f = spy_native(c, "twice", twice, NULL, NULL);\n'
        '    int status = f ? spy_set_attr(c, module, "twice", f) : -1;\n'
        "    spy_release(f);\n"
        "    return status;\n"
        "}\n", encoding="utf-8")
    library = "twice.dll" if os.name == "nt" else "twice.so"
    result = run("gcc" if os.name == "nt" else "cc", "-shared", *([] if os.name == "nt" else ["-fPIC"]),
                 "-DSPY_SHARED_MODULE", "-I", archive, "twice.c", "-o", library, cwd=directory)
    assert result.returncode == 0, result
    result = run(archive / f"spy{exe}", "-c", "import twice; print(twice.twice(21))", cwd=directory)
    assert (result.returncode, result.stdout) == (0, "42\n"), result
    version = run(archive / f"spy{exe}", "--version", cwd=directory).stdout
    result = run(archive / f"spy-worker{exe}", "--version", cwd=directory)
    assert result.returncode == 0 and version == f"spy {result.stdout}", (version, result)

    (directory / "hello.py").write_text("import sys\nprint('hello', sys.version_info[0])\n", encoding="utf-8")
    spyc = archive / f"spyc{exe}"
    if os.name == "nt":
        result = run(spyc, "-M", "sys", "hello.py", cwd=directory)
        assert result.returncode == 1 and "not supported on this platform" in result.stderr, result
        result = run(spyc, "-e", "-M", "sys", "-o", "hello.c", "hello.py", cwd=directory)
        assert result.returncode == 0, result
        result = run("gcc", "-I", archive, "hello.c", archive / "libspy-std.a", archive / "libspy.a", "-lm",
                     "-o", "hello.exe", cwd=directory)
    else:
        result = run(spyc, "-M", "sys", "-o", "hello", "hello.py", cwd=directory)
    assert result.returncode == 0, result
    result = run(directory / f"hello{exe}", cwd=directory)
    assert (result.returncode, result.stdout) == (0, "hello 3\n"), result
print(f"{archive.name}: spy, a native module, spy-worker and spyc run from the archive")
