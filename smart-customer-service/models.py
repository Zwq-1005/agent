import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def get_qwen_model():
    """连接通义千问模型"""
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model = "qwen-plus"
    
    # 1. 获取 API Key
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    # 2. 确保 api_key 是字符串，而不是 None 或其他类型
    if not api_key or not isinstance(api_key, str):
        raise ValueError("API Key 未找到或格式错误，请检查 .env 文件")

    # 3. 初始化模型
    llm = ChatOpenAI(
        base_url=base_url, 
        model=model, 
        api_key=api_key  
    )
    return llm
