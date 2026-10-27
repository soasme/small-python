"""Check that every section of the Python 3.15 standard is modeled.

tests/tla/coverage.txt has one line per heading of docs/standards/3_15.md:

    <heading path> | <Model>, <Model>, ...
    <heading path> | - <why no model applies>
    <heading path> | = sections

where the heading path joins the headings from the chapter down with " > ".
A model listed formalizes that section's behavior within the model's bounds
(its .tla file says which); "-" records sections that state no behavior of
the Core profile, such as licenses, history, and host services; "= sections"
says a heading is covered by its subsections, allowed only when its own text
is at most INTRO lines and every subsection is covered. A heading repeated
under the same parent gets " (2)" and so on. This fails if a heading has no
line, a line names no heading, a model does not exist, or a line still says
TODO ("TODO: <models>" names the models planned); --allow-todo lets TODO
lines pass while models are being written, and --promote turns each into
its plan once all the models it names exist.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
STANDARD = ROOT / "docs" / "standards" / "3_15.md"
MODELS = ROOT / "tests" / "tla"
COVERAGE = MODELS / "coverage.txt"
INTRO = 10


def headings():
    """The standard's sections, in order, as [path, own text lines, subsection paths, title]."""
    sections = []
    stack = []      # (level, section) of the enclosing headings
    used = set()
    fenced = False
    for line in STANDARD.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            fenced = not fenced
        match = None if fenced else re.match(r"(#{2,6}) (.*)", line)
        if match:
            level = len(match.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            title = match.group(2).strip()
            path = " > ".join([s[3] for _, s in stack] + [title])
            name, n = path, 1
            while name in used:
                n += 1
                name = f"{path} ({n})"
            used.add(name)
            section = [name, 0, [], title]
            if stack:
                stack[-1][1][2].append(name)
            stack.append((level, section))
            sections.append(section)
        elif stack and line.strip():
            stack[-1][1][1] += 1
    return sections


def read_coverage():
    entries = {}
    if COVERAGE.exists():
        for number, line in enumerate(COVERAGE.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip() or line.startswith("#"):
                continue
            heading, sep, target = line.rpartition(" | ")
            if not sep:
                sys.exit(f"{COVERAGE}:{number}: no ' | ' separator")
            entries[heading] = target.strip()
    return entries


def models(target):
    return [m.strip() for m in target.split(",")]


def exists(model):
    return (MODELS / f"{model}.tla").exists()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--promote", action="store_true", help="map planned sections whose models all exist")
    parser.add_argument("--allow-todo", action="store_true", help="let TODO lines pass")
    args = parser.parse_args()
    sections = headings()
    paths = [s[0] for s in sections]
    entries = read_coverage()
    if args.promote:
        for p, target in entries.items():
            plan = target[len("TODO:"):].strip() if target.startswith("TODO:") else ""
            if plan and all(exists(m) for m in models(plan)):
                entries[p] = plan
        text = COVERAGE.read_text(encoding="utf-8").splitlines()
        COVERAGE.write_text("\n".join(
            line if line.startswith("#") or " | " not in line else f"{line.rpartition(' | ')[0]} | {entries[line.rpartition(' | ')[0]]}"
            for line in text) + "\n", encoding="utf-8")
    problems = []
    seen = set(paths)

    def covered(p):
        target = entries.get(p, "TODO")
        if target.startswith("TODO"):
            return False
        if target == "= sections":
            return all(covered(c) for c in children[p])
        return True

    children = {s[0]: s[2] for s in sections}
    for p, own, subsections, _ in sections:
        target = entries.get(p)
        if target is None:
            problems.append(f"no entry: {p}")
        elif target.startswith("TODO"):
            if not args.allow_todo:
                problems.append(f"TODO: {p}")
        elif target == "= sections":
            if not subsections:
                problems.append(f"'= sections' without subsections: {p}")
            elif own > INTRO:
                problems.append(f"'= sections' for {own} lines of its own text (at most {INTRO}): {p}")
            elif not args.allow_todo and not covered(p):
                problems.append(f"'= sections' with uncovered subsections: {p}")
        elif target.startswith("-"):
            if not target[1:].strip():
                problems.append(f"exclusion without a reason: {p}")
        else:
            for model in models(target):
                if not exists(model):
                    problems.append(f"no model {model}.tla: {p}")
    for p in entries:
        if p not in seen:
            problems.append(f"stale entry (no such heading): {p}")
    modeled = sum(1 for p in paths if not entries.get(p, "TODO").startswith("TODO") and entries[p][0] not in "-=")
    excluded = sum(1 for p in paths if entries.get(p, "").startswith("-"))
    grouped = sum(1 for p in paths if entries.get(p) == "= sections")
    for problem in problems[:40]:
        print(problem)
    if len(problems) > 40:
        print(f"... and {len(problems) - 40} more")
    print(f"{len(paths)} sections: {modeled} modeled, {grouped} covered by their subsections, "
          f"{excluded} excluded, {len(paths) - modeled - grouped - excluded} not covered")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
