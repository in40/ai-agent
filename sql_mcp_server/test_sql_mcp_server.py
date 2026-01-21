"""
Test suite for SQL MCP Server
"""

import asyncio
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sql_mcp_server.sql_mcp_server import SQLRequestHandler, SQLMCPServer
from models.sql_generator import SQLGenerator
from models.sql_executor import SQLExecutor


class TestSQLRequestHandler(unittest.TestCase):
    """Test cases for SQLRequestHandler."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_generator = Mock(spec=SQLGenerator)
        self.mock_executor = Mock(spec=SQLExecutor)
        self.handler = SQLRequestHandler(self.mock_generator, self.mock_executor)

    @patch('sql_mcp_server.sql_mcp_server.multi_db_manager')
    def test_generate_sql_success(self, mock_multi_db_manager):
        """Test successful SQL generation."""
        # Arrange
        parameters = {
            "user_request": "Show me all users",
            "schema_dump": {"users": [{"name": "id", "type": "int"}]}
        }
        
        self.mock_generator.generate_sql.return_value = "SELECT * FROM users;"
        
        # Act
        result = asyncio.run(self.handler.generate_sql(parameters))
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["sql_query"], "SELECT * FROM users;")
        self.mock_generator.generate_sql.assert_called_once()

    def test_generate_sql_missing_request(self):
        """Test SQL generation with missing user request."""
        # Arrange
        parameters = {
            "schema_dump": {"users": [{"name": "id", "type": "int"}]}
        }
        
        # Act
        result = asyncio.run(self.handler.generate_sql(parameters))
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertIn("User request is required", result["error"])

    def test_execute_sql_success(self):
        """Test successful SQL execution."""
        # Arrange
        parameters = {
            "sql_query": "SELECT * FROM users;",
            "db_name": "test_db"
        }
        
        self.mock_executor.execute_sql_and_get_results.return_value = [{"id": 1, "name": "John"}]
        
        # Act
        result = asyncio.run(self.handler.execute_sql(parameters))
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], 1)
        self.mock_executor.execute_sql_and_get_results.assert_called_once()

    def test_execute_sql_missing_query(self):
        """Test SQL execution with missing query."""
        # Arrange
        parameters = {
            "db_name": "test_db"
        }
        
        # Act
        result = asyncio.run(self.handler.execute_sql(parameters))
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertIn("SQL query is required", result["error"])

    @patch('sql_mcp_server.sql_mcp_server.multi_db_manager')
    def test_get_schema_success(self, mock_multi_db_manager):
        """Test successful schema retrieval."""
        # Arrange
        parameters = {"db_name": "test_db"}
        expected_schema = {"users": [{"name": "id", "type": "int"}]}
        mock_multi_db_manager.get_schema_dump.return_value = expected_schema
        
        # Act
        result = asyncio.run(self.handler.get_schema(parameters))
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["schema"], expected_schema)

    def test_validate_sql_safe_query(self):
        """Test validation of a safe SQL query."""
        # Arrange
        parameters = {
            "sql_query": "SELECT * FROM users;",
            "schema_dump": {}
        }
        
        self.mock_executor.check_for_harmful_commands.return_value = (True, [])
        
        # Act
        result = asyncio.run(self.handler.validate_sql(parameters))
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["is_safe"])
        self.assertEqual(len(result["issues"]), 0)

    def test_validate_sql_unsafe_query(self):
        """Test validation of an unsafe SQL query."""
        # Arrange
        parameters = {
            "sql_query": "DROP TABLE users;",
            "schema_dump": {}
        }
        
        self.mock_executor.check_for_harmful_commands.return_value = (False, ["Contains potentially harmful command: drop"])
        
        # Act
        result = asyncio.run(self.handler.validate_sql(parameters))
        
        # Assert
        self.assertEqual(result["status"], "validation_failed")
        self.assertFalse(result["is_safe"])
        self.assertEqual(len(result["issues"]), 1)


class TestSQLMCPServer(unittest.TestCase):
    """Test cases for SQLMCPServer."""

    def setUp(self):
        """Set up test fixtures."""
        self.server = SQLMCPServer(host="127.0.0.1", port=8092, registry_url="http://127.0.0.1:8080")

    @patch('sql_mcp_server.sql_mcp_server.RegistryClient')
    @patch('sql_mcp_server.sql_mcp_server.SQLGenerator')
    @patch('sql_mcp_server.sql_mcp_server.SQLExecutor')
    @patch('sql_mcp_server.sql_mcp_server.multi_db_manager')
    async def test_start_server(self, mock_multi_db_manager, mock_sql_executor, mock_sql_generator, mock_registry_client):
        """Test starting the SQL MCP server."""
        # Arrange
        mock_registry_instance = Mock()
        mock_registry_client.return_value = mock_registry_instance
        
        mock_generator_instance = Mock()
        mock_sql_generator.return_value = mock_generator_instance
        
        mock_executor_instance = Mock()
        mock_sql_executor.return_value = mock_executor_instance
        
        # Act
        await self.server.start()
        
        # Assert
        self.assertTrue(self.server.running)
        self.assertIsNotNone(self.server.sql_generator)
        self.assertIsNotNone(self.server.sql_executor)
        self.assertIsNotNone(self.server.request_handler)
        mock_registry_instance.register_service.assert_called_once()

    @patch('sql_mcp_server.sql_mcp_server.RegistryClient')
    async def test_stop_server(self, mock_registry_client):
        """Test stopping the SQL MCP server."""
        # Arrange
        mock_registry_instance = Mock()
        mock_registry_client.return_value = mock_registry_instance
        
        # We need to start the server first to set up the runner
        with patch('sql_mcp_server.sql_mcp_server.SQLGenerator'), \
             patch('sql_mcp_server.sql_mcp_server.SQLExecutor'), \
             patch('sql_mcp_server.sql_mcp_server.multi_db_manager'), \
             patch.object(self.server, '_start_server'):
            
            await self.server.start()
            self.server.runner = Mock()
            self.server.runner.cleanup = AsyncMock()
            
            # Act
            await self.server.stop()
            
            # Assert
            self.assertFalse(self.server.running)
            mock_registry_instance.deregister_service.assert_called_once_with("sql-service")


class AsyncMock(Mock):
    """Helper class to mock async functions."""
    
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


if __name__ == '__main__':
    unittest.main()