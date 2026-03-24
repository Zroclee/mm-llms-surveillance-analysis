import base64
import json
import operator
import os
from typing import Any

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from typing_extensions import Annotated, TypedDict

try:
    from .tools.tool_cv2 import opencv_image_compare_tool
except ImportError:
    try:
        from agents.tools.tool_cv2 import opencv_image_compare_tool
    except ImportError:
        from tools.tool_cv2 import opencv_image_compare_tool

_qwen_model: ChatOpenAI | None = None
_ds_model: ChatOpenAI | None = None
_ds_model_with_tools = None


class MessagesState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], operator.add]
    basic_image_path: str
    comparison_image_path: str
    compare_tool_result: dict[str, Any]
    difference_found: bool
    qwen_analysis: str
    alert_report: str


def _encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False)


def _get_qwen_model() -> ChatOpenAI:
    global _qwen_model
    if _qwen_model is None:
        _qwen_model = ChatOpenAI(
            model="qwen3.5-plus",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    return _qwen_model


def _get_ds_model() -> ChatOpenAI:
    global _ds_model
    if _ds_model is None:
        _ds_model = ChatOpenAI(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
        )
    return _ds_model


def _get_ds_model_with_tools():
    global _ds_model_with_tools
    if _ds_model_with_tools is None:
        _ds_model_with_tools = _get_ds_model().bind_tools([opencv_image_compare_tool])
    return _ds_model_with_tools


def ds_llm_call(state: MessagesState):
    res = _get_ds_model_with_tools().invoke(
        [
            SystemMessage(
                content=(
                    "你是仓库物品监控告警流程中的主管模型。"
                    "你的第一步必须调用opencv_image_compare_tool对比两张图片是否存在显著差异，"
                    "不要直接给出最终结论。"
                )
            ),
            HumanMessage(
                content=(
                    "请先调用opencv_image_compare_tool。"
                    f"基础图路径: {state['basic_image_path']}\n"
                    f"实时图路径: {state['comparison_image_path']}"
                )
            ),
        ]
    )
    return {"messages": [res]}


def compare_tool_call(state: MessagesState):
    last_message = state["messages"][-1] if state.get("messages") else None
    tool_call = None
    if last_message is not None and getattr(last_message, "tool_calls", None):
        for item in last_message.tool_calls:
            if item.get("name") == "opencv_image_compare_tool":
                tool_call = item
                break

    if tool_call:
        args = tool_call.get("args", {}) or {}
        image1_source = args.get("image1_source") or state["basic_image_path"]
        image2_source = args.get("image2_source") or state["comparison_image_path"]
        result = opencv_image_compare_tool.invoke(
            {"image1_source": image1_source, "image2_source": image2_source}
        )
        tool_message = ToolMessage(
            content=json.dumps(result, ensure_ascii=False),
            tool_call_id=tool_call.get("id", "opencv_image_compare_tool"),
        )
    else:
        result = opencv_image_compare_tool.invoke(
            {
                "image1_source": state["basic_image_path"],
                "image2_source": state["comparison_image_path"],
            }
        )
        tool_message = ToolMessage(
            content=json.dumps(result, ensure_ascii=False),
            tool_call_id="opencv_image_compare_tool_manual",
        )

    return {
        "messages": [tool_message],
        "compare_tool_result": result,
        "difference_found": result.get("是否存在显著差异") == "是",
    }


def qwen_llm_call(state: MessagesState):
    basic_image_b64 = _encode_image(state["basic_image_path"])
    comparison_image_b64 = _encode_image(state["comparison_image_path"])
    res = _get_qwen_model().invoke(
        [
            SystemMessage(
                content=(
                    "你是仓库监控视觉分析专家。请分析两张图中的差异点，明确指出："
                    "1) 差异区域与变化描述；"
                    "2) 是否存在物品移动；"
                    "3) 是否存在物品丢失；"
                    "4) 置信度与依据；"
                    "5) 建议的处置动作。"
                )
            ),
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": "第一张为基础图，第二张为实时图，请重点分析仓库物品变化。",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{basic_image_b64}"},
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{comparison_image_b64}"
                        },
                    },
                ]
            ),
        ]
    )
    return {"messages": [res], "qwen_analysis": _normalize_content(res.content)}


def ds_generate_alert_call(state: MessagesState):
    compare_info = json.dumps(
        state.get("compare_tool_result", {}), ensure_ascii=False, indent=2
    )
    qwen_analysis = state.get("qwen_analysis", "")
    res = _get_ds_model().invoke(
        [
            SystemMessage(
                content=(
                    "你是仓库监控告警主管模型。"
                    "请基于工具对比结果与视觉分析结果，生成最终告警报告。"
                    "如果无显著差异，输出“无告警”并给出简要理由；"
                    "如果有显著差异，输出完整告警报告。"
                )
            ),
            HumanMessage(
                content=(
                    "请生成仓库监控告警报告（Markdown格式）。\n"
                    f"基础图路径: {state['basic_image_path']}\n"
                    f"实时图路径: {state['comparison_image_path']}\n\n"
                    f"工具对比结果:\n{compare_info}\n\n"
                    f"Qwen视觉分析结果:\n{qwen_analysis or '无（未触发视觉深度分析）'}\n\n"
                    "报告必须包含：告警级别、差异摘要、是否存在物品移动、是否存在物品丢失、处置建议。"
                )
            ),
        ]
    )
    return {"messages": [res], "alert_report": _normalize_content(res.content)}


def route_after_compare(state: MessagesState) -> str:
    if state.get("difference_found"):
        return "qwen_llm_call"
    return "ds_generate_alert_call"


workflow = StateGraph(MessagesState)
workflow.add_node("ds_llm_call", ds_llm_call)
workflow.add_node("compare_tool_call", compare_tool_call)
workflow.add_node("qwen_llm_call", qwen_llm_call)
workflow.add_node("ds_generate_alert_call", ds_generate_alert_call)
workflow.add_edge(START, "ds_llm_call")
workflow.add_edge("ds_llm_call", "compare_tool_call")
workflow.add_conditional_edges(
    "compare_tool_call",
    route_after_compare,
    {
        "qwen_llm_call": "qwen_llm_call",
        "ds_generate_alert_call": "ds_generate_alert_call",
    },
)
workflow.add_edge("qwen_llm_call", "ds_generate_alert_call")
workflow.add_edge("ds_generate_alert_call", END)
surveillance_graph = workflow.compile()


def run_surveillance_agent(
    basic_image_path: str,
    comparison_image_path: str,
) -> str:
    result = surveillance_graph.invoke(
        {
            "messages": [],
            "basic_image_path": basic_image_path,
            "comparison_image_path": comparison_image_path,
        }
    )
    return result.get("alert_report", "")
