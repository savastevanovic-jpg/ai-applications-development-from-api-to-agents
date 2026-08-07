import os
import sys
import asyncio
import json
from pathlib import Path

from mcp import Resource
from mcp.types import Prompt

from commons.constants import ANTHROPIC_API_KEY
from commons.models.message import Message
from commons.models.role import Role
from t9_mcp_fundamentals.agent.agent import AgentMCPFundamentals
from t9_mcp_fundamentals.agent.mcp_clients.http import HttpMCPClient
from t9_mcp_fundamentals.agent.mcp_clients.stdio import StdioMCPClient
from t9_mcp_fundamentals.agent.prompts import SYSTEM_PROMPT


async def main():
    #TODO:
    # 1. Create `HttpMCPClient(mcp_server_url="http://localhost:8005/mcp")` as an async context manager
    #    (`async with ... as mcp_client:`) — all steps below happen inside this block
    async with HttpMCPClient(mcp_server_url="http://localhost:8005/mcp") as mcp_client:
    # 2. Print Available Resources
        mcp_resources = await mcp_client.get_resources()
        print("Available Resources:")
        for resource in mcp_resources:
            print(f"- {resource.name} (Description: {resource.description})")
        # 3. Print Available Tools
        mcp_tools = await mcp_client.get_tools()
        print("Available Tools:")
        for tool in mcp_tools:
            print(f"- {tool['name']}: {tool['description']}")
        # 4. Create `AgentMCPFundamentals`
        antropic_agent = AgentMCPFundamentals(
            api_key=ANTHROPIC_API_KEY,
            model="claude-haiku-4-5",
            tools=mcp_tools,
            mcp_client=mcp_client,
        )
        # 5. Create `messages` list with a single system prompt
        messages = []
        # 6. Print Available Prompts
        mcp_prompts = await mcp_client.get_prompts()
        print("Available Prompts:")
        for prompt in mcp_prompts:
            print(f"- {prompt.name}: {prompt.description}")
        # 7. Run an infinite loop:
        #     - get user input with `input("\n> ").strip()`
        #     - if user_input.lower() == 'exit': break
        #     - append Message(role=Role.USER, content=user_input) to `messages`
        #     - call `await agent.get_response(messages)` and append the returned `ai_message` to `messages`
        while True:
            user_input = input("\n> ").strip()
            if user_input.lower() == 'exit':
                break
            messages.append(Message(role=Role.USER, content=user_input))
            ai_message = await antropic_agent.get_response(messages)
            messages.append(ai_message)


if __name__ == "__main__":
    asyncio.run(main())
