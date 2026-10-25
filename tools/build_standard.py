"""Assemble a single-file language reference from pinned, licensed CPython docs.

Optional documentation tools only: pypandoc-binary==1.17, Pygments==2.19.2.
No package here is linked into the engine or needed to read the generated file.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import textwrap

import pypandoc

ROOT = Path(__file__).resolve().parent.parent
MARKER = "<!-- BEGIN PINNED PYTHON 3.15 REFERENCE -->"
CHAPTERS = [
    ("Language reference introduction and notation", "reference/introduction.rst"),
    ("Lexical analysis", "reference/lexical_analysis.rst"),
    ("Data model", "reference/datamodel.rst"),
    ("Execution model", "reference/executionmodel.rst"),
    ("Import system", "reference/import.rst"),
    ("Expressions", "reference/expressions.rst"),
    ("Simple statements", "reference/simple_stmts.rst"),
    ("Compound statements", "reference/compound_stmts.rst"),
    ("Top-level components", "reference/toplevel_components.rst"),
    ("Complete grammar", "reference/grammar.rst"),
    ("Built-in types", "builtins/stdtypes.rst"),
    ("Built-in constants", "builtins/constants.rst"),
    ("Built-in functions", "builtins/functions.rst"),
    ("Built-in exceptions", "builtins/exceptions.rst"),
    ("Formatting protocols and optional string helpers", "library/string.rst"),
    ("Template string objects", "library/string.templatelib.rst"),
    ("Annotation objects and evaluation", "library/annotationlib.rst"),
    ("Intrinsic types and optional type helpers", "library/types.rst"),
    ("Glossary", "glossary.rst"),
    ("Copyright", "copyright.rst"),
    ("History and licenses", "license.rst"),
]


def public_grammar(checkout):
    # Use the very same filtering lexer as CPython's published grammar. This
    # removes C actions and diagnostic-only productions without hand-editing it.
    path = checkout / "Doc/tools/extensions/lexers/peg_lexer.py"
    spec = importlib.util.spec_from_file_location("python315_peg_lexer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    grammar = (checkout / "Grammar/python.gram").read_text()
    text = "".join(value for _, value in module.PEGLexer().get_tokens(grammar))
    if "_PyAST" in text or "@trailer" in text:
        raise ValueError("grammar filtering left implementation actions")
    return text


def prepare(path, checkout, manifest):
    source = path.read_text()
    manifest[str(path.relative_to(checkout))] = hashlib.sha256(path.read_bytes()).hexdigest()
    # Sphinx accepts adjacent explicit targets and directives; plain reST
    # interprets the directive as the target URL unless separated by a blank.
    source = re.sub(r"^(\s*\.\. _[^\n:]+:)\n(?=\S)", r"\1\n\n", source, flags=re.M)
    lines = source.splitlines()
    out, i = [], 0
    while i < len(lines):
        target = re.match(r"^(\s*)\.\. _([^\n:]+):\s*$", lines[i])
        if target:
            indent, name = target.groups()
            out.extend(["", indent + ".. raw:: html", "", indent + f'   <a id="{name}"></a>',
                        "", indent + f".. _{name}: #{name}", ""])
            i += 1; continue
        match = re.match(r"^(\s*)\.\. ([\w-]+)::(.*)$", lines[i])
        if not match:
            out.append(lines[i]); i += 1; continue
        indent, kind, argument = match.groups()
        argument = argument.strip()
        j = i + 1
        while j < len(lines) and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip()) > len(indent)):
            j += 1
        body = textwrap.dedent("\n".join(lines[i + 1:j]))
        # These are presentation/index directives, not language descriptions.
        if kind in {"index", "highlight", "toctree"}:
            i = j; continue
        if kind == "literalinclude":
            target = (path.parent / argument).resolve()
            if not target.is_relative_to(checkout.resolve()):
                raise ValueError(f"include outside pinned checkout: {target}")
            manifest[str(target.relative_to(checkout))] = hashlib.sha256(target.read_bytes()).hexdigest()
            content = public_grammar(checkout) if target.name == "python.gram" else target.read_text()
            out.extend([indent + ".. code-block:: text", "", textwrap.indent(content, indent + "   "), ""])
            i = j; continue
        if kind in {"grammar-snippet", "productionlist"}:
            content = re.sub(r"^\s*:[\w-]+:.*\n?", "", body, flags=re.M).strip()
            out.extend([indent + ".. code-block:: text", "", textwrap.indent(content, indent + "   "), ""])
            i = j; continue
        if kind in {"doctest", "testcode"}:
            # Sphinx options control the test harness, not the example text.
            content = re.sub(r"^\s*:[\w-]+:.*\n?", "", body, flags=re.M).strip()
            out.extend([indent + ".. code-block:: pycon", "", textwrap.indent(content, indent + "   "), ""])
            i = j; continue
        if kind in {"class", "function", "method", "classmethod", "staticmethod", "attribute", "exception", "data", "decorator", "awaitablefunction", "describe"}:
            # 'class' is a presentation directive in standard reST. Passing a
            # Sphinx class signature through it would silently discard the name.
            signatures = [argument]
            k = i + 1
            while k < j and lines[k].strip() and not lines[k].lstrip().startswith(":"):
                signatures.append(lines[k].strip()); k += 1
            while k < j and (not lines[k].strip() or re.match(r"\s*:(noindex|no-index|canonical):", lines[k])):
                k += 1
            out.extend(["", indent + ".. code-block:: text", "", textwrap.indent("\n".join(signatures), indent + "   "), ""])
            remaining = textwrap.dedent("\n".join(lines[k:j])).splitlines()
            lines[i:j] = [indent + line if line else "" for line in remaining] + [""]
            continue
        if kind in {"versionadded", "versionchanged", "deprecated", "deprecated-removed", "impl-detail", "audit-event"}:
            title = {"versionadded": "Added in", "versionchanged": "Changed in", "deprecated": "Deprecated in",
                     "deprecated-removed": "Deprecation/removal", "impl-detail": "CPython implementation detail (informative)",
                     "audit-event": "Host audit event"}[kind]
            out.extend([indent + f".. admonition:: {title} {argument}".rstrip(), ""])
            i += 1; continue
        out.append(lines[i]); i += 1
    # Pandoc preserves arbitrary directives as divs, including their signatures
    # and nested contents. Standard Sphinx roles become readable code spans.
    return "\n".join(out) + "\n"


class Blocks(list):
    """A replacement for one block, spliced into its parent's block list."""


