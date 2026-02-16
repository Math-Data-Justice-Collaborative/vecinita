# ############################################################################
# FILE: local_hf_provider.py
# PATH: src/agent/tools/embedders/local_hf_provider.py
# ROLE: Local Embedding Provider (HuggingFace)
# DESCRIPTION: Implements the BaseProvider using a local MiniLM model.
#              This is the "99% Availability" engine that runs on the CPU,
#              eliminating dependency on external APIs for vector search.
# ############################################################################

from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from .base_provider import BaseProvider

class LocalHFProvider(BaseProvider):
    """
    Sovereign embedding provider that runs entirely within the Docker container.
    """

    def __init__(self):
        """
        Initializes the all-MiniLM-L6-v2 model. 
        The model weights (~80MB) are cached locally upon first initialization 
        or during the Docker build stage.
        """
        # all-MiniLM-L6-v2 is the industry standard for fast, local CPU embeddings.
        self.client = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generates a 384-dimension vector locally.
        
        Args:
            text (str): Input text from the user or document.
            
        Returns:
            List[float]: A 384-dimensional numerical representation.
        """
        return self.client.embed_query(text)
    
    def get_dimension(self) -> int:
        """
        Returns the fixed dimension for the MiniLM-L6 model.
        
        Returns:
            int: 384
        """
        return 384

# ############################################################################
# END OF FILE: local_hf_provider.py
# ############################################################################
