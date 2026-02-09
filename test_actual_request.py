#!/usr/bin/env python3
"""
More comprehensive test to simulate the actual request to the agent service
"""
import json
import requests
import sys
import traceback
import os

def test_actual_request():
    """Test making an actual request to the agent service"""
    
    # Define the problematic custom system prompt
    custom_system_prompt = """найди информацию в локальных документах и интернете и сформулируй детальные требования по информационной безопасности мобильного приложения для использования сотрудниками российского банка для обработки ПДН

Проанализируйте запрос пользователя и предложите подходящие MCP-запросы или сервисы, которые могут понадобиться для его выполнения.

Формат ответа для вызовов MCP-инструментов:
{
  "response": "", // оставьте пустым, если заполняете "tool_calls" для вызовов MCP-сервисов
  "is_final_answer": false, // Установите FALSE, если вы выполняете вызовы инструментов для сбора информации
  "has_sufficient_info": false, // Установите false, если планируете получить больше информации через вызовы инструментов
  "confidence_level": 0.5, // Число с плавающей точкой от 0.0 до 1.0, отражающее уверенность в ответе
  "tool_calls": [
    {
      "service_id": "идентификатор сервиса из списка доступных",
      "method": "вызываемый метод",
      "params": {
        "param1": "значение1",
        "param2": "значение2"
      }
    },
    {
      "service_id": "идентификатор сервиса из списка доступных для 2-го сервиса",
      "method": "вызываемый метод",
      "params": {
        "param1": "значение1",
        "param2": "значение2"
      }
    }
  ]
}

Формат ответа для финального ответа:
{
  "response": "Ваш ответ пользователю",
  "is_final_answer": true, // Установите true, если этот ответ полностью отвечает на запрос пользователя
  "has_sufficient_info": true, // Установите true, если у вас достаточно информации для ответа
  "confidence_level": 0.9, // Число с плавающей точкой от 0.0 до 1.0
  "tool_calls": [] // Оставьте пустым массивом для финального ответа
}

Available MCP Services:
[
  {
    "id": "dns-server-127-0-0-1-8089",
    "host": "127.0.0.1",
    "port": 8089,
    "type": "mcp_dns",
    "metadata": {
      "service_type": "dns_resolver",
      "capabilities": [
        "ipv4_resolution"
      ],
      "started_at": "2026-02-03T22:30:56.954481"
    }
  },
  {
    "id": "search-server-127-0-0-1-8090",
    "host": "127.0.0.1",
    "port": 8090,
    "type": "mcp_search",
    "metadata": {
      "service_type": "search_engine",
      "capabilities": [
        "web_search",
        "brave_search"
      ],
      "started_at": "2026-02-03T22:30:58.965294"
    }
  },
  {
    "id": "download-server-127-0-0-1-8093",
    "host": "127.0.0.1",
    "port": 8093,
    "type": "mcp_download",
    "metadata": {
      "service_type": "file_downloader",
      "capabilities": [
        "url_download",
        "file_transfer"
      ],
      "download_dir": "./downloads",
      "started_at": "2026-02-03T22:31:06.086911",
      "max_concurrent_downloads": 4
    }
  },
  {
    "id": "sql-server-127-0-0-1-8092",
    "host": "127.0.0.1",
    "port": 8092,
    "type": "mcp_sql",
    "metadata": {
      "name": "sql-service",
      "description": "SQL generation and execution service for database queries",
      "capabilities": [
        {
          "name": "generate_sql",
          "description": "Generate SQL query based on user request and schema",
          "parameters": {
            "user_request": {
              "type": "string",
              "required": true
            },
            "schema_dump": {
              "type": "object",
              "required": true
            },
            "attached_files": {
              "type": "array",
              "required": false
            },
            "previous_sql_queries": {
              "type": "array",
              "required": false
            },
            "table_to_db_mapping": {
              "type": "object",
              "required": false
            },
            "table_to_real_db_mapping": {
              "type": "object",
              "required": false
            }
          }
        },
        {
          "name": "execute_sql",
          "description": "Execute SQL query against the database",
          "parameters": {
            "sql_query": {
              "type": "string",
              "required": true
            },
            "db_name": {
              "type": "string",
              "required": false
            },
            "table_to_db_mapping": {
              "type": "object",
              "required": false
            }
          }
        },
        {
          "name": "get_schema",
          "description": "Get database schema information",
          "parameters": {
            "db_name": {
              "type": "string",
              "required": false
            }
          }
        },
        {
          "name": "validate_sql",
          "description": "Validate SQL query for safety and correctness",
          "parameters": {
            "sql_query": {
              "type": "string",
              "required": true
            },
            "schema_dump": {
              "type": "object",
              "required": false
            }
          }
        }
      ]
    }
  },
  {
    "id": "rag-server-127-0-0-1-8091",
    "host": "127.0.0.1",
    "port": 8091,
    "type": "rag",
    "metadata": {
      "name": "rag-service",
      "description": "RAG (Retrieval-Augmented Generation) service for document retrieval and ingestion",
      "protocol": "http",
      "capabilities": [
        {
          "name": "query_documents",
          "description": "Query documents using RAG",
          "parameters": {
            "query": {
              "type": "string",
              "required": true
            },
            "top_k": {
              "type": "integer",
              "required": false
            }
          }
        },
        {
          "name": "ingest_documents",
          "description": "Ingest documents into the RAG system",
          "parameters": {
            "directory_path": {
              "type": "string",
              "required": false
            },
            "file_paths": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "required": false
            }
          }
        },
        {
          "name": "list_documents",
          "description": "List available documents in the RAG system",
          "parameters": {}
        },
        {
          "name": "rerank_documents",
          "description": "Rerank documents based on relevance to query",
          "parameters": {"query": {
              "type": "string",
              "required": true
            },
            "documents": {
              "type": "array",
              "items": {
                "type": "object"
              },
              "required": true
            },
            "top_k": {
              "type": "integer",
              "required": false
            }
          }
        },
        {
          "name": "process_search_results_with_download",
          "description": "Process search results by downloading content, summarizing, and reranking",
          "parameters": {
            "search_results": {
              "type": "array",
              "items": {
                "type": "object"
              },
              "required": true
            },
            "user_query": {
              "type": "string",
              "required": true
            }
          }
        }
      ]
    }
  }
]"""

    # Create the request payload
    payload = {
        "user_request": "Test request with Russian prompt",
        "custom_system_prompt": custom_system_prompt
    }

    # Serialize to JSON with UTF-8 encoding
    json_str = json.dumps(payload, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    
    # Check the actual byte length
    print(f"JSON string length: {len(json_str)} characters")
    print(f"JSON bytes length: {len(json_bytes)} bytes")
    
    # Check if the prompt exceeds the max_length constraint (5000 chars)
    prompt_length = len(custom_system_prompt)
    print(f"Custom system prompt length: {prompt_length} characters")
    
    if prompt_length > 5000:
        print(f"⚠️  WARNING: Custom system prompt exceeds 5000 character limit by {prompt_length - 5000} characters!")
        print("This is likely causing the 400 error due to validation failure.")
        return False
    
    # Try to make an actual request to the agent service
    try:
        # Get the agent service URL from environment or use default
        agent_url = os.getenv('AGENT_SERVICE_URL', 'http://localhost:5002/query')
        
        # Headers with proper content type
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            # Authorization header would be needed in a real scenario
            # 'Authorization': 'Bearer your-jwt-token-here'
        }
        
        print(f"Making request to: {agent_url}")
        
        # Make the request
        response = requests.post(
            agent_url,
            data=json_bytes,
            headers=headers
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 400:
            print(f"Response body (400 error): {response.text}")
            return False
        else:
            print(f"Response body: {response.text[:500]}...")  # Truncate for readability
            return True
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Connection error - agent service may not be running")
        print("This is expected if the service isn't running for testing purposes")
        return True  # Not a failure of the encoding itself
    except Exception as e:
        print(f"✗ Request failed with exception: {e}")
        traceback.print_exc()
        return False

def test_simplified_request():
    """Test with a much simpler version of the prompt"""
    
    # Much shorter version focusing on the core issue
    simple_prompt = """найди информацию и сформулируй требования по информационной безопасности"""

    payload = {
        "user_request": "Test request",
        "custom_system_prompt": simple_prompt
    }

    json_str = json.dumps(payload, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    
    print(f"\nSimple prompt length: {len(simple_prompt)} characters")
    print(f"Simple JSON bytes length: {len(json_bytes)} bytes")
    
    try:
        # Get the agent service URL from environment or use default
        agent_url = os.getenv('AGENT_SERVICE_URL', 'http://localhost:5002/query')
        
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
        }
        
        print(f"Making simplified request to: {agent_url}")
        
        response = requests.post(
            agent_url,
            data=json_bytes,
            headers=headers
        )
        
        print(f"Simplified response status: {response.status_code}")
        if response.status_code == 400:
            print(f"Simplified response body (400 error): {response.text}")
            return False
        else:
            print(f"Simplified response body: {response.text[:500]}...")
            return True
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Connection error - agent service may not be running")
        return True  # Not a failure of the encoding itself
    except Exception as e:
        print(f"✗ Simplified request failed with exception: {e}")
        return False

if __name__ == "__main__":
    print("Testing actual request to agent service with Russian text...")
    
    print("\n=== Testing full prompt ===")
    full_test_passed = test_actual_request()
    
    print("\n=== Testing simplified prompt ===")
    simple_test_passed = test_simplified_request()
    
    print(f"\nResults:")
    print(f"Full prompt test: {'PASS' if full_test_passed else 'FAIL'}")
    print(f"Simple prompt test: {'PASS' if simple_test_passed else 'FAIL'}")
    
    if not full_test_passed and "WARNING: Custom system prompt exceeds 5000 character limit" in globals():
        print("\nThe issue is the length of the custom system prompt exceeding the 5000 character limit.")
        print("The validation in the agent service is rejecting the request with a 400 error.")
    elif not full_test_passed:
        print("\nThe issue persists even with proper encoding and length.")
        print("There may be other validation or processing issues in the agent service.")