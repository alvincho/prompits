# Send Message Example

This example demonstrates how to send messages between agents and receive responses.

## Message Transportation

Currently, this example uses gRPC for message transportation between agents. In the future, once it's stable, the A2A (Agent-to-Agent) protocol will be used as the primary communication method between agents, providing enhanced capabilities and standardization.

## Prerequisites

- Python 3.8+
- Two agents configured and running (agent1_lite.json and agent2_lite.json)

## Running the Example

1. Start the first agent in a terminal:
   ```bash
   python3 ../create-agent.py --config ../agent1_lite.json --refresh --verbose-level INFO
   ```

2. Start the second agent in another terminal:
   ```bash
   python3 ../create-agent.py --config ../agent2_lite.json --refresh --verbose-level INFO
   ```

3. Run the send_message example:
   ```bash
   python3 send_message.py
   ```

## What This Example Does

This example demonstrates:
- How to connect to an agent using gRPC
- How to send a message from one agent to another
- How to receive and process responses

## Code Explanation

The `send_message.py` script performs the following steps:

1. Connects to Agent1 (the sender) using gRPC
2. Retrieves Agent2's information from the shared plaza
3. Composes a message to send to Agent2
4. Sends the message through Agent1's communication channel
5. Waits for and displays the response from Agent2
6. Disconnects from the agent when finished

This demonstrates the basic pattern for inter-agent communication in the Prompits framework.



