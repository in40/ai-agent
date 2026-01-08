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

            # Step 3.5: If no results found, try wider search strategies
            if not db_results:
                if ENABLE_SCREEN_LOGGING:
                    logger.info("No results found with initial query. Trying wider search strategies...")

                # Generate a prompt for wider search strategies
                wider_search_context = f"""
                The original user request was: "{user_request}"

                The database schema is:
                {self.format_schema_dump(schema_dump)}

                The initial SQL query based on this request returned no results.

                Please suggest wider search strategies that could help find relevant data in the database.
                Consider the following approaches:
                1. Using LIKE operators with wildcards for partial matches
                2. Searching in related tables that might contain relevant information
                3. Using broader categories or classifications
                4. Looking for similar data patterns
                5. Using full-text search if available
                6. Suggesting alternative search terms based on the schema and column names

                Provide specific suggestions that reference actual table and column names from the schema.
                """

                # Use the prompt generator to get suggestions for wider search
                wider_search_suggestions = self.prompt_generator.generate_wider_search_prompt(
                    wider_search_context, attached_files
                )

                if ENABLE_SCREEN_LOGGING:
                    logger.info(f"Wider search suggestions: {wider_search_suggestions}")

                # Generate new SQL based on the wider suggestions
                new_sql_query = self.sql_generator.generate_sql(wider_search_suggestions, schema_dump, attached_files)
                if ENABLE_SCREEN_LOGGING:
                    logger.info(f"Generated new SQL based on wider search: {new_sql_query}")

                # Execute the new query
                new_db_results = self.sql_executor.execute_sql_and_get_results(new_sql_query)
                if ENABLE_SCREEN_LOGGING:
                    logger.info(f"New query executed, got {len(new_db_results)} results")

                # If we still have no results, try additional analysis
                if not new_db_results:
                    if ENABLE_SCREEN_LOGGING:
                        logger.info("Still no results. Performing additional analysis...")

                    # Perform additional analysis based on schema and data
                    additional_analysis_results = self.perform_additional_analysis(user_request, schema_dump)

                    # If we have additional analysis results, use them
                    if additional_analysis_results:
                        db_results = additional_analysis_results
                    else:
                        # If still no results, return a message indicating this
                        db_results = []
                else:
                    db_results = new_db_results
            # End of wider search logic

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


    def perform_additional_analysis(self, user_request, schema_dump):
        """
        Perform additional analysis based on schema and user request to find relevant data
        """
        results = []

        # Check if there are name-related columns in the schema
        name_columns = []
        for table_name, columns in schema_dump.items():
            for col in columns:
                if any(name_part in col['name'].lower() for name_part in ['name', 'first_name', 'last_name', 'surname', 'full_name']):
                    name_columns.append((table_name, col['name']))

        if name_columns:
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Found name-related columns: {name_columns}")

            # Query for all names in the database
            all_names = []
            for table_name, col_name in name_columns:
                try:
                    query = f"SELECT DISTINCT {col_name} FROM {table_name} WHERE {col_name} IS NOT NULL LIMIT 50"
                    names_results = self.sql_executor.execute_sql_and_get_results(query)
                    for row in names_results:
                        name_value = row[col_name]
                        if name_value and name_value not in all_names:
                            all_names.append(name_value)
                except Exception as e:
                    logger.warning(f"Could not query names from {table_name}.{col_name}: {str(e)}")

            if all_names:
                # Use the response generator to analyze names (e.g., gender detection)
                name_analysis_prompt = f"""
                Here is a list of names from the database: {', '.join(all_names[:20])} (showing first 20)

                Based on common knowledge, please categorize these names by gender (male/female/neutral)
                or provide other relevant insights about these names that might help with the original request: "{user_request}"

                If the original request was related to people, this analysis might provide useful context.
                """

                name_analysis = self.response_generator.generate_natural_language_response(
                    name_analysis_prompt
                )

                if ENABLE_SCREEN_LOGGING:
                    logger.info(f"Name analysis: {name_analysis}")

                # Add name analysis to results
                results.append({"analysis_type": "name_analysis", "content": name_analysis})

        # Check for other types of columns that might be analyzed
        email_columns = []
        phone_columns = []
        date_columns = []

        for table_name, columns in schema_dump.items():
            for col in columns:
                col_name_lower = col['name'].lower()
                if 'email' in col_name_lower:
                    email_columns.append((table_name, col['name']))
                elif any(phone_part in col_name_lower for phone_part in ['phone', 'tel', 'mobile', 'contact']):
                    phone_columns.append((table_name, col['name']))
                elif any(date_part in col_name_lower for date_part in ['date', 'created', 'updated', 'modified', 'timestamp']):
                    date_columns.append((table_name, col['name']))

        # Analyze email domains if any email columns exist
        if email_columns:
            all_emails = []
            for table_name, col_name in email_columns:
                try:
                    query = f"SELECT DISTINCT {col_name} FROM {table_name} WHERE {col_name} IS NOT NULL AND {col_name} != '' LIMIT 50"
                    emails_results = self.sql_executor.execute_sql_and_get_results(query)
                    for row in emails_results:
                        email_value = row[col_name]
                        if email_value and email_value not in all_emails:
                            all_emails.append(email_value)
                except Exception as e:
                    logger.warning(f"Could not query emails from {table_name}.{col_name}: {str(e)}")

            if all_emails:
                # Extract domains and analyze them
                domains = [email.split('@')[1] for email in all_emails if '@' in email]
                unique_domains = list(set(domains))

                if unique_domains:
                    domain_analysis_prompt = f"""
                    Here are the email domains found in the database: {', '.join(unique_domains[:10])}

                    Provide insights about these domains that might be relevant to the original request: "{user_request}"
                    For example, they might indicate company affiliations, geographic regions, or other patterns.
                    """

                    domain_analysis = self.response_generator.generate_natural_language_response(
                        domain_analysis_prompt
                    )

                    if ENABLE_SCREEN_LOGGING:
                        logger.info(f"Domain analysis: {domain_analysis}")

                    results.append({"analysis_type": "domain_analysis", "content": domain_analysis})

        # Analyze date ranges if any date columns exist
        if date_columns:
            date_info = []
            for table_name, col_name in date_columns:
                try:
                    query = f"""
                    SELECT
                        MIN({col_name}) as earliest_date,
                        MAX({col_name}) as latest_date,
                        COUNT({col_name}) as record_count
                    FROM {table_name}
                    WHERE {col_name} IS NOT NULL
                    """
                    date_results = self.sql_executor.execute_sql_and_get_results(query)
                    if date_results:
                        date_info.append({
                            "table": table_name,
                            "column": col_name,
                            "info": date_results[0]
                        })
                except Exception as e:
                    logger.warning(f"Could not query dates from {table_name}.{col_name}: {str(e)}")

            if date_info:
                date_analysis_prompt = f"""
                Here is date information from the database:
                {str(date_info)}

                Provide insights about these date ranges that might be relevant to the original request: "{user_request}"
                """

                date_analysis = self.response_generator.generate_natural_language_response(
                    date_analysis_prompt
                )

                if ENABLE_SCREEN_LOGGING:
                    logger.info(f"Date analysis: {date_analysis}")

                results.append({"analysis_type": "date_analysis", "content": date_analysis})

        # If we have any analysis results, return them; otherwise return empty list
        return results if results else []

    def format_schema_dump(self, schema_dump):
        """
        Format the schema dump into a readable string for the LLM
        """
        formatted = ""
        for table_name, columns in schema_dump.items():
            formatted += f"\nTable: {table_name}\n"
            for col in columns:
                formatted += f"  - {col['name']} ({col['type']}) - Nullable: {col['nullable']}\n"
        return formatted
    
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