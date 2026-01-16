"""
Dedicated MCP Model for AI Agent.

This model is specifically configured and optimized for handling MCP-related queries.
It extends the functionality of the MCPCapableModel but uses dedicated configuration
settings for MCP-specific tasks.
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
    DEDICATED_MCP_LLM_PROVIDER,
    DEDICATED_MCP_LLM_MODEL,
    DEDICATED_MCP_LLM_HOSTNAME,
    DEDICATED_MCP_LLM_PORT,
    DEDICATED_MCP_LLM_API_PATH,
    OPENAI_API_KEY,
    DEEPSEEK_API_KEY,
    GIGACHAT_CREDENTIALS,
    GIGACHAT_SCOPE,
    GIGACHAT_ACCESS_TOKEN,
    GIGACHAT_VERIFY_SSL_CERTS,
    ENABLE_SCREEN_LOGGING
)
from utils.prompt_manager import PromptManager
from utils.ssh_keep_alive import SSHKeepAliveContext
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class DedicatedMCPModel:
    """
    Dedicated MCP Model that is specifically configured for handling MCP-related queries.
    This model uses dedicated configuration settings for optimal MCP service interaction.
    """

    def __init__(self):
        # Store configuration values as instance attributes to preserve them
        self.dedicated_mcp_llm_provider = DEDICATED_MCP_LLM_PROVIDER if DEDICATED_MCP_LLM_PROVIDER and DEDICATED_MCP_LLM_PROVIDER.strip() else None
        self.dedicated_mcp_llm_model = DEDICATED_MCP_LLM_MODEL if DEDICATED_MCP_LLM_MODEL and DEDICATED_MCP_LLM_MODEL.strip() else None
        self.dedicated_mcp_llm_hostname = DEDICATED_MCP_LLM_HOSTNAME if DEDICATED_MCP_LLM_HOSTNAME and DEDICATED_MCP_LLM_HOSTNAME.strip() else None
        self.dedicated_mcp_llm_port = DEDICATED_MCP_LLM_PORT if DEDICATED_MCP_LLM_PORT and DEDICATED_MCP_LLM_PORT.strip() else None
        self.dedicated_mcp_llm_api_path = DEDICATED_MCP_LLM_API_PATH if DEDICATED_MCP_LLM_API_PATH and DEDICATED_MCP_LLM_API_PATH.strip() else None

        # Also store fallback configuration values
        self.mcp_llm_provider = MCP_LLM_PROVIDER if MCP_LLM_PROVIDER and MCP_LLM_PROVIDER.strip() else None
        self.mcp_llm_model = MCP_LLM_MODEL if MCP_LLM_MODEL and MCP_LLM_MODEL.strip() else None
        self.mcp_llm_hostname = MCP_LLM_HOSTNAME if MCP_LLM_HOSTNAME and MCP_LLM_HOSTNAME.strip() else None
        self.mcp_llm_port = MCP_LLM_PORT if MCP_LLM_PORT and MCP_LLM_PORT.strip() else None
        self.mcp_llm_api_path = MCP_LLM_API_PATH if MCP_LLM_API_PATH and MCP_LLM_API_PATH.strip() else None

        self.prompt_llm_provider = PROMPT_LLM_PROVIDER if PROMPT_LLM_PROVIDER and PROMPT_LLM_PROVIDER.strip() else None
        self.prompt_llm_model = PROMPT_LLM_MODEL if PROMPT_LLM_MODEL and PROMPT_LLM_MODEL.strip() else None
        self.prompt_llm_hostname = PROMPT_LLM_HOSTNAME if PROMPT_LLM_HOSTNAME and PROMPT_LLM_HOSTNAME.strip() else None
        self.prompt_llm_port = PROMPT_LLM_PORT if PROMPT_LLM_PORT and PROMPT_LLM_PORT.strip() else None
        self.prompt_llm_api_path = PROMPT_LLM_API_PATH if PROMPT_LLM_API_PATH and PROMPT_LLM_API_PATH.strip() else None

        # Log the configuration being used before creating the LLM
        if ENABLE_SCREEN_LOGGING:
            logger.info(f"DedicatedMCPModel configured with provider: {self.dedicated_mcp_llm_provider}, model: {self.dedicated_mcp_llm_model}")

        # Initialize the prompt manager
        self.prompt_manager = PromptManager()

        # Create the LLM based on the dedicated MCP provider configuration
        provider = self.dedicated_mcp_llm_provider or self.mcp_llm_provider or self.prompt_llm_provider
        model = self.dedicated_mcp_llm_model or self.mcp_llm_model or self.prompt_llm_model
        hostname = self.dedicated_mcp_llm_hostname or self.mcp_llm_hostname or self.prompt_llm_hostname
        port = self.dedicated_mcp_llm_port or self.mcp_llm_port or self.prompt_llm_port
        api_path = self.dedicated_mcp_llm_api_path or self.mcp_llm_api_path or self.prompt_llm_api_path

        # If dedicated config is not set, fall back to MCP config, then to prompt config
        if not provider or not provider.strip():
            provider = self.mcp_llm_provider or self.prompt_llm_provider
        if not model or not model.strip():
            model = self.mcp_llm_model or self.prompt_llm_model
        if not hostname or not hostname.strip():
            hostname = self.mcp_llm_hostname or self.prompt_llm_hostname
        if not port or not port.strip():
            port = self.mcp_llm_port or self.prompt_llm_port
        if not api_path or not api_path.strip():
            api_path = self.mcp_llm_api_path or self.prompt_llm_api_path

        if provider and provider.lower() == 'gigachat':
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
            if provider and provider.lower() in ['openai', 'deepseek', 'qwen']:
                # For cloud providers, use HTTPS with the specified hostname
                # But for default OpenAI, allow using the default endpoint
                if provider.lower() == 'openai' and hostname == "api.openai.com":
                    base_url = None  # Use default OpenAI endpoint
                else:
                    base_url = f"https://{hostname}:{port}{api_path}" if hostname and port and api_path else None
            else:
                # For local providers like LM Studio or Ollama, use custom base URL with HTTP
                base_url = f"http://{hostname}:{port}{api_path}" if hostname and port and api_path else None

            # Create ChatOpenAI instance with appropriate configuration
            if provider and provider.lower() == 'openai':
                self.llm = ChatOpenAI(
                    model=model,
                    temperature=0.1,
                    openai_api_key=OPENAI_API_KEY,
                    base_url=base_url
                )
            elif provider and provider.lower() == 'deepseek':
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

        # Define the system prompt template for the dedicated MCP model using external prompt
        system_prompt = self.prompt_manager.get_prompt("mcp_capable_model")
        if system_prompt is None:
            # Fallback to default prompt if external prompt is not found
            system_prompt = """
