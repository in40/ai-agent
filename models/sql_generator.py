from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import (
    SQL_LLM_PROVIDER, SQL_LLM_MODEL, SQL_LLM_HOSTNAME, SQL_LLM_PORT,
    SQL_LLM_API_PATH, OPENAI_API_KEY, GIGACHAT_CREDENTIALS, GIGACHAT_SCOPE,
    GIGACHAT_ACCESS_TOKEN, GIGACHAT_VERIFY_SSL_CERTS, ENABLE_SCREEN_LOGGING
)
from utils.prompt_manager import PromptManager
import json
import logging

logger = logging.getLogger(__name__)

class SQLGenerator:
    def __init__(self):
        # Log the configuration being used before creating the LLM
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"SQLGenerator configured with provider: {SQL_LLM_PROVIDER}, model: {SQL_LLM_MODEL}")

        # Initialize the prompt manager
        self.prompt_manager = PromptManager()

        # Create the LLM based on the provider
        if SQL_LLM_PROVIDER.lower() == 'gigachat':
            # Import GigaChat model when needed
            from utils.gigachat_integration import GigaChatModel
            self.llm = GigaChatModel(
                model=SQL_LLM_MODEL,
                temperature=0,  # Lower temperature for more consistent SQL generation
                credentials=GIGACHAT_CREDENTIALS,
                scope=GIGACHAT_SCOPE,
                access_token=GIGACHAT_ACCESS_TOKEN,
                verify_ssl_certs=GIGACHAT_VERIFY_SSL_CERTS
            )
        else:
            # Construct the base URL based on provider configuration for other providers
            if SQL_LLM_PROVIDER.lower() in ['openai', 'deepseek', 'qwen']:
                # For cloud providers, use HTTPS unless hostname is not the standard one
                if SQL_LLM_HOSTNAME not in ["api.openai.com", "api.deepseek.com", "dashscope.aliyuncs.com"]:
                    base_url = f"https://{SQL_LLM_HOSTNAME}:{SQL_LLM_PORT}{SQL_LLM_API_PATH}"
                else:
                    base_url = None  # Use default OpenAI endpoint
            else:
                # For local providers like LM Studio or Ollama, use custom base URL with HTTP
                base_url = f"http://{SQL_LLM_HOSTNAME}:{SQL_LLM_PORT}{SQL_LLM_API_PATH}"

            # Create the LLM with the determined base URL
            self.llm = ChatOpenAI(
                model=SQL_LLM_MODEL,
                temperature=0,  # Lower temperature for more consistent SQL generation
                api_key=OPENAI_API_KEY or ("sk-fake-key" if base_url else OPENAI_API_KEY),
                base_url=base_url
            )

        # Define the prompt template for SQL generation using external prompt
        system_prompt = self.prompt_manager.get_prompt("sql_generator")
        if system_prompt is None:
            # Fallback to default prompt if external prompt is not found
            system_prompt = """You are an expert SQL developer. Your task is to generate correct SQL queries based on natural language requests.

            Database schema:
            {schema_dump}

            Instructions:
            1. Generate only the SQL query without any additional text or explanation
            2. Use proper SQL syntax for PostgreSQL
            3. Make sure the query is safe and doesn't include any harmful commands
            4. Use appropriate JOINs if needed to connect related tables
            5. If the request is ambiguous, make reasonable assumptions based on the schema
            6. Always use table aliases for better readability
            7. Limit results if the query could return a large dataset unless specifically asked for all records
            8. Wrap the SQL query between <sql_to_use> and </sql_to_use> tags
            """

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{user_request}")
        ])

        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser
    
    def generate_sql(self, user_request, schema_dump):
        """
        Generate SQL query based on user request and database schema
        """
        # Format the schema dump as a string for the prompt
        schema_str = self.format_schema_dump(schema_dump)

        # Log the request
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"SQLGenerator request - User request: {user_request[:100]}...")  # Truncate for log readability
            logger.info(f"SQLGenerator request - Schema (first 200 chars): {schema_str[:200]}...")

        # Generate the SQL query
        response = self.chain.invoke({
            "user_request": user_request,
            "schema_dump": schema_str
        })

        # Log the response
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"SQLGenerator response: {response[:200]}...")  # Truncate for log readability

        # Clean up the response to extract just the SQL
        sql_query = self.clean_sql_response(response)

        return sql_query
    
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