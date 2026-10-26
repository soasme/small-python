import re

from setuptools import Extension, setup

version = re.search(r'#define SPY_VERSION "([^"]+)"', open("spy.h").read()).group(1)
setup(
    version=version,
    packages=["smallpython"],
    package_dir={"": "python"},
    ext_modules=[Extension(
        "smallpython._core",
        sources=["python/smallpython/_core.c", "spy.c", "spy-std.c"],
        include_dirs=["."],
        extra_compile_args=["-std=c11"],
    )],
)
