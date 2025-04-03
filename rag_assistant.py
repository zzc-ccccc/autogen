from autogen import AssistantAgent
from ragflow_tool import query_ragflow_service

def create_rag_assistant(llm_config):
    """创建RAGflow知识库查询助手"""
    return AssistantAgent(
        name="rag_assistant",
        system_message="""你是一个专门负责知识库查询的RAGflow助手。你的主要职责是：
        1. 处理需要查询知识库的问题
        2. 使用RAGflow工具获取准确的知识库信息
        3. 基于查询结果提供清晰的解答
        4. 对于不需要知识库查询的问题，将任务转交给其他专家
        
        你必须遵循以下原则：
        1. 优先使用query_ragflow_service工具查询知识库
        2. 不要编造或臆测知识库中的信息
        3. 如果问题超出知识库范围，说明情况并建议咨询其他专家""",
        llm_config={
            **llm_config,
            "functions": [
                {
                    "name": "query_ragflow_service",
                    "description": "查询RAGflow知识库获取信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_query": {
                                "type": "string",
                                "description": "用户的查询问题"
                            },
                            "chat_id": {
                                "type": "string",
                                "description": "对话ID",
                                "default": "f062554a104211f0b7b40242ac120004"
                            }
                        },
                        "required": ["user_query"]
                    }
                }
            ]
        }
    )