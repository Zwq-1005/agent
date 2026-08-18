"""
LangGraph workflow for statistical analysis.

Graph structure:
    START → Router → Coder → Executor → Reviewer → END
                    ↑                    │
                    └──── retry ────────┘ (on failure, max 3 retries)
"""
import json
import logging
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

import pandas as pd
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL, MAX_RETRY_COUNT
from app.graph.sandbox import execute_code

logger = logging.getLogger(__name__)


# ─── State Definition ──────────────────────────────────────────────────────────────

class AnalysisState(TypedDict):
    """State passed between nodes in the stats graph."""
    messages: Annotated[List[Dict[str, str]], "Conversation history"]
    user_message: str
    file_path: str | None
    df_info: Dict[str, Any] | None  # columns, dtypes, shape info
    intent: str
    code: str
    execution_result: Dict[str, Any] | None
    error: str | None
    retry_count: int
    final_output: str | None


# ─── LLM Setup ─────────────────────────────────────────────────────────────────────

def get_llm():
    """Get configured LLM instance."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")
    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        temperature=0.1,
    )


# ─── Node 1: Router ────────────────────────────────────────────────────────────────

ROUTER_PROMPT = """你是一个数据分析意图识别器。根据用户的输入，将意图分类为以下之一：

- data_cleaning: 数据清洗（处理缺失值、异常值、重复值、格式转换等）
- descriptive_stats: 描述性统计（均值、方差、分位数、频率分布等）
- comparison_test: 组间比较（t检验、方差分析、非参数检验等）
- regression_analysis: 回归分析（线性回归、Logistic回归、相关性分析等）
- survival_analysis: 生存分析（Kaplan-Meier、Cox回归等）
- categorical_analysis: 分类变量分析（卡方检验、Fisher精确检验等）
- diagnosis_test: 诊断试验评价（ROC曲线、敏感度/特异度等）
- visualization: 数据可视化（绘图、图表等）

用户输入: {user_message}

数据列信息: {df_info}

请只返回JSON格式的分类结果，不要有其他文字：
{{"intent": "<意图类型>", "reasoning": "<简短理由>", "language": "<zh|en>"}}"""


def router_node(state: AnalysisState) -> AnalysisState:
    """Classify user intent for the analysis."""
    llm = get_llm()

    prompt = ROUTER_PROMPT.format(
        user_message=state["user_message"],
        df_info=json.dumps(state.get("df_info", {}), ensure_ascii=False),
    )

    response = llm.invoke(prompt)
    try:
        content = response.content
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.strip("`").strip()
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content)
        state["intent"] = result.get("intent", "descriptive_stats")
    except (json.JSONDecodeError, KeyError):
        content = response.content.lower()
        if "清洗" in content or "cleaning" in content:
            state["intent"] = "data_cleaning"
        elif "回归" in content or "regression" in content or "logistic" in content:
            state["intent"] = "regression_analysis"
        elif "生存" in content or "survival" in content or "cox" in content or "kaplan" in content:
            state["intent"] = "survival_analysis"
        elif "图" in content or "visualization" in content or "plot" in content:
            state["intent"] = "visualization"
        elif "卡方" in content or "chi" in content or "fisher" in content or "频数" in content:
            state["intent"] = "categorical_analysis"
        elif "roc" in content or "auc" in content or "诊断" in content:
            state["intent"] = "diagnosis_test"
        elif "比较" in content or "t检验" in content or "anova" in content or "方差" in content:
            state["intent"] = "comparison_test"
        else:
            state["intent"] = "descriptive_stats"

    state["error"] = None
    return state


# ─── Node 2: Coder ─────────────────────────────────────────────────────────────────

CODER_PROMPT = """你是一个 Python/Pandas 医学统计分析代码生成器。

根据用户的意图和数据集信息，生成可直接执行的 pandas/scipy 分析代码。

要求：
1. 数据已加载到变量 `df` 中，直接使用 `df` 进行分析
2. 如果需要保存结果图表，使用 matplotlib.pyplot（已导入为 plt），调用 plt.savefig 会自动捕获
3. 如果有表格形式的关键结果，将其赋值给变量 `result`（DataFrame 或字符串）
4. 如果生成了图表，请设置图表标题为中文，使用 plt.title()
5. 只输出纯 Python 代码，不要用 markdown 代码块包裹，不要有解释文字
6. 代码必须稳健，处理可能的 NaN 值、除零等情况
7. 对于中文输出，确保使用 UTF-8 编码
8. 使用 scipy.stats 进行统计检验（如 ttest_ind, mannwhitneyu, f_oneway, chi2_contingency 等）
9. 检查数据是否满足检验的前提假设（正态性、方差齐性等）

