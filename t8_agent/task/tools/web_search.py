from typing import Any

from typing import Any

import requests

from commons.constants import ANTHROPIC_ENDPOINT
from t8_agent.task.tools.base import BaseTool


class WebSearchTool(BaseTool):

    def __init__(self, anthropic_api_key: str):
        self.__api_key = anthropic_api_key
        self.__endpoint = ANTHROPIC_ENDPOINT

    @property
    def name(self) -> str:
        #TODO: Provide tool name as `web_search_tool`
        return "web_search_tool"

    @property
    def description(self) -> str:
        #TODO: Provide description of this tool
        return "A tool that performs web search using the Anthropic API. It takes a search query as input and returns relevant search results."

    @property
    def input_schema(self) -> dict[str, Any]:
        #TODO: Provide tool params Schema (it applies `request` string to search by)
        return {
            "type": "object",
            "properties": {
                "request": {
                    "type": "string",
                    "description": "The search query to be used for web search."
                }
            },
            "required": ["request"],
            "additionalProperties": False
        }

    def execute(self, arguments: dict[str, Any]) -> str:
        #TODO:
        # https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool
        # 1. Make POST call to `claude-3-haiku-20240307` (Anthropic's smallest model) with
        #    headers: `x-api-key: self.__api_key`, `anthropic-version: "2023-06-01"`,
        #    `Content-Type: application/json`
        response = requests.post(
            url=self.__endpoint,
            headers={
                "x-api-key": self.__api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-haiku-4-5",
                "tools": [
                    {
                        "type": "web_search_20250305",
                        "name": "web_search"
                    }
                ],
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": arguments["request"]
                    }
                ]
            }
        )

        # 2. Request body should include "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        #    "max_tokens", and "messages" built from `arguments["request"]`
        # 3. Check if response status is 200 and if yes then return message content, otherwise return
        #    `f"Error: {response.status_code} {response.text}"`
        if response.status_code == 200:
            return response.json().get("content", [])
        else:
            raise NotImplementedError()