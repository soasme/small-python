"""Build small_python: pure Python plus the spy-worker executable.

The engine sources sit in the parent directory of this one. They are copied
into csrc/ before every build, so an sdist carries them and builds alone. The
worker is an executable, not an extension module, so one wheel per platform
serves every CPython: it is tagged py3-none-<platform>. MSVC has no C11
complex numbers, so on Windows the worker is built with MinGW-w64 GCC.
"""
import os
import shutil
import sys
from pathlib import Path

from setuptools import Extension, setup
from setuptools.command.bdist_wheel import bdist_wheel
from setuptools.command.build_ext import build_ext

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
FILES = {
    "csrc/spy-worker.c": "spy-worker.c",
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


class build_worker(build_ext):
    """Compile spy-worker.c as the engine and as the worker, then link them."""

    def get_ext_filename(self, name):
        return os.path.join(*name.split(".")) + (".exe" if sys.platform == "win32" else "")

    def build_extension(self, ext):
        if sys.platform == "win32":
            return self.build_with_gcc(ext)
        objects = []
        for part, macros in (("engine", [("SPY_WORKER_ENGINE", None)]), ("worker", [])):
            objects += self.compiler.compile(
                ext.sources, output_dir=os.path.join(self.build_temp, part), macros=macros,
                include_dirs=ext.include_dirs, extra_postargs=ext.extra_compile_args)
        path = self.get_ext_fullpath(ext.name)
        self.compiler.link_executable(objects, os.path.basename(path), output_dir=os.path.dirname(path),
                                      libraries=["m"])

    def build_with_gcc(self, ext):
        objects = []
        for part, flags in (("engine", ["-DSPY_WORKER_ENGINE"]), ("worker", [])):
            objects.append(os.path.join(self.build_temp, part + ".o"))
            self.mkpath(self.build_temp)
            self.spawn(["gcc", "-c", *ext.sources, "-o", objects[-1], *flags,
                        *(f"-I{d}" for d in ext.include_dirs), *ext.extra_compile_args])
        path = self.get_ext_fullpath(ext.name)
        self.mkpath(os.path.dirname(path))
        self.spawn(["gcc", *objects, "-o", path, "-static", "-lm"])


class bdist_platform_wheel(bdist_wheel):
    def get_tag(self):
        return "py3", "none", super().get_tag()[2]


setup(
    ext_modules=[Extension(
        "small_python.spy-worker",
        sources=["csrc/spy-worker.c"],
        depends=[target for target in FILES if target.endswith((".c", ".h"))],
        include_dirs=["csrc"],
        extra_compile_args=["-std=c11", "-O2"],
    )],
    cmdclass={"build_ext": build_worker, "bdist_wheel": bdist_platform_wheel},
)
