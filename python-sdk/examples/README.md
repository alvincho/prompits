# Python SDK Examples

This directory contains example usage of the Python SDK.

## Prerequisites

Before running the examples, ensure you have the following installed:

- Python 3.x
- Any other dependencies required by the examples (e.g., listed in a `requirements.txt` file).

## Running the Examples

To run an example, navigate to this directory in your terminal and execute the desired Python script:

## Setup

### Ollama Setup

Some examples use Ollama for local LLM inference. If you want to run these examples:

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Start the Ollama service
3. Pull the required models:
   ```bash
   ollama pull granite3.2:8b
   ```



Before running any examples, you need to start an agent:
```python
cd path/to/python-sdk/examples
python3 create-agent.py --config agent1_lite.json
python3 create-agent.py --config agent2_lite.json
```

## Available Examples

### send_message

This example demonstrates how to send messages between agents and receive responses.

1. Start two agents using the provided configuration files:
   ```bash
   python3 create-agent.py --config agent1_lite.json --refresh --verbose-level INFO
   python3 create-agent.py --config agent2_lite.json --refresh --verbose-level INFO
   ```

2. Run the send_message example:
   ```bash
   cd send_message
   python3 send_message.py
   ```

See the README.md in the ./send_message directory for more detailed information on running this example.

### pathfinder

This example demonstrates how to use Pathfinder to execute a multi-step workflow (Pathway) that processes text through an LLM.

1. Start two agents using the provided configuration files:
   ```bash
   python3 create-agent.py --config agent1_lite.json --refresh --verbose-level INFO
   python3 create-agent.py --config agent2_lite.json --refresh --verbose-level INFO
   ```

2. Run the pathfinder example:
   ```bash
   cd pathfinder
   python3 pathfinder.py
   ```

The example executes a 2-step Pathway:
1. First step sends a prompt to an LLM to get an answer
2. Second step sends the output to the LLM for translation

See the README.md in the ./pathfinder directory for more detailed information on running this example.

### mcp_client

This example demonstrates how to use the Model Context Protocol (MCP) client to access files from a filesystem.

1. Start the MCP client agent:
   ```bash
   python3 create-agent.py --config mcp_client/mcp_client_agent.json --refresh --verbose-level INFO
   ```

2. The MCP client agent will start a filesystem server that provides access to the specified directory.

3. Other agents can then communicate with this agent to access files through the MCP protocol.

Note: The configuration in `mcp_client_agent.json` specifies the directory to be served. You may need to modify the path in the configuration file to match your system.

See the README.md in the ./mcp_client directory for more detailed information on running this example.

### monitor-web

This example provides a Streamlit web application that allows you to monitor running agents and send messages to them.

1. Start one or more agents using the provided configuration files:
   ```bash
   python3 create-agent.py --config agent1_lite.json --refresh --verbose-level INFO
   python3 create-agent.py --config agent2_lite.json --refresh --verbose-level INFO
   ```

2. Run the monitor-web application:
   ```bash
   cd monitor-web
   streamlit run app.py
   ```

3. The web interface will display all running agents and allow you to:
   - View agent details and status
   - Send messages to specific agents
   - Monitor agent communication

Note: Ensure you have Streamlit installed (`pip install streamlit`) before running the application.

See the README.md in the ./monitor-web directory for more detailed information on running this example.
