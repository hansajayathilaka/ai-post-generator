import json
from pathlib import Path


def update_index(posts_dir: str | Path, new_entry: dict) -> None:
    index_path = Path(posts_dir) / "index.json"
    entries: list[dict] = json.loads(index_path.read_text())

    # Replace if same id already exists (idempotent re-run), otherwise append
    entries = [e for e in entries if e.get("id") != new_entry["id"]]
    entries.append(new_entry)
    entries.sort(key=lambda e: e.get("created_at", ""), reverse=True)

    index_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n")
    print(f"[update_index] index.json now has {len(entries)} entries")
