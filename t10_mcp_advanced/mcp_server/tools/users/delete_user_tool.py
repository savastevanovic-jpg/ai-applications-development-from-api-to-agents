from typing import Any

from t10_mcp_advanced.mcp_server.tools.users.base import BaseUserServiceTool


class DeleteUserTool(BaseUserServiceTool):

    @property
    def name(self) -> str:
        #TODO: Provide tool name as `delete_users`
        return "delete_users"

    @property
    def description(self) -> str:
        #TODO: Provide description of this tool
        return "Delete a user from the User Service by their unique identifier."

    @property
    def input_schema(self) -> dict[str, Any]:
        #TODO:
        # Provide tool params Schema. This tool applies user `id` (number) as a parameter and it is required
        return {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "The unique identifier of the user to delete"}
            },
            "required": ["id"],
            "additionalProperties": False
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        #TODO:
        # 1. Get int `id` from arguments
        # 2. Call user_client delete_user and return its results
        # 3. Optional: You can wrap it with `try-except` and return error as string `f"Error while deleting user by id: {str(e)}"`
        user_id = arguments.get("id")
        try:
            await self._user_client.delete_user(user_id)
            return f"User deleted successfully: {user_id}"
        except Exception as e:
            return f"Error while deleting user by id: {str(e)}"