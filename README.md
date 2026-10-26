# smallpy

A placeholder Python package. No functionality yet.

Requires Python 3.12 or newer. Manage the project with [uv](https://docs.astral.sh/uv/):

```sh
uv sync --locked
uv run python -c "import smallpy"
uv build
```

## Publishing

The workflow in `.github/workflows/publish.yml` builds and publishes to PyPI when
a version tag matching `pyproject.toml` is pushed (for example, `v0.1.0`).

Before the first release, configure a [PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
with these values:

- Project: `smallpy`
- Owner: `soasme`
- Repository: `smallpy`
- Workflow: `publish.yml`
- Environment: `pypi`

Create the `pypi` environment in the GitHub repository settings as well.
No PyPI API token is needed.

To publish the initial version after the repository is pushed:

```sh
git tag v0.1.0
git push origin v0.1.0
```

For later releases, preview a version bump:

```sh
uv run python scripts/bumpversion.py patch
```

Use `major`, `minor`, or `patch`. The script clones `origin` into a temporary
directory, bumps the version and lockfile, builds and checks the distributions,
and displays the changes. Add `-y` to commit, tag, and push the release:

```sh
uv run python scripts/bumpversion.py patch -y
git pull --ff-only
```

Releases use the remote `main` branch; push any intended changes before running
the script. The working checkout is left untouched.