数据集信息:
- 列名: {columns}
- 数据类型: {dtypes}
- 行数: {row_count}
- 字段定义: {field_definitions}

用户意图: {intent}
用户指令: {user_message}

直接输出代码（不要用 ``` 包裹）："""


def coder_node(state: AnalysisState) -> AnalysisState:
    """Generate Python/Pandas code based on user intent."""
    llm = get_llm()

    df_info = state.get("df_info", {})
    error_context = ""
    if state.get("error"):
        error_context = (
            f"\n\n上一次代码执行出错，请修复错误：\n"
            f"错误信息: {state['error']}\n"
            f"失败的代码:\n{state.get('code', '')}\n"
            f"请仔细分析错误原因并生成修正后的代码。"
        )

    prompt = CODER_PROMPT.format(
        columns=json.dumps(df_info.get("columns", []), ensure_ascii=False),
        dtypes=json.dumps(df_info.get("dtypes", {}), ensure_ascii=False),
        row_count=df_info.get("row_count", "未知"),
        field_definitions=json.dumps(
            df_info.get("field_definitions", []), ensure_ascii=False
        ),
        intent=state["intent"],
        user_message=state["user_message"],
    ) + error_context

    response = llm.invoke(prompt)
    code = response.content.strip()

    # Strip markdown code fences if present
    if code.startswith("```"):
        lines = code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)

    state["code"] = code
    return state


# ─── Node 3: Executor ──────────────────────────────────────────────────────────────

def executor_node(state: AnalysisState) -> AnalysisState:
    """Execute the generated code in a sandbox."""
    file_path = state.get("file_path")
    if not file_path:
        state["execution_result"] = {
            "success": False,
            "stdout": "",
            "stderr": "No data file loaded. Please upload a file first.",
            "figure_base64": None,
            "result_text": "",
            "result_table": None,
        }
        state["error"] = "No data file loaded. Please upload a file first."
        return state

    try:
        df = pd.read_csv(file_path)
    except Exception:
        try:
            df = pd.read_excel(file_path)
        except Exception:
            try:
                df = pd.read_json(file_path)
            except Exception as e:
                state["execution_result"] = {
                    "success": False,
                    "stdout": "",
                    "stderr": str(e),
                    "figure_base64": None,
                    "result_text": "",
                    "result_table": None,
                }
                state["error"] = f"Failed to read data file: {e}"
                return state

    result = execute_code(state["code"], df)
    state["execution_result"] = result

    if not result["success"]:
        state["error"] = result.get("stdout") or result.get("stderr") or "Unknown execution error"
    else:
        state["error"] = None

    return state


# ─── Node 4: Reviewer ──────────────────────────────────────────────────────────────

def reviewer_node(state: AnalysisState) -> AnalysisState:
    """Review execution results. Route back to Coder on failure, or end on success."""
    exec_result = state.get("execution_result", {})
    retry_count = state.get("retry_count", 0)

    if exec_result.get("success"):
        parts = []
        if exec_result.get("stdout"):
            parts.append(exec_result["stdout"])
        if exec_result.get("result_text"):
            parts.append(exec_result["result_text"])
        if exec_result.get("figure_base64"):
            pass  # Handled separately as chart type in SSE

        state["final_output"] = "\n".join(parts) if parts else "分析完成"
    else:
        if retry_count < MAX_RETRY_COUNT:
            state["retry_count"] = retry_count + 1
            logger.info(f"Retry {retry_count + 1}/{MAX_RETRY_COUNT} after execution failure")
        else:
            state["final_output"] = (
                f"分析失败（已重试 {MAX_RETRY_COUNT} 次）:\n"
                f"{state.get('error', '未知错误')}"
            )

    return state


# ─── Routing Functions ─────────────────────────────────────────────────────────────

def should_retry(state: AnalysisState) -> Literal["coder", "end"]:
    """Decide whether to retry or end."""
    exec_result = state.get("execution_result", {})
    retry_count = state.get("retry_count", 0)

    if not exec_result.get("success") and retry_count < MAX_RETRY_COUNT:
        return "coder"
    return "end"


# ─── Graph Builder ─────────────────────────────────────────────────────────────────

