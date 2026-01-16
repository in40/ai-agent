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
    DEFAULT_LLM_MODEL, DEFAULT_LLM_HOSTNAME, DEFAULT_LLM_PORT, DEFAULT_LLM_API_PATH
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
        # Determine if we should use the default model configuration
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

        # Initialize the prompt manager
        self.prompt_manager = PromptManager()

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
                temperature=0.7,  # Slightly higher temperature for more natural responses
                api_key=api_key,
                base_url=base_url
            )

        # Define the prompt template for generating natural language responses using external prompt
        system_prompt = self.prompt_manager.get_prompt("response_generator")
        if system_prompt is None:
            # Fallback to default prompt if external prompt is not found
            system_prompt = "You are an expert at converting database results into natural language responses."

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{generated_prompt}")
        ])

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
                logger.info("ResponseGenerator full LLM request:")
                for i, message in enumerate(full_prompt):
                    logger.info(f"  Message {i+1} ({message.type}): {message.content}")

                # Log any attached files
                if attached_files:
                    logger.info(f"  Attached files: {len(attached_files)} file(s)")
                    for idx, file_info in enumerate(attached_files):
                        logger.info(f"    File {idx+1}: {file_info.get('filename', 'Unknown')} ({file_info.get('size', 'Unknown')} bytes)")

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

            return response_text

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Re-raise the exception to trigger the retry
            raise