#!/usr/bin/env python3
"""Turn a YAML data file into readable GitHub Issue blocks."""
import pathlib
import sys

import yaml


def fence(text: str) -> str:
    return "```text\n" + text.strip() + "\n```\n"


def md_image(alt, src) -> str:
    src = str(src or "").strip()
    alt = str(alt or pathlib.Path(src).stem or "image")
    return f"![{alt}]({src})" if src else ""


def main() -> None:
    path = pathlib.Path(sys.argv[1])
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    name = path.name
    chunks = [f"### 🧾 Editable items from `{path.as_posix()}`\n"]

    if name == "learning_events.yml":
        for event in data.get("events") or []:
            title = event.get("title") or "untitled"
            alt = event.get("alt") or title
            lines = [
                f"title: {event.get('title', '')}",
                f"alt: {alt}",
                f"description: {event.get('description', '')}",
                "image:",
                md_image(alt, event.get("image")) or "(drag a photo onto the next line)",
                "outputs:",
            ]
            outputs = event.get("outputs") or []
            if outputs:
                for out in outputs:
                    lines.append(
                        f"- {out.get('country', '')} | {out.get('flag', '')} | {out.get('title', '')} | {out.get('url', '')}"
                    )
            else:
                lines.append("(none)")
            chunks.append(f"#### Event: {title}\n" + fence("\n".join(lines)))

        for adj in data.get("adjacent_events") or []:
            title = adj.get("title") or "untitled"
            lines = [
                f"country: {adj.get('country', '')}",
                f"flag: {adj.get('flag', '')}",
                f"title: {adj.get('title', '')}",
                f"url: {adj.get('url', '')}",
            ]
            chunks.append(f"#### Adjacent: {title}\n" + fence("\n".join(lines)))

        chunks.append(
            """### Add a new EMP event (optional)

Copy a block below. Drag the photo **inside** the text fence, then rename `![image](url)` to `![EMP-A-2026](url)` with no quotes. Leave a block unchanged to skip.

#### Event: new_event
```text
title: EMP-A 2026 - City, Country
alt: EMP-A 2026
description: Write a short description of the event.
image:
![EMP-A-2026](paste-or-drag-image-here)
outputs:
- Ghana | 🇬🇭 | Output title | https://doi.org/...
```

#### Adjacent: new_adjacent
```text
country: Country
flag: 🇷🇼
title: Training title
url: https://example.com
```
"""
        )

    elif name == "publications.yml":
        pubs = data if isinstance(data, list) else []
        for pub in pubs:
            title = pub.get("title") or "untitled"
            lines = [
                f"title: {pub.get('title', '')}",
                f"authors: {pub.get('authors', '')}",
                f"year: {pub.get('year', '')}",
                f"journal: {pub.get('journal', '')}",
                f"url: {pub.get('url', '')}",
                f"abstract: {pub.get('abstract', '')}",
            ]
            chunks.append(f"#### Publication: {title}\n" + fence("\n".join(lines)))
        chunks.append(
            """### Add a publication (optional)

#### Publication: new_publication
```text
title: New paper title
authors: Names
year: 2026
journal: Journal name
url: https://doi.org/...
abstract: One paragraph summary.
```
"""
        )

    elif name == "orgs.yml":
        for partner in (data.get("partners") or []):
            disp = partner.get("display_name") or partner.get("name") or "partner"
            lines = [
                f"name: {partner.get('name', '')}",
                f"display_name: {partner.get('display_name', '')}",
                f"url: {partner.get('url', '')}",
                "logo:",
                md_image(disp, partner.get("logo")) or "(drag a logo onto the next line)",
            ]
            chunks.append(f"#### Partner: {disp}\n" + fence("\n".join(lines)))
        chunks.append(
            """### Add a partner (optional)

Drag the logo **inside** the text fence.

#### Partner: new_partner
```text
name: Organisation name
display_name: Short name
url: https://example.org
logo:
![short-name](paste-or-drag-logo-here)
```
"""
        )

    elif name == "social_media.yml":
        links = data if isinstance(data, list) else []
        for link in links:
            label = link.get("name") or "link"
            lines = [
                f"name: {link.get('name', '')}",
                f"icon: {link.get('icon', '')}",
                f"url: {link.get('url', '')}",
            ]
            chunks.append(f"#### Link: {label}\n" + fence("\n".join(lines)))
        chunks.append(
            """### Add a social link (optional)

#### Link: new_link
```text
name: Bluesky
icon: bi bi-link
url: https://example.com
```
"""
        )
    else:
        chunks.append("```yaml\n" + raw + "\n```\n")

    chunks.append(
        """
> 📝 **How to edit:**
> 1. Click **··· → Edit**
> 2. Change the text inside each ` ```text ` block
> 3. For photos/logos: put the cursor inside that event/partner block, drag the file in, rename `![image]` to a short filename, no quotes around the URL
> 4. **Delete an item:** remove that whole `#### Event:` / `#### Publication:` / `#### Partner:` / `#### Adjacent:` / `#### Link:` block
> 5. **Reorder:** cut and paste whole blocks. Leave `new_*` templates unchanged to skip them
> 6. Click **Update comment** — a Pull Request is created
>
> Images in EMP events are saved to `assets/img/EMP/`. Partner logos go to `assets/img/partners/`.
"""
    )
    sys.stdout.write("\n".join(chunks))


if __name__ == "__main__":
    main()
