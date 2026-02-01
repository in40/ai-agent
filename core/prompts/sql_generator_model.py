from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from config.settings import (
    SQL_LLM_PROVIDER, SQL_LLM_MODEL, SQL_LLM_HOSTNAME, SQL_LLM_PORT,
    SQL_LLM_API_PATH, OPENAI_API_KEY, DEEPSEEK_API_KEY, GIGACHAT_CREDENTIALS, GIGACHAT_SCOPE,
    GIGACHAT_ACCESS_TOKEN, GIGACHAT_VERIFY_SSL_CERTS, ENABLE_SCREEN_LOGGING
)
from utils.prompt_manager import PromptManager
from utils.ssh_keep_alive import SSHKeepAliveContext
import json
import logging
import re
import time
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class SQLOutput(BaseModel):
    """Structured output for SQL generation"""
    sql_query: str = Field(description="The generated SQL query")

class SQLGenerator:
    def __init__(self):
        # Log the configuration being used before creating the LLM
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"SQLGenerator configured with provider: {SQL_LLM_PROVIDER}, model: {SQL_LLM_MODEL}")

        # Initialize the prompt manager
        self.prompt_manager = PromptManager("./core/prompts")

        # Define the prompt template for SQL generation using external prompt
        system_prompt = self.prompt_manager.get_prompt("sql_generator")
        if system_prompt is None:
            # Fallback to default prompt if external prompt is not found
            system_prompt = """You are an expert SQL developer. Your task is to generate correct SQL queries based on natural language requests.

            Database schema:
            {schema_dump}

            {db_mapping}

            Instructions:
            1. Generate only the SQL query without any additional text or explanation
            2. Use proper SQL syntax for PostgreSQL
            3. Make sure the query is safe and doesn't include any harmful commands
            4. Use appropriate JOINs if needed to connect related tables
            5. If the request is ambiguous, make reasonable assumptions based on the schema
            6. Always use table aliases for better readability
            7. Limit results if the query could return a large dataset unless specifically asked for all records
            8. Use only tables available in the schema, don't make up any tables and table's names.
            9. When referencing tables, use only the table name without database prefixes (PostgreSQL doesn't support cross-database references in a single query)
            10. For example: customers, products (NOT sales_db.public.customers)
            11. Respond with a JSON object containing the following field:
                - sql_query: The generated SQL query
            12. Respond ONLY with the JSON object, nothing else.
            """

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{user_request}")
        ])

        # Create the LLM with structured output based on the provider
        if SQL_LLM_PROVIDER.lower() == 'gigachat':
            # Import GigaChat model when needed
            from utils.gigachat_integration import GigaChatModel
            llm_base = GigaChatModel(
                model=SQL_LLM_MODEL,
                temperature=0,  # Lower temperature for more consistent SQL generation
                credentials=GIGACHAT_CREDENTIALS,
                scope=GIGACHAT_SCOPE,
                access_token=GIGACHAT_ACCESS_TOKEN,
                verify_ssl_certs=GIGACHAT_VERIFY_SSL_CERTS
            )
            self.llm = llm_base.with_structured_output(SQLOutput)  # Use structured output
        else:
            # Construct the base URL based on provider configuration for other providers
            if SQL_LLM_PROVIDER.lower() in ['openai', 'deepseek', 'qwen']:
                # For cloud providers, use HTTPS with the specified hostname
                # But for default OpenAI, allow using the default endpoint
                if SQL_LLM_PROVIDER.lower() == 'openai' and SQL_LLM_HOSTNAME == "api.openai.com":
                    base_url = None  # Use default OpenAI endpoint
                else:
                    base_url = f"https://{SQL_LLM_HOSTNAME}:{SQL_LLM_PORT}{SQL_LLM_API_PATH}"
            else:
                # For local providers like LM Studio or Ollama, use custom base URL with HTTP
                base_url = f"http://{SQL_LLM_HOSTNAME}:{SQL_LLM_PORT}{SQL_LLM_API_PATH}"

            # Select the appropriate API key based on the provider
            if SQL_LLM_PROVIDER.lower() == 'deepseek':
                api_key = DEEPSEEK_API_KEY or ("sk-fake-key" if base_url else DEEPSEEK_API_KEY)
            else:
                api_key = OPENAI_API_KEY or ("sk-fake-key" if base_url else OPENAI_API_KEY)

            # Create the LLM with the determined base URL and structured output
            llm_base = ChatOpenAI(
                model=SQL_LLM_MODEL,
                temperature=0,  # Lower temperature for more consistent SQL generation
                api_key=api_key,
                base_url=base_url
            )
            self.llm = llm_base.with_structured_output(SQLOutput)  # Use structured output

        # Create the chain - no need for separate output parser since we're using with_structured_output
        self.chain = self.prompt | self.llm
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_sql(self, user_request, schema_dump, attached_files=None, previous_sql_queries=None, table_to_db_mapping=None, table_to_real_db_mapping=None):
        """
        Generate SQL query based on user request and database schema
        """
        # Format the schema dump as a string for the prompt, including database grouping if available
        schema_str = self.format_schema_dump(schema_dump, table_to_db_mapping, table_to_real_db_mapping)

        # Format the database mapping information if provided
        db_mapping_str = self.format_database_mapping(table_to_db_mapping, table_to_real_db_mapping) if table_to_db_mapping else ""

        # Format the previous SQL queries for the prompt
        if previous_sql_queries:
            previous_sql_str = "\n".join([f"- {query}" for query in previous_sql_queries])
        else:
            previous_sql_str = "No previous SQL queries."

        try:
            # Log the full request to LLM, including all roles and prompts
            if ENABLE_SCREEN_LOGGING:
                # Get the full prompt with all messages (system and human) without invoking the LLM
                full_prompt = self.prompt.format_messages(
                    user_request=user_request,
                    schema_dump=schema_str,
                    db_mapping=db_mapping_str,
                    previous_sql_queries=previous_sql_str
                )
                logger.info("SQLGenerator full LLM request:")
                for i, message in enumerate(full_prompt):
                    if message.type == "system":
                        logger.info(f"  System Message {i+1}:")
                        # Log the full content in chunks to avoid any potential truncation
                        content = message.content
                        chunk_size = 2000  # Size of each chunk
                        for j in range(0, len(content), chunk_size):
                            chunk = content[j:j+chunk_size]
                            logger.info(f"    Chunk {j//chunk_size + 1}: {chunk}")
                    else:
                        logger.info(f"  Message {i+1} ({message.type}):")
                        # Log the full content in chunks to avoid any potential truncation
                        content = message.content
                        chunk_size = 2000  # Size of each chunk
                        for j in range(0, len(content), chunk_size):
                            chunk = content[j:j+chunk_size]
                            logger.info(f"    Chunk {j//chunk_size + 1}: {chunk}")

                # Log any attached files
                if attached_files:
                    logger.info(f"  Attached files: {len(attached_files)} file(s)")
                    for idx, file_info in enumerate(attached_files):
                        logger.info(f"    File {idx+1}: {file_info.get('filename', 'Unknown')} ({file_info.get('size', 'Unknown')} bytes)")

            # Use SSH keep-alive during the LLM call
            with SSHKeepAliveContext():
                # Generate the SQL query
                structured_response = self.chain.invoke({
                    "user_request": user_request,
                    "schema_dump": schema_str,
                    "db_mapping": db_mapping_str,
                    "previous_sql_queries": previous_sql_str
                })

            # Log the response
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"SQLGenerator response: {structured_response}")

            # Since we're using Pydantic parser, the response should already be structured
            if isinstance(structured_response, SQLOutput):
                sql_query = structured_response.sql_query
            else:
                # Fallback to cleaning the string response if structured parsing fails
                sql_query = self.clean_sql_response(str(structured_response))

            return sql_query

        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            # Re-raise the exception to trigger the retry
            raise

    def format_database_mapping(self, table_to_db_mapping, table_to_real_db_mapping=None):
        """
        Format the table-to-database mapping into a readable string for the LLM
        """
        if not table_to_db_mapping:
            return ""

        # Group tables by database for better organization
        db_to_tables = {}
        for table_name, db_name in table_to_db_mapping.items():
            if db_name not in db_to_tables:
                db_to_tables[db_name] = []
            db_to_tables[db_name].append(table_name)

        formatted = "\nDatabase mapping information:\n"
        for db_name, tables in db_to_tables.items():
            # Use real database name if available, otherwise use the alias
            display_name = db_name
            if table_to_real_db_mapping:
                for table_name, real_db_name in table_to_real_db_mapping.items():
                    if table_name in tables:
                        display_name = real_db_name
                        break

            formatted += f"\nDatabase '{display_name}' contains tables: {', '.join(tables)}\n"

            # Add a note about which columns exist in which databases if needed
            # This is handled in the schema formatting below

        return formatted
    
    def format_schema_dump(self, schema_dump, table_to_db_mapping=None, table_to_real_db_mapping=None):
        """
        Format the schema dump into a readable string for the LLM
        If table_to_db_mapping is provided, group tables by database
        """
        if table_to_db_mapping:
            # Group tables by database for better organization
            db_to_tables = {}
            for table_name in schema_dump.keys():
                if table_name in table_to_db_mapping:
                    db_name = table_to_db_mapping[table_name]
                    if db_name not in db_to_tables:
                        db_to_tables[db_name] = []
                    db_to_tables[db_name].append(table_name)

            formatted = ""
            for db_name, tables in db_to_tables.items():
                # Use real database name if available, otherwise use the alias
                display_name = db_name
                if table_to_real_db_mapping and db_name in table_to_real_db_mapping.values():
                    # Find the corresponding real name for this database
                    for table, real_name in table_to_real_db_mapping.items():
                        if table in tables:
                            display_name = real_name
                            break

                formatted += f"\n=== DATABASE: {display_name} ===\n"

                for table_name in tables:
                    table_info = schema_dump[table_name]

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
                formatted += "\n"  # Extra newline between databases
        else:
            # Original format without database grouping
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
    
    def clean_sql_response(self, response):
        """
        Clean up the LLM response to extract just the SQL query
        """
        import re

        # First, try to extract SQL between custom tags
        sql_match = re.search(r'<sql_to_use>(.*?)</sql_to_use>', response, re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1).strip()
        else:
            # If custom tags aren't found, try to extract from markdown blocks
            sql_query = response.strip()

            # Remove markdown code block markers
            if sql_query.startswith("```sql"):
                sql_query = sql_query[5:]  # Remove ```sql
            elif sql_query.startswith("```"):
                sql_query = sql_query[3:]  # Remove ```

            if sql_query.endswith("```"):
                sql_query = sql_query[:-3]  # Remove ```

        # Remove any remaining leading/trailing whitespace
        return sql_query.strip()