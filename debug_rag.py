#!/usr/bin/env python3
"""
Debug script to test RAG ingestion functionality directly
"""
import os
import sys
sys.path.insert(0, '/root/qwen_test/ai_agent')

from rag_component.main import RAGOrchestrator
from langchain_openai import OpenAI

def test_ingestion():
    print("Creating RAG Orchestrator...")
    
    # Create a mock LLM for testing
    try:
        llm = OpenAI(model_name="text-ada-001", temperature=0)
    except Exception as e:
        print(f"Could not create OpenAI LLM: {e}")
        # Use a mock object instead
        llm = None
    
    rag_orchestrator = RAGOrchestrator(llm=llm)
    
    # Test file path
    test_file = "/root/qwen_test/ai_agent/test_ural.txt"
    
    print(f"Checking if file exists: {os.path.exists(test_file)}")
    print(f"File path: {test_file}")
    
    if os.path.exists(test_file):
        print("File exists, attempting ingestion...")
        success = rag_orchestrator.ingest_documents([test_file])
        print(f"Ingestion result: {success}")
    else:
        print("File does not exist!")

if __name__ == "__main__":
    test_ingestion()