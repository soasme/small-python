"""Model-check the TLA+ specifications in tests/tla and replay them on Python.

usage: tla_check.py ENGINE [--oracle PYTHON] [--java JAVA] [--jar TLA2TOOLS] [--only NAME]

Each NAME.tla has a NAME.cfg naming its invariants and properties; TLC checks
them over the model's whole state space. A model with a NAME.replay.py also
gets conformance-tested: TLC's state graph is dumped, and for every
transition a case is built from the shortest path that reaches its source
state followed by the transition itself. The cases are inserted into the
replay script, which performs each step on real Python objects and compares
what happens with the model's state. The pinned CPython oracle must pass
every case, which validates the model against the reference implementation;
the engine must pass them to conform to it.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TLA = ROOT / "tests/tla"
ORACLE = ROOT / "tests/upstream/cpython-build/python.exe"
JAR = ROOT / ".obj/tla/tla2tools.jar"
MARKER = "CASES = \"\"  # filled in by tests/tla_check.py, with walks() and states()\n"
# Inserted after the cases: the walks and their states, decoded as needed.
PRELUDE = '''

def walks():
    """The walks, one at a time: CASES holds them all, a blank line apart."""
    start = 0
    while start < len(CASES):
        end = CASES.find("\\n\\n", start)
        end = len(CASES) if end < 0 else end
        yield CASES[start:end]
        start = end + 2


def states(walk):
    """The states of a walk, decoded one line at a time."""
    start = 0
    while start < len(walk):
        end = walk.find("\\n", start)
        end = len(walk) if end < 0 else end
        yield eval(walk[start:end])
        start = end + 1


def check_programs(outcome, field="outcome"):
    """Replays a model whose one step computes a program's outcome: compares
    outcome(program) with the model's for every program, and reports."""
    failures = count = 0
    for walk in walks():
        count += 1
        steps = states(walk)
        program = next(steps)["program"]
        for state in steps:
            actual = outcome(program)
            if actual != state[field]:
                failures += 1
                if failures <= 20:
                    print("MISMATCH", program, "expected", state[field], "got", actual)
    if failures:
        print(failures, "mismatches")
    else:
        print("replayed", count, "cases")
