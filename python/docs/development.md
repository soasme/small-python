# Development

The package lives in `python/` of the Small Python repository:

```text
python/
  pyproject.toml          package metadata and cibuildwheel settings
  setup.py                builds the spy-worker executable
  src/small_python/
    __init__.py           the public names and versions
    _runtime.py           Runtime, Object, errors: the parent side of the protocol
    _wire.py              message framing and value encoding
    _runtime.pyi          type stub
  csrc/                   engine sources copied in at build time (ignored by git)
  docs/                   this documentation
  tests/                  unittest suite for the package
  scripts/bumpversion.py  release helper
```

The package is pure Python plus one executable, `small_python/spy-worker`,
built from the repository's `spy-worker.c` (the protocol worker) and the
engine's `spy.c` and `spy-std.c`. `setup.py` copies those files, their
headers, and licenses into `python/csrc/` before each build, so the source
distribution carries everything and builds without the rest of the
repository. The protocol between the package and its worker is specified in
[docs/packaging/protocol.md](../../docs/packaging/protocol.md), and the
package in [docs/packaging/python.md](../../docs/packaging/python.md).

## Build and test

With [uv](https://docs.astral.sh/uv/), from `python/`:

```sh
uv sync --locked                    # build and install into .venv
uv run python -m unittest discover -s tests   # run the tests
uv build                            # sdist and wheel into dist/
```

Or, from the repository root, without uv:

```sh
make test-binding
```

which builds `spy-worker` with the Makefile, assembles the package in
`.obj/binding`, and runs the same tests. The tests use only the standard library; `pytest tests` also
runs them. Rebuild after changing the engine sources: `uv sync --reinstall-package small-python`.

## Release

The wheel holds an executable, not an extension module, so it is tagged
`py3-none-<platform>` and one wheel per platform serves CPython 3.10 and later.
Wheels are built on Linux (manylinux and musllinux, x86_64 and aarch64),
macOS (arm64 and x86_64), and Windows (x86_64, with MinGW-w64 GCC on `PATH`) by
[cibuildwheel](https://cibuildwheel.pypa.io/), configured under
`[tool.cibuildwheel]` in `pyproject.toml`; each wheel runs the tests in
`python/tests`.

Pushing a tag `vX.Y.Z` that matches the `version` in `python/pyproject.toml`
and in `javascript/package.json` runs `.github/workflows/publish.yml`, which
builds the sdist and wheels and publishes them to PyPI, and builds the
WebAssembly worker and publishes the JavaScript package to npm, both with
trusted publishing.

To prepare a release, preview the version bump:

```sh
cd python
uv run python scripts/bumpversion.py patch
```

Use `major`, `minor`, or `patch`. The script clones `origin` into a temporary
directory, bumps the version and lockfile in `python/` and the version in
`javascript/package.json`, builds and checks the
distributions, and shows the change. Add `-y` to commit, tag, and push:

```sh
uv run python scripts/bumpversion.py patch -y
git pull --ff-only
```

Releases are cut from the remote `main` branch, so push your changes first. The
working checkout is not modified.

The package version (`small_python.__version__`) is independent of the engine
version (`small_python.SPY_VERSION`, from `spy.h`).
