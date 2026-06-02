# Git-Based AI Blog Site — Architecture Plan

## What We're Building

A two-phase system:

1. **Phase 1 — Static Blog Site**: Astro 5 static site that reads posts from `posts/` markdown folders and deploys to GitHub Pages.
2. **Phase 2 — AI Post Generator**: Nightly GitHub Actions workflow that uses Claude or Gemini + Tavily to discover unique topics, research them, generate full posts, and open PRs. Merging the PR triggers deployment.

No CMS. No database. Git is the content store. PR review = editorial workflow.

---

## Full File/Folder Structure

```
asd-site/
├── .github/
│   └── workflows/
│       ├── generate-post.yml     # nightly AI generation → opens PR
│       └── deploy.yml            # build + deploy to GitHub Pages on push to main
│
├── .claude/
│   └── commands/
│       ├── next-task.md          # /next-task — guided next step
│       ├── phase1.md             # /phase1 — Phase 1 status + next task
│       ├── phase2.md             # /phase2 — Phase 2 status + next task
│       └── generate-post.md     # /generate-post — run generation script locally
│
├── posts/
│   ├── index.json                # master post list (auto-maintained)
│   └── {YYYY-MM-DD-slug}/
│       ├── meta.json
│       ├── post.md
│       └── assets/
│           └── hero.jpg
│
├── scripts/                      # Phase 2 only — runs in GitHub Actions
│   ├── ai_client.py              # Claude/Gemini abstraction
│   ├── search_topic.py           # Tavily search + duplicate detection
│   ├── research_topic.py         # multi-source research
│   ├── write_post.py             # AI content generation
│   ├── download_images.py        # image fetch + resize
│   ├── update_index.py           # posts/index.json updater
│   ├── generate_post.py          # main orchestrator
│   └── requirements.txt
│
├── src/
│   ├── components/
│   │   ├── PostCard.astro
│   │   ├── TagBadge.astro
│   │   ├── Header.astro
│   │   └── Footer.astro
│   ├── layouts/
│   │   ├── BaseLayout.astro
│   │   └── PostLayout.astro
│   ├── pages/
│   │   ├── index.astro
│   │   └── posts/[id].astro
│   └── styles/
│       └── global.css
│
├── public/
│   └── favicon.svg
│
├── CLAUDE.md
├── TASKS.md
├── PROGRESS.md
├── PLAN.md                       # this file
├── config.json
├── astro.config.mjs
├── package.json
├── tsconfig.json
└── .gitignore
```

---

## Tech Stack

| Concern | Choice | Reason |
|---|---|---|
| Static site | **Astro 5** | Zero JS by default, native MD/MDX, GitHub Pages deploy is trivial |
| Markdown | `@astrojs/mdx` | Adds MDX support for future interactive components |
| Web search | **Tavily** (`tavily-python`) | Structured JSON sources — ideal LLM input |
| AI generation | **Claude** `claude-sonnet-4-6` or **Gemini** `gemini-2.0-flash` | Auto-detected from env vars; Claude preferred |
| Images | `requests` + `Pillow` | Download, validate, resize before committing |
| PR automation | `peter-evans/create-pull-request@v7` | Standard, handles branch dedup |
| Deploy | GitHub Pages (`actions/deploy-pages@v4`) | Zero cost, static-only |

---

## config.json Schema

```json
{
  "site": {
    "name": "My AI Blog",
    "description": "Automated long-form articles",
    "author": "AI Author",
    "url": "https://username.github.io/asd-site",
    "language": "en"
  },
  "generation": {
    "niche": "technology and software engineering",
    "topic_hints": ["AI", "developer tools", "open source", "cloud computing"],
    "tone": "informative and accessible",
    "post_length_words": 1200,
    "max_images": 3,
    "search_attempts": 10,
    "similarity_threshold": 0.70
  },
  "design": {
    "color_palette": {
      "primary": "#2563EB",
      "background": "#FFFFFF",
      "text": "#1F2937",
      "accent": "#F59E0B"
    },
    "font_family": "system-ui, sans-serif"
  }
}
```

---

## Post Schema

`posts/{id}/meta.json` (same shape as entries in `posts/index.json`):

```json
{
  "id": "2026-06-02-quantum-computing-basics",
  "title": "Quantum Computing Basics Explained",
  "slug": "quantum-computing-basics",
  "created_at": "2026-06-02T02:00:00Z",
  "author": "AI Author",
  "tags": ["technology", "quantum"],
  "excerpt": "A brief introduction to quantum computing...",
  "hero_image": "assets/hero.jpg"
}
```

`posts/index.json` is an array of these objects, sorted by `created_at` descending.

---

## Phase 1 — Implementation Details

### Scaffold (P1-02 to P1-03)

```bash
npm create astro@latest . -- --template minimal --typescript strict --no-git
npm install @astrojs/mdx
```

`astro.config.mjs`:
```js
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';

export default defineConfig({
  site: 'https://username.github.io',
  base: '/asd-site',
  integrations: [mdx()],
  output: 'static',
});
```

