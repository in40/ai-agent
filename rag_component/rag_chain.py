"""
RAG chain module for the RAG component.
Combines retrieved documents with user queries to generate responses.
"""
from typing import Dict, Any, List
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from .retriever import Retriever
from .config import RAG_ENABLED


class RAGChain:
    """Class responsible for creating and executing the RAG chain."""
    
    def __init__(self, retriever: Retriever, llm):
        """
        Initialize the RAG chain.
        
        Args:
            retriever: Instance of the Retriever class
            llm: Language model to use for generation
        """
        self.retriever = retriever
        self.llm = llm
        self.enabled = RAG_ENABLED
        
        # Define the prompt template for RAG
        self.rag_prompt_template = PromptTemplate.from_template(
            "Use the following pieces of context to answer the question at the end. "
            "If you don't know the answer, just say that you don't know, don't try to make up an answer.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Helpful Answer:"
        )
        
        # Create the RAG chain
        self.rag_chain = (
            {"context": self.retriever.get_relevant_documents, "question": RunnablePassthrough()}
            | self.rag_prompt_template
            | self.llm
            | StrOutputParser()
        )
    
    def generate_response(self, query: str) -> str:
        """
        Generate a response using the RAG chain.
        
        Args:
            query: User query
            
        Returns:
            Generated response based on retrieved documents
        """
        if not self.enabled:
            return "RAG functionality is currently disabled."
        
        return self.rag_chain.invoke(query)
    
    def get_context_and_response(self, query: str) -> Dict[str, Any]:
        """
        Get both the retrieved context and the generated response.
        
        Args:
            query: User query
            
        Returns:
            Dictionary containing both context and response
        """
        if not self.enabled:
            return {
                "context": [],
                "response": "RAG functionality is currently disabled."
            }
        
        # Get relevant documents
        context = self.retriever.get_relevant_documents(query)
        
        # Generate response using the chain
        response = self.rag_chain.invoke(query)
        
        return {
            "context": context,
            "response": response
        }