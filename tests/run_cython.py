"""Run unchanged pure-Python doctests from a pinned Cython checkout.

This is a language adapter, not Cython's compiled-extension test runner. It
neither removes unsupported code nor replaces upstream expected results.
"""

import argparse
import ast
from collections import Counter
import doctest
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tokenize
import warnings

ROOT = Path(__file__).resolve().parent.parent


def verify_checkout(path, commit):
    if not (path / "runtests.py").is_file():
        raise SystemExit("missing Cython checkout; run: make upstream")
    head = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    if head != commit:
        raise SystemExit(f"Cython revision mismatch: expected {commit}, got {head}")
    dirty = subprocess.check_output(["git", "-C", str(path), "status", "--porcelain", "--untracked-files=no"], text=True)
    if dirty:
        raise SystemExit("upstream tracked files have modifications; restore them before testing")


def inventory(path):
    return {
        directory.name: dict(sorted(Counter(p.suffix or "<none>" for p in directory.rglob("*") if p.is_file()).items()))
        for directory in sorted((path / "tests").iterdir()) if directory.is_dir()
    }


def groups(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if not doc:
                continue
            name = getattr(node, "name", "<module>")
            examples = doctest.DocTestParser().get_examples(doc, name)
            if examples:
                line = node.body[0].lineno
                yield name, line, examples


def frame(mode, source):
    data = source.encode("utf-8")
    return f"{mode} {len(data)}\n".encode("ascii") + data


def run_group(driver, source, examples, timeout):
    active = [e for e in examples if not e.options.get(doctest.SKIP)]
    request = frame("E", source) + b"".join(frame("I", e.source) for e in active)
    try:
        result = subprocess.run([str(driver)], input=request, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "driver timeout"
    if result.returncode:
        return None, f"driver exit {result.returncode}: {result.stderr.decode('utf-8', errors='replace')[:500]}"
    try:
        replies = [json.loads(line) for line in result.stdout.decode("utf-8").splitlines()]
    except (UnicodeError, ValueError) as exc:
        return None, f"invalid driver response: {exc}"
    if len(replies) != len(active) + 1:
        return None, "incomplete driver response"
    return replies, None


def check_example(example, reply):
    flags = 0
    for option, enabled in example.options.items():
        if enabled:
            flags |= option
    checker = doctest.OutputChecker()
    if example.exc_msg is not None:
        actual = reply["type"] + (": " + reply["message"] if reply["message"] else "") + "\n"
        expected = example.exc_msg
        if flags & doctest.IGNORE_EXCEPTION_DETAIL:
            actual, expected = actual.split(":", 1)[0].strip(), expected.split(":", 1)[0].strip()
        return not reply["ok"] and checker.check_output(expected, actual, flags)
    return reply["ok"] and checker.check_output(example.want, reply["output"], flags)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, default=ROOT / "tests/upstream/cython")
    parser.add_argument("--driver", type=Path, default=ROOT / "run-cython")
    parser.add_argument("--report", type=Path, default=ROOT / "tests/results/cython.json")
    parser.add_argument("--select", default="*.py", help="glob within upstream tests/run (default: all .py files)")
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--report-only", action="store_true", help="write a failing baseline without returning a failing status")
    args = parser.parse_args()
    pin = json.loads((ROOT / "tests/upstream.json").read_text())["cython"]
    verify_checkout(args.upstream, pin["commit"])
    if not args.driver.is_file():
        raise SystemExit("missing run-cython executable; run: make run-cython")
    records, files = [], []
    selected = sorted((args.upstream / "tests/run").glob(args.select))
    if not selected:
        raise SystemExit(f"selector matched no upstream files: {args.select}")
    for path in selected:
        relative = str(path.relative_to(args.upstream))
        if path.suffix != ".py":
            files.append({"file": relative, "status": "adapter-ineligible", "reason": "only upstream pure-Python .py files are adapted"})
            continue
        try:
            with tokenize.open(path) as stream:
                source = stream.read()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                tree = ast.parse(source, filename=relative)
            tests = list(groups(tree))
        except (SyntaxError, UnicodeError, ValueError) as exc:
            files.append({"file": relative, "status": "adapter-ineligible", "reason": f"host parser cannot discover doctests: {exc}"})
            continue
        if not tests:
            files.append({"file": relative, "status": "adapter-ineligible", "reason": "no static doctests; unittest/build/dynamic tests need another adapter"})
            continue
        files.append({"file": relative, "status": "attempted", "groups": len(tests)})
        for name, line, examples in tests:
            replies, error = run_group(args.driver.resolve(), source, examples, args.timeout)
            initialization = replies[0] if replies else None
            responses = iter(replies[1:] if replies else [])
            for index, example in enumerate(examples):
                record = {"file": relative, "group": name, "example": index, "line": line + example.lineno,
                          "source": example.source, "expected": example.want}
                if example.options.get(doctest.SKIP):
                    record.update(status="skip", reason="upstream doctest SKIP directive")
                elif error:
                    record.update(status="error", reason=error)
                else:
                    reply = next(responses)
                    if not initialization["ok"]:
                        record.update(status="fail", reason="unchanged module initialization failed", actual=initialization)
                    else:
                        record.update(status="pass" if check_example(example, reply) else "fail", actual=reply)
                records.append(record)
    counts = Counter(r["status"] for r in records)
    file_counts = Counter(f["status"] for f in files)
    report = {
        "schema": 1, "suite": "Cython upstream pure-Python doctests", "commit": pin["commit"],
        "selector": args.select, "host_python": sys.version.split()[0],
        "host_platform": platform.platform(),
        "engine_sources": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                           for name in ("spy.c", "spy.h", "run-cython.c")},
        "driver_sha256": hashlib.sha256(args.driver.read_bytes()).hexdigest(),
        "scope": "Unchanged .py modules and upstream doctest expectations; no compiled Cython, C API/ABI, .pyx, .srctree, or unittest claim.",
        "adapter_limits": ["Static docstrings only; dynamic __test__ is not discovered.",
                           "Interactive driver displays only the final top-level expression in an example.",
                           "No exception traceback-frame comparison; exception type/message follow doctest matching."],
        "inventory": inventory(args.upstream), "files": dict(file_counts), "examples": dict(counts),
        "file_results": files, "results": records,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Cython {pin['commit']}: files {dict(file_counts)}; examples {dict(counts)}")
    print(f"Report: {args.report}")
    if not records:
        raise SystemExit("no upstream examples were discovered")
    incomplete = counts["fail"] or counts["error"] or file_counts["adapter-ineligible"]
    return 0 if args.report_only else int(bool(incomplete))


if __name__ == "__main__":
    raise SystemExit(main())
