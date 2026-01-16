from utils.database import DatabaseManager
from models.sql_generator import SQLGenerator
from models.sql_executor import SQLExecutor
from models.prompt_generator import PromptGenerator
from models.response_generator import ResponseGenerator
from config.settings import ENABLE_SCREEN_LOGGING, DISABLE_DATABASES
import logging
import time

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self, database_url=None):
        # Initialize components
        from utils.multi_database_manager import multi_db_manager
        # Add the primary database if database_url is provided
        if database_url and not DISABLE_DATABASES:
            # Extract the real database name from the URL to use as the configuration name
            db_name = multi_db_manager._extract_db_name_from_url(database_url)
            multi_db_manager.add_database(db_name, database_url)
        elif not DISABLE_DATABASES:
            # Use the primary database from config if available
            from config.settings import DATABASE_URL
            if DATABASE_URL:
                # Extract the real database name from the URL to use as the configuration name
                db_name = multi_db_manager._extract_db_name_from_url(DATABASE_URL)
                multi_db_manager.add_database(db_name, DATABASE_URL)

        self.db_manager = multi_db_manager if not DISABLE_DATABASES else None
        self.sql_generator = SQLGenerator()
        self.sql_executor = SQLExecutor(self.db_manager) if not DISABLE_DATABASES else None  # Will use multi_db_manager by default
        self.prompt_generator = PromptGenerator()
        self.response_generator = ResponseGenerator()

        # Store the disable databases setting
        self.disable_databases = DISABLE_DATABASES

    def process_request(self, user_request, attached_files=None):
        """
        Process a natural language request from the user through all components
        """
        start_time = time.time()

        # Initialize conversation history to maintain full context
        conversation_history = [
            {"role": "user", "content": user_request}
        ]

        try:
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Processing request: {user_request}")

            # Check if databases are disabled
            if self.disable_databases:
                if ENABLE_SCREEN_LOGGING:
                    logger.info("Databases are disabled, skipping database operations")

                # Generate response without database results
                response_prompt = self.prompt_generator.generate_prompt_for_response_llm(
                    user_request, [], attached_files
                )

                # Add the prompt generator's response to conversation history
                conversation_history.append({"role": "system", "content": response_prompt})

                final_response = self.response_generator.generate_natural_language_response(
                    response_prompt, attached_files
                )

                # Add the final response to conversation history
                conversation_history.append({"role": "assistant", "content": final_response})

                end_time = time.time()
                processing_time = end_time - start_time

                return {
                    "original_request": user_request,
                    "generated_sql": None,
                    "db_results": None,
                    "final_response": final_response,
                    "processing_time": processing_time,
                    "conversation_history": conversation_history
                }

            # Step 1: Get database schema
            if ENABLE_SCREEN_LOGGING:
                logger.info("Getting database schema...")

            # Get all available database names
            all_databases = self.db_manager.list_databases()

            # Collect schema dumps from all databases
            combined_schema_dump = {}
            table_to_db_mapping = {}  # Map original table names to database names
            table_to_real_db_mapping = {}  # Map original table names to real database names

            for db_name in all_databases:
                try:
                    schema_dump = self.db_manager.get_schema_dump(db_name, use_real_name=True)

                    # Add all tables from this database to the combined schema
                    for table_name, table_info in schema_dump.items():
                        # Store the original table name
                        combined_schema_dump[table_name] = table_info

                        # Store mapping from original table name to database
                        table_to_db_mapping[table_name] = db_name

                        # Store mapping from original table name to real database name
                        from config.database_aliases import get_db_alias_mapper
                        db_alias_mapper = get_db_alias_mapper()
                        real_name = db_alias_mapper.get_real_name(db_name)
                        if real_name:
                            table_to_real_db_mapping[table_name] = real_name
                        else:
                            table_to_real_db_mapping[table_name] = db_name  # Use alias if no real name mapping

                    logger.info(f"Retrieved schema with {len(schema_dump)} tables from '{db_name}' database")
                except Exception as e:
                    logger.warning(f"Error retrieving schema from '{db_name}' database: {str(e)}")
                    # Continue with other databases even if one fails

            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Retrieved combined schema with {len(combined_schema_dump)} tables from {len(all_databases)} databases")

            # Step 2: Generate SQL query using first LLM
            if ENABLE_SCREEN_LOGGING:
                logger.info("Generating SQL query...")

            # Include conversation history in the SQL generation request
            sql_generation_context = f"Previous conversation:\n{self.format_conversation_history(conversation_history)}\n\nCurrent request: {user_request}"
            sql_query = self.sql_generator.generate_sql(sql_generation_context, combined_schema_dump, attached_files, table_to_db_mapping, table_to_real_db_mapping)

            # Add the SQL query to conversation history
            conversation_history.append({"role": "assistant", "content": f"Generated SQL: {sql_query}"})

            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Generated SQL: {sql_query}")

            # Step 3: Execute SQL query against database
            if ENABLE_SCREEN_LOGGING:
                logger.info("Executing SQL query...")

            # Execute the SQL query
            db_results = self.sql_executor.execute_sql_and_get_results(sql_query)
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Query executed, got {len(db_results)} results")

            # Step 3.5: If no results found, try wider search strategies
            if not db_results:
                if ENABLE_SCREEN_LOGGING:
                    logger.info("No results found with initial query. Trying wider search strategies...")

                # Generate a prompt for wider search strategies
                wider_search_context = f"""
                Previous conversation:
                {self.format_conversation_history(conversation_history)}

                The original user request was: "{user_request}"

                The database schema is:
                {self.format_schema_dump(combined_schema_dump)}

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
                    wider_search_context, attached_files, combined_schema_dump, table_to_db_mapping
                )

                if ENABLE_SCREEN_LOGGING:
                    logger.info(f"Wider search suggestions: {wider_search_suggestions}")

                # Add the wider search suggestions to conversation history
                conversation_history.append({"role": "assistant", "content": f"Wider search suggestions: {wider_search_suggestions}"})

                # Generate new SQL based on the wider suggestions
                # Include conversation history in the SQL generation request
                new_sql_generation_context = f"Previous conversation:\n{self.format_conversation_history(conversation_history)}\n\nWider search suggestions: {wider_search_suggestions}"
                new_sql_query = self.sql_generator.generate_sql(new_sql_generation_context, combined_schema_dump, attached_files, table_to_db_mapping, table_to_real_db_mapping)

                # Add the new SQL query to conversation history
                conversation_history.append({"role": "assistant", "content": f"Generated new SQL based on wider search: {new_sql_query}"})

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

            # Include conversation history in the prompt generation request
            prompt_generation_context = f"Previous conversation:\n{self.format_conversation_history(conversation_history)}\n\nCurrent request: {user_request}"
            response_prompt = self.prompt_generator.generate_prompt_for_response_llm(
                prompt_generation_context, db_results, attached_files
            )

            # Add the response prompt to conversation history
            conversation_history.append({"role": "system", "content": response_prompt})

            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Generated response prompt: {response_prompt}")  # Full content without truncation

            # Step 5: Generate natural language response using third LLM
            if ENABLE_SCREEN_LOGGING:
                logger.info("Generating natural language response...")

            # Include conversation history in the final response generation
            final_response_context = f"Previous conversation:\n{self.format_conversation_history(conversation_history)}\n\nResponse prompt: {response_prompt}"
            final_response = self.response_generator.generate_natural_language_response(
                final_response_context, attached_files
            )

            # Add the final response to conversation history
            conversation_history.append({"role": "assistant", "content": final_response})

            if ENABLE_SCREEN_LOGGING:
                logger.info(f"Final response: {final_response}")  # Full content without truncation

            end_time = time.time()
            processing_time = end_time - start_time

            return {
                "original_request": user_request,
                "generated_sql": sql_query,
                "db_results": db_results,
                "final_response": final_response,
                "processing_time": processing_time,
                "conversation_history": conversation_history
            }

        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            if ENABLE_SCREEN_LOGGING:
                logger.error(f"Error processing request: {str(e)}")

            # If databases are disabled, return a simpler response
            if self.disable_databases:
                # Generate a response without database results in case of error
                try:
                    # Include conversation history in the error fallback
                    error_fallback_context = f"Previous conversation:\n{self.format_conversation_history(conversation_history)}\n\nCurrent request: {user_request}"
                    response_prompt = self.prompt_generator.generate_prompt_for_response_llm(
                        error_fallback_context, [], attached_files
                    )

                    # Add the prompt to conversation history
                    conversation_history.append({"role": "system", "content": response_prompt})

                    final_response = self.response_generator.generate_natural_language_response(
                        response_prompt, attached_files
                    )

                    # Add the final response to conversation history
                    conversation_history.append({"role": "assistant", "content": final_response})

                    return {
                        "original_request": user_request,
                        "generated_sql": None,
                        "db_results": None,
                        "final_response": final_response,
                        "processing_time": processing_time,
                        "conversation_history": conversation_history
                    }
                except Exception as fallback_error:
                    # If even the fallback fails, return the error message
                    return {
                        "original_request": user_request,
                        "generated_sql": None,
                        "db_results": None,
                        "final_response": f"Error processing request: {str(fallback_error)}",
                        "processing_time": processing_time,
                        "conversation_history": conversation_history
                    }
            else:
                # Return error with processing time
                return {
                    "original_request": user_request,
                    "generated_sql": None,
                    "db_results": None,
                    "final_response": f"Error processing request: {str(e)}",
                    "processing_time": processing_time,
                    "conversation_history": conversation_history
                }


    def perform_additional_analysis(self, user_request, schema_dump):
        """
        Perform additional analysis based on schema and user request to find relevant data
        """
        # If databases are disabled, return empty results
        if self.disable_databases:
            return []

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
                Previous conversation:
                {self.format_conversation_history(conversation_history)}

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
                    Previous conversation:
                    {self.format_conversation_history(conversation_history)}

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
                Previous conversation:
                {self.format_conversation_history(conversation_history)}

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

    def format_conversation_history(self, conversation_history):
        """
        Format the conversation history into a readable string for inclusion in LLM prompts
        """
        formatted_history = ""
        for entry in conversation_history:
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            formatted_history += f"[{role.upper()}]: {content}\n\n"
        return formatted_history

    def format_schema_dump(self, schema_dump):
        """
        Format the schema dump into a readable string for the LLM
        """
        formatted = ""
        for table_name, table_info in schema_dump.items():
            # Handle both the old format (list of columns) and new format (dict with columns and comment)
            if isinstance(table_info, list):
                # Old format - backward compatibility
                columns = table_info
                table_comment = None
            else:
                # New format with comments
                columns = table_info.get('columns', [])
                table_comment = table_info.get('comment', None)

            formatted += f"\nTable: {table_name}"
            if table_comment:
                formatted += f" - Comment: {table_comment}"
            formatted += "\n"

            for col in columns:
                if isinstance(col, dict):
                    # New format with comments
                    col_info = f"  - {col['name']} ({col['type']}) - Nullable: {col['nullable']}"
                    if col.get('comment'):
                        col_info += f" - Comment: {col['comment']}"
                    formatted += col_info + "\n"
                else:
                    # Old format - backward compatibility
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