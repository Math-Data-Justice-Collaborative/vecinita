# ############################################################################
# FILE: __init__.py
# PATH: src/agent/tools/__init__.py
# ROLE: Package exporter for Vecinita Agent Tools.
# LOGIC: Exports direct functions for Gemini RAG and legacy tools for LangGraph.
# ############################################################################

"""
Vecinita Toolset Initialization.
This module acts as the central gateway for all retrieval and search tools.
"""

# 1. Direct Import for Gemini Engine (main.py)
# We import the core db_search function that was defined in db_search.py
from .db_search import db_search

# 2. Legacy/Static Tool Exports
# These are maintained for compatibility with the existing LangGraph nodes
try:
    from .static_response import static_response_tool
except ImportError:
    static_response_tool = None

try:
    from .web_search import web_search_tool
except ImportError:
    web_search_tool = None

# 3. Explicit Export Control
# This defines what is accessible via 'from src.agent.tools import *'
__all__ = [
    "db_search",
    "static_response_tool",
    "web_search_tool",
]

## end-of-file __init__.py
