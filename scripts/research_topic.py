import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logger import RunLogger


def _research_with_gemini(topic: str, model_name: str, logger: "RunLogger | None") -> dict:
    from google import genai
    from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    prompt = f"""Research the following topic for a technical blog post targeting software developers.

Topic: {topic}
Today's date: {today}

Provide a comprehensive research summary covering:
- What it is and how it works
- Latest developments and announcements as of {today}
- Key technical details and architectural insights
- Real-world adoption and use cases in the developer community

Base everything on current, authoritative sources."""

    print(f"[research_topic] Gemini grounding query: {topic}")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=GenerateContentConfig(
            tools=[Tool(google_search=GoogleSearch())],
        ),
    )

    # Extract sources from grounding metadata
    sources: list[dict] = []
    seen_urls: set[str] = set()
    candidate = response.candidates[0]
    grounding = candidate.grounding_metadata
    if grounding and grounding.grounding_chunks:
        for chunk in grounding.grounding_chunks:
            web = getattr(chunk, "web", None)
            if web and getattr(web, "uri", None):
                url = web.uri
                if url not in seen_urls:
                    seen_urls.add(url)
                    sources.append({
                        "url": url,
                        "title": getattr(web, "title", None) or url,
                        "content": "",
                    })

    combined_text = response.text or ""
    if len(combined_text) > 8000:
        combined_text = combined_text[:8000]

    print(f"[research_topic] Gemini grounding: {len(sources)} sources for: {topic}")

    queries = [topic]
    if logger:
        logger.log_research(queries, sources, len(combined_text))

    return {"topic": topic, "sources": sources, "combined_text": combined_text}


def _research_with_tavily(topic: str, logger: "RunLogger | None") -> dict:
    from tavily import TavilyClient

    client = TavilyClient()
    queries = [
        topic,
        f"how does {topic} work",
        f"{topic} latest developments",
    ]

    seen_urls: set[str] = set()
    all_sources: list[dict] = []
    snippets: list[str] = []

    for query in queries:
        print(f"[research_topic] Tavily query: {query}")
        try:
            results = client.search(query, search_depth="advanced", max_results=5)
            for item in results.get("results", []):
                url = item.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_sources.append({
                        "url": url,
                        "title": item.get("title", ""),
                        "content": item.get("content", ""),
                    })
                    if item.get("content"):
                        snippets.append(item["content"])
        except (ValueError, ConnectionError, TimeoutError, RuntimeError) as e:
            print(f"[research_topic] Tavily search failed for '{query}': {e}")

    combined_text = "\n\n".join(snippets)
    if len(combined_text) > 8000:
        combined_text = combined_text[:8000]

    print(f"[research_topic] Tavily: {len(all_sources)} unique sources for: {topic}")

    if logger:
        logger.log_research(queries, all_sources, len(combined_text))

    return {"topic": topic, "sources": all_sources, "combined_text": combined_text}


def research_topic(topic: str, config: dict, logger: "RunLogger | None" = None) -> dict:
    gen = config["generation"]
    provider = gen.get("research_provider", "tavily").lower()

    if provider == "gemini" and os.environ.get("GEMINI_API_KEY"):
        model_name = gen.get("research_model", "gemini-2.0-flash")
        print(f"[research_topic] Using Gemini Search Grounding ({model_name})")
        try:
            return _research_with_gemini(topic, model_name, logger)
        except (ValueError, ConnectionError, TimeoutError, RuntimeError, OSError) as e:
            print(f"[research_topic] Gemini grounding failed ({e}), falling back to Tavily")

    return _research_with_tavily(topic, logger)
