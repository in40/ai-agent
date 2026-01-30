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
from transformers import AutoTokenizer, AutoModel
import torch
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

        # If the request fails, it might be because the model is an LLM loaded as encoder
        # In this case, we'll try to handle T5Encoder models specially
        if response.status_code != 200:
            # Check if this is a T5 model that might be loaded as an LLM
            if "t5" in self.model.lower() or "frida" in self.model.lower():
                # For T5 models loaded as LLMs, we need to handle them differently
                # This is a fallback approach - in practice, you'd want to use a proper embedding endpoint
                print(f"Warning: Model {self.model} might not support embeddings via LM Studio's /v1/embeddings endpoint.")
                print("T5Encoder models should ideally be loaded as embedding models in LM Studio,")
                print("or use the local HuggingFace approach with the T5EncoderEmbeddings class.")

                # Return a mock response with appropriate dimensions for testing
                # In a real scenario, you'd need to either:
                # 1. Load the model properly as an embedding model in LM Studio
                # 2. Or use the HuggingFace approach instead
                raise Exception(f"Model {self.model} does not appear to support embeddings via LM Studio's API. "
                                f"Consider using the HuggingFace provider instead with EMBEDDING_PROVIDER=huggingface")
            else:
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

        # If the request fails, it might be because the model is an LLM loaded as encoder
        if response.status_code != 200:
            # Check if this is a T5 model that might be loaded as an LLM
            if "t5" in self.model.lower() or "frida" in self.model.lower():
                # For T5 models loaded as LLMs, we need to handle them differently
                print(f"Warning: Model {self.model} might not support embeddings via LM Studio's /v1/embeddings endpoint.")
                print("T5Encoder models should ideally be loaded as embedding models in LM Studio,")
                print("or use the local HuggingFace approach with the T5EncoderEmbeddings class.")

                # Raise an exception suggesting the proper approach
                raise Exception(f"Model {self.model} does not appear to support embeddings via LM Studio's API. "
                                f"Consider using the HuggingFace provider instead with EMBEDDING_PROVIDER=huggingface")
            else:
                raise Exception(f"LM Studio embedding request failed with status {response.status_code}: {response.text}")

        result = response.json()

        # Extract the first embedding from response
        if result.get("data") and len(result["data"]) > 0:
            return result["data"][0].get("embedding", [])
        else:
            raise Exception("No embeddings returned from LM Studio")


