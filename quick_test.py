#!/usr/bin/env python3
"""
Quick test to see if the vector store gets created.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def quick_test():
    """Quick test to see if we can initialize the RAG components."""
    print("Quick test to initialize RAG components...")
    
    try:
        # Import required modules
        from rag_component import RAGOrchestrator
        from models.response_generator import ResponseGenerator
        
        print("✓ Successfully imported RAG components")
        
        # Initialize the response generator to get the LLM
        response_gen = ResponseGenerator()
        llm = response_gen.llm  # Access the LLM directly from the response generator
        
        print("✓ Successfully accessed the LLM")
        
        # Initialize the RAG orchestrator (this might create the vector store)
        rag_orchestrator = RAGOrchestrator(llm=llm)
        
        print("✓ RAG orchestrator initialized")
        
        # Check if the vector store directory was created
        import os
        chroma_dir = "./data/chroma_db"
        
        if os.path.exists(chroma_dir):
            print(f"✓ Vector store directory exists: {chroma_dir}")
            contents = os.listdir(chroma_dir)
            if contents:
                print(f"  Contents: {contents}")
            else:
                print("  Directory is empty but exists")
        else:
            print(f"⚠ Vector store directory does not exist: {chroma_dir}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during quick test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n✓ Quick test completed successfully!")
    else:
        print("\n✗ Quick test failed.")
        sys.exit(1)