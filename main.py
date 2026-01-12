import argparse
import os
from langgraph_agent import create_enhanced_agent_graph, AgentState
from config.settings import ENABLE_SCREEN_LOGGING, str_to_bool
import logging

# Explicitly check the environment variable for screen logging
enable_screen_logging = str_to_bool(os.getenv("ENABLE_SCREEN_LOGGING"), False)

# Set up logging based on configuration
if enable_screen_logging or ENABLE_SCREEN_LOGGING:
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Ensure logs go to stdout
        ]
    )
    # Set specific loggers to INFO level to ensure they show up
    logging.getLogger().setLevel(logging.INFO)
    # Enable HTTP request logging for debugging if screen logging is enabled
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.DEBUG)

    # Also ensure our application loggers are set to INFO
    logging.getLogger("ai_agent").setLevel(logging.INFO)
    logging.getLogger("models").setLevel(logging.INFO)
    logging.getLogger("utils").setLevel(logging.INFO)
    logging.getLogger("langgraph_agent").setLevel(logging.INFO)
else:
    # Disable logging output if screen logging is disabled
    logging.basicConfig(level=logging.WARNING)

from utils.multi_database_manager import multi_db_manager as DatabaseManager, reload_database_config

def main():
    parser = argparse.ArgumentParser(description='AI Agent for Natural Language to SQL Queries using LangGraph')
    parser.add_argument('--request', type=str, help='Natural language request to process')
    parser.add_argument('--database', type=str, default=None, help='Name of the database to use for queries (default: primary database from DATABASE_URL)')

    args = parser.parse_args()

    # Reload database configuration from environment variables
    reload_database_config()

    # List all available databases
    all_databases = DatabaseManager.list_databases()

    # Create the LangGraph agent
    graph = create_enhanced_agent_graph()

    # If request is provided as argument, process it
    if args.request:
        # Define initial state
        initial_state: AgentState = {
            "user_request": args.request,
            "schema_dump": {},
            "sql_query": "",
            "db_results": [],
            "all_db_results": {},
            "table_to_db_mapping": {},
            "table_to_real_db_mapping": {},
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "retry_count": 0,
            "database_name": args.database if args.database else "all_databases"
        }

        try:
            # Run the graph with recursion limit to prevent infinite loops
            result = graph.invoke(initial_state, config={"configurable": {"thread_id": "default"}, "recursion_limit": 50})
            print("Final Response:")
            print(result.get("final_response"))
        except Exception as e:
            print(f"Error processing request: {str(e)}")
    else:
        # Interactive mode
        print("AI Agent with LangGraph is ready. Enter your natural language requests (type 'quit' to exit):")
        print(f"Available databases: {', '.join(all_databases) if all_databases else 'None'}")

        # If a specific database was provided via command line, use it
        if args.database:
            print(f"Using database: {args.database}")
        elif len(all_databases) == 1:
            # If only one database is available, use it
            args.database = all_databases[0]
            print(f"Using database: {args.database}")
        else:
            print("Using all available databases for queries")

        while True:
            try:
                user_input = input("\nYour request: ")
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break

                # Define initial state
                initial_state: AgentState = {
                    "user_request": user_input,
                    "schema_dump": {},
                    "sql_query": "",
                    "db_results": [],
                    "all_db_results": {},
                    "table_to_db_mapping": {},
                    "table_to_real_db_mapping": {},
                    "final_response": "",
                    "messages": [],
                    "validation_error": None,
                    "retry_count": 0,
                    "database_name": args.database if args.database else "all_databases"
                }

                # Run the graph with recursion limit to prevent infinite loops
                result = graph.invoke(initial_state, config={"configurable": {"thread_id": "default"}, "recursion_limit": 50})
                print("\nFinal Response:")
                print(result.get("final_response"))

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error processing request: {str(e)}")

if __name__ == "__main__":
    main()