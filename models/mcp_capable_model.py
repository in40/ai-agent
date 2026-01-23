"""
MCP-Capable Model for AI Agent.

This model understands MCP server capabilities and can generate appropriate tool calls
when needed based on the user request and available MCP services.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from config.settings import (
    PROMPT_LLM_PROVIDER,
    PROMPT_LLM_MODEL,
    PROMPT_LLM_HOSTNAME,
    PROMPT_LLM_PORT,
    PROMPT_LLM_API_PATH,
    MCP_LLM_PROVIDER,
    MCP_LLM_MODEL,
    MCP_LLM_HOSTNAME,
    MCP_LLM_PORT,
    MCP_LLM_API_PATH,
    OPENAI_API_KEY,
    DEEPSEEK_API_KEY,
    GIGACHAT_CREDENTIALS,
    GIGACHAT_SCOPE,
    GIGACHAT_ACCESS_TOKEN,
    GIGACHAT_VERIFY_SSL_CERTS,
    ENABLE_SCREEN_LOGGING,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_HOSTNAME,
    DEFAULT_LLM_PORT,
    DEFAULT_LLM_API_PATH
)
from utils.prompt_manager import PromptManager
from utils.ssh_keep_alive import SSHKeepAliveContext
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class MCPCapableModel:
    """
    MCP-Capable Model that can understand MCP server capabilities and generate appropriate tool calls.
    """
    
    def __init__(self):
        # Log the configuration being used before creating the LLM
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"MCPCapableModel configured with provider: {PROMPT_LLM_PROVIDER}, model: {PROMPT_LLM_MODEL}")

        # Initialize the prompt manager with the correct prompts directory
        self.prompt_manager = PromptManager("./core/prompts")

        # Create the LLM based on the provider
        # Use MCP-specific configuration if available, otherwise fall back to prompt configuration
        # If MCP_LLM_PROVIDER is empty or set to "default", use the default configuration
        if MCP_LLM_PROVIDER.lower() in ['', 'default']:
            provider = DEFAULT_LLM_PROVIDER
            model = DEFAULT_LLM_MODEL
            hostname = DEFAULT_LLM_HOSTNAME
            port = DEFAULT_LLM_PORT
            api_path = DEFAULT_LLM_API_PATH
        elif MCP_LLM_PROVIDER and MCP_LLM_PROVIDER.strip():
            provider = MCP_LLM_PROVIDER
            model = MCP_LLM_MODEL
            hostname = MCP_LLM_HOSTNAME
            port = MCP_LLM_PORT
            api_path = MCP_LLM_API_PATH
        else:
            # Fall back to prompt configuration if MCP config is not available
            provider = PROMPT_LLM_PROVIDER
            model = PROMPT_LLM_MODEL
            hostname = PROMPT_LLM_HOSTNAME
            port = PROMPT_LLM_PORT
            api_path = PROMPT_LLM_API_PATH

        if provider.lower() == 'gigachat':
            # Import GigaChat model when needed
            from utils.gigachat_integration import GigaChatModel
            self.llm = GigaChatModel(
                model=model,
                temperature=0.1,
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

            # Create ChatOpenAI instance with appropriate configuration
            if provider.lower() == 'openai':
                self.llm = ChatOpenAI(
                    model=model,
                    temperature=0.1,
                    openai_api_key=OPENAI_API_KEY,
                    base_url=base_url
                )
            elif provider.lower() == 'deepseek':
                self.llm = ChatOpenAI(
                    model=model,
                    temperature=0.1,
                    openai_api_key=DEEPSEEK_API_KEY,
                    base_url=base_url
                )
            else:
                # Default to generic ChatOpenAI for other providers
                self.llm = ChatOpenAI(
                    model=model,
                    temperature=0.1,
                    base_url=base_url
                )

        # Define the system prompt template for the MCP-capable model using external prompt
        system_prompt = self.prompt_manager.get_prompt("mcp_capable_model")
        if system_prompt is None:
            # If the external prompt is not found, raise an error to ensure prompts are maintained properly
            raise FileNotFoundError("mcp_capable_model.txt not found in prompts directory. Please ensure the prompt file exists.")

        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input_text}")
        ])

        # Create the output parser
        self.output_parser = StrOutputParser()

        # Create the chain
        self.chain = self.prompt | self.llm | self.output_parser

    def generate_mcp_tool_calls(self, user_request: str, mcp_services: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate MCP tool calls based on user request and available services.

        Args:
            user_request: The user's natural language request
            mcp_services: List of available MCP services

        Returns:
            Dictionary containing tool calls to execute
        """
        logger.info(f"Generating MCP tool calls for request: {user_request}")

        # Format MCP services as JSON for the prompt
        mcp_services_json = json.dumps(mcp_services, indent=2)

        try:
            # Use SSH keep-alive during the LLM call
            with SSHKeepAliveContext():
                # Generate the response using the chain
                response = self.chain.invoke({
                    "input_text": user_request,
                    "mcp_services_json": mcp_services_json
                })

            # Try to parse the response as JSON
            try:
                result = json.loads(response)
                logger.info(f"MCP tool calls generated: {result}")
                return result
            except json.JSONDecodeError:
                logger.warning(f"LLM response is not valid JSON: {response}")
                # If response is not valid JSON, return empty tool calls
                return {"tool_calls": []}

        except Exception as e:
            logger.error(f"Error generating MCP tool calls: {str(e)}")
            # Return empty tool calls in case of error
            return {"tool_calls": []}

    def execute_mcp_tool_calls(self, tool_calls: List[Dict[str, Any]], mcp_services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute the MCP tool calls and return the results.

        Args:
            tool_calls: List of tool calls to execute
            mcp_services: List of available MCP services

        Returns:
            List of results from executed tool calls
        """
        logger.info(f"Executing {len(tool_calls)} MCP tool calls")
        results = []

        # Create a service lookup dictionary for easy access
        service_lookup = {service['id']: service for service in mcp_services}

        for call in tool_calls:
            service_id = call.get('service_id')
            action = call.get('action')
            parameters = call.get('parameters', {})

            # Find the service
            if service_id not in service_lookup:
                logger.warning(f"Service {service_id} not found in available services")
                results.append({
                    "service_id": service_id,
                    "status": "error",
                    "error": f"Service {service_id} not found"
                })
                continue

            service = service_lookup[service_id]

            # Execute the tool call - this is a simplified implementation
            # In a real implementation, you would need to make actual calls to the MCP services
            try:
                # Simulate calling the MCP service
                result = self._call_mcp_service(service, action, parameters)
                results.append(result)
            except Exception as e:
                logger.error(f"Error calling MCP service {service_id}: {str(e)}")
                results.append({
                    "service_id": service_id,
                    "status": "error",
                    "error": str(e)
                })

        logger.info(f"MCP tool calls execution completed. Results: {results}")
        return results

    def return_response_to_llm(self, response_data: Any) -> str:
        """
        Return the response directly to the LLM model.

        Args:
            response_data: The response data to return to the LLM

        Returns:
            Formatted response string that can be processed by the LLM
        """
        import json

        # Format the response data for the LLM
        if isinstance(response_data, dict):
            return json.dumps(response_data, indent=2)
        elif isinstance(response_data, list):
            return json.dumps(response_data, indent=2)
        else:
            return str(response_data)

    def _call_mcp_service(self, service: Dict[str, Any], action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actually call an MCP service.
        Determines the protocol to use (HTTP, TCP socket, etc.) based on service metadata
        and makes the appropriate network call.
        """
        import socket
        import json
        import requests
        from datetime import datetime

        logger.info(f"Calling MCP service {service['id']} with action '{action}' and parameters {parameters}")

        # Determine the protocol to use based on service metadata or default to HTTP
        service_protocol = service.get('metadata', {}).get('protocol', 'http')
        service_host = service['host']
        service_port = service['port']

        try:
            if service_protocol.lower() == 'http':
                # Use HTTP protocol to call the service
                base_url = f"http://{service_host}:{service_port}"

                # Determine the endpoint based on the action
                # This is a convention - you might need to adjust based on your actual service implementation
                if action:
                    endpoint = f"{base_url}/{action.lstrip('/')}"  # Ensure action doesn't start with extra slash
                else:
                    # If no action is specified, use the base URL directly
                    endpoint = base_url

                # Prepare the request payload
                payload = {
                    "action": action,
                    "parameters": parameters,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

                # Make the HTTP request
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=30  # 30-second timeout
                )

                if response.status_code == 200:
                    # Parse the response
                    result_data = response.json()
                    return {
                        "service_id": service['id'],
                        "action": action,
                        "parameters": parameters,
                        "status": "success",
                        "result": result_data,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                else:
                    return {
                        "service_id": service['id'],
                        "action": action,
                        "parameters": parameters,
                        "status": "error",
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }

            elif service_protocol.lower() == 'tcp':
                # Use TCP socket to call the service
                # Create a socket and connect to the service
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(30)  # 30-second timeout
                    sock.connect((service_host, service_port))

                    # Prepare the request payload
                    request_payload = {
                        "service_id": service['id'],
                        "action": action,
                        "parameters": parameters,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }

                    # Send the request as JSON
                    request_json = json.dumps(request_payload)
                    sock.sendall(request_json.encode('utf-8'))

                    # Receive the response
                    response_data = sock.recv(4096)
                    response_json = response_data.decode('utf-8')

                    # Parse the response
                    result_data = json.loads(response_json)

                    return {
                        "service_id": service['id'],
                        "action": action,
                        "parameters": parameters,
                        "status": "success",
                        "result": result_data,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
            else:
                # Default to HTTP if protocol is not specified or recognized
                logger.warning(f"Unknown protocol '{service_protocol}' for service {service['id']}, defaulting to HTTP")
                base_url = f"http://{service_host}:{service_port}"

                # Determine the endpoint based on the action
                if action:
                    endpoint = f"{base_url}/{action.lstrip('/')}"  # Ensure action doesn't start with extra slash
                else:
                    # If no action is specified, use the base URL directly
                    endpoint = base_url

                # Prepare the request payload
                payload = {
                    "action": action,
                    "parameters": parameters,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

                # Make the HTTP request
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )

                if response.status_code == 200:
                    # Parse the response
                    result_data = response.json()
                    return {
                        "service_id": service['id'],
                        "action": action,
                        "parameters": parameters,
                        "status": "success",
                        "result": result_data,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                else:
                    return {
                        "service_id": service['id'],
                        "action": action,
                        "parameters": parameters,
                        "status": "error",
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
        except requests.exceptions.Timeout:
            return {
                "service_id": service['id'],
                "action": action,
                "parameters": parameters,
                "status": "error",
                "error": "Request timed out",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except requests.exceptions.RequestException as e:
            return {
                "service_id": service['id'],
                "action": action,
                "parameters": parameters,
                "status": "error",
                "error": f"HTTP request failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except socket.timeout:
            return {
                "service_id": service['id'],
                "action": action,
                "parameters": parameters,
                "status": "error",
                "error": "TCP request timed out",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except socket.error as e:
            return {
                "service_id": service['id'],
                "action": action,
                "parameters": parameters,
                "status": "error",
                "error": f"TCP connection failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except json.JSONDecodeError as e:
            return {
                "service_id": service['id'],
                "action": action,
                "parameters": parameters,
                "status": "error",
                "error": f"Invalid JSON response: {str(e)}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            return {
                "service_id": service['id'],
                "action": action,
                "parameters": parameters,
                "status": "error",
                "error": f"Unexpected error calling MCP service: {str(e)}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

    def _get_llm_instance(self, provider=None, model=None):
        """
        Returns the LLM instance for use by other components
        If provider or model are specified, creates a new instance with those parameters
        """
        if provider is not None or model is not None:
            # Use the specified provider/model or fall back to defaults
            use_provider = provider or getattr(self, "_default_provider", MCP_LLM_PROVIDER)
            use_model = model or getattr(self, "_default_model", MCP_LLM_MODEL)

            # Determine if we should use the default model configuration
            use_default = use_provider.lower() in ["", "default"]

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
                actual_hostname = getattr(self, "_default_hostname", MCP_LLM_HOSTNAME)
                actual_port = getattr(self, "_default_port", MCP_LLM_PORT)
                actual_api_path = getattr(self, "_default_api_path", MCP_LLM_API_PATH)

            # Create the LLM based on the provider
            if actual_provider.lower() == "gigachat":
                from utils.gigachat_integration import GigaChatModel
                return GigaChatModel(
                    model=actual_model,
                    temperature=0.1,
                    credentials=GIGACHAT_CREDENTIALS,
                    scope=GIGACHAT_SCOPE,
                    access_token=GIGACHAT_ACCESS_TOKEN,
                    verify_ssl_certs=GIGACHAT_VERIFY_SSL_CERTS
                )
            else:
                # Construct the base URL based on provider configuration for other providers
                if actual_provider.lower() in ["openai", "deepseek", "qwen"]:
                    # For cloud providers, use HTTPS with the specified hostname
                    if actual_provider.lower() == "openai" and actual_hostname == "api.openai.com":
                        base_url = None  # Use default OpenAI endpoint
                    else:
                        base_url = f"https://{actual_hostname}:{actual_port}{actual_api_path}"
                else:
                    # For local providers like LM Studio or Ollama, use custom base URL with HTTP
                    base_url = f"http://{actual_hostname}:{actual_port}{actual_api_path}"

                # Select the appropriate API key based on the provider
                if actual_provider.lower() == "deepseek":
                    api_key = DEEPSEEK_API_KEY or ("sk-fake-key" if base_url else DEEPSEEK_API_KEY)
                else:
                    api_key = OPENAI_API_KEY or ("sk-fake-key" if base_url else OPENAI_API_KEY)

                # Create the LLM with the determined base URL
                return ChatOpenAI(
                    model=actual_model,
                    temperature=0.1,
                    api_key=api_key,
                    base_url=base_url
                )
        else:
            # Return the default LLM instance
            return self.llm