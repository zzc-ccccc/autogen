# AutoGen Demo Project

This project contains four Python examples demonstrating different AI agent applications using the AutoGen framework.

## Requirements

- Python 3.9+
- Ollama service (for running local LLM models)

## Virtual Environment Setup

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment

Windows:
```bash
venv\Scripts\activate
```

Linux/MacOS:
```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install autogen requests
pip install -U "autogen-agentchat"
pip install ollama
```

## Ollama configuration

1. Install Ollama: Access [Ollama official website](https://ollama.ai/) to download and install
2. Download DeepSeek model:
```bash
ollama pull deepseek-r1:7b
ollama pull mistral
```
3. Make sure Ollama service is running at http://localhost:11434

## Example file explanation

### 1. single_agent.py
- Single agent example
- Create a RAG assistant agent that can answer questions about the content of the workspace file
- Running way: `python single_agent.py`

### 2. multi_agent.py
- Multi agent collaboration example
- Contains user agent, RAG assistant and translator three agents
- Implemented rules for agent conversion and group chat management
- Running way: `python multi_agent.py`

### 3. basic_autogen_agent_llm.py
- Basic code execution example
- Showcases how to use local code executor and Docker code executor
- Contains code generation agent that can generate and execute Python scripts
- Running way: `python basic_autogen_agent_llm.py`

### 4. rag_flow_main.py
- RAGFlow integration example
- Demonstrates connecting to RAGFlow knowledge base
- Implements a RAG expert agent with tool calling capability
- Running way: `python rag_flow_main.py`

## Notes

1. Make sure Ollama service is running before running the example
2. All examples use DeepSeek-R1-7B model, please ensure it is downloaded correctly
3. Code execution will generate a file in the specified working directory, please check the corresponding directory

## Common problems

1. If model loading error occurs, please check if Ollama service is running correctly
2. If dependency problem occurs, please ensure all necessary packages are installed