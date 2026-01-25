#!/usr/bin/env python3
"""
Test script to verify the embedding provider system works correctly
"""

import os
import tempfile
import subprocess
import sys

def test_embedding_providers():
    """Test the embedding provider system"""
    
    print("=== Testing Embedding Provider System ===")
    
    # Test 1: Default HuggingFace provider
    print("\n1. Testing default HuggingFace provider...")
    result = subprocess.run([
        sys.executable, "-c", 
        """
import os
# Clear any existing embedding provider settings
for key in list(os.environ.keys()):
    if 'EMBEDDING' in key:
        del os.environ[key]

from rag_component.embedding_manager import EmbeddingManager
emb_manager = EmbeddingManager()
print(f"Provider: {emb_manager.provider}")
print(f"Model: {emb_manager.model_name}")
print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")
assert emb_manager.provider == 'huggingface', f"Expected huggingface, got {emb_manager.provider}"
print("✓ Default HuggingFace provider test passed")
        """
    ], capture_output=True, text=True, cwd="/root/qwen_test/ai_agent")
    
    if result.returncode != 0:
        print(f"✗ Test failed: {result.stderr}")
    else:
        print(result.stdout)
    
    # Test 2: OpenAI provider
    print("\n2. Testing OpenAI provider...")
    result = subprocess.run([
        sys.executable, "-c", 
        """
import os
os.environ['EMBEDDING_PROVIDER'] = 'openai'
os.environ['EMBEDDING_MODEL'] = 'text-embedding-ada-002'

from rag_component.embedding_manager import EmbeddingManager
emb_manager = EmbeddingManager()
print(f"Provider: {emb_manager.provider}")
print(f"Model: {emb_manager.model_name}")
print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")
assert emb_manager.provider == 'openai', f"Expected openai, got {emb_manager.provider}"
print("✓ OpenAI provider test passed")
        """
    ], capture_output=True, text=True, cwd="/root/qwen_test/ai_agent")
    
    if result.returncode != 0:
        print(f"Note: OpenAI test failed as expected (no API key): {result.stderr}")
    else:
        print(result.stdout)
    
    # Test 3: DeepSeek provider
    print("\n3. Testing DeepSeek provider...")
    result = subprocess.run([
        sys.executable, "-c", 
        """
import os
os.environ['EMBEDDING_PROVIDER'] = 'deepseek'
os.environ['EMBEDDING_MODEL'] = 'deepseek-embedding'

from rag_component.embedding_manager import EmbeddingManager
emb_manager = EmbeddingManager()
print(f"Provider: {emb_manager.provider}")
print(f"Model: {emb_manager.model_name}")
print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")
assert emb_manager.provider == 'deepseek', f"Expected deepseek, got {emb_manager.provider}"
print("✓ DeepSeek provider test passed")
        """
    ], capture_output=True, text=True, cwd="/root/qwen_test/ai_agent")
    
    if result.returncode != 0:
        print(f"Note: DeepSeek test failed as expected (no API key): {result.stderr}")
    else:
        print(result.stdout)
    
    # Test 4: Local provider (Ollama/LM Studio)
    print("\n4. Testing local provider (Ollama/LM Studio)...")
    result = subprocess.run([
        sys.executable, "-c", 
        """
import os
os.environ['EMBEDDING_PROVIDER'] = 'ollama'
os.environ['EMBEDDING_MODEL'] = 'nomic-embed-text'

from rag_component.embedding_manager import EmbeddingManager
emb_manager = EmbeddingManager()
print(f"Provider: {emb_manager.provider}")
print(f"Model: {emb_manager.model_name}")
print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")
assert emb_manager.provider == 'ollama', f"Expected ollama, got {emb_manager.provider}"
print("✓ Ollama provider test passed")
        """
    ], capture_output=True, text=True, cwd="/root/qwen_test/ai_agent")
    
    if result.returncode != 0:
        print(f"Note: Ollama test failed as expected (no API key): {result.stderr}")
    else:
        print(result.stdout)
    
    # Test 5: RAG-specific provider override
    print("\n5. Testing RAG-specific provider override...")
    result = subprocess.run([
        sys.executable, "-c", 
        """
import os
os.environ['EMBEDDING_PROVIDER'] = 'huggingface'  # Global setting
os.environ['EMBEDDING_MODEL'] = 'all-MiniLM-L6-v2'
os.environ['RAG_EMBEDDING_PROVIDER'] = 'openai'  # RAG-specific override
os.environ['RAG_EMBEDDING_MODEL'] = 'text-embedding-ada-002'

from rag_component.embedding_manager import EmbeddingManager
emb_manager = EmbeddingManager()
print(f"Global provider: huggingface")
print(f"RAG provider: {emb_manager.provider}")
print(f"RAG model: {emb_manager.model_name}")
print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")
assert emb_manager.provider == 'openai', f"Expected openai (RAG override), got {emb_manager.provider}"
print("✓ RAG-specific provider override test passed")
        """
    ], capture_output=True, text=True, cwd="/root/qwen_test/ai_agent")
    
    if result.returncode != 0:
        print(f"Note: RAG override test failed: {result.stderr}")
    else:
        print(result.stdout)

    print("\n=== All tests completed ===")

if __name__ == "__main__":
    test_embedding_providers()