"""Run unchanged pure-Python doctests from a pinned Cython checkout.

This is a language adapter, not Cython's compiled-extension test runner. It
neither removes unsupported code nor replaces upstream expected results.
"""

import argparse
import ast
from collections import Counter
import doctest
import contextlib
import io
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tokenize
import tempfile
import types
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
    def walk(node, parents):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names = parents + ([node.name] if hasattr(node, "name") else [])
            name = ".".join(names) or "<module>"
            doc = ast.get_docstring(node, clean=False)
            if doc:
                examples = doctest.DocTestParser().get_examples(doc, name)
                if examples:
                    yield name, node.body[0].lineno, examples
            parents = names
        for child in ast.iter_child_nodes(node):
            yield from walk(child, parents)
    yield from walk(tree, [])


def discover_dynamic(path):
    """Isolated oracle worker; never modifies upstream source or expectations."""
    output = io.StringIO()
    result = {"status": "discovered", "groups": []}
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        try:
            module = types.ModuleType(path.stem)
            module.__file__ = str(path)
            sys.modules[module.__name__] = module
            sys.path[:0] = [str(path.parent), str(path.parents[2])]
            with tokenize.open(path) as stream:
                source = stream.read()
            exec(compile(source, str(path), "exec"), module.__dict__)
            for test in doctest.DocTestFinder().find(module, module.__name__):
                if not test.examples:
                    continue
                name = test.name.removeprefix(module.__name__).removeprefix(".") or "<module>"
                result["groups"].append({"name": name, "line": (test.lineno or 0) + 1,
                                         "docstring": test.docstring})
        except BaseException as exc:
            result.update(status="discovery-error", detail=f"{type(exc).__name__}: {exc}")
    result["diagnostics"] = output.getvalue()
    print(json.dumps(result))


def dynamic_groups(path, timeout):
    # Module-level test code runs outside the source tree. Failed discovery
    # remains visible and cannot turn an unexamined dynamic suite into a pass.
    try:
        with tempfile.TemporaryDirectory(prefix="spy-cython-discovery-") as work:
            run = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--discover", str(path.resolve())],
                                 cwd=work, capture_output=True, text=True, timeout=timeout)
        if run.returncode:
            return {"status": "discovery-error", "detail": f"worker exit {run.returncode}: {run.stderr[-2000:]}"}
        return json.loads(run.stdout)
    except (subprocess.TimeoutExpired, ValueError) as exc:
        return {"status": "discovery-error", "detail": str(exc)}


def example_signature(examples):
    return [(e.source, e.want, e.exc_msg, e.options) for e in examples]


def frame(mode, source):
    data = source.encode("utf-8")
    return f"{mode} {len(data)}\n".encode("ascii") + data


def run_group(driver, source, examples, timeout, module_path=None):
    active = [e for e in examples if not e.options.get(doctest.SKIP)]
    request = frame("M", source) + b"".join(frame("I", e.source) for e in active)
    try:
        command = [str(driver)]
        if module_path is not None:
            paths = module_path if isinstance(module_path, (list, tuple)) else [module_path]
            for path in paths:
                command += ["--module-path", str(path)]
        result = subprocess.run(command, input=request, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "driver timeout"
    if result.returncode:
        return None, f"driver exit {result.returncode}: {result.stderr.decode('utf-8', errors='replace')[:500]}"
    if result.stderr:
        return None, f"unexpected driver diagnostics: {result.stderr.decode('utf-8', errors='replace')[:500]}"
    try:
        replies = [json.loads(line) for line in result.stdout.decode("utf-8").splitlines()]
    except (UnicodeError, ValueError) as exc:
        return None, f"invalid driver response: {exc}"
    if not replies or len(replies) != (len(active) + 1 if replies[0]["ok"] else 1):
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
    # Apply this in discovery workers too; their script directory is otherwise
    # searched before CPython's standard library.
    sys.path[:] = [entry for entry in sys.path if Path(entry).resolve() != ROOT / 'tests']
    if len(sys.argv) == 3 and sys.argv[1] == "--discover":
        discover_dynamic(Path(sys.argv[2]))
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, default=ROOT / "tests/upstream/cython")
    parser.add_argument("--driver", type=Path, default=ROOT / "run-cython")
    parser.add_argument("--report", type=Path, default=ROOT / "tests/results/cython.json")
    parser.add_argument("--select", default="*.py", help="glob within upstream tests/run (default: all .py files)")
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--dynamic", action="store_true", help="also discover runtime docstrings in isolated host processes")
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
        discovery = {"status": "not-requested"}
        if args.dynamic:
            discovery = dynamic_groups(path, args.timeout)
            known = {name: example_signature(examples) for name, line, examples in tests}
            for group in discovery.pop("groups", []):
                examples = doctest.DocTestParser().get_examples(group["docstring"], group["name"])
                if known.get(group["name"]) != example_signature(examples):
                    # Retain a differing static group as well: runtime mutation
                    # is not permission to silently remove a source test.
                    tests.append((group["name"], group["line"], examples))
        if not tests:
            files.append({"file": relative, "status": "adapter-ineligible", "reason": "no discovered doctests; unittest/build tests need another adapter", "dynamic_discovery": discovery})
            continue
        files.append({"file": relative, "status": "attempted", "groups": len(tests), "dynamic_discovery": discovery})
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
                    if not initialization["ok"]:
                        record.update(status="fail", executed=False, reason="unchanged module initialization failed", actual=initialization)
                    else:
                        reply = next(responses)
                        record.update(status="pass" if check_example(example, reply) else "fail", executed=True, actual=reply)
                records.append(record)
    counts = Counter(r["status"] for r in records)
    file_counts = Counter(f["status"] for f in files)
    report = {
        "schema": 1, "suite": "Cython upstream pure-Python doctests", "commit": pin["commit"],
        "selector": args.select, "dynamic_discovery": args.dynamic, "host_python": sys.version.split()[0],
        "host_platform": platform.platform(),
        "engine_sources": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                           for name in ("spy.c", "spy.h", "spy-unicode.h", "spy-intrinsics.h", "intrinsics.py", "host.h", "run-cython.c")},
        "driver_sha256": hashlib.sha256(args.driver.read_bytes()).hexdigest(),
        "scope": "Unchanged .py modules and upstream doctest expectations; no compiled Cython, C API/ABI, .pyx, .srctree, or unittest claim.",
        "adapter_limits": ["Runtime docstrings require --dynamic and successful oracle module initialization.",
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
    incomplete = counts["fail"] or counts["error"] or file_counts["adapter-ineligible"] or any(
        f.get("dynamic_discovery", {}).get("status") == "discovery-error" for f in files)
    return 0 if args.report_only else int(bool(incomplete))


if __name__ == "__main__":
    raise SystemExit(main())
