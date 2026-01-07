from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import (
    PROMPT_LLM_PROVIDER, PROMPT_LLM_MODEL, PROMPT_LLM_HOSTNAME,
    PROMPT_LLM_PORT, PROMPT_LLM_API_PATH, OPENAI_API_KEY,
    GIGACHAT_CREDENTIALS, GIGACHAT_SCOPE, GIGACHAT_ACCESS_TOKEN, ENABLE_SCREEN_LOGGING
)
import json
import logging

logger = logging.getLogger(__name__)

class PromptGenerator:
    def __init__(self):
        # Log the configuration being used before creating the LLM
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"PromptGenerator configured with provider: {PROMPT_LLM_PROVIDER}, model: {PROMPT_LLM_MODEL}")

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
        
        # Define the prompt template for generating a prompt for the response LLM
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating detailed prompts for language models. 
            Your task is to create a comprehensive prompt that will help another LLM generate 
            a detailed natural language response based on database query results and the original user request.
            
            Guidelines:
            1. The prompt should include the original user request
            2. The prompt should include the database query results
            3. The prompt should guide the response LLM on how to format and structure the answer
            4. The prompt should specify the tone and level of detail required
            5. The prompt should ensure the response is in natural language and easy to understand
            """),
            ("human", """Original user request: {user_request}
            
            Database query results: {db_results}

            Create a detailed prompt for another LLM to generate a natural language response based on these results.""")
        ])
        
        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser
    
    def generate_prompt_for_response_llm(self, user_request, db_results):
        """
        Generate a detailed prompt for the response LLM based on user request and database results
        """
        # Format the database results as a string
        results_str = self.format_db_results(db_results)

        # Log the request
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"PromptGenerator request - User request: {user_request[:100]}...")  # Truncate for log readability
            logger.info(f"PromptGenerator request - DB results (first 200 chars): {results_str[:200]}...")

        # Generate the prompt for the response LLM
        response = self.chain.invoke({
            "user_request": user_request,
            "db_results": results_str
        })

        # Log the response
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"PromptGenerator response: {response[:200]}...")  # Truncate for log readability

        return response
    
    def format_db_results(self, db_results):
        """
        Format database results into a readable string
        """
        if not db_results:
            return "No results found."
        
        # Convert the results to JSON string for readability
        return json.dumps(db_results, indent=2, default=str)