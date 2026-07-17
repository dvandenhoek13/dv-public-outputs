#!/usr/bin/env python3
"""Build website commentary posts and merge them into outputs.json.

Posts live in posts/*.md with simple YAML-like front matter. The script uses only
Python's standard library so it can run in GitHub Actions without extra packages.
"""
from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "posts"
ARTICLES_DIR = ROOT / "articles"
OUTPUTS_PATH = ROOT / "outputs.json"
SITE_BASE = "https://dvandenhoek13.github.io/dv-public-outputs"


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
    required = {"title", "date", "category", "topic", "summary", "slug"}
    missing = sorted(required - meta.keys())
    if missing:
        raise ValueError(f"{path} is missing metadata: {', '.join(missing)}")
    return meta, body.strip()


def inline_markup(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', text)
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


def article_page(meta: dict[str, str], body_html: str) -> str:
    title = html.escape(meta["title"])
    summary = html.escape(meta["summary"])
    published = html.escape(meta["date"])
    topic = html.escape(meta["topic"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Dan van den Hoek</title>
<meta name="description" content="{summary}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{summary}">
<meta property="og:type" content="article">
<style>
:root{{--cyan:#00BCD4;--bg:#111216;--panel:#17191f;--text:#f5f5f5;--muted:#bfc5cc;--line:#3b4048}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font-family:Arial,Helvetica,sans-serif;line-height:1.68}}
main{{max-width:820px;margin:0 auto;padding:48px 22px 80px}} .eyebrow{{font-family:'Courier New',monospace;color:var(--cyan);font-weight:800;text-transform:uppercase}}
h1{{font-size:clamp(2rem,6vw,3.7rem);line-height:1.08;margin:.35rem 0 1rem}} .meta{{color:var(--muted);margin-bottom:2.4rem}}
h2{{font-size:1.55rem;margin-top:2.3rem}} p{{font-size:1.08rem}} blockquote{{border-left:4px solid var(--cyan);margin:2rem 0;padding:.2rem 0 .2rem 1.2rem;font-size:1.25rem;font-weight:700}}
a{{color:#8cecf7}} .back{{display:inline-block;margin-bottom:2rem;text-decoration:none;font-family:'Courier New',monospace}}
footer{{margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--line);color:var(--muted)}}
</style>
</head>
<body><main>
<a class="back" href="../">← Back to media</a>
<div class="eyebrow">{topic}</div>
<h1>{title}</h1>
<div class="meta">Published {published} · Dr Dan van den Hoek</div>
<article>{body_html}</article>
<footer>Evidence-based commentary on strength, inclusive sport, technology and performance.</footer>
</main></body></html>"""


def main() -> None:
    ARTICLES_DIR.mkdir(exist_ok=True)
    payload = json.loads(OUTPUTS_PATH.read_text(encoding="utf-8"))
    existing = [
        item for item in payload.get("outputs", [])
        if item.get("source_type") != "Website commentary"
    ]
    commentary: list[dict[str, str]] = []

    for path in sorted(POSTS_DIR.glob("*.md")):
        meta, body = parse_post(path)
        body_html = markdown_to_html(body)
        article_path = ARTICLES_DIR / f"{meta['slug']}.html"
        article_path.write_text(article_page(meta, body_html), encoding="utf-8")
        year = meta["date"][:4]
        commentary.append({
            "title": meta["title"],
            "source": "Dan van den Hoek",
            "year": year,
            "date": meta["date"],
            "category": meta["category"],
            "topic": meta["topic"],
            "description": meta["summary"],
            "url": f"{SITE_BASE}/articles/{meta['slug']}.html",
            "button_text": "Read article",
            "source_type": "Website commentary",
        })

    payload["generated_at"] = date.today().isoformat()
    payload["outputs"] = sorted(
        existing + commentary,
        key=lambda item: (str(item.get("date", "")), str(item.get("title", ""))),
        reverse=True,
    )
    OUTPUTS_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Built {len(commentary)} commentary post(s); {len(payload['outputs'])} total media outputs.")


if __name__ == "__main__":
    main()
