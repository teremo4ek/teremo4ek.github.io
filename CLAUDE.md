# CLAUDE.md

## Project

Personal site/blog of Yury Bely. Built on **Hugoplate** (Hugo + Tailwind CSS) template. Hosted on GitHub Pages.

## Tech Stack

- Hugo Extended v0.126+
- Tailwind CSS, PostCSS, PurgeCSS
- Hugo Modules (gethugothemes)
- Node v20+, Go v1.22+

## Commands

- `npm run dev` — local dev server
- `npm run build` — production build (minified, purged CSS)
- `npm run preview` — preview production build
- `npm install` — install dependencies
- `npm run update-modules` — update Hugo modules

## Key Files

- `hugo.toml` — main Hugo config
- `config/_default/params.toml` — site params (logo, SEO, features)
- `config/_default/menus.en.toml` — navigation menus
- `config/_default/languages.toml` — language config
- `data/theme.json` — colors and fonts
- `data/social.json` — social links
- `assets/scss/custom.scss` — custom styles (currently empty)

## Content

All content is in `content/english/` — homepage, about, blog, contact, authors, pages.

## Creating Blog Posts

Posts go in `content/english/blog/` as Markdown files (`YYYY-MM-DD-title.md`). Frontmatter:

```yaml
---
title: "Post Title"
description: "SEO description"
date: 2026-05-13T05:00:00Z
image: "/images/cover.png"
categories: ["Category"]
tags: ["tag1", "tag2"]
draft: false
---
```

Fields: `title`, `description`, `date` (RFC3339), `image` (path from site root), `categories`, `tags`, `draft` (true = dev only), `meta_title` (optional SEO). Images go in `assets/images/` or `static/images/`. Posts sort by date (newest first), 10 per page.

## Multilingual (English + Russian)

- English: `content/english/`, URL at root `/`
- Russian: `content/russian/`, URL at `/ru/`
- Language switcher is built into the theme header (auto-shows when multilingual)
- Config: `config/_default/languages.toml`, menus: `menus.en.toml` / `menus.ru.toml`
- UI translations: `i18n/en.yaml` / `i18n/ru.yaml`
- Russian blog posts go in `content/russian/blog/` with the same frontmatter format

## Theme

`themes/hugoplate/` — do not modify directly. Override via `layouts/` or `assets/`.

## Current State

Minimally customized template. Personal info (bio, socials) is set. Blog has 1 demo post. GA and Disqus use placeholder values. Images are placeholders.