You are an intelligent assistant with access to various MCP (Multi-Component Protocol) services and traditional LLM model knowledge. Your role is to understand user requests, determine if they can be fulfilled using the available MCP services or traditional methods.
Search engines awailable can be used to search any type of information.

Always try to provide responce to user.

Available MCP Services:
{mcp_services_json}

Your capabilities:
1. Analyze user requests to determine if MCP services can fulfill them
2. Generate appropriate tool calls to MCP services when needed
3. If MCP services cannot fulfill the request, use traditional methods
4. Always prioritize MCP services when they are relevant to the request
5. Do not ignore traditional methods
"""

        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input_text}")
        ])

        # Create the output parser
        self.output_parser = StrOutputParser()

        # Create the chain
        self.chain = self.prompt | self.llm | self.output_parser

    def get_config_info(self):
        """
        Returns the configuration information for debugging purposes.
        """
        return {
            "dedicated_mcp_llm_provider": self.dedicated_mcp_llm_provider,
            "dedicated_mcp_llm_model": self.dedicated_mcp_llm_model,
            "dedicated_mcp_llm_hostname": self.dedicated_mcp_llm_hostname,
            "dedicated_mcp_llm_port": self.dedicated_mcp_llm_port,
            "dedicated_mcp_llm_api_path": self.dedicated_mcp_llm_api_path,
            "mcp_llm_provider": self.mcp_llm_provider,
            "mcp_llm_model": self.mcp_llm_model,
            "mcp_llm_hostname": self.mcp_llm_hostname,
            "mcp_llm_port": self.mcp_llm_port,
            "mcp_llm_api_path": self.mcp_llm_api_path,
            "prompt_llm_provider": self.prompt_llm_provider,
            "prompt_llm_model": self.prompt_llm_model,
            "prompt_llm_hostname": self.prompt_llm_hostname,
            "prompt_llm_port": self.prompt_llm_port,
            "prompt_llm_api_path": self.prompt_llm_api_path
        }

    def generate_mcp_tool_calls(self, user_request: str, mcp_services: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate MCP tool calls based on user request and available services.

        Args:
            user_request: The user's natural language request
            mcp_services: List of available MCP services

        Returns:
            Dictionary containing tool calls to execute
        """
        logger.info(f"Generating MCP tool calls with DedicatedMCPModel for request: {user_request}")

        # Format MCP services as JSON for the prompt
        mcp_services_json = json.dumps(mcp_services, indent=2)

        try:
            # Log the full request to LLM, including all roles and prompts
            if ENABLE_SCREEN_LOGGING:
                # Get the full prompt with all messages (system and human) without invoking the LLM
                full_prompt = self.prompt.format_messages(
                    input_text=user_request,
                    mcp_services_json=mcp_services_json
                )
                logger.info("DedicatedMCPModel full LLM request:")
                for i, message in enumerate(full_prompt):
                    if message.type == "system":
                        logger.info(f"  System Message {i+1}: {message.content}")  # Full content without truncation
                    else:
                        logger.info(f"  Message {i+1} ({message.type}): {message.content}")

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
                logger.info(f"DedicatedMCPModel generated tool calls: {result}")
                return result
            except json.JSONDecodeError:
                logger.warning(f"DedicatedMCPModel response is not valid JSON: {response}")
                # If response is not valid JSON, return empty tool calls
                return {"tool_calls": []}

        except Exception as e:
            logger.error(f"Error generating MCP tool calls with DedicatedMCPModel: {str(e)}")
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
        logger.info(f"Executing {len(tool_calls)} MCP tool calls with DedicatedMCPModel")
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
                logger.error(f"Error calling MCP service {service_id} with DedicatedMCPModel: {str(e)}")
                results.append({
                    "service_id": service_id,
                    "status": "error",
                    "error": str(e)
                })

        logger.info(f"DedicatedMCPModel tool calls execution completed. Results: {results}")
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

        logger.info(f"Calling MCP service {service['id']} with DedicatedMCPModel for action '{action}' and parameters {parameters}")

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
                endpoint = f"{base_url}/{action.lstrip('/')}"  # Ensure action doesn't start with extra slash

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
                endpoint = f"{base_url}/{action.lstrip('/')}"

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