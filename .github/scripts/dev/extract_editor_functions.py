"""Pull the real functions out of the workflow YAML so the test exercises shipped code."""
import pathlib
import re
import sys

ORG = pathlib.Path("/tmp/emt-org-github/.github/workflows")


def dedent_block(text: str) -> str:
    lines = [l for l in text.split("\n")]
    indents = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
    pad = min(indents) if indents else 0
    return "\n".join(l[pad:] if len(l) >= pad else l for l in lines)


def grab(path: pathlib.Path, start_pat: str, end_pat: str) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(start_pat, text, re.M)
    if not m:
        sys.exit(f"start not found in {path.name}: {start_pat}")
    rest = text[m.start():]
    e = re.search(end_pat, rest)
    if not e:
        sys.exit(f"end not found in {path.name}: {end_pat}")
    return dedent_block(rest[: e.end()])


prefill = ORG / "prefill-issue-content.yml"
topr = ORG / "issue-to-pr.yml"

parts = [
    grab(prefill, r"^\s*const decodeEntities = ", r"\n\s*const cmsSections"),
    grab(topr, r"^\s*const escapeHtml = ", r";\n"),
    grab(topr, r"^\s*const editableToHtml = ", r"\n\s*\};"),
    grab(topr, r"^\s*const rebuildSectionInner = ", r"\n\s*\};"),
    grab(topr, r"^\s*// Reduce HTML and editable text", r"\n\s*const headingText[\s\S]*?\n\s*\);"),
]

out = "\n\n".join(parts)
# The prefill block ends just before cmsSections; drop that trailing marker line.
out = re.sub(r"^const cmsSections.*$", "", out, flags=re.M)
out += """

module.exports = { htmlToEditable, editableToHtml, rebuildSectionInner, normalizeForCompare, headingText };
"""
pathlib.Path("/tmp/rt-test/shipped.js").write_text(out, encoding="utf-8")
print("wrote shipped.js")
