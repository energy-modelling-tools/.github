"""Report pages whose CMS:section markers the Issue editor can no longer read.

Hand-editing a page is easy to get wrong: rename a marker, drop a closing one, or
duplicate an id, and the editor silently stops offering those sections. Managers
then see a half-empty issue and, worse, saving it reads the missing sections as
deletions.

Two modes:

    python3 check_cms_markers.py                    # every org repo, opens issues
    python3 check_cms_markers.py --local DIR [DIR]  # local checkouts, prints only
"""
import base64
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ORG = os.environ.get("ORG", "energy-modelling-tools")
SKIP_REPOS = {".github", "page-template"}
PAGE_SUFFIXES = (".markdown", ".html")
SKIP_PAGES = {"404.html"}

# Any comment that means to be a marker, so typos are caught instead of ignored.
MARKER_RE = re.compile(r"<!--\s*(/?)\s*CMS\b([^>]*?)-->", re.I)
OPEN_RE = re.compile(r"^:section\s+id=(\S+)$")
ISSUE_STAMP = "<!-- emt:cms-marker-check -->"
ISSUE_TITLE = "Editable page sections need attention"


def check_page(text):
    """Problems with the markers in one page, as '<line>: <what>' strings."""
    problems = []
    open_id = None
    seen_ids = {}
    for match in MARKER_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        closing, rest = match.group(1) == "/", match.group(2).strip()
        if closing:
            if rest != ":section":
                problems.append(f"{line}: `{match.group(0)}` should be `<!-- /CMS:section -->`")
                continue
            if open_id is None:
                problems.append(f"{line}: closing marker with nothing open")
                continue
            open_id = None
            continue
        opened = OPEN_RE.match(rest)
        if not opened:
            problems.append(f"{line}: `{match.group(0)}` should be `<!-- CMS:section id=... -->`")
            continue
        section_id = opened.group(1)
        if open_id is not None:
            problems.append(f"{line}: `{section_id}` opens while `{open_id}` is still open")
        if section_id in seen_ids:
            problems.append(f"{line}: id `{section_id}` is already used on line {seen_ids[section_id]}")
        seen_ids[section_id] = line
        open_id = section_id
    if open_id is not None:
        problems.append(f"end of file: `{open_id}` is never closed")
    return problems


