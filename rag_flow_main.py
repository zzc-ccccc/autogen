# main.py
import autogen
from ragflow_tool import query_ragflow_service  # 导入工具函数
import os

# --- 配置 AutoGen Agent 使用的 LLM ---
# 这个 LLM 需要能够理解何时调用工具 (Function Calling / Tool Use)
# 可以是 OpenAI GPT, 也可以是配置好的、支持工具调用的本地 Ollama 模型
# 确保对应的 API Key (如 OPENAI_API_KEY) 也在 .env 文件中或环境变量中设置了

# 示例：使用环境变量中的 OpenAI 配置 (或者你可以修改为 Ollama 配置)
# config_list_for_autogen = autogen.config_list_from_dotenv(dotenv_file_path="d:/autogen1/.env")
# 如果用 Ollama 并且它支持工具调用：
# 修改Ollama配置部分（恢复base_url定义）
ollama_model_for_autogen = "deepseek-r1:1.5b"
ollama_base_url_for_autogen = "http://10.255.255.254:11434/v1"  # 恢复base_url定义

# 修改Ollama配置部分（完全删除openai相关参数）
config_list_for_autogen = [
    {
        "model": ollama_model_for_autogen,
        "base_url": ollama_base_url_for_autogen,
        "api_key": "ollama",  # 必须存在但值任意
        # 完全移除timeout参数（先测试基础连接）
    }
]

# --- 配置使用工具的 Agent 的 LLM Config ---
# 修改导入语句（移除工具函数）
import autogen
import os

# --- 删除工具模式定义和LLM配置中的tools参数 ---
llm_config_ragflow_expert = {
    "config_list": config_list_for_autogen,
    "temperature": 0,
    "timeout": 60,
    "cache_seed": 42
}

# 修改系统消息
system_message="你是一个回答 RAGflow 相关问题的助手。请基于你的知识进行回答。"

# 删除文件中所有重复的 llm_config_ragflow_expert 定义（原文件第70-74行）


# --- 创建 AutoGen Agents ---
user_proxy = autogen.UserProxyAgent(
   name="User_Proxy_Executor",
   human_input_mode="TERMINATE",
   max_consecutive_auto_reply=5,  # 保持参数一致
   code_execution_config=False,
   default_auto_reply="请求超时，请稍后再试。"
)

# RAGflow 知识专家 Agent
ragflow_expert = autogen.AssistantAgent(
    name="RAGflow_Knowledge_Expert",
    system_message="你是一个专门回答 RAGflow 相关问题的助手。\n"
                   "对于通用的编程或常识问题，请直接回答。\n"
                   "如果问题明确涉及到需要查询 RAGflow 内部知识库、特定文档内容、或项目特定信息时，"
                   "你**必须**使用 `query_ragflow_service` 工具来查找答案，然后根据工具返回的结果进行回复。\n"
                   "不要自己编造关于 RAGflow 内部知识的答案。",
    llm_config=llm_config_ragflow_expert,
)

# --- 发起对话 ---
if __name__ == "__main__":
    # 清理之前的聊天记录 (如果需要)
    # autogen.runtime_logging.stop()
    # autogen.runtime_logging.start(config={"dbname": "logs.db"})

    # 发起一个需要调用 RAGflow 的问题
    user_proxy.initiate_chat(
        recipient=ragflow_expert,
        message="根据 RAGflow 的知识库，请解释一下 RAG 是什么？",  # 这个问题应该触发工具调用
        # message="写一个 Python 函数计算斐波那契数列。",  # 这个通用问题不应触发工具调用
    )

    # autogen.runtime_logging.stop()  # 停止日志记录