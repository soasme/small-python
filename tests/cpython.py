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
from unittest.util import safe_repr
import warnings

from run_cython import check_example, run_group, engine_fingerprints

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "tests/upstream/cpython"
PORTS = ("test.test_unpack", "test.test_unpack_ex", "test.test_listcomps", "test.test_genexps",
         "test.test_generators", "test.test_syntax", "test.test_extcall", "test.test_metaclass")


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
            line = strings.get(test.docstring, (test.lineno or 0) + 1)
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
                elif not replies[0]["ok"]:
                    record.update(actual=replies[0], status="failed", executed=False, detail="group initialization failed")
                else:
                    reply = next(active)
                    record.update(actual=reply, executed=True, status="passed" if check_example(example, reply) else "failed")
                records.append(record)
    return groups, records


def unittest_ports(driver, modules):
    records, controls, fixtures = [], [], []
    for module_name in modules:
        module = importlib.import_module(module_name)
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        cases = []

        def flatten(tests):
            for test in tests:
                if isinstance(test, unittest.TestSuite):
                    flatten(test)
                else:
                    cases.append(test)

        flatten(suite)
        if not cases:
            raise RuntimeError(f"no unittest cases discovered in {module_name}")
        if loader.errors:
            raise RuntimeError("oracle discovery failed: " + "\n".join(loader.errors))
        oracle_subtests = []

        class Result(unittest.TextTestResult):
            def addSubTest(self, test, subtest, error):
                oracle_subtests.append({"id": test.id(), "parameters": safe_repr(dict(subtest.params)),
                                        "status": "passed" if error is None else "failed"})
                super().addSubTest(test, subtest, error)

            def addSkip(self, test, reason):
                if hasattr(test, "test_case"):
                    oracle_subtests.append({"id": test.test_case.id(), "parameters": safe_repr(dict(test.params)),
                                            "status": "skipped", "reason": reason})
                super().addSkip(test, reason)

        diagnostics = io.StringIO()
        with contextlib.redirect_stdout(diagnostics), contextlib.redirect_stderr(diagnostics):
            control = unittest.TextTestRunner(stream=diagnostics, resultclass=Result).run(suite)
        controls.append({"module": module_name, "attempted": control.testsRun,
                         "failed": len(control.failures) + len(control.errors) + len(control.unexpectedSuccesses),
                         "expected_failures": len(control.expectedFailures),
                         "skipped": len(control.skipped), "subtests": oracle_subtests, "output": diagnostics.getvalue()})
        path = Path(module.__file__)
        relative = str(path.relative_to(UPSTREAM))
        with tokenize.open(path) as stream:
            source = f"__name__ = {module_name!r}\n" + stream.read()
        source += "\nimport unittest as _spy_unittest\n"
        if hasattr(module, "setUpModule"):
            source += "setUpModule()\n"
        actions = []
        current = None

        def finish_class(cls):
            name = cls.__qualname__
            actions.append(({"phase": "tearDownClass", "class": name},
                            f"try:\n    if _spy_class_ready:\n        {name}.tearDownClass()\n"
                            f"finally:\n    {name}.doClassCleanups()\n"))

        for case in cases:
            cls = type(case)
            name = cls.__qualname__
            if cls.__module__ != module_name or "<locals>" in name:
                records.append({"id": case.id(), "file": relative, "status": "adapter-ineligible",
                                "detail": "dynamically located/imported test classes require another adapter"})
                continue
            if current is not cls:
                if current is not None:
                    finish_class(current)
                actions.append(({"phase": "setUpClass", "class": name},
                                f"_spy_class_ready = False\n{name}._class_cleanups = []\n"
                                f"_spy_unittest._class_setup({name})\n_spy_class_ready = True\n"))
                current = cls
            actions.append(({"phase": "test", "id": case.id(), "class": name},
                            f"if _spy_class_ready:\n    _spy_unittest._run_case({name}, {case._testMethodName!r})\n"))
        if current is not None:
            finish_class(current)
        if hasattr(module, "tearDownModule"):
            actions.append(({"phase": "tearDownModule"}, "tearDownModule()\n"))
        replies, error = run_group(driver, source, [doctest.Example(code, "") for metadata, code in actions],
                                   30, [ROOT / "tests/support", UPSTREAM / "Lib"])
        responses = iter(replies[1:] if replies else [])
        ready, setup = False, None
        for metadata, code in actions:
            record = dict(metadata, file=relative, source=code)
            if error:
                record.update(status="driver-error", detail=error, executed=False)
            elif not replies[0]["ok"]:
                record.update(status="failed", detail="unchanged module or module setup failed",
                              actual=replies[0], executed=False)
            else:
                reply = next(responses)
                skipped = not reply["ok"] and reply["type"] == "unittest.SkipTest"
                record.update(actual=reply, executed=True,
                              status="passed" if reply["ok"] else "skipped" if skipped else "failed")
                if metadata["phase"] == "test":
                    subtests = []
                    try:
                        for line in reply["output"].splitlines():
                            if line.startswith("@spy-subtests@"):
                                for message, params, status, kind, detail in ast.literal_eval(line[len("@spy-subtests@"):]):
                                    subtests.append({"message": message, "parameters": params, "status": status,
                                                     "exception": kind, "detail": detail})
                    except (ValueError, SyntaxError, TypeError) as exc:
                        record.update(status="driver-error", detail=f"invalid subtest results: {exc}")
                    if subtests:
                        record["subtests"] = subtests
                    expected = [subtest["status"] for subtest in oracle_subtests if subtest["id"] == metadata["id"]]
                    record["oracle_subtest_count"] = len(expected)
                    if record["status"] == "passed" and [subtest["status"] for subtest in subtests] != expected:
                        record.update(status="failed", detail="subtest results do not match oracle execution")
                if metadata["phase"] == "setUpClass":
                    ready, setup = reply["ok"], record
                elif metadata["phase"] == "test" and not ready:
                    record.update(status="skipped" if setup["status"] == "skipped" else "failed",
                                  detail="class setup failed", actual=setup["actual"], executed=False)
            (records if metadata["phase"] == "test" else fixtures).append(record)
    return controls, records, fixtures


