#!/usr/bin/env python3
"""
Test script to verify that logging now shows full (uncut) details for all tables from all databases
"""
import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ai_agent import AIAgent
from database.utils.database import DatabaseManager
from config.settings import ENABLE_SCREEN_LOGGING

def test_full_logging():
    """Test that logging now shows full (uncut) details"""
    
    print("Testing full logging functionality...")
    
    # Enable screen logging
    os.environ['ENABLE_SCREEN_LOGGING'] = 'true'
    
    # Create an AI agent instance
    agent = AIAgent()
    
    # Set up logging to see the output
    if ENABLE_SCREEN_LOGGING:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Test with a simple request to trigger schema logging
    print("\nMaking a request that will trigger schema logging...")
    result = agent.process_request("Show me all tables in the database")
    
    print("\nCompleted test of logging functionality.")
    print("Check the logs above to confirm that full schema details are displayed without truncation.")

if __name__ == "__main__":
    test_full_logging()