"""
Embedding manager module for the RAG component.
Handles conversion of text to vector embeddings using various models.
"""
from typing import List
import numpy as np
from langchain_openai import OpenAIEmbeddings as LangChainOpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import (
    EMBEDDING_PROVIDER,
    EMBEDDING_MODEL,
    EMBEDDING_HOSTNAME,
    EMBEDDING_PORT,
    EMBEDDING_API_PATH,
    OPENAI_API_KEY,
    DEEPSEEK_API_KEY,
    GIGACHAT_CREDENTIALS,
    GIGACHAT_SCOPE,
    GIGACHAT_ACCESS_TOKEN,
    GIGACHAT_VERIFY_SSL_CERTS
)
from .config import RAG_EMBEDDING_PROVIDER, RAG_EMBEDDING_MODEL


class EmbeddingManager:
    """Class responsible for managing text embeddings."""

    def __init__(self):
        # Use RAG-specific settings if available, otherwise use global settings
        self.provider = RAG_EMBEDDING_PROVIDER if RAG_EMBEDDING_PROVIDER is not None else EMBEDDING_PROVIDER
        self.model_name = RAG_EMBEDDING_MODEL if RAG_EMBEDDING_MODEL is not None else EMBEDDING_MODEL
        self.hostname = EMBEDDING_HOSTNAME
        self.port = EMBEDDING_PORT
        self.api_path = EMBEDDING_API_PATH
        self._embeddings = None
        self._initialize_embeddings()

    def _initialize_embeddings(self):
        """Initialize the appropriate embedding model based on provider configuration."""
        provider = self.provider.lower().strip() if self.provider else "huggingface"

        if provider == "openai":
            # Use OpenAI embeddings
            self._embeddings = LangChainOpenAIEmbeddings(
                model=self.model_name,
                openai_api_key=OPENAI_API_KEY
            )
        elif provider == "huggingface":
            # Use HuggingFace embeddings (default)
            self._embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
        elif provider == "deepseek":
            # Use OpenAI-compatible embeddings via DeepSeek API
            base_url = f"https://{self.hostname}:{self.port}{self.api_path}" if self.hostname and self.port and self.api_path else None
            self._embeddings = LangChainOpenAIEmbeddings(
                model=self.model_name,
                openai_api_key=DEEPSEEK_API_KEY,
                base_url=base_url
            )
        elif provider == "gigachat":
            # Use GigaChat embeddings if available
            # Note: GigaChat may not have embedding models, so we'll fall back to OpenAI-compatible
            base_url = f"https://{self.hostname}:{self.port}{self.api_path}" if self.hostname and self.port and self.api_path else None
            self._embeddings = LangChainOpenAIEmbeddings(
                model=self.model_name,
                openai_api_key=GIGACHAT_ACCESS_TOKEN,  # Using access token as API key
                base_url=base_url
            )
        elif provider in ["ollama", "lm studio"]:
            # Use OpenAI-compatible embeddings via local providers
            base_url = f"http://{self.hostname}:{self.port}{self.api_path}" if self.hostname and self.port and self.api_path else None
            self._embeddings = LangChainOpenAIEmbeddings(
                model=self.model_name,
                base_url=base_url
            )
        else:
            # Default to HuggingFace if provider is unknown
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