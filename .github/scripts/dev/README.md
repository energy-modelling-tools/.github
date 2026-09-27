# Editor round-trip test

The Issue editor has one property that matters more than any other: **a manager who
opens an edit issue and saves it without changing anything must not change the site.**
If that breaks, every edit produces a huge diff and reviewers stop reading them.

This test checks that property against real site content.

## Running it

Clone the sites you want to check into `/tmp/emt-<name>` (the hub goes in `/tmp/emt-hub`):

```bash
for r in maed onsset osemosys clews ffrm nismod onstove pathcalc fintrack finplan minfin; do
  gh repo clone energy-modelling-tools/$r /tmp/emt-$r -- --depth 1
done
gh repo clone energy-modelling-tools/energy-modelling-tools.github.io /tmp/emt-hub -- --depth 1
```

Then, from a checkout of this repository:

```bash
python3 .github/scripts/dev/extract_editor_functions.py
node .github/scripts/dev/roundtrip_test.js
```

Expected output:

```
no-op edit rewrote the file: none  ✅
edit lost or mangled text:   none  ✅
```

## How it works

`extract_editor_functions.py` scrapes the real JavaScript out of
`prefill-issue-content.yml` and `issue-to-pr.yml` so the test exercises shipped code
rather than a copy that can drift. If you rename or restructure those functions the
extractor will fail loudly — update the patterns at the bottom of the script.

`roundtrip_test.js` then checks four things for every `CMS:section` it finds:

1. HTML turned into editable text and back is byte-identical to the original.
2. Appending a word keeps every other word intact.
3. Saving the prefilled title and link boxes untouched leaves the file alone.
4. A real title or link edit reaches its own section and no other.

## Things that have broken before

- Source line wrapping inside a `<p>` was turned into literal `<br>` tags, so one
  edit put forced line breaks through an entire page.
- DOI URLs contain parentheses (`S2542-5196(24)00209-2`) and the Markdown link
  pattern truncated them.
- A blank line means a paragraph break in the text box but is only source wrapping in
  the HTML, so the two sides need different normalisation.
- New About sections inserted at `<!-- Icon Links -->` sit outside the inner content
  column and look shifted left. They must follow the last existing section.
- The link box was written back to the last `<a>` before the heading, which on these
  pages is the previous section's button, so every save shifted the buttons by one.
- A commented-out `<h3 ...>` above a section paired with the real `</h3>` below it and
  the title box swallowed everything in between.
