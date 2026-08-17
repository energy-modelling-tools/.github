#!/usr/bin/env python3
"""Wrap editable prose in CMS:section markers so the Issue editor can reach it.

Run once per site when onboarding it to the Issue-based editor:

    python3 add_cms_markers.py path/to/site/*.markdown path/to/site/index.html

Blocks that are Liquid templates, buttons, or already marked are left alone.
"""
import pathlib
import re
import sys

BLOCK_RE = re.compile(r"<(p|ul)\b[^>]*>.*?</\1>", re.I | re.S)
HEADING_RE = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
EXISTING_RE = re.compile(r"<!--\s*CMS:section\s+id=([^\s]+)\s*-->", re.I)


def slug(text: str) -> str:
    text = TAG_RE.sub(" ", text or "")
    text = re.sub(r"&[a-z]+;", " ", text, flags=re.I)
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
    text = re.sub(r"_{2,}", "_", text)
    return "_".join(text.split("_")[:5]) or "section"


def plain_text(html: str) -> str:
    return TAG_RE.sub("", html).replace("&nbsp;", " ").strip()


def is_liquid(html: str) -> bool:
    return "{%" in html or "{{" in html


def is_button_only(html: str) -> bool:
    """A paragraph that is just a call-to-action button, not prose."""
    if 'class="btn' not in html and "class='btn" not in html:
        return False
    without_links = re.sub(r"<a\b.*?</a>", "", html, flags=re.I | re.S)
    return not plain_text(without_links)


def commented_ranges(text: str):
    return [
        (m.start(), m.end())
        for m in re.finditer(r"<!--.*?-->", text, re.S)
        if not m.group(0).lstrip("<!- ").lower().startswith("cms:section")
    ]


def add_markers(text: str, stem: str) -> tuple[str, int]:
    if EXISTING_RE.search(text):
        return text, 0

    skip = commented_ranges(text)
    used = set()
    edits = []

    for match in BLOCK_RE.finditer(text):
        start, end = match.span()
        block = match.group(0)

        if any(s <= start < e for s, e in skip):
            continue
        if is_liquid(block) or is_button_only(block):
            continue
        if not plain_text(block):
            continue

        heading = ""
        for h in HEADING_RE.finditer(text, 0, start):
            heading = h.group(2)
        base = f"{stem}_{slug(heading)}" if heading else f"{stem}_section"
        section_id = base
        counter = 2
        while section_id in used:
            section_id = f"{base}_{counter}"
            counter += 1
        used.add(section_id)

        indent = ""
        line_start = text.rfind("\n", 0, start) + 1
        if not text[line_start:start].strip():
            indent = text[line_start:start]

        edits.append((start, end, section_id, indent))

    for start, end, section_id, indent in reversed(edits):
        block = text[start:end]
        text = (
            text[:start]
            + f"<!-- CMS:section id={section_id} -->\n{indent}"
            + block
            + f"\n{indent}<!-- /CMS:section -->"
            + text[end:]
        )

    return text, len(edits)


def main() -> None:
    total = 0
    for arg in sys.argv[1:]:
        path = pathlib.Path(arg)
        if not path.exists():
            print(f"skip (missing): {path}")
            continue
        stem = re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_") or "page"
        if stem == "index":
            stem = "home"
        original = path.read_text(encoding="utf-8")
        updated, count = add_markers(original, stem)
        if count:
            path.write_text(updated, encoding="utf-8")
        print(f"{path}: {count} section(s)")
        total += count
    print(f"total: {total}")


if __name__ == "__main__":
    main()
