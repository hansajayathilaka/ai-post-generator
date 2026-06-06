"""Rebuild posts/index.json from all posts/*/meta.json files.

Run this before the Astro build so index.json is always in sync with
the post directories, without requiring individual PRs to touch it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from update_index import rebuild_index

if __name__ == "__main__":
    posts_dir = Path(__file__).parent.parent / "posts"
    rebuild_index(posts_dir)
