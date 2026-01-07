from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import (
    RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL, RESPONSE_LLM_HOSTNAME,
    RESPONSE_LLM_PORT, RESPONSE_LLM_API_PATH, OPENAI_API_KEY,
    GIGACHAT_CREDENTIALS, GIGACHAT_SCOPE, GIGACHAT_ACCESS_TOKEN, ENABLE_SCREEN_LOGGING
)
import logging

logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self):
        # Log the configuration being used before creating the LLM
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"ResponseGenerator configured with provider: {RESPONSE_LLM_PROVIDER}, model: {RESPONSE_LLM_MODEL}")

        # Create the LLM based on the provider
        if RESPONSE_LLM_PROVIDER.lower() == 'gigachat':
            # Import GigaChat model when needed
            from utils.gigachat_integration import GigaChatModel
            self.llm = GigaChatModel(
                model=RESPONSE_LLM_MODEL,
                temperature=0.7,  # Slightly higher temperature for more natural responses
                credentials=GIGACHAT_CREDENTIALS,
                scope=GIGACHAT_SCOPE,
                access_token=GIGACHAT_ACCESS_TOKEN,
                verify_ssl_certs=GIGACHAT_VERIFY_SSL_CERTS
            )
        else:
            # Construct the base URL based on provider configuration for other providers
            if RESPONSE_LLM_PROVIDER.lower() in ['openai', 'deepseek', 'qwen']:
                # For cloud providers, use HTTPS unless hostname is not the standard one
                if RESPONSE_LLM_HOSTNAME not in ["api.openai.com", "api.deepseek.com", "dashscope.aliyuncs.com"]:
                    base_url = f"https://{RESPONSE_LLM_HOSTNAME}:{RESPONSE_LLM_PORT}{RESPONSE_LLM_API_PATH}"
                else:
                    base_url = None  # Use default OpenAI endpoint
            else:
                # For local providers like LM Studio or Ollama, use custom base URL with HTTP
                base_url = f"http://{RESPONSE_LLM_HOSTNAME}:{RESPONSE_LLM_PORT}{RESPONSE_LLM_API_PATH}"

            # Create the LLM with the determined base URL
            self.llm = ChatOpenAI(
                model=RESPONSE_LLM_MODEL,
                temperature=0.7,  # Slightly higher temperature for more natural responses
                api_key=OPENAI_API_KEY or ("sk-fake-key" if base_url else OPENAI_API_KEY),
                base_url=base_url
            )
        
        # Define the prompt template for generating natural language responses
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at converting database results into natural language responses."),
            ("human", "{generated_prompt}")
        ])
        
        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser
    
    def generate_natural_language_response(self, generated_prompt):
        """
        Generate a natural language response based on the generated prompt
        """
        # Log the request
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"ResponseGenerator request: {generated_prompt[:100]}...")  # Truncate for log readability

        response = self.chain.invoke({
            "generated_prompt": generated_prompt
        })

        # Log the response
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"ResponseGenerator response: {response[:200]}...")  # Truncate for log readability

        return response