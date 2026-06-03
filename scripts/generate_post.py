import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from slugify import slugify

# Allow importing sibling modules when run directly or via GitHub Actions
sys.path.insert(0, str(Path(__file__).parent))

from config import load_config
from download_images import download_images
from logger import RunLogger
from research_topic import research_topic
from search_topic import TopicExhaustedError, find_unique_topic
from update_index import load_index, update_index
from write_post import generate_post_content


def _build_sources_section(sources: list[dict]) -> str:
    lines = []
    for i, s in enumerate(sources, 1):
        url = s.get("url", "")
        title = s.get("title", "") or url
        if url:
            lines.append(f"{i}. [{title}]({url})")
    if not lines:
        return ""
    return "\n\n---\n\n## Sources\n\n" + "\n".join(lines) + "\n"


def main() -> None:
    repo_root = Path(__file__).parent.parent
    config = load_config()
    posts_dir = repo_root / "posts"
    index = load_index(posts_dir)
    logger = RunLogger()

    try:
        topic, _context = find_unique_topic(config, index, logger=logger)
    except TopicExhaustedError:
        print("No unique topic found — skipping generation.")
        sys.exit(0)

    research = research_topic(topic, config, logger=logger)
    post_data = generate_post_content(research, config, logger=logger)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    safe_slug = slugify(post_data["slug"])[:60]
    post_id = f"{today}-{safe_slug}"
    post_dir = posts_dir / post_id
    assets_dir = post_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Append sources bibliography to the end of the post
    sources_section = _build_sources_section(research["sources"])
    full_markdown = post_data["markdown_body"] + sources_section
    (post_dir / "post.md").write_text(full_markdown, encoding="utf-8")

    # Save sources as structured JSON for programmatic use
    sources_json = [
        {"title": s.get("title", ""), "url": s.get("url", "")}
        for s in research["sources"]
        if s.get("url")
    ]
    (post_dir / "sources.json").write_text(
        json.dumps(sources_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    max_images = config["generation"].get("max_images", 3)
    images = download_images(post_data["image_queries"], assets_dir, max_images)

    meta = {
        "id": post_id,
        "title": post_data["title"],
        "slug": safe_slug,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "author": config["site"]["author"],
        "tags": post_data["tags"],
        "excerpt": post_data["excerpt"],
        "hero_image": f"assets/{images[0]}" if images else None,
    }
    (post_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")

    update_index(posts_dir, meta)

    logger.log_post(meta["title"], meta["slug"], meta["tags"], meta["excerpt"])
    logger.save(post_dir)

    # Write rich PR body for the workflow to use
    pr_body_path = Path("/tmp/pr_body.md")
    logger.write_pr_body(post_id, pr_body_path)

    github_env = os.environ.get("GITHUB_ENV", os.devnull)
    with open(github_env, "a") as f:
        f.write(f"POST_TITLE={meta['title']}\n")
        f.write(f"POST_ID={post_id}\n")
        f.write(f"POST_TAGS={','.join(meta['tags'])}\n")
        f.write(f"POST_MODEL={logger.model}\n")
        f.write(f"POST_TOPIC={logger.topic}\n")
        f.write(f"RESEARCH_SOURCES_COUNT={logger.sources_count}\n")

    print(f"Generated: {post_id}")


if __name__ == "__main__":
    main()