def rewrite(node, labels):
    if isinstance(node, list):
        items = []
        for child in node:
            child = rewrite(child, labels)
            if isinstance(child, Blocks):
                items.extend(child)
            else:
                items.append(child)
        return items
    if not isinstance(node, dict):
        return node
    if node.get("t") == "Div":
        (identifier, _, _), children = node["c"]
        result = Blocks()
        if identifier and identifier not in labels:
            result.append({"t": "RawBlock", "c": ["html", f'<a id="{identifier}"></a>']})
        result.extend(rewrite(children, labels))
        return result
    if node.get("t") == "Code":
        attrs, text = node["c"]
        role = dict(attrs[2]).get("role")
        if role:
            text = " ".join(text.split())
            explicit = re.match(r"(.+) <([^>]+)>$", text)
            display, target = explicit.groups() if explicit else (text.lstrip("~!"), text.lstrip("~!"))
            if role == "ref" and target in labels:
                return {"t": "Link", "c": [["", [], []], [{"t": "Str", "c": display}], ["#" + target, ""]]}
            if role == "pep" and target.isdigit():
                return {"t": "Link", "c": [["", [], []], [{"t": "Str", "c": "PEP " + target}], [f"https://peps.python.org/pep-{int(target):04d}/", ""]]}
            return {"t": "Code", "c": [["", [], []], display]}
    if node.get("t") == "Header":
        level, (identifier, classes, attrs), content = node["c"]
        result = Blocks()
        if identifier and identifier not in labels:
            result.append({"t": "RawBlock", "c": ["html", f'<a id="{identifier}"></a>']})
        result.append({"t": "Header", "c": [min(6, level + 2), ["", classes, attrs], rewrite(content, labels)]})
        return result
    result = {key: rewrite(value, labels) for key, value in node.items()}
    return result


