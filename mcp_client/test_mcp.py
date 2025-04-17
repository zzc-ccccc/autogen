from utils.mcp_client import McpClients

config = {  "homeassistant": {    "url": "http://192.168.31.190:8123/mcp_server/sse",    "headers": {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI3MzFjNTA2MzA3ZjY0MTAxOGNhNzViYzk4YjZkMTI5ZSIsImlhdCI6MTc0NDAzNjYwNCwiZXhwIjoyMDU5Mzk2NjA0fQ.mlkkqIpFPde3quY8dou9ZwDxv607G3Y9MokE5cvO-YI"}, "timeout": 60,    "sse_read_timeout": 300  }}



client = McpClients(config)
tools = client.fetch_tools()  # 获取工具列表
print(tools)
client.close()