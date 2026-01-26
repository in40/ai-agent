"""
Embedding manager module for the RAG component.
Handles conversion of text to vector embeddings using various models.
"""
from typing import List
import numpy as np
import requests
from langchain_core.embeddings import Embeddings
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


class LMStudioEmbeddings(Embeddings):
    """Custom embedding class for LM Studio."""

    def __init__(self, model: str, base_url: str, api_key: str = "dummy"):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key

        # Validate connection to LM Studio
        try:
            response = requests.get(f"{self.base_url}/models")
            if response.status_code != 200:
                print(f"Warning: Could not validate LM Studio connection. Status: {response.status_code}")
        except Exception as e:
            print(f"Warning: Could not connect to LM Studio at {self.base_url}. Error: {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        # Filter out empty strings
        filtered_texts = [text for text in texts if text and text.strip()]

        if not filtered_texts:
            return []

        # Prepare the request
        payload = {
            "input": filtered_texts,
            "model": self.model
        }

        headers = {
            "Content-Type": "application/json"
        }

        # Make the request to LM Studio
        response = requests.post(f"{self.base_url}/embeddings", json=payload, headers=headers)

        if response.status_code != 200:
            raise Exception(f"LM Studio embedding request failed with status {response.status_code}: {response.text}")

        result = response.json()

        # Extract embeddings from response
        embeddings = []
        for item in result.get("data", []):
            embeddings.append(item.get("embedding", []))

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        if not text or not text.strip():
            # Return a zero vector of appropriate dimension if text is empty
            return [0.0] * 10  # Adjust as needed

        # Prepare the request
        payload = {
            "input": [text],
            "model": self.model
        }

        headers = {
            "Content-Type": "application/json"
        }

        # Make the request to LM Studio
        response = requests.post(f"{self.base_url}/embeddings", json=payload, headers=headers)

        if response.status_code != 200:
            raise Exception(f"LM Studio embedding request failed with status {response.status_code}: {response.text}")

        result = response.json()

        # Extract the first embedding from response
        if result.get("data") and len(result["data"]) > 0:
            return result["data"][0].get("embedding", [])
        else:
            raise Exception("No embeddings returned from LM Studio")


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
        elif provider == "lm studio":
            # Use custom embeddings for LM Studio to avoid compatibility issues with LangChain's OpenAIEmbeddings
            base_url = f"http://{self.hostname}:{self.port}{self.api_path}" if self.hostname and self.port and self.api_path else None
            self._embeddings = LMStudioEmbeddings(
                model=self.model_name,
                base_url=base_url
            )
        elif provider == "ollama":
            # Use OpenAI-compatible embeddings via Ollama
            base_url = f"http://{self.hostname}:{self.port}{self.api_path}" if self.hostname and self.port and self.api_path else None
            # For Ollama, we typically don't need an API key, but we need to configure the client properly
            # Setting openai_api_key to a dummy value to satisfy LangChain requirements
            self._embeddings = LangChainOpenAIEmbeddings(
                model=self.model_name,
                base_url=base_url,
                openai_api_key="dummy"
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
        # Handle empty or whitespace-only strings
        if not text or not text.strip():
            # Return a zero vector of appropriate dimension if text is empty
            # For most embedding models, a common dimension is 384 or 768
            # We'll return a small default vector as a fallback
            return [0.0] * 10  # Small default vector, adjust as needed
        return self._embeddings.embed_query(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple text strings.

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors
        """
        # Filter out empty or whitespace-only strings before embedding
        filtered_texts = [text for text in texts if text and text.strip()]
        if not filtered_texts:
            # Return empty list if all texts were empty
            return []
        return self._embeddings.embed_documents(filtered_texts)

    @property
    def embeddings(self):
        """Return the underlying embeddings object."""
        return self._embeddings