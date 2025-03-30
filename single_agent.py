import autogen
import requests
import json
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor, DockerCommandLineCodeExecutor
import os

model = "deepseek-r1:7b"

ollama_config_list = [
    {
        "model": model,
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama", # required, but not used,
    }
]


# 创建基于本地模型的LLM配置
llm_config = {
    "config_list": ollama_config_list,
    "cache_seed": None, 
    "temperature":0.0, 
    "seed": 52,
    "timeout": 300,  # optional, timeout for API calls
}

rag_assistant = ConversableAgent(
    name="rag_assistant",
    system_message="""Assistant who can answer questions about the content of the files in the workspace.""",
    llm_config=llm_config,
    code_execution_config = False,
    max_consecutive_auto_reply=1,
    human_input_mode="NEVER"
)


if __name__ == "__main__":
    query = input("请输入您的问题: ")
    rag_assistant.initiate_chat(rag_assistant,  message=query)