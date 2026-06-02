# Project Progress

## Current Status: Phase 2 — Scripts complete, awaiting API keys + GitHub Secrets

---

## Phase 1 — Static Site

| | |
|---|---|
| Started | 2026-06-02 |
| Completed | 2026-06-02 |
| Blocked on | — |

**All P1-01 through P1-18 complete.**

---

## Phase 2 — AI Generation

| | |
|---|---|
| Started | 2026-06-02 |
| Scripts complete | 2026-06-02 |
| Blocked on | GitHub Secrets (ANTHROPIC_API_KEY / GEMINI_API_KEY, TAVILY_API_KEY) |

**Completed so far:**
- [x] P2-01 through P2-09: All scripts and workflow created

**Remaining manual steps:**
- [ ] P2-10: Local end-to-end test (`python scripts/generate_post.py` with API keys in env)
- [ ] P2-11: Add GitHub Secrets: `ANTHROPIC_API_KEY` and/or `GEMINI_API_KEY`, `TAVILY_API_KEY`
- [ ] P2-12: Trigger `workflow_dispatch` → verify PR opens with new post
- [ ] P2-13: Merge test PR → verify deploy.yml runs and live site updates

---

## Session Log

### 2026-06-02 (session 1)

- Planned full architecture (see PLAN.md)
- Created project skeleton: .gitignore, CLAUDE.md, TASKS.md, PROGRESS.md, PLAN.md
- Created .claude/commands/ slash commands for guided development

### 2026-06-02 (session 2)

- Completed all Phase 1 tasks (P1-01 through P1-18)
- Redesigned site layout and components

### 2026-06-02 (session 3)

- Completed P2-01 through P2-09:
  - `scripts/requirements.txt`
  - `scripts/ai_client.py` — Claude (claude-sonnet-4-6) / Gemini (gemini-2.0-flash) abstraction
  - `scripts/search_topic.py` — Tavily topic search + difflib duplicate detection
  - `scripts/research_topic.py` — 3-query multi-source research
  - `scripts/write_post.py` — AI post generation + JSON metadata extraction
  - `scripts/download_images.py` — Tavily image search + Pillow resize → hero.jpg
  - `scripts/update_index.py` — idempotent index.json updater
  - `scripts/generate_post.py` — main orchestrator, writes GITHUB_ENV vars
  - `.github/workflows/generate-post.yml` — nightly cron (02:00 UTC) + workflow_dispatch
- **Resume from:** P2-10 (local test) — requires ANTHROPIC_API_KEY/GEMINI_API_KEY + TAVILY_API_KEY
