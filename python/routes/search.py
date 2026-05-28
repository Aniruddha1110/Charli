# routes/search.py — Web search endpoints

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from modules.web_search import search, search_and_summarise, search_news
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])


# ── Models ─────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query:       str
    max_results: Optional[int] = 5
    summarise:   Optional[bool] = True


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/")
async def web_search(request: SearchRequest):
    """
    Search the web and optionally summarise with Ollama.

    Body:
        {
            "query": "latest AI news",
            "max_results": 5,
            "summarise": true
        }
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(f"Search request: '{request.query}' summarise={request.summarise}")

    if request.summarise:
        result = search_and_summarise(
            request.query.strip(),
            max_results=request.max_results
        )
    else:
        results = search(request.query.strip(), max_results=request.max_results)
        result  = {
            "query":   request.query,
            "results": results,
            "summary": None,
        }

    return result


@router.get("/quick")
async def quick_search(q: str, max_results: int = 5):
    """
    Quick GET search without summarisation — for fast lookups.
    GET /search/quick?q=python tutorials
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = search(q.strip(), max_results=max_results)
    return {"query": q, "results": results, "count": len(results)}


@router.get("/news")
async def news_search(q: str, max_results: int = 5):
    """
    Search for recent news articles.
    GET /search/news?q=artificial intelligence
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = search_news(q.strip(), max_results=max_results)
    return {"query": q, "results": results, "count": len(results)}

class OpenUrlRequest(BaseModel):
    url: str

@router.post("/open")
async def open_url(request: OpenUrlRequest):
    """Open a URL in the default browser."""
    import webbrowser
    try:
        webbrowser.open(request.url)
        return {"success": True, "url": request.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))