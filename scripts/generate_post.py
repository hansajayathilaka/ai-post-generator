import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from slugify import slugify

# Allow importing sibling modules when run directly or via GitHub Actions
sys.path.insert(0, str(Path(__file__).parent))

from download_images import download_images
from research_topic import research_topic
from search_topic import TopicExhaustedError, find_unique_topic
from update_index import update_index
from write_post import generate_post_content


def main() -> None:
    repo_root = Path(__file__).parent.parent
    config = json.loads((repo_root / "config.json").read_text())
    posts_dir = repo_root / "posts"
    index = json.loads((posts_dir / "index.json").read_text())

    try:
        topic, _context = find_unique_topic(config, index)
    except TopicExhaustedError:
        print("No unique topic found — skipping generation.")
        sys.exit(0)

    research = research_topic(topic, config)
    post_data = generate_post_content(research, config)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    safe_slug = slugify(post_data["slug"])[:60]
    post_id = f"{today}-{safe_slug}"
    post_dir = posts_dir / post_id
    assets_dir = post_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    (post_dir / "post.md").write_text(post_data["markdown_body"], encoding="utf-8")

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

    github_env = os.environ.get("GITHUB_ENV", os.devnull)
    with open(github_env, "a") as f:
        f.write(f"POST_TITLE={meta['title']}\n")
        f.write(f"POST_ID={post_id}\n")
        f.write(f"POST_TAGS={','.join(meta['tags'])}\n")

    print(f"Generated: {post_id}")


if __name__ == "__main__":
    main()
