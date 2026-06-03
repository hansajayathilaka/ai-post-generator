import random
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import TYPE_CHECKING

from tavily import TavilyClient

if TYPE_CHECKING:
    from logger import RunLogger


class TopicExhaustedError(Exception):
    pass


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _is_duplicate(candidate: str, existing_titles: list[str], threshold: float) -> bool:
    return any(_similarity(candidate, title) >= threshold for title in existing_titles)


def find_unique_topic(
    config: dict,
    existing_posts: list[dict],
    logger: "RunLogger | None" = None,
) -> tuple[str, list[dict]]:
    gen = config["generation"]
    niche = gen["niche"]
    hints = list(gen["topic_hints"])
    threshold = gen.get("similarity_threshold", 0.85)
    max_attempts = gen.get("search_attempts", 5)
    current_year = datetime.now(timezone.utc).year

    client = TavilyClient()
    existing_titles = [p["title"] for p in existing_posts]
    used_hints: set[str] = set()

    for attempt in range(max_attempts):
        available = [h for h in hints if h not in used_hints] or hints
        hint = random.choice(available)
        used_hints.add(hint)

        query = f"{niche}: {hint} latest developments {current_year}"
        print(f"[search_topic] Query: {query}")
        results = client.search(query, search_depth="advanced", max_results=5)
        candidates = results.get("results", [])

        for item in candidates:
            title = item.get("title", "")
            if not title:
                continue
            if not _is_duplicate(title, existing_titles, threshold):
                topic = title
                context = candidates
                print(f"[search_topic] Found unique topic on attempt {attempt + 1}: {topic}")
                if logger:
                    logger.log_topic_search(query, attempt + 1, topic, candidates)
                return topic, context

        print(f"[search_topic] Attempt {attempt + 1}: all candidates were duplicates, retrying...")

    raise TopicExhaustedError(f"No unique topic found after {max_attempts} attempts")
