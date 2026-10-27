# Development

The package lives in `python/` of the Small Python repository:

```text
python/
  pyproject.toml          package metadata and cibuildwheel settings
  setup.py                builds the small_python._core extension
  src/small_python/
    __init__.py           Runtime, Object, Error, and the version
    _core.c               the CPython binding to the spy_* C API
  csrc/                   engine sources copied in at build time (ignored by git)
  docs/                   this documentation
  scripts/bumpversion.py  release helper
```

The extension compiles the binding together with the engine's `spy.c` and
`spy-std.c`. Those files stay at the top of the repository; `setup.py` copies
them and their headers and licenses into `python/csrc/` before each build, so
the source distribution carries everything and builds without the rest of the
repository.

## Build and test

With [uv](https://docs.astral.sh/uv/), from `python/`:

```sh
uv sync --locked                    # build and install into .venv
uv run python ../tests/binding.py   # run the binding tests
uv build                            # sdist and wheel into dist/
```

Or, from the repository root, without uv:

```sh
make test-binding
```

which builds the extension into `.obj/binding` with `setuptools` and runs the
same tests. Rebuild after changing the engine sources: `uv sync --reinstall-package small-python`.

## Release

Wheels are built for CPython 3.13 and later on Linux (manylinux and musllinux,
x86_64 and aarch64) and macOS (arm64 and x86_64) by
[cibuildwheel](https://cibuildwheel.pypa.io/), configured under
`[tool.cibuildwheel]` in `pyproject.toml`; each wheel runs
`tests/binding.py`.

Pushing a tag `vX.Y.Z` that matches the `version` in `python/pyproject.toml`
runs `.github/workflows/publish.yml`, which builds the sdist and wheels and
publishes them to PyPI with trusted publishing.

To prepare a release, preview the version bump:

```sh
cd python
uv run python scripts/bumpversion.py patch
```

Use `major`, `minor`, or `patch`. The script clones `origin` into a temporary
directory, bumps the version and lockfile in `python/`, builds and checks the
distributions, and shows the change. Add `-y` to commit, tag, and push:

```sh
uv run python scripts/bumpversion.py patch -y
git pull --ff-only
```

Releases are cut from the remote `main` branch, so push your changes first. The
working checkout is not modified.

The package version (`small_python.__version__`) is independent of the engine
version (`small_python.SPY_VERSION`, from `spy.h`).
