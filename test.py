import autogen
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent, GroupChat, GroupChatManager
import os

model = "deepseek-r1:7b"

ollama_config_list = [
    {
        "model": model,
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    }
]

llm_config = {
    "config_list": ollama_config_list,
    "cache_seed": None,
    "temperature": 0.0,
    "seed": 52,
    "timeout": 300,
}

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

class SmartGroupChatManager(GroupChatManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_agents = [user_proxy, qa_assistant, planner_agent, tool_user, summarize]

    def _get_agent_by_name(self, name):
        for agent in self.all_agents:
            if agent.name == name:
                return agent
        return None

    def _process_received_message(self, message, sender, silent):
        if sender.name == "user":
            message_lower = message.lower()
            selected_agents = [self._get_agent_by_name("user")]

            if any(k in message_lower for k in ["plan", "project", "timeline", "goal", "step"]):
                selected_agents.append(self._get_agent_by_name("planner_agent"))
            elif any(k in message_lower for k in ["tool", "api", "run", "test", "use"]):
                selected_agents.append(self._get_agent_by_name("tool_user"))
            else:
                selected_agents.append(self._get_agent_by_name("qa_assistant"))

            selected_agents.append(self._get_agent_by_name("summarize"))

            self.groupchat.agents = selected_agents

            new_transitions = {}
            for i in range(len(self.groupchat.agents) - 1):
                new_transitions[self.groupchat.agents[i]] = [self.groupchat.agents[i + 1]]
            self.groupchat.allowed_or_disallowed_speaker_transitions = new_transitions

        return super()._process_received_message(message, sender, silent)

transition_rules = {
    user_proxy: [qa_assistant, planner_agent, tool_user],
    qa_assistant: [summarize],
    planner_agent: [summarize],
    tool_user: [summarize]
}

groupchat = GroupChat(
    agents=[user_proxy, qa_assistant, planner_agent, tool_user, summarize],
    messages=[],
    max_round=10,
    allowed_or_disallowed_speaker_transitions=transition_rules,
    speaker_transitions_type="allowed"
)

manager = SmartGroupChatManager(groupchat=groupchat, llm_config=llm_config)

if __name__ == "__main__":
    query = input("Please enter your question: ")
    user_proxy.initiate_chat(recipient=manager, message=query)