def api(token, method, url, payload=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        try:
            return err.code, json.loads(body)
        except json.JSONDecodeError:
            return err.code, {"message": body}


class ReportingUnavailable(Exception):
    """The token cannot use this repo's issues, so findings go nowhere."""


def paginate(token, url):
    items = []
    page = 1
    while True:
        status, data = api(token, "GET", f"{url}&page={page}")
        if status != 200:
            raise RuntimeError(f"HTTP {status} for {url}: {data}")
        if not data:
            break
        items.extend(data)
        if len(data) < 100:
            break
        page += 1
    return items


def is_page(name):
    return name.endswith(PAGE_SUFFIXES) and name not in SKIP_PAGES


def check_repo(token, repo):
    """{filename: [problems]} for one org repo."""
    status, listing = api(token, "GET", f"https://api.github.com/repos/{repo}/contents/")
    if status != 200:
        raise RuntimeError(f"HTTP {status} listing {repo}: {listing}")
    findings = {}
    for entry in listing:
        if entry.get("type") != "file" or not is_page(entry.get("name", "")):
            continue
        path = urllib.parse.quote(entry["path"])
        status, blob = api(token, "GET", f"https://api.github.com/repos/{repo}/contents/{path}")
        if status != 200:
            raise RuntimeError(f"HTTP {status} reading {repo}/{entry['name']}: {blob}")
        text = base64.b64decode(blob.get("content", "")).decode("utf-8", errors="replace")
        problems = check_page(text)
        if problems:
            findings[entry["name"]] = problems
    return findings


def issue_body(repo, findings):
    lines = [
        ISSUE_STAMP,
        "",
        "The Issue editor reads editable sections between `<!-- CMS:section id=... -->` and",
        "`<!-- /CMS:section -->`. On the pages below it cannot, so those sections are missing",
        "from the edit forms — and a form that is missing a section reads it as deleted when",
        "someone saves.",
        "",
    ]
    for name, problems in sorted(findings.items()):
        lines.append(f"### `{name}`")
        lines.append("")
        for problem in problems:
            lines.append(f"- {problem}")
        lines.append("")
    lines += [
        "Fix the markers in the file, or regenerate them with",
        "`python3 .github/scripts/add_cms_markers.py <file>` from the org `.github` repo.",
        "",
        "This issue is opened and closed automatically by `check-cms-markers.yml`.",
    ]
    return "\n".join(lines)


def issue_api(token, repo, method, path, payload=None):
    status, data = api(token, method, f"https://api.github.com/repos/{repo}/{path}", payload)
    if status in (403, 404, 410):
        raise ReportingUnavailable(f"HTTP {status} on {path}: {data.get('message', data)}")
    return status, data


def existing_issue(token, repo):
    status, issues = issue_api(token, repo, "GET", "issues?state=open&per_page=100")
    if status != 200:
        raise RuntimeError(f"HTTP {status} listing issues on {repo}: {issues}")
    for issue in issues:
        if "pull_request" in issue:
            continue
        if ISSUE_STAMP in (issue.get("body") or ""):
            return issue
    return None


def report(token, repo, findings):
    issue = existing_issue(token, repo)
    if not findings:
        if issue:
            issue_api(token, repo, "PATCH", f"issues/{issue['number']}", {"state": "closed"})
            print(f"  closed #{issue['number']}, markers are healthy again")
        return
    body = issue_body(repo, findings)
    if issue:
        if (issue.get("body") or "").strip() == body.strip():
            print(f"  #{issue['number']} already says this")
            return
        status, _ = issue_api(token, repo, "PATCH", f"issues/{issue['number']}", {"body": body})
        print(f"  updated #{issue['number']} (HTTP {status})")
        return
    status, created = issue_api(token, repo, "POST", "issues",
                               {"title": ISSUE_TITLE, "body": body})
    if status == 201:
        print(f"  opened #{created['number']}")
    else:
        raise RuntimeError(f"HTTP {status} opening an issue on {repo}: {created}")


def run_local(dirs):
    bad = 0
    for directory in dirs:
        root = pathlib.Path(directory)
        for page in sorted(root.iterdir()):
            if not page.is_file() or not is_page(page.name):
                continue
            problems = check_page(page.read_text(encoding="utf-8", errors="replace"))
            if problems:
                bad += 1
                print(f"{page}")
                for problem in problems:
                    print(f"  {problem}")
    print("pages with broken markers:", bad or "none  ✅")
    return 0


def run_org():
    token = os.environ.get("TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    repos = paginate(token, f"https://api.github.com/orgs/{ORG}/repos?per_page=100&type=all")
    total = 0
    undelivered = []
    for repo in sorted(r["name"] for r in repos if not r.get("archived")):
        if repo in SKIP_REPOS:
            continue
        full = f"{ORG}/{repo}"
        findings = check_repo(token, full)
        total += len(findings)
        print(f"{full}: {len(findings) or 'no'} page(s) with broken markers")
        try:
            report(token, full, findings)
        except ReportingUnavailable as err:
            # A repo the token cannot file issues on is only a problem if it has
            # something to say about it.
            print(f"  ⚠️ cannot use issues here — {err}")
            if findings:
                undelivered.append(full)
    print("\npages with broken markers:", total or "none  ✅")
    if undelivered:
        print("\nFindings that could not be reported:", ", ".join(undelivered))
        print("Give the app Issues write access on those repos, or fix the pages by hand.")
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        sys.exit(run_local(sys.argv[2:]))
    try:
        sys.exit(run_org())
    except RuntimeError as err:
        print(f"❌ {err}")
        sys.exit(1)
