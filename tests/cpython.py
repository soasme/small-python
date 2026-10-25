"""Inventory pinned CPython tests and run explicitly documented language ports.

Run this tool with the pinned CPython 3.15 build. CPython is a development
oracle, never an implementation dependency of spy.
"""

import argparse
import ast
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import contextlib
import doctest
import hashlib
import importlib
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import tokenize
import unittest
import warnings

from run_cython import check_example, run_group

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "tests/upstream/cpython"
PORTS = ("test.test_unpack", "test.test_unpack_ex", "test.test_listcomps", "test.test_genexps")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    pin = json.loads((ROOT / "tests/upstream.json").read_text())["cpython"]
    head = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()
    if head != pin["commit"]:
        raise SystemExit("CPython checkout does not match tests/upstream.json")
    dirty = subprocess.check_output(["git", "-C", str(UPSTREAM), "status", "--porcelain", "--untracked-files=no"], text=True)
    if dirty:
        raise SystemExit("CPython tracked source has modifications")
    if sys.version_info[:3] != (3, 15, 0):
        raise SystemExit("use the pinned CPython 3.15.0 build to discover and check its tests")
    import test
    if not Path(test.__file__).resolve().is_relative_to(UPSTREAM):
        raise SystemExit("oracle must load test modules from the pinned checkout")
    return pin


def static_cases(tree):
    """Candidates, not a claim that dynamic unittest discovery is complete."""
    result = []

    def walk(node, parents):
        for child in ast.iter_child_nodes(node):
            scope = parents
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                scope = parents + [child.name]
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test"):
                    result.append({"name": ".".join(scope), "line": child.lineno, "status": "unported"})
            walk(child, scope)

    walk(tree, [])
    return result


def inventory():
    tracked = subprocess.check_output(["git", "-C", str(UPSTREAM), "ls-files", "-z", "Lib/test"], text=True).split("\0")
    files = []
    for relative in filter(None, tracked):
        path = UPSTREAM / relative
        entry = {"file": relative, "sha256": digest(path), "status": "unported"}
        if path.suffix == ".py":
            try:
                with tokenize.open(path) as stream, warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    tree = ast.parse(stream.read(), filename=relative)
                entry["static_candidates"] = static_cases(tree)
                entry["dynamic_discovery_required"] = True
            except (SyntaxError, UnicodeError, ValueError) as exc:
                # The suite deliberately includes invalid source fixtures.
                entry["parse_error"] = str(exc)
        files.append(entry)
    return files


def discover_module(name):
    """Isolated workers prevent one module's imports from hiding another."""
    try:
        run = subprocess.run([sys.executable, __file__, "worker", name], capture_output=True, text=True, timeout=60)
        if run.returncode:
            return {"module": name, "status": "discovery-error", "detail": run.stderr[-2000:]}
        return json.loads(run.stdout)
    except (subprocess.TimeoutExpired, ValueError) as exc:
        return {"module": name, "status": "discovery-error", "detail": str(exc)}


def worker(name):
    loader = unittest.TestLoader()
    cases = []

    def walk(suite):
        if isinstance(suite, unittest.TestSuite):
            for test in suite:
                walk(test)
        else:
            entry = {"id": suite.id(), "status": "unported"}
            if isinstance(suite, unittest.loader._FailedTest):
                entry["status"] = "discovery-error"
            if getattr(suite, "__unittest_skip__", False):
                entry["oracle_skip"] = getattr(suite, "__unittest_skip_why__", "")
            method = getattr(suite, suite._testMethodName, None)
            if getattr(method, "__unittest_skip__", False):
                entry["oracle_skip"] = getattr(method, "__unittest_skip_why__", "")
            cases.append(entry)

    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            walk(loader.loadTestsFromName(name))
            status = "discovery-error" if loader.errors else "discovered"
        except unittest.SkipTest as exc:
            status = "oracle-skipped"
            loader.errors.append(str(exc))
        except Exception as exc:
            status = "discovery-error"
            loader.errors.append(repr(exc))
    print(json.dumps({"module": name, "status": status, "cases": cases,
                      "errors": loader.errors, "diagnostics": output.getvalue()}))