def convert(source, labels):
    tree = json.loads(pypandoc.convert_text(source, "json", format="rst"))
    tree = rewrite(tree, labels)
    result = pypandoc.convert_text(json.dumps(tree), "gfm", format="json", extra_args=["--wrap=none"])
    return re.sub(r"\n{4,}", "\n\n\n", result).strip() + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    checkout = ROOT / "tests/upstream/cpython"
    pin = json.loads((ROOT / "tests/upstream.json").read_text())["cpython"]
    actual = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if actual != pin["commit"]:
        raise SystemExit("wrong CPython checkout; run make upstream")
    if subprocess.check_output(["git", "-C", str(checkout), "diff", "--name-only", "HEAD"], text=True):
        raise SystemExit("modified upstream source cannot define a pinned edition")
    target = ROOT / "docs/standards/3_15.md"
    front = target.read_text().split(MARKER)[0].rstrip() + "\n\n" + MARKER + "\n\n"
    output = [front, "## Reference chapter contents\n\n"]
    for number, (title, _) in enumerate(CHAPTERS, 1):
        output.append(f"{number}. [{title}](#slp315-chapter-{number})\n")
    manifest = {}
    labels = set()
    for _, relative in CHAPTERS:
        labels.update(re.findall(r"^\s*\.\. _([^\n:]+):\s*$", (checkout / "Doc" / relative).read_text(), flags=re.M))
    for number, (title, relative) in enumerate(CHAPTERS, 1):
        path = checkout / "Doc" / relative
        output.append(f'\n<a id="slp315-chapter-{number}"></a>\n\n## {number}. {title}\n\n')
        output.append(f"Source: `Doc/{relative}` at `{pin['commit']}`.\n\n")
        chapter = convert(prepare(path, checkout, manifest), labels)
        # Each source page numbers its own footnotes. Preserve their scope when
        # all pages are combined into one Markdown document.
        chapter = re.sub(r"\[\^(\d+)\]", rf"[^ch{number}-\1]", chapter)
        for signature in re.findall(r"^\s*\.\. (?:class|function|method|classmethod|staticmethod|attribute|exception|data|decorator|awaitablefunction|describe)::\s*(.+)$", path.read_text(), flags=re.M):
            if signature.strip() not in chapter:
                raise ValueError(f"conversion lost signature in {relative}: {signature}")
        output.append(chapter)
    license_path = checkout / "LICENSE"
    manifest["LICENSE"] = hashlib.sha256(license_path.read_bytes()).hexdigest()
    output.append("\n## A. Complete upstream license notice\n\n```text\n" + license_path.read_text() + "\n```\n")
    output.append("\n## B. Source integrity manifest\n\n")
    output.append("Presentation conversion: pypandoc-binary 1.17; Pygments 2.19.2.\n\n")
    output.append("The chapters above are derived from PSF-licensed Python documentation. Changes are consolidation, Markdown conversion, added profile clauses, and removal of indexing-only metadata. Copyright and full license terms are retained above.\n\n")
    output.append("| Source file | SHA-256 |\n| --- | --- |\n")
    for path, sha in sorted(manifest.items()):
        output.append(f"| `{path}` | `{sha}` |\n")
    text = "".join(output)
    if args.check:
        if text != target.read_text():
            raise SystemExit("standard is not reproducible; regenerate and inspect the change")
        print("SLP-315 generated reference matches pinned sources")
    else:
        target.write_text(text)
        print(f"Wrote {target.relative_to(ROOT)}: {len(text):,} characters, {len(manifest)} pinned sources")


if __name__ == "__main__":
    main()
