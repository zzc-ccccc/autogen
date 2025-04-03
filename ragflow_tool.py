# ragflow_tool.py
import requests
import os
from dotenv import load_dotenv
import json

# 加载 .env 文件中的环境变量
# 确保你的 .env 文件与这个脚本或主脚本在同一目录，或者提供正确路径
# load_dotenv() 
# 或者指定路径:
load_dotenv("d:/autogen1/.env") # 使用你实际的 .env 文件路径

RAGFLOW_BASE_URL = os.getenv("RAGFLOW_API_URL")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY")

def query_ragflow_service(user_query: str, chat_id: str = "f062554a104211f0b7b40242ac120004"):
    """
    调用 RAGflow 的类 OpenAI 聊天 API 端点 (POST /chats_openai/{chat_id}/chat/completions) 
    来获取基于知识库的答案。
    """
    if not RAGFLOW_BASE_URL or not RAGFLOW_API_KEY:
        return "错误：RAGFLOW_API_URL 或 RAGFLOW_API_KEY 未在 .env 文件中正确设置。"

    # 构建包含 chat_id 的完整 URL (请再次确认基础 URL 和路径!)
    endpoint_path = f"/chats_openai/{chat_id}/chat/completions"
    full_url = RAGFLOW_BASE_URL.rstrip('/') + endpoint_path

    headers = {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type": "application/json"
    }

    # 构建符合类 OpenAI 格式的请求体
    payload = {
      "model": "ragflow-model", # 这个值根据文档似乎可以任意写
      "messages": [{"role": "user", "content": user_query}],
      "stream": False
      # 根据 RAGflow API 文档，可能需要添加其他参数，如 kb_id 等
    }

    print(f"--- 调用 RAGflow API ---")
    print(f"URL: {full_url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    # print(f"Headers: {headers}") # 调试时可以取消注释，但注意不要泄露 Key

    try:
        response = requests.post(full_url, headers=headers, json=payload, timeout=120) # 增加超时时间
        response.raise_for_status() # 检查 HTTP 错误 (如 4xx, 5xx)
        
        result = response.json()
        
        # 解析响应 (严格按照 Postman 成功时返回的格式)
        # 假设和 OpenAI 一致: choices[0].message.content
        answer = result.get("choices", [{}])[0].get("message", {}).get("content", None)

        if answer:
             print(f"--- RAGflow 响应 ---")
             print(answer)
             return answer
        else:
             print(f"--- RAGflow 响应格式不符或无答案 ---")
             print(f"原始响应: {result}")
             return "无法从 RAGflow 响应中提取有效答案。"

    except requests.exceptions.RequestException as e:
        print(f"调用 RAGflow API 出错: {e}")
        return f"调用 RAGflow API 时出错: {e}"
    except Exception as e:
        print(f"处理 RAGflow 响应出错: {e}")
        return f"处理 RAGflow 响应时出错: {e}"