'''



class Values:
    """A parser for the TLA+ values TLC prints in its state dumps."""

    ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "f": "\f"}
    TOKEN = re.compile(r'\s*(?:(<<|>>|\|->|:>|@@|[\[\]{}(),])|("(?:[^"\\]|\\.)*")|(-?\d+)|(TRUE|FALSE)|([A-Za-z_]\w*))')

    def __init__(self, text):
        self.tokens = []
        position = 0
        text = text.strip()
        while position < len(text):
            match = self.TOKEN.match(text, position)
            if not match:
                raise ValueError(f"cannot parse TLA+ value at {text[position:position + 30]!r}")
            self.tokens.append(match.groups())
            position = match.end()
        self.index = 0

    def peek(self):
        return self.tokens[self.index][0] if self.index < len(self.tokens) else None

    def take(self, symbol=None):
        token = self.tokens[self.index]
        if symbol is not None and token[0] != symbol:
            raise ValueError(f"expected {symbol}, found {token}")
        self.index += 1
        return token

    def value(self):
        symbol, string, number, boolean, name = self.take()
        if string is not None:
            return re.sub(r"\\(.)", lambda m: self.ESCAPES.get(m.group(1), m.group(1)), string[1:-1])
        if number is not None:
            return int(number)
        if boolean is not None:
            return boolean == "TRUE"
        if name is not None:
            return name
        if symbol == "<<":
            return tuple(self.items(">>"))
        if symbol == "{":
            return frozenset(self.items("}"))
        if symbol == "[":
            record = {}
            while self.peek() != "]":
                key = self.take()[4]
                self.take("|->")
                record[key] = self.value()
                if self.peek() == ",":
                    self.take(",")
            self.take("]")
            return record
        if symbol == "(":
            mapping = {}
            while True:
                key = self.value()
                self.take(":>")
                mapping[key] = self.value()
                if self.peek() != "@@":
                    break
                self.take("@@")
            self.take(")")
            return mapping
        raise ValueError(f"unexpected token {symbol}")

    def items(self, closing):
        items = []
        while self.peek() != closing:
            items.append(self.value())
            if self.peek() == ",":
                self.take(",")
        self.take(closing)
        return items


def parse_state(label):
    """A state from its dump label: one `/\\ name = value` conjunct per
    variable, where a long value continues on the following lines."""
    state = {}
    for conjunct in re.split(r"^/\\ ", label.strip(), flags=re.M):
        if conjunct.strip():
            name, _, text = conjunct.partition(" = ")
            state[name.strip()] = Values(text).value()
    return state


def parse_graph(path):
    nodes, edges, initial = {}, {}, []
    node = re.compile(r'^(-?\d+) \[label="(.*)"(,style = filled)?\];?$')
    edge = re.compile(r'^(-?\d+) -> (-?\d+)')
    for line in path.read_text(encoding="utf-8").splitlines():
        match = node.match(line)
        if match:
            # Dot escapes each backslash and quote, and breaks lines with \n.
            label = re.sub(r"\\(.)", lambda m: "\n" if m.group(1) == "n" else m.group(1), match.group(2))
            nodes[match.group(1)] = parse_state(label)
            if match.group(3):
                initial.append(match.group(1))
            continue
        match = edge.match(line)
        if match:
            edges.setdefault(match.group(1), []).append(match.group(2))
    return nodes, edges, initial


def cases(nodes, edges, initial, nearby=2000):
    """Walks from the initial states that together take every transition.

    A walk keeps taking untaken transitions; where its state has none left,
    it moves along the shortest path to a state that has, if one is among
    the nearest `nearby` states. Otherwise the next walk starts with the
    shortest path from an initial state to such a state.
    """
    parent = {start: None for start in initial}
    order = deque(initial)
    reached = []
    while order:
        node = order.popleft()
        reached.append(node)
        for target in edges.get(node, ()):
            if target not in parent:
                parent[target] = node
                order.append(target)
    untaken = {node: list(edges.get(node, ())) for node in reached}

    def near(start):
        previous, queue = {start: None}, deque([start])
        while queue and len(previous) < nearby:
            node = queue.popleft()
            for target in edges.get(node, ()):
                if target in previous:
                    continue
                previous[target] = node
                if untaken[target]:
                    route = [target]
                    while previous[route[-1]] != start:
                        route.append(previous[route[-1]])
                    return route[::-1]
                queue.append(target)
        return None

    walks = []
    for node in reversed(reached):     # deepest first, so prefixes take transitions too
        while untaken[node]:
            walk = [node]
            while parent[walk[-1]] is not None:
                walk.append(parent[walk[-1]])
            walk.reverse()
            for source, target in zip(walk, walk[1:]):
                if target in untaken[source]:
                    untaken[source].remove(target)
            current = node
            while True:
                if untaken[current]:
                    current = untaken[current].pop()
                    walk.append(current)
                    continue
                route = near(current)
                if route is None:
                    break
                for source, target in zip([current] + route, route):
                    if target in untaken[source]:
                        untaken[source].remove(target)
                walk += route
                current = route[-1]
            walks.append([nodes[n] for n in walk])
    return walks


def model_check(name, java, jar, directory, dump):
    command = [java, "-XX:+UseParallelGC", "-cp", str(jar), "tlc2.TLC", "-nowarning", "-workers", "auto",
               "-metadir", str(Path(directory) / "states"), "-config", str(TLA / f"{name}.cfg")]
    if dump:
        command += ["-dump", "dot,actionlabels", str(Path(directory) / name)]
    command.append(str(TLA / f"{name}.tla"))
    result = subprocess.run(command, cwd=TLA, capture_output=True, text=True)
    output = result.stdout + result.stderr
    summary = re.search(r"(\d+) states generated, (\d+) distinct states found", output)
    passed = result.returncode == 0 and "No error has been found" in output
    return passed, output, summary.group(2) if summary else "?"


def replay(name, all_cases, engine, oracle, directory):
    template = (TLA / f"{name}.replay.py").read_text(encoding="utf-8")
    if template.count(MARKER) != 1:
        raise SystemExit(f"{name}.replay.py must contain the line {MARKER.strip()!r}")
    script = Path(directory) / f"{name}_replay.py"
    # All walks are one string, a state per line and a blank line between
    # walks, which the script decodes as it goes, so the cases do not crowd
    # the heap its collections scan. The script's FIELDS line names the
    # state variables it reads.
    fields = re.search(r"^FIELDS = (\(.*\))$", template, re.M)
    fields = eval(fields.group(1)) if fields else None
    walks = ["\n".join(repr({k: v for k, v in state.items() if fields is None or k in fields}) for state in walk)
             for walk in all_cases]
    walks = [walk + "\n" for walk in walks[:-1]] + walks[-1:]
    script.write_text(template.replace(MARKER, f"CASES = {chr(10).join(walks)!r}\n" + PRELUDE), encoding="utf-8")
    outcomes = {}
    # PEP 765's warnings about return, break, and continue in finally go to
    # stderr; the programs use those on purpose.
    for label, command in (("oracle", [str(oracle), "-E", "-s", "-W", "ignore::SyntaxWarning", script.name]),
                           ("engine", [str(engine), script.name])):
        result = subprocess.run(command, cwd=directory, capture_output=True, text=True, timeout=600,
                                env={"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"})
        output = result.stdout.strip()
        expected = f"replayed {len(all_cases)} cases"
        passed = result.returncode == 0 and output.endswith(expected)
        outcomes[label] = (passed, (output + "\n" + result.stderr[-2000:]).strip())
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("engine", type=Path)
    parser.add_argument("--oracle", type=Path, default=ORACLE)
    parser.add_argument("--java", default=os.environ.get("JAVA", shutil.which("java") or "java"))
    parser.add_argument("--jar", type=Path, default=JAR)
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    args.engine = args.engine.resolve()
    if not args.jar.exists():
        raise SystemExit(f"{args.jar} not found; run `make tla-tools`")
    failures = 0
    for spec in sorted(TLA.glob("*.tla")):
        name = spec.stem
        if args.only and args.only not in name:
            continue
        has_replay = (TLA / f"{name}.replay.py").exists()
        with tempfile.TemporaryDirectory(prefix="tla-") as directory:
            passed, output, states = model_check(name, args.java, args.jar, directory, has_replay)
            if not passed:
                failures += 1
                print(f"{name}: model check FAILED\n{output[-4000:]}")
                continue
            line = f"{name}: model checked, {states} distinct states"
            if has_replay:
                nodes, edges, initial = parse_graph(Path(directory) / f"{name}.dot")
                all_cases = cases(nodes, edges, initial)
                edge_list = [(source, target) for source in edges for target in edges[source]]
                outcomes = replay(name, all_cases, args.engine, args.oracle, directory)
                line += f"; {len(edge_list)} transitions replayed in {len(all_cases)} walks: oracle {'passed' if outcomes['oracle'][0] else 'FAILED'}, " \
                        f"{args.engine.name} {'passed' if outcomes['engine'][0] else 'FAILED'}"
                for label, (ok, text) in outcomes.items():
                    if not ok:
                        failures += 1
                        line += f"\n  {label} output:\n    " + "\n    ".join(text.splitlines()[:20])
            print(line)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
