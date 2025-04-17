from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools, SseMcpToolAdapter, SseServerParams
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_core import CancellationToken
from autogen_agentchat.ui import Console
from autogen_core.models import ModelInfo
import asyncio
import os
from dotenv import load_dotenv

from utils.mcp_client import McpClients

# 加载.env文件中的环境变量
load_dotenv()

async def main() -> None:
    # 从环境变量获取敏感信息
    home_assistant_url = os.getenv("HOME_ASSISTANT_URL")
    home_assistant_token = os.getenv("HOME_ASSISTANT_TOKEN")
    home_assistant_timeout = int(os.getenv("HOME_ASSISTANT_TIMEOUT", "30"))
    home_assistant_sse_read_timeout = int(os.getenv("HOME_ASSISTANT_SSE_READ_TIMEOUT", "300"))

    # Create server params for the remote MCP service
    server_params = SseServerParams(
        url=home_assistant_url,
        headers={"Authorization": f"Bearer {home_assistant_token}"},
        timeout=home_assistant_timeout,  # Connection timeout in seconds
    )


    # 从环境变量获取Ollama配置
    ollama_model = os.getenv("OLLAMA_MODEL")
    ollama_host = os.getenv("OLLAMA_HOST")

    # 修改Ollama配置部分
    model_client = OllamaChatCompletionClient(
        model=ollama_model,
        host=ollama_host,
        model_info=ModelInfo(
            family="unknown",
            name=ollama_model,
            function_calling=True,
            vision=False,
            json_output=False
        )
    )

    # 从环境变量获取OpenAI配置
    openai_model = os.getenv("OPENAI_MODEL")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    openai_model_client = OpenAIChatCompletionClient(
        model=openai_model,
        api_key=openai_api_key,
    )

    # client = McpClients(config)
    # tools = client.fetch_tools()
    # print(tools)

    tools = await mcp_server_tools(server_params)

    #setup agent
    agent = AssistantAgent(
        name="homeassistant",
        model_client=model_client,
        tools=tools,
        reflect_on_tool_use=True
    )

    # Let the agent control the device
    await Console(
        agent.run_stream(
            task="""Turn on the desk lamp in minto.""",
            cancellation_token=CancellationToken()
        )
    )


if __name__ == "__main__":
    asyncio.run(main())