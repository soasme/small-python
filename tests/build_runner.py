"""Run the bundler tests (tests/build) on spyc (docs/build.md 10.2).

usage: build_runner.py SPYC [--oracle PYTHON | --oracle-only PYTHON] [--only SUBSTRING]

Each test is a program, tests/build/NAME.py, with the modules it imports in
a sibling NAME.fixtures directory, and a header:

    # build: spyc options, and further entries for -c
    # bundles: the files the bundle holds, relative to the test's directory
    # negative: text of the error spyc reports      (a build that must fail)
    # oracle: skip | passes                          (optional)
    # description: what the test shows

The test is the entry; with -m MODULE it is placed at that module's path.
Phases: the oracle runs the program unbundled (with --oracle); spyc builds it
twice, from copies at different paths, which must give the same C file, a
metafile and dependency rule naming exactly the bundled files; the program
is compiled against libspy.a and runs in an empty directory. --oracle-only
checks the tests against the oracle alone, without spyc.
"""
import argparse
import json
import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests/build"
TIMEOUT = 600 if "ASAN_OPTIONS" in os.environ else 60


def metadata(path):
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            break
        key, _, value = line[1:].strip().partition(":")
        if _:
            fields[key.strip()] = value.strip()
    return fields


def options(fields):
    """The spyc options, the entries named on the command line, and the
    module run with -m, if any."""
    words, flags, entries, module = shlex.split(fields.get("build", "")), [], [], None
    takes = {"-m", "-M", "-I", "-x", "-D", "-N", "--alias"}
    while words:
        word = words.pop(0)
        if word in takes:
            flags += [word, words.pop(0)]
            if word == "-m":
                module = flags[-1]
        elif word.startswith("-"):
            flags.append(word)
        else:
            entries.append(word)
    return flags, entries, module


def stage(path, directory, module):
    fixtures = path.with_suffix(".fixtures")
    if fixtures.is_dir():
        shutil.copytree(fixtures, directory, dirs_exist_ok=True)
    entry = Path(*module.split(".")).with_suffix(".py") if module else Path(path.name)
    (directory / entry).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(path, directory / entry)
    return entry


def run(command, directory, env=None):
    base = {"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"}
    base.update({k: v for k, v in os.environ.items() if k.endswith("SAN_OPTIONS")})
    try:
        result = subprocess.run(command, cwd=directory, capture_output=True, text=True, timeout=TIMEOUT,
                                env={**base, **(env or {})})
    except subprocess.TimeoutExpired:
        return None, "timed out"
    return result.returncode, (result.stdout + result.stderr).strip()


def oracle_phase(path, fields, oracle):
    """The unbundled program on the oracle: the -I roots on PYTHONPATH, and
    -O, -OO, or -m as the build says."""
    flags, entries, module = options(fields)
    expect = fields.get("oracle", "fails" if "negative" in fields else "passes")
    with tempfile.TemporaryDirectory(prefix="build-") as temp:
        directory = Path(temp)
        entry = stage(path, directory, module)
        roots = [str(directory / flags[i + 1]) for i, flag in enumerate(flags) if flag == "-I"]
        python = [str(oracle), "-s", *(flag for flag in flags if flag in ("-O", "-OO"))]
        runs = [[*python, "-m", module]] if module else [[*python, str(entry)]]
        runs += [[*python, name] for name in entries]
        # A program the build rejects must fail on the oracle for the same reason.
        reason = fields.get("negative", "").partition("error: ")[2]
        for command in runs:
            code, output = run(command, directory, {"PYTHONPATH": os.pathsep.join(roots)} if roots else None)
            if code != 0:
                return expect == "fails" and reason in output, f"{shlex.join(command[3:])}: {output[-1500:]}"
        return expect == "passes", "the program ran" if expect == "fails" else ""


HOST = """#include "spy.h"
#include <stdio.h>
{declarations}
char *{loader}(void *, const char *);
static int output(void *p, const char *s, size_t n) {{ return fwrite(s, 1, n, p) == n ? 0 : -1; }}
static int entry(const char *source, const char *filename) {{
    SPYContext *c = spy_context_new();
    if (!c) return 1;
    spy_set_output(c, output, stdout);
    spy_set_module_loader(c, {loader}, NULL);
    int status = spy_exec(c, source, filename);
    if (status) fprintf(stderr, "%s:%zu: %s: %s\\n", spy_error_filename(c), spy_error_line(c),
                        spy_error_type(c), spy_error_display(c));
    spy_context_free(c);
    return status;
}}
int main(void) {{
    return {calls} ? 1 : 0;
}}
"""


