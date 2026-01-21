"""
GigaChat integration for the AI Agent with OAuth token authentication support.
"""
from typing import Optional, List, Any, Dict, Union, Type
import logging
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable
from gigachat import GigaChat
from gigachat.models import Chat, Messages, Model
import json
import re

logger = logging.getLogger(__name__)


class GigaChatModel(BaseChatModel):
    """
    Custom GigaChat integration with OAuth token authentication support.
    """
    model: str = Field(default="GigaChat:latest")
    credentials: Optional[str] = Field(default=None)
    scope: Optional[str] = Field(default="GIGACHAT_API_PERS")
    access_token: Optional[str] = Field(default=None)
    user: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    cert_file: Optional[str] = Field(default=None)
    key_file: Optional[str] = Field(default=None)
    key_file_password: Optional[str] = Field(default=None)
    verify_ssl_certs: Optional[bool] = Field(default=True)
    timeout: Optional[float] = Field(default=30.0)
    temperature: Optional[float] = Field(default=0.7)
    
    # Internal client instance
    _client: Optional[GigaChat] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._client = self._create_client()

    def _create_client(self) -> GigaChat:
        """
        Create a GigaChat client with the configured authentication method.
        """
        # Determine which authentication method to use based on provided parameters
        auth_params = {}

        if self.access_token:
            # Use access token directly
            auth_params["access_token"] = self.access_token
        elif self.credentials:
            # Use credentials (likely for OAuth)
            auth_params["credentials"] = self.credentials
            if self.scope:
                auth_params["scope"] = self.scope
        elif self.user and self.password:
            # Use username and password
            auth_params["user"] = self.user
            auth_params["password"] = self.password
        elif self.cert_file and self.key_file:
            # Use TLS certificates
            auth_params["cert_file"] = self.cert_file
            auth_params["key_file"] = self.key_file
            if self.key_file_password:
                auth_params["key_file_password"] = self.key_file_password
        else:
            raise ValueError(
                "No valid authentication method provided. "
                "Please provide one of: access_token, credentials, user/password, or cert/key files."
            )

        # Create the client with authentication parameters
        # Note: GigaChat constructor doesn't accept temperature directly
        # We'll handle temperature in the chat request
        # Only pass authentication parameters to avoid validation issues
        client_params = auth_params.copy()
        # Convert verify_ssl_certs to a boolean if it's not already
        client_params["verify_ssl_certs"] = bool(self.verify_ssl_certs)

        client = GigaChat(**client_params)

        return client

    @property
    def _llm_type(self) -> str:
        """Return type of chat model."""
        return "gigachat"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Generate a response from GigaChat.
        """
        # Convert LangChain messages to GigaChat format
        gigachat_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                gigachat_messages.append(Messages(role="user", content=msg.content))
            elif isinstance(msg, AIMessage):
                gigachat_messages.append(Messages(role="assistant", content=msg.content))
            elif isinstance(msg, SystemMessage):
                gigachat_messages.append(Messages(role="system", content=msg.content))
            else:
                # For other message types, treat as human message
                gigachat_messages.append(Messages(role="user", content=str(msg.content)))

        # Create the chat request
        # Pass model and temperature in kwargs to override defaults if needed
        chat_kwargs = {
            "messages": gigachat_messages,
            "model": self.model,
            "temperature": self.temperature,
        }
        chat_kwargs.update(kwargs)

        chat_request = Chat(**chat_kwargs)

        # Make the API call
        response = self._client.chat(chat_request)

        # Convert the response to LangChain format
        content = response.choices[0].message.content
        generation = ChatGeneration(
            message=AIMessage(content=content),
            generation_info={
                "finish_reason": response.choices[0].finish_reason,
                "model": response.model,
            }
        )

        return ChatResult(generations=[generation])

    def with_structured_output(self, schema: Union[Dict, Type[BaseModel]], *, include_raw: bool = False, **kwargs: Any):
        """
        Add structured output support to the GigaChat model.
        """
        if isinstance(schema, type) and (issubclass(schema, BaseModel) or hasattr(schema, '__fields__')):
            return GigaChatStructuredOutput(
                gigachat_model=self,
                schema=schema,
                include_raw=include_raw
            )
        else:
            raise NotImplementedError("Only Pydantic BaseModel schemas are supported for structured output")

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ):
        """
        Async stream response from GigaChat.
        """
        # Convert LangChain messages to GigaChat format
        gigachat_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                gigachat_messages.append(Messages(role="user", content=msg.content))
            elif isinstance(msg, AIMessage):
                gigachat_messages.append(Messages(role="assistant", content=msg.content))
            elif isinstance(msg, SystemMessage):
                gigachat_messages.append(Messages(role="system", content=msg.content))
            else:
                # For other message types, treat as human message
                gigachat_messages.append(Messages(role="user", content=str(msg.content)))

        # Create the chat request
        chat_kwargs = {
            "messages": gigachat_messages,
            "model": self.model,
            "temperature": self.temperature,
            "stream": True,  # Enable streaming
        }
        chat_kwargs.update(kwargs)

        chat_request = Chat(**chat_kwargs)

        # Make the streaming API call
        async for chunk in self._client.astream(chat_request):
            content = chunk.choices[0].delta.content
            if content:
                yield ChatGenerationChunk(message=AIMessage(content=content))


class GigaChatStructuredOutput(Runnable):
    """
    Wrapper class to handle structured output for GigaChat model.
    """
    def __init__(self, gigachat_model: 'GigaChatModel', schema: Type[BaseModel], include_raw: bool = False):
        self.gigachat_model = gigachat_model
        self.schema = schema
        self.include_raw = include_raw

    def invoke(self, input: Union[str, Dict], config=None, **kwargs):
        """
        Invoke the GigaChat model with structured output.
        """
        from langchain_core.runnables.utils import Input, Output
        from langchain_core.callbacks.manager import CallbackManagerForChainRun
        from langchain_core.tracers.log_stream import RunLog, RunLogPatch
        import asyncio

        # Handle the input appropriately
        if isinstance(input, str):
            # Create a message from the string input
            messages = [HumanMessage(content=input)]
        elif isinstance(input, dict):
            # If input is a dict, it might be a prompt template input
            # In this case, we need to format it properly
            # For structured output, we'll just take the first value or use a default key
            if "input" in input:
                messages = [HumanMessage(content=input["input"])]
            elif "user_request" in input:
                messages = [HumanMessage(content=input["user_request"])]
            elif len(input) == 1:
                # If there's only one key-value pair, use the value
                value = next(iter(input.values()))
                messages = [HumanMessage(content=value)]
            else:
                # If multiple keys, convert the whole dict to string
                messages = [HumanMessage(content=str(input))]
        else:
            # Assume it's already in the right format
            messages = input

        # Ensure messages is a list of BaseMessage objects
        if isinstance(messages, BaseMessage):
            messages = [messages]
        elif not isinstance(messages, list) or not all(isinstance(m, BaseMessage) for m in messages):
            # If not a list of BaseMessages, try to convert
            messages = [HumanMessage(content=str(messages))]

        # Generate the response using the underlying model
        # The generate method expects a list of message lists
        result = self.gigachat_model.generate([messages], config=config, **kwargs)
        # The result.generations[0] might be a list of generations or a single generation
        # depending on how the model implements the generate method
        first_generation = result.generations[0]
        if isinstance(first_generation, list):
            # If it's a list, take the first element
            content = first_generation[0].message.content
        else:
            # If it's a single ChatGeneration object, get its message content
            content = first_generation.message.content

        # Try to parse the response as JSON
        try:
            # First, try to extract JSON from code blocks
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # If no code block, try to extract JSON directly
                json_match = re.search(r'({.*?})', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # If no JSON found, try to parse the entire content
                    json_str = content

            parsed_data = json.loads(json_str)
            structured_output = self.schema(**parsed_data)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.warning(f"Failed to parse structured output: {e}. Content: {content}")
            # If parsing fails, try to create a basic response
            # This is a fallback that attempts to match field names in the content
            structured_output = self._fallback_parsing(content)

        if self.include_raw:
            return {"parsed": structured_output, "raw": content}
        else:
            return structured_output

    async def ainvoke(self, input_data: Union[str, Dict], config=None, **kwargs):
        """
        Async invoke the GigaChat model with structured output.
        """
        # If input_data is a string, convert it to a HumanMessage
        if isinstance(input_data, str):
            messages = [HumanMessage(content=input_data)]
        else:
            # Assume it's already in the right format
            messages = input_data

        # Generate the response asynchronously
        result = await self.gigachat_model.agenerate(messages, **kwargs)
        content = result.generations[0].text

        # Try to parse the response as JSON
        try:
            # First, try to extract JSON from code blocks
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # If no code block, try to extract JSON directly
                json_match = re.search(r'({.*?})', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # If no JSON found, try to parse the entire content
                    json_str = content

            parsed_data = json.loads(json_str)
            structured_output = self.schema(**parsed_data)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.warning(f"Failed to parse structured output: {e}. Content: {content}")
            # If parsing fails, try to create a basic response
            # This is a fallback that attempts to match field names in the content
            structured_output = self._fallback_parsing(content)

        if self.include_raw:
            return {"parsed": structured_output, "raw": content}
        else:
            return structured_output

    def stream(self, input_data: Union[str, Dict], config=None, **kwargs):
        """
        Stream the GigaChat model with structured output.
        """
        # Structured output doesn't typically support streaming, so we'll just return the full result
        yield self.invoke(input_data, config, **kwargs)

    async def astream(self, input_data: Union[str, Dict], config=None, **kwargs):
        """
        Async stream the GigaChat model with structured output.
        """
        # Structured output doesn't typically support streaming, so we'll just return the full result
        yield await self.ainvoke(input_data, config, **kwargs)

    def _fallback_parsing(self, content: str):
        """
        Fallback method to parse content when JSON parsing fails.
        """
        # Create a dictionary with default values for all fields in the schema
        field_values = {}
        for field_name, field_info in self.schema.__fields__.items():
            # Try to find the field value in the content
            # This is a simple approach - in practice, you might want more sophisticated parsing
            field_values[field_name] = f"Could not extract {field_name} from response"

        try:
            return self.schema(**field_values)
        except Exception:
            # If even the fallback fails, return an instance with default values
            return self.schema.construct()