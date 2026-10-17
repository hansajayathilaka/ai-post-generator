"""Anonymous Parallel Search MCP adapter for the synchronous generation pipeline."""

import asyncio
from datetime import timedelta
from uuid import uuid4

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_URL = "https://search.parallel.ai/mcp"
USER_AGENT = "ai-post-generator/0.0.1 (Parallel research)"
REQUEST_TIMEOUT = 45
# Reuse one identifier across discovery and research in this generation process.
SESSION_ID = str(uuid4())


async def _search(objective: str, queries: list[str]) -> list[dict]:
    async with asyncio.timeout(REQUEST_TIMEOUT):
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=30,
        ) as client:
            async with streamable_http_client(MCP_URL, http_client=client) as (read, write, _):
                async with ClientSession(
                    read, write, read_timeout_seconds=timedelta(seconds=REQUEST_TIMEOUT),
                ) as session:
                    await session.initialize()
                    result = await session.call_tool("web_search", {
                        "objective": objective,
                        "search_queries": queries,
                        "session_id": SESSION_ID,
                    })
                    if result.isError:
                        message = " ".join(
                            block.text for block in result.content if block.type == "text"
                        )
                        raise RuntimeError(f"Parallel search failed: {message}")
                    payload = result.structuredContent
                    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                        raise ValueError("Parallel search returned no structured results")

                    sources = []
                    seen_urls = set()
                    for item in payload["results"]:
                        if not isinstance(item, dict):
                            raise ValueError("Invalid Parallel search result")
                        url = item.get("url")
                        excerpts = item.get("excerpts")
                        title = item.get("title")
                        if (not isinstance(url, str) or not url.startswith(("https://", "http://"))
                                or not isinstance(excerpts, list)
                                or any(not isinstance(text, str) for text in excerpts)
                                or title is not None and not isinstance(title, str)):
                            raise ValueError("Invalid Parallel search source")
                        if url not in seen_urls:
                            seen_urls.add(url)
                            sources.append({
                                "url": url, "title": title or url,
                                "content": "\n\n".join(excerpts),
                            })
                    return sources


def search_parallel(objective: str, queries: list[str]) -> list[dict]:
    """Return the existing title/url/content source shape, or stop on failure.

    Explicit Parallel selection never falls back to a different provider.
    Cancellation and KeyboardInterrupt propagate; transport errors stop the run.
    """
    try:
        return asyncio.run(_search(objective, queries))
    except Exception as exc:
        # HTTP/MCP context managers may nest the actual error in task groups.
        # Keep actionable service errors (including rate limits) visible.
        cause = exc
        while isinstance(cause, ExceptionGroup) and len(cause.exceptions) == 1:
            cause = cause.exceptions[0]
        raise RuntimeError(f"Parallel research unavailable: {cause}") from exc
