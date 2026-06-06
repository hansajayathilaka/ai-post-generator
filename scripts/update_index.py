import json
from pathlib import Path


def load_index(posts_dir: str | Path) -> list[dict]:
    return json.loads((Path(posts_dir) / "index.json").read_text())


def load_index_from_posts(posts_dir: str | Path) -> list[dict]:
    """Build the post list by scanning posts/*/meta.json directly.

    Used by the generate script so PRs never need to touch index.json.
    """
    posts_dir = Path(posts_dir)
    entries = []
    for meta_path in sorted(posts_dir.glob("*/meta.json")):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            entry = {k: v for k, v in data.items() if k != "$schema"}
            entries.append(entry)
        except (json.JSONDecodeError, OSError):
            pass
    entries.sort(key=lambda e: e.get("created_at", ""), reverse=True)
    return entries


def save_index(posts_dir: str | Path, entries: list[dict]) -> None:
    index_path = Path(posts_dir) / "index.json"
    index_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n")


def rebuild_index(posts_dir: str | Path) -> None:
    """Rebuild index.json from all posts/*/meta.json files."""
    entries = load_index_from_posts(posts_dir)
    save_index(posts_dir, entries)
    print(f"[update_index] Rebuilt index.json with {len(entries)} entries")


def update_index(posts_dir: str | Path, new_entry: dict) -> None:
    entries = load_index(posts_dir)

    # Replace if same id already exists (idempotent re-run), otherwise append
    entries = [e for e in entries if e.get("id") != new_entry["id"]]
    entry = {k: v for k, v in new_entry.items() if k != "$schema"}
    entries.append(entry)
    entries.sort(key=lambda e: e.get("created_at", ""), reverse=True)

    save_index(posts_dir, entries)
    print(f"[update_index] index.json now has {len(entries)} entries")
