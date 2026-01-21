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

        # Initialize the prompt manager with the correct prompts directory
        self.prompt_manager = PromptManager("./core/prompts")

        # Create the LLM based on the dedicated MCP provider configuration
        # If DEDICATED_MCP_LLM_PROVIDER is empty or set to "default", use the default configuration
        if DEDICATED_MCP_LLM_PROVIDER.lower() in ['', 'default']:
            provider = DEFAULT_LLM_PROVIDER
            model = DEFAULT_LLM_MODEL
            hostname = DEFAULT_LLM_HOSTNAME
            port = DEFAULT_LLM_PORT
            api_path = DEFAULT_LLM_API_PATH
        elif DEDICATED_MCP_LLM_PROVIDER and DEDICATED_MCP_LLM_PROVIDER.strip():
            provider = DEDICATED_MCP_LLM_PROVIDER
            model = DEDICATED_MCP_LLM_MODEL
            hostname = DEDICATED_MCP_LLM_HOSTNAME
            port = DEDICATED_MCP_LLM_PORT
            api_path = DEDICATED_MCP_LLM_API_PATH
        elif MCP_LLM_PROVIDER and MCP_LLM_PROVIDER.strip():
            provider = MCP_LLM_PROVIDER
            model = MCP_LLM_MODEL
            hostname = MCP_LLM_HOSTNAME
            port = MCP_LLM_PORT
            api_path = MCP_LLM_API_PATH
        elif PROMPT_LLM_PROVIDER and PROMPT_LLM_PROVIDER.strip():
            provider = PROMPT_LLM_PROVIDER
            model = PROMPT_LLM_MODEL
            hostname = PROMPT_LLM_HOSTNAME
            port = PROMPT_LLM_PORT
            api_path = PROMPT_LLM_API_PATH
        else:
            # If none of the specific configurations are set, use the default configuration
            provider = DEFAULT_LLM_PROVIDER
            model = DEFAULT_LLM_MODEL
            hostname = DEFAULT_LLM_HOSTNAME
            port = DEFAULT_LLM_PORT
            api_path = DEFAULT_LLM_API_PATH

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
        system_prompt_template = self.prompt_manager.get_prompt("mcp_capable_model")
        if system_prompt_template is None:
            # If the external prompt is not found, raise an error to ensure prompts are maintained properly
            raise FileNotFoundError("mcp_capable_model.txt not found in prompts directory. Please ensure the prompt file exists.")

        # Store the system prompt template for later use when creating temporary chains
        self.system_prompt_template = system_prompt_template

        # Create the output parser
        self.output_parser = StrOutputParser()

        # Store the system prompt template for later use when creating temporary chains
        # We need to handle the template variables properly to avoid conflicts with JSON examples
        self.system_prompt_template = system_prompt_template

        # Create a basic prompt template with an empty JSON for MCP services for general use
        # We need to properly handle the template variable to avoid conflicts with JSON examples
        # The prompt contains {mcp_services_json} as a variable and {{ }} as literal braces for JSON examples
        # Replace the template variable with an empty JSON object string representation
        basic_system_prompt = system_prompt_template.replace('{mcp_services_json}', '{}')

        self.basic_prompt = ChatPromptTemplate.from_messages([
            ("system", basic_system_prompt),
            ("human", "{input_text}")
        ])

        # Create the chain with the basic prompt
        self.chain = self.basic_prompt | self.llm | self.output_parser

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

                # Handle nested structure where the tool call is wrapped in a 'tool_call' key
                if isinstance(result, dict) and 'tool_call' in result:
                    # Extract the actual tool call from the 'tool_call' key
                    actual_tool_call = result['tool_call']
                    if isinstance(actual_tool_call, dict):
                        # Wrap the single tool call in a list and return
                        return {"tool_calls": [actual_tool_call]}

                # Ensure the result has the expected format with a 'tool_calls' key
                if isinstance(result, list):
                    # If the result is a list of tool calls, wrap it
                    return {"tool_calls": result}
                elif isinstance(result, dict) and "tool_calls" not in result:
                    # If the result is a single tool call object, wrap it in a list
                    return {"tool_calls": [result]}
                else:
                    # If it already has the 'tool_calls' key or is in the expected format, return as is
                    return result
            except json.JSONDecodeError:
                logger.warning(f"DedicatedMCPModel response is not valid JSON: {response}")

                # Try to extract JSON from the response if it contains JSON within a larger string
                # This handles cases where the LLM returns a response with JSON inside it
                import re

                # First, try to find JSON between ```json and ``` markers (common in LLM responses)
                json_pattern = r'```(?:json)?\s*\n*(\{(?:.|\n)*?\})\s*\n*```'
                json_match = re.search(json_pattern, response, re.DOTALL)

                if not json_match:
                    # If not found, try to find any JSON object in the response
                    # Look for JSON objects that start with { and end with }, handling nested structures
                    brace_count = 0
                    start_idx = -1

                    for i, char in enumerate(response):
                        if char == '{':
                            if brace_count == 0:
                                start_idx = i
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0 and start_idx != -1:
                                # Found a complete JSON object
                                try:
                                    potential_json = response[start_idx:i+1]
                                    result = json.loads(potential_json)
                                    logger.info(f"DedicatedMCPModel extracted JSON from response: {result}")

                                    # Handle nested structure where the tool call is wrapped in a 'tool_call' key
                                    if isinstance(result, dict) and 'tool_call' in result:
                                        # Extract the actual tool call from the 'tool_call' key
                                        actual_tool_call = result['tool_call']
                                        if isinstance(actual_tool_call, dict):
                                            # Wrap the single tool call in a list and return
                                            return {"tool_calls": [actual_tool_call]}

                                    # Ensure the extracted result has the expected format
                                    if isinstance(result, list):
                                        return {"tool_calls": result}
                                    elif isinstance(result, dict) and "tool_calls" not in result:
                                        return {"tool_calls": [result]}
                                    else:
                                        return result
                                except json.JSONDecodeError:
                                    # If this JSON object is invalid, continue looking
                                    continue

                if json_match:
                    try:
                        extracted_json = json_match.group(1)  # Get the captured group (the JSON part)
                        result = json.loads(extracted_json)
                        logger.info(f"DedicatedMCPModel extracted JSON from response: {result}")

                        # Handle nested structure where the tool call is wrapped in a 'tool_call' key
                        if isinstance(result, dict) and 'tool_call' in result:
                            # Extract the actual tool call from the 'tool_call' key
                            actual_tool_call = result['tool_call']
                            if isinstance(actual_tool_call, dict):
                                # Wrap the single tool call in a list and return
                                return {"tool_calls": [actual_tool_call]}

                        # Ensure the extracted result has the expected format
                        if isinstance(result, list):
                            return {"tool_calls": result}
                        elif isinstance(result, dict) and "tool_calls" not in result:
                            return {"tool_calls": [result]}
                        else:
                            return result
                    except json.JSONDecodeError:
                        logger.warning(f"Extracted text is still not valid JSON: {extracted_json}")

                        # Sometimes the LLM might return JSON with extra formatting, try to clean it
                        cleaned_json = extracted_json.strip()
                        # Remove any trailing commas before closing braces or brackets
                        cleaned_json = re.sub(r',(\s*[}\]])', r'\1', cleaned_json)
                        try:
                            result = json.loads(cleaned_json)
                            logger.info(f"DedicatedMCPModel extracted and cleaned JSON from response: {result}")

                            # Handle nested structure where the tool call is wrapped in a 'tool_call' key
                            if isinstance(result, dict) and 'tool_call' in result:
                                # Extract the actual tool call from the 'tool_call' key
                                actual_tool_call = result['tool_call']
                                if isinstance(actual_tool_call, dict):
                                    # Wrap the single tool call in a list and return
                                    return {"tool_calls": [actual_tool_call]}

                            # Ensure the cleaned result has the expected format
                            if isinstance(result, list):
                                return {"tool_calls": result}
                            elif isinstance(result, dict) and "tool_calls" not in result:
                                return {"tool_calls": [result]}
                            else:
                                return result
                        except json.JSONDecodeError:
                            logger.warning(f"Even cleaned JSON is not valid: {cleaned_json}")

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
            # Handle both 'service' and 'service_id' fields - some LLMs return 'service' instead of 'service_id'
            service_id = call.get('service_id') or call.get('service')

            # Handle both 'action' and 'method' fields - some LLMs return 'method' instead of 'action'
            action = call.get('action') or call.get('method')

            # Collect parameters - start with any existing 'parameters' object
            parameters = call.get('parameters', {}).copy()

            # Check if there's a 'params' key in the call (used by some LLMs to group parameters)
            if 'params' in call:
                # Merge the contents of 'params' into the main parameters dict
                parameters.update(call['params'])

            # Add any other fields that aren't service/action identifiers to the parameters
            # This handles cases where parameters are passed directly in the call object
            # rather than nested under a 'parameters' key
            for key, value in call.items():
                if key not in ['service_id', 'service', 'action', 'method', 'parameters', 'params']:
                    parameters[key] = value

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

    def evaluate_if_can_answer(self, user_request: str, synthesized_result: str) -> bool:
        """
        Evaluate if the agent can adequately answer the user's request based on the synthesized results.

        Args:
            user_request: The original user request
            synthesized_result: The synthesized results from MCP services

        Returns:
            Boolean indicating whether the agent can adequately answer the request
        """
        logger.info(f"Evaluating if DedicatedMCPModel can answer request: {user_request[:100]}...")

        # Create a prompt to evaluate if the synthesized results adequately answer the question
        evaluation_prompt = f"""
        Original request: {user_request}

        Synthesized results from MCP services:
        {synthesized_result}

        Based on the synthesized results, can the original request be adequately answered?
        Respond with only 'true' if the request can be adequately answered, or 'false' if it cannot.
        """

        try:
            # Create a temporary system prompt by replacing the {mcp_services_json} placeholder with an empty JSON object
            # We need to be careful to avoid conflicts with JSON examples in the prompt
            temp_system_prompt = self.system_prompt_template.replace('{mcp_services_json}', '{}')

            # Create a temporary chain with the formatted system prompt
            temp_prompt = ChatPromptTemplate.from_messages([
                ("system", temp_system_prompt),
                ("human", "{input_text}")
            ])

            temp_chain = temp_prompt | self.llm | self.output_parser

            # Use SSH keep-alive during the LLM call
            with SSHKeepAliveContext():
                # Generate the response using the temporary chain
                response = temp_chain.invoke({
                    "input_text": evaluation_prompt
                })

            # Parse the response to determine if we can answer
            response_lower = response.strip().lower()
            can_answer = 'true' in response_lower or 'yes' in response_lower

            logger.info(f"DedicatedMCPModel evaluation result: can_answer = {can_answer}")
            return can_answer

        except Exception as e:
            logger.error(f"Error evaluating if can answer with DedicatedMCPModel: {str(e)}")
            # Default to False in case of error, meaning we cannot adequately answer
            return False

    def analyze_request_for_mcp_services(self, user_request: str, mcp_servers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the user request to determine what MCP services might be needed.

        Args:
            user_request: The user's natural language request
            mcp_servers: List of available MCP servers

        Returns:
            Dictionary containing suggested queries or actions to take
        """
        logger.info(f"Analyzing request with DedicatedMCPModel: {user_request[:100]}...")

        # Format MCP servers as JSON for the prompt
        mcp_servers_json = json.dumps(mcp_servers, indent=2)

        # Create a prompt to analyze the request and suggest MCP services to use
        analysis_prompt = f"""
        User request: {user_request}

        Available MCP services:
        {mcp_servers_json}

        Analyze the user request and suggest appropriate MCP queries or services that might be needed to fulfill the request.
        """

        try:
            # Create a temporary system prompt by replacing the {mcp_services_json} placeholder with actual JSON
            # We need to be careful to avoid conflicts with JSON examples in the prompt
            temp_system_prompt = self.system_prompt_template.replace('{mcp_services_json}', mcp_servers_json)

            # Create a temporary chain with the formatted system prompt
            temp_prompt = ChatPromptTemplate.from_messages([
                ("system", temp_system_prompt),
                ("human", "{input_text}")
            ])

            temp_chain = temp_prompt | self.llm | self.output_parser

            # Log the full request to LLM, including all roles and prompts
            if ENABLE_SCREEN_LOGGING:
                # Get the full prompt with all messages (system and human) without invoking the LLM
                full_prompt = temp_prompt.format_messages(input_text=analysis_prompt)
                logger.info("DedicatedMCPModel full LLM request:")
                for i, message in enumerate(full_prompt):
                    if message.type == "system":
                        logger.info(f"  System Message {i+1}: {message.content[:200]}...")  # Truncate for logging
                    else:
                        logger.info(f"  Message {i+1} ({message.type}): {message.content}")

            # Use SSH keep-alive during the LLM call
            with SSHKeepAliveContext():
                # Generate the response using the temporary chain
                response = temp_chain.invoke({
                    "input_text": analysis_prompt
                })

            # Try to parse the response as JSON
            try:
                result = json.loads(response)
                logger.info(f"DedicatedMCPModel analysis result: {result}")
                return result
            except json.JSONDecodeError:
                logger.warning(f"DedicatedMCPModel analysis response is not valid JSON: {response}")
                # Return a default structure with the raw response
                return {"suggested_queries": [], "analysis": response}

        except Exception as e:
            logger.error(f"Error analyzing request with DedicatedMCPModel: {str(e)}")
            # Return a default structure in case of error
            return {"suggested_queries": [], "analysis": f"Error analyzing request: {str(e)}"}

    def execute_single_query(self, query: str, mcp_servers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute a single query against the MCP server pool.

        Args:
            query: The query to execute
            mcp_servers: List of available MCP servers

        Returns:
            Result of the query execution
        """
        logger.info(f"Executing single query with DedicatedMCPModel: {query}")

        # This is a simplified implementation - in a real system, you would
        # determine which server to use based on the query and execute it
        try:
            # For now, we'll just return a simulated result
            # In a real implementation, you would route the query to the appropriate MCP service
            return {
                "status": "success",
                "data": f"Simulated result for query: {query}",
                "query_executed": query
            }
        except Exception as e:
            logger.error(f"Error executing single query with DedicatedMCPModel: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "query_executed": query
            }

    def plan_refined_queries(self, user_request: str, current_results: List[Dict], synthesized_result: str) -> List[Dict]:
        """
        Plan refined queries for the next iteration based on current results and gaps

        Args:
            user_request: Original user request
            current_results: Current MCP results
            synthesized_result: Current synthesized result

        Returns:
            List of refined queries to execute
        """
        logger.info(f"Planning refined queries for request: {user_request[:100]}...")

        # Create a prompt to plan refined queries based on current results
        planning_prompt = f"""
        Original request: {user_request}

        Current results: {json.dumps(current_results, indent=2)}

        Current synthesized result: {synthesized_result}

        Based on the current results and the original request, what additional MCP queries should be performed
        to better address the user's request? If the request has been adequately addressed,
        return an empty list.
        """

        try:
            # Create a temporary system prompt by replacing the {mcp_services_json} placeholder with an empty JSON object
            # We need to be careful to avoid conflicts with JSON examples in the prompt
            temp_system_prompt = self.system_prompt_template.replace('{mcp_services_json}', '{}')

            # Create a temporary chain with the formatted system prompt
            temp_prompt = ChatPromptTemplate.from_messages([
                ("system", temp_system_prompt),
                ("human", "{input_text}")
            ])

            temp_chain = temp_prompt | self.llm | self.output_parser

            # Use SSH keep-alive during the LLM call
            with SSHKeepAliveContext():
                # Generate the response using the temporary chain
                response = temp_chain.invoke({
                    "input_text": planning_prompt
                })

            # Parse the response - in a real implementation, this would return structured query plans
            # For now, we'll return an empty list to prevent infinite loops
            logger.info("Planned refined queries (returned empty list to prevent infinite loops)")
            return []

        except Exception as e:
            logger.error(f"Error planning refined queries with DedicatedMCPModel: {str(e)}")
            # Return empty list in case of error to prevent infinite loops
            return []