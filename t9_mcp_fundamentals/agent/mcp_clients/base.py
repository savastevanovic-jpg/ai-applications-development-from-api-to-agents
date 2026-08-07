from abc import abstractmethod, ABC
from typing import Optional, Any

from mcp import ClientSession
from mcp.types import CallToolResult, TextContent, GetPromptResult, ReadResourceResult, Resource, TextResourceContents, BlobResourceContents, Prompt, ListResourcesResult, ListToolsResult, ListPromptsResult
from pydantic import AnyUrl


class MCPClient(ABC):

    def __init__(self) -> None:
        self.session: Optional[ClientSession] = None

    @abstractmethod
    async def __aenter__(self):
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ...

    async def get_tools(self) -> list[dict[str, Any]]:
        """Get available tools from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")
        #TODO:
        # 1. Call `await self.session.list_tools()` and assign to `tools`
        tools: ListToolsResult = await self.session.list_tools()
        # 2. Return list with dicts with tool schemas. It should be provided according to OpenAI specification
        # https://developers.openai.com/api/docs/guides/function-calling
         # 3. Transform MCP tool format to Anthropic format (inputSchema -> input_schema)
        result = []
        for tool in tools.tools:
            tool_dict = tool.model_dump()
            # MCP uses camelCase 'inputSchema', Anthropic expects snake_case 'input_schema'
            if 'inputSchema' in tool_dict:
                tool_dict['input_schema'] = tool_dict.pop('inputSchema')
            tool_dict = {x[0]: x[1] for x in tool_dict.items() if x[0] in ["name", "description", "input_schema"]}  # Remove None values
            result.append(tool_dict)
        return result
    
    async def call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """Call a specific tool on the MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected. Call connect() first.")

        #TODO:
        # 1. Call `await self.session.call_tool(tool_name, tool_args)` and assign to `tool_result: CallToolResult` variable
        tool_result: CallToolResult = await self.session.call_tool(tool_name, tool_args)
         # 2. Get `content` with index `0` from `tool_result` and assign to `content` variable
        content = tool_result.content[0]
         # 3. print(f"    ⚙️: {content}\n")
        print(f"    ⚙️: {content}\n")
         # 4. If `isinstance(content, TextContent)` -> return content.text
         #    else -> return content
        if isinstance(content, TextContent):
            return content.text
        else:
            return content

    async def get_resources(self) -> list[Resource]:
        """Get available resources from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        #TODO:
        # Wrap into try/except (not all MCP servers have resources), get `list_resources` (it is async) and resources
        # from it. In case of error print error and return an empty array
        try:
            resources: ListResourcesResult = await self.session.list_resources()
            return resources.resources
        except Exception as e:
            print(f"Error fetching resources: {e}")
            return []

    async def get_resource(self, uri: AnyUrl) -> str:
        """Get specific resource content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")

        #TODO:
        # 1. Get resource by uri (uri is that we provided on the Server side "users-management://flow-diagram")
        resource = await self.session.get_resource(uri)
        # 2. Get contents of [0] resource
        content = resource[0].contents
        # 3. ResourceContents has 2 types TextResourceContents and BlobResourceContents, in case if content is instance
        #    of TextResourceContents return it is `text`, in case of BlobResourceContents return it is `blob`
        # ---
        if isinstance(content, TextResourceContents):
            return content.text
        elif isinstance(content, BlobResourceContents):
            return content.blob
        else:
            raise ValueError("Unknown resource content type.")
        # Optional: Later on in app.py you can try to fetch resource and print it (in our case it is image/png provided
        # as bytes, but you can return on the server side some dict just to check how resources are looks like).

    async def get_prompts(self) -> list[Prompt]:
        """Get available prompts from MCP server"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        #TODO:
        # Wrap into try/except (not all MCP servers have prompts), get `list_prompts` (it is async) and prompts
        # from it. In case of error print error and return an empty array
        try:
            prompts: ListPromptsResult = await self.session.list_prompts()
            return prompts.prompts
        except Exception as e:
            print(f"Error fetching prompts: {e}")
            return []

    async def get_prompt(self, name: str) -> str:
        """Get specific prompt content"""
        if not self.session:
            raise RuntimeError("MCP client not connected.")
        #TODO:
        # 1. Get prompt by name
        prompt_result: GetPromptResult = await self.session.get_prompt(name)
        # 2. Create variable `combined_content` with empty string
        combined_content = ""
        # 3. Iterate through prompt result `messages` and:
        #       - if `message` has attribute 'content' and is instance of TextContent then concat `combined_content`
        #          with `message.content.text + "\n"`
        #       - if `message` has attribute 'content' and is instance of `str` then concat `combined_content` with
        #          with `message.content + "\n"`
        for message in prompt_result.messages:
            if hasattr(message, 'content'):
                if isinstance(message.content, TextContent):
                    combined_content += message.content.text + "\n"
                elif isinstance(message.content, str):
                    combined_content += message.content + "\n"
        # 4. Return `combined_content`
        return combined_content