#!/usr/bin/env python3
"""Check the public C API in spy.h and generate its reference.

    tools/api.py                  write docs/api.md from spy.h
    tools/api.py --check LIB      check that every declaration is documented,
                                  docs/api.md is current, LIB exports exactly
                                  the declared functions, and spy.h stays
                                  compatible with the last release

Compatibility compiles the release's declarations against the current
header, so the compiler, not this script, judges each signature.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "docs/api.md"
TOKEN = re.compile(r"/\*.*?\*/|#[^\n]*|[^;/#]*(?:/(?!\*)[^;/#]*)*;", re.S)


def comment_text(comment):
    lines = [re.sub(r"^\s*\*? ?", "", line) for line in comment[2:-2].splitlines()]
    return " ".join(line.strip() for line in lines if line.strip())


def parse(header):
    """Sections of (title, [(text, [declaration])]). A comment documents the
    declarations that follow it up to a blank line; a section's own comment
    is the text of its first block. Declarations before the first section
    fall in an untitled one."""
    sections, block, previous = [("", [])], None, 0
    for match in TOKEN.finditer(header):
        token = match[0].strip()
        gap = "\n\n" in header[previous:match.start() + match[0].index(token[0])]
        previous = match.end()
        if token.startswith("/*"):
            text = comment_text(token)
            title = re.match(r"== (.+?) ==\s*", text)
            if title:
                sections.append((title[1], []))
                text = text[title.end():]
            block = (text, [])
            sections[-1][1].append(block)
        elif not token.startswith(("#if", "#endif", "#include", "#define SPY_H")):
            if gap or block is None:
                block = ("", [])
                sections[-1][1].append(block)
            block[1].append(token)
    return sections if sections[0][1] else sections[1:]


def declarations(sections):
    return [decl for _, blocks in sections for _, decls in blocks for decl in decls]


def functions(decls):
    """Function name -> declaration, for every function the header declares."""
    found = {}
    for decl in decls:
        match = re.match(r"[^(]*?\b(spy_\w+)\s*\(", decl)
        if match and not decl.startswith(("typedef", "#")):
            found[match[1]] = decl
    return found


def callbacks(decls):
    found = {}
    for decl in decls:
        match = re.match(r"typedef [^(]*\(\*(\w+)\)", decl)
        if match:
            found[match[1]] = decl
    return found


def constants(decls):
    """Enumeration constant -> value, with implicit values counted."""
    found = {}
    for decl in decls:
        body = re.search(r"\benum\b[^{]*\{(.*?)\}", decl, re.S)
        if not body:
            continue
        value = -1
        for item in body[1].split(","):
            name, _, given = item.partition("=")
            value = int(given) if given.strip() else value + 1
            found[name.strip()] = value
    return found


def reference(sections):
    out = ["# C API reference", "",
           "Generated from [spy.h](../spy.h) by `tools/api.py`; edit the header and",
           "run `make api-reference`. The [manual](manual.md#34-c-api) explains how",
           "the pieces fit together.", ""]
    for title, _ in sections:
        out.append(f"- [{title}](#{title.lower().replace(' ', '-')})")
    for title, blocks in sections:
        out += ["", f"## {title}"]
        for text, decls in blocks:
            if decls:
                out += ["", "```c", *decls, "```"]
            if text:
                out += ["", textwrap.fill(text, 76, break_long_words=False, break_on_hyphens=False)]
    return "\n".join(out) + "\n"


def undocumented(sections):
    return [decl for _, blocks in sections for text, decls in blocks
            for decl in decls if not text and not decl.startswith("typedef struct")]


def exported(library):
    """External symbols the library defines, without the Mach-O underscore."""
    listing = subprocess.run(["nm", "-gP", library], check=True, text=True, capture_output=True).stdout
    names = set()
    for line in listing.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[1] in "TDBSC" and len(fields[1]) == 1:
            name = fields[0]
            names.add(name[1:] if sys.platform == "darwin" and name.startswith("_") else name)
    return names


def level(version):
    """Releases with the same level are compatible: the major version, or
    before 1.0 the minor version."""
    major, minor, _ = version.split(".")
    return (major, minor) if major == "0" else (major,)


def incompatibilities(old, new):
    """What the release's declarations need that the current header lacks."""
    old_decls, new_decls = declarations(parse(old)), declarations(parse(new))
    problems = [f"{name} = {value} changed or removed" for name, value in constants(old_decls).items()
                if constants(new_decls).get(name) != value]
    lines = ['#include "spy.h"']
    for name, decl in functions(old_decls).items():
        lines.append(re.sub(rf"\b{name}\s*\(", f"(*abi_{name})(", decl, count=1)[:-1] + f" = {name};")
    for name, decl in callbacks(old_decls).items():
        lines.append(decl.replace(f"(*{name})", f"(*abi_{name})", 1))
        lines.append(f'_Static_assert(_Generic((abi_{name})0, {name}: 1, default: 0), "{name}");')
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp, "abi.c")
        source.write_text("\n".join(lines) + "\n")
        compiler = os.environ.get("CC", "cc").split()
        result = subprocess.run([*compiler, "-std=c11", "-Werror", "-fsyntax-only", f"-I{ROOT}", str(source)],
                                text=True, capture_output=True)
    for line in result.stderr.splitlines():
        match = re.search(r"abi\.c:(\d+):\d+: error: (.*)", line)
        if match:
            problems.append(f"{lines[int(match[1]) - 1]}: {match[2]}")
    if result.returncode and not problems:
        problems.append(result.stderr.strip())
    return problems


def check(library):
    header = (ROOT / "spy.h").read_text()
    sections = parse(header)
    decls = declarations(sections)
    errors = [f"undocumented in spy.h: {decl}" for decl in undocumented(sections)]
    if REFERENCE.read_text() != reference(sections):
        errors.append("docs/api.md is stale; run make api-reference")
    exports = exported(library)
    errors += [f"{library} does not define {name}" for name in sorted(functions(decls).keys() - exports)]
    errors += [f"{library} exports {name}, which spy.h does not declare" for name in sorted(exports - functions(decls).keys())]
    tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0", "--match", "v[0-9]*", "HEAD"],
                         cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()
    old = subprocess.run(["git", "show", f"{tag}:spy.h"], cwd=ROOT, check=True, text=True, capture_output=True).stdout
    version = (ROOT / "VERSION").read_text().strip()
    problems = incompatibilities(old, header)
    if problems and level(version) == level(tag[1:]):
        errors += [f"incompatible with {tag} without a new {'minor' if version.startswith('0.') else 'major'} version: {p}"
                   for p in problems]
    if errors:
        sys.exit("\n".join(errors))
    print(f"C API: {len(functions(decls))} functions documented and exported, compatible with {tag}"
          + (f" except {len(problems)} changes allowed by {version}" if problems else ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", metavar="LIB")
    args = parser.parse_args()
    if args.check:
        check(args.check)
    else:
        REFERENCE.write_text(reference(parse((ROOT / "spy.h").read_text())))


if __name__ == "__main__":
    main()
