# Getting Started with Prompits Python SDK
 
 This folder contains a minimal example to help you get started with the Prompits Python SDK.
 
 ## Overview
 
 You will find two agent configuration files in this folder:
 
 - `agent1_lite.json`
 - `agent2_lite.json`
 
 These agents are configured to use a shared SQLite database `test_lite.db` as the **Plaza Pool** for inter-agent communication and storage.
 
 ## Prerequisites
 
 - Python 3.8+
 - Install required dependencies (if any) via pip:
   ```bash
   pip install -r requirements.txt
   ```
 
 ## Starting an Agent
 
 Use the following command to start an agent:
 
 ```bash
 python ../src/create-agent.py --config agent1_lite.py --refresh
 ```
 
 To list all the practices available in an agent, you can run:

 ```bash
 python ../src/create-agent.py --config agent1_lite.json --list-practices
 ```

 You can also start agents using JSON configuration files. For example:

 ```bash
 python ../src/create-agent.py --config agent1_lite.json --refresh --verbose-level INFO 
 ```

 Start 2 agents in two separate terminals(command prompts) to see both online

 ```bash
 python ../src/create-agent.py --config agent1_lite.json --refresh --verbose-level INFO 

 python ../src/create-agent.py --config agent2_lite.json --refresh --verbose-level INFO 
 ```

 This will display the agent-level and pit-level practices registered in the system.

 Once both agents are running, they will register themselves in the shared `test_lite.db`, and you will be able to see that the two agents recognize and can communicate with each other through the Plaza Pool.
 
 ## Notes
 
 - The `--refresh` flag will reset the agent's state.
 - Setting the `--verbose-level INFO` can display more information, including active agents.
 - Make sure `test_lite.db` exists or will be created in the correct location for the agents to interact through the Plaza Pool.
 
 ## Next Steps
 
 After launching the agents, you can begin testing inter-agent communication and Pathway execution as outlined in the broader Prompits system.