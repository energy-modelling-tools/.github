# Maintaining the Issue editor

Reference for whoever takes over development. Managers should read
[EDITING-CHEATSHEET.md](EDITING-CHEATSHEET.md) instead.

## What this is

12 Jekyll sites (11 tool sites + the hub). Non-technical managers edit content by
opening a GitHub Issue; a workflow prefills it with editable boxes, and saving the
issue opens a Pull Request. No one clones a repo or writes YAML by hand.

## Single source of truth

All editor logic lives in **`energy-modelling-tools/.github`** on `main`. Each site
only carries a thin caller that says "use the org's workflow":

```yaml
uses: energy-modelling-tools/.github/.github/workflows/issue-to-pr.yml@main
```

Change these once and all 12 sites pick it up on their next issue:

| Path | Role |
|---|---|
| `.github/workflows/prefill-issue-content.yml` | Page HTML → editable boxes |
| `.github/workflows/prefill-yml-content.yml` | Data YAML → editable boxes |
| `.github/workflows/issue-to-pr.yml` | Edited boxes → page HTML → PR |
| `.github/workflows/update-yml-with-images.yml` | Edited boxes → data YAML → PR |
| `.github/workflows/issue-upload-image.yml` | Standalone image uploads |
| `.github/workflows/pr-close-cleanup.yml` | Deletes branches after PR close |
| `.github/scripts/yaml_to_issue.py` | YAML → issue blocks |
| `.github/scripts/apply_yml_issue.py` | Issue blocks → YAML, downloads images |
| `.github/ISSUE_TEMPLATE/*.yml` | Org default issue forms |

The Python scripts are checked out at runtime from `.github@main` into `.emt-scripts`.

## Per-repo, NOT automatic

| Thing | Why | How to fix |
|---|---|---|
| `.github/workflows/issue-content-handler.yml` | GitHub requires the caller in the repo | `propagate-issue-workflows.yml` pushes it from `workflow-templates/`; runs on push, weekly Monday 03:00, or `workflow_dispatch` |
| `<!-- CMS:section -->` markers in pages | Per-site content | `.github/scripts/add_cms_markers.py <files>`, then review the diff |
| CLEWs and hub issue templates | Different data filenames | Local `.github/ISSUE_TEMPLATE/` overrides the org default |
| Labels `content-edit`, `yml-edit`, `upload-image` | Repo-level | `gh label create` per repo |
| Actions permissions | Repo-level | Set org-wide: Org Settings → Actions → General → Workflow permissions → "Read and write" + "Allow GitHub Actions to create and approve pull requests" |

**A repo with its own `.github/ISSUE_TEMPLATE/` stops receiving org template updates.**
Only CLEWs and the hub should have one.

## Site-specific notes

- **CLEWs** — uses `_data/publication.yml` (singular) and `pros.yml`; no
  `learning_events.yml`. Its homepage and Applications page are Liquid includes, so
  they have no editable sections.
- **Hub** (`energy-modelling-tools.github.io`) — only `index.html` plus
  `_data/tools.yml`, which drives the homepage tool grid. Block order = grid order.
- **NISMOD** — no `dataset.markdown`.

## Adding a new site

1. Add `<!-- CMS:section -->` markers: `python3 .github/scripts/add_cms_markers.py index.html about.markdown ...`
2. Run `propagate-issue-workflows.yml` (or wait for Monday) to install the caller
3. Create the three labels
4. Confirm Actions can create PRs (inherited if the org default is set)

## Round-trip test

The property that matters: **opening an edit issue and saving it unchanged must not
change the site.** If it breaks, every edit produces a huge diff and reviewers stop
reading them.

```bash
python3 .github/scripts/dev/extract_editor_functions.py
node .github/scripts/dev/roundtrip_test.js
```

It scrapes the real JS out of the workflow YAML (so it cannot drift from shipped code)
and checks all ~294 sections across the 12 sites. See
[`.github/scripts/dev/README.md`](../.github/scripts/dev/README.md). Run it before and
after any change to the prefill or rebuild logic.

## Gotchas already hit

- **Auth on redirect** — GitHub attachment URLs redirect to a signed host that rejects
  a forwarded `Authorization` header with a 404. `apply_yml_issue.py` uses
  `DropAuthOnRedirect` to strip it across hosts. Don't reintroduce a plain `urlopen`.
- **Source wrapping is not a line break** — HTML wrapped across source lines must be
  collapsed on prefill, otherwise the rebuild writes literal `<br>` into every
  paragraph and one edit reformats the whole page. Only real `<br>` and `</p><p>`
  count as breaks.
- **Untouched sections must be skipped** — `issue-to-pr.yml` compares each section via
  `normalizeForCompare` and returns the original HTML byte-for-byte when unchanged.
- **PARABREAK is asymmetric** — a blank line is a paragraph break in the text box but
  only source wrapping in HTML. `normalizeForCompare(value, fromEditable)` needs the
  flag; passing it wrongly makes real edits look unchanged and silently drops them.
- **DOI URLs contain parentheses** (`S2542-5196(24)00209-2`). Markdown link patterns
  must allow one balanced pair: `\(((?:[^()\s]|\([^()]*\))+)\)`.
- **Never write temp files into the checkout** — `create-pull-request` commits
  everything. Reports go to `EMT_REPORT_DIR` (`runner.temp`).
- **Image download failures must not fail the run** — `resolve_media` falls back to the
  previously committed path and the workflow comments the failures on the issue.

## Known debt

- `propagate-issue-workflows.yml` depends on the `PAGE_TEMPLATE_APP_*` org secrets.
  The older `UPDATE_WORK_FLOW_*` pair is dead — don't switch back.
- Prefill and rebuild each carry their own copy of the HTML↔text conversion. They must
  stay in sync; the round-trip test is what catches divergence.
- `_data/pros.yml` (CLEWs) has no editable-block handler and falls back to a raw YAML
  dump.
