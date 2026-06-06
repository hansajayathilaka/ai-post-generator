import os
import random
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logger import RunLogger


class TopicExhaustedError(Exception):
    pass


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _is_duplicate(candidate: str, existing_titles: list[str], threshold: float) -> bool:
    return any(_similarity(candidate, title) >= threshold for title in existing_titles)


def _search_with_gemini(query: str, model_name: str) -> list[dict]:
    from google import genai
    from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    prompt = f"""Search for recent news and articles about: {query}

Return a list of 5 recent, specific article titles about this topic. Each title should be concrete and newsworthy.
Format: Return only the titles, one per line, no numbering or bullets."""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=GenerateContentConfig(
            tools=[Tool(google_search=GoogleSearch())],
        ),
    )

    sources: list[dict] = []
    seen_titles: set[str] = set()

    # Prefer grounding chunk titles (they come from actual search results)
    candidate = response.candidates[0]
    grounding = candidate.grounding_metadata
    if grounding and grounding.grounding_chunks:
        for chunk in grounding.grounding_chunks:
            web = getattr(chunk, "web", None)
            if web and getattr(web, "title", None):
                title = web.title
                if title not in seen_titles:
                    seen_titles.add(title)
                    sources.append({"title": title, "url": getattr(web, "uri", "")})

    # Fall back to response text lines if grounding returned nothing
    if not sources:
        for line in (response.text or "").strip().split("\n"):
            line = line.strip()
            if line and len(line) > 10 and line not in seen_titles:
                seen_titles.add(line)
                sources.append({"title": line, "url": ""})

    return sources


def _search_with_tavily(query: str) -> list[dict]:
    from tavily import TavilyClient

    client = TavilyClient()
    results = client.search(query, search_depth="advanced", max_results=5)
    return results.get("results", [])


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

    provider = gen.get("research_provider", "tavily").lower()
    use_gemini = provider == "gemini" and bool(os.environ.get("GEMINI_API_KEY"))
    model_name = gen.get("research_model", "gemini-2.0-flash")

    existing_titles = [p["title"] for p in existing_posts]
    used_hints: set[str] = set()

    for attempt in range(max_attempts):
        available = [h for h in hints if h not in used_hints] or hints
        hint = random.choice(available)
        used_hints.add(hint)

        query = f"{niche}: {hint} latest developments {current_year}"
        print(f"[search_topic] Query: {query}")

        if use_gemini:
            print(f"[search_topic] Using Gemini search grounding ({model_name})")
            candidates = _search_with_gemini(query, model_name)
        else:
            candidates = _search_with_tavily(query)

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
