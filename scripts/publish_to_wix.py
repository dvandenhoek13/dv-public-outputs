#!/usr/bin/env python3
"""Publish Markdown Insights to the secure Wix CMS endpoint.

GitHub remains the source of truth. Each post in posts/*.md is converted into
an authenticated JSON request. Publishing is idempotent because Wix creates or
updates records using the article slug.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "posts"
DEFAULT_ENDPOINT = "https://www.danvandenhoek.com/_functions/publishInsight"


def parse_post(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path} must begin with front matter")

    _, front, body = text.split("---\n", 2)
    meta: dict[str, str] = {}
    for raw in front.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            raise ValueError(f"Invalid front-matter line in {path}: {raw}")
        key, value = raw.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")

    required = {"title", "date", "summary", "slug"}
    missing = sorted(required - meta.keys())
    if missing:
        raise ValueError(f"{path} is missing metadata: {', '.join(missing)}")

    return meta, body.strip()


def inline_markup(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2">\1</a>',
        text,
    )
    return text


def markdown_to_html(markdown: str) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            blocks.append(f"<p>{inline_markup(' '.join(paragraph))}</p>")
            paragraph.clear()

    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith("### "):
            flush()
            blocks.append(f"<h3>{inline_markup(line[4:])}</h3>")
        elif line.startswith("## "):
            flush()
            blocks.append(f"<h2>{inline_markup(line[3:])}</h2>")
        elif line.startswith("# "):
            flush()
            blocks.append(f"<h1>{inline_markup(line[2:])}</h1>")
        elif line.startswith("> "):
            flush()
            blocks.append(f"<blockquote>{inline_markup(line[2:])}</blockquote>")
        else:
            paragraph.append(line)

    flush()
    return "\n".join(blocks)


def to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def payload_for(meta: dict[str, str], body: str) -> dict[str, object]:
    words = len(re.findall(r"\b\w+\b", body))
    estimated_read_time = max(1, round(words / 220))

    return {
        "title": meta["title"],
        "slug": meta["slug"],
        "summary": meta["summary"],
        "body": markdown_to_html(body),
        "publishDate": meta["date"],
        "category": meta.get("category", "Insights"),
        "readTime": int(meta.get("read_time", estimated_read_time)),
        "featured": to_bool(meta.get("featured")),
        "status": meta.get("status", "Published"),
        "seoDescription": meta.get("seo_description", meta["summary"]),
    }


def publish(endpoint: str, key: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-vdh-publish-key": key,
            "User-Agent": "VDH-Publishing-Engine/1.0",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Wix returned HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach Wix: {error.reason}") from error

    if not result.get("success"):
        raise RuntimeError(f"Wix rejected the article: {result}")
    return result


def main() -> None:
    key = os.environ.get("WIX_PUBLISH_KEY", "").strip()
    configured_endpoint = os.environ.get("WIX_PUBLISH_URL", "").strip()
    endpoint = configured_endpoint or DEFAULT_ENDPOINT

    if not key:
        print("WIX_PUBLISH_KEY is not configured; skipping Wix publication.")
        return

    selected = [Path(arg) for arg in sys.argv[1:]] if len(sys.argv) > 1 else sorted(POSTS_DIR.glob("*.md"))
    if not selected:
        raise SystemExit("No Insight Markdown files were found.")

    published_count = 0
    for path in selected:
        meta, body = parse_post(path)
        if meta.get("status", "Published").strip().lower() != "published":
            print(f"Skipped draft: {meta['title']}")
            continue
        result = publish(endpoint, key, payload_for(meta, body))
        published_count += 1
        print(f"{result.get('action', 'published').title()}: {meta['title']} ({meta['slug']})")

    print(f"Published {published_count} Insight(s) to Wix.")


if __name__ == "__main__":
    main()
