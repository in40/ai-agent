from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import (
    PROMPT_LLM_PROVIDER, PROMPT_LLM_MODEL, PROMPT_LLM_HOSTNAME,
    PROMPT_LLM_PORT, PROMPT_LLM_API_PATH, OPENAI_API_KEY, DEEPSEEK_API_KEY,
    GIGACHAT_CREDENTIALS, GIGACHAT_SCOPE, GIGACHAT_ACCESS_TOKEN,
    GIGACHAT_VERIFY_SSL_CERTS, ENABLE_SCREEN_LOGGING, DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL, DEFAULT_LLM_HOSTNAME, DEFAULT_LLM_PORT, DEFAULT_LLM_API_PATH,
    FORCE_DEFAULT_MODEL_FOR_ALL
)
from utils.prompt_manager import PromptManager
from utils.ssh_keep_alive import SSHKeepAliveContext
import json
import logging
import uuid

logger = logging.getLogger(__name__)

class PromptGenerator:
    def __init__(self):
        # Check if we should force the default model for all components
        use_default = FORCE_DEFAULT_MODEL_FOR_ALL

        # If not forcing default globally, check if this specific component should use default
        if not use_default:
            # If PROMPT_LLM_PROVIDER is empty or set to "default", use the default configuration
            use_default = PROMPT_LLM_PROVIDER.lower() in ['', 'default']

        # Set the actual configuration values based on whether to use defaults
        if use_default:
            provider = DEFAULT_LLM_PROVIDER
            model = DEFAULT_LLM_MODEL
            hostname = DEFAULT_LLM_HOSTNAME
            port = DEFAULT_LLM_PORT
            api_path = DEFAULT_LLM_API_PATH
        else:
            provider = PROMPT_LLM_PROVIDER
            model = PROMPT_LLM_MODEL
            hostname = PROMPT_LLM_HOSTNAME
            port = PROMPT_LLM_PORT
            api_path = PROMPT_LLM_API_PATH

        # Log the configuration being used before creating the LLM
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"PromptGenerator configured with provider: {provider}, model: {model}")

        # Initialize the prompt manager with the correct prompts directory
        self.prompt_manager = PromptManager("./core/prompts")

        # Create the LLM based on the provider
        if provider.lower() == 'gigachat':
            # Import GigaChat model when needed
            from utils.gigachat_integration import GigaChatModel
            self.llm = GigaChatModel(
                model=model,
                temperature=0.1,
                credentials=GIGACHAT_CREDENTIALS,
                scope=GIGACHAT_SCOPE,
                access_token=GIGACHAT_ACCESS_TOKEN,
                verify_ssl_certs=GIGACHAT_VERIFY_SSL_CERTS
            )
        else:
            # Construct the base URL based on provider configuration for other providers
            if provider.lower() in ['openai', 'deepseek', 'qwen']:
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
            if provider.lower() == 'deepseek':
                api_key = DEEPSEEK_API_KEY or ("sk-fake-key" if base_url else DEEPSEEK_API_KEY)
            else:
                api_key = OPENAI_API_KEY or ("sk-fake-key" if base_url else OPENAI_API_KEY)

            # Create the LLM with the determined base URL
            self.llm = ChatOpenAI(
                model=model,
                temperature=0.1,
                api_key=api_key,
                base_url=base_url
            )

        # Define the prompt template for generating a prompt for the response LLM using external prompt
        system_prompt = self.prompt_manager.get_prompt("prompt_generator")
        if system_prompt is None:
            # If the external prompt is not found, raise an error to ensure prompts are maintained properly
            raise FileNotFoundError("prompt_generator.txt not found in prompts directory. Please ensure the prompt file exists.")

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """Original user request: {user_request}

            Query results: {db_results}

            Create a detailed prompt for another LLM to generate a natural language response based on these results.""")
        ])

        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser
    
    def generate_prompt_for_response_llm(self, user_request, db_results, attached_files=None):
        """
        Generate a detailed prompt for the response LLM based on user request and database results
        """
        # Format the database results as a string
        results_str = self.format_db_results(db_results)

        # Log the full request to LLM, including all roles and prompts
        if ENABLE_SCREEN_LOGGING:
            # Get the full prompt with all messages (system and human) without invoking the LLM
            full_prompt = self.prompt.format_messages(
                user_request=user_request,
                db_results=results_str
            )
            logger.info("PromptGenerator full LLM request:")
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
            # Generate the prompt for the response LLM
            response = self.chain.invoke({
                "user_request": user_request,
                "db_results": results_str
            })

        # Log the response
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"PromptGenerator response: {response}")

        return response

    def generate_wider_search_prompt(self, wider_search_context, attached_files=None, schema_dump=None, db_mapping=None, previous_sql_queries=None):
        """
        Generate a prompt for wider search strategies when initial query returns no results
        """
        try:
            # Define the prompt template for generating wider search strategies using external prompt
            system_prompt = self.prompt_manager.get_prompt("wider_search_generator")
            if system_prompt is None:
                # If the external prompt is not found, raise an error to ensure prompts are maintained properly
                raise FileNotFoundError("wider_search_generator.txt not found in prompts directory. Please ensure the prompt file exists.")

            # Check if the template expects specific variables
            has_schema_dump = "{schema_dump}" in system_prompt
            has_db_mapping = "{db_mapping}" in system_prompt
            has_prev_queries = "{previous_sql_queries}" in system_prompt
            has_wider_context = "{wider_search_context}" in system_prompt

            # Format the previous SQL queries for the prompt if provided
            if previous_sql_queries:
                previous_sql_str = "\n".join([f"- {query}" for query in previous_sql_queries])
            else:
                previous_sql_str = "No previous SQL queries."

            # Create the prompt template based on required variables
            if has_schema_dump or has_db_mapping or has_prev_queries:
                # Template expects specific variables in the system message
                # Need to handle the formatting carefully to avoid conflicts with curly braces in schema/db_mapping
                schema_str = str(schema_dump) if schema_dump else ""
                db_map_str = str(db_mapping) if db_mapping else ""

                # To avoid format conflicts, we'll use temporary unique placeholders
                # that won't conflict with content in the schema/db_mapping
                import uuid
                prev_queries_placeholder = f"__TEMP_PREV_QUERIES_{uuid.uuid4()}__"
                schema_dump_placeholder = f"__TEMP_SCHEMA_DUMP_{uuid.uuid4()}__"
                db_mapping_placeholder = f"__TEMP_DB_MAPPING_{uuid.uuid4()}__"

                # Create a copy of the system prompt to work with
                system_prompt_work = system_prompt

                # Replace the placeholders with temporary unique ones
                if has_prev_queries:
                    system_prompt_work = system_prompt_work.replace("{previous_sql_queries}", prev_queries_placeholder)

                if has_schema_dump:
                    system_prompt_work = system_prompt_work.replace("{schema_dump}", schema_dump_placeholder)

                if has_db_mapping:
                    system_prompt_work = system_prompt_work.replace("{db_mapping}", db_mapping_placeholder)

                # Now safely replace the temporary placeholders with actual values,
                # properly escaping any curly braces in the content
                if has_prev_queries:
                    # Escape curly braces in previous_sql_str to prevent format conflicts
                    escaped_prev_queries = previous_sql_str.replace('{', '{{').replace('}', '}}')
                    system_prompt_work = system_prompt_work.replace(prev_queries_placeholder, escaped_prev_queries)

                if has_schema_dump:
                    # Escape curly braces in schema_str to prevent format conflicts
                    escaped_schema = schema_str.replace('{', '{{').replace('}', '}}')
                    system_prompt_work = system_prompt_work.replace(schema_dump_placeholder, escaped_schema)

                if has_db_mapping:
                    # Escape curly braces in db_map_str to prevent format conflicts
                    escaped_db_mapping = db_map_str.replace('{', '{{').replace('}', '}}')
                    system_prompt_work = system_prompt_work.replace(db_mapping_placeholder, escaped_db_mapping)

                # The wider_search_context should always be in the human message part
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt_work),
                    ("human", "{wider_search_context}")
                ])
                prompt_kwargs = {
                    "wider_search_context": wider_search_context
                }
            else:
                # Template expects wider_search_context variable in human message
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", "{wider_search_context}")
                ])

                # Prepare the arguments for the prompt
                prompt_kwargs = {
                    "wider_search_context": wider_search_context
                }

            # Create the chain for this specific task
            output_parser = StrOutputParser()
            chain = prompt | self.llm | output_parser

            # Log the full request to LLM, including all roles and prompts
            if ENABLE_SCREEN_LOGGING:
                # Get the full prompt with all messages (system and human) without invoking the LLM
                full_prompt = prompt.format_messages(**prompt_kwargs)
                logger.info("PromptGenerator wider search LLM request:")
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

            # Generate the wider search prompt - wrap this in additional error handling
            try:
                # Use SSH keep-alive during the LLM call
                with SSHKeepAliveContext():
                    response = chain.invoke(prompt_kwargs)

                # Log the raw response type and content for debugging
                logger.debug(f"Raw response type: {type(response)}, content: {repr(response)}")
            except Exception as chain_error:
                logger.error(f"Error during chain invocation: {str(chain_error)}")
                logger.error(f"Chain error type: {type(chain_error)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Return a default suggestion if the chain fails
                return """Consider these alternative search strategies:
        1. Try searching with broader terms or synonyms
        2. Look in related tables that might contain the information
        3. Use wildcards to match partial data
        4. Check if the data exists in a different format or spelling"""

            # Ensure the response is a string
            if isinstance(response, dict):
                # If response is a dictionary, try to extract the content
                if hasattr(response, 'content'):
                    response = response.content
                elif 'content' in response:
                    response = response['content']
                elif 'text' in response:
                    response = response['text']
                else:
                    # If it's a dict but doesn't have expected keys, convert to string
                    response = str(response)
            elif isinstance(response, (list, tuple)):
                # If response is a list/tuple, convert to string
                response = str(response)
            elif hasattr(response, '__dict__') and hasattr(response, 'content'):
                # If response is an object with content attribute (like AIMessage)
                response = response.content
            elif not isinstance(response, str):
                # If it's anything else, convert to string
                response = str(response)

            # Log the response
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"PromptGenerator wider search response: {response}")

            return response
        except Exception as e:
            logger.error(f"Error in generate_wider_search_prompt: {str(e)}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

            # Return a default suggestion if the LLM call fails
            return """Consider these alternative search strategies:
    1. Try searching with broader terms or synonyms
    2. Look in related tables that might contain the information
    3. Use wildcards to match partial data
    4. Check if the data exists in a different format or spelling"""
    
    def format_db_results(self, db_results):
        """
        Format results into a readable string, distinguishing between different sources
        """
        if not db_results:
            return "No results found."

        # Separate results by source
        db_results_list = []
        mcp_results_list = []
        other_results_list = []

        for result in db_results:
            if isinstance(result, dict):
                source = result.get("_source", "DATABASE")  # Default to DATABASE for backward compatibility
                if source == "MCP_SERVICE":
                    mcp_results_list.append(result)
                elif source == "DATABASE":
                    db_results_list.append(result)
                else:
                    other_results_list.append(result)
            else:
                # If result is not a dict, treat as database result for backward compatibility
                db_results_list.append(result)

        # Format each category separately
        formatted_parts = []

        if db_results_list:
            formatted_parts.append("Database query results:")
            formatted_parts.append(json.dumps(db_results_list, indent=2, default=str))

        if mcp_results_list:
            formatted_parts.append("MCP service results:")
            formatted_parts.append(json.dumps(mcp_results_list, indent=2, default=str))

        if other_results_list:
            formatted_parts.append("Other results:")
            formatted_parts.append(json.dumps(other_results_list, indent=2, default=str))

        return "\n\n".join(formatted_parts)

    def _get_llm_instance(self, provider=None, model=None):
        """
        Returns the LLM instance for use by other components
        If provider or model are specified, creates a new instance with those parameters
        """
        if provider is not None or model is not None:
            # Use the specified provider/model or fall back to defaults
            use_provider = provider or getattr(self, "_default_provider", PROMPT_LLM_PROVIDER)
            use_model = model or getattr(self, "_default_model", PROMPT_LLM_MODEL)

            # Determine if we should use the default model configuration
            use_default = use_provider.lower() in ["", "default"]

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
                actual_hostname = getattr(self, "_default_hostname", PROMPT_LLM_HOSTNAME)
                actual_port = getattr(self, "_default_port", PROMPT_LLM_PORT)
                actual_api_path = getattr(self, "_default_api_path", PROMPT_LLM_API_PATH)

            # Create the LLM based on the provider
            if actual_provider.lower() == "gigachat":
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
                if actual_provider.lower() in ["openai", "deepseek", "qwen"]:
                    # For cloud providers, use HTTPS with the specified hostname
                    if actual_provider.lower() == "openai" and actual_hostname == "api.openai.com":
                        base_url = None  # Use default OpenAI endpoint
                    else:
                        base_url = f"https://{actual_hostname}:{actual_port}{actual_api_path}"
                else:
                    # For local providers like LM Studio or Ollama, use custom base URL with HTTP
                    base_url = f"http://{actual_hostname}:{actual_port}{actual_api_path}"

                # Select the appropriate API key based on the provider
                if actual_provider.lower() == "deepseek":
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