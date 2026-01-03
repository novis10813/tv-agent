"""
MCP HTTP Client
用於連接 Android TV MCP Server 並執行 tool calls
支援 FastMCP Streamable HTTP transport with session management
"""

import json
import httpx
from typing import Any


class MCPClient:
    """MCP HTTP Client for Streamable HTTP transport"""
    
    def __init__(self, base_url: str):
        """
        Args:
            base_url: MCP server URL (e.g., http://192.168.0.13:8765/mcp)
        """
        self.base_url = base_url.rstrip("/")
        self._session_id: str | None = None
        self._tools: list[dict] | None = None
    
    def _parse_sse_response(self, text: str) -> dict:
        """解析 SSE event-stream 格式的回應"""
        # SSE 格式: event: message\ndata: {...}\n\n
        for line in text.strip().split("\n"):
            if line.startswith("data: "):
                return json.loads(line[6:])
        # 如果不是 SSE 格式，嘗試直接解析 JSON
        return json.loads(text)
    
    async def initialize(self) -> dict:
        """初始化 MCP session 並取得可用 tools"""
        async with httpx.AsyncClient() as client:
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "agentic-tv-controller",
                        "version": "0.1.0"
                    }
                }
            }
            
            response = await client.post(
                self.base_url,
                json=init_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                timeout=30.0
            )
            
            # 從 header 取得 session ID
            self._session_id = response.headers.get("mcp-session-id")
            
            # 解析 SSE 格式的回應
            result = self._parse_sse_response(response.text)
            
            if "error" in result:
                raise Exception(f"MCP initialize failed: {result['error']}")
            
            return result.get("result", {})
    
    async def list_tools(self) -> list[dict]:
        """取得 MCP server 上的所有 tools"""
        if self._tools is not None:
            return self._tools
        
        if not self._session_id:
            await self.initialize()
        
        async with httpx.AsyncClient() as client:
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            
            # 帶上 session ID
            if self._session_id:
                headers["mcp-session-id"] = self._session_id
            
            response = await client.post(
                self.base_url,
                json=request,
                headers=headers,
                timeout=30.0
            )
            
            result = self._parse_sse_response(response.text)
            
            if "error" in result:
                raise Exception(f"MCP list_tools failed: {result['error']}")
            
            self._tools = result.get("result", {}).get("tools", [])
            return self._tools
    
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """
        呼叫 MCP tool
        
        Args:
            name: Tool 名稱
            arguments: Tool 參數
        
        Returns:
            Tool 執行結果
        """
        if not self._session_id:
            await self.initialize()
        
        async with httpx.AsyncClient() as client:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": name,
                    "arguments": arguments
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            
            if self._session_id:
                headers["mcp-session-id"] = self._session_id
            
            response = await client.post(
                self.base_url,
                json=request,
                headers=headers,
                timeout=60.0
            )
            
            result = self._parse_sse_response(response.text)
            
            if "error" in result:
                return f"Error: {result['error'].get('message', 'Unknown error')}"
            
            # 解析 MCP tool response
            content = result.get("result", {}).get("content", [])
            if content and len(content) > 0:
                return content[0].get("text", str(content))
            
            return str(result.get("result", "OK"))
    
    def mcp_tools_to_openai_tools(self, mcp_tools: list[dict]) -> list[dict]:
        """
        將 MCP tools 轉換為 OpenAI function calling 格式
        """
        openai_tools = []
        
        for tool in mcp_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                }
            }
            openai_tools.append(openai_tool)
        
        return openai_tools
