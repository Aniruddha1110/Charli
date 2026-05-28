# web_search.py — Web search using ddgs + Ollama summarisation

import time
from ddgs import DDGS
from ai.ollama_client import ollama
from utils.logger import get_logger

logger = get_logger(__name__)


def search(query: str, max_results: int = 5) -> list[dict]:
    """Search DuckDuckGo web results."""
    logger.info(f"Searching: '{query}'")

    for attempt in range(3):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    query,
                    max_results=max_results,
                ))
            if results:
                return [{
                    "title":   r.get("title",   ""),
                    "url":     r.get("href",     ""),
                    "snippet": r.get("body",     ""),
                } for r in results]
        except Exception as e:
            logger.warning(f"Search attempt {attempt + 1} failed: {e}")
            time.sleep(1.5)

    logger.error("All search attempts failed")
    return []


def search_and_summarise(query: str, max_results: int = 5) -> dict:
    """Search + summarise with Ollama."""
    results = search(query, max_results=max_results)

    if not results:
        return {
            "query":   query,
            "results": [],
            "summary": (
                "I couldn't fetch live results right now. "
                "DuckDuckGo may be rate limiting. Try again in a moment."
            ),
        }

    context = "\n\n".join([
        f"[{i+1}] {r['title']}\n{r['snippet']}"
        for i, r in enumerate(results)
    ])

    prompt = f"""You are Charli, a helpful AI assistant.
The user searched for: "{query}"

Here are the top search results:

{context}

Provide a clear, concise summary that directly answers the user's query.
Keep it under 150 words. Be factual. Write naturally."""

    summary = ollama.prompt(prompt)

    return {
        "query":   query,
        "results": results,
        "summary": summary,
    }


def search_news(query: str, max_results: int = 5) -> list[dict]:
    """Search for recent news with rate limit handling."""
    logger.info(f"News search: '{query}'")

    for attempt in range(3):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(
                    query,
                    max_results=max_results,
                ))
            if results:
                return [{
                    "title":   r.get("title",  ""),
                    "url":     r.get("url",    ""),
                    "snippet": r.get("body",   ""),
                    "source":  r.get("source", ""),
                    "date":    r.get("date",   ""),
                } for r in results]
        except Exception as e:
            logger.warning(f"News attempt {attempt + 1} failed: {e}")
            time.sleep(2)

    # Fallback — use regular search with "news" appended
    logger.warning("News search failed, falling back to web search")
    results = search(f"{query} news today", max_results=max_results)
    return [{
        "title":   r["title"],
        "url":     r["url"],
        "snippet": r["snippet"],
        "source":  "",
        "date":    "",
    } for r in results]