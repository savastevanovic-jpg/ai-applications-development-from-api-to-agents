from typing import Optional, Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult, TextContent


class StdioMCPClient:
    """Handles MCP server connection and tool execution via stdio"""

    def __init__(self, command: str, args: Optional[list[str]] = None) -> None:
        self.command = command
        self.args = args or []
        self.session: Optional[ClientSession] = None
        self._stdio_context = None
        self._session_context = None

    @classmethod
    async def create(cls, command: str, args: Optional[list[str]] = None) -> 'StdioMCPClient':
        """Async factory method to create and connect StdioMCPClient"""
        instance = cls(command, args)
        await instance.connect()
        return instance

    async def connect(self):
        """Launch the MCP server process over stdio and initialize the session"""
        server_params = StdioServerParameters(command=self.command, args=self.args)
        self._stdio_context = stdio_client(server_params)
        read_stream, write_stream = await self._stdio_context.__aenter__()

        self._session_context = ClientSession(read_stream, write_stream)
        self.session: ClientSession = await self._session_context.__aenter__()

        init_result = await self.session.initialize()
        print(init_result.model_dump_json(indent=2))

    async def get_tools(self) -> list[dict[str, Any]]:
        """Get available tools from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        tools = await self.session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in tools.tools
        ]

    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        print(f"    Calling `{tool_name}` with {tool_args}")

        tool_result: CallToolResult = await self.session.call_tool(tool_name, tool_args)

        if not tool_result.content:
            return "No content returned from tool"

        content = tool_result.content[0]
        print(f"    ⚙️: {content}\n")

        if isinstance(content, TextContent):
            return content.text

        return str(content)
