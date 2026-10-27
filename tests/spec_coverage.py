"""Report which clauses of PLS-315 the specification tests (tests/spec) cover.

usage: spec_coverage.py [--missing]

Every test names the clauses it exercises on its "# spec: PLS-315 ..." line.
Each name must be a clause of docs/standards/3_15.md. A test of a subclause
covers the enclosing clause too, so the report counts the clauses X.Y of the
normative chapters (6 to 29 and Annexes A and B) that some test reaches.
With --missing it lists the clauses no test reaches. It fails when some
clause has no test.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "tests/spec"
STANDARD = ROOT / "docs/standards/3_15.md"


def clauses():
    text = STANDARD.read_text(encoding="utf-8")
    return re.findall(r"^#{2,5} ((?:\d+|[A-E])(?:\.\d+)*)\b(.*)$", text, re.M)


def normative(number):
    head = number.split(".")[0]
    return head in ("A", "B") or (head.isdigit() and 6 <= int(head) <= 29)


def main():
    headings = dict(clauses())
    covered, errors = {}, []
    for path in sorted(SPEC.rglob("*.py")):
        if path.name == "harness.py" or ".fixtures" in str(path.parent):
            continue
        name = str(path.relative_to(SPEC))
        line = next((l for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("# spec:")), "")
        match = re.fullmatch(r"# spec: PLS-315 (.+)", line)
        if not match:
            errors.append(f"{name}: no '# spec: PLS-315 ...' line")
            continue
        for ref in match.group(1).split(", "):
            if ref not in headings:
                errors.append(f"{name}: no clause {ref}")
            parts = ref.split(".")
            for depth in range(1, len(parts) + 1):
                covered.setdefault(".".join(parts[:depth]), []).append(name)
    if errors:
        sys.exit("\n".join(errors))
    targets = [number for number in headings if normative(number) and number.count(".") == 1]
    missing = [number for number in targets if number not in covered]
    if "--missing" in sys.argv[1:]:
        for number in missing:
            print(f"{number}{headings[number]}")
    print(f"Spec coverage: {len(targets) - len(missing)}/{len(targets)} clauses of PLS-315 chapters 6-29 "
          f"and Annexes A-B have a test")
    if missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
