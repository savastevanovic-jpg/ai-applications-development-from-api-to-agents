from typing import Any

from commons.user_service.user_info import UserSearchRequest
from t10_mcp_advanced.mcp_server.tools.users.base import BaseUserServiceTool


class SearchUsersTool(BaseUserServiceTool):

    @property
    def name(self) -> str:
        #TODO: Provide tool name as `search_users`
        return "search_users"

    @property
    def description(self) -> str:
        #TODO: Provide description of this tool
        return """
Search for users in the User Service based on optional criteria such as name, surname, email, and gender.
        """
    
    @property
    def input_schema(self) -> dict[str, Any]:
        #TODO:
        # Provide tool params Schema:
        # - name: str
        # - surname: str
        # - email: str
        # - gender: str
        # None of them are required (see UserClient.search_users method)
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the user to search for"},
                "surname": {"type": "string", "description": "The surname of the user to search for"},
                "email": {"type": "string", "description": "The email of the user to search for"},
                "gender": {"type": "string", "description": "The gender of the user to search for"}
            },
            "required": [],
            "additionalProperties": False
        }

    async def execute(self, arguments: dict[str, Any]) -> str:
        #TODO:
        # 1. Call user_client search_users (with `**arguments`) and return its results
        # 2. Optional: You can wrap it with `try-except` and return error as string `f"Error while searching users: {str(e)}"`
        search_request = UserSearchRequest.model_validate(arguments)
        try:
            users = await self._user_client.search_users(search_request)
            return f"Users found: {users}"
        except Exception as e:
            return f"Error while searching users: {str(e)}"
