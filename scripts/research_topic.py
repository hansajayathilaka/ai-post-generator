from tavily import TavilyClient


def research_topic(topic: str, config: dict) -> dict:
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
        try:
            results = client.search(query, search_depth="advanced", max_results=5)
            for item in results.get("results", []):
                url = item.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_sources.append({"url": url, "title": item.get("title", ""), "content": item.get("content", "")})
                    if item.get("content"):
                        snippets.append(item["content"])
        except Exception as e:
            print(f"[research_topic] Search failed for '{query}': {e}")

    combined_text = "\n\n".join(snippets)
    if len(combined_text) > 8000:
        combined_text = combined_text[:8000]

    print(f"[research_topic] Gathered {len(all_sources)} unique sources for: {topic}")
    return {"topic": topic, "sources": all_sources, "combined_text": combined_text}
