# AutoGen 示例项目

这个项目包含了三个使用AutoGen框架的Python示例，展示了不同场景下的AI代理应用。

## 环境要求

- Python 3.9+
- Ollama服务（用于运行本地LLM模型）

## 虚拟环境配置

1. 创建虚拟环境
```bash
python -m venv venv
```

2. 激活虚拟环境

Windows:
```bash
venv\Scripts\activate
```

Linux/MacOS:
```bash
source venv/bin/activate
```

## 安装依赖

```bash
pip install autogen requests
pip install -U "autogen-agentchat"
pip install ollama
```

## Ollama配置

1. 安装Ollama: 访问 [Ollama官网](https://ollama.ai/) 下载并安装
2. 下载DeepSeek模型:
```bash
ollama pull deepseek-r1:7b
```
3. 确保Ollama服务运行在 http://localhost:11434

## 示例文件说明

### 1. single_agent.py
- 单代理示例
- 创建一个RAG助手代理，可以回答关于工作区文件内容的问题
- 运行方式：`python single_agent.py`

### 2. multi_agent.py
- 多代理协作示例
- 包含用户代理、RAG助手和翻译器三个代理
- 实现了代理之间的转换规则和群聊管理
- 运行方式：`python multi_agent.py`

### 3. basic_autogen_agent_llm.py
- 基础代码执行示例
- 展示了如何使用本地代码执行器和Docker代码执行器
- 包含代码编写代理，可以生成并执行Python脚本
- 运行方式：`python basic_autogen_agent_llm.py`

## 注意事项

1. 确保在运行示例之前已启动Ollama服务
2. 所有示例都使用DeepSeek-R1-7B模型，请确保已正确下载
3. 代码执行时会在指定工作目录生成文件，请注意查看相应目录

## 常见问题

1. 如果遇到模型加载错误，请检查Ollama服务是否正常运行
2. 如果遇到依赖问题，请确保已正确安装所有必要的包