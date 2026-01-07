import os
from unittest.mock import Mock, patch
from ai_agent import AIAgent

def test_ai_agent():
    """
    Test the AI agent workflow with mock components
    """
    # For testing purposes, we'll use mock components since we don't have a real database
    with patch('ai_agent.DatabaseManager') as mock_db_manager, \
         patch('ai_agent.SQLGenerator') as mock_sql_generator, \
         patch('ai_agent.SQLExecutor') as mock_sql_executor, \
         patch('ai_agent.PromptGenerator') as mock_prompt_generator, \
         patch('ai_agent.ResponseGenerator') as mock_response_generator:
        
        # Setup mock return values
        mock_db_manager.return_value.get_schema_dump.return_value = {
            'users': [
                {'name': 'id', 'type': 'integer', 'nullable': False},
                {'name': 'name', 'type': 'varchar', 'nullable': False},
                {'name': 'email', 'type': 'varchar', 'nullable': True}
            ]
        }
        
        mock_sql_generator.return_value.generate_sql.return_value = "SELECT * FROM users LIMIT 5;"
        mock_sql_executor.return_value.execute_sql_and_get_results.return_value = [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
        ]
        
        mock_prompt_generator.return_value.generate_prompt_for_response_llm.return_value = \
            "Create a response based on: user requested user data, and here are the results..."
        
        mock_response_generator.return_value.generate_natural_language_response.return_value = \
            "Here are the users you requested: John Doe and Jane Smith."
        
        # Create the agent
        agent = AIAgent()
        
        # Process a test request
        user_request = "Show me some user data"
        result = agent.process_request(user_request)
        
        # Verify the result
        assert result["original_request"] == user_request
        assert result["generated_sql"] == "SELECT * FROM users LIMIT 5;"
        assert len(result["db_results"]) == 2
        assert "John Doe" in result["final_response"]
        assert "processing_time" in result
        assert isinstance(result["processing_time"], float)
        assert result["processing_time"] >= 0

        print("Test passed! AI agent workflow is functioning correctly.")
        print(f"Original request: {result['original_request']}")
        print(f"Generated SQL: {result['generated_sql']}")
        print(f"Sample result: {result['db_results'][0]}")
        print(f"Final response: {result['final_response']}")
        print(f"Processing time: {result['processing_time']:.2f} seconds")

if __name__ == "__main__":
    test_ai_agent()