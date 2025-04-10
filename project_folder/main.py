from autogen import UserProxyAgent, ConversableAgent, GroupChat, GroupChatManager
from autogen.coding import LocalCommandLineCodeExecutor
from autogen.agentchat.contrib.mcp_agent import MCPAIAgent

from dotenv import load_dotenv
import os

# ✅ 加载 .env 文件
load_dotenv()

# 本地 Ollama 模型配置
ollama_config_list = [
    {
        "model": "deepseek-r1:7b",  # 改成你安装的模型名
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "price": [0.0, 0.0]  # 避免成本提示警告
    }
]

llm_config = {
    "config_list": ollama_config_list,
    "temperature": 0.3,
    "seed": 42,
}

# ✅ 用户发起 agent
user_proxy = UserProxyAgent(
    name="user_proxy",
    code_execution_config=False,
    human_input_mode="TERMINATE"
)

# ✅ 回答/逻辑助手
rag_assistant = ConversableAgent(
    name="rag_assistant",
    llm_config=llm_config,
    system_message="""
You are an assistant who helps the user with reasoning, file analysis, and task coordination.
""",
    code_execution_config=False,
)

# ✅ 本地 Python 执行 agent
executor = ConversableAgent(
    name="executor",
    llm_config=llm_config,
    system_message="You are a Python code executor. Only respond with code results.",
    code_execution_config={"executor": LocalCommandLineCodeExecutor(work_dir=".")},
)

# ✅ MCP 智能家居控制 agent
mcp_agent = MCPAIAgent(
    name="mcp_home_assistant",
    llm_config=llm_config,
    mcp_config={
        "url": os.getenv("SSE_URL"),
        "headers": {
            "Authorization": f"Bearer {os.getenv('API_ACCESS_TOKEN')}"
        },
        "tool_filter": ["states", "lights", "light", "devices", "history", "service"],
    }
)

# 多智能体群组
groupchat = GroupChat(
    agents=[user_proxy, rag_assistant, executor, mcp_agent],
    messages=[],
    max_round=10,
)

manager = GroupChatManager(
    groupchat=groupchat,
    llm_config=llm_config,
)

# 🚀 启动入口
if __name__ == "__main__":
    print("✅ AutoGen + MCP 控制系统已启动！你可以输入自然语言命令控制你的智能家居")
    query = input("请输入控制指令，例如：打开客厅的灯、查看所有设备状态 等。\n> ")
    user_proxy.initiate_chat(manager, message=query)
