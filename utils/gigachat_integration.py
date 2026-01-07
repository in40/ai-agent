"""
GigaChat integration for the AI Agent with OAuth token authentication support.
"""
from typing import Optional, List, Any, Dict
import logging
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from pydantic import BaseModel, Field
from gigachat import GigaChat
from gigachat.models import Chat, Messages, Model
import json

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
        client_params["verify_ssl_certs"] = self.verify_ssl_certs

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