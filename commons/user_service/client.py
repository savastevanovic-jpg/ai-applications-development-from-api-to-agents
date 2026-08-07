from typing import Any, Optional

import aiohttp

from commons.user_service.user_info import UserUpdate, UserCreate, UserSearchRequest

USER_SERVICE_ENDPOINT = "http://localhost:8041"


class UserServiceClient:

    def __user_to_string(self, user: dict[str, Any]):
        user_str = "```\n"
        for key, value in user.items():
            user_str += f"    {key}: {value}\n"
        user_str += "```\n"

        return user_str

    def __users_to_string(self, users: list[dict[str, Any]]):
        users_str = ""
        for value in users:
            users_str += self.__user_to_string(value)
        users_str += "\n"

        return users_str

    async def get_user_by_id(self, user_id: str) -> str:
        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json"}
            async with session.get(
                url=f"{USER_SERVICE_ENDPOINT}/v1/users/{user_id}",
                headers=headers
             ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.__user_to_string(data)
                raise Exception(f"HTTP {response.status}: {await response.text()}")

    async def search_users(self, search_request: UserSearchRequest) -> str:
        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json"}
            params = {}
            if search_request.name:
                params["name"] = search_request.name
            if search_request.surname:
                params["surname"] = search_request.surname
            if search_request.email:
                params["email"] = search_request.email
            if search_request.gender:
                params["gender"] = search_request.gender

            async with session.get(
                url=f"{USER_SERVICE_ENDPOINT}/v1/users/search",
                headers=headers,
                params=params
             ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Get {len(data)} users successfully")
                    return self.__users_to_string(data)
                raise Exception(f"HTTP {response.status}: {await response.text()}")

    async def add_user(self, user_create_model: UserCreate) -> str:
        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json"}
            async with session.post(
                url=f"{USER_SERVICE_ENDPOINT}/v1/users",
                headers=headers,
                json=user_create_model.model_dump()
             ) as response:
                if response.status == 201:
                    return f"User successfully added: {await response.text()}"
                raise Exception(f"HTTP {response.status}: {await response.text()}")

    async def update_user(self, user_id: str, user_update_model: UserUpdate) -> str:
        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json"}
            async with session.put(
                url=f"{USER_SERVICE_ENDPOINT}/v1/users/{user_id}",
                headers=headers,
                json=user_update_model.model_dump()
             ) as response:
                if response.status == 200:
                    return f"User successfully updated: {await response.text()}"
                raise Exception(f"HTTP {response.status}: {await response.text()}")

    async def delete_user(self, user_id: str) -> str:
        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json"}
            async with session.delete(
                url=f"{USER_SERVICE_ENDPOINT}/v1/users/{user_id}",
                headers=headers
             ) as response:
                if response.status == 204:
                    return "User successfully deleted"
                raise Exception(f"HTTP {response.status}: {await response.text()}")