def c_name(entry):
    return "spy_" + "".join(ch if ch.isalnum() else "_" for ch in entry.split(".")[0])


def build_phase(path, fields, spyc, cc):
    flags, entries, module = options(fields)
    negative = fields.get("negative")
    outputs = []
    with tempfile.TemporaryDirectory(prefix="build-") as temp:
        for copy in ("a", "copy b"):
            directory = Path(temp) / copy
            directory.mkdir()
            entry = stage(path, directory, module)
            command = [str(spyc), *flags, "--metafile", "meta.json", "--deps", "program.d", "-o", "program.c"]
            command += ([] if module else [str(entry)]) + entries
            code, output = run(command, directory)
            if negative:
                if code != 1 or negative not in output:
                    return False, f"expected spyc to fail with {negative!r}, got status {code}: {output[-1500:]}"
                if (directory / "program.c").exists():
                    return False, "a failed build wrote its output"
                continue
            if code != 0:
                return False, f"spyc: {output[-1500:]}"
            outputs.append((directory / "program.c").read_bytes())
        if negative:
            return True, ""
        if outputs[0] != outputs[1]:
            return False, "the output depends on the directory it was built in"
        bundles = set(fields.get("bundles", "").split())
        inputs = set(json.loads((directory / "meta.json").read_text(encoding="utf-8"))["inputs"])
        if inputs != bundles:
            return False, f"metafile inputs {sorted(inputs)}, expected {sorted(bundles)}"
        target, _, prerequisites = (directory / "program.d").read_text(encoding="utf-8").replace("\\\n", " ").partition(":")
        if target.strip() != "program.c" or set(prerequisites.split()) != bundles:
            return False, f"dependency rule {target}:{prerequisites.strip()}, expected {sorted(bundles)}"

        # The program runs from an empty directory, with no source to fall back on.
        sources = [directory / "program.c"]
        if "-c" in flags:
            names = [module] if module else [path.name] + entries
            loader = (flags[flags.index("-N") + 1] if "-N" in flags else c_name(names[0])) + "_load"
            host = directory / "host.c"
            host.write_text(HOST.format(
                declarations="\n".join(f"extern const char {c_name(name)}[];" for name in names), loader=loader,
                calls=" || ".join(f'entry({c_name(name)}, "{name}")' for name in names)), encoding="utf-8")
            sources.append(host)
        libraries = [str(ROOT / "libspy-std.a")] if "-M" in flags else []
        binary = Path(temp) / "program"
        code, output = run([*cc, "-std=c11", "-O0", "-I", str(ROOT), *map(str, sources), *libraries,
                            str(ROOT / "libspy.a"), "-lm", "-o", str(binary)], directory)
        if code != 0:
            return False, f"cc: {output[-1500:]}"
        empty = Path(temp) / "empty"
        empty.mkdir()
        code, output = run([str(binary)], empty)
        return code == 0, output[-1500:]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("spyc", type=Path)
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--oracle-only", type=Path)
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    oracle = args.oracle_only or args.oracle
    cc = shlex.split(os.environ.get("CC", "cc"))
    tests = [path for path in sorted(TESTS.glob("*.py")) if args.only in path.stem]
    if not tests:
        raise SystemExit(f"no build tests in {TESTS}")
    if not args.oracle_only and not (ROOT / "libspy.a").exists():
        raise SystemExit("libspy.a not found; run make")
    failures = skipped = 0
    for path in tests:
        fields = metadata(path)
        results = []
        if oracle and fields.get("oracle") != "skip":
            ok, detail = oracle_phase(path, fields, oracle.resolve())
            results.append(("oracle", ok, detail))
        if not args.oracle_only:
            ok, detail = build_phase(path, fields, args.spyc.resolve(), cc)
            results.append(("bundle", ok, detail))
        failed = [(label, detail) for label, ok, detail in results if not ok]
        failures += bool(failed)
        skipped += not results
        print(f"{path.stem}: " + (", ".join(f"{label} {'passed' if ok else 'FAILED'}" for label, ok, _ in results) or "skipped"))
        for label, detail in failed:
            print("    " + f"{label}: {detail}".replace("\n", "\n    "))
    print(f"{len(tests) - failures - skipped} of {len(tests)} build tests passed, {skipped} skipped, {failures} failed")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
