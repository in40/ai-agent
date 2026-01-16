#!/usr/bin/env python3
"""
Demonstration script showing that the logging now displays full LLM requests
with all roles (system, human) and attached files information.
"""

import os
import logging

# Enable screen logging to see the changes
os.environ['ENABLE_SCREEN_LOGGING'] = 'true'
os.environ['SQL_LLM_PROVIDER'] = 'OpenAI'
os.environ['RESPONSE_LLM_PROVIDER'] = 'OpenAI'
os.environ['PROMPT_LLM_PROVIDER'] = 'OpenAI'

# Set up logging to see the output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def demonstrate_logging_changes():
    """Demonstrate the improved logging functionality"""
    print("Demonstrating the improved logging functionality...")
    print("="*60)
    print("CHANGES MADE:")
    print("1. Full LLM requests now show ALL roles (system, human, assistant)")
    print("2. Complete prompts are displayed WITHOUT truncation")
    print("3. Attached files information is shown when present")
    print("4. Logging occurs BEFORE the LLM call using format_messages()")
    print("="*60)
    
    # Import the AI Agent
    from core.ai_agent import AIAgent
    from unittest.mock import Mock, patch
    
    # Create a mock database manager to avoid needing a real database
    mock_db = Mock()
    mock_db.get_schema_dump.return_value = {
        'users': [
            {'name': 'id', 'type': 'integer', 'nullable': False},
            {'name': 'name', 'type': 'varchar(255)', 'nullable': False},
            {'name': 'email', 'type': 'varchar(255)', 'nullable': True}
        ]
    }
    mock_db.test_connection.return_value = True

    # Create the agent and patch the database manager
    agent = AIAgent()
    agent.db_manager = mock_db

    # Mock the SQL executor to avoid needing to execute real SQL
    agent.sql_executor.execute_sql_and_get_results = Mock(return_value=[])

    # Mock the LLM responses to avoid needing real API calls
    with patch.object(agent.sql_generator, 'generate_sql', return_value='SELECT * FROM users;'), \
         patch.object(agent.prompt_generator, 'generate_prompt_for_response_llm', return_value='Summarize the user data.'), \
         patch.object(agent.response_generator, 'generate_natural_language_response', return_value='Here are the results.'):
        
        print("\n--- DEMONSTRATION 1: Processing request WITHOUT attached files ---")
        result = agent.process_request('Show all users', attached_files=None)
        
        print("\n--- DEMONSTRATION 2: Processing request WITH attached files ---")
        attached_files = [
            {'filename': 'document1.pdf', 'size': 102400, 'type': 'application/pdf'},
            {'filename': 'image1.jpg', 'size': 51200, 'type': 'image/jpeg'}
        ]
        result = agent.process_request('Show all users based on attached documents', attached_files=attached_files)
        
        print("\n" + "="*60)
        print("EXPECTED LOG OUTPUT SUMMARY:")
        print("✓ SQLGenerator full LLM request:")
        print("    - System Message 1: [full system prompt content]")
        print("    - Message 2 (human): [user request + schema]")
        print("✓ PromptGenerator full LLM request:")
        print("    - System Message 1: [full system prompt content]")
        print("    - Message 2 (human): [user request + db results]")
        print("✓ ResponseGenerator full LLM request:")
        print("    - System Message 1: [full system prompt content]")
        print("    - Message 2 (human): [generated prompt for response]")
        print("✓ When attached files are present:")
        print("    - Attached files: 2 file(s)")
        print("    - File 1: document1.pdf (102400 bytes)")
        print("    - File 2: image1.jpg (51200 bytes)")
        print("="*60)

if __name__ == "__main__":
    demonstrate_logging_changes()