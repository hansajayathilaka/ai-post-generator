import json
from datetime import datetime, timezone
from pathlib import Path


class RunLogger:
    def __init__(self):
        self._log: dict = {
            "run_at": datetime.now(timezone.utc).isoformat(),
            "topic": "",
            "topic_search": {},
            "research": {},
            "generation": {},
            "post": {},
        }

    def log_topic_search(self, query: str, attempt: int, topic: str, candidates: list[dict]) -> None:
        self._log["topic"] = topic
        self._log["topic_search"] = {
            "query": query,
            "attempt": attempt,
            "topic": topic,
            "candidates": [{"title": c.get("title", ""), "url": c.get("url", "")} for c in candidates],
        }

    def log_research(self, queries: list[str], sources: list[dict], combined_text_len: int) -> None:
        self._log["research"] = {
            "queries": queries,
            "sources_count": len(sources),
            "sources": [{"title": s.get("title", ""), "url": s.get("url", "")} for s in sources],
            "combined_text_chars": combined_text_len,
        }

    def log_generation(self, model: str, system_prompt: str, user_prompt: str, response_chars: int) -> None:
        self._log["generation"] = {
            "model": model,
            "system_prompt": system_prompt,
            "user_prompt_chars": len(user_prompt),
            "response_chars": response_chars,
        }

    def log_post(self, title: str, slug: str, tags: list[str], excerpt: str) -> None:
        self._log["post"] = {
            "title": title,
            "slug": slug,
            "tags": tags,
            "excerpt": excerpt,
        }

    def save(self, post_dir: Path) -> Path:
        path = post_dir / "run_log.json"
        path.write_text(json.dumps(self._log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[logger] Run log saved to {path}")
        return path

    def write_pr_body(self, post_id: str, path: Path) -> None:
        post = self._log["post"]
        gen = self._log["generation"]
        research = self._log["research"]
        search = self._log["topic_search"]

        sources_md = "\n".join(
            f"{i + 1}. [{s['title'] or s['url']}]({s['url']})"
            for i, s in enumerate(research.get("sources", []))
            if s.get("url")
        )

        candidates_md = "\n".join(
            f"- {c['title']}" for c in search.get("candidates", []) if c.get("title")
        )

        body = f"""## AI Post Review

**Post ID**: `{post_id}`
**Title**: {post.get('title', '')}
**Excerpt**: {post.get('excerpt', '')}
**Tags**: {', '.join(f'`{t}`' for t in post.get('tags', []))}

---

### Generation Details

| Field | Value |
|---|---|
| Run at | `{self._log['run_at']}` |
| Model | `{gen.get('model', 'unknown')}` |
| Discovered topic | {search.get('topic', '')} |
| Topic search query | `{search.get('query', '')}` |
| Topic found on attempt | {search.get('attempt', '?')} |
| Research sources | {research.get('sources_count', 0)} unique URLs |
| Research text fed to LLM | {research.get('combined_text_chars', 0):,} chars |
| LLM user prompt | {gen.get('user_prompt_chars', 0):,} chars |
| LLM response | {gen.get('response_chars', 0):,} chars |

---

### Topic Search Candidates

{candidates_md or '_none_'}

---

### Research Sources ({research.get('sources_count', 0)})

{sources_md or '_none_'}

---

### Research Queries

{chr(10).join(f'- `{q}`' for q in research.get('queries', []))}

---

> Full details in `posts/{post_id}/run_log.json`. Review the content and images before merging — merging triggers a deploy to GitHub Pages.
"""
        path.write_text(body, encoding="utf-8")
        print(f"[logger] PR body written to {path}")

    @property
    def topic(self) -> str:
        return self._log.get("topic", "")

    @property
    def sources(self) -> list[dict]:
        return self._log.get("research", {}).get("sources", [])

    @property
    def model(self) -> str:
        return self._log.get("generation", {}).get("model", "unknown")

    @property
    def sources_count(self) -> int:
        return self._log.get("research", {}).get("sources_count", 0)
