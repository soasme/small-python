#!/usr/bin/env python3
"""Preview a release in a temporary clone; use -y to commit, tag, and push it.

Every package shares the engine's version: VERSION, spy.h, the manual, the
Python and npm packages, the Rust crates, and the todo example's dependency
on the published small-python, with the version fixtures of their tests.
The tag publishes all of them (.github/workflows/publish.yml)."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

# Each file spells the version as "X.Y.Z" exactly this many times.
QUOTED = {
    "spy.h": 1,
    "python/pyproject.toml": 1,
    "python/tests/test_isolation.py": 1,
    "javascript/package.json": 1,
    "javascript/test/fake-worker.js": 1,
    "javascript/test/runtime.test.js": 1,
    "rust/Cargo.toml": 1,
    "rust/small-python/Cargo.toml": 1,
    "rust/small-python-sys/Cargo.toml": 1,
    "rust/small-python-worker/Cargo.toml": 1,
    "examples/todo/Cargo.toml": 2,
}
LOCKS = ("python/uv.lock", "rust/Cargo.lock")
RELEASE_FILES = ("VERSION", "docs/manual.md", *QUOTED, *LOCKS)


def run(*args: str, cwd: Path) -> str:
    return subprocess.run(
        args, cwd=cwd, check=True, text=True, capture_output=True
    ).stdout.strip()


def run_checked(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def replace(path: Path, old: str, new: str, count: int) -> None:
    text = path.read_text()
    if text.count(old) != count:
        raise RuntimeError(f"{path.name}: expected {old} {count} times, found {text.count(old)}")
    path.write_text(text.replace(old, new))


def bumped(version: str, part: str) -> str:
    major, minor, patch = map(int, version.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("part", choices=("major", "minor", "patch"))
    parser.add_argument(
        "-y", "--yes", action="store_true", help="commit, tag, and push the release"
    )
    args = parser.parse_args()

    root = Path(run("git", "rev-parse", "--show-toplevel", cwd=Path.cwd()))
    origin = run("git", "remote", "get-url", "origin", cwd=root)
    with tempfile.TemporaryDirectory(prefix="small-python-bumpversion-") as directory:
        clone = Path(directory) / "small-python"
        run_checked(
            "git", "clone", "--quiet", "--branch", "main", origin, str(clone), cwd=root
        )
        old = (clone / "VERSION").read_text().strip()
        version = bumped(old, args.part)
        tag = f"v{version}"
        if run("git", "tag", "--list", tag, cwd=clone):
            raise RuntimeError(f"Tag {tag} already exists.")

        replace(clone / "VERSION", old, version, 1)
        replace(clone / "docs/manual.md", f"Version {old}", f"Version {version}", 1)
        for name, count in QUOTED.items():
            replace(clone / name, f'"{old}"', f'"{version}"', count)
        run_checked("uv", "lock", cwd=clone / "python")
        run_checked("cargo", "update", "--workspace", cwd=clone / "rust")

        package = clone / "python"
        run_checked("uv", "build", cwd=package)
        distributions = sorted(
            str(path)
            for pattern in ("*.whl", "*.tar.gz")
            for path in (package / "dist").glob(pattern)
        )
        run_checked("uvx", "twine", "check", "--strict", *distributions, cwd=package)
        run_checked("make", "rust-vendor", cwd=clone)
        run_checked("cargo", "publish", "--workspace", "--dry-run", cwd=clone / "rust")
        print("Release plan:", flush=True)
        run_checked("git", "diff", "--", *RELEASE_FILES, cwd=clone)
        if args.yes:
            run_checked("git", "add", *RELEASE_FILES, cwd=clone)
            run_checked("git", "commit", "-m", f"chore(release): {version}", cwd=clone)
            run_checked("git", "tag", tag, cwd=clone)
            run_checked(
                "git",
                "push",
                "--atomic",
                "origin",
                "HEAD:main",
                f"refs/tags/{tag}",
                cwd=clone,
            )


if __name__ == "__main__":
    main()
