"""
Reranker module for the RAG component.
Handles re-ranking of retrieved documents based on query relevance.
"""
from typing import List, Dict, Any
import requests
import logging
import numpy as np
from .config import (
    RERANKER_MODEL,
    RERANKER_HOSTNAME,
    RERANKER_PORT,
    RERANKER_API_PATH,
    RERANKER_ENABLED
)

logger = logging.getLogger(__name__)


class Reranker:
    """Class responsible for re-ranking documents based on query relevance."""

    def __init__(self):
        self.model = RERANKER_MODEL
        self.hostname = RERANKER_HOSTNAME
        self.port = RERANKER_PORT
        self.api_path = RERANKER_API_PATH
        self.enabled = RERANKER_ENABLED
        self.base_url = f"http://{self.hostname}:{self.port}{self.api_path}"
        
        if self.enabled:
            logger.info(f"Reranker initialized with model: {self.model}, URL: {self.base_url}")
        else:
            logger.info("Reranker is disabled")

    def rerank_documents(self, query: str, documents: List[Dict[str, Any]], top_k: int = None) -> List[Dict[str, Any]]:
        """
        Re-rank documents based on their relevance to the query.
        Uses the embeddings endpoint to get embeddings for query and documents,
        then computes similarity scores to rerank.

        Args:
            query: The user query
            documents: List of documents to re-rank
            top_k: Number of top documents to return (optional)

        Returns:
            List of re-ranked documents with updated scores
        """
        if not self.enabled or not documents:
            return documents

        try:
            headers = {
                "Content-Type": "application/json"
            }

            logger.debug(f"Starting reranking for {len(documents)} documents")

            # Get embedding for the query
            query_payload = {
                "input": query,
                "model": self.model
            }

            query_response = requests.post(f"{self.base_url}/embeddings", json=query_payload, headers=headers, timeout=30)

            if query_response.status_code != 200:
                logger.error(f"Failed to get query embedding: {query_response.text}")
                return documents

            query_embedding_data = query_response.json()
            if "data" not in query_embedding_data or len(query_embedding_data["data"]) == 0:
                logger.error(f"Query embedding response missing data: {query_embedding_data}")
                return documents

            query_embedding = query_embedding_data["data"][0]["embedding"]
            logger.debug(f"Query embedding received with dimension: {len(query_embedding) if query_embedding else 'N/A'}")

            # Get embeddings for each document and compute similarity
            reranked_docs_with_scores = []
            for idx, doc in enumerate(documents):
                doc_payload = {
                    "input": doc.get('content', ''),
                    "model": self.model
                }

                doc_response = requests.post(f"{self.base_url}/embeddings", json=doc_payload, headers=headers, timeout=30)

                if doc_response.status_code != 200:
                    logger.warning(f"Failed to get embedding for document {idx}: {doc_response.text}")
                    # Assign a low score to documents that couldn't be embedded
                    reranked_docs_with_scores.append((doc, 0.0))
                    continue

                doc_embedding_data = doc_response.json()
                if "data" not in doc_embedding_data or len(doc_embedding_data["data"]) == 0:
                    logger.warning(f"Document {idx} embedding response missing data: {doc_embedding_data}")
                    # Assign a low score to documents that couldn't be embedded
                    reranked_docs_with_scores.append((doc, 0.0))
                    continue

                doc_embedding = doc_embedding_data["data"][0]["embedding"]

                # Compute cosine similarity between query and document embeddings
                query_vec = np.array(query_embedding)
                doc_vec = np.array(doc_embedding)

                # Calculate cosine similarity
                cosine_sim = np.dot(query_vec, doc_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(doc_vec))

                reranked_docs_with_scores.append((doc, float(cosine_sim)))

            # Sort documents by similarity score in descending order
            reranked_docs_with_scores.sort(key=lambda x: x[1], reverse=True)

            # Take top_k if specified
            if top_k:
                reranked_docs_with_scores = reranked_docs_with_scores[:top_k]

            # Format the results
            reranked_docs = []
            for doc, score in reranked_docs_with_scores:
                updated_doc = doc.copy()
                updated_doc["score"] = score
                # Add a flag to indicate this document was reranked
                updated_doc["reranked"] = True
                reranked_docs.append(updated_doc)

            logger.info(f"Reranking completed for {len(documents)} documents, returning {len(reranked_docs)}")
            return reranked_docs

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during reranking: {str(e)}")
            # Return original documents if reranking fails
            return documents
        except Exception as e:
            logger.error(f"Unexpected error during reranking: {str(e)}")
            # Return original documents if reranking fails
            return documents