# Task List

Track implementation progress here. Check off tasks as they're completed.
Use `/next-task` slash command to get guided to the next step.

---

## Phase 1 — Static Site (Astro)

> Goal: Working blog site deployed to GitHub Pages. Posts read from `posts/` folder.

- [x] P1-01: `git init` + `.gitignore`
- [x] P1-02: `npm create astro@latest . -- --template minimal --typescript strict --no-git`
- [x] P1-03: `npm install @astrojs/mdx` + configure `astro.config.mjs`
- [x] P1-04: `src/layouts/BaseLayout.astro` — HTML shell, accepts `title` prop, imports global.css
- [x] P1-05: `src/layouts/PostLayout.astro` — hero image, title/date/author header, `<slot />`
- [x] P1-06: `src/components/PostCard.astro` — card with title, excerpt, date, tags, link
- [x] P1-07: `src/components/TagBadge.astro` — styled tag pill
- [x] P1-08: `src/components/Header.astro` + `src/components/Footer.astro`
- [x] P1-09: `src/styles/global.css` — CSS custom properties for design.color_palette, typography
- [x] P1-10: `src/pages/index.astro` — import posts/index.json, sort by date, render PostCards
- [x] P1-11: `src/pages/posts/[id].astro` — getStaticPaths from index.json, fs.readFileSync post.md + meta.json
- [x] P1-12: `posts/index.json` — initial empty array `[]`
- [x] P1-13: Sample post: `posts/2026-06-02-hello-world/` with meta.json, post.md, assets/
- [x] P1-14: Add sample post entry to `posts/index.json`
- [x] P1-15: `config.json` — initial values (site name, niche, color palette, etc.)
- [x] P1-16: `public/favicon.svg`
- [x] P1-17: `.github/workflows/deploy.yml` — build + deploy to GitHub Pages on push to main
- [x] P1-18: Smoke test: `npm run build` passes, `npm run preview` shows posts

**Phase 1 complete when:** Site builds cleanly, index page lists posts, clicking a post shows full content.

---

## Phase 2 — AI Generation (GitHub Actions + Python)

> Goal: Nightly GitHub Action generates a post, opens PR. Merging PR triggers deploy.

- [x] P2-01: `scripts/requirements.txt` — anthropic, google-generativeai, tavily-python, requests, Pillow, python-slugify
- [x] P2-02: `scripts/ai_client.py` — unified provider abstraction (Claude or Gemini based on env vars)
- [x] P2-03: `scripts/search_topic.py` — Tavily topic search + duplicate check with difflib, `TopicExhaustedError`
- [x] P2-04: `scripts/research_topic.py` — multi-source Tavily research, returns combined_text + sources
- [x] P2-05: `scripts/write_post.py` — AI content generation, returns markdown_body + metadata JSON
- [x] P2-06: `scripts/download_images.py` — Tavily image search, download + resize with Pillow
- [x] P2-07: `scripts/update_index.py` — append to posts/index.json, sort by date, write back
- [x] P2-08: `scripts/generate_post.py` — main orchestrator, writes $GITHUB_ENV vars
- [x] P2-09: `.github/workflows/generate-post.yml` — nightly cron + workflow_dispatch, opens PR
- [ ] P2-10: Local end-to-end test with real API keys
- [ ] P2-11: Add GitHub Secrets: `ANTHROPIC_API_KEY` and/or `GEMINI_API_KEY`, `TAVILY_API_KEY`
- [ ] P2-12: Trigger `workflow_dispatch` → verify PR opens with new post
- [ ] P2-13: Merge test PR → verify deploy.yml runs and live site updates

**Phase 2 complete when:** Nightly action runs without errors, PR is created with valid post content, merging deploys to GitHub Pages.

---

## Notes

- P1-02 requires Node.js — run `npm create astro@latest . -- --template minimal --typescript strict --no-git` in project root
- P2-10 requires at least one AI key + Tavily key in local environment
- GitHub repo must be created and connected before P1-17 test and P2-11
