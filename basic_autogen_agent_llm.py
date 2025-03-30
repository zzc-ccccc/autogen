"""Author: https://github.com/lestan"""
"""Tested on AutoGen version 0.2.19"""
"""This is a basic working version of AutoGen that uses a local LLM served by Ollama"""
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor, DockerCommandLineCodeExecutor
import os
from pathlib import Path
import pprint

#model = "mixtral:latest"
model = "deepseek-r1:7b"

ollama_config_list = [
    {
        "model": model,
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama", # required, but not used,
    }
]

work_dir = Path("generated_code")
work_dir.mkdir(exist_ok=True)

local_code_executor = LocalCommandLineCodeExecutor(
    work_dir=work_dir
)

docker_code_executor = DockerCommandLineCodeExecutor(
    work_dir=work_dir,
    stop_container=True
)

# create an AssistantAgent instance named "assistant"
code_executor_agent = AssistantAgent(
    name="code_executor_agent",
    llm_config=False,
    code_execution_config={"executor": local_code_executor}, # change to docker_code_executor to use docker
    human_input_mode="NEVER",
)

code_writer_system_message = """
Please provide Python or shell script solutions to solve the user's tasks, which the user can execute by simply running the code. Each solution should be placed inside a code block with the first line reserved for a comment including the filename. Do not ask the user to modify the code or copy and paste results; instead, use the `print` function for output when relevant.
1. Gather information: Write a script that outputs necessary information such as browsing/searching the web, downloading/reading a file, printing the content of a webpage or file, getting the current date/time, or checking the operating system. After displaying sufficient information to solve the task based on language skills, you may stop the code and solve the remaining task yourself. 
2. Perform a task: Write an executable script to solve the given task and output the result. If necessary, break down the problem into steps with clear explanations of which steps involve coding and which steps require language skills. Do not ask the user to modify the code or provide feedback; the code should be ready for execution.
3. When writing an executable script, always begin with a code block and do not use escape characters or leading spaces if not required.
Please provide one code block per response to allow the user to easily execute each solution.
Here are some examples of a code block with a filename comment:
```python
# filename: script_one.py
print("Hello, World!")
```
```sh
# filename: script_two.sh
printf "Hello, World!"
```
"""

code_writer_agent = ConversableAgent(
    name="code_writer_agent",
    system_message=code_writer_system_message,
    llm_config={"config_list": ollama_config_list, "cache_seed": None, "temperature":0.0, "seed": 52},
    code_execution_config=False, # turn off code execution for this agent
    max_consecutive_auto_reply=2,
    human_input_mode="NEVER",
)

task = """Write Python code to plot a chart of NVDA and TSLA stock price change YTD shown side by side for comparison and save the Python code to disk using the filename specified.""" 
#task = """Write Python code to plot a chart of the YTD stock performance of the top 10 banks and save the Python code to disk using the filename specified."""

if __name__ == "__main__":
    # the coding assistant receives a message from the code executor, which contains the task description
    chat_result = code_executor_agent.initiate_chat(
        code_writer_agent,
        message=task,
        clear_history=True,
    )

    pprint.pprint(chat_result)