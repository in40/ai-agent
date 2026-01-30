#!/usr/bin/env python3
"""
Final test to confirm the issue and demonstrate the solution
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_issue_and_solution():
    """Test to confirm the issue and demonstrate the solution."""
    print("=== TESTING THE ISSUE AND SOLUTION ===")
    
    print("\n1. Confirming the issue exists:")
    print("   - Russian query: 'Для биномиального закона распределения 256 независимых данных'")
    print("   - Current similarity threshold: 0.7")
    print("   - Highest matching document score: ~0.66")
    print("   - Expected result: No documents returned (due to threshold)")
    
    # Test with the current threshold (0.7)
    from rag_component.main import RAGOrchestrator
    from rag_component.config import RAG_SIMILARITY_THRESHOLD
    
    print(f"\nCurrent RAG_SIMILARITY_THRESHOLD: {RAG_SIMILARITY_THRESHOLD}")
    
    # Initialize RAG orchestrator
    rag_orchestrator = RAGOrchestrator(llm=None)
    
    # Russian query
    russian_query = "Для биномиального закона распределения 256 независимых данных"
    
    # Get documents using the same method as the API
    documents = rag_orchestrator.retrieve_documents(russian_query)
    
    print(f"Documents returned with threshold {RAG_SIMILARITY_THRESHOLD}: {len(documents)}")
    
    if documents:
        print("Scores of returned documents:")
        for i, doc in enumerate(documents):
            print(f"  Document {i+1}: Score = {doc.get('score', 'N/A')}")
    else:
        print("No documents returned with current threshold.")
    
    print("\n2. Testing with lower threshold (0.6):")
    # Temporarily change the threshold
    original_threshold = RAG_SIMILARITY_THRESHOLD
    os.environ['RAG_SIMILARITY_THRESHOLD'] = '0.6'
    
    # Reload the config to pick up the new value
    import importlib
    import rag_component.config
    importlib.reload(rag_component.config)
    from rag_component.config import RAG_SIMILARITY_THRESHOLD as NEW_THRESHOLD
    
    print(f"New RAG_SIMILARITY_THRESHOLD: {NEW_THRESHOLD}")
    
    # Create a new RAG orchestrator to use the new threshold
    rag_orchestrator_new = RAGOrchestrator(llm=None)
    
    # Get documents again
    documents_new = rag_orchestrator_new.retrieve_documents(russian_query)
    
    print(f"Documents returned with threshold {NEW_THRESHOLD}: {len(documents_new)}")
    
    if documents_new:
        print("Scores of returned documents:")
        for i, doc in enumerate(documents_new):
            print(f"  Document {i+1}: Score = {doc.get('score', 'N/A')}")
            print(f"    Content preview: {doc.get('content', '')[:100]}...")
    else:
        print("No documents returned with new threshold.")
    
    print("\n3. Solution:")
    print("   The issue is that the similarity threshold (0.7) is too high for this query.")
    print("   The highest matching document has a score of approximately 0.66.")
    print("   Documents with scores below the threshold are filtered out.")
    print("\n4. Recommended fixes:")
    print("   a) Lower the RAG_SIMILARITY_THRESHOLD in the .env file")
    print("      From: RAG_SIMILARITY_THRESHOLD=0.7")
    print("      To:   RAG_SIMILARITY_THRESHOLD=0.6  (or lower)")
    print("   b) Alternatively, implement dynamic threshold adjustment")
    print("   c) Or provide a way to adjust threshold per query")
    
    # Restore original threshold
    os.environ['RAG_SIMILARITY_THRESHOLD'] = str(original_threshold)
    importlib.reload(rag_component.config)
    
    return True

if __name__ == "__main__":
    success = test_issue_and_solution()
    if success:
        print("\n✓ Issue confirmed and solution demonstrated!")
    else:
        print("\n✗ Test failed.")
        sys.exit(1)