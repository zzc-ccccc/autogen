# main.py
from typing import Annotated
import autogen
from tools.ragflow_tool import query_ragflow_service  # 导入工具函数
from autogen.coding import LocalCommandLineCodeExecutor, DockerCommandLineCodeExecutor
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent
import os
from pathlib import Path
from dotenv import load_dotenv
# --- 配置使用工具的 Agent 的 LLM Config ---
# 修改导入语句（移除工具函数）
import os


# --- 配置 AutoGen Agent 使用的 LLM ---
# 这个 LLM 需要能够理解何时调用工具 (Function Calling / Tool Use)
# 可以是 OpenAI GPT, 也可以是配置好的、支持工具调用的本地 Ollama 模型
# 确保对应的 API Key (如 OPENAI_API_KEY) 也在 .env 文件中或环境变量中设置了

# 示例：使用环境变量中的 OpenAI 配置 (或者你可以修改为 Ollama 配置)
# config_list_for_autogen = autogen.config_list_from_dotenv(dotenv_file_path="d:/autogen1/.env")
# 如果用 Ollama 并且它支持工具调用：
# 修改Ollama配置部分（恢复base_url定义）
ollama_model_for_autogen = "mistral"
ollama_base_url_for_autogen = "http://localhost:11434/v1"  # 恢复base_url定义


# 修改Ollama配置部分（完全删除openai相关参数）
config_list_for_autogen = [
    {
        "model": ollama_model_for_autogen,
        "base_url": ollama_base_url_for_autogen,
        "api_key": "ollama",  # 必须存在但值任意
        # 完全移除timeout参数（先测试基础连接）
    }
]


# --- 删除工具模式定义和LLM配置中的tools参数 ---
llm_config_ragflow_expert = {
    "config_list": config_list_for_autogen,
    "temperature": 0,
    "timeout": 60,
    "cache_seed": 42
}


# 代码执行
work_dir = Path("tools")
work_dir.mkdir(exist_ok=True)

local_code_executor = LocalCommandLineCodeExecutor(
    work_dir=work_dir
)

docker_code_executor = DockerCommandLineCodeExecutor(
    work_dir=work_dir,
    stop_container=True
)


# 修改系统消息
#system_message="你是一个回答 RAGflow 相关问题的助手。请基于你的知识进行回答。"

# 删除文件中所有重复的 llm_config_ragflow_expert 定义（原文件第70-74行）


# --- 创建 AutoGen Agents ---
user_proxy = autogen.UserProxyAgent(
   name="User_Proxy_Executor",
   human_input_mode="NEVER",
   max_consecutive_auto_reply=5,  # 保持参数一致
   code_execution_config=False
)

# RAGflow 知识专家 Agent
ragflow_expert = AssistantAgent(
    name="RAGflow_Knowledge_Expert",
    system_message=""" call ragflow_guy to answer the question from RAGFlow""",
    code_execution_config=False, 
    llm_config=llm_config_ragflow_expert,  
)

@user_proxy.register_for_execution()
@ragflow_expert.register_for_llm(description="Query RAGflow")
def ragflow_guy(message: Annotated[str, "The question to query RAGflow."]) -> str:
    print(f"--- Receive message from user_proxy ---")
    print(message)
    print(f"--- call ragflow funxtion ---")
    result = query_ragflow_service(message)
    return result





# --- 发起对话 ---
if __name__ == "__main__":
    # 清理之前的聊天记录 (如果需要)
    # autogen.runtime_logging.stop()
    # autogen.runtime_logging.start(config={"dbname": "logs.db"})

    # 发起一个需要调用 RAGflow 的问题
    user_proxy.initiate_chat(
        recipient=ragflow_expert,
        message="do i need to use EC2 in this assignment?",  # 这个问题应该触发工具调用
        # message="写一个 Python 函数计算斐波那契数列。",  # 这个通用问题不应触发工具调用
        slient= False,
        clear_history= True,
    )

    # autogen.runtime_logging.stop()  # 停止日志记录