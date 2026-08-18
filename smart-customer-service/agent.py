"""
智能客服Agent：集成6个工具 + 多轮对话记忆 + 消息裁剪中间件
"""
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model
from langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime
from typing import Any

from models import get_qwen_model
from tools import all_tools

# ========== 消息裁剪中间件 ==========
MSG_LEN = 10  # 保留最近10条消息


@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """
    保留最近MSG_LEN条消息，防止上下文窗口溢出。
    确保第一条消息不是tool类型（tool消息必须跟在AI消息后面）。
    """
    messages = state["messages"]

    if len(messages) <= MSG_LEN:
        return None

    # 取最近MSG_LEN条
    recent = messages[-MSG_LEN:]

    # 如果第一条是tool消息，往前多取一条AI消息
    if recent[0].type == "tool":
        recent = messages[-(MSG_LEN + 1) :]

    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *recent]}


# ========== 创建Agent ==========
def create_customer_service_agent():
    model = get_qwen_model()

    agent = create_agent(
        model=model,
        tools=all_tools,
        checkpointer=InMemorySaver(),
        middleware=[trim_messages],
        system_prompt="""你是"智锐科技"的智能客服助手小睿。你的职责是帮助用户处理以下事务：

1. 【订单查询】用户询问订单状态、订单详情时，使用 query_order 工具按订单号查询，或使用 query_orders_by_name 工具按姓名查询全部订单
2. 【物流查询】用户询问快递、物流、到货时间时，使用 query_logistics 工具查询
3. 【工单创建】用户需要退货、换货、维修、投诉时，使用 create_ticket 工具创建售后工单。你需要收集：用户姓名、问题类型（退货/换货/维修/投诉/其他）、问题描述
4. 【产品咨询】用户询问产品功能、使用方法、退换货政策、保修政策等时，使用 search_product_knowledge 工具检索知识库

注意事项：
- 回答要专业、礼貌、简洁
- 如果用户信息不完整（如缺少订单号或姓名），主动追问
- 如果用户只是闲聊或打招呼，直接友好回复即可，不需要调用工具
- 无法解决的问题，建议用户联系人工客服 400-888-0000
- 创建工单后，务必告知用户工单号和预计处理时间
- 当前日期时间可使用 get_current_datetime 工具查询""",
    )
    return agent


# ========== 测试 ==========
if __name__ == "__main__":
    agent = create_customer_service_agent()
    config = {"configurable": {"thread_id": "test-001"}}

    # 测试1：闲聊
    print("=== 测试1：闲聊 ===")
    resp = agent.invoke({"messages": [{"role": "user", "content": "你好"}]}, config=config)
    print(resp["messages"][-1].content)

    # 测试2：订单查询
    print("\n=== 测试2：订单查询 ===")
    config = {"configurable": {"thread_id": "test-002"}}
    resp = agent.invoke({"messages": [{"role": "user", "content": "帮我查一下订单ORD202401001的状态"}]}, config=config)
    print(resp["messages"][-1].content)

    # 测试3：知识库检索
    print("\n=== 测试3：知识库检索 ===")
    config = {"configurable": {"thread_id": "test-003"}}
    resp = agent.invoke({"messages": [{"role": "user", "content": "AI学习机Pro有什么功能"}]}, config=config)
    print(resp["messages"][-1].content)

    # 测试4：创建工单
    print("\n=== 测试4：创建工单 ===")
    config = {"configurable": {"thread_id": "test-004"}}
    resp = agent.invoke({"messages": [{"role": "user", "content": "我叫张三，我买的学习机屏幕有亮点，想退货"}]}, config=config)
    print(resp["messages"][-1].content)

    # 测试5：多轮对话记忆
    print("\n=== 测试5：多轮对话记忆 ===")
    config = {"configurable": {"thread_id": "test-005"}}
    resp = agent.invoke({"messages": [{"role": "user", "content": "帮我查一下订单ORD202401001"}]}, config=config)
    print(resp["messages"][-1].content)
    resp = agent.invoke({"messages": [{"role": "user", "content": "这个订单的物流到哪了？"}]}, config=config)
    print(resp["messages"][-1].content)