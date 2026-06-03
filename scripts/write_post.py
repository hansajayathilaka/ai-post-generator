import json
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from ai_client import get_ai_client

if TYPE_CHECKING:
    from logger import RunLogger


def _extract_json_block(text: str) -> dict | None:
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Fallback: try to find a raw JSON object at the end
    match = re.search(r"\{[^{}]*\"title\"[^{}]*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def _extract_metadata_via_ai(client, text: str) -> dict:
    prompt = (
        "Extract the blog post metadata from the following text and return ONLY a JSON object "
        "with keys: title, slug, excerpt, tags (array), image_queries (array). "
        "No explanation, just the JSON.\n\n" + text[:3000]
    )
    response = client.generate("You are a JSON extraction assistant.", prompt)
    raw = re.sub(r"```json|```", "", response).strip()
    return json.loads(raw)


def generate_post_content(
    research_bundle: dict,
    config: dict,
    logger: "RunLogger | None" = None,
) -> dict:
    gen = config["generation"]
    site = config["site"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    system_prompt = (
        f"Today's date is {today}. "
        f"You are a {gen['tone']} writer specialising in {gen['niche']}. "
        f"Write in {site.get('language', 'en')}. "
        "Target audience: software developers who follow the latest tools and techniques. "
        "When writing about recent developments, treat the research sources as ground truth for "
        "current facts — do not rely on your training data for recency claims."
    )

    source_urls = "\n".join(
        f"- [{s['title']}]({s['url']})" for s in research_bundle["sources"] if s.get("url")
    )

    user_prompt = f"""Write a blog post about: {research_bundle['topic']}

Today's date: {today}
Target length: {gen['post_length_words']} words.
Use the research content below to inform the post. Cite sources inline as Markdown links where relevant. Do NOT include a Sources, References, or Further Reading section at the end.

{research_bundle['combined_text']}

Sources (for inline citations only):
{source_urls}

After the article, append a JSON block (between ```json and ```) containing:
{{
  "title": "A compelling headline",
  "slug": "url-safe-slug-no-date",
  "excerpt": "1-2 sentence summary for the post card",
  "tags": ["tag1", "tag2", "tag3"],
  "image_queries": ["descriptive image search query 1", "descriptive image search query 2"]
}}"""

    client = get_ai_client()
    response = client.generate(system_prompt, user_prompt)

    if logger:
        logger.log_generation(client.model_name, system_prompt, user_prompt, len(response))

    metadata = _extract_json_block(response)
    if not metadata:
        print("[write_post] JSON block not found in response, running fallback extraction...")
        metadata = _extract_metadata_via_ai(client, response)

    # Strip the trailing JSON block from the markdown body
    markdown_body = re.sub(r"```json.*?```", "", response, flags=re.DOTALL).strip()

    return {
        "markdown_body": markdown_body,
        "title": metadata.get("title", research_bundle["topic"]),
        "slug": metadata.get("slug", "post"),
        "excerpt": metadata.get("excerpt", ""),
        "tags": metadata.get("tags", []),
        "image_queries": metadata.get("image_queries", [research_bundle["topic"]]),
    }
