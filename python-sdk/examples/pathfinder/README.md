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

To run the script:

```bash
python test_pathfinder.py
```

Or using `pytest` if the script is structured accordingly:

```bash
pytest test_pathfinder.py
```

## ✅ Expected Output

You should see log messages showing:

- Agent registration
- Post execution by selected agents
- Final result after both steps

Example:
```
✔ Post 1 executed by Agent2
✔ Post 2 executed by Agent1
✔ Pathway completed: Response successfully translated to Chinese.
```

## 📁 Location

`examples/pathfinder/test_pathfinder.py`

## 🤝 Contributing

Feel free to expand this test with:
- More complex Pathways (branching, parallelism)
- Custom agent logic
- Performance benchmarking
