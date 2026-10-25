"""Fetch exact upstream revisions without installing runtime dependencies."""

import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent


def fetch(name, spec):
    destination = ROOT / "upstream" / name
    if not destination.exists():
        destination.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(destination)], check=True)
        subprocess.run(["git", "-C", str(destination), "remote", "add", "origin", spec["url"]], check=True)
    actual = subprocess.run(
        ["git", "-C", str(destination), "rev-parse", "HEAD"], capture_output=True, text=True
    )
    if actual.returncode or actual.stdout.strip() != spec["commit"]:
        dirty = subprocess.run(["git", "-C", str(destination), "status", "--porcelain"], capture_output=True, text=True, check=True)
        if dirty.stdout:
            raise SystemExit(f"refusing to change a dirty upstream checkout: {destination}")
        subprocess.run(["git", "-C", str(destination), "fetch", "--depth", "1", spec["url"], spec["commit"]], check=True)
        subprocess.run(["git", "-C", str(destination), "checkout", "--detach", spec["commit"]], check=True)
    actual = subprocess.check_output(["git", "-C", str(destination), "rev-parse", "HEAD"], text=True).strip()
    if actual != spec["commit"]:
        raise SystemExit(f"revision mismatch for {name}: {actual}")
    print(f"{name}: {actual}")


if __name__ == "__main__":
    specs = json.loads((ROOT / "upstream.json").read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("projects", nargs="*", choices=list(specs), default=["cython", "cpython"])
    args = parser.parse_args()
    for name in args.projects:
        fetch(name, specs[name])
