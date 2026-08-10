import asyncio
import json
import os

from commons.constants import ANTHROPIC_API_KEY
from commons.models.message import Message
from commons.models.role import Role
from t10_mcp_advanced.agent.agent import CustomAgentMCP
from t10_mcp_advanced.agent.clients.custom_mcp_client import CustomMCPClient
from t10_mcp_advanced.agent.clients.mcp_client import MCPClient
from t10_mcp_advanced.agent.clients.stdio_mcp_client import StdioMCPClient


async def main():
    #TODO:
    # 1. Take a look what applies CustomAgentMCP
    # 2. Create empty list where you save tools from MCP Servers later
    tools = []
    # 3. Create empty dict where where key is str (tool name) and value is instance of MCPClient or CustomMCPClient
    tool_map: dict[str, MCPClient | CustomMCPClient | StdioMCPClient] = {}
    # 4. Create UMS MCPClient, url is `http://localhost:8006/mcp` (use static method create and don't forget that its async)
    ums_client = await MCPClient.create("http://localhost:8006/mcp")
    # 5. Collect tools and dict [tool name, mcp client]
    ums_tools = await ums_client.get_tools()
    tools.extend(ums_tools)
    for tool in ums_tools:
        tool_map[tool["function"]["name"]] = ums_client
    # 6. Do steps 4 and 5 for `https://remote.mcpservers.org/fetch/mcp`
    fetch_client = await StdioMCPClient.create("mcp-server-fetch")
    fetch_tools = await fetch_client.get_tools()
    tools.extend(fetch_tools)
    for tool in fetch_tools:
        tool_map[tool["function"]["name"]] = fetch_client
    # 7. Create CustomAgentMCP
    agent = CustomAgentMCP(ANTHROPIC_API_KEY, "claude-haiku-4-5", tools, tool_map)
    # 8. Create array with Messages and add there System message with simple instructions for LLM that it should help to handle user request
    # 9. Create simple console chat (as we done in previous tasks)
    messages: list[Message] = [
        Message(
            role=Role.SYSTEM,
            content="You are a helpful assistant. Use the available tools to help the user "
                    "accomplish their requests. Be concise and clear in your responses.",
        )
    ]

    # 9. Create simple console chat
    print("Chat started. Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        messages.append(Message(role=Role.USER, content=user_input))

        ai_message = await agent.get_completion(messages)
        messages.append(ai_message)



if __name__ == "__main__":
    asyncio.run(main())


# Check if Arkadiy Dobkin present as a user, if not then search info about him in the web and add him