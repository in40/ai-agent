"""
Embedding manager module for the RAG component.
Handles conversion of text to vector embeddings using various models.
"""
from typing import List
import numpy as np
from langchain_openai import OpenAIEmbeddings as LangChainOpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from .config import RAG_EMBEDDING_MODEL


class EmbeddingManager:
    """Class responsible for managing text embeddings."""
    
    def __init__(self):
        self.model_name = RAG_EMBEDDING_MODEL
        self._embeddings = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize the appropriate embedding model based on configuration."""
        if self.model_name.startswith("text-embedding"):
            # Use OpenAI embeddings
            self._embeddings = LangChainOpenAIEmbeddings(model=self.model_name)
        else:
            # Use HuggingFace embeddings (default)
            self._embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for a single text string.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of embedding values
        """
        return self._embeddings.embed_query(text)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple text strings.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        return self._embeddings.embed_documents(texts)
    
    @property
    def embeddings(self):
        """Return the underlying embeddings object."""
        return self._embeddings