def ports(driver):
    records, groups = [], []
    for module_name in PORTS:
        module = importlib.import_module(module_name)
        with tokenize.open(module.__file__) as stream:
            tree = ast.parse(stream.read())
        strings = {node.value: node.lineno for node in ast.walk(tree)
                   if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        for test in doctest.DocTestFinder().find(module, module_name):
            if not test.examples:
                continue
            # This is the declared adaptation: host doctest supplies the
            # framework. Every example, including imports inside it, is sent
            # unchanged. Module fixtures are NOT implemented by this adapter.
            oracle = doctest.DocTestRunner()
            diagnostics = io.StringIO()
            oracle_result = oracle.run(test, out=diagnostics.write, clear_globs=False)
            line = strings.get(test.docstring, test.lineno + 1)
            groups.append({"name": test.name, "file": str(Path(test.filename).relative_to(UPSTREAM)),
                           "line": line, "oracle_attempted": oracle_result.attempted,
                           "oracle_failed": oracle_result.failed, "oracle_output": diagnostics.getvalue()})
            replies, error = run_group(driver, f"__name__ = {module_name!r}\n", test.examples, 10)
            active = iter(replies[1:] if replies else [])
            for index, example in enumerate(test.examples):
                record = {"id": f"{test.name}:{index}", "file": groups[-1]["file"],
                          "line": line + example.lineno, "source": example.source,
                          "expected": example.want, "options": example.options}
                if example.options.get(doctest.SKIP):
                    record["status"] = "skipped"
                elif error:
                    record.update(status="driver-error", detail=error)
                else:
                    reply = next(active)
                    record.update(actual=reply, status="passed" if replies[0]["ok"] and check_example(example, reply) else "failed")
                records.append(record)
    return groups, records


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "worker":
        worker(sys.argv[2])
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inventory", "discover", "doctests"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--driver", type=Path, default=ROOT / "run-cython")
    args = parser.parse_args()
    pin = verify()
    report = {"upstream": pin, "oracle": sys.version, "platform": platform.platform(),
              "complete": False, "files": inventory(),
              "limits": ["Static candidates omit generated cases; they are not a complete case count.",
                         "Discovery is platform-dependent; skipped/error modules remain unresolved.",
                         "No unittest module or subtest is yet ported by this adapter."]}
    failed = True
    if args.mode == "discover":
        from test.libregrtest.findtests import findtests
        from test.libregrtest.utils import abs_module_name
        names = [abs_module_name(name, None) for name in findtests()]
        with ThreadPoolExecutor(max_workers=4) as pool:
            report["modules"] = list(pool.map(discover_module, names))
        report["module_summary"] = dict(Counter(m["status"] for m in report["modules"]))
        report["discovered_cases"] = sum(len(m.get("cases", [])) for m in report["modules"])
    elif args.mode == "doctests":
        if not args.driver.is_file():
            raise SystemExit("build run-cython before running doctest ports")
        report["driver_sha256"] = digest(args.driver)
        report["engine_sha256"] = {name: digest(ROOT / name) for name in ("spy.c", "spy.h", "run-cython.c")}
        report["adaptation"] = "Extract all doctest groups in PORTS with upstream DocTestFinder; replace only the doctest framework, preserve every example and expected result; module unittest fixtures remain unported."
        report["groups"], report["cases"] = ports(args.driver.resolve())
        report["summary"] = dict(Counter(c["status"] for c in report["cases"]))
        failed = not report["cases"] or any(c["status"] != "passed" for c in report["cases"]) or any(g["oracle_failed"] for g in report["groups"])
    path = args.report or ROOT / f"tests/results/cpython-{args.mode}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(path), "files": len(report["files"]),
                      "summary": report.get("summary", report.get("module_summary", {})),
                      "discovered_cases": report.get("discovered_cases"), "complete": False}))
    if failed and not args.report_only:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
