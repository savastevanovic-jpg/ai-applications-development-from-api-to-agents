import json
from typing import Any

import requests

from commons.constants import ANTHROPIC_ENDPOINT
from commons.models.message import Message
from commons.models.role import Role
from t8_agent.task.agents._base import BaseAgent
from t8_agent.task.tools.base import BaseTool


class AnthropicBasedAgent(BaseAgent):

    def __init__(self, model: str, api_key: str, tools: list[BaseTool] | None = None, system_prompt: str | None = None):
        super().__init__(model, api_key, tools, system_prompt)
        #TODO:
        # 1. Set `self._api_key` as-is (Anthropic uses raw key in `x-api-key` header, no "Bearer" prefix)
        self._api_key = api_key
        # 2. Build `self._tools_schemas` using `tool.anthropic_schema` for each tool in `tools`
        self._tools_schemas = [tool.anthropic_schema for tool in tools] if tools else []
        # 3. Set `self._endpoint` to `ANTHROPIC_MESSAGES_ENDPOINT`
        self._endpoint = ANTHROPIC_ENDPOINT
        # 4. Print `self._endpoint` and `self._tools_schemas` (use json.dumps with indent=4)
        print(json.dumps(self._endpoint, indent=4))
        print(json.dumps(self._tools_schemas, indent=4))

    def get_response(self, messages: list[Message], print_request: bool = True) -> Message:
        #TODO:
        # 1. Build `request_messages` from `messages` as-is — Anthropic does NOT accept a
        #    "system" role inside messages; `self._system_prompt` (if set) must be passed
        #    separately as a top-level `system` field in request_data, not prepended to messages
        # 2. Build headers: `x-api-key: self._api_key`, `anthropic-version: "2023-06-01"`,
        #    `Content-Type: application/json`
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        # 3. Build request_data with `model`, `max_tokens`, serialized `request_messages` (.to_dict()),
        #    `tools`, and `system` (if `self._system_prompt` is set)
        request_data = {
            "model": self._model,
            "max_tokens": 1000,
            "messages": [self._to_request_message(message) for message in messages],
            "tools": self._tools_schemas,
            "system": self._system_prompt if self._system_prompt else None
        }
        # 4. If `print_request` — print `self._endpoint` and the REQUEST payload
        if print_request:
            print(json.dumps(self._endpoint, indent=4))
            print(json.dumps(request_data, indent=4))
        # 5. POST to `self._endpoint` with headers and json body
        response = requests.post(self._endpoint, headers=headers, json=request_data)
        # 6. On HTTP 200:
        #    a. Parse response JSON, print RESPONSE
        #    b. Extract `content` (list of blocks) and `stop_reason` from the response
        #    c. Separate `content` blocks into text (type == "text") and tool_use (type == "tool_use") blocks
        #    d. Build `ai_response` as Message(role=Role.ASSISTANT, content=..., tool_calls=...)
        #    e. If `stop_reason == "tool_use"`:
        #       - Append `ai_response` to `messages`
        #       - Call `_process_tool_calls(tool_calls)` and extend `messages` with the result
        #       - Recurse: return `self.get_response(messages, print_request)`
        #    f. Otherwise return `ai_response`
        if response.status_code == 200:
            response_json = response.json()
            if print_request:
                print(json.dumps(response_json, indent=4))
            content = response_json.get("content", [])
            stop_reason = response_json.get("stop_reason", "")
            tool_use_blocks = [block for block in content if block.get("type") == "tool_use"]
            ai_response = Message(role=Role.ASSISTANT, content=content, tool_calls=tool_use_blocks)
            if stop_reason == "tool_use":
                messages.append(ai_response)
                tool_messages = self._process_tool_calls(tool_use_blocks)
                messages.extend(tool_messages)
                return self.get_response(messages, print_request)
            return ai_response
        # 7. On error — raise Exception with status code and response text
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")

    @staticmethod
    def _to_request_message(message: Message) -> dict[str, Any]:
        if message.role == Role.TOOL:
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
            return {"role": Role.ASSISTANT.value, "content": message.content}
        return message.to_dict()

    def _process_tool_calls(self, tool_calls: list[dict[str, Any]]) -> list[Message]:
        #TODO:
        # For each tool_call in tool_calls:
        # 1. Extract `tool_call_id` from tool_call["id"]
        # 2. Extract `function_name` from tool_call["name"]
        # 3. Extract `arguments` from tool_call["input"] (already a parsed dict, no json.loads needed)
        # 4. Call `_call_tool(function_name, arguments)` and store the result
        # 5. Append Message(role=Role.TOOL, name=function_name, tool_call_id=..., content=result)
        # 6. Print the function name and result
        # Return the list of tool messages
        tool_messages: list[Message] = []
        for tool_call in tool_calls:
            tool_call_id = tool_call.get("id")
            function_name = tool_call.get("name")
            arguments = tool_call.get("input", {})
            result = self._call_tool(function_name, arguments)
            tool_message = Message(role=Role.TOOL, name=function_name, tool_call_id=tool_call_id, content=result)
            print(f"Tool called: {function_name}, Result: {result}")
            tool_messages.append(tool_message)
        return tool_messages

    def _call_tool(self, function_name: str, arguments: dict[str, Any]) -> str:
        #TODO:
        # 1. Look up the tool by `function_name` in `self._tools_dict`
        tool = self._tools_dict.get(function_name)
        # 2. If found — call `tool.execute(arguments)` and return the result
        if tool:
            return tool.execute(arguments)
        # 3. If not found — return `f"Unknown function: {function_name}"`
        return f"Unknown function: {function_name}"