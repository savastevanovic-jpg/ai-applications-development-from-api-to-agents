from typing import Any

from t10_mcp_advanced.mcp_server.tools.users.base import BaseUserServiceTool


class GetUserByIdTool(BaseUserServiceTool):

    @property
    def name(self) -> str:
        #TODO: Provide tool name as `get_user_by_id`
        return "get_user_by_id"

    @property
    def description(self) -> str:
        #TODO: Provide description of this tool
        return "Retrieve a user by their unique identifier."

    @property
    def input_schema(self) -> dict[str, Any]:
        #TODO:
        # Provide tool params Schema. This tool applies user `id` (number) as a parameter and it is required
        return {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "The unique identifier of the user to retrieve"}
            },
            "required": ["id"],
            "additionalProperties": False
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        #TODO:
        # 1. Get int `id` from arguments
        # 2. Call user_client get_user and return its results
        # 3. Optional: You can wrap it with `try-except` and return error as string `f"Error while retrieving user by id: {str(e)}"`
        user_id = arguments.get("id")
        try:
            user = await self._user_client.get_user_by_id(user_id)
            return f"User retrieved successfully: {user}"
        except Exception as e:
            return f"Error while retrieving user by id: {str(e)}"