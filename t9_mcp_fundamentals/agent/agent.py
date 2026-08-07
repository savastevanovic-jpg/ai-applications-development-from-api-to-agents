import json
from typing import Any

from anthropic import AsyncAnthropic

from commons.models.message import Message
from commons.models.role import Role
from t9_mcp_fundamentals.agent.mcp_clients.base import MCPClient
from t9_mcp_fundamentals.agent.prompts import SYSTEM_PROMPT


class AgentMCPFundamentals:
    """Handles AI model interactions and integrates with MCP client"""

    def __init__(self, api_key: str, model: str, tools: list[dict[str, Any]], mcp_client: MCPClient):
        self.model = model
        self.tools = tools
        self.mcp_client = mcp_client
        self.anthropic = AsyncAnthropic(api_key=api_key)

    def _collect_tool_calls(self, content_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract tool_use blocks from the assembled streaming content"""
        return [block for block in content_blocks if block["type"] == "tool_use"]

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

    async def _stream_response(self, messages: list[Message]) -> Message:
        """Stream Anthropic response and handle tool calls"""
        async with self.anthropic.messages.stream(
            model=self.model,
            max_tokens=1024,
            messages=[self._to_anthropic_message(msg) for msg in messages],
            tools=self.tools,
            temperature=0.0,
            system=SYSTEM_PROMPT,
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

    async def get_response(self, messages: list[Message]) -> Message:
        """Process user query with streaming and tool calling"""
        ai_message: Message = await self._stream_response(messages)

        if ai_message.tool_calls:
            # Keep tool_calls on the appended message: Anthropic requires each tool_result
            # to reference a tool_use block from the preceding assistant turn.
            messages.append(ai_message)
            await self._call_tools(ai_message, messages)
            return await self.get_response(messages)

        return ai_message

    async def _call_tools(self, ai_message: Message, messages: list[Message]):
        """Execute tool calls using MCP client"""
        #TODO:
        # 1. Iterate through tool_calls
        # 2. Get tool name and tool arguments (arguments is already a parsed dict in Anthropic's
        #    tool_use blocks — accessible via tool_call["input"], no json.loads needed)
        # 3. Wrap into try/except block and call mcp_client tool call. If succeed then add tool message (don't forget
        #    about tool call id), otherwise add tool message with error message (it kind of fallback strategy).
        for tool_call in ai_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["input"] if tool_call["input"] else {}

            try:
                result = await self.mcp_client.call_tool(tool_name, tool_args)
                messages.append(Message(role=Role.USER, content=result, tool_call_id=tool_call["id"]))
            except Exception as e:
                error_message = f"Error calling tool '{tool_name}': {str(e)}"
                messages.append(Message(role=Role.USER, content=error_message, tool_call_id=tool_call["id"]))