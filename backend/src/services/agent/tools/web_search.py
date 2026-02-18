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


# NOTE: This placeholder function should NOT be called directly.
# Instead, use create_web_search_tool() to get a properly configured instance.
# The factory function handles:
# - Tavily API initialization (if TAVILY_API_KEY is set)
# - DuckDuckGo fallback (if Tavily unavailable)
# - Response normalization across providers
#
# Example:
#   from langchain_core.tools import Tool
#   web_search = create_web_search_tool(search_depth='advanced', max_results=5)
#   result = web_search.invoke({"query": "climate change 2024"})

@tool
def web_search_tool(query: str) -> str:
    """Placeholder tool - do not use directly.
    
    Use create_web_search_tool() instead to get a configured instance.
    This function exists only for type hinting and documentation.
    
    Args:
        query: The search query (not used in placeholder)
        
    Returns:
        Never returns - call create_web_search_tool() instead
        
    Raises:
        RuntimeError: Always - this is a placeholder
    """
    raise RuntimeError(
        "web_search_tool() is a placeholder. "
        "Use create_web_search_tool() to create a properly configured instance. "
        "See create_web_search_tool() docstring for examples."
    )


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

            # Return normalized results as JSON
            if normalized:
                return json.dumps(normalized)

            # If we get here, no results were found or no provider is available.
            # CRITICAL FIX: Return a message instead of an empty list so the LLM doesn't crash.
            logger.warning(
                "No web search provider available or no results found.")
            return json.dumps([{
                "title": "System",
                "content": "Web search is currently unavailable or returned no results. Please answer based on internal knowledge if possible.",
                "url": ""
            }])

        except Exception as e:
            logger.error(f"Web search error: {e}")
            # CRITICAL FIX: Return the error as content so the LLM knows what happened.
            return json.dumps([{
                "title": "Error",
                "content": f"Web search failed: {str(e)}",
                "url": ""
            }])

    return web_search
