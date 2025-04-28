# `test_pathfinder.py`

This script demonstrates and tests how the **Pathfinder** component operates in the **Prompits** system.

## 🧠 Overview

In Prompits, an **Agent** has capabilities, called **Practices**, which it advertises on a shared communication space called the **Plaza**.

In the Prompits Multi-Agent System (MAS), agents are autonomous and not guaranteed to be online or available at all times. The Pathfinder must operate dynamically, discovering available agents at runtime based on the **Practice** they advertise. This allows the system to be fault-tolerant and adaptive, working even when some agents are offline.

During execution, the Pathfinder searches for agents that can handle specific **Practices** required by each **Post** in the **Pathway**. It then delegates the task to the most suitable available agent.

This demo requires **at least one agent** that supports the `Chat` practice, which is used in the first Post to generate a response from a prompt.

The **Pathfinder** is responsible for discovering the optimal way to execute a series of steps—called **Posts**—defined in a **Pathway**.

## 🎯 What This Test Does

This test uses a `Pathfinder` to execute a simple **Pathway** consisting of two sequential posts:

```
In Prompits, agent has capability (practice) and advertises it on a plaza.
The pathfinder will find the best way to run each post.
This example uses a Pathfinder to find the best way to run a pathway.

The pathway has two steps (posts):
1. Send a prompt to an LLM agent and return the response.
2. Translate the response of the first post to Chinese.
```

## 🛠️ How It Works

- Agents register themselves with specific **Practices** (e.g. text generation, translation).
- The **Pathfinder** examines the Pathway and delegates tasks to appropriate agents.
- Each Post in the Pathway is executed in order.
- Outputs from one step can be passed as inputs to the next.

## 🚀 Running the Example
1. Start at least one agent with the `Chat` practice:
   ```bash
   python ../create-agent.py --config ../agent2_lite.json --refresh --verbose-level INFO
   ```

2. Make sure you have Ollama installed and running with the required models (qwen2.5:32b or similar).

3. Prepare your test environment:
   ```bash
   # Clone the repository if you haven't already
   git clone https://github.com/prompits/python-sdk.git
   cd python-sdk/examples/pathfinder
   ```

To run the script:

```bash
python test_pathfinder.py
```

## ✅ Expected Output

You should see log messages showing:

- Agent registration
- Post execution by selected agents
- Final result after both steps

Example Output:
```
Pathway Result: {'prompt': 'What is the capital of France?', 'original_text': 'The capital of France is Paris.', 'result': 'La capitale de la France est Paris.'}
```

## 📁 Location

`examples/pathfinder/test_pathfinder.py`

## 🔧 Customizing the Pathway

The demo Pathway is defined in `pathway_demo.json`. You can customize it by modifying:

- **Model names**: Change the LLM model used in any Post
- **Prompts**: Adjust the instructions given to the model
- **Parameters**: Modify any other parameters for the Posts

Example modification:
### original 1st step
```json
   "entrance_post": {
        "post_id": "post_1",
        "name": "Preprocess Input",
        "practice": "Chat",
        "parameters": {
            "model": "qwen2.5:32b", 
            "prompt": "{prompt}"
        },
```
* Change model qwen2.5:32b to qwen2.5:7b

### original 2nd step
```json
            "post_id": "post_2",
            "name": "Translate to French",
            "practice": "Chat",
            "parameters": {
                "model": "qwen2.5:32b",
                "prompt": "Translate the following text to French: {original_text}"
            },

```
- change **model** qwen2.5:32b to qwen2.5:7b
- change **prompt** to any other prompt you want

### change initial prompt in test_pathfinder.py
```python

    # Run the pathway
    input_vars = {"prompt": "What is the capital of France?"}
    result = pathfinder.Run(pathway, **input_vars)
```
- change input_vars to the prompt you want