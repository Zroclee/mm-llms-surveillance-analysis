# 大模型
from langchain_openai import ChatOpenAI
import os

# 千文 视觉理解大模型推荐
# qwen3.5-plus  qwen3-vl-plus  qwen-vl-max
model = ChatOpenAI(
    model="qwen3.5-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

model.invoke(
    [
        SystemMessage(
            content="你是一名安全专家，现在正在监控一家仓库的安全情况。我会给出两个监控图片，第一张为仓库的原始图像，第二张为仓库的当前图像。请仔细对比两张图片，如第二张监控画面存在异常情况，如物品减少，出现异常人员，请给出相应的解释。"
        ),
        HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{state['basic_image']}",
                    },
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{state['comparison_image']}",
                    },
                },
            ]
        ),
    ]
)

# # 定义状态
# from typing_extensions import TypedDict
# from pydantic import BaseModel, Field
# class MessagesState(TypedDict):
#     basic_image: str
#     comparison_image: str
#     vl_llm_res: str
#     anomaly_type: AnomalyType = Field(description="异常类型")
#     risk_level: RiskLevel = Field(description="风险等级")
#     final_result: str = Field(description="最终判断结果")
#     recommendations: str = Field(description="建议采取的措施")

# # 定义节点
# def model_call_node(state: MessagesState) -> MessagesState:
#     """
#     调用大模型
#     """
#     # 调用大模型
#     response = model.invoke(state["messages"])
#     # 更新状态
#     state["messages"].append(response)
#     return state


# # 定义图
# from langgraph.graph import StateGraph, START, END

# graph = StateGraph(MessagesState)

# agent = graph.compile()
