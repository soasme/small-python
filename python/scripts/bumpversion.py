#!/usr/bin/env python3
"""Preview a release in a temporary clone; use -y to commit, tag, and push it.
The tag publishes both packages, so the npm package takes the same version."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

# The package lives in python/ of the repository; git paths are from the root.
PROJECT = "python"
RELEASE_FILES = (f"{PROJECT}/pyproject.toml", f"{PROJECT}/uv.lock", "javascript/package.json")


def run(*args: str, cwd: Path) -> str:
    return subprocess.run(
        args, cwd=cwd, check=True, text=True, capture_output=True
    ).stdout.strip()


def run_checked(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


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
        package = clone / PROJECT
        run_checked("uv", "version", "--bump", args.part, "--no-sync", cwd=package)
        version = run("uv", "version", "--short", cwd=package)
        run_checked("npm", "version", version, "--no-git-tag-version", cwd=clone / "javascript")
        tag = f"v{version}"
        if run("git", "tag", "--list", tag, cwd=clone):
            raise RuntimeError(f"Tag {tag} already exists.")

        run_checked("uv", "build", cwd=package)
        distributions = sorted(
            str(path)
            for pattern in ("*.whl", "*.tar.gz")
            for path in (package / "dist").glob(pattern)
        )
        run_checked("uvx", "twine", "check", "--strict", *distributions, cwd=package)
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
