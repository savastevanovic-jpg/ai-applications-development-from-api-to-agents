from typing import Any

from anthropic import AsyncAnthropic

from commons.models.message import Message
from commons.models.role import Role
from t10_mcp_advanced.agent.clients.custom_mcp_client import CustomMCPClient
from t10_mcp_advanced.agent.clients.mcp_client import MCPClient
from t10_mcp_advanced.agent.clients.stdio_mcp_client import StdioMCPClient


class CustomAgentMCP:
    """Handles AI model interactions and integrates with MCP client"""

    def __init__(
            self,
            api_key: str,
            model: str,
            tools: list[dict[str, Any]],
            tool_name_client_map: dict[str, MCPClient | CustomMCPClient | StdioMCPClient]
    ):
        self.model = model
        self.tools = self._to_anthropic_tools(tools)
        self.tool_name_client_map = tool_name_client_map
        self.anthropic = AsyncAnthropic(api_key=api_key)

    @staticmethod
    def _to_anthropic_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert the OpenAI-style function schemas returned by the MCP clients into Anthropic's tool shape"""
        return [
            {
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"],
            }
            for tool in tools
        ]

    @staticmethod
    def _to_anthropic_message(message: Message) -> dict[str, Any]:
        """Convert a generic Message into Anthropic's expected request shape"""
        if message.tool_call_id:
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": message.tool_call_id,
                        "content": message.content,
                    }
                ],
            }
        if message.role == Role.ASSISTANT and message.tool_calls:
            content = [{"type": "text", "text": message.content}] if message.content else []
            content += message.tool_calls
            return {"role": Role.ASSISTANT.value, "content": content}
        return message.to_dict()

    def _collect_tool_calls(self, content_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract tool_use blocks from the assembled streaming content"""
        return [block for block in content_blocks if block["type"] == "tool_use"]

    async def _stream_response(self, messages: list[Message]) -> Message:
        """Stream Anthropic response and handle tool calls"""
        system_prompt = next((msg.content for msg in messages if msg.role == Role.SYSTEM), "")
        conversation = [msg for msg in messages if msg.role != Role.SYSTEM]

        async with self.anthropic.messages.stream(
            model=self.model,
            max_tokens=1024,
            messages=[self._to_anthropic_message(msg) for msg in conversation],
            tools=self.tools,
            temperature=0.0,
            system=system_prompt,
        ) as stream:

            print("🤖: ", end="", flush=True)

            async for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "text_delta":
                    print(event.delta.text, end="", flush=True)

            print()
            final_message = await stream.get_final_message()

        content_blocks = [block.model_dump() for block in final_message.content]
        text_content = "".join(block["text"] for block in content_blocks if block["type"] == "text")
        tool_calls = self._collect_tool_calls(content_blocks)

        return Message(
            role=Role.ASSISTANT,
            content=text_content,
            tool_calls=tool_calls if tool_calls else [],
        )

    async def get_completion(self, messages: list[Message]) -> Message:
        """Process user query with streaming and tool calling"""
        ai_message: Message = await self._stream_response(messages)

        # Check if any tool calls are present and perform them
        if ai_message.tool_calls:
            messages.append(ai_message)
            await self._call_tools(ai_message, messages)
            # recursively calling agent with tool messages
            return await self.get_completion(messages)

        return ai_message

    async def _call_tools(self, ai_message: Message, messages: list[Message]):
        """Execute tool calls using MCP client"""
        for tool_call in ai_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["input"] if tool_call["input"] else {}

            try:
                client = self.tool_name_client_map.get(tool_name)
                if not client:
                    raise Exception(f"Unable to call {tool_name}. MCP client not found.")

                tool_result = await client.call_tool(tool_name, tool_args)

                # Add tool result to history
                messages.append(
                    Message(
                        role=Role.USER,
                        content=str(tool_result),
                        tool_call_id=tool_call["id"],
                    )
                )
            except Exception as e:
                error_msg = f"Error: {e}"
                print(f"Error: {error_msg}")
                messages.append(
                    Message(
                        role=Role.USER,
                        content=error_msg,
                        tool_call_id=tool_call["id"],
                    )
                )
