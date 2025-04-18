import autogen
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent, GroupChat, GroupChatManager
import sounddevice as sd
import numpy as np
import whisper
import wave
import threading
import queue
import time
from pynput import keyboard
import sys
from TTS.api import TTS
import torch


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
voice_agent = AssistantAgent(
    name="voice_agent",
    system_message="""You are a voice recognition agent responsible for:
    1. Recording audio from the computer's microphone
    2. Converting the recorded speech to text using Whisper
    3. Passing the transcribed text to other agents for processing
    
    When user wants to use voice input, you should:
    1. Start recording from the microphone
    2. Save the audio to a WAV file
    3. Use Whisper to transcribe the audio
    4. Pass the transcribed text to the appropriate agent""",
    llm_config=llm_config,
    code_execution_config={
        "last_n_messages": 2,
        "work_dir": "groupchat",
        "use_docker": False,
    },
    human_input_mode="NEVER"
)

summarize = ConversableAgent(
    name="summarize",
    system_message="Use the outputs from other agents to provide a concise summary.",
    llm_config=llm_config
)

# 智能管理器
def record_audio_hold(sample_rate=16000):
    audio_queue = queue.Queue()
    recording = False
    stream = None

    def audio_callback(indata, frames, time, status):
        if recording:
            audio_queue.put(indata.copy())

    def on_press(key):
        nonlocal recording, stream
        try:
            if key == keyboard.Key.space and not recording:
                recording = True
                print("Recording... (Hold spacebar to speak, release to stop)")
                stream = sd.InputStream(
                    samplerate=sample_rate,
                    channels=1,
                    dtype=np.float32,
                    callback=audio_callback
                )
                stream.start()
        except Exception as e:
            print(f"Recording error: {e}")

    def on_release(key):
        nonlocal recording, stream
        if key == keyboard.Key.space and recording:
            recording = False
            if stream:
                stream.stop()
                stream.close()
            return False

    print("Press and hold spacebar to speak, release to stop...")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

    audio_chunks = []
    while not audio_queue.empty():
        audio_chunks.append(audio_queue.get())

    if not audio_chunks:
        print("No audio input detected")
        return None

    audio_data = np.concatenate(audio_chunks)
    print("Recording completed")
    return audio_data

def save_audio(audio_data, filename="command.wav", sample_rate=16000):
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())

def transcribe_audio(filename="command.wav"):
    model = whisper.load_model("base")
    result = model.transcribe(filename)
    return result["text"]

# 缓存TTS模型
_tts_models = {}

def text_to_speech(text, volume_scale=0.1, speed_scale=1.0):
    # 使用默认的TTS模型
    model_name = "tts_models/en/ljspeech/tacotron2-DDC"
    
    try:
        # 初始化TTS模型
        tts = TTS(model_name)
        tts.to("cuda" if torch.cuda.is_available() else "cpu")
        
        # 创建停止事件和键盘监听器
        stop_event = threading.Event()
        
        def on_press(key):
            try:
                if key == keyboard.KeyCode.from_char('q'):
                    print("\nStopping voice output...")
                    stop_event.set()
                    sd.stop()
                    return False
            except Exception as e:
                print(f"Error handling key press: {e}")
        
        # 启动键盘监听
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        
        # 生成语音，禁用音标显示
        print("\nGenerating voice output (press 'q' to stop)...")
        wav = tts.tts(text=text, use_phonemes=False)
        
        # 音频后处理
        wav = np.array(wav)
        # 先进行归一化，再调整音量
        wav = wav / np.max(np.abs(wav))
        wav = wav * volume_scale
        
        # 播放音频
        sd.play(wav, samplerate=22050, blocking=False)
        
        # 等待播放完成或停止信号
        while sd.get_stream() and sd.get_stream().active and not stop_event.is_set():
            time.sleep(0.1)
            
        # 清理资源
        listener.stop()
        sd.stop()
        
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        if 'listener' in locals():
            listener.stop()
        sd.stop()

class SmartGroupChatManager(GroupChatManager):
    def _process_received_message(self, message, sender, silent):
        if sender.name == "user":
            message_lower = message.lower()
            
            # Check if voice input is needed
            if "voice" in message_lower:
                print("Preparing to receive voice input...")
                audio_data = record_audio()
                save_audio(audio_data)
                message = transcribe_audio()
                print(f"Voice recognition result: {message}")
                message_lower = message.lower()
            selected_agents = [self.groupchat.agents[0]]  # Always include user_proxy
            
            # 添加voice_agent进行语音处理
            selected_agents.append(voice_agent)
            
            # 最后添加summarize进行总结
            selected_agents.append(summarize)
            print(f"[DEBUG] Selected agents: {[agent.name for agent in selected_agents]}")
            
            # 更新groupchat的agents列表
            self.groupchat.agents = selected_agents
            
            # 构建新的transition rules
            new_transitions = {}
            for i in range(len(selected_agents)-1):
                new_transitions[selected_agents[i]] = [selected_agents[i+1]]
            
            self.groupchat.allowed_or_disallowed_speaker_transitions = new_transitions
        
        # 只在summarize agent输出最终总结时进行语音播报
        if sender.name == "summarize":
            print("\nGenerating voice response...")
            text_to_speech(message)
            print("Voice response completed.")
        
        return super()._process_received_message(message, sender, silent)

# 所有 agent 注册到团队中
all_agents = [user_proxy, voice_agent, summarize]

# 初始transition rules
transition_rules = {
    user_proxy: [voice_agent],
    voice_agent: [summarize]
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
    print("Please select input method:")
    print("1. Press 'V' for voice input/output (hold spacebar to speak)")
    print("2. Directly input your question")
    choice = input("Please choose (V/direct input): ").strip()
    
    # 设置语音模式标志
    manager.voice_mode = (choice.upper() == 'V')
    
    if manager.voice_mode:
        audio_data = record_audio_hold()
        if audio_data is not None:
            save_audio(audio_data)
            query = transcribe_audio()
            print(f"Voice recognition result: {query}")
        else:
            print("Failed to get valid voice input, please try again")
            sys.exit(1)
    else:
        query = choice
    
    user_proxy.initiate_chat(recipient=manager, message=query)
