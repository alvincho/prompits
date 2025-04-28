# MCP Client Example

This example demonstrates how to use the MCP (Mission Control Protocol) client to interact with agents and pathways.

## Prerequisites

- Python 3.8 or higher
- Prompits SDK installed
- Running agents with gRPC plugs configured

## Setup

1. Create or modify your MCP client agent configuration file (mcp_client_agent.json). The example is a filesystem server, change the path:
   ```json
   {
       "services": {
         "mcp_client": {
           "type": "MCPClient",
           "name": "mcp_client",
           "description": "MCP client for communication",
           "mcp_server_params": {
             "filesystem": {
               "command": "npx",
               "args": [
                 "-y",
                 "@modelcontextprotocol/server-filesystem",
                 "/path/to/your/documents"
               ]
             }
           }
         }
   }
   ```

2. Start the MCP client agent:

   ```bash
   python3 ../create-agent.py --config mcp_client_agent.json --refresh --verbose-level INFO
   ```
3. Modify the mcp_client.py
```python
    # Create MCPClient
    arguments = {"tool_name":"list_directory","arguments":{"path":"/Users/alvincho/Downloads/temp"}}
    result = agent.UsePracticeRemote("filesystem/list_directory","MCPClientAgent@MainPlaza",arguments )
    print(f"\nResult: {result}")
    content=json.loads(result[0]["content"])
    files = content["body"]["result"]["content"][0]
    print(f"File: {files["text"]}")
```
- change tool name **list_directory** to your tool_name
- change practice name **filesystem/list_directory** to your server_name/tool_name
## Running the Example

To run the MCP client example:
```python
python3 mcp_client.py
```