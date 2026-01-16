import argparse
import os
from langgraph_agent import create_enhanced_agent_graph, AgentState
from config.settings import ENABLE_SCREEN_LOGGING, str_to_bool, DISABLE_DATABASES
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
from utils.markdown_renderer import print_markdown

def main():
    parser = argparse.ArgumentParser(description='AI Agent for Natural Language to SQL Queries using LangGraph')
    parser.add_argument('--request', type=str, help='Natural language request to process')
    parser.add_argument('--database', type=str, default=None, help='Name of the database to use for queries (default: primary database from DATABASE_URL)')
    parser.add_argument('--registry-url', type=str, help='URL of the MCP registry server')

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
            "response_prompt": "",
            "final_response": "",
            "messages": [],
            "validation_error": None,
            "retry_count": 0,
            "execution_error": None,
            "sql_generation_error": None,
            "disable_sql_blocking": False,
            "disable_databases": DISABLE_DATABASES,
            "query_type": "initial",
            "database_name": args.database if args.database else "all_databases",
            "previous_sql_queries": [],
            "registry_url": args.registry_url,
            "discovered_services": [],
            "mcp_service_results": [],
            "use_mcp_results": False,
            "mcp_tool_calls": [],
            "mcp_capable_response": ""
        }

        try:
            # Run the graph with recursion limit to prevent infinite loops
            result = graph.invoke(initial_state, config={"configurable": {"thread_id": "default"}, "recursion_limit": 50})
            print("Final Response:")
            print_markdown(result.get("final_response"))
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
                    "disable_sql_blocking": False,
                    "disable_databases": DISABLE_DATABASES,
                    "database_name": args.database if args.database else "all_databases",
                    "query_type": "initial",
                    "previous_sql_queries": [],
                    "registry_url": args.registry_url,  # Include registry URL in state
                    "discovered_services": [],
                    "mcp_service_results": [],
                    "use_mcp_results": False,
                    "mcp_tool_calls": [],
                    "mcp_capable_response": ""
                }

                # Run the graph with recursion limit to prevent infinite loops
                result = graph.invoke(initial_state, config={"configurable": {"thread_id": "default"}, "recursion_limit": 50})
                print("\nFinal Response:")
                print_markdown(result.get("final_response"))

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error processing request: {str(e)}")

if __name__ == "__main__":
    main()