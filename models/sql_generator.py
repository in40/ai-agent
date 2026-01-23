from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from config.settings import (
    SQL_LLM_PROVIDER, SQL_LLM_MODEL, SQL_LLM_HOSTNAME, SQL_LLM_PORT,
    SQL_LLM_API_PATH, OPENAI_API_KEY, DEEPSEEK_API_KEY, GIGACHAT_CREDENTIALS, GIGACHAT_SCOPE,
    GIGACHAT_ACCESS_TOKEN, GIGACHAT_VERIFY_SSL_CERTS, ENABLE_SCREEN_LOGGING, DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL, DEFAULT_LLM_HOSTNAME, DEFAULT_LLM_PORT, DEFAULT_LLM_API_PATH,
    FORCE_DEFAULT_MODEL_FOR_ALL
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
        # Check if we should force the default model for all components
        use_default = FORCE_DEFAULT_MODEL_FOR_ALL

        # If not forcing default globally, check if this specific component should use default
        if not use_default:
            # If SQL_LLM_PROVIDER is empty or set to "default", use the default configuration
            use_default = SQL_LLM_PROVIDER.lower() in ['', 'default']

        # Set the actual configuration values based on whether to use defaults
        if use_default:
            provider = DEFAULT_LLM_PROVIDER
            model = DEFAULT_LLM_MODEL
            hostname = DEFAULT_LLM_HOSTNAME
            port = DEFAULT_LLM_PORT
            api_path = DEFAULT_LLM_API_PATH
        else:
            provider = SQL_LLM_PROVIDER
            model = SQL_LLM_MODEL
            hostname = SQL_LLM_HOSTNAME
            port = SQL_LLM_PORT
            api_path = SQL_LLM_API_PATH

        # Log the configuration being used before creating the LLM
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"SQLGenerator configured with provider: {provider}, model: {model}")

        # Initialize the prompt manager
        self.prompt_manager = PromptManager("./core/prompts")

        # Define the prompt template for SQL generation using external prompt
        system_prompt = self.prompt_manager.get_prompt("sql_generator")
        if system_prompt is None:
            # If the external prompt is not found, raise an error to ensure prompts are maintained properly
            raise FileNotFoundError("sql_generator.txt not found in prompts directory. Please ensure the prompt file exists.")

        # Store the prompt name for logging
        self.prompt_name = "sql_generator"

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{user_request}")
        ])

        # Create the LLM with structured output based on the provider
        if provider.lower() == 'gigachat':
            # Import GigaChat model when needed
            from utils.gigachat_integration import GigaChatModel
            llm_base = GigaChatModel(
                model=model,
                temperature=0,  # Lower temperature for more consistent SQL generation
                credentials=GIGACHAT_CREDENTIALS,
                scope=GIGACHAT_SCOPE,
                access_token=GIGACHAT_ACCESS_TOKEN,
                verify_ssl_certs=GIGACHAT_VERIFY_SSL_CERTS
            )
            self.llm = llm_base.with_structured_output(SQLOutput)  # Use structured output
        elif provider.lower() == 'deepseek':
            # DeepSeek doesn't support structured output, so we'll use regular output and parse manually
            base_url = f"https://{hostname}:{port}{api_path}"
            api_key = DEEPSEEK_API_KEY or ("sk-fake-key" if base_url else DEEPSEEK_API_KEY)

            # Create the LLM with the determined base URL but without structured output
            llm_base = ChatOpenAI(
                model=model,
                temperature=0,  # Lower temperature for more consistent SQL generation
                api_key=api_key,
                base_url=base_url
            )
            self.llm = llm_base  # Don't use structured output for DeepSeek
            self.use_structured_output = False
        else:
            # Construct the base URL based on provider configuration for other providers
            if provider.lower() in ['openai', 'qwen']:
                # For cloud providers, use HTTPS with the specified hostname
                # But for default OpenAI, allow using the default endpoint
                if provider.lower() == 'openai' and hostname == "api.openai.com":
                    base_url = None  # Use default OpenAI endpoint
                else:
                    base_url = f"https://{hostname}:{port}{api_path}"
            else:
                # For local providers like LM Studio or Ollama, use custom base URL with HTTP
                base_url = f"http://{hostname}:{port}{api_path}"

            # Select the appropriate API key based on the provider
            api_key = OPENAI_API_KEY or ("sk-fake-key" if base_url else OPENAI_API_KEY)

            # Create the LLM with the determined base URL and structured output
            llm_base = ChatOpenAI(
                model=model,
                temperature=0,  # Lower temperature for more consistent SQL generation
                api_key=api_key,
                base_url=base_url
            )
            self.llm = llm_base.with_structured_output(SQLOutput)  # Use structured output
            self.use_structured_output = True

        # Create the chain
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
                logger.info(f"SQLGenerator full LLM request using prompt file: {self.prompt_name}")
                for i, message in enumerate(full_prompt):
                    if message.type == "system":
                        logger.info(f"  System Message {i+1}: {message.content}")  # Full content without truncation
                    else:
                        logger.info(f"  Message {i+1} ({message.type}): {message.content}")

                # Log any attached files
                if attached_files:
                    logger.info(f"  Attached files: {len(attached_files)} file(s)")
                    for idx, file_info in enumerate(attached_files):
                        logger.info(f"    File {idx+1}: {file_info.get('filename', 'Unknown')} ({file_info.get('size', 'Unknown')} bytes)")

            # Use SSH keep-alive during the LLM call
            with SSHKeepAliveContext():
                # Generate the SQL query
                response = self.chain.invoke({
                    "user_request": user_request,
                    "schema_dump": schema_str,
                    "db_mapping": db_mapping_str,
                    "previous_sql_queries": previous_sql_str
                })

            # Log the response
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"SQLGenerator response: {response}")

            # Handle response based on whether structured output is used
            if hasattr(self, 'use_structured_output') and not self.use_structured_output:
                # For providers that don't support structured output (like DeepSeek)
                # we need to extract the content from the response object
                # The response might be a LangChain message object with a content attribute
                if hasattr(response, 'content'):
                    # Extract the content from the LangChain message object
                    response_content = response.content
                else:
                    # If it's not a message object, use the response as-is
                    response_content = str(response)

                sql_query = self.clean_sql_response(response_content)
            else:
                # For providers that support structured output
                if isinstance(response, SQLOutput):
                    sql_query = response.sql_query
                else:
                    # Fallback to cleaning the string response if structured parsing fails
                    # Extract content if it's a message object
                    if hasattr(response, 'content'):
                        response_content = response.content
                    else:
                        response_content = str(response)

                    sql_query = self.clean_sql_response(response_content)

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
        import json

        # First, remove any content between ###ponder### tags and ###/ponder### tags
        # This removes the explanatory text that comes before the actual SQL
        response_without_ponder = re.sub(r'###ponder###.*?###/ponder###', '', response, flags=re.DOTALL)

        # Also remove any content between <thinking> tags and </thinking> tags
        # This is another common pattern for LLM reasoning sections
        response_without_thinking = re.sub(r'<thinking>.*?</thinking>', '', response_without_ponder, flags=re.DOTALL)

        # Use the cleaned response for further processing
        response = response_without_thinking

        # First, try to extract SQL between custom tags (in order of preference)
        # More specific tags for SQL extraction from DeepSeek and other models
        tag_patterns = [
            r'<sql_generated>(.*?)</sql_generated>',
            r'<sql_query>(.*?)</sql_query>',
            r'<sql_code>(.*?)</sql_code>',
            r'<sql>(.*?)</sql>',
            r'<sql_to_use>(.*?)</sql_to_use>'
        ]

        for pattern in tag_patterns:
            sql_match = re.search(pattern, response, re.DOTALL)
            if sql_match:
                sql_query = sql_match.group(1).strip()
                # Additional sanitization to remove system characters
                sql_query = self.sanitize_sql_query(sql_query)
                return sql_query

        # Try to parse the response as JSON and extract the sql_query field
        # This handles responses from models that don't support structured output
        try:
            # First, try to extract JSON from the response if it's embedded in a larger text
            # Look for JSON objects that might contain sql_query
            # This pattern looks for content that looks like a JSON object containing sql_query
            # It handles both single-line and multi-line JSON structures
            json_pattern = r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\"sql_query\"[^{}]*\})'
            json_match = re.search(json_pattern, response, re.DOTALL)

            if json_match:
                json_str = json_match.group(1)
                try:
                    parsed_json = json.loads(json_str)

                    if isinstance(parsed_json, dict) and 'sql_query' in parsed_json:
                        sql_query = parsed_json['sql_query'].strip()
                        # Additional sanitization to remove system characters
                        sql_query = self.sanitize_sql_query(sql_query)
                        return sql_query
                except json.JSONDecodeError:
                    # If the extracted string isn't valid JSON, continue to other methods
                    pass

            # If the entire response looks like a JSON object, try parsing it directly
            # First, try to strip any leading/trailing text that might surround the JSON
            stripped_response = response.strip()

            # Look for the first JSON object in the response
            start_idx = stripped_response.find('{')
            end_idx = stripped_response.rfind('}')

            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                json_str = stripped_response[start_idx:end_idx+1]
                try:
                    parsed_json = json.loads(json_str)
                    if isinstance(parsed_json, dict) and 'sql_query' in parsed_json:
                        sql_query = parsed_json['sql_query'].strip()
                        # Additional sanitization to remove system characters
                        sql_query = self.sanitize_sql_query(sql_query)
                        return sql_query
                except json.JSONDecodeError:
                    # If the entire response isn't valid JSON, continue to other methods
                    pass
        except Exception:
            # If any other error occurs during JSON parsing, continue with other methods
            pass

        # Additional check: If the response looks like a LangChain message object representation
        # e.g., content='{"sql_query": "..."}', try to extract the content part
        content_pattern = r"content='(\{.*\})'"
        content_match = re.search(content_pattern, response)
        if content_match:
            content_str = content_match.group(1)
            try:
                parsed_json = json.loads(content_str)
                if isinstance(parsed_json, dict) and 'sql_query' in parsed_json:
                    sql_query = parsed_json['sql_query'].strip()
                    # Additional sanitization to remove system characters
                    sql_query = self.sanitize_sql_query(sql_query)
                    return sql_query
            except json.JSONDecodeError:
                # If this fails, continue with other methods
                pass

        # Additional check: Handle cases where the JSON content has escaped quotes/newlines
        # This can happen with responses from some LLMs
        # Look for content='{' and try to extract the JSON portion
        # Use a more flexible pattern to match the content part
        content_start = response.find("content='")
        if content_start != -1:
            # Find the JSON part within the content
            json_start = response.find('{', content_start)
            if json_start != -1:
                # Find the matching closing brace
                brace_count = 0
                json_end = -1
                for i in range(json_start, len(response)):
                    if response[i] == '{':
                        brace_count += 1
                    elif response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i
                            break

                if json_end != -1:
                    json_part = response[json_start:json_end+1]
                    # Try to fix common escaping issues before parsing
                    # Replace double backslashes with single backslashes for newlines, etc.
                    json_part_fixed = json_part.replace('\\\\n', '\\n').replace('\\\\t', '\\t').replace('\\\\r', '\\r')
                    # Handle escaped quotes - first handle double quotes
                    json_part_fixed = json_part_fixed.replace('\\"', '"')
                    # Then handle single quotes in SQL strings - these should remain as single quotes
                    # The issue is that in the original response, single quotes in SQL are often escaped as \'
                    # But in JSON, this becomes a literal backslash+quote which is invalid
                    # So we need to be careful not to unescape these incorrectly
                    # Instead, let's try to fix the JSON by replacing \' with ' in contexts where it's likely SQL
                    import re
                    # Replace \' with ' but only when it appears to be inside SQL string literals
                    # This is a bit tricky, but we can look for patterns like ILIKE \'%...%\'
                    json_part_fixed = re.sub(r"ILIKE\s+'([^']*)\\\'([^']*)'", r"ILIKE '\1'\''\2'", json_part_fixed)
                    # A more general approach: replace escaped single quotes in contexts that look like SQL
                    # This is complex, so let's try a simpler approach - just replace \' with ' in the SQL query part
                    # But first, let's try to parse the JSON as is and handle the error differently

                    try:
                        parsed_json = json.loads(json_part_fixed)
                        if isinstance(parsed_json, dict) and 'sql_query' in parsed_json:
                            sql_query = parsed_json['sql_query'].strip()
                            # Additional sanitization to remove system characters
                            sql_query = self.sanitize_sql_query(sql_query)
                            return sql_query
                    except json.JSONDecodeError:
                        # If the JSON is still invalid, try a different approach
                        # Extract the SQL query using regex from the original JSON string
                        sql_query_match = re.search(r'"sql_query":\s*"((?:[^"\\]|\\.)*")', json_part)
                        if sql_query_match:
                            # Extract the SQL query part (still escaped)
                            escaped_sql = sql_query_match.group(1)
                            # Remove the outer quotes and handle escapes
                            # Remove the outer quotes
                            if escaped_sql.startswith('"') and escaped_sql.endswith('"'):
                                escaped_sql = escaped_sql[1:-1]

                            # Unescape common sequences
                            sql_query = escaped_sql.replace('\n', '\n').replace('\t', '\t').replace('\r', '\r')
                            sql_query = sql_query.replace('\\"', '"').replace("\\'", "'")

                            # Additional sanitization to remove system characters
                            sql_query = self.sanitize_sql_query(sql_query)
                            return sql_query

                        # If this also fails, continue with other methods
                        pass

        # If custom tags and JSON parsing aren't found, try to extract from markdown blocks
        # Look for SQL code blocks in markdown format
        markdown_match = re.search(r'```(?:sql)?\n(.*?)\n```', response, re.DOTALL)
        if markdown_match:
            sql_query = markdown_match.group(1).strip()
        else:
            # If no markdown blocks found, return the original response
            # This handles plain SQL without any formatting
            sql_query = response.strip()

        # Additional sanitization to remove system characters
        sql_query = self.sanitize_sql_query(sql_query)
        return sql_query

    def sanitize_sql_query(self, sql_query):
        """
        Sanitize SQL query to remove system characters and prevent injection
        """
        import re

        # Remove common escape sequences that might interfere with SQL execution
        # Replace escaped single quotes with regular single quotes
        sql_query = re.sub(r"\\'", "'", sql_query)

        # Replace other common escape sequences
        sql_query = sql_query.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')

        # Remove extra backslashes that might be used for escaping
        # This handles cases where the LLM might have added extra escaping
        sql_query = re.sub('\\\\\\\\', '\\\\', sql_query)

        # Remove any potential comment indicators that could be used maliciously
        # This is a basic protection against comment-based SQL injection
        sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)
        sql_query = re.sub(r'--.*', '', sql_query)

        # Check if the query originally ended with a semicolon before stripping
        original_ends_with_semicolon = sql_query.rstrip().endswith(';')

        # Remove any potential command terminators that could allow multiple statements
        # This is important for preventing stacked query attacks (only if there are multiple statements)
        # If the query only has one statement ending with ;, preserve the semicolon
        stripped_sql = sql_query.rstrip().rstrip(';')

        # Additional sanitization to remove any remaining leading/trailing whitespace
        result = stripped_sql.strip()

        # Add back the semicolon if the original query ended with one and we didn't find other statements
        # Count potential statement separators in the stripped result
        potential_statements = len([s for s in result.split(';') if s.strip()])
        if original_ends_with_semicolon and potential_statements == 1:
            result = result + ';'

        return result

    def _get_llm_instance(self, provider=None, model=None):
        """
        Returns the LLM instance for use by other components
        If provider or model are specified, creates a new instance with those parameters
        """
        if provider is not None or model is not None:
            # Use the specified provider/model or fall back to defaults
            use_provider = provider or getattr(self, '_default_provider', SQL_LLM_PROVIDER)
            use_model = model or getattr(self, '_default_model', SQL_LLM_MODEL)

            # Determine if we should use the default model configuration
            use_default = use_provider.lower() in ['', 'default']

            if use_default:
                actual_provider = DEFAULT_LLM_PROVIDER
                actual_model = DEFAULT_LLM_MODEL
                actual_hostname = DEFAULT_LLM_HOSTNAME
                actual_port = DEFAULT_LLM_PORT
                actual_api_path = DEFAULT_LLM_API_PATH
            else:
                actual_provider = use_provider
                actual_model = use_model
                # For simplicity, we'll use the same hostname/port/api_path as the main instance
                actual_hostname = getattr(self, '_default_hostname', SQL_LLM_HOSTNAME)
                actual_port = getattr(self, '_default_port', SQL_LLM_PORT)
                actual_api_path = getattr(self, '_default_api_path', SQL_LLM_API_PATH)

            # Create the LLM based on the provider
            if actual_provider.lower() == 'gigachat':
                from utils.gigachat_integration import GigaChatModel
                return GigaChatModel(
                    model=actual_model,
                    temperature=0.1,
                    credentials=GIGACHAT_CREDENTIALS,
                    scope=GIGACHAT_SCOPE,
                    access_token=GIGACHAT_ACCESS_TOKEN,
                    verify_ssl_certs=GIGACHAT_VERIFY_SSL_CERTS
                )
            else:
                # Construct the base URL based on provider configuration for other providers
                if actual_provider.lower() in ['openai', 'deepseek', 'qwen']:
                    # For cloud providers, use HTTPS with the specified hostname
                    if actual_provider.lower() == 'openai' and actual_hostname == "api.openai.com":
                        base_url = None  # Use default OpenAI endpoint
                    else:
                        base_url = f"https://{actual_hostname}:{actual_port}{actual_api_path}"
                else:
                    # For local providers like LM Studio or Ollama, use custom base URL with HTTP
                    base_url = f"http://{actual_hostname}:{actual_port}{actual_api_path}"

                # Select the appropriate API key based on the provider
                if actual_provider.lower() == 'deepseek':
                    api_key = DEEPSEEK_API_KEY or ("sk-fake-key" if base_url else DEEPSEEK_API_KEY)
                else:
                    api_key = OPENAI_API_KEY or ("sk-fake-key" if base_url else OPENAI_API_KEY)

                # Create the LLM with the determined base URL
                return ChatOpenAI(
                    model=actual_model,
                    temperature=0.1,
                    api_key=api_key,
                    base_url=base_url
                )
        else:
            # Return the default LLM instance
            return self.llm