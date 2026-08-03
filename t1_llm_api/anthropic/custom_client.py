import json
import aiohttp
import requests

from commons.models.message import Message
from commons.models.role import Role
from t1_llm_api.base_client import AIClient


class CustomAnthropicAIClient(AIClient):
    """
    Custom HTTP client for Anthropic's Claude API.

    This implementation uses raw HTTP requests (requests/aiohttp) instead of
    the official SDK, demonstrating how to interact with Claude's API directly
    and handle its Server-Sent Events (SSE) streaming format.
    """

    def response(self, messages: list[Message], **kwargs) -> Message:
        """
        Get a synchronous response using raw HTTP POST request.

        Args:
            messages (list[Message]): The conversation history.
            **kwargs: Additional parameters like max_tokens (default: 1024).

        Returns:
            Message: The AI's response message.

        Raises:
            ValueError: If the API response contains no content blocks.
            Exception: If the HTTP request fails (non-200 status code).

        Note:
            Requires 'x-api-key' header and 'anthropic-version' header.
            Claude's API returns content as an array of content blocks.
            The response is printed to stdout before being returned.
        """
        #TODO:
        # https://docs.anthropic.com/en/api/messages-examples
        # - Prepare headers with api key, anthropic version and content type
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        # - Add System prompt
        if "max_tokens" not in kwargs:
            kwargs["max_tokens"] = 1024
        payload = {
            "model": self._model_name,
            "messages": [{"role": msg.role.value, "content": msg.content} for msg in messages],
            "system": self._system_prompt,
            **kwargs
        }
        # - Execute post request to AI API (use `requests`)
        response = requests.post(
            self._endpoint,
            headers=headers,
            data=json.dumps(payload)
        )
        # - Parse response
        if response.status_code != 200:
            raise Exception(f"Request failed with status code {response.status_code}: {response.text}")
        response_data = response.json()
        content_blocks = response_data.get("content", [])
        if not content_blocks:
            raise ValueError("No content blocks found in the response.")
        # - Concatenate content blocks into a single string
        full_response = "".join(block.get("text", "") for block in content_blocks)
        # - Print response to console
        print(full_response)
        # - Return ASSISTANT message
        return Message(role=Role.ASSISTANT, content=full_response)

    async def stream_response(self, messages: list[Message], **kwargs) -> Message:
        """
        Get a streaming response using raw HTTP with Server-Sent Events (SSE).

        The response is streamed using Anthropic's SSE format, with text deltas
        printed immediately as they arrive.

        Args:
            messages (list[Message]): The conversation history.
            **kwargs: Additional parameters like max_tokens (default: 1024).

        Returns:
            Message: The complete AI response message after all deltas are received.

        Note:
            Uses Server-Sent Events (SSE) format where each line starts with "data: ".
            Listens for 'content_block_delta' events with 'text_delta' type.
            Stops processing when 'message_stop' event is received.
            Each delta is printed to stdout as it arrives.
        """
        #TODO:
        # https://docs.anthropic.com/en/docs/build-with-claude/streaming
        # - Prepare headers with api key, anthropic version and content type
        # - Add System prompt
        # - Execute post request to AI API (use `aihttp`)
        # - Handle stream with chunks
        # - Parse response
        # - Print chunks to console
        # - Return ASSISTANT message
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        if "max_tokens" not in kwargs:
            kwargs["max_tokens"] = 1024
        payload = {
            "model": self._model_name,
            "messages": [{"role": msg.role.value, "content": msg.content} for msg in messages],
            "system": self._system_prompt,
            "stream": True,
            **kwargs
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._endpoint,
                headers=headers,
                data=json.dumps(payload)
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Request failed with status code {resp.status}: {await resp.text()}")
                full_response = ""
                async for line in resp.content:
                    decoded_line = line.decode('utf-8').strip()
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[len("data: "):]
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            event_type = data_json.get("type")
                            if event_type == "content_block_delta":
                                text_delta = data_json.get("delta", {}).get("text", "")
                                full_response += text_delta
                                print(text_delta, end="", flush=True)
                            elif event_type == "message_stop":
                                break
                        except json.JSONDecodeError:
                            continue
                print()  # Newline after streaming is done
                return Message(role=Role.ASSISTANT, content=full_response)