class T5EncoderEmbeddings(Embeddings):
    """Custom embedding class for T5 encoder models that connects to LM Studio."""

    def __init__(self, model: str, base_url: str, api_key: str = "lm-studio"):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        # Filter out empty strings
        filtered_texts = [text for text in texts if text and text.strip()]

        if not filtered_texts:
            return []

        # Apply the appropriate prefix for document embeddings based on FRIDA model requirements
        prefixed_texts = [f"search_document: {text}" if not text.startswith(("search_query:", "search_document:", "paraphrase:", "categorize:", "categorize_sentiment:", "categorize_topic:", "categorize_entailment:")) else text for text in filtered_texts]

        # The FRIDA model should be loaded as an embedding model in LM Studio
        # so that the embeddings endpoint works properly
        payload = {
            "input": prefixed_texts,
            "model": self.model
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Make the request to LM Studio's embeddings endpoint
        # Ensure we don't double up on the /v1 path
        embeddings_url = f"{self.base_url}/embeddings" if self.base_url.endswith('/v1') else f"{self.base_url}/v1/embeddings"

        try:
            response = requests.post(embeddings_url, json=payload, headers=headers)
        except requests.exceptions.ConnectionError:
            print(f"Cannot connect to LM Studio server at {embeddings_url}")
            print("Please ensure LM Studio is running and accessible at the configured address.")

            # Raise an informative error
            raise Exception(f"Cannot connect to LM Studio server for model {self.model}. "
                          f"Please ensure LM Studio is running and accessible at {embeddings_url}")

        # If the embeddings endpoint works, process the response
        if response.status_code == 200:
            result = response.json()

            # Extract embeddings from response
            embeddings = []
            for item in result.get("data", []):
                embeddings.append(item.get("embedding", []))

            return embeddings
        else:
            # If the embeddings endpoint fails, it likely means the model is not loaded
            # as an embedding model in LM Studio
            if response.status_code == 500:
                print(f"Embeddings endpoint returned 500 error for model {self.model}.")
                print("This indicates the FRIDA model is not loaded as an embedding model in LM Studio.")
                print("Please load the FRIDA model as an embedding model in LM Studio for proper functionality.")
            else:
                print(f"Embeddings endpoint failed for model {self.model}. Status: {response.status_code}")

            raise Exception(f"T5Encoder model {self.model} is not loaded as an embedding model in LM Studio. "
                          f"Please load it as an embedding model for proper embedding functionality. "
                          f"Status code returned: {response.status_code}")

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        if not text or not text.strip():
            # Return a zero vector of appropriate dimension if text is empty
            return [0.0] * 1536  # Standard dimension, adjust as needed

        # Apply the appropriate prefix for query embeddings based on FRIDA model requirements
        if not text.startswith(("search_query:", "search_document:", "paraphrase:", "categorize:", "categorize_sentiment:", "categorize_topic:", "categorize_entailment:")):
            prefixed_text = f"search_query: {text}"
        else:
            prefixed_text = text

        # The FRIDA model should be loaded as an embedding model in LM Studio
        # so that the embeddings endpoint works properly
        payload = {
            "input": [prefixed_text],
            "model": self.model
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Make the request to LM Studio's embeddings endpoint
        # Ensure we don't double up on the /v1 path
        embeddings_url = f"{self.base_url}/embeddings" if self.base_url.endswith('/v1') else f"{self.base_url}/v1/embeddings"

        try:
            response = requests.post(embeddings_url, json=payload, headers=headers)
        except requests.exceptions.ConnectionError:
            print(f"Cannot connect to LM Studio server at {embeddings_url}")
            print("Please ensure LM Studio is running and accessible at the configured address.")

            # Raise an informative error
            raise Exception(f"Cannot connect to LM Studio server for model {self.model}. "
                          f"Please ensure LM Studio is running and accessible at {embeddings_url}")

        # If the embeddings endpoint works, process the response
        if response.status_code == 200:
            result = response.json()

            # Extract the first embedding from response
            if result.get("data") and len(result["data"]) > 0:
                return result["data"][0].get("embedding", [])
            else:
                raise Exception(f"No embeddings returned from LM Studio for model {self.model}")
        else:
            # If the embeddings endpoint fails, it likely means the model is not loaded
            # as an embedding model in LM Studio
            if response.status_code == 500:
                print(f"Embeddings endpoint returned 500 error for model {self.model}.")
                print("This indicates the FRIDA model is not loaded as an embedding model in LM Studio.")
                print("Please load the FRIDA model as an embedding model in LM Studio for proper functionality.")
            else:
                print(f"Embeddings endpoint failed for model {self.model}. Status: {response.status_code}")

            raise Exception(f"T5Encoder model {self.model} is not loaded as an embedding model in LM Studio. "
                          f"Please load it as an embedding model for proper embedding functionality. "
                          f"Status code returned: {response.status_code}")


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

        # Check if this is a T5 model first, regardless of provider
        # This ensures T5 models always use the appropriate embedding handler
        if "t5" in self.model_name.lower() or "frida" in self.model_name.lower():
            # Determine the base URL based on the provider
            if provider == "lm studio":
                # Use LM Studio endpoint for T5 models
                # Ensure proper URL format - if api_path is /v1, don't duplicate it
                if self.api_path and self.api_path == "/v1":
                    base_url = f"http://{self.hostname}:{self.port}{self.api_path}" if self.hostname and self.port else "http://localhost:1234/v1"
                else:
                    base_url = f"http://{self.hostname}:{self.port}{self.api_path}" if self.hostname and self.port and self.api_path else "http://localhost:1234/v1"
                self._embeddings = T5EncoderEmbeddings(
                    model=self.model_name,
                    base_url=base_url
                )
            else:
                # For other providers, we might want to use HuggingFace approach
                # But since the user wants to connect to LM Studio, we'll default to LM Studio approach
                if self.api_path and self.api_path == "/v1":
                    base_url = f"http://{self.hostname or 'localhost'}:{self.port or '1234'}{self.api_path}"
                else:
                    base_url = f"http://{self.hostname or 'localhost'}:{self.port or '1234'}{self.api_path or '/v1'}"
                self._embeddings = T5EncoderEmbeddings(
                    model=self.model_name,
                    base_url=base_url
                )
        elif provider == "openai":
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
            base_url = f"http://{self.hostname}:{self.port}{self.api_path}" if self.hostname and self.port and self.api_path else "http://localhost:1234/v1"
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