def build_stats_graph() -> StateGraph:
    """Build and compile the LangGraph stats analysis graph."""
    workflow = StateGraph(AnalysisState)

    workflow.add_node("router", router_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("reviewer", reviewer_node)

    workflow.set_entry_point("router")
    workflow.add_edge("router", "coder")
    workflow.add_edge("coder", "executor")
    workflow.add_edge("executor", "reviewer")

    workflow.add_conditional_edges(
        "reviewer",
        should_retry,
        {
            "coder": "coder",
            "end": END,
        },
    )

    return workflow.compile()


# ─── Run Graph with Streaming ──────────────────────────────────────────────────────

async def run_graph_stream(
    user_message: str,
    file_path: str,
    df_info: Dict[str, Any],
):
    """
    Run the stats graph with streaming events.

    Yields SSE-formatted events for each stage of the analysis.
    """
    graph = build_stats_graph()

    initial_state: AnalysisState = {
        "messages": [],
        "user_message": user_message,
        "file_path": file_path,
        "df_info": df_info,
        "intent": "",
        "code": "",
        "execution_result": None,
        "error": None,
        "retry_count": 0,
        "final_output": None,
    }

    final_state = None
    async for event in graph.astream_events(initial_state, version="v2"):
        kind = event.get("event")
        data = event.get("data", {})

        if kind == "on_chain_start":
            node_name = event.get("name", "")

            if node_name == "router":
                yield "event: thinking\ndata: 正在分析你的需求...\n\n"
            elif node_name == "coder":
                yield "event: thinking\ndata: 正在生成分析代码...\n\n"
            elif node_name == "executor":
                yield "event: executing\ndata: 正在执行分析...\n\n"
            elif node_name == "reviewer":
                pass  # Internal node

        elif kind == "on_chain_end":
            node_name = event.get("name", "")
            output = data.get("output", {})

            if node_name == "router":
                intent = output.get("intent", "")
                yield f"event: thinking\ndata: 识别意图: {intent}\n\n"
            elif node_name == "coder":
                code = output.get("code", "")
                yield f"event: coding\ndata: {json.dumps({'code': code})}\n\n"
            elif node_name == "executor":
                exec_result = output.get("execution_result", {})
                if exec_result.get("success"):
                    if exec_result.get("stdout"):
                        yield (
                            f"event: result\ndata: {json.dumps({'type': 'text', 'content': exec_result['stdout'], 'title': '执行输出'})}\n\n"
                        )
                    if exec_result.get("result_text"):
                        yield (
                            f"event: result\ndata: {json.dumps({'type': 'text', 'content': exec_result['result_text'], 'title': '分析结果'})}\n\n"
                        )
                    if exec_result.get("result_table"):
                        yield (
                            f"event: result\ndata: {json.dumps({'type': 'table', 'content': '', 'title': '结果表格', 'columns': exec_result['result_table']['columns'], 'rows': exec_result['result_table']['rows']})}\n\n"
                        )
                    if exec_result.get("figure_base64"):
                        yield (
                            f"event: result\ndata: {json.dumps({'type': 'chart', 'content': exec_result['figure_base64'], 'title': '可视化图表'})}\n\n"
                        )
                else:
                    error_msg = exec_result.get("stdout") or exec_result.get("stderr") or "Unknown error"
                    yield (
                        f"event: error\ndata: {json.dumps({'type': 'error', 'content': error_msg, 'title': '执行错误'})}\n\n"
                    )
            elif node_name == "reviewer":
                final_output = output.get("final_output")
                if final_output and not output.get("execution_result", {}).get("success"):
                    yield (
                        f"event: error\ndata: {json.dumps({'type': 'error', 'content': final_output, 'title': '分析失败'})}\n\n"
                    )
                yield "event: done\ndata: 分析完成\n\n"
                final_state = output

    # Fallback: if no streaming events were yielded, do a regular invoke
    if final_state is None:
        final_state = graph.invoke(initial_state)
        exec_result = final_state.get("execution_result", {})
        if exec_result:
            yield "event: thinking\ndata: 分析完成\n\n"
            if exec_result.get("success"):
                if exec_result.get("stdout"):
                    yield f"event: result\ndata: {json.dumps({'type': 'text', 'content': exec_result['stdout'], 'title': '执行输出'})}\n\n"
                if exec_result.get("result_text"):
                    yield f"event: result\ndata: {json.dumps({'type': 'text', 'content': exec_result['result_text'], 'title': '分析结果'})}\n\n"
                if exec_result.get("result_table"):
                    yield f"event: result\ndata: {json.dumps({'type': 'table', 'content': '', 'title': '结果表格', 'columns': exec_result['result_table']['columns'], 'rows': exec_result['result_table']['rows']})}\n\n"
                if exec_result.get("figure_base64"):
                    yield f"event: result\ndata: {json.dumps({'type': 'chart', 'content': exec_result['figure_base64'], 'title': '可视化图表'})}\n\n"
            else:
                yield f"event: error\ndata: {json.dumps({'type': 'error', 'content': final_state.get('error', 'Unknown error'), 'title': '执行错误'})}\n\n"
        yield "event: done\ndata: 分析完成\n\n"
