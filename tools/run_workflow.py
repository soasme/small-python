#!/usr/bin/env python3
"""Run a GitHub Actions workflow locally with act (https://github.com/nektos/act).

    tools/run_workflow.py                      # every Linux job of test.yml
    tools/run_workflow.py test.yml -j test     # one job
    tools/run_workflow.py -j test --matrix compiler:gcc

The workflow, a file in .github/workflows or a path, is the first argument when
given. The remaining arguments go to act unchanged. act runs each job in Docker
on a copy of the tree (ignored files excluded), so the checkout is untouched.
Jobs for macOS and Windows runners have no container image and are skipped;
act reports them. The exit status is act's: nonzero when any job fails.

Jobs run natively, in act's Ubuntu image with what GitHub's ubuntu-latest
has and the image lacks: clang and its sanitizer runtimes, Rust, and Maven.
Docker builds the image once and caches it. On an arm64 host the jobs run on
arm64, not under x86_64 emulation, whose posix_spawn reports no exec failure."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGE = "small-python-act"
DOCKERFILE = b"""FROM catthehacker/ubuntu:act-latest
RUN apt-get update && apt-get install -y --no-install-recommends clang libclang-rt-dev maven \\
 && rm -rf /var/lib/apt/lists/*
ENV RUSTUP_HOME=/usr/local/rustup CARGO_HOME=/usr/local/cargo PATH=/usr/local/cargo/bin:$PATH
RUN curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
"""


def main():
    act_args = sys.argv[1:]
    if act_args and act_args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    name = "test.yml"
    if act_args and not act_args[0].startswith("-"):
        name = act_args.pop(0)
    workflow = Path(name)
    if not workflow.exists():
        workflow = ROOT / ".github" / "workflows" / name
    if not workflow.is_file():
        sys.exit(f"run_workflow: no workflow {name}")
    if not shutil.which("act"):
        sys.exit("run_workflow: act is not installed (brew install act)")
    if subprocess.run(["docker", "info"], capture_output=True).returncode:
        sys.exit("run_workflow: Docker is not running")
    if subprocess.run(["docker", "build", "-q", "-t", IMAGE, "-"], input=DOCKERFILE).returncode:
        sys.exit("run_workflow: cannot build the runner image")

    with tempfile.TemporaryDirectory(prefix="act-artifacts-") as artifacts:
        command = ["act", "push", "--workflows", str(workflow),
                   "-P", f"ubuntu-latest={IMAGE}", "--pull=false",
                   "--artifact-server-path", artifacts, *act_args]
        print("+", " ".join(command), flush=True)
        return subprocess.run(command, cwd=ROOT).returncode


if __name__ == "__main__":
    sys.exit(main())
