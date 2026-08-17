#!/usr/bin/env python3
"""Download dragged images and write YAML from parsed GitHub Issue blocks."""
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request

import yaml

EXT_MAP = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/svg+xml": "svg",
}

PLACEHOLDER_RE = re.compile(
    r"paste-or-drag|example\.com|example\.org|\.\.\.|user-attachments/?$",
    re.I,
)


class PrettyDumper(yaml.SafeDumper):
    pass


def _represent_str(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    if (
        data == ""
        or data.strip() != data
        or data.lower() in {"true", "false", "null", "yes", "no", "on", "off"}
        or re.fullmatch(r"[-+]?\d+(\.\d+)?", data)
        or any(ch in data for ch in ":#{}[]&*!|>%@`")
    ):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


PrettyDumper.add_representer(str, _represent_str)


def dump_yaml(data, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.dump(
        data,
        Dumper=PrettyDumper,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=1000,
    )
    path.write_text(text, encoding="utf-8")


def safe_name(value: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-._")
    return value or "image"


def is_remote(url: str) -> bool:
    return bool(re.match(r"^https?://", url or "", re.I))


def is_placeholder(url: str) -> bool:
    return not url or bool(PLACEHOLDER_RE.search(url))


class DropAuthOnRedirect(urllib.request.HTTPRedirectHandler):
    """GitHub signs the attachment host itself and rejects a forwarded token."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and urllib.parse.urlparse(newurl).hostname != req.host:
            new.remove_header("Authorization")
        return new


def download(url: str, dest_base: pathlib.Path) -> pathlib.Path:
    token = os.environ.get("GITHUB_TOKEN", "")
    parsed = urllib.parse.urlparse(url)
    headers = {
        "User-Agent": "energy-modelling-tools-yml-sync",
        "Accept": "*/*",
    }
    if token and parsed.hostname and "github.com" in parsed.hostname:
        headers["Authorization"] = f"Bearer {token}"
    opener = urllib.request.build_opener(DropAuthOnRedirect)
    req = urllib.request.Request(url, headers=headers)
    with opener.open(req, timeout=60) as resp:
        content_type = resp.info().get_content_type()
        data = resp.read()
        final_url = resp.geturl()
    ext = EXT_MAP.get(content_type, "")
    if not ext:
        path_name = pathlib.Path(urllib.parse.urlparse(final_url).path).name
        match = re.search(r"\.([A-Za-z0-9]+)$", path_name)
        ext = (match.group(1).lower() if match else "png")
        if ext not in {"png", "jpg", "jpeg", "gif", "svg", "webp"}:
            ext = "png"
        if ext == "jpeg":
            ext = "jpg"
    dest = dest_base.with_suffix("." + ext)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"Saved {url} -> {dest}")
    return dest


def resolve_media(
    src: str,
    alt: str,
    dest_dir: pathlib.Path,
    yaml_path: str,
    saved: list,
    failures: list,
    fallback: str = "",
) -> str:
    src = (src or "").strip().strip("\"'")
    if is_placeholder(src) or not is_remote(src):
        return src
    try:
        dest = download(src, dest_dir / safe_name(alt))
    except Exception as err:
        failures.append(f"{alt}: {type(err).__name__} {err}")
        print(f"Could not download {src} for {alt}: {err}")
        return fallback
    saved.append(dest.as_posix())
    if yaml_path == "relative":
        return f"../{dest.as_posix()}"
    return f"/{dest.as_posix()}"


def str_field(item: dict, *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        return str(value).strip()
    return ""


def existing_media(file_path: pathlib.Path, list_key: str, media_key: str) -> dict:
    """Map an item's title to the media path already committed, for fallbacks."""
    if not file_path.exists():
        return {}
    try:
        data = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    items = data.get(list_key) if isinstance(data, dict) else data
    known = {}
    for item in items or []:
        if not isinstance(item, dict):
            continue
        media = str(item.get(media_key) or "").strip()
        if not media:
            continue
        for key in ("title", "alt", "display_name", "name"):
            value = str(item.get(key) or "").strip()
            if value:
                known[value] = media
    return known


def main() -> None:
    payload = json.loads(sys.stdin.read())
    file_path = pathlib.Path(payload["file"])
    name = file_path.name
    saved = []
    failures = []

    if name == "learning_events.yml":
        previous = existing_media(file_path, "events", "image")
        events = []
        for event in payload.get("events") or []:
            alt = str_field(event, "alt", "title") or "event"
            image = resolve_media(
                str_field(event, "image"),
                alt,
                pathlib.Path("assets/img/EMP"),
                "relative",
                saved,
                failures,
                previous.get(str_field(event, "title")) or previous.get(alt, ""),
            )
            outputs = []
            for out in event.get("outputs") or []:
                outputs.append(
                    {
                        "country": str_field(out, "country"),
                        "flag": str_field(out, "flag"),
                        "title": str_field(out, "title"),
                        "url": str_field(out, "url"),
                    }
                )
            events.append(
                {
                    "title": str_field(event, "title"),
                    "image": image,
                    "alt": alt,
                    "description": str_field(event, "description"),
                    "outputs": outputs,
                }
            )
        adjacent = []
        for item in payload.get("adjacent") or []:
            adjacent.append(
                {
                    "country": str_field(item, "country"),
                    "flag": str_field(item, "flag"),
                    "title": str_field(item, "title"),
                    "url": str_field(item, "url"),
                }
            )
        dump_yaml({"events": events, "adjacent_events": adjacent}, file_path)

    elif name == "publications.yml":
        pubs = []
        for pub in payload.get("publications") or []:
            pubs.append(
                {
                    "title": str_field(pub, "title"),
                    "authors": str_field(pub, "authors"),
                    "year": str_field(pub, "year"),
                    "journal": str_field(pub, "journal"),
                    "url": str_field(pub, "url"),
                    "abstract": str_field(pub, "abstract"),
                }
            )
        dump_yaml(pubs, file_path)

    elif name == "orgs.yml":
        previous = existing_media(file_path, "partners", "logo")
        partners = []
        for partner in payload.get("partners") or []:
            display = str_field(partner, "display_name", "name") or "partner"
            logo = resolve_media(
                str_field(partner, "logo"),
                display,
                pathlib.Path("assets/img/partners"),
                "root",
                saved,
                failures,
                previous.get(str_field(partner, "name")) or previous.get(display, ""),
            )
            partners.append(
                {
                    "name": str_field(partner, "name"),
                    "logo": logo,
                    "display_name": display,
                    "url": str_field(partner, "url"),
                }
            )
        dump_yaml({"partners": partners}, file_path)

    elif name == "social_media.yml":
        links = []
        for link in payload.get("links") or []:
            links.append(
                {
                    "name": str_field(link, "name"),
                    "icon": str_field(link, "icon"),
                    "url": str_field(link, "url"),
                }
            )
        dump_yaml(links, file_path)

    else:
        raise SystemExit(f"Unsupported YAML file: {name}")

    # Keep reports outside the checkout so they never land in the pull request.
    report_dir = pathlib.Path(os.environ.get("EMT_REPORT_DIR") or ".")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "uploaded_files.txt").write_text(
        "\n".join(saved) + ("\n" if saved else ""),
        encoding="utf-8",
    )
    (report_dir / "image_failures.txt").write_text(
        "\n".join(failures) + ("\n" if failures else ""),
        encoding="utf-8",
    )
    print(f"Wrote {file_path}")


if __name__ == "__main__":
    main()
