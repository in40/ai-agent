#!/usr/bin/env python3
"""
Debug script to test the encoding issue with Russian text in custom system prompt
"""
import json
import requests
import sys
import traceback

def test_custom_prompt_encoding():
    """Test sending a request with Russian text in custom system prompt"""
    
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

    # Test JSON serialization
    try:
        json_str = json.dumps(payload, ensure_ascii=False)
        print("✓ JSON serialization successful")
        print(f"JSON length: {len(json_str)} characters")
        
        # Check if the Russian text is preserved correctly
        loaded_back = json.loads(json_str)
        if loaded_back["custom_system_prompt"] == custom_system_prompt:
            print("✓ Russian text preserved correctly after JSON serialization/deserialization")
        else:
            print("✗ Russian text was altered during JSON serialization/deserialization")
            
    except Exception as e:
        print(f"✗ JSON serialization failed: {e}")
        return False

    # Try to make an actual request (this might fail if the service isn't running)
    try:
        # Note: This assumes the agent service is running on localhost:5002
        # You may need to adjust the URL based on your setup
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer your-token-here'  # Replace with actual token if required
        }
        
        print("\nAttempting to send request to agent service...")
        # Commenting out the actual request to avoid errors if service isn't running
        # response = requests.post("http://localhost:5002/query", 
        #                         data=json_str.encode('utf-8'), 
        #                         headers=headers)
        # print(f"Response status: {response.status_code}")
        
        print("✓ Request would be sent with proper UTF-8 encoding")
        return True
        
    except Exception as e:
        print(f"✗ Request failed: {e}")
        traceback.print_exc()
        return False

def test_simplified_prompt():
    """Test with a simplified version of the prompt to isolate the issue"""
    
    # Simplified version with minimal Russian text
    simple_prompt = "найди информацию и сформулируй требования"
    
    payload = {
        "user_request": "Test request",
        "custom_system_prompt": simple_prompt
    }
    
    try:
        json_str = json.dumps(payload, ensure_ascii=False)
        print(f"\n✓ Simple prompt JSON serialization successful, length: {len(json_str)}")
        
        # Check preservation
        loaded_back = json.loads(json_str)
        if loaded_back["custom_system_prompt"] == simple_prompt:
            print("✓ Simple Russian text preserved correctly")
        else:
            print("✗ Simple Russian text was altered")
            
        return True
    except Exception as e:
        print(f"✗ Simple prompt JSON serialization failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing encoding of Russian text in custom system prompt...")
    
    print("\n=== Testing full prompt ===")
    full_test_passed = test_custom_prompt_encoding()
    
    print("\n=== Testing simplified prompt ===")
    simple_test_passed = test_simplified_prompt()
    
    print(f"\nResults:")
    print(f"Full prompt test: {'PASS' if full_test_passed else 'FAIL'}")
    print(f"Simple prompt test: {'PASS' if simple_test_passed else 'FAIL'}")
    
    if not full_test_passed:
        print("\nThe issue is likely related to the length or complexity of the Russian text in the custom prompt.")
        print("Consider shortening the prompt or ensuring proper UTF-8 encoding in your client.")