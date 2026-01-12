#!/usr/bin/env python3
"""
Demonstration script showing how the improved SQL execution handles table validation
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent import run_enhanced_agent

def demo_improved_error_handling():
    """
    Demonstrate how the improved SQL execution handles non-existent tables
    """
    print("=== Improved SQL Execution Error Handling Demo ===\n")
    
    print("Before the improvement:")
    print("- SQL queries with non-existent tables would reach the database")
    print("- This caused database errors like 'relation \"contacts\" does not exist'")
    print("- These errors were logged as confusing error messages\n")
    
    print("After the improvement:")
    print("- SQL queries are validated for table existence before execution")
    print("- Non-existent tables are caught early in the process")
    print("- More informative warnings are logged\n")
    
    print("Running a query that references a non-existent table 'contacts'...")
    print("This simulates the example from the error logs.\n")
    
    # Simulate a query that would previously cause the error
    user_request = "Show me the names and phone numbers of customers from Asian countries"
    
    try:
        result = run_enhanced_agent(user_request)
        
        print("Query execution completed with the following results:")
        print(f"- Generated SQL: {result['generated_sql']}")
        print(f"- Number of results: {len(result['db_results'])}")
        print(f"- Retry count: {result['retry_count']}")
        print(f"- Any errors: {result['execution_error'] or 'None'}")
        
        if result['execution_error']:
            print(f"\nExecution error: {result['execution_error']}")
        
        print("\nThe system now properly handles non-existent tables by:")
        print("1. Validating table existence before sending to the database")
        print("2. Providing clearer error messages")
        print("3. Allowing the system to attempt query refinement or wider search strategies")
        
    except Exception as e:
        print(f"Error during agent execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_improved_error_handling()