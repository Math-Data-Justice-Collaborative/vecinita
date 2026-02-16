# ############################################################################
# FILE: base_provider.py
# PATH: src/agent/tools/embedders/base_provider.py
# ROLE: Abstract Base Class (Interface) for Embedding Strategies
# DESCRIPTION: Enforces a consistent "Contract" for all embedding providers
#              (Google, Local HF, OpenAI, etc.) to ensure the Search Router
#              can swap models dynamically without breaking.
# ############################################################################

from abc import ABC, abstractmethod
from typing import List

class BaseProvider(ABC):
    """
    Standard interface for all embedding implementations within the 
    Vecinita-RIOS framework.
    """

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Converts a raw string into a numerical vector (embedding).
        
        Args:
            text (str): The user query or document chunk to be vectorized.
            
        Returns:
            List[float]: The resulting vector for semantic search.
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """
        Returns the specific vector size produced by this model.
        Used by the Router to prevent Supabase dimension mismatch errors.
        
        Returns:
            int: The dimension count (e.g., 768 for Google, 384 for MiniLM).
        """
        pass

# ############################################################################
# END OF FILE: base_provider.py
# ############################################################################
