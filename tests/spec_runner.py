"""Run the language specification tests (tests/spec) on an engine.

usage: spec_runner.py ENGINE [--oracle PYTHON] [--report FILE] [--only SUBSTRING] [--strict]

Each test is staged in a temporary directory beside harness.py, with the
contents of a sibling NAME.fixtures directory, and run as a script; the
engine's results are reported per chapter. The tests encode PLS-315 and need
no other implementation. With --oracle, a second implementation (such as the
pinned CPython 3.15 build) must also pass every test, which validates the
tests themselves. With --strict the exit status is nonzero when the engine
fails any test.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "tests/spec"
TIMEOUT = 60


def metadata(path):
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            break
        key, _, value = line[1:].strip().partition(":")
        if value:
            fields[key.strip()] = value.strip()
    return fields


def run(command, directory):
    # A sanitizer build keeps its options; nothing else leaks into a test.
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"}
    env.update({name: value for name, value in os.environ.items() if name.endswith("SAN_OPTIONS")})
    try:
        result = subprocess.run(command, cwd=directory, capture_output=True, text=True, timeout=TIMEOUT, env=env)
    except subprocess.TimeoutExpired:
        return None, "timed out"
    return result.returncode, (result.stdout + result.stderr).strip()


def outcome(code, output, negative):
    if negative:
        if code == 0 or code is None:
            return False, output if code is None else f"expected {negative}, the test ran"
        last = output.splitlines()[-1] if output else ""
        return negative in last, output
    return code == 0, output


def check(path, engine, oracle):
    fields = metadata(path)
    negative = fields.get("negative")
    with tempfile.TemporaryDirectory(prefix="spec-") as directory:
        shutil.copy(SPEC / "harness.py", directory)
        fixtures = path.with_suffix(".fixtures")
        if fixtures.is_dir():
            shutil.copytree(fixtures, directory, dirs_exist_ok=True)
        shutil.copy(path, Path(directory) / "test_spec.py")
        oracle_ok, oracle_output = (outcome(*run([str(oracle), "-E", "-s", "test_spec.py"], directory), negative)
                                    if oracle else (None, ""))
        engine_ok, engine_output = outcome(*run([str(engine), "test_spec.py"], directory), negative)
    return {"test": str(path.relative_to(SPEC)), "spec": fields.get("spec", ""),
            "oracle": {None: "skipped", True: "passed", False: "failed"}[oracle_ok], "engine": "passed" if engine_ok else "failed",
            "oracle_output": "" if oracle_ok is not False else oracle_output[-2000:],
            "engine_output": "" if engine_ok else engine_output[-2000:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("engine", type=Path)
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--report", type=Path, default=ROOT / "tests/results/spec.json")
    parser.add_argument("--only", default="")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    if args.oracle and not args.oracle.is_file():
        raise SystemExit(f"missing oracle {args.oracle}")
    engine = args.engine.resolve()
    tests = sorted(path for path in SPEC.rglob("*.py") if path.name != "harness.py" and ".fixtures" not in str(path.parent) and args.only in str(path))
    with ThreadPoolExecutor(os.cpu_count() or 4) as pool:
        oracle = args.oracle and args.oracle.resolve()
        results = list(pool.map(lambda path: check(path, engine, oracle), tests))
    chapters = {}
    for result in results:
        chapter = result["test"].split("/")[0]
        counts = chapters.setdefault(chapter, {"tests": 0, "passed": 0})
        counts["tests"] += 1
        counts["passed"] += result["engine"] == "passed"
    invalid = [result for result in results if result["oracle"] == "failed"]
    failed = [result for result in results if result["oracle"] != "failed" and result["engine"] != "passed"]
    for result in invalid:
        print(f"INVALID {result['test']} (the oracle fails it)\n    " + result["oracle_output"].replace("\n", "\n    "))
    for result in failed:
        print(f"FAIL {result['test']}")
        if args.verbose:
            print("    " + result["engine_output"].replace("\n", "\n    "))
    for chapter, counts in sorted(chapters.items()):
        print(f"{chapter}: {counts['passed']}/{counts['tests']}")
    passed = sum(result["engine"] == "passed" for result in results if result["oracle"] != "failed")
    validated = f"; {len(invalid)} invalid on {args.oracle.name}" if args.oracle else ""
    print(f"Spec: {passed}/{len(results) - len(invalid)} tests pass on {engine.name}{validated}")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps({"chapters": chapters, "results": results}, indent=2) + "\n")
    if invalid or (args.strict and failed):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
