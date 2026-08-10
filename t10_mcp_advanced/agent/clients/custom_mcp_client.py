import json
import uuid
from typing import Optional, Any
import aiohttp


MCP_SESSION_ID_HEADER = "Mcp-Session-Id"

class CustomMCPClient:
    """Pure Python MCP client without external MCP libraries"""

    def __init__(self, mcp_server_url: str) -> None:
        self.server_url = mcp_server_url
        self.session_id: Optional[str] = None
        self.http_session: Optional[aiohttp.ClientSession] = None

    @classmethod
    async def create(cls, mcp_server_url: str) -> 'CustomMCPClient':
        """Async factory method to create and connect CustomMCPClient"""
        instance = cls(mcp_server_url)
        await instance.connect()
        return instance

    async def _send_request(self, method: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Send JSON-RPC request to MCP server"""
        #TODO:
        # 1. Check session is present
        if self.http_session is None:
            raise RuntimeError("MCP client not connected. Call connect() first.")
        # 2. Prepare request body and don't forget to add parameters there if they are present. Sample of request body see in Postman collection
        request_data = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params or {}
        }
        # 3. Prepare headers dict. Remember that according to protocol MCP Server Accept application/json and text/event-stream
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        # 4. Add session ID header for non-initialize requests (notify, discovery, operation):
        if self.session_id:
            headers[MCP_SESSION_ID_HEADER] = self.session_id
        # 5. Make POST request using `self.http_session.post()` as `response` with:
        #       - url: self.server_url
        #       - json: request_data
        #       - headers: headers
        async with self.http_session.post(self.server_url, json=request_data, headers=headers) as response:
            # 6. If MCP_SESSION_ID_HEADER exists in `response.headers`, set `self.session_id = response.headers[MCP_SESSION_ID_HEADER]` and print session ID
            if MCP_SESSION_ID_HEADER in response.headers:
                self.session_id = response.headers[MCP_SESSION_ID_HEADER]
                print(f"Session ID: {self.session_id}")
            # 7. Handle response:
            #    - If `response.status == 202`, return empty dict `{}` (successful notification)
            if response.status == 202:
                return {}
            #    - Get `content-type` from response headers
            content_type = response.headers.get("Content-Type", "")
            #    - If `'text/event-stream' in content_type.lower()`:
            #        - call `await self._parse_sse_response_streaming(response)` and assign to `response_data`
            if 'text/event-stream' in content_type.lower():
                response_data = await self._parse_sse_response_streaming(response)
            else:
                #      Otherwise call `await response.json()` and assign to `response_data`
                response_data = await response.json()
            #    - If "error" in `response_data`, extract `error = response_data["error"]` and raise RuntimeError(f"MCP Error {error['code']}: {error['message']}")
            if "error" in response_data:
                error = response_data["error"]
                raise RuntimeError(f"MCP Error {error['code']}: {error['message']}")
            #    - Return `response_data`
            return response_data
        #    And:
        #       - If `not self.session_id` and `response.headers.get(MCP_SESSION_ID_HEADER)` exists, set `self.session_id = response.headers[MCP_SESSION_ID_HEADER]`
        #       - If `response.status == 202`, return empty dict `{}` (successful notification)
        #       - Get `content-type` from response headers
        #       - If `'text/event-stream' in content_type.lower()`:
        #           - call `await self._parse_sse_response_streaming(response)` and assign to `response_data`
        #         Otherwise call `await response.json()` and assign to `response_data`
        #       - If "error" in `response_data`, extract `error = response_data["error"]` and raise RuntimeError(f"MCP Error {error['code']}: {error['message']}")
        #       - Return `response_data`


    async def _parse_sse_response_streaming(self, response: aiohttp.ClientResponse) -> dict[str, Any]:
        """Parse Server-Sent Events response with streaming"""
        #TODO:
        # Response stream sample:
        # data: {
        #     "jsonrpc": "2.0",
        #     "id": 1,
        #     "result": {
        #         "content": [
        #             {
        #                 "type": "text",
        #                 "text": "some tool call result"
        #             }
        #         ]
        #     }
        # }
        # data: [DONE]
        # ---
        # 1. Make async loop from the `response.content`
        #       - create `line_str` from `line.decode('utf-8').strip()`
        #       - if line is not present or starts with ':' skip iteration (with continue)
        #       - if line starts with 'data: ' then:
        #           - extract data part: `data_part = line[6:]` (remove 'data: ' prefix)
        #           - If `data_part != '[DONE]'`, then `return json.loads(data_part)` (we just need first chunk since MCP tool returns response with 1 chunk)
        for line in response.content:
            line_str = line.decode('utf-8').strip()
            if not line_str or line_str.startswith(':'):
                continue
            if line_str.startswith('data: '):
                data_part = line_str[6:]  # remove 'data: ' prefix
                if data_part != '[DONE]':
                    return json.loads(data_part)
        # 2. raise RuntimeError("No valid data found in SSE response")
        raise RuntimeError("No valid data found in SSE response")

    async def connect(self) -> None:
        """Connect to MCP server and initialize session"""
        #TODO:
        # 1. Set up aiohttp.ClientTimeout with `total=30, connect=10`
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        # 2. Set up aiohttp.TCPConnector with `limit=100, limit_per_host=10`
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        self.http_session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        # 3. Try-except block:
        #       - Create `init_params` dictionary with:
        #           - "protocolVersion": "2024-11-05"
        #           - "capabilities": {"tools": {}}
        #           - "clientInfo": {"name": "my-custom-mcp-client", "version": "1.0.0"}
        #       - Call `await self._send_request("initialize", init_params)` and save result into variable (to print later capabilities of MCP Server)
        #       - Call `await self._send_notification("notifications/initialized")`
        #       - Print capabilities (from init request)
        # 4. Catch Exception as `e` and raise RuntimeError(f"Failed to connect to MCP server: {e}")
        try:
            init_params = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "my-custom-mcp-client", "version": "1.0.0"},
            }
            init_response = await self._send_request("initialize", init_params)
            await self._send_notification("notifications/initialized")
            capabilities = init_response.get("result", {}).get("capabilities", {})
            print(f"Connected. Server capabilities: {capabilities}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to MCP server: {e}") from e


    async def _send_notification(self, method: str) -> None:
        """Send notification (no response expected)"""
        if self.http_session is None:
            raise RuntimeError("HTTP session not initialized")

        request_data = {
            "jsonrpc": "2.0",
            "method": method,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers[MCP_SESSION_ID_HEADER] = self.session_id

        async with self.http_session.post(self.server_url, json=request_data, headers=headers) as response:
            if MCP_SESSION_ID_HEADER in response.headers:
                self.session_id = response.headers[MCP_SESSION_ID_HEADER]
                print(f"Session ID: {self.session_id}")
            if response.status not in (200, 202):
                body = await response.text()
                raise RuntimeError(f"Notification failed: {response.status}: {body}")
            return

    async def get_tools(self) -> list[dict[str, Any]]:
        """Get available tools from MCP server"""
        if self.http_session is None:
            raise RuntimeError("MCP client not connected. Call connect() first.")
        response = await self._send_request("tools/list")
        tools = response.get("result", {}).get("tools", [])
        if not isinstance(tools, list):
            raise RuntimeError("Invalid tools response from MCP server")
        return tools

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server"""
        #TODO:
        # 1. Check if `self.http_session` is None, raise RuntimeError("MCP client not connected. Call connect() first.") if so
        if self.http_session is None:
            raise RuntimeError("MCP client not connected. Call connect() first.") 
        # 2. print(f"    Calling `{tool_name}` with {tool_args}")
        print(f"    Calling `{tool_name}` with {tool_args}")
        # 3. Create `params` dictionary with:
        #       - "name": tool_name
        #       - "arguments": tool_args
        params = {
            "name": tool_name,
            "arguments": tool_args
        }
        # 4. Call `await self._send_request("tools/call", params)` and assign to `response`
        response = await self._send_request("tools/call", params)
        #       response sample:
        #       {
        #           "jsonrpc": "2.0",
        #           "id": 1,
        #           "result": {
        #               "content": [
        #                   {
        #                       "type": "text",
        #                       "text": "some tool call result"
        #                   }
        #                ]
        #           }
        #       }
        # 5. Extract content using walrus operator: `if content:= response["result"].get("content", [])`
        content = response["result"].get("content", [])
        if content:
            # 6. Extract first item using walrus operator: `if item := content[0]`
            item = content[0]
            if item:
            # 7. Extract text result: `text_result = item.get("text", "")`
                text_result = item.get("text", "")
                # 8. print(f"    ⚙️: {text_result}\n")
                print(f"    ⚙️: {text_result}\n")
                # 9. Return `text_result`
                return text_result
        # 10. If no content found, return "Unexpected error occurred!"
        return "Unexpected error occurred!"