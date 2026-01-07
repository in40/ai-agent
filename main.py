import argparse
import os
from ai_agent import AIAgent
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
else:
    # Disable logging output if screen logging is disabled
    logging.basicConfig(level=logging.WARNING)

def main():
    parser = argparse.ArgumentParser(description='AI Agent for Natural Language to SQL Queries')
    parser.add_argument('--database-url', type=str, help='Database URL for connection')
    parser.add_argument('--request', type=str, help='Natural language request to process')
    
    args = parser.parse_args()
    
    # Initialize the AI agent
    agent = AIAgent(database_url=args.database_url)
    
    # Test database connection
    if not agent.test_connection():
        print("Error: Could not connect to the database")
        return
    
    # If request is provided as argument, process it
    if args.request:
        try:
            result = agent.process_request(args.request, attached_files=None)
            print("Final Response:")
            print(result["final_response"])
            print(f"\nProcessing Time: {result['processing_time']:.2f} seconds")
        except Exception as e:
            print(f"Error processing request: {str(e)}")
    else:
        # Interactive mode
        print("AI Agent is ready. Enter your natural language requests (type 'quit' to exit):")
        while True:
            try:
                user_input = input("\nYour request: ")
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break

                result = agent.process_request(user_input, attached_files=None)
                print("\nFinal Response:")
                print(result["final_response"])
                print(f"\nProcessing Time: {result['processing_time']:.2f} seconds")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error processing request: {str(e)}")

if __name__ == "__main__":
    main()