#!/usr/bin/env python3
"""
Enhanced command-line client for the AI Agent that can work in both standalone and backend modes.
This client maintains the original functionality while adding support for the new backend API.
"""
import argparse
import os
import sys
import json
import requests
from typing import Dict, Any, Optional

# Import the original LangGraph agent functionality
from langgraph_agent.langgraph_agent import run_enhanced_agent
from config.settings import ENABLE_SCREEN_LOGGING, str_to_bool, DISABLE_DATABASES
import logging

# Import interactive logger utility
from utils.interactive_logger import setup_interactive_logging, suppress_heartbeats, show_heartbeats

# Explicitly check the environment variable for screen logging
enable_screen_logging = str_to_bool(os.getenv("ENABLE_SCREEN_LOGGING"), False)

# Set up logging based on configuration
if enable_screen_logging or ENABLE_SCREEN_LOGGING:
    # Configure root logger with interactive capabilities
    setup_interactive_logging()
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

from database.utils.multi_database_manager import multi_db_manager as DatabaseManager, reload_database_config
from utils.markdown_renderer import print_markdown


class AIAgentClient:
    """AI Agent client that supports both standalone and backend API modes"""
    
    def __init__(self, backend_url: Optional[str] = None, auth_token: Optional[str] = None):
        """
        Initialize the AI Agent client
        
        Args:
            backend_url: URL of the backend API (if None, runs in standalone mode)
            auth_token: Authentication token for backend API
        """
        self.backend_url = backend_url
        self.auth_token = auth_token
        self.use_backend = bool(backend_url)
        
        # Reload database configuration from environment variables
        reload_database_config()
    
    def _make_backend_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the backend API
        
        Args:
            endpoint: API endpoint to call
            data: Request data to send
            
        Returns:
            Response from the backend API
        """
        if not self.backend_url:
            raise ValueError("Backend URL not configured")
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        url = f"{self.backend_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Backend API request failed: {str(e)}")
    
    def query_agent(self, user_request: str, disable_sql_blocking: bool = False, 
                   disable_databases: bool = False) -> Dict[str, Any]:
        """
        Query the AI agent
        
        Args:
            user_request: Natural language request to process
            disable_sql_blocking: Whether to disable SQL blocking
            disable_databases: Whether to disable database operations
            
        Returns:
            Response from the AI agent
        """
        if self.use_backend:
            # Use backend API
            data = {
                'user_request': user_request,
                'disable_sql_blocking': disable_sql_blocking,
                'disable_databases': disable_databases
            }
            
            return self._make_backend_request('/api/agent/query', data)
        else:
            # Use standalone agent
            return run_enhanced_agent(
                user_request=user_request,
                disable_sql_blocking=disable_sql_blocking,
                disable_databases=disable_databases
            )
    
    def query_rag(self, query: str) -> Dict[str, Any]:
        """
        Query the RAG component
        
        Args:
            query: Query to process
            
        Returns:
            Response from the RAG component
        """
        if self.use_backend:
            # Use backend API
            data = {'query': query}
            return self._make_backend_request('/api/rag/query', data)
        else:
            # Use standalone RAG (implementing the same functionality)
            from rag_component.main import RAGOrchestrator
            from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
            from models.response_generator import ResponseGenerator
            
            response_generator = ResponseGenerator()
            llm = response_generator._get_llm_instance(
                provider=RESPONSE_LLM_PROVIDER,
                model=RESPONSE_LLM_MODEL
            )
            
            rag_orchestrator = RAGOrchestrator(llm=llm)
            return rag_orchestrator.query(query)
    
    def ingest_documents(self, file_paths: list) -> bool:
        """
        Ingest documents into the RAG component
        
        Args:
            file_paths: List of file paths to ingest
            
        Returns:
            True if ingestion was successful, False otherwise
        """
        if self.use_backend:
            # Use backend API
            data = {'file_paths': file_paths}
            response = self._make_backend_request('/api/rag/ingest', data)
            return 'message' in response and 'successfully' in response['message']
        else:
            # Use standalone RAG
            from rag_component.main import RAGOrchestrator
            from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
            from models.response_generator import ResponseGenerator
            
            response_generator = ResponseGenerator()
            llm = response_generator._get_llm_instance(
                provider=RESPONSE_LLM_PROVIDER,
                model=RESPONSE_LLM_MODEL
            )
            
            rag_orchestrator = RAGOrchestrator(llm=llm)
            return rag_orchestrator.ingest_documents(file_paths)
    
    def retrieve_documents(self, query: str, top_k: int = 5) -> list:
        """
        Retrieve documents from the RAG component
        
        Args:
            query: Query to search for
            top_k: Number of top results to return
            
        Returns:
            List of relevant documents
        """
        if self.use_backend:
            # Use backend API
            data = {'query': query, 'top_k': top_k}
            response = self._make_backend_request('/api/rag/retrieve', data)
            return response.get('documents', [])
        else:
            # Use standalone RAG
            from rag_component.main import RAGOrchestrator
            from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
            from models.response_generator import ResponseGenerator
            
            response_generator = ResponseGenerator()
            llm = response_generator._get_llm_instance(
                provider=RESPONSE_LLM_PROVIDER,
                model=RESPONSE_LLM_MODEL
            )
            
            rag_orchestrator = RAGOrchestrator(llm=llm)
            return rag_orchestrator.retrieve_documents(query, top_k=top_k)


def main():
    parser = argparse.ArgumentParser(description='AI Agent Client - Enhanced command-line client with backend support')
    parser.add_argument('--request', type=str, help='Natural language request to process')
    parser.add_argument('--database', type=str, default=None, help='Name of the database to use for queries (default: primary database from DATABASE_URL)')
    parser.add_argument('--registry-url', type=str, help='URL of the MCP registry server')
    parser.add_argument('--backend-url', type=str, help='URL of the backend API (if not provided, runs in standalone mode)')
    parser.add_argument('--auth-token', type=str, help='Authentication token for backend API')
    parser.add_argument('--disable-sql-blocking', action='store_true', help='Disable SQL blocking for safety')
    parser.add_argument('--disable-databases', action='store_true', help='Disable database operations')
    parser.add_argument('--rag-query', type=str, help='Query the RAG component instead of the main agent')
    parser.add_argument('--ingest-documents', nargs='+', help='Ingest documents into the RAG component')
    
    args = parser.parse_args()

    # Create the AI Agent client
    client = AIAgentClient(backend_url=args.backend_url, auth_token=args.auth_token)

    # List all available databases
    all_databases = DatabaseManager.list_databases()

    # If ingest-documents is provided, ingest the documents
    if args.ingest_documents:
        try:
            success = client.ingest_documents(args.ingest_documents)
            if success:
                print(f"Successfully ingested documents: {args.ingest_documents}")
            else:
                print(f"Failed to ingest documents: {args.ingest_documents}")
        except Exception as e:
            print(f"Error ingesting documents: {str(e)}")
        return

    # If rag-query is provided, query the RAG component
    if args.rag_query:
        try:
            result = client.query_rag(args.rag_query)
            print("RAG Response:")
            print(json.dumps(result, indent=2, default=str))
        except Exception as e:
            print(f"Error querying RAG: {str(e)}")
        return

    # If request is provided as argument, process it
    if args.request:
        try:
            if args.rag_query:
                # Query RAG component
                result = client.query_rag(args.request)
                print("RAG Response:")
                print(json.dumps(result, indent=2, default=str))
            else:
                # Query main agent
                result = client.query_agent(
                    user_request=args.request,
                    disable_sql_blocking=args.disable_sql_blocking,
                    disable_databases=args.disable_databases or DISABLE_DATABASES
                )
                print("Final Response:")
                print_markdown(result.get("final_response", "No response generated"))
                
                # Print additional information if in verbose mode
                if os.getenv("VERBOSE_OUTPUT", "").lower() == "true":
                    print("\nAdditional Information:")
                    print(f"Generated SQL: {result.get('generated_sql', 'N/A')}")
                    print(f"DB Results: {len(result.get('db_results', []))} records")
                    print(f"Retry Count: {result.get('retry_count', 0)}")
        except Exception as e:
            print(f"Error processing request: {str(e)}")
    else:
        # Interactive mode
        print("AI Agent Client is ready. Enter your natural language requests (type 'quit' to exit):")
        print(f"Mode: {'Backend API' if client.use_backend else 'Standalone'}")
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
                # Suppress heartbeat logs while waiting for user input
                suppress_heartbeats()

                user_input = input("\nYour request: ")

                # Show heartbeat logs again after user input
                show_heartbeats()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                # Check if this is a special command
                if user_input.lower().startswith('rag '):
                    # Process as RAG query
                    rag_query = user_input[4:].strip()  # Remove 'rag ' prefix
                    try:
                        result = client.query_rag(rag_query)
                        print("\nRAG Response:")
                        print(json.dumps(result, indent=2, default=str))
                    except Exception as e:
                        print(f"\nError querying RAG: {str(e)}")
                else:
                    # Process as main agent query
                    try:
                        result = client.query_agent(
                            user_request=user_input,
                            disable_sql_blocking=args.disable_sql_blocking,
                            disable_databases=args.disable_databases or DISABLE_DATABASES
                        )
                        print("\nFinal Response:")
                        print_markdown(result.get("final_response", "No response generated"))
                        
                        # Print additional information if in verbose mode
                        if os.getenv("VERBOSE_OUTPUT", "").lower() == "true":
                            print("\nAdditional Information:")
                            print(f"Generated SQL: {result.get('generated_sql', 'N/A')}")
                            print(f"DB Results: {len(result.get('db_results', []))} records")
                            print(f"Retry Count: {result.get('retry_count', 0)}")
                    except Exception as e:
                        print(f"\nError processing request: {str(e)}")

            except KeyboardInterrupt:
                # Show heartbeat logs again before exiting
                show_heartbeats()
                print("\nGoodbye!")
                break
            except Exception as e:
                # Show heartbeat logs again before showing error
                show_heartbeats()
                print(f"Error processing request: {str(e)}")


if __name__ == "__main__":
    main()