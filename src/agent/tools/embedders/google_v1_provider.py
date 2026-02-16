# ############################################################################
# FILE: google_v1_provider.py
# PATH: src/agent/tools/embedders/google_v1_provider.py
# ROLE: Google Generative AI Embedding Provider
# DESCRIPTION: Implements the BaseProvider using Google's models. 
#              Provides superior bilingual semantic nuance and spelling 
#              resilience. Optimized for the "Quality" strategy.
# ############################################################################

import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from .base_provider import BaseProvider

class GoogleV1Provider(BaseProvider):
    """
    Cloud-based provider leveraging Gemini's embedding engine.
    Requires a valid GOOGLE_API_KEY and active internet connection.
    """

    def __init__(self):
        """
        Initializes the Google embedding client. 
        Explicitly pins the API version to 'v1' to bypass 'v1beta' 404 errors.
        """
        self.client = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            version="v1"  # CRITICAL: Forces the stable production path
        )
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generates a 768-dimension vector via Google's API.
        
        Args:
            text (str): Input text to be vectorized.
            
        Returns:
            List[float]: A 768-dimensional numerical representation.
        """
        return self.client.embed_query(text)
    
    def get_dimension(self) -> int:
        """
        Returns the standard dimension for the Google embedding-001 model.
        
        Returns:
            int: 768
        """
        return 768

# ############################################################################
# END OF FILE: google_v1_provider.py
# ############################################################################
