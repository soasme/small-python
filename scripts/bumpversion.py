#!/usr/bin/env python3
"""Preview a release in a temporary clone; use -y to commit, tag, and push it."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

RELEASE_FILES = ("pyproject.toml", "uv.lock")


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
        run_checked("uv", "version", "--bump", args.part, "--no-sync", cwd=clone)
        version = run("uv", "version", "--short", cwd=clone)
        tag = f"v{version}"
        if run("git", "tag", "--list", tag, cwd=clone):
            raise RuntimeError(f"Tag {tag} already exists.")

        run_checked("uv", "build", cwd=clone)
        distributions = sorted(
            str(path)
            for pattern in ("*.whl", "*.tar.gz")
            for path in (clone / "dist").glob(pattern)
        )
        run_checked("uvx", "twine", "check", "--strict", *distributions, cwd=clone)
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
