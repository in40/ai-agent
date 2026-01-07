from utils.database import DatabaseManager
from models.sql_generator import SQLGenerator
from models.sql_executor import SQLExecutor
from models.prompt_generator import PromptGenerator
from models.response_generator import ResponseGenerator
from config.settings import ENABLE_SCREEN_LOGGING
import logging
import time

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self, database_url=None):
        # Initialize components
        self.db_manager = DatabaseManager(database_url)
        self.sql_generator = SQLGenerator()
        self.sql_executor = SQLExecutor(self.db_manager)
        self.prompt_generator = PromptGenerator()
        self.response_generator = ResponseGenerator()
    
    def process_request(self, user_request, attached_files=None):
        """
        Process a natural language request from the user through all components
        """
        start_time = time.time()

        try:
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Processing request: {user_request}")

            # Step 1: Get database schema
            if ENABLE_SCREEN_LOGGING:
                logger.info("Getting database schema...")
            schema_dump = self.db_manager.get_schema_dump()
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Retrieved schema with {len(schema_dump)} tables")

            # Step 2: Generate SQL query using first LLM
            if ENABLE_SCREEN_LOGGING:
                logger.info("Generating SQL query...")
            sql_query = self.sql_generator.generate_sql(user_request, schema_dump, attached_files)
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Generated SQL: {sql_query}")

            # Step 3: Execute SQL query against database
            if ENABLE_SCREEN_LOGGING:
                logger.info("Executing SQL query...")
            db_results = self.sql_executor.execute_sql_and_get_results(sql_query)
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Query executed, got {len(db_results)} results")

            # Step 4: Generate prompt for response LLM using second LLM
            if ENABLE_SCREEN_LOGGING:
                logger.info("Generating prompt for response LLM...")
            response_prompt = self.prompt_generator.generate_prompt_for_response_llm(
                user_request, db_results, attached_files
            )
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Generated response prompt: {response_prompt[:100]}...")  # Truncate for log readability

            # Step 5: Generate natural language response using third LLM
            if ENABLE_SCREEN_LOGGING:
                logger.info("Generating natural language response...")
            final_response = self.response_generator.generate_natural_language_response(
                response_prompt, attached_files
            )
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Final response: {final_response[:100]}...")  # Truncate for log readability

            end_time = time.time()
            processing_time = end_time - start_time

            return {
                "original_request": user_request,
                "generated_sql": sql_query,
                "db_results": db_results,
                "final_response": final_response,
                "processing_time": processing_time
            }

        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            if ENABLE_SCREEN_LOGGING:
                logger.error(f"Error processing request: {str(e)}")
            # Return error with processing time
            return {
                "original_request": user_request,
                "generated_sql": None,
                "db_results": None,
                "final_response": f"Error processing request: {str(e)}",
                "processing_time": processing_time
            }
    
    def test_connection(self):
        """
        Test the database connection
        """
        return self.db_manager.test_connection()

    def refresh_schema(self):
        """
        Force a refresh of the database schema cache
        """
        self.db_manager.clear_schema_cache()
        logger.info("Database schema cache refreshed")