def main():
    # Keep project test names (notably numbers.py) out of oracle imports.
    sys.path[:] = [entry for entry in sys.path if Path(entry).resolve() != ROOT / 'tests']
    if len(sys.argv) == 3 and sys.argv[1] == "worker":
        worker(sys.argv[2])
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inventory", "discover", "doctests", "unittest"))
    parser.add_argument("--module", action="append", help="complete unittest module to adapt (default: the documented passing whole-module ports)")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--driver", type=Path, default=ROOT / "run-cython")
    args = parser.parse_args()
    pin = verify()
    report = {"upstream": pin, "oracle": sys.version, "platform": platform.platform(),
              "complete": False, "files": inventory(),
              "limits": ["Static candidates omit generated cases; they are not a complete case count.",
                         "Discovery is platform-dependent; skipped/error modules remain unresolved.",
                         "Unittest coverage is limited to explicitly adapted modules; unported subtests remain obligations."]}
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
        report["engine_sha256"] = engine_fingerprints()
        report["adaptation"] = "Extract all doctest groups in PORTS with upstream DocTestFinder; replace only the doctest framework, preserve every example and expected result; module unittest fixtures remain unported."
        report["groups"], report["cases"] = ports(args.driver.resolve())
        for entry in report["files"]:
            cases = [case for case in report["cases"] if case["file"] == entry["file"]]
            if cases:
                entry["status"] = "partial-doctest-port"
                entry["doctest_summary"] = dict(Counter(case["status"] for case in cases))
        report["summary"] = dict(Counter(c["status"] for c in report["cases"]))
        failed = not report["cases"] or any(c["status"] != "passed" for c in report["cases"]) or any(g["oracle_failed"] for g in report["groups"])
    elif args.mode == "unittest":
        if not args.driver.is_file():
            raise SystemExit("build run-cython before running unittest ports")
        report["driver_sha256"] = digest(args.driver)
        report["engine_sha256"] = engine_fingerprints()
        report["framework_sha256"] = digest(ROOT / "tests/support/unittest.py")
        report["adaptation"] = "Initialize complete unchanged upstream modules; search tests/support for the unittest adaptation, then the unchanged pinned Lib tree for dependencies and fixtures; retain every discovered case ID and run module/class/test fixtures. Unsupported framework operations fail explicitly."
        report["groups"], report["cases"], report["fixtures"] = unittest_ports(
            args.driver.resolve(), args.module or ["test.test_decorators", "test.test_augassign", "test.test_int_literal",
                                                  "test.test_unary", "test.test_keywordonlyarg", "test.test_named_expressions",
                                                  "test.test_longexp", "test.test_unicode_identifiers", "test.test_exception_variations",
                                                  "test.test_typechecks", "test.test_subclassinit", "test.test_utf8source",
                                                  "test.test_binop"])
        for entry in report["files"]:
            cases = [case for case in report["cases"] if case["file"] == entry["file"]]
            if cases:
                entry["status"] = "partial-unittest-port"
                entry["unittest_summary"] = dict(Counter(case["status"] for case in cases))
        report["summary"] = dict(Counter(c["status"] for c in report["cases"]))
        failed = (not report["cases"] or any(c["status"] != "passed" for c in report["cases"])
                  or any(f["status"] != "passed" for f in report["fixtures"])
                  or any(g["failed"] or g["skipped"] for g in report["groups"]))
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
