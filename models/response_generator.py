from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from config.settings import (
    RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL, RESPONSE_LLM_HOSTNAME,
    RESPONSE_LLM_PORT, RESPONSE_LLM_API_PATH, OPENAI_API_KEY, DEEPSEEK_API_KEY,
    GIGACHAT_CREDENTIALS, GIGACHAT_SCOPE, GIGACHAT_ACCESS_TOKEN,
    GIGACHAT_VERIFY_SSL_CERTS, ENABLE_SCREEN_LOGGING, DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL, DEFAULT_LLM_HOSTNAME, DEFAULT_LLM_PORT, DEFAULT_LLM_API_PATH,
    FORCE_DEFAULT_MODEL_FOR_ALL
)
from utils.prompt_manager import PromptManager
from utils.ssh_keep_alive import SSHKeepAliveContext
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ResponseOutput(BaseModel):
    """Structured output for response generation"""
    response_text: str = Field(description="The generated natural language response")

class ResponseGenerator:
    def __init__(self):
        # Check if we should force the default model for all components
        use_default = FORCE_DEFAULT_MODEL_FOR_ALL

        # If not forcing default globally, check if this specific component should use default
        if not use_default:
            # If RESPONSE_LLM_PROVIDER is empty or set to "default", use the default configuration
            use_default = RESPONSE_LLM_PROVIDER.lower() in ['', 'default']

        # Set the actual configuration values based on whether to use defaults
        if use_default:
            provider = DEFAULT_LLM_PROVIDER
            model = DEFAULT_LLM_MODEL
            hostname = DEFAULT_LLM_HOSTNAME
            port = DEFAULT_LLM_PORT
            api_path = DEFAULT_LLM_API_PATH
        else:
            provider = RESPONSE_LLM_PROVIDER
            model = RESPONSE_LLM_MODEL
            hostname = RESPONSE_LLM_HOSTNAME
            port = RESPONSE_LLM_PORT
            api_path = RESPONSE_LLM_API_PATH

        # Log the configuration being used before creating the LLM
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"ResponseGenerator configured with provider: {provider}, model: {model}")

        # Initialize the prompt manager with the correct prompts directory
        self.prompt_manager = PromptManager("./core/prompts")

        # Define the prompt template for generating natural language responses using external prompt
        system_prompt = self.prompt_manager.get_prompt("response_generator")
        if system_prompt is None:
            # If the external prompt is not found, raise an error to ensure prompts are maintained properly
            raise FileNotFoundError("response_generator.txt not found in prompts directory. Please ensure the prompt file exists.")

        # Store the prompt name for logging
        self.prompt_name = "response_generator"

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{generated_prompt}")
        ])

        # Create the LLM based on the provider
        if provider.lower() == 'gigachat':
            # Import GigaChat model when needed
            from utils.gigachat_integration import GigaChatModel
            self.llm = GigaChatModel(
                model=model,
                temperature=0.7,  # Slightly higher temperature for more natural responses
                credentials=GIGACHAT_CREDENTIALS,
                scope=GIGACHAT_SCOPE,
                access_token=GIGACHAT_ACCESS_TOKEN,
                verify_ssl_certs=GIGACHAT_VERIFY_SSL_CERTS
            )
        else:
            # Construct the base URL based on provider configuration for other providers
            if provider.lower() in ['openai', 'deepseek', 'qwen']:
                # For cloud providers, use HTTPS with the specified hostname
                # But for default endpoints, allow using the default endpoint
                if (provider.lower() == 'openai' and hostname == "api.openai.com"):
                    base_url = None  # Use default OpenAI endpoint
                elif (provider.lower() == 'deepseek' and hostname == "api.deepseek.com"):
                    base_url = "https://api.deepseek.com"  # Use DeepSeek's API endpoint
                elif (provider.lower() == 'qwen' and hostname == "dashscope.aliyuncs.com"):
                    base_url = None  # Use default Qwen endpoint
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
                temperature=0.7,  # Slightly higher temperature for more natural responses
                api_key=api_key,
                base_url=base_url
            )

        # Create the output parser (keeping it for potential future use)
        self.output_parser = StrOutputParser()

        # Create the chain with the parser
        self.chain = self.prompt | self.llm | self.output_parser
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_natural_language_response(self, generated_prompt, attached_files=None):
        """
        Generate a natural language response based on the generated prompt
        """
        try:
            # Log the full request to LLM, including all roles and prompts
            if ENABLE_SCREEN_LOGGING:
                # Get the full prompt with all messages (system and human) without invoking the LLM
                full_prompt = self.prompt.format_messages(generated_prompt=generated_prompt)
                logger.info(f"ResponseGenerator full LLM request using prompt file: {self.prompt_name}")
                for i, message in enumerate(full_prompt):
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
            else:
                # Even when screen logging is disabled, log the content being sent for enhancement
                logger.info(f"[ENHANCEMENT_DEBUG] ResponseGenerator received request with prompt length: {len(generated_prompt)} characters")
                logger.info(f"[ENHANCEMENT_DEBUG] Full generated prompt being sent for enhancement: {generated_prompt}")

            # Use SSH keep-alive during the LLM call
            with SSHKeepAliveContext():
                response = self.chain.invoke({
                    "generated_prompt": generated_prompt
                })

            # Log the response
            if ENABLE_SCREEN_LOGGING:
                logger.info(f"ResponseGenerator response: {response}")

            # Try to parse as structured output first
            try:
                # Attempt to parse the response with the Pydantic parser
                parser = PydanticOutputParser(pydantic_object=ResponseOutput)
                structured_response = parser.parse(response)
                response_text = structured_response.response_text
            except Exception:
                # Fallback to returning the string response if structured parsing fails
                response_text = response

            # Log the full LLM request and response for debugging
            from utils.llm_request_logger import log_llm_request_details
            log_llm_request_details(
                provider=RESPONSE_LLM_PROVIDER,
                model=RESPONSE_LLM_MODEL,
                prompt=str(full_prompt) if 'full_prompt' in locals() else generated_prompt,
                response=response_text
            )

            return response_text

        except Exception as e:
            logger.error(f"Error generating response: {e}")

            # Log the error for debugging
            from utils.llm_request_logger import log_llm_request_details
            log_llm_request_details(
                provider=RESPONSE_LLM_PROVIDER,
                model=RESPONSE_LLM_MODEL,
                prompt=generated_prompt,
                error=str(e)
            )

            # Re-raise the exception to trigger the retry
            raise

    def generate_response(self, user_request=None, informational_content=None, generated_prompt=None, attached_files=None, previous_signals=None, previous_tool_calls=None):
        """
        Enhanced method to generate response with detailed logging of all inputs
        """
        # Log all the content being sent for enhancement
        logger.info(f"[ENHANCEMENT_DEBUG] generate_response called with:")
        if user_request is not None:
            logger.info(f"[ENHANCEMENT_DEBUG]   user_request: {user_request}")
        if informational_content is not None:
            logger.info(f"[ENHANCEMENT_DEBUG]   informational_content: {informational_content}")
        if previous_signals is not None:
            logger.info(f"[ENHANCEMENT_DEBUG]   previous_signals: {previous_signals}")
        if previous_tool_calls is not None:
            logger.info(f"[ENHANCEMENT_DEBUG]   previous_tool_calls: {previous_tool_calls}")

        # If generated_prompt is provided, use it directly
        if generated_prompt is not None:
            return self.generate_natural_language_response(generated_prompt, attached_files)

        # Otherwise, construct the prompt from user_request and informational_content
        if user_request is not None and informational_content is not None:
            # Construct a prompt combining user request and informational content
            combined_prompt = f"User Request: {user_request}\n\nInformational Content:\n{informational_content}"
            return self.generate_natural_language_response(combined_prompt, attached_files)

        # Fallback to original behavior if only generated_prompt is provided
        return self.generate_natural_language_response(user_request or generated_prompt, attached_files)

    def _get_llm_instance(self, provider=None, model=None):
        """
        Returns the LLM instance for use by other components (e.g., RAG)
        If provider or model are specified, creates a new instance with those parameters
        """
        if provider is not None or model is not None:
            # Use the specified provider/model or fall back to defaults
            use_provider = provider or getattr(self, '_default_provider', RESPONSE_LLM_PROVIDER)
            use_model = model or getattr(self, '_default_model', RESPONSE_LLM_MODEL)

            # Determine if we should use the default model configuration
            # Check if the provider is explicitly set to 'default'
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
                # In a more sophisticated implementation, you might want to pass these as well
                actual_hostname = getattr(self, '_default_hostname', RESPONSE_LLM_HOSTNAME)
                actual_port = getattr(self, '_default_port', RESPONSE_LLM_PORT)
                actual_api_path = getattr(self, '_default_api_path', RESPONSE_LLM_API_PATH)

            # Create the LLM based on the provider
            if actual_provider.lower() == 'gigachat':
                from utils.gigachat_integration import GigaChatModel
                return GigaChatModel(
                    model=actual_model,
                    temperature=0.7,
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
                    temperature=0.7,
                    api_key=api_key,
                    base_url=base_url
                )
        else:
            # Return the default LLM instance
            return self.llm