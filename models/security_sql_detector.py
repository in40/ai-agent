"""
Security SQL Detector module for analyzing SQL queries for potential security vulnerabilities
using an LLM-based approach to reduce false positives compared to simple keyword matching.
"""

from typing import Dict, Any, Tuple
import logging
import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config.settings import (
    SECURITY_LLM_PROVIDER,
    SECURITY_LLM_MODEL,
    SECURITY_LLM_HOSTNAME,
    SECURITY_LLM_PORT,
    SECURITY_LLM_API_PATH,
    OPENAI_API_KEY,
    DEEPSEEK_API_KEY,
    ENABLE_SCREEN_LOGGING,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_HOSTNAME,
    DEFAULT_LLM_PORT,
    DEFAULT_LLM_API_PATH
)
from utils.ssh_keep_alive import SSHKeepAliveContext

logger = logging.getLogger(__name__)


class SecuritySQLDetector:
    """
    A class that uses an LLM to analyze SQL queries for potential security vulnerabilities.
    This helps reduce false positives compared to simple keyword matching.
    """
    
    def __init__(self):
        """
        Initialize the SecuritySQLDetector with an LLM client
        """
        # Determine if we should use the default model configuration
        # If SECURITY_LLM_PROVIDER is empty or set to "default", use the default configuration
        use_default = SECURITY_LLM_PROVIDER.lower() in ['', 'default']

        # Set the actual configuration values based on whether to use defaults
        if use_default:
            provider = DEFAULT_LLM_PROVIDER
            model = DEFAULT_LLM_MODEL
            hostname = DEFAULT_LLM_HOSTNAME
            port = DEFAULT_LLM_PORT
            api_path = DEFAULT_LLM_API_PATH
        else:
            provider = SECURITY_LLM_PROVIDER
            model = SECURITY_LLM_MODEL
            hostname = SECURITY_LLM_HOSTNAME
            port = SECURITY_LLM_PORT
            api_path = SECURITY_LLM_API_PATH

        try:
            # Determine the LLM provider and configure accordingly
            if provider.lower() == "openai":
                self.llm = ChatOpenAI(
                    model=model,
                    temperature=0.1,  # Low temperature for more consistent security analysis
                    api_key=OPENAI_API_KEY
                )
            elif provider.lower() == "deepseek":
                # For DeepSeek, use ChatOpenAI with DeepSeek configuration
                # Construct the base URL for DeepSeek
                base_url = f"https://{hostname}:{port}{api_path}"

                self.llm = ChatOpenAI(
                    model=model,
                    temperature=0.1,
                    api_key=DEEPSEEK_API_KEY,
                    base_url=base_url
                )
            elif provider.lower() == "gigachat":
                # For GigaChat, use the GigaChat integration
                from langchain_gigachat.chat_models import GigaChat

                # Use credentials if provided, otherwise use access token
                if os.getenv("GIGACHAT_CREDENTIALS"):
                    self.llm = GigaChat(
                        credentials=os.getenv("GIGACHAT_CREDENTIALS"),
                        scope=os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
                        model=model,
                        temperature=0.1,
                        verify_ssl=os.getenv("GIGACHAT_VERIFY_SSL_CERTS", "true").lower() == "true"
                    )
                elif os.getenv("GIGACHAT_ACCESS_TOKEN"):
                    self.llm = GigaChat(
                        access_token=os.getenv("GIGACHAT_ACCESS_TOKEN"),
                        model=model,
                        temperature=0.1,
                        verify_ssl=os.getenv("GIGACHAT_VERIFY_SSL_CERTS", "true").lower() == "true"
                    )
                else:
                    raise ValueError("Either GIGACHAT_CREDENTIALS or GIGACHAT_ACCESS_TOKEN must be set for GigaChat provider")
            elif provider.lower() == "lm studio":
                # For LM Studio, use ChatOpenAI with local configuration
                # langchain_openai.ChatOpenAI is already imported at the top of the file

                # Construct the base URL for LM Studio
                base_url = f"http://{hostname}:{port}{api_path}"

                self.llm = ChatOpenAI(
                    model=model,
                    temperature=0.1,
                    base_url=base_url,
                    api_key="not-needed"  # LM Studio doesn't require a real API key
                )
            else:
                # For other providers (like Ollama), use the Ollama approach
                from langchain_ollama import ChatOllama

                # Construct the base URL for non-OpenAI providers
                base_url = f"http://{hostname}:{port}{api_path}"

                self.llm = ChatOllama(
                    model=model,
                    base_url=base_url,
                    temperature=0.1
                )
        except ImportError as e:
            logger.error(f"Import error in SecuritySQLDetector: {str(e)}")
            # Fallback to a basic configuration if imports fail
            raise
        except Exception as e:
            logger.error(f"Error initializing SecuritySQLDetector: {str(e)}")
            # Re-raise the exception to be handled by the calling function
            raise
        
        # Create the output parser - using string parser instead of JSON parser
        self.output_parser = StrOutputParser()

        # Load the security analysis prompt from the external file
        from utils.prompt_manager import PromptManager
        pm = PromptManager("./core/prompts")
        self.prompt_name = "security_sql_analysis"
        security_prompt_template = pm.get_prompt(self.prompt_name)

        if security_prompt_template is None:
            # Fallback to default prompt if external file is not found
            logger.warning("Security prompt file not found, using default prompt")
            self.prompt_name = "default_security_prompt"
            security_prompt_template = (
                "You are a security expert specializing in SQL injection and database vulnerability assessment. "
                "Analyze the provided SQL query for potential security vulnerabilities. "
                "Focus on identifying actual threats rather than false positives. "
                "Consider the context that this query is generated from natural language input. "
                "Be careful to distinguish between legitimate column/table names that might contain keywords "
                "like 'create', 'drop', 'select', etc. and actual malicious commands.\n\n"
                "Analyze the following SQL query for security vulnerabilities:\n\n"
                "SQL Query: {sql_query}\n\n"
                "Schema Context: {schema_context}\n\n"
                "Respond with a JSON object containing the following fields:\n"
                "- is_safe: boolean indicating if the query is safe\n"
                "- security_issues: array of strings listing any security issues found\n"
                "- confidence_level: string (\"high\", \"medium\", or \"low\") indicating confidence in the analysis\n"
                "- explanation: string explaining the analysis\n\n"
                "Example response format:\n"
                "{{\n"
                "  \"is_safe\": true,\n"
                "  \"security_issues\": [],\n"
                "  \"confidence_level\": \"high\",\n"
                "  \"explanation\": \"Query is safe as it only performs a simple SELECT operation\"\n"
                "}}\n\n"
                "IMPORTANT: Respond ONLY with the JSON object, nothing else."
            )

        # Create a prompt template for security analysis
        self.security_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", security_prompt_template),
            ("human", "SQL Query: {sql_query}\n\nSchema Context: {schema_context}")
        ])

        # Create the chain
        self.chain = self.security_analysis_prompt | self.llm | self.output_parser

    def analyze_query(self, sql_query: str, schema_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a SQL query for security vulnerabilities using the LLM
        
        Args:
            sql_query (str): The SQL query to analyze
            schema_context (Dict[str, Any]): Optional schema context to help with analysis
            
        Returns:
            Dict[str, Any]: Analysis results with security assessment
        """
        logger.info(f"Analyzing SQL query for security: {sql_query[:100]}...")
        
        # Prepare schema context for the LLM
        schema_str = ""
        if schema_context:
            schema_str = str(schema_context)
        else:
            schema_str = "No schema context provided"
        
        try:
            # Log the full request to LLM, including all roles and prompts
            if ENABLE_SCREEN_LOGGING:
                # Get the full prompt with all messages (system and human) without invoking the LLM
                full_prompt = self.security_analysis_prompt.format_messages(
                    sql_query=sql_query,
                    schema_context=schema_str
                )
                logger.info(f"SecuritySQLDetector full LLM request using prompt file: {self.prompt_name}")
                for i, message in enumerate(full_prompt):
                    if message.type == "system":
                        logger.info(f"  System Message {i+1}: {message.content}")  # Full content without truncation
                    else:
                        logger.info(f"  Message {i+1} ({message.type}): {message.content}")

            # Use SSH keep-alive during the LLM call
            with SSHKeepAliveContext():
                # Run the chain to analyze the query
                raw_result = self.chain.invoke({
                    "sql_query": sql_query,
                    "schema_context": schema_str
                })

            # Extract JSON from the raw result string
            # Look for JSON between curly braces
            import re
            # Use a stack-based approach to find properly balanced JSON
            def find_json_object(text):
                stack = []
                start = -1

                for i, char in enumerate(text):
                    if char == '{':
                        if len(stack) == 0:
                            start = i
                        stack.append(char)
                    elif char == '}':
                        if stack:
                            stack.pop()
                            if len(stack) == 0 and start != -1:
                                return text[start:i+1]
                return None

            json_str = find_json_object(raw_result)
            if not json_str:
                # If the stack-based approach doesn't work, try a simpler pattern
                json_match = re.search(r'\{.*?\}(?!\s*[,}])', raw_result, re.DOTALL)
                if json_match:
                    json_str = json_match.group()

            if json_str:
                try:
                    result_dict = json.loads(json_str)

                    # Validate required fields exist
                    required_fields = ["is_safe", "security_issues", "confidence_level", "explanation"]
                    for field in required_fields:
                        if field not in result_dict:
                            logger.error(f"Security analysis missing required field: {field}")
                            return {
                                "is_safe": False,
                                "security_issues": [f"Missing field: {field}"],
                                "confidence_level": "low",
                                "explanation": f"Security analysis missing required field: {field}"
                            }

                    logger.info(f"Security analysis completed. Safe: {result_dict.get('is_safe', 'unknown')}")
                    return result_dict
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse JSON from LLM response: {str(je)}")
                    logger.debug(f"Raw LLM response: {raw_result}")
                    logger.debug(f"Extracted potential JSON: {json_str}")
            else:
                logger.error(f"Could not find JSON in LLM response: {raw_result}")

                # Try to extract information even if it's not in JSON format
                # Look for key terms that might indicate the LLM's assessment
                raw_lower = raw_result.lower()
                is_safe = "not safe" not in raw_lower and "unsafe" not in raw_lower and "vulnerability" not in raw_lower and "issue" not in raw_lower
                confidence = "low"

                if "high" in raw_lower and "confidence" in raw_lower:
                    confidence = "high"
                elif "medium" in raw_lower and "confidence" in raw_lower:
                    confidence = "medium"

                return {
                    "is_safe": is_safe,
                    "security_issues": [f"Could not parse security analysis from LLM response. Raw response: {raw_result[:200]}..."],
                    "confidence_level": confidence,
                    "explanation": "Security analysis failed due to parsing error, but attempting to extract meaning from raw response"
                }

            # If we couldn't parse the JSON properly, return a conservative result
            return {
                "is_safe": False,
                "security_issues": ["Could not parse security analysis from LLM response"],
                "confidence_level": "low",
                "explanation": "Security analysis failed due to parsing error"
            }
        except Exception as e:
            logger.error(f"Error during security analysis: {str(e)}")
            # In case of error, return a conservative result
            return {
                "is_safe": False,
                "security_issues": ["Analysis error occurred"],
                "confidence_level": "low",
                "explanation": f"Security analysis failed due to error: {str(e)}"
            }

    def is_query_safe(self, sql_query: str, schema_context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Determine if a SQL query is safe to execute based on LLM analysis
        
        Args:
            sql_query (str): The SQL query to check
            schema_context (Dict[str, Any]): Optional schema context to help with analysis
            
        Returns:
            Tuple[bool, str]: (is_safe, reason_for_safety_or_risk)
        """
        analysis = self.analyze_query(sql_query, schema_context)
        
        is_safe = analysis.get("is_safe", False)
        confidence = analysis.get("confidence_level", "low")
        issues = analysis.get("security_issues", [])
        explanation = analysis.get("explanation", "No explanation provided")
        
        if not is_safe:
            reason = f"Security issues detected: {', '.join(issues)}. {explanation}. Confidence: {confidence}"
        else:
            reason = f"No security issues detected. {explanation}. Confidence: {confidence}"
        
        return is_safe, reason