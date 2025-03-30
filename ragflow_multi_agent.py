import autogen
import requests
import json
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent, GroupChat, GroupChatManager
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

# 创建用户代理
user_proxy = autogen.UserProxyAgent(
    name="user",
    system_message="""A Human Head of Architecture""",
    human_input_mode="NEVER",  # 设置为TERMINATE表示对话结束时才需要人类输入
    code_execution_config={
        "last_n_messages": 2,
        "work_dir": "groupchat",
        "use_docker": False,
    }

)

rag_assistant = AssistantAgent(
    name="rag_assistant",
    system_message="""You are a helpful assistant. You can answer user's question if you know the answer.""",
    llm_config=llm_config,
    code_execution_config = False,
    max_consecutive_auto_reply=1,
    human_input_mode="NEVER"
)

translator = ConversableAgent(
    name="translator",
    system_message="""Use the output of the rag_assistant to summarize.""",
    llm_config=llm_config
)

transition_rules = {
    user_proxy: [rag_assistant],
    rag_assistant: [translator]
}

groupchat = autogen.GroupChat(
        agents=[user_proxy, rag_assistant, translator], 
        messages=[], 
        max_round=10,
        allowed_or_disallowed_speaker_transitions=transition_rules,
        speaker_transitions_type="allowed")


manager = autogen.GroupChatManager(
        groupchat=groupchat, 
        llm_config=llm_config)


if __name__ == "__main__":
    query = input("请输入您的问题: ")

    groupchat_result = user_proxy.initiate_chat(
        recipient=manager, 
        message=query)
    