import asyncio
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_core.models import UserMessage

async def main():
    ollama_client = OllamaChatCompletionClient(
        model = "mistral",
        host = "http://localhost:11434/"
    )

    result = await ollama_client.create([UserMessage(content="What is the capital of France?", source="user")])
    print(result)

# 运行异步函数
if __name__ == "__main__":
    asyncio.run(main())
