"""
LLM Request Logger - A wrapper to log all LLM requests and responses
"""
import logging
import time
from datetime import datetime
from langchain_core.language_models import BaseLanguageModel
from langchain_core.callbacks import CallbackManagerForLLMRun
from typing import Any, Dict, List, Mapping, Optional
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.messages import BaseMessage


class LLMRequestLogger:
    """
    A wrapper class that logs all LLM requests and responses
    """
    def __init__(self, llm: BaseLanguageModel, logger_name: str = "llm_logger"):
        self.llm = llm
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        # Create file handler to log to a file
        if not self.logger.handlers:
            file_handler = logging.FileHandler('/var/log/ai_agent/llm_requests.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
    def generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> ChatResult:
        """
        Wrapper for the LLM's generate method that logs requests and responses
        """
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"LLM REQUEST at {datetime.now().isoformat()}")
        self.logger.info(f"Messages: {self._format_messages(messages)}")
        self.logger.info(f"Stop tokens: {stop}")
        self.logger.info(f"Additional kwargs: {kwargs}")
        
        try:
            # Call the actual LLM
            result = self.llm.generate(messages, stop=stop, run_manager=run_manager, **kwargs)
            
            # Log the response
            end_time = time.time()
            duration = end_time - start_time
            
            self.logger.info(f"LLM RESPONSE after {duration:.2f}s")
            self.logger.info(f"Response: {self._format_response(result)}")
            
            return result
        except Exception as e:
            # Log the error
            end_time = time.time()
            duration = end_time - start_time
            
            self.logger.error(f"LLM ERROR after {duration:.2f}s: {str(e)}")
            raise
    
    def _format_messages(self, messages: List[BaseMessage]) -> str:
        """
        Format messages for logging
        """
        formatted = []
        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__
            content = str(msg.content)[:200] + "..." if len(str(msg.content)) > 200 else str(msg.content)  # Truncate long content
            formatted.append(f"[{i}] {msg_type}: {content}")
        return " | ".join(formatted)
    
    def _format_response(self, result: ChatResult) -> str:
        """
        Format the LLM response for logging
        """
        if result.generations:
            gen = result.generations[0][0]  # First generation of first message
            response_text = gen.text[:200] + "..." if len(gen.text) > 200 else gen.text  # Truncate long responses
            return f"{type(gen).__name__}: {response_text}"
        return "No generations in response"
    
    def __getattr__(self, name):
        """
        Delegate other attributes/methods to the wrapped LLM
        """
        return getattr(self.llm, name)


def log_llm_request_details(provider: str, model: str, prompt: str, response: str = None, error: str = None):
    """
    Log detailed information about an LLM request
    """
    logger = logging.getLogger("llm_logger")
    
    logger.info("="*80)
    logger.info(f"LLM REQUEST DETAILS")
    logger.info(f"Provider: {provider}")
    logger.info(f"Model: {model}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("-"*40)
    logger.info(f"PROMPT SENT TO LLM:")
    logger.info(prompt)
    if response:
        logger.info("-"*40)
        logger.info(f"LLM RESPONSE:")
        logger.info(response)
    if error:
        logger.info("-"*40)
        logger.error(f"LLM ERROR:")
        logger.error(error)
    logger.info("="*80)