"""
FastAPI 后端服务
启动命令：uvicorn api:app --reload --host 0.0.0.0 --port 8000
"""
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from agent import create_customer_service_agent

app = FastAPI(title="智锐科技智能客服系统", version="1.0.0")

# 全局Agent实例（所有会话共享）
agent = create_customer_service_agent()


# ========== 数据模型 ==========
class ChatRequest(BaseModel):
    """请求体：用户消息 + 会话ID"""
    message: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    """响应体：AI回复 + 会话ID"""
    reply: str
    thread_id: str


# ========== API 接口 ==========
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """对话接口 - 接收用户消息，返回AI回复"""
    config = {"configurable": {"thread_id": req.thread_id}}
    response = agent.invoke(
        {"messages": [{"role": "user", "content": req.message}]},
        config=config,
    )
    reply = response["messages"][-1].content
    return ChatResponse(reply=reply, thread_id=req.thread_id)


@app.get("/health")
async def health():
    """健康检查接口"""
    return {"status": "ok"}


@app.get("/new-session")
async def new_session():
    """生成新会话ID"""
    return {"thread_id": str(uuid.uuid4())}