from autogen import AssistantAgent, UserProxyAgent, ConversableAgent, GroupChat, GroupChatManager
from autogen.coding import LocalCommandLineCodeExecutor, DockerCommandLineCodeExecutor
from collections import defaultdict
import os
import json
from datetime import datetime

class TaskManager:
    def __init__(self, agents, llm_config):
        self.agents = agents
        self.llm_config = llm_config
        self.current_speaker = None
        self.last_speaker = None
        self.agent_dict = {agent.name: agent for agent in agents}
        self.conversation_flow = []
        self.has_summary_spoken = False
        self.speaker_counter = defaultdict(int)
        
        # 定义任务关键词映射
        self.task_keywords = {
            'coding': ['code', 'programming', 'function', 'algorithm', 'implement', 'debug', 'class', 'method', 
                     'variable', 'loop', 'condition', 'exception', 'compile', 'runtime', 'syntax', 'library',
                     'framework', 'api', '代码', '编程', '函数', '算法', '实现', '调试', '类', '方法',
                     '变量', '循环', '条件', '异常', '编译', '运行时', '语法', '库', '框架'],
            'data': ['data', 'analysis', 'statistics', 'dataset', 'analyze', 'visualization', 'mining',
                    'prediction', 'clustering', 'classification', '数据', '分析', '统计', '数据集', '可视化',
                    '挖掘', '预测', '聚类', '分类'],
            'documentation': ['document', 'documentation', 'reference', 'manual', 'guide', 'specification',
                            'instruction', 'tutorial', 'example', '文档', '参考', '手册', '指南', '规范',
                            '说明', '教程', '示例'],
            'rag': ['knowledge base', 'ragflow', 'rag', 'retrieval', 'query', 'search', 'lookup',
                   '知识库', '检索', '查询', '搜索', '查找']
        }
        
    def analyze_task(self, message):
        """根据消息内容分析任务类型并规划对话流程"""
        message = message.lower()
        domain = self.get_task_domain(message)
        
        # 判断是否是概念解释类问题
        is_concept_question = any(keyword in message for keyword in ['what is', 'what are', '什么是', '解释'])
        
        # 根据任务领域和问题类型设置对话流程
        if is_concept_question:
            if domain == 'coding':
                self.conversation_flow = ['coding_assistant', 'summary_assistant']
            elif domain == 'data':
                self.conversation_flow = ['data_assistant', 'summary_assistant']
            elif domain == 'documentation':
                self.conversation_flow = ['doc_assistant', 'summary_assistant']
            elif domain == 'rag':
                self.conversation_flow = ['rag_assistant', 'summary_assistant']
            else:
                self.conversation_flow = ['chat_assistant', 'summary_assistant']
        else:
            if domain == 'coding':
                self.conversation_flow = ['chat_assistant', 'coding_assistant', 'summary_assistant']
            elif domain == 'data':
                self.conversation_flow = ['chat_assistant', 'data_assistant', 'summary_assistant']
            elif domain == 'documentation':
                self.conversation_flow = ['chat_assistant', 'doc_assistant', 'summary_assistant']
            elif domain == 'rag':
                self.conversation_flow = ['rag_assistant', 'summary_assistant']
            else:
                self.conversation_flow = ['chat_assistant', 'summary_assistant']
        
        # 重置发言计数
        self.speaker_counter.clear()
        return {'suggested_flow': self.conversation_flow}
        
    def get_task_domain(self, message):
        """根据关键词匹配确定任务领域"""
        scores = defaultdict(int)
        
        # 对每个领域进行关键词匹配和评分
        for domain, keywords in self.task_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    scores[domain] += 1
        
        # 如果没有明确的领域匹配，返回默认领域
        if not scores:
            return 'general'
        
        # 返回得分最高的领域
        return max(scores.items(), key=lambda x: x[1])[0]

    def get_agent_by_domain(self, domain):
        """根据领域返回对应的agent"""
        domain_map = {
            'coding': next(a for a in self.agents if a.name == 'coding_assistant'),
            'data': next(a for a in self.agents if a.name == 'data_assistant'),
            'documentation': next(a for a in self.agents if a.name == 'doc_assistant'),
            'rag': next(a for a in self.agents if a.name == 'rag_assistant')
        }
        return domain_map.get(domain, next(a for a in self.agents if a.name == 'chat_assistant'))
    
    def should_summarize(self, groupchat):
        """判断是否需要总结对话"""
        # 如果没有消息，不需要总结
        if not groupchat.messages:
            return False
            
        # 接近最大轮次时需要总结
        if len(groupchat.messages) >= groupchat.max_round - 1:
            return True
            
        # 当消息数量达到3条时，开始考虑是否需要总结
        if len(groupchat.messages) >= 3:
            # 检查最近三条消息的总长度
            recent_msgs = groupchat.messages[-3:]
            total_length = sum(len(msg.get('content', '')) for msg in recent_msgs)
            if total_length > 1000:  # 如果最近三条消息总长度超过1000字符，触发总结
                return True
                
            # 检查是否有重复的发言模式
            last_speakers = [msg.get('speaker', '') for msg in recent_msgs]
            if len(set(last_speakers)) <= 1:  # 如果连续三次都是同一个speaker
                return True
                
        # 检查某个agent是否发言过多（超过3次）
        for name, count in self.speaker_counter.items():
            if count >= 3 and name != 'summary_assistant':
                return True
                
        return False
    
    def save_chat_history(self, query, messages):
        """保存对话历史到JSON文件"""
        history_file = 'chat_history/history.json'
        os.makedirs('chat_history', exist_ok=True)
        
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = {"chat_history": []}
        
        # 提取关键信息
        chat_record = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "messages": [{
                "speaker": msg.get("speaker", ""),
                "content": msg.get("content", ""),
                "type": "summary" if msg.get("speaker") == "summary_assistant" else "conversation"
            } for msg in messages]
        }
        
        # 添加对话总结
        summary_messages = [msg for msg in messages if msg.get("speaker") == "summary_assistant"]
        if summary_messages:
            chat_record["final_summary"] = summary_messages[-1].get("content", "")
        
        history["chat_history"].append(chat_record)
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    
    def select_next_speaker(self, last_speaker, groupchat):
        """根据消息内容和对话状态选择下一个发言者"""
        # 初始化对话
        if not groupchat or not groupchat.messages:
            self.speaker_counter.clear()
            self.has_summary_spoken = False
            self.conversation_flow = ['chat_assistant']
            return self.agent_dict.get('chat_assistant')
        
        last_message = groupchat.messages[-1]
        message_text = last_message.get('content', '').lower()
        last_speaker_name = last_message.get('speaker')
        
        # 更新发言计数
        if last_speaker_name:
            self.speaker_counter[last_speaker_name] += 1
        
        # 如果是用户的第一次发言，分析任务并设置对话流程
        if last_speaker_name == 'user' and self.speaker_counter['user'] == 1:
            self.analyze_task(message_text)
        
        # 如果summary_assistant已经发言过，结束对话
        if self.has_summary_spoken:
            return None
        
        # 检查是否需要总结
        if self.should_summarize(groupchat):
            self.has_summary_spoken = True
            return self.agent_dict.get('summary_assistant')
        
        # 根据对话流程选择下一个发言者
        if self.conversation_flow:
            next_speaker_name = self.conversation_flow[0]
            self.conversation_flow = self.conversation_flow[1:]
            return self.agent_dict.get(next_speaker_name)
        
        # 如果没有预设的对话流程，根据任务领域选择专家
        domain = self.get_task_domain(message_text)
        next_speaker = self.get_agent_by_domain(domain)
        
        # 避免同一个助手连续发言
        if next_speaker.name == last_speaker_name:
            available_agents = [a for a in self.agents 
                              if a.name not in [last_speaker_name, 'user', 'summary_assistant'] 
                              and self.speaker_counter[a.name] < 3]
            if available_agents:
                next_speaker = min(available_agents, key=lambda x: self.speaker_counter[x.name])
        
        return next_speaker