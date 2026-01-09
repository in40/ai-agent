from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import (
    PROMPT_LLM_PROVIDER, PROMPT_LLM_MODEL, PROMPT_LLM_HOSTNAME,
    PROMPT_LLM_PORT, PROMPT_LLM_API_PATH, OPENAI_API_KEY,
    GIGACHAT_CREDENTIALS, GIGACHAT_SCOPE, GIGACHAT_ACCESS_TOKEN, ENABLE_SCREEN_LOGGING
)
from utils.prompt_manager import PromptManager
import json
import logging

logger = logging.getLogger(__name__)

class PromptGenerator:
    def __init__(self):
        # Log the configuration being used before creating the LLM
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"PromptGenerator configured with provider: {PROMPT_LLM_PROVIDER}, model: {PROMPT_LLM_MODEL}")

        # Initialize the prompt manager
        self.prompt_manager = PromptManager()

        # Create the LLM based on the provider
        if PROMPT_LLM_PROVIDER.lower() == 'gigachat':
            # Import GigaChat model when needed
            from utils.gigachat_integration import GigaChatModel
            self.llm = GigaChatModel(
                model=PROMPT_LLM_MODEL,
                temperature=0.1,
                credentials=GIGACHAT_CREDENTIALS,
                scope=GIGACHAT_SCOPE,
                access_token=GIGACHAT_ACCESS_TOKEN,
                verify_ssl_certs=GIGACHAT_VERIFY_SSL_CERTS
            )
        else:
            # Construct the base URL based on provider configuration for other providers
            if PROMPT_LLM_PROVIDER.lower() in ['openai', 'deepseek', 'qwen']:
                # For cloud providers, use HTTPS unless hostname is not the standard one
                if PROMPT_LLM_HOSTNAME not in ["api.openai.com", "api.deepseek.com", "dashscope.aliyuncs.com"]:
                    base_url = f"https://{PROMPT_LLM_HOSTNAME}:{PROMPT_LLM_PORT}{PROMPT_LLM_API_PATH}"
                else:
                    base_url = None  # Use default OpenAI endpoint
            else:
                # For local providers like LM Studio or Ollama, use custom base URL with HTTP
                base_url = f"http://{PROMPT_LLM_HOSTNAME}:{PROMPT_LLM_PORT}{PROMPT_LLM_API_PATH}"

            # Create the LLM with the determined base URL
            self.llm = ChatOpenAI(
                model=PROMPT_LLM_MODEL,
                temperature=0.1,
                api_key=OPENAI_API_KEY or ("sk-fake-key" if base_url else OPENAI_API_KEY),
                base_url=base_url
            )

        # Define the prompt template for generating a prompt for the response LLM using external prompt
        system_prompt = self.prompt_manager.get_prompt("prompt_generator")
        if system_prompt is None:
            # Fallback to default prompt if external prompt is not found
            system_prompt = """You are an expert at creating detailed prompts for language models.
            Your task is to create a comprehensive prompt that will help another LLM generate
            a detailed natural language response based on database query results and the original user request.

            Guidelines:
            1. The prompt should include the original user request
            2. The prompt should include the database query results
            3. The prompt should guide the response LLM on how to format and structure the answer
            4. The prompt should specify the tone and level of detail required
            5. The prompt should ensure the response is in natural language and easy to understand
            """

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """Original user request: {user_request}

            Database query results: {db_results}

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

        # Generate the prompt for the response LLM
        response = self.chain.invoke({
            "user_request": user_request,
            "db_results": results_str
        })

        # Log the response
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"PromptGenerator response: {response}")

        return response

    def generate_wider_search_prompt(self, wider_search_context, attached_files=None):
        """
        Generate a prompt for wider search strategies when initial query returns no results
        """
        try:
            # Define the prompt template for generating wider search strategies using external prompt
            system_prompt = self.prompt_manager.get_prompt("wider_search_generator")
            if system_prompt is None:
                # Fallback to default prompt if external prompt is not found
                system_prompt = """You are an expert at analyzing database schemas and suggesting wider search strategies when initial queries return no results. Your task is to provide specific suggestions for alternative queries that might yield relevant data based on the database schema and the original user request.

    When the initial query returns no results, consider these strategies:
    1. Use LIKE operators with wildcards for partial matches
    2. Search in related tables that might contain relevant information
    3. Use broader categories or classifications
    4. Look for similar data patterns
    5. Use full-text search if available
    6. Suggest alternative search terms based on the schema and column names

    Always reference specific table and column names from the provided schema. Be creative but practical in your suggestions, and ensure they align with the user's original intent."""

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{wider_search_context}")
            ])

            # Create the chain for this specific task
            output_parser = StrOutputParser()
            chain = prompt | self.llm | output_parser

            # Log the full request to LLM, including all roles and prompts
            if ENABLE_SCREEN_LOGGING:
                # Get the full prompt with all messages (system and human) without invoking the LLM
                full_prompt = prompt.format_messages(
                    wider_search_context=wider_search_context
                )
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
                response = chain.invoke({
                    "wider_search_context": wider_search_context
                })

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
        Format database results into a readable string
        """
        if not db_results:
            return "No results found."
        
        # Convert the results to JSON string for readability
        return json.dumps(db_results, indent=2, default=str)