"""Test jsonify and the json module it links (make test).

probe.py must print the same as a program spyc built and under the Python
running this script; jsonify must print what json.dumps(indent=2) prints,
in color, and fail with a message for a bad command line, file or document.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(*command, cwd=HERE):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=60)


expected, actual = run(sys.executable, "probe.py"), run("./probe")
assert expected.returncode == 0 and actual.returncode == 0, (expected.stderr, actual.stderr)
if expected.stdout != actual.stdout:
    for line, (want, got) in enumerate(zip(expected.stdout.splitlines(), actual.stdout.splitlines()), 1):
        if want != got:
            print(f"probe.py line {line}:\n  CPython {want}\n  spy     {got}")
    raise SystemExit("json differs from CPython")
print(f"json: {len(expected.stdout.splitlines())} probes match CPython")

DOCUMENT = '{"name": "caf\\u00e9 \\u2603", "list": [1, 2.5, -3e+20, 123456789012345678901234567890],' \
           ' "nested": {"t": true, "f": false, "n": null, "empty": [], "none": {}}, "s": "a \\"q\\"\\n"}'
with tempfile.TemporaryDirectory(prefix="jsonify ") as temp:
    directory = Path(temp)
    (directory / "data file.json").write_text(DOCUMENT, encoding="utf-8")
    result = run(str(HERE / "jsonify"), "data file.json", cwd=directory)
    assert result.returncode == 0, result
    plain = re.sub("\033\\[[0-9;]*m", "", result.stdout)
    assert plain == json.dumps(json.loads(DOCUMENT), indent=2, ensure_ascii=False) + "\n", plain
    assert '\033[1;34m"name"\033[0m: \033[32m"café ☃"\033[0m' in result.stdout, result.stdout
    assert "\033[36m2.5\033[0m" in result.stdout and "\033[35mnull\033[0m" in result.stdout, result.stdout
    # A relative path above the working directory is outside what the program may open.
    (directory / "bad.json").write_text("[1, 2", encoding="utf-8")
    for args, error in (([], "usage: jsonify FILE"), (["a", "b"], "usage: jsonify FILE"),
                        (["missing.json"], "FileNotFoundError"), (["bad.json"], "ValueError: EOF while parsing"),
                        (["../outside.json"], "Error")):
        result = run(str(HERE / "jsonify"), *args, cwd=directory)
        assert result.returncode == 1 and error in result.stderr and not result.stdout, (args, result)
print("jsonify passed")

# Where the module departs from CPython's json, on purpose (README.md).
LIMITS = r"""import json
def kind(function, *args, **kwargs):
    try:
        function(*args, **kwargs)
        return "ok"
    except Exception as error:
        return type(error).__name__ + ": " + str(error)
deep = []
for _ in range(999):
    deep = [deep]
print(kind(json.dumps, deep), kind(json.dumps, [deep]))
print(kind(json.loads, "[" * 1000 + "]" * 1000), kind(json.loads, "[" * 1001 + "]" * 1001))
# Brackets inside a string, after an escaped quote too, are not nesting.
print(kind(json.loads, '"\\"' + "[" * 1001 + '"'), kind(json.loads, "NaN"))
print(kind(json.dumps, "\udcff"), kind(json.loads, '"\\udcff"'), kind(json.dumps, 1, sort_keys=True))
"""
with tempfile.TemporaryDirectory(prefix="jsonify ") as temp:
    directory = Path(temp)
    (directory / "limits.py").write_text(LIMITS, encoding="utf-8")
    subprocess.run([str(HERE / "../../bin/spyc"), "-o", "limits", "limits.py", str(HERE / "target/release/libjson.a"),
                    "--", *sys.argv[1:]], cwd=directory, check=True)
    result = run("./limits", cwd=directory)
    assert result.stdout.splitlines() == [
        "ok RecursionError: maximum recursion depth exceeded while encoding a JSON object",
        "ok RecursionError: maximum recursion depth exceeded while decoding a JSON document",
        "ok ValueError: expected value at line 1 column 1",
        "ValueError: surrogates not allowed ValueError: lone leading surrogate in hex escape at line 1 column 7 "
        "TypeError: dumps() got an unexpected keyword argument 'sort_keys'"], result
print("json limits passed")
