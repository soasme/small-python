"""Native modules (spy-module.h) through the spy command: what an import
finds and runs, and what it reports on each failure (manual 3.2; the
SpyNative.tla model).

usage: native.py SPY   (CC and CFLAGS: the build's compiler and flags)

The modules are built from examples/fib.c and tests/native/ as shared
libraries; fib.c is also linked into a C host, without SPY_SHARED_MODULE,
as an ordinary C module.
"""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SPY = Path(sys.argv[1]).resolve()
SUFFIX = ".dll" if os.name == "nt" else ".so"
VERSION = (ROOT / "VERSION").read_text().strip()
MAJOR, MINOR, PATCH = map(int, VERSION.split("."))
CC = shlex.split(os.environ.get("CC", "cc"))
CFLAGS = shlex.split(os.environ.get("CFLAGS", "-O2 -std=c11 -Wall -Wextra -Wpedantic"))


def compile_module(source, target, *defines):
    subprocess.run([*CC, *CFLAGS, "-shared", "-fPIC", "-DSPY_SHARED_MODULE", *defines, "-I", str(ROOT),
                    str(source), "-o", str(target)], check=True)


def run(directory, *args, stdin=None):
    return subprocess.run([str(SPY), *args], cwd=directory, input=stdin, capture_output=True, text=True, timeout=60)


def case(name, files, program, *args):
    """Run program as main.py in a directory holding files (name -> a
    library in LIB, text, or None for a directory); it must succeed."""
    directory = TEMP / name
    for path, content in {**files, "main.py": program}.items():
        target = directory / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            target.mkdir()
        elif isinstance(content, Path):
            shutil.copy(content, target)
        else:
            target.write_text(content, encoding="utf-8")
    result = run(directory, *(args or ["main.py"]))
    assert result.returncode == 0, (name, result.stdout, result.stderr)
    return result.stdout


