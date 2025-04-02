import autogen
import requests
import json
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent, GroupChat, GroupChatManager
from autogen.coding import LocalCommandLineCodeExecutor, DockerCommandLineCodeExecutor
import os
import re

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

data_processor = AssistantAgent(
    name="data_processor",
    system_message="""You are a data processing expert specialized in analyzing and processing data.
    You can help with data analysis, visualization, statistical calculations, and data transformation tasks.""",
    llm_config=llm_config,
    code_execution_config=False,
    human_input_mode="NEVER"
)

code_generator = AssistantAgent(
    name="code_generator",
    system_message="""You are a code generation expert specialized in writing and optimizing code.
    You can help with generating code snippets, implementing algorithms, and providing coding solutions.""",
    llm_config=llm_config,
    code_execution_config=False,
    human_input_mode="NEVER"
)

summarize = ConversableAgent(
    name="summarize",
    system_message="""Use the output of other agents to provide a clear and concise summary.""",
    llm_config=llm_config
)

class SmartGroupChatManager(GroupChatManager):
    def _process_received_message(self, message, sender, silent):
        if sender.name == "user":
            # 分析用户问题，确定需要的agents
            message_lower = message.lower()
            selected_agents = [self.groupchat.agents[0]]  # 始终包含user_proxy
            
            # 检查是否包含数据处理相关关键词
            data_keywords = ["数据", "分析", "统计", "可视化", "data", "analyze", "statistics", "visualization"]
            needs_data_processing = any(keyword in message_lower for keyword in data_keywords)
            
            # 检查是否包含代码生成相关关键词
            code_keywords = ["代码", "编程", "实现", "算法", "code", "program", "implement", "algorithm"]
            needs_code_generation = any(keyword in message_lower for keyword in code_keywords)
            
            # 根据关键词选择合适的agent
            if needs_data_processing:
                # 如果需要数据处理，使用data_processor
                for agent in self.groupchat.agents:
                    if agent.name == "data_processor":
                        selected_agents.append(agent)
                        break
            elif needs_code_generation:
                # 如果需要代码生成，使用code_generator
                for agent in self.groupchat.agents:
                    if agent.name == "code_generator":
                        selected_agents.append(agent)
                        break
            else:
                # 如果没有匹配到特定agent，使用默认的rag_assistant
                for agent in self.groupchat.agents:
                    if agent.name == "rag_assistant":
                        selected_agents.append(agent)
                        break
            
            # 始终添加summarize作为最后一个agent
            for agent in self.groupchat.agents:
                if agent.name == "summarize":
                    selected_agents.append(agent)
                    break
            
            # 更新groupchat的agents列表
            self.groupchat.agents = selected_agents
            
            # 构建新的transition rules
            new_transitions = {}
            for i in range(len(selected_agents)-1):
                new_transitions[selected_agents[i]] = [selected_agents[i+1]]
            
            self.groupchat.allowed_or_disallowed_speaker_transitions = new_transitions
        
        return super()._process_received_message(message, sender, silent)

transition_rules = {
    user_proxy: [rag_assistant, data_processor, code_generator],
    rag_assistant: [summarize],
    data_processor: [summarize],
    code_generator: [summarize]
}

groupchat = autogen.GroupChat(
        agents=[user_proxy, rag_assistant, data_processor, code_generator, summarize], 
        messages=[], 
        max_round=10,
        allowed_or_disallowed_speaker_transitions=transition_rules,
        speaker_transitions_type="allowed")


manager = SmartGroupChatManager(
        groupchat=groupchat, 
        llm_config=llm_config)


if __name__ == "__main__":
    query = input("请输入您的问题: ")

    groupchat_result = user_proxy.initiate_chat(
        recipient=manager, 
        message=query)
    