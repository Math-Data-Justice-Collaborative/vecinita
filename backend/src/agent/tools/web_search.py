"""Web search tool for Vecinita agent.

Provides web search via Tavily when available and falls back to DuckDuckGo
otherwise. Use when the internal database doesn't have relevant info or for
external, up-to-date sources.
"""

import logging
import os
from typing import Optional, Dict, Any, List
import json
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def create_web_search_tool(search_depth: str = "advanced", max_results: int = 5) -> tool:
    """Create a configured web_search tool using Tavily or DuckDuckGo.

    Prefers Tavily when `TAVILY_API_KEY` (or `TVLY_API_KEY`) is set; otherwise
    falls back to DuckDuckGo. Results are normalized into a list of dicts with
    keys: 'title', 'content' (or 'snippet'), and 'url'.

    Args:
        search_depth: Tavily search depth, e.g., 'basic' or 'advanced'.
        max_results: Maximum number of results to return (Tavily/DDG).
    """
    # Support multiple env var names to avoid setup friction
    tavily_key = (
        os.getenv("TAVILY_API_KEY")
        or os.getenv("TAVILY_API_AI_KEY")
        or os.getenv("TVLY_API_KEY")
    )
    use_tavily = bool(tavily_key)

    tavily = None
    ddg = None

    if use_tavily:
        try:
            from langchain_tavily import TavilySearch
            tavily = TavilySearch(
                max_results=max_results,
                search_depth=search_depth,
                include_answer=True,
                include_raw_content=False,
                api_key=tavily_key,
            )
            logger.info("Web search initialized with Tavily API")
        except Exception as e:
            logger.warning(
                f"Failed to initialize Tavily, falling back to DuckDuckGo: {e}")
            use_tavily = False

    if not use_tavily:
        try:
            from langchain_community.tools import DuckDuckGoSearchResults
            # Suppress noisy internal ddgs engine logs while preserving warnings and errors
            try:
                logging.getLogger("ddgs.ddgs").setLevel(logging.WARNING)
            except Exception:
                pass
            ddg = DuckDuckGoSearchResults(num_results=max_results)
            logger.info("Web search initialized with DuckDuckGo")
        except Exception as e:
            logger.error(f"Failed to initialize DuckDuckGo search: {e}")

    @tool
    def web_search(query: str) -> str:
        """Search the web for information.

        Args:
            query: The search query

        Returns:
            JSON string of normalized results with 'title', 'content'/'snippet', 'url'.
        """
        normalized: List[Dict[str, Any]] = []

        try:
            if use_tavily and tavily is not None:
                logger.info(f"Web search (Tavily): {query}")
                results = tavily.invoke({"query": query})
                for r in results or []:
                    normalized.append({
                        "title": r.get("title") or "",
                        "content": r.get("content") or r.get("answer") or "",
                        "url": r.get("url") or r.get("source") or "",
                    })
                if normalized:
                    return json.dumps(normalized)
            # DuckDuckGo fallback
            elif ddg is not None:
                logger.info(f"Web search (DuckDuckGo): {query}")
                results = ddg.invoke(query)
                if isinstance(results, list):
                    for r in results:
                        normalized.append({
                            "title": r.get("title") or "",
                            "content": r.get("snippet") or "",
                            "url": r.get("link") or "",
                        })
                elif isinstance(results, str) and results:
                    normalized.append({
                        "title": "DuckDuckGo Result",
                        "content": results,
                        "url": "",
                    })
                if normalized:
                    return json.dumps(normalized)

            # If we get here, no results were found or no provider is available.
            logger.warning(
                "No web search provider available or no results found.")
            return "[]"

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return "[]"

    return web_search
