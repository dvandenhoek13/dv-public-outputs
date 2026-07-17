# VDH Public Outputs and Insights Publishing Engine

This repository is the source of truth for Dr Dan van den Hoek's public outputs and original website Insights.

## Content model

- `posts/` contains original Insights as Markdown with front matter.
- `social/` contains complementary platform copy for LinkedIn, Facebook and future channels.
- `scripts/build_commentary.py` builds portable fallback HTML and refreshes the public-output feed.
- `scripts/publish_to_wix.py` converts each Markdown Insight to HTML and sends it to the secure Wix CMS endpoint.
- `articles/` contains generated GitHub Pages fallback copies.
- `outputs.json` stores the Media page feed, including externally published commentary and media appearances.

Research outputs remain separate in `dv-research-outputs`.

## Publishing workflow

1. Create or edit a Markdown file in `posts/`.
2. Commit the change to `main`.
3. GitHub Actions validates the repository, builds the fallback article and posts the Insight to Wix.
4. Wix creates a new CMS item or updates the existing item with the same slug.
5. The canonical public address is:

   `https://www.danvandenhoek.com/insights/<slug>`

The GitHub Pages copy is retained only as a portable fallback and uses a canonical link pointing to the Wix-hosted article.

## Required GitHub configuration

In the repository, open:

`Settings → Secrets and variables → Actions`

Create this repository secret:

- `WIX_PUBLISH_KEY` — the exact value stored as `VDH_PUBLISH_KEY` in Wix Secrets Manager.

Optionally create this repository variable:

- `WIX_PUBLISH_URL` — `https://www.danvandenhoek.com/_functions/publishInsight`

The workflow already uses that URL as its default, so the variable is only needed if the endpoint changes.

## Insight front matter

Each Markdown file begins with:

```yaml
---
title: Article title
date: 2026-07-17
category: Insights
topic: Para Powerlifting
summary: Short card and sharing summary.
slug: article-url-slug
read_time: 5
featured: false
status: Published
seo_description: Search description of approximately 150–160 characters.
tags: tag one, tag two
hero_image_alt: Accessible description of the hero image.
---
```

Required fields are `title`, `date`, `summary` and `slug`. The Media fallback builder also expects `category` and `topic`.

## Drafts

Use:

```yaml
status: Draft
```

Draft handling can be extended later to support scheduled publication. At present, only approved files should be merged to `main`.

## Updating Media outputs

External appearances and publications remain manually curated in `outputs.json`. Each item should include:

- `title`
- `source`
- `year`
- `date`
- `category`
- `topic`
- `description`
- `url`
- `button_text`
