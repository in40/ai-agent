#!/usr/bin/env python3
"""
MCP Search Server Wrapper for Qwen Code
Converts HTTP-based search server to MCP protocol for Qwen integration
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'registry'))

from mcp import MCPClient


class QwenMCPSearchClient:
    """MCP client for Qwen Code to perform internet searches"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8090):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
    
    async def search(self, query: str) -> Dict[str, Any]:
        """
        Perform a search query via the HTTP search server
        
        Args:
            query: The search query string
            
        Returns:
            Dictionary containing search results
        """
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "query": query,
                "parameters": {"query": query}
            }
            
            async with session.post(
                f"{self.base_url}/search",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                return result


async def main():
    """Test the MCP search client"""
    client = QwenMCPSearchClient()
    
    query = "latest AI news 2026"
    print(f"Searching for: {query}")
    
    result = await client.search(query)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
