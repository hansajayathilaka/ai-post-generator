import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from slugify import slugify

sys.path.insert(0, str(Path(__file__).parent))

from config import load_config
from download_images import download_images
from logger import RunLogger
from research_topic import research_topic
from search_topic import TopicExhaustedError, find_unique_topic
from update_index import load_index_from_posts
from write_post import generate_post_content


def _write_post_files(
    post_dir: Path,
    assets_dir: Path,
    post_id: str,
    safe_slug: str,
    post_data: dict,
    research: dict,
    config: dict,
) -> dict:
    """Write post.md, sources.json, downloaded images, and meta.json. Returns the meta dict."""
    (post_dir / "post.md").write_text(post_data["markdown_body"], encoding="utf-8")

    sources_json = [
        {"title": s.get("title", ""), "url": s.get("url", "")}
        for s in research["sources"]
        if s.get("url")
    ]
    (post_dir / "sources.json").write_text(
        json.dumps(sources_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    images = download_images(
        post_data["image_queries"],
        assets_dir,
        config["generation"].get("max_images", 3),
    )

    meta = {
        "$schema": "../../schemas/meta.schema.json",
        "id": post_id,
        "title": post_data["title"],
        "slug": safe_slug,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "author": config["site"]["author"],
        "tags": post_data["tags"],
        "excerpt": post_data["excerpt"],
        "hero_image": f"assets/{images[0]}" if images else None,
    }
    (post_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    return meta


def _export_github_env(post_id: str, meta: dict, logger: RunLogger) -> None:
    """Write post metadata to GITHUB_ENV so the workflow can use them in the PR."""
    github_env = os.environ.get("GITHUB_ENV", os.devnull)
    with open(github_env, "a", encoding="utf-8") as f:
        f.write(f"POST_TITLE={meta['title']}\n")
        f.write(f"POST_ID={post_id}\n")
        f.write(f"POST_TAGS={','.join(meta['tags'])}\n")
        f.write(f"POST_MODEL={logger.model}\n")
        f.write(f"POST_TOPIC={logger.topic}\n")
        f.write(f"RESEARCH_SOURCES_COUNT={logger.sources_count}\n")


def main() -> None:
    repo_root = Path(__file__).parent.parent
    config = load_config()
    posts_dir = repo_root / "posts"
    index = load_index_from_posts(posts_dir)
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

    meta = _write_post_files(post_dir, assets_dir, post_id, safe_slug, post_data, research, config)

    logger.log_post(meta["title"], meta["slug"], meta["tags"], meta["excerpt"])
    logger.save(post_dir)
    logger.write_pr_body(post_id, Path("/tmp/pr_body.md"))

    _export_github_env(post_id, meta, logger)
    print(f"Generated: {post_id}")


if __name__ == "__main__":
    main()