### Layouts

**BaseLayout.astro** — accepts `title: string` prop. Renders full HTML shell, imports `global.css`, includes `<Header>` and `<Footer>`, `<slot />` in `<main>`.

**PostLayout.astro** — accepts post metadata as props. Renders hero image (if `hero_image` present), article header with title/date/author, then `<slot />` for Markdown content.

### Components

**PostCard.astro** — props: `{ id, title, excerpt, created_at, tags, hero_image }`. Renders a card linking to `/posts/{id}`. Shows title, excerpt, formatted date, tag badges.

**TagBadge.astro** — props: `{ tag: string }`. Single styled pill.

**Header.astro** — site name from config or hardcoded constant, nav links (Home only in Phase 1).

**Footer.astro** — simple copyright line.

### Pages

**`src/pages/index.astro`**:
```astro
---
import postsIndex from '../../posts/index.json';
import PostCard from '../components/PostCard.astro';
import BaseLayout from '../layouts/BaseLayout.astro';

const posts = postsIndex.sort(
  (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
);
---
<BaseLayout title="Home">
  <div class="posts-grid">
    {posts.map(post => <PostCard {...post} />)}
  </div>
</BaseLayout>
```

**`src/pages/posts/[id].astro`**:
```astro
---
import { readFileSync } from 'fs';
import { join } from 'path';
import matter from 'gray-matter'; // or manual parse
import postsIndex from '../../../posts/index.json';
import PostLayout from '../../layouts/PostLayout.astro';

export async function getStaticPaths() {
  return postsIndex.map(post => ({ params: { id: post.id }, props: { meta: post } }));
}

const { id } = Astro.params;
const { meta } = Astro.props;

// Read markdown at build time (SSG — Node environment)
const rawMd = readFileSync(
  join(process.cwd(), 'posts', id, 'post.md'),
  'utf-8'
);
---
<!-- render rawMd via Astro's built-in markdown rendering or marked -->
```

