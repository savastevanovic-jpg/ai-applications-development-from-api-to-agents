from commons.constants import ANTHROPIC_API_KEY
from commons.models.conversation import Conversation
from commons.models.message import Message
from commons.models.role import Role
from commons.user_service.client import UserServiceClient

from t8_agent.task.agents.anthropic import AnthropicBasedAgent
from t8_agent.task.prompts import SYSTEM_PROMPT
from t8_agent.task.tools.users.create_user_tool import CreateUserTool
from t8_agent.task.tools.users.delete_user_tool import DeleteUserTool
from t8_agent.task.tools.users.get_user_by_id_tool import GetUserByIdTool
from t8_agent.task.tools.users.search_users_tool import SearchUsersTool
from t8_agent.task.tools.users.update_user_tool import UpdateUserTool
from t8_agent.task.tools.web_search import WebSearchTool


def main():
    #TODO:
    # 1. Create UserClient
    client = UserServiceClient()
    # 2. Create list with all tools (WebSearchTool, GetUserByIdTool, SearchUsersTool, CreateUserTool, UpdateUserTool, DeleteUserTool)
    tools = [
        WebSearchTool(anthropic_api_key=ANTHROPIC_API_KEY),
        GetUserByIdTool(user_client=client),
        SearchUsersTool(user_client=client),
        CreateUserTool(user_client=client),
        UpdateUserTool(user_client=client),
        DeleteUserTool(user_client=client)
    ]
    # 3. Create OpenAIBasedAgent with all tools (or AnthropicBasedAgent)
    agent = AnthropicBasedAgent(model="claude-haiku-4-5", api_key=ANTHROPIC_API_KEY, tools=tools, system_prompt=SYSTEM_PROMPT)
    # 4. Create Conversation
    conversation = Conversation()
    # 5. Run infinite loop and in loop and:
    #    - get user input from terminal (`input("> ").strip()`)
    #    - Add User message to Conversation
    #    - Call OpenAIClient with conversation history
    #    - Add Assistant message to Conversation and print its content
    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue
        conversation.add_message(Message(role=Role.USER, content=user_input))
        assistant_response = agent.get_response(conversation.messages)
        conversation.add_message(assistant_response)
        print(assistant_response.content)


main()
