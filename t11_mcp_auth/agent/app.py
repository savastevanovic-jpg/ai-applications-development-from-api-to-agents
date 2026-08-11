import asyncio
import json

from commons.constants import ANTHROPIC_API_KEY, DEFAULT_SYSTEM_PROMPT
from commons.models.message import Message
from commons.models.role import Role
from t11_mcp_auth.agent._agent import AgentMCPAuth
from t11_mcp_auth.agent.mcp_clients.api_key_mcp_client import ApiKeyMCPClient
from t11_mcp_auth.agent.mcp_clients.oauth_mcp_client import OauthHttpMCPClient

MCP_API_KEY: str = "dev-secret-key"

async def main():
    #TODO:
    # 1. Use either `ApiKeyMCPClient(mcp_server_url="http://localhost:8007/mcp", api_key=MCP_API_KEY)`
    async with ApiKeyMCPClient(mcp_server_url="http://localhost:8007/mcp", api_key=MCP_API_KEY) as mcp_client:
        #    or `OauthHttpMCPClient(mcp_server_url="http://localhost:8008/mcp")` as an async context manager
        #    (`async with ... as mcp_client:`) — all steps below happen inside this block
        # 2. Get available tools and print each one as indented JSON
        tools = await mcp_client.get_tools()
        print(json.dumps(tools, indent=4))

        # 3. Create `AgentMCPAuth` with `api_key`, `model`, `tools`, and `mcp_client`
        agent = AgentMCPAuth(ANTHROPIC_API_KEY, "claude-haiku-4-5", tools, mcp_client)

        # 4. Create a `messages` list with a single system `Message`
        messages: list[Message] = [
            Message(role=Role.SYSTEM, content=DEFAULT_SYSTEM_PROMPT)
        ]

        # 5. Print a ready message and run an infinite loop:
        #    - Get user input; break if it equals "exit"
        #    - Append a user `Message` to `messages`
        #    - Call `await agent.get_completion(messages)` and append the returned `ai_message`
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
