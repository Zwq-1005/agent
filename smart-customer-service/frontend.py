"""
Streamlit 聊天前端
启动命令：streamlit run frontend.py
（需先启动后端：uvicorn api:app --reload --host 0.0.0.0 --port 8000）
"""
import streamlit as st
import requests

# ========== 页面配置 ==========
st.set_page_config(
    page_title="智锐科技 · 智能客服",
    page_icon="🤖",
    layout="centered",
)

# ========== 隐藏 Streamlit 默认样式 ==========
hide_streamlit_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stAppDeployButton {display:none;}
        header {visibility: hidden;}
        .st-emotion-cache-1kyxreq {padding-top: 0;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ========== 标题区域 ==========
st.markdown("""
<div style="
    background: linear-gradient(135deg, #1a73e8, #0d47a1);
    padding: 20px 30px;
    border-radius: 12px;
    color: white;
    margin-bottom: 20px;
    text-align: center;
">
    <h1> 智锐科技 · 智能客服</h1>
    <p>基于 LangChain Agent 的企业智能客服助手</p>
</div>
""", unsafe_allow_html=True)

# ========== API 地址 ==========
API_URL = "http://localhost:8000"

# ========== 初始化会话状态 ==========
if "thread_id" not in st.session_state:
    # 向后端请求一个新的会话ID
    try:
        resp = requests.get(f"{API_URL}/new-session")
        st.session_state.thread_id = resp.json()["thread_id"]
    except:
        st.session_state.thread_id = "default"

if "messages" not in st.session_state:
    st.session_state.messages = []


# ========== 显示聊天历史 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ========== 快捷按钮（欢迎语之后显示一次） ==========
if len(st.session_state.messages) == 0:
    st.markdown("""<div style="text-align:center;color:#666;margin-bottom:10px;">
        你好，我是小睿！请问有什么可以帮你？
    </div>""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    quick_actions = [
        (" 查询订单", "帮我查一下订单ORD202401001的状态"),
        (" 查询物流", "订单ORD202401001的物流到哪了"),
        (" 产品咨询", "AI学习机Pro有什么功能"),
        (" 创建工单", "我叫张三，学习机屏幕有亮点，想退货"),
        (" 按姓名查", "张三的全部订单有哪些"),
        (" 售后政策", "保修政策是什么"),
    ]
    for i, (label, query) in enumerate(quick_actions):
        col = [col1, col2, col3][i % 3]
        if col.button(label, key=f"quick_{i}", use_container_width=True):
            st.session_state.quick_query = query
            st.rerun()


# ========== 处理快捷提问 ==========
if "quick_query" in st.session_state and st.session_state.quick_query:
    query = st.session_state.quick_query
    st.session_state.quick_query = ""

    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # 调用API
    with st.chat_message("assistant"):
        with st.spinner("小睿正在思考..."):
            try:
                resp = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "message": query,
                        "thread_id": st.session_state.thread_id,
                    },
                    timeout=30,
                )
                reply = resp.json()["reply"]
            except Exception as e:
                reply = f"抱歉，系统出了点问题：{e}\\n请联系人工客服 400-888-0000"
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()


# ========== 聊天输入框 ==========
if prompt := st.chat_input("请输入您的问题..."):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 调用后端API
    with st.chat_message("assistant"):
        with st.spinner("小睿正在思考..."):
            try:
                resp = requests.post(
                    f"{API_URL}/chat",
                    json={
                        "message": prompt,
                        "thread_id": st.session_state.thread_id,
                    },
                    timeout=30,
                )
                reply = resp.json()["reply"]
            except Exception as e:
                reply = f"抱歉，系统出了点问题：{e}\\n请联系人工客服 400-888-0000"
        st.markdown(reply)

    # 保存回复到历史
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # 自动刷新页面
    st.rerun()


# ========== 边栏：会话管理 ==========
with st.sidebar:
    st.markdown("###  会话管理")
    st.caption(f"会话ID: {st.session_state.thread_id[:8]}...")

    if st.button(" 新对话", use_container_width=True):
        # 重置会话
        try:
            resp = requests.get(f"{API_URL}/new-session")
            st.session_state.thread_id = resp.json()["thread_id"]
        except:
            st.session_state.thread_id = "default"
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("###  可查询的数据")
    st.caption("""
    **订单列表：**
    - ORD202401001（张三 - 已发货）
    - ORD202401002（李四 - 已完成）
    - ORD202401003（王五 - 待发货）
    - ORD202401005（张三 - 已发货）
    **测试用户：** 张三、李四、王五、赵六
    **测试工单：** 张三（退货）、李四（维修）
    """)