# Editing your model's website

Everything happens in your repository's **Issues** tab. You never touch code.

## The three forms

| Open this | To change |
|---|---|
| **Edit content** | Page text and titles: homepage, About, Applications, Datasets, Get Involved, Learning intro |
| **Edit YAML file** | EMP event cards, papers, partner logos, social links — **including their images** |
| **Upload Images** | Pictures for anywhere else (rarely needed) |

> EMP event photos and partner logos go in **Edit YAML file**, not Upload Images.

## How to make a change

1. **Issues → New issue** → pick a form → choose the file → **Submit**
2. Wait ~30 seconds, then refresh. The issue fills with one box per section or item.
3. Click **··· → Edit** (top right of the issue text)
4. Change what you need (see below)
5. Click **Update comment**
6. Wait ~1 minute → a **Pull Request** appears. Open it, check the preview, click **Merge**.
7. The site updates in a few minutes.

## What you can do inside the boxes

| Task | How |
|---|---|
| Change a title | Edit the text after `heading:` |
| Change a paragraph | Edit the text inside the ```` ```text ```` box |
| Add a photo | Put the cursor inside that item's box, drag the image in, rename `![image]` to a short name. No quotes around the link. |
| Add an item | Fill in the `new_event` / `new_publication` / `new_partner` template at the bottom. Leave it untouched to skip it. |
| Delete an item | Delete that whole `#### Event:` / `#### Publication:` / `#### Section:` block |
| Reorder items | Cut and paste whole blocks. Top of the list = first on the page. |

**Bold** = `**text**`  ·  Link = `[words](https://...)`  ·  Blank line = new paragraph

## If something goes wrong

| Problem | Fix |
|---|---|
| No boxes appeared | Wait a minute and refresh. Still nothing → check you picked a file. |
| A comment says an image could not be saved | Your text was saved and the old picture kept. Re-drag the image inside that block, no quotes around the link. |
| The page looks wrong after merging | Open the merged Pull Request → **Revert**. The site goes back. |
| You changed your mind before merging | Just close the Pull Request. Nothing is published. |

**Never delete a `<!-- CMS:section -->` line.** It marks what the editor is allowed to change.
