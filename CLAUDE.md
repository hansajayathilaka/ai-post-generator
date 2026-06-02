# asd-site — Project Context

## What This Is

Git-based AI blog generator. Two phases:

- **Phase 1**: Static blog site built from markdown files using Astro 5. Posts live in `posts/` as folders. Manual or AI-generated content.
- **Phase 2**: Nightly GitHub Actions pipeline that uses Claude or Gemini + Tavily to discover topics, research them, generate posts, and open PRs. Merging the PR triggers deployment.

No CMS. No database. The git repo IS the content store.

## Directory Layout

```
posts/                    ← content layer (shared between Phase 1 and Phase 2)
  index.json              ← master post list, sorted by created_at desc
  {YYYY-MM-DD-slug}/
    meta.json
    post.md
    assets/

scripts/                  ← Phase 2 Python scripts (run in GitHub Actions only)
src/                      ← Astro frontend (Phase 1)
  components/
  layouts/
  pages/
  styles/
.github/workflows/        ← generate-post.yml + deploy.yml
.claude/commands/         ← Claude Code slash commands
config.json               ← site + AI generation config (source of truth)
```

## Phase Boundary

Phase 2 scripts write ONLY to `posts/`. Astro build reads ONLY from `posts/`. No cross-imports. The contract between phases is the `meta.json` schema.

## Key Schemas

### posts/index.json entry (= meta.json)
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

### config.json top-level fields
- `site`: name, description, author, url, language
- `generation`: niche, topic_hints, tone, post_length_words, max_images, search_attempts, similarity_threshold
- `design`: color_palette (primary/background/text/accent), font_family

## Running Locally

```bash
# Phase 1 — frontend dev
npm install
npm run dev          # http://localhost:4321
npm run build        # outputs to dist/
npm run preview      # serve dist/ locally

# Phase 2 — post generation (requires API keys)
pip install -r scripts/requirements.txt
python scripts/generate_post.py
```

## Required Environment Variables

At least one AI provider key required:

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API (preferred if set) |
| `GEMINI_API_KEY` | Gemini API (fallback if Claude not set) |
| `TAVILY_API_KEY` | Web search for topic discovery + research |

## Task and Progress Files

- [TASKS.md](TASKS.md) — ordered checkbox task list for both phases
- [PROGRESS.md](PROGRESS.md) — milestone tracking, last session notes
- [PLAN.md](PLAN.md) — full architecture plan with implementation details

## Slash Commands

| Command | What it does |
|---|---|
| `/next-task` | Show next unchecked task |
| `/phase1` | Show Phase 1 status + next task |
| `/phase2` | Show Phase 2 status + next task |
| `/generate-post` | Run post generation script locally |

## Tech Stack

- **Astro 5** — static site generator
- **@astrojs/mdx** — MDX support
- **anthropic** Python SDK — Claude generation
- **google-generativeai** Python SDK — Gemini generation
- **tavily-python** — web search
- **Pillow** — image download + resize
- **peter-evans/create-pull-request@v7** — GitHub Action for PR creation
- **GitHub Pages** (`actions/deploy-pages@v4`) — hosting