with tempfile.TemporaryDirectory(prefix="spy native ") as temp:
    TEMP = Path(temp)
    LIB = TEMP / "lib"
    LIB.mkdir()
    library = {}
    for source, name, defines in [
        (ROOT / "examples/fib.c", "fib", []),
        *((ROOT / f"tests/native/{n}.c", n, []) for n in ("probe", "failing", "silent", "misnamed", "plain")),
        *((ROOT / "tests/native/version.c", name, [f'-DBUILT="{built}"', f"-DINIT=spy_init_{name}"])
          for name, built in [("current", VERSION), ("older", f"{MAJOR}.{MINOR - 1}.0"),
                              ("newer", f"{MAJOR}.{MINOR}.{PATCH + 1}"), ("major", f"{MAJOR + 1}.{MINOR}.0"),
                              ("garbled", "x")])]:
        library[name] = LIB / (name + SUFFIX)
        compile_module(source, library[name], *defines)
    (LIB / ("bad" + SUFFIX)).write_text("not a library\n")
    library["bad"] = LIB / ("bad" + SUFFIX)

    # A module calls the engine through the table its host set: the example
    # imports, raises, and is cached under its name without a __file__.
    case("fib", {"fib" + SUFFIX: library["fib"]},
         "import fib, sys\n"
         "assert [fib.fib(n) for n in range(10)] == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]\n"
         "assert fib.__name__ == 'fib' and sys.modules['fib'] is fib and not hasattr(fib, '__file__')\n"
         "try:\n    fib.fib(-1)\nexcept ValueError as e:\n    assert str(e) == 'fib() argument must be in 0..92'\n"
         "else:\n    raise AssertionError\n")

    # A library loads once: a second import is the cached module, and one
    # after its removal runs the init again. Calls back into Python keep
    # their arguments and exceptions.
    case("probe", {"probe" + SUFFIX: library["probe"]},
         "import sys, probe\n"
         "import probe as same\n"
         "assert same is probe and probe.count() == 1\n"
         "del sys.modules['probe']\n"
         "import probe as again\n"
         "assert again is not probe and again.count() == 2\n"
         "assert probe.call(lambda *a, **k: (a, k), 1, x=2) == ((1,), {'x': 2})\n"
         "def boom():\n    raise KeyError('k')\n"
         "try:\n    probe.call(boom)\nexcept KeyError as e:\n    assert e.args == ('k',)\n"
         "else:\n    raise AssertionError\n")

    # NAME.so comes before NAME.py, as CPython's extension modules do; a
    # directory named NAME.so is not a library. A package's submodule may be
    # native, and a copy of a library elsewhere is another library, with
    # state of its own. A package's __init__ is source, so pkg2 is a
    # namespace package.
    case("search", {"probe" + SUFFIX: library["probe"], "probe.py": "raise AssertionError('source')\n",
                    "thing" + SUFFIX: None, "thing.py": "value = 1\n",
                    "pkg/__init__.py": "", "pkg/probe" + SUFFIX: library["probe"],
                    "pkg2/__init__" + SUFFIX: library["probe"]},
         "import probe, thing, pkg.probe, pkg2\n"
         "from pkg import probe as sub\n"
         "assert probe.count() == 1 and thing.value == 1\n"
         "assert sub is pkg.probe and sub.__name__ == 'pkg.probe' and sub.__package__ == 'pkg'\n"
         "assert sub is not probe and sub.count() == 1\n"
         "assert pkg2.__file__ is None\n")

    # -c and standard input search the working directory.
    files = {"probe" + SUFFIX: library["probe"]}
    assert case("command", files, "", "-c", "import probe; print(probe.count())") == "1\n"
    assert run(TEMP / "command", "-", stdin="import probe\nprint(probe.count())\n").stdout == "1\n"

    # Each failure raises, leaves nothing in sys.modules, and is raised
    # again by the next import: an init that failed runs again.
    failures = {
        "bad": (ImportError, "bad" + SUFFIX),
        "plain": (ImportError, "dynamic module does not define spy_module (build it with SPY_SHARED_MODULE)"),
        "misnamed": (ImportError, "dynamic module does not define module export function (spy_init_misnamed)"),
        "older": (ImportError, f"dynamic module was built for spy {MAJOR}.{MINOR - 1}.0, not {VERSION}"),
        "newer": (ImportError, f"dynamic module was built for spy {MAJOR}.{MINOR}.{PATCH + 1}, not {VERSION}"),
        "major": (ImportError, f"dynamic module was built for spy {MAJOR + 1}.{MINOR}.0, not {VERSION}"),
        "garbled": (ImportError, f"dynamic module was built for spy x, not {VERSION}"),
        "silent": (SystemError, "initialization of silent failed without raising an exception"),
    }
    program = ["import sys",
               "def fails(name, kind, text):",
               "    try:",
               "        __import__(name)",
               "    except kind as e:",
               "        assert text in str(e), (name, str(e))",
               "    else:",
               "        raise AssertionError(name)",
               "    assert name not in sys.modules",
               "import current",
               "fails('failing', ValueError, 'attempt 1')",
               "fails('failing', ValueError, 'attempt 2')"]
    program += [f"fails({name!r}, {kind.__name__}, {text!r})" for name, (kind, text) in failures.items()]
    program += [f"fails({name!r}, {kind.__name__}, {text!r})" for name, (kind, text) in failures.items()]
    case("failures", {name + SUFFIX: library[name] for name in [*failures, "current", "failing"]},
         "\n".join(program) + "\n")
    # Uncaught, the error is reported as any other.
    result = run(TEMP / "failures", "-c", "import misnamed")
    assert result.returncode == 1 and result.stderr.endswith(
        "ImportError: dynamic module does not define module export function (spy_init_misnamed)\n"), result

    # Without SPY_SHARED_MODULE, fib.c is a C module a host links itself.
    host = TEMP / "host.c"
    host.write_text('#include "spy.h"\n#include <assert.h>\n'
                    "int spy_init_fib(SPYContext *, SPYValue *);\n"
                    "int main(void) {\n"
                    "    SPYContext *c = spy_context_new();\n"
                    '    assert(c && !spy_new_module(c, "fib", spy_init_fib));\n'
                    '    assert(!spy_exec(c, "import fib\\nassert fib.fib(10) == 55\\n", "host.py"));\n'
                    "    spy_context_free(c);\n"
                    "    return 0;\n"
                    "}\n")
    binary = TEMP / "host"
    subprocess.run([*CC, *CFLAGS, *shlex.split(os.environ.get("LDFLAGS", "")), "-I", str(ROOT), str(host),
                    str(ROOT / "examples/fib.c"), str(ROOT / "libspy.a"), "-lm", "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("Native modules: loading, search, failures and static linking passed")
