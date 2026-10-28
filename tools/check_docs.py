"""Check the checked-in manual and standard without fetching or extra packages."""

from collections import Counter
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent


def without_code(text):
    out, fence = [], None
    for line in text.splitlines():
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if match:
            marker = match[1]
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is None and not line.startswith("    "):
            out.append(line)
    if fence is not None:
        raise ValueError("unclosed Markdown code fence")
    return "\n".join(out)


def anchors(text):
    result = set(re.findall(r'<a id="([^"]+)">', text))
    for title in re.findall(r"^#{1,6} (.+)$", text, flags=re.M):
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        result.add(slug)
    return result


def main():
    files = [ROOT / "README.md", ROOT / "AGENTS.md", *sorted((ROOT / "docs").rglob("*.md"))]
    texts = {path: without_code(path.read_text()) for path in files}
    for path, text in texts.items():
        if 'href="..%20' in text or re.search(r'<div(?! class="line-block">)', text):
            raise ValueError(f"unconverted reference markup: {path.relative_to(ROOT)}")
        if text.count('<div class="line-block">') != text.count("</div>"):
            raise ValueError(f"unbalanced HTML blocks: {path.relative_to(ROOT)}")
        prose = re.sub(r"`+[^`]+`+", "", text)
        prose = re.sub(r"<code\b[^>]*>.*?</code>", "", prose, flags=re.S)
        for link in re.findall(r"\]\(([^)]+)\)", prose):
            if "://" in link or link.startswith(("mailto:", "/")):
                continue
            target, _, fragment = unquote(link).partition("#")
            destination = (path.parent / target).resolve() if target else path
            if not (destination.is_file() or (destination.is_dir() and not fragment)):
                raise ValueError(f"missing file in {path.relative_to(ROOT)}: {link}")
            if fragment:
                content = texts.get(destination)
                if content is None:
                    content = without_code(destination.read_text())
                if fragment not in anchors(content):
                    raise ValueError(f"missing anchor in {path.relative_to(ROOT)}: {link}")
        notes = re.findall(r"^\[\^([^\]]+)\]:", text, flags=re.M)
        duplicates = [name for name, count in Counter(notes).items() if count > 1]
        if duplicates:
            raise ValueError(f"duplicate footnotes in {path.relative_to(ROOT)}: {duplicates}")
    standard = (ROOT / "docs/standards/3_15.md").read_text()
    for required in ("PLS-315:2026-draft2", "file: [statements] ENDMARKER", "## 26 Mappings and Sets",
                     "#### 20.8.1 sentinel ( *name*, /, *, *repr*=None )", "### 17.5 Lazy imports", "## Annex B (normative) Host Hooks"):
        if required not in standard:
            raise ValueError(f"standard missing required content: {required}")
    # Cross-references such as (13.10) or 16.4.3 name an existing clause.
    sections = set(re.findall(r"^#{2,5} ((?:\d+|[A-E])(?:\.\d+)*)\b", standard, flags=re.M))
    for number, line in enumerate(without_code(standard).splitlines(), 1):
        if line.startswith("#"):
            continue
        prose = re.sub(r"`+[^`]+`+", "", line)
        for ref in re.findall(r"(?<![\w.])((?:[1-9]\d?|[A-E])\.\d+(?:\.\d+)*)(?![\w.]*\d)", prose):
            if ref not in sections and not re.fullmatch(r"\d+\.\d+\.0|3\.15|1\.0|2\.675?", ref):
                raise ValueError(f"standard line {number}: no clause {ref}")
    version = (ROOT / "VERSION").read_text().strip()
    header = (ROOT / "spy.h").read_text()
    if f'#define SPY_VERSION "{version}"' not in header:
        raise ValueError("VERSION and spy.h differ")
    print(f"Documentation: {len(files)} files, links, anchors, footnotes, standard contents and cross-references, and version checked")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        sys.exit(str(exc))
