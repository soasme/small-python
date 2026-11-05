"""What the json module does with many values, one line each. test.py runs
it under CPython and as a program spyc built with libjson.a; the two must
print the same. Errors print only their kind: messages are serde_json's."""

import json


class Sink:
    def __init__(self):
        self.parts = []

    def write(self, text):
        self.parts.append(text)


class Source:
    def read(self):
        return '{"read": [1, 2]}'


def show(function, *args, **kwargs):
    try:
        print(repr(function(*args, **kwargs)))
    except Exception as error:
        print(next(kind for kind in (TypeError, ValueError, RecursionError, Exception) if isinstance(error, kind)).__name__)


big = 2 ** 100
nested = {"name": "Small Python", "tags": ["c11", "embeddable"], "size": 1.5, "empty": {}, "none": [],
          "flags": {"fast": True, "slow": False, "unknown": None}, "deep": [[1, [2, {"three": 3}]], []]}
values = [None, True, False, 0, -7, big, -big, 0.1, -0.0, 1e16, 1.5e-7, 2.5, "", "plain", "quote \" back \\",
          "tab\t new\n ctrl\x01 del\x7f", "café", "snow ☃", "emoji 😀", [], {}, [1, "two", None], (1, 2),
          {"b": 1, "a": 2}, {1: "int", 2.5: "float", True: "bool", None: "none"}, nested]
for value in values:
    show(json.dumps, value)
    show(json.dumps, value, indent=2)
    show(json.dumps, value, ensure_ascii=False)
show(json.dumps, nested, indent=0)
show(json.dumps, nested, indent="\t")
show(json.dumps, nested, indent=None)

texts = ["null", "true", "false", "0", "-0", "42", "-42", "123456789012345678901234567890", "1.0", "-0.0",
         "2.5E-3", '"\\u00e9\\ud83d\\ude00\\n"', '"café"', "[]", "{}", '[1, [2, [3]]]',
         '{"z": 1, "a": {"y": [true, null]}}', '{"k": 1, "k": 2, "j": 3}', '  [1 , 2]  ', b'{"bytes": 1}']
for text in texts:
    show(json.loads, text)
    show(lambda t: json.loads(json.dumps(json.loads(t))), text)

# Out of a float's range: loads gives an infinity, which dumps writes as
# Infinity, a token loads does not read (README.md).
show(json.loads, "[1e400, -1e400]")
for bad in ["", "[", "[1,]", "{1: 2}", "nul", "1 2", '"unterminated', 7]:
    show(json.loads, bad)
cycle = []
cycle.append(cycle)
for number in [float("inf"), -float("inf"), float("nan")]:
    show(json.dumps, [number, {number: 1}])
    show(json.dumps, number, allow_nan=False)
    show(json.dumps, {number: 1}, allow_nan=False)
for bad in [{(1, 2): 3}, {1, 2}, object(), cycle, [1, cycle]]:
    show(json.dumps, bad)
deep = []
for _ in range(900):
    deep = [deep]
show(lambda: json.loads(json.dumps(deep)) == deep)

sink = Sink()
show(json.dump, nested, sink, indent=2)
print(repr("".join(sink.parts)))
show(json.load, Source())
