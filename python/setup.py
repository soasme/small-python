"""Build small_python._core from the binding and the Small Python engine.

The engine sources sit in the parent directory of this one. They are copied
into csrc/ before every build, so an sdist carries them and builds alone.
"""
import shutil
from pathlib import Path

from setuptools import Extension, setup

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
FILES = {
    "csrc/spy.c": "spy.c",
    "csrc/spy.h": "spy.h",
    "csrc/spy-std.c": "spy-std.c",
    "csrc/spy-std.h": "spy-std.h",
    "csrc/spy-std-modules.h": "spy-std-modules.h",
    "csrc/spy-intrinsics.h": "spy-intrinsics.h",
    "csrc/spy-unicode.h": "spy-unicode.h",
    "csrc/licenses/python.txt": "docs/licenses/python.txt",
    "csrc/licenses/unicode.txt": "docs/licenses/unicode.txt",
}

if (ENGINE / "spy.c").is_file():
    for target, source in FILES.items():
        (HERE / target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ENGINE / source, HERE / target)

setup(
    ext_modules=[Extension(
        "small_python._core",
        sources=["src/small_python/_core.c", "csrc/spy.c", "csrc/spy-std.c"],
        depends=[target for target in FILES if target.endswith(".h")],
        include_dirs=["csrc"],
        extra_compile_args=["-std=c11"],
    )],
)
