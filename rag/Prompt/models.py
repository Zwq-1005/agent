from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
# 加载环境变量
load_dotenv()


def get_qwen_llm(model="qwen-plus", temperature=0.4):
    """
    获取QWEN模型
    """
    # 连接地址
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # 连接模型
    llm = ChatOpenAI(base_url=base_url, model=model, temperature=temperature)
    return llm


if __name__ == "__main__":
    llm = get_qwen_llm()
    print(llm.invoke("你好"))
