import autogen
import requests
import json
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent, GroupChat, GroupChatManager
from autogen.coding import LocalCommandLineCodeExecutor, DockerCommandLineCodeExecutor
import os
from datetime import datetime
from collections import defaultdict
from task_manager import TaskManager
from tools.ragflow_tool import query_ragflow_service  # 导入工具函数
from rag_assistant import create_rag_assistant  # 添加RAG助手导入

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
    system_message="""A human user who needs help with various tasks.""",
    human_input_mode="NEVER",
    code_execution_config={
        "last_n_messages": 2,
        "work_dir": "groupchat",
        "use_docker": False,
    }
)

# 创建聊天助手
chat_assistant = AssistantAgent(
    name="chat_assistant",
    system_message="""You are a knowledgeable assistant who can answer general questions and provide explanations on various topics.
    Focus on providing clear, accurate, and concise responses to user queries.
    Do not write code or perform technical analysis - defer those tasks to other specialists.""",
    llm_config=llm_config
)

# RAGflow 知识专家 Agent
ragflow_expert = autogen.AssistantAgent(
    name="RAGflow_Knowledge_Expert",
    system_message="你是一个专门回答 RAGflow 相关问题的助手。\n"
                   "对于通用的编程或常识问题，请直接回答。\n"
                   "如果问题明确涉及到需要查询 RAGflow 内部知识库、特定文档内容、或项目特定信息时，"
                   "你**必须**使用 `query_ragflow_service` 工具来查找答案，然后根据工具返回的结果进行回复。\n"
                   "不要自己编造关于 RAGflow 内部知识的答案。",
    llm_config=llm_config
)

# 创建编码助手
coding_assistant = AssistantAgent(
    name="coding_assistant",
    system_message="""You are a coding expert who MUST:
    1. Focus exclusively on writing, reviewing and debugging code
    2. Provide clean, well-documented code solutions
    3. Follow best practices and design patterns
    4. Explain technical concepts only in the context of code implementation
    Do not provide general explanations or documentation - defer those to other specialists.""",
    llm_config=llm_config
)

# 创建数据分析助手
data_assistant = AssistantAgent(
    name="data_assistant",
    system_message="""You are a data analysis expert who MUST:
    1. Focus on data processing strategies and analytical approaches
    2. Provide insights on data structures, algorithms and optimization
    3. Suggest appropriate tools and methods for data analysis
    4. Think through data-related problems step by step
    Do not write implementation code - defer that to the coding specialist.""",
    llm_config=llm_config
)

# 创建文档助手
doc_assistant = AssistantAgent(
    name="doc_assistant",
    system_message="""You are a documentation expert who MUST:
    1. Focus on creating clear, organized documentation
    2. Write user guides, API docs, and technical specifications
    3. Improve existing documentation for clarity and completeness
    4. Structure information in a logical, accessible way
    Do not write code or provide technical solutions - defer those to other specialists.""",
    llm_config=llm_config
)

# 创建总结助手
summary_assistant = AssistantAgent(
    name="summary_assistant",
    system_message="""You are a summarization expert who MUST:
    1. Provide CONCISE summaries (max 300 words) that capture key points
    2. Focus on actionable conclusions and next steps
    3. Highlight important decisions and outcomes
    4. Use clear, structured formatting
    Keep summaries brief and focused - detailed explanations belong to other specialists.""",
    llm_config=llm_config
)

# 对话历史保存功能已移至TaskManager类中

# 创建RAG助手
rag_assistant = create_rag_assistant(llm_config)

# 创建任务管理器
task_manager = TaskManager(
    agents=[user_proxy, chat_assistant, coding_assistant, data_assistant, doc_assistant, summary_assistant, rag_assistant],
    llm_config=llm_config
)

# 创建群聊
groupchat = GroupChat(
    agents=[user_proxy, chat_assistant, coding_assistant, data_assistant, doc_assistant, summary_assistant, rag_assistant],
    messages=[],
    max_round=10,
    speaker_selection_method=task_manager.select_next_speaker  # 使用TaskManager的选择器方法
)

# 创建群聊管理器
manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

if __name__ == "__main__":
    query = input("请输入您的问题: ")
    # 启动群聊
    chat_result = user_proxy.initiate_chat(
        recipient=manager,
        message=query
    )
    
    # 保存对话历史
    task_manager.save_chat_history(query, groupchat.messages)