# MCPClient is a Pit
# MCPClient is a service that gets tools information from the Anthropic Model Content Protocol service
# and creates practices for the agent

from prompits.Pit import Pit
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio

from prompits.Practice import Practice


class MCPClient(Pit):
    """
    MCPClient is a Pit that gets tools information from the Anthropic Model Content Protocol service
    and creates practices for the agent

    The CallTool practice is not implemented correctly yet and can't be used in a pathway.
    """
    def __init__(self, name, description, mcp_server_params: dict):
        super().__init__(name, description)
        self.json_data = mcp_server_params
        if isinstance(mcp_server_params, dict):
            self.mcp_server_params = StdioServerParameters(**mcp_server_params)
        else:
            self.mcp_server_params = mcp_server_params
        print(f"MCPClient init: {self.mcp_server_params}")
        self.tools= asyncio.run(self._GetTools())
        self.AddPractice(Practice("GetTools", self._GetTools, 
                                  description="Get tools from the MCP server", 
                                  is_async=True))
        for tool in self.tools:
            print(f"tool: {tool.name}")
            print(f"tool.inputSchema: {tool.inputSchema}")
            self.AddPractice(Practice(tool.name, 
                                      function= self._CallTool, input_schema=tool.inputSchema, 
                                      description=tool.description, parameters={"tool_name":tool.name},
                                      is_async=True))
        #print(self.practices)
        #self.mcp_client = ClientSession(mcp_server_params)

    # Optional: create a sampling callback
    async def handle_sampling_message(
        message: types.CreateMessageRequestParams,
    ) -> types.CreateMessageResult:
        result= types.CreateMessageResult(
            role="assistant",
            content=types.TextContent(
                type="text",
                text="Hello, world! from model",
            ),
            model="gpt-3.5-turbo",
            stopReason="endTurn",
        )
        self.log(f"handle_sampling_message: {result}", 'DEBUG')
        return result
    
    async def _CallTool(self, tool_name:str, arguments:dict):
        """
        Call a tool using the MCP client

        Args:
            tool_name (str): The name of the tool to call
            arguments (dict): The arguments to pass to the tool

        Returns:
            dict: The result of the tool call
        """
        async with stdio_client(self.mcp_server_params) as (read, write):
            async with ClientSession(
                read, write, sampling_callback=self.handle_sampling_message
            ) as session:
                # Initialize the connection
                await session.initialize()

                return await session.call_tool(tool_name, arguments)
    
    async def _GetTools(self):
        """
        Get tools from the MCP server

        Returns:
            list: The tools from the MCP server
        """
        async with stdio_client(self.mcp_server_params) as (read, write):
            async with ClientSession(
                read, write, sampling_callback=self.handle_sampling_message
            ) as session:
                # Initialize the connection
                await session.initialize()

                # # List available prompts
                # prompts = await session.list_prompts()

                # # Get a prompt
                # prompt = await session.get_prompt(
                #     "example-prompt", arguments={"arg1": "value"}
                # )

                # List available resources
                # resources = await session.list_resources()

                # List available tools
                tools = await session.list_tools()
                for key, value in tools:
                    if key == "tools":
                        return value
                return []
            
                # # Read a resource
                # content, mime_type = await session.read_resource("file://some/path")

                # # Call a tool
                # result = await session.call_tool("tool-name", arguments={"arg1": "value"})

    def FromJson(self, json_data):
        """
        Initialize the MCP client from a JSON object

        Args:
            json_data (dict): The JSON object to initialize the MCP client from
        """
        self.mcp_server_params = StdioServerParameters(**json_data)
        self.json_data = json_data
        self.mcp_client = ClientSession(self.mcp_server_params)

    def ToJson(self):
        """
        Convert the MCP client to a JSON object

        Returns:
            dict: The JSON object to convert the MCP client to
        """
        return self.json_data
