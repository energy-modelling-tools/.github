# Handover demo — 45 minutes

Running order for the live session with model managers. Record the meeting; do not
make a polished video afterwards.

**Before you start:** one browser window, logged in, on a manager's repo (not MAED).
Have [EDITING-CHEATSHEET.md](EDITING-CHEATSHEET.md) printed or shared.

| Time | Segment |
|---|---|
| 0:00–0:05 | Framing |
| 0:05–0:20 | Demo 1 — page text |
| 0:20–0:32 | Demo 2 — event card with a photo |
| 0:32–0:42 | Hands-on: each manager does one edit |
| 0:42–0:45 | Approvals, rollback, questions |

---

## 0:00–0:05 Framing

- Show the live site, then the repo. Say: everything is edited from the **Issues** tab.
- Name who merges Pull Requests after today, and their backup.
- Say once, plainly: this runs entirely on GitHub. If GitHub is having problems the
  editor stops working, and [githubstatus.com](https://www.githubstatus.com) will say so.
  That way nobody mistakes an outage for a broken system.

## 0:05–0:20 Demo 1 — change page text and a title

1. **Issues → New issue → Edit content**
2. File: `about.markdown (About page text)` → **Submit new issue**
3. Wait ~30s, **refresh**. Point out: one box per section, `heading:` is the title.
4. **··· → Edit**
5. Change one `heading:` line and one sentence inside a ```` ```text ```` box
6. **Update comment**
7. Wait ~1 min, refresh. Open the linked **Pull Request**.
8. Open **Files changed**. Point out that only the edited section appears.
9. **Merge pull request** → **Confirm merge**
10. Open the live page, refresh until it updates (a few minutes).

Say while waiting: bold is `**text**`, links are `[words](https://...)`, a blank line
starts a new paragraph, and never delete a `<!-- CMS:section -->` line.

## 0:20–0:32 Demo 2 — add an EMP event with a photo

1. **Issues → New issue → Edit YAML file**
2. File: `_data/learning_events.yml (EMP event cards)` → **Submit**
3. Refresh. Scroll to the bottom: `#### Event: new_event`
4. **··· → Edit**
5. Fill in title and description in that block
6. Put the cursor on the `logo:`/`image:` line, **drag an image file in**
7. Rename `![image]` to a short name, e.g. `![EMP-A-2026]`. Say: no quotes around the link.
8. **Update comment** → wait → open the PR → **Merge**

Also show, without doing them:
- Delete an item = delete its whole `#### Event:` block
- Reorder = cut and paste whole blocks
- You do **not** need a separate Upload Images issue for these photos

## 0:32–0:42 Hands-on

Each manager, on their own repo, makes one real edit end to end: open the issue, edit,
save, merge. Walk the room. Note where people hesitate — that is what the cheat sheet
needs to fix.

## 0:42–0:45 Close

- Who reviews and merges, and the expected turnaround
- **If a page looks wrong:** open the merged PR → **Revert**
- **If you change your mind before merging:** just close the PR, nothing is published
- If an image fails, a comment says so; the text is still saved and the old picture kept
- Where the cheat sheet lives, and who to contact

---

## Recovery during the demo

| If | Do |
|---|---|
| Nothing works — pages 404, issues or Actions hang | Check [githubstatus.com](https://www.githubstatus.com) first. During an outage, stop demoing and reschedule; nothing here can be fixed from your side. |
| No boxes appear after 1 min | Refresh again; check a file was selected in the form |
| No PR appears | **Actions** tab → open the latest run → read the failed step |
| PR fails with "not permitted to create or approve pull requests" | Org Settings → Actions → General → Workflow permissions |
| A merge breaks the page | Demonstrate **Revert** — this is a feature, not a failure |