Note: Astro's `Astro.glob()` alternative: `const allPosts = await Astro.glob('../../posts/*/post.md')` — match by folder name. Either approach works. The `fs.readFileSync` approach is more explicit for AI-generated content.

### Styles

`src/styles/global.css` — define CSS custom properties mapping to `config.json` design values. In Phase 1 these are hardcoded values; Phase 3 can generate them dynamically.

```css
:root {
  --color-primary: #2563EB;
  --color-bg: #FFFFFF;
  --color-text: #1F2937;
  --color-accent: #F59E0B;
  --font-family: system-ui, sans-serif;
}

body {
  font-family: var(--font-family);
  color: var(--color-text);
  background: var(--color-bg);
  line-height: 1.7;
}

article {
  max-width: 65ch;
  margin: 0 auto;
}
```

---

## Phase 2 — Implementation Details

### `scripts/ai_client.py`

```python
import os
import anthropic
import google.generativeai as genai

class ClaudeClient:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        msg = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return msg.content[0].text

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.model.generate_content(
            f"{system_prompt}\n\n{user_prompt}"
        )
        return response.text

def get_ai_client():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ClaudeClient()
    elif os.environ.get("GEMINI_API_KEY"):
        return GeminiClient()
    raise EnvironmentError("Set ANTHROPIC_API_KEY or GEMINI_API_KEY")
```

### `scripts/search_topic.py`

Key function: `find_unique_topic(config, existing_posts, max_attempts=10)`

- Build query from `config["generation"]["niche"]` + random item from `topic_hints`
- Call `TavilyClient(api_key=...).search(query, search_depth="advanced", max_results=5)`
- For each candidate title, check similarity against all existing post titles using `difflib.SequenceMatcher`
- If similarity > `similarity_threshold` (default 0.70) → treat as duplicate
- On duplicate: retry with modified query (add "NOT {topic}", rotate topic hints)
- After `max_attempts`: raise `TopicExhaustedError`
- Return: `(topic_string, tavily_context_list)`

### `scripts/research_topic.py`

Key function: `research_topic(topic, config) -> dict`

- Run 3 Tavily searches: `"{topic}"`, `"how does {topic} work"`, `"{topic} latest developments"`
- Collect all results, deduplicate by URL
- Concatenate content snippets, truncate to ~8000 chars
- Return: `{ "topic": str, "sources": list[dict], "combined_text": str }`

### `scripts/write_post.py`

Key function: `generate_post_content(research_bundle, config) -> dict`

System prompt built from config:
```
You are a {tone} writer specialising in {niche}.
Write in {language}. Target audience: curious non-experts.
```

User prompt:
```
Write a blog post about: {topic}

Target length: {post_length_words} words.
Use these research sources (cite inline as Markdown links):

{combined_text}

Sources:
{source_urls}

End your response with a JSON block (between ```json and ```) containing:
{ "title": "...", "slug": "url-safe-slug", "excerpt": "1-2 sentences", 
  "tags": ["tag1", "tag2"], "image_queries": ["query1", "query2"] }
```

Parse the JSON block from the response. If parse fails, run a second AI call to extract metadata.

Return: `{ "markdown_body": str, "title": str, "slug": str, "excerpt": str, "tags": list, "image_queries": list }`

### `scripts/download_images.py`

Key function: `download_images(image_queries, assets_dir, max_images=3) -> list[str]`

- For each query: Tavily search with `include_images=True`
- Filter URLs to jpg/jpeg/png/webp extensions
- Download with `requests` (User-Agent header, 10s timeout)
- Open with Pillow, validate it's a real image
- Resize to max 1200px wide, maintain aspect ratio
- Save as `{assets_dir}/image-{n}.jpg`
- Catch all errors gracefully (missing images are not fatal)
- Return list of saved filenames

### `scripts/update_index.py`

Key function: `update_index(posts_dir, new_entry)`

- Read `posts/index.json`
- Append new entry
- Sort by `created_at` descending
- Write back with `indent=2`

### `scripts/generate_post.py` — Orchestrator

```python
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path
from slugify import slugify

from search_topic import find_unique_topic, TopicExhaustedError
from research_topic import research_topic
from write_post import generate_post_content
from download_images import download_images
from update_index import update_index

def main():
    config = json.loads(Path("config.json").read_text())
    index = json.loads(Path("posts/index.json").read_text())

    try:
        topic, context = find_unique_topic(config, index)
    except TopicExhaustedError:
        print("No unique topic found after 10 attempts. Skipping.")
        sys.exit(0)

    research = research_topic(topic, config)
    post_data = generate_post_content(research, config)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    post_id = f"{today}-{post_data['slug']}"
    post_dir = Path("posts") / post_id
    assets_dir = post_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    (post_dir / "post.md").write_text(post_data["markdown_body"])

    images = download_images(post_data["image_queries"], assets_dir)

    meta = {
        "id": post_id,
        "title": post_data["title"],
        "slug": post_data["slug"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "author": config["site"]["author"],
        "tags": post_data["tags"],
        "excerpt": post_data["excerpt"],
        "hero_image": f"assets/{images[0]}" if images else None,
    }
    (post_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    update_index("posts", meta)

    # Write outputs for GitHub Actions
    github_env = os.environ.get("GITHUB_ENV", os.devnull)
    with open(github_env, "a") as f:
        f.write(f"POST_TITLE={meta['title']}\n")
        f.write(f"POST_TAGS={','.join(meta['tags'])}\n")

    print(f"Generated: {post_id}")

if __name__ == "__main__":
    main()
```

### `.github/workflows/generate-post.yml`

```yaml
name: Generate Daily Post

on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r scripts/requirements.txt

      - name: Generate post
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          TAVILY_API_KEY: ${{ secrets.TAVILY_API_KEY }}
        run: python scripts/generate_post.py

      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v7
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "feat: add AI-generated post"
          branch: ai-post/${{ github.run_id }}
          title: "AI Post: ${{ env.POST_TITLE }}"
          body: |
            Automated post generated by the AI blog generator.

            **Topic**: ${{ env.POST_TITLE }}
            **Tags**: ${{ env.POST_TAGS }}

            Review the content and images before merging.
          labels: ai-generated,content
          delete-branch: true
```

### `.github/workflows/deploy.yml`

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm

      - run: npm ci
      - run: npm run build

      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist/
      - uses: actions/deploy-pages@v4
        id: deployment
```

---

## How Phases Connect

```
Phase 2 (Python + GitHub Actions)
  writes → posts/{id}/post.md
  writes → posts/{id}/meta.json
  writes → posts/{id}/assets/*
  updates → posts/index.json
                ↓
        git commit + PR → merge to main
                ↓
Phase 1 (Astro build, triggered by deploy.yml)
  reads ← posts/index.json       (index page)
  reads ← posts/{id}/post.md     (post content)
  reads ← posts/{id}/meta.json   (metadata)
  copies ← posts/{id}/assets/*   (images → dist/)
                ↓
        GitHub Pages serves dist/
```

The interface contract: `meta.json` schema. Both phases must honour it. Any schema change requires coordinated update to both Astro templates and Python scripts.

---

## GitHub Repository Setup

Before Phase 1 deploy works:
1. Create repo on GitHub, push main branch
2. Settings → Pages → Source: **GitHub Actions**
3. Settings → Actions → General → Workflow permissions: **Read and write** + **Allow Actions to create PRs**

Before Phase 2 works:
4. Settings → Secrets → Add: `TAVILY_API_KEY`
5. Settings → Secrets → Add: `ANTHROPIC_API_KEY` and/or `GEMINI_API_KEY`

---

## Extension Points

| Hook | Future use |
|---|---|
| `config.json` `design.color_palette` | Phase 3: inject as CSS variables at build time |
| `meta.json` `status` field | Editorial draft/published filter |
| `src/pages/tags/[tag].astro` | Tag index pages (data already in every post) |
| `post.md` → MDX | Interactive components in posts |
| `scripts/ai_client.py` | Add OpenAI or other providers following same interface |
| `scripts/` | Newsletter sender, social media poster, SEO optimizer |
