"""Web search tool for Vecinita agent.

Provides web search via Tavily when available and falls back to DuckDuckGo
otherwise. Use when the internal database doesn't have relevant info or for
external, up-to-date sources.
"""

import json
import logging
import os
from typing import Any, cast

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


_DEFAULT_WEB_SEARCH_TOOL: Any | None = None


@tool
def web_search_tool(query: str) -> str:
    """Search the web using configured provider with automatic fallback.

    Args:
        query: The search query

    Returns:
        JSON string containing normalized web search results
    """
    global _DEFAULT_WEB_SEARCH_TOOL
    if _DEFAULT_WEB_SEARCH_TOOL is None:
        _DEFAULT_WEB_SEARCH_TOOL = create_web_search_tool()

    try:
        return cast(str, _DEFAULT_WEB_SEARCH_TOOL.invoke({"query": query}))
    except Exception as e:
        logger.error(f"web_search_tool wrapper error: {e}")
        return json.dumps(
            [{"title": "Error", "content": f"Web search failed: {str(e)}", "url": ""}]
        )


def create_web_search_tool(search_depth: str = "advanced", max_results: int = 5) -> Any:
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
        os.getenv("TAVILY_API_KEY") or os.getenv("TAVILY_API_AI_KEY") or os.getenv("TVLY_API_KEY")
    )
    use_tavily = bool(tavily_key)

    tavily = None
    ddg = None

    if use_tavily:
        try:
            from langchain_tavily import TavilySearch  # type: ignore[import-not-found]

            tavily = TavilySearch(
                max_results=max_results,
                search_depth=search_depth,
                include_answer=True,
                include_raw_content=False,
                api_key=tavily_key,
            )
            logger.info("Web search initialized with Tavily API")
        except Exception as e:
            logger.warning(f"Failed to initialize Tavily, falling back to DuckDuckGo: {e}")
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
        normalized: list[dict[str, Any]] = []

        try:
            if use_tavily and tavily is not None:
                logger.info(f"Web search (Tavily): {query}")
                results = tavily.invoke({"query": query})
                for r in results or []:
                    normalized.append(
                        {
                            "title": r.get("title") or "",
                            "content": r.get("content") or r.get("answer") or "",
                            "url": r.get("url") or r.get("source") or "",
                        }
                    )
            # DuckDuckGo fallback
            elif ddg is not None:
                logger.info(f"Web search (DuckDuckGo): {query}")
                results = ddg.invoke(query)
                if isinstance(results, list):
                    for r in results:
                        normalized.append(
                            {
                                "title": r.get("title") or "",
                                "content": r.get("snippet") or "",
                                "url": r.get("link") or "",
                            }
                        )
                elif isinstance(results, str) and results:
                    normalized.append(
                        {
                            "title": "DuckDuckGo Result",
                            "content": results,
                            "url": "",
                        }
                    )

            # Return normalized results as JSON
            if normalized:
                return json.dumps(normalized)

            # If we get here, no results were found or no provider is available.
            # CRITICAL FIX: Return a message instead of an empty list so the LLM doesn't crash.
            logger.warning("No web search provider available or no results found.")
            return json.dumps(
                [
                    {
                        "title": "System",
                        "content": "Web search is currently unavailable or returned no results. Please answer based on internal knowledge if possible.",
                        "url": "",
                    }
                ]
            )

        except Exception as e:
            logger.error(f"Web search error: {e}")
            # CRITICAL FIX: Return the error as content so the LLM knows what happened.
            return json.dumps(
                [{"title": "Error", "content": f"Web search failed: {str(e)}", "url": ""}]
            )

    return web_search
