#!/usr/bin/env python3
"""
Comprehensive test for the embedding provider system
"""

import subprocess
import sys

def test_provider(provider_name, model_name, expected_type, description):
    """Test a specific provider in a subprocess"""
    print(f"Testing {description}...")
    
    code = f'''
import os
os.environ.clear()
os.environ["EMBEDDING_PROVIDER"] = "{provider_name}"
os.environ["EMBEDDING_MODEL"] = "{model_name}"

from rag_component.embedding_manager import EmbeddingManager
emb_manager = EmbeddingManager()
print(f"Provider: {{emb_manager.provider}}")
print(f"Model: {{emb_manager.model_name}}")
print(f"Embeddings type: {{type(emb_manager.embeddings).__name__}}")
assert emb_manager.provider == "{provider_name}", f"Expected {provider_name}, got {{emb_manager.provider}}"
print("✓ Test passed")
'''
    
    result = subprocess.run([sys.executable, "-c", code], 
                          capture_output=True, text=True, 
                          cwd="/root/qwen_test/ai_agent")
    
    if result.returncode == 0:
        print(f"   {result.stdout.strip()}")
        print(f"   ✓ {description} test passed\n")
        return True
    else:
        print(f"   ✗ {description} test failed: {result.stderr}")
        return False

def test_rag_override():
    """Test RAG-specific provider override"""
    print("Testing RAG-specific provider override...")
    
    code = '''
import os
os.environ.clear()
os.environ["EMBEDDING_PROVIDER"] = "huggingface"
os.environ["EMBEDDING_MODEL"] = "all-MiniLM-L6-v2"
os.environ["RAG_EMBEDDING_PROVIDER"] = "openai"
os.environ["RAG_EMBEDDING_MODEL"] = "text-embedding-3-small"

from rag_component.embedding_manager import EmbeddingManager
emb_manager = EmbeddingManager()
print(f"RAG provider: {emb_manager.provider}")
print(f"RAG model: {emb_manager.model_name}")
print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")
assert emb_manager.provider == "openai", f"Expected openai due to RAG override, got {emb_manager.provider}"
print("✓ Test passed")
'''
    
    result = subprocess.run([sys.executable, "-c", code], 
                          capture_output=True, text=True, 
                          cwd="/root/qwen_test/ai_agent")
    
    if result.returncode == 0:
        print(f"   {result.stdout.strip()}")
        print("   ✓ RAG-specific provider override test passed\n")
        return True
    else:
        print(f"   ✗ RAG-specific provider override test failed: {result.stderr}")
        return False

def test_default_behavior():
    """Test default behavior when no provider is specified"""
    print("Testing default behavior...")
    
    code = '''
import os
os.environ.clear()  # No embedding provider set, should use defaults

from rag_component.embedding_manager import EmbeddingManager
emb_manager = EmbeddingManager()
print(f"Provider: {emb_manager.provider}")
print(f"Model: {emb_manager.model_name}")
print(f"Embeddings type: {type(emb_manager.embeddings).__name__}")
# Default should be huggingface
assert emb_manager.provider == "huggingface", f"Expected huggingface default, got {emb_manager.provider}"
print("✓ Test passed")
'''
    
    result = subprocess.run([sys.executable, "-c", code], 
                          capture_output=True, text=True, 
                          cwd="/root/qwen_test/ai_agent")
    
    if result.returncode == 0:
        print(f"   {result.stdout.strip()}")
        print("   ✓ Default behavior test passed\n")
        return True
    else:
        print(f"   ✗ Default behavior test failed: {result.stderr}")
        return False

def main():
    print("=== Testing Embedding Provider System ===\n")
    
    tests = [
        ("huggingface", "all-MiniLM-L6-v2", "HuggingFaceEmbeddings", "HuggingFace provider"),
        ("openai", "text-embedding-ada-002", "OpenAIEmbeddings", "OpenAI provider"),
        ("deepseek", "deepseek-embedding", "OpenAIEmbeddings", "DeepSeek provider"),
        ("ollama", "nomic-embed-text", "OpenAIEmbeddings", "Ollama provider"),
    ]
    
    results = []
    
    for provider, model, expected_type, desc in tests:
        results.append(test_provider(provider, model, expected_type, desc))
    
    results.append(test_rag_override())
    results.append(test_default_behavior())
    
    passed = sum(results)
    total = len(results)
    
    print(f"=== Test Results: {passed}/{total} passed ===")
    
    if passed == total:
        print("🎉 All embedding provider tests passed!")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())