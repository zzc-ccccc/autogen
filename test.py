import autogen
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent, GroupChat, GroupChatManager

# 模型配置
model = "deepseek-r1:7b"

ollama_config_list = [
    {
        "model": model,
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",  # Required but unused
    }
]

llm_config = {
    "config_list": ollama_config_list,
    "cache_seed": None,
    "temperature": 0.0,
    "seed": 52,
    "timeout": 300,
}

# 用户代理
user_proxy = UserProxyAgent(
    name="user",
    system_message="A Human Head of Architecture",
    human_input_mode="NEVER",
    code_execution_config={
        "last_n_messages": 2,
        "work_dir": "groupchat",
        "use_docker": False,
    }
)

# 功能代理
qa_assistant = AssistantAgent(
    name="qa_assistant",
    system_message="You are a helpful assistant specialized in question answering and factual lookup.",
    llm_config=llm_config,
    code_execution_config=False,
    human_input_mode="NEVER"
)

planner_agent = AssistantAgent(
    name="planner_agent",
    system_message="You are a strategic planning agent who can break down goals into actionable steps.",
    llm_config=llm_config,
    code_execution_config=False,
    human_input_mode="NEVER"
)

tool_user = AssistantAgent(
    name="tool_user",
    system_message="You are responsible for calling tools or APIs and reporting results.",
    llm_config=llm_config,
    code_execution_config=False,
    human_input_mode="NEVER"
)

summarize = ConversableAgent(
    name="summarize",
    system_message="Use the outputs from other agents to provide a concise summary.",
    llm_config=llm_config
)

# 智能管理器
class SmartGroupChatManager(GroupChatManager):
    def _process_received_message(self, message, sender, silent):
        if sender.name == "user":
            message_lower = message.lower()
            selected_agents = [self.groupchat.agents[0]]  # 始终包含user_proxy
            
            if any(k in message_lower for k in ["plan", "timeline", "goal", "project", "step"]):
                selected_agents.append(planner_agent)
            elif any(k in message_lower for k in ["tool", "api", "run", "test", "use"]):
                selected_agents.append(tool_user)
            else:
                selected_agents.append(qa_assistant)
            
            selected_agents.append(summarize)
            print(f"[DEBUG] Selected agents: {[agent.name for agent in selected_agents]}")
            
            # 更新groupchat的agents列表
            self.groupchat.agents = selected_agents
            
            # 构建新的transition rules
            new_transitions = {}
            for i in range(len(selected_agents)-1):
                new_transitions[selected_agents[i]] = [selected_agents[i+1]]
            
            self.groupchat.allowed_or_disallowed_speaker_transitions = new_transitions
        
        return super()._process_received_message(message, sender, silent)

# 所有 agent 注册到团队中
all_agents = [user_proxy, qa_assistant, planner_agent, tool_user, summarize]

# 初始transition rules
transition_rules = {
    user_proxy: [qa_assistant, planner_agent, tool_user],
    qa_assistant: [summarize],
    planner_agent: [summarize],
    tool_user: [summarize]
}

groupchat = GroupChat(
    agents=all_agents,
    messages=[],
    max_round=10,
    allowed_or_disallowed_speaker_transitions=transition_rules,
    speaker_transitions_type="allowed",
)

manager = SmartGroupChatManager(groupchat=groupchat, llm_config=llm_config)

if __name__ == "__main__":
    query = input("Please enter your question: ")
    user_proxy.initiate_chat(recipient=manager, message=query)
