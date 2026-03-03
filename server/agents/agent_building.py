# 大模型
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import TypedDict
import os

# 千文 视觉理解大模型推荐
# qwen3.5-plus  qwen3-vl-plus  qwen-vl-max
model = ChatOpenAI(
      model="qwen3.5-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


class MessagesState(TypedDict):
    basic_image: str
    comparison_image: str


def vl_llm_node(state: MessagesState):
    """
    调用千文视觉理解大模型
    """
    response = model.invoke(
        [
            SystemMessage(
                content="""你是一位经验丰富的房地产贷款放款经理和建筑工程监理专家。你的职责是根据建筑工地的图片来评估施工进度，以决定是否符合放款条件。

你将收到两张图片：
1. 第一张图是【基准图】：可能是项目早期的状态、上一个周期的进度图或项目规划图，作为参考基准。
2. 第二张图是【事实图】：当前最新的建筑工地现场拍摄图。

请根据这两张图片，完成以下分析并生成一份专业的《建筑进度监察与放款评估报告》。

### 分析维度：
1. **当前建设阶段判断**：
   - 仔细观察【事实图】，判断当前建筑处于哪个阶段（例如：土地平整、地基施工、主体结构施工（层数）、封顶、二次结构、外立面施工、内部装修、竣工验收等）。
   - 依据：请结合可见的建筑形态（如基坑、桩基、梁柱、墙体、门窗等）进行判断。

2. **建筑材料与施工迹象分析**：
   - 观察现场的建筑材料（如：钢筋、混凝土、模板、脚手架、砖块、玻璃、保温材料等）。
   - 观察施工设备（如：塔吊、挖掘机、升降机等）的状态。
   - 通过材料和设备的使用情况，佐证你对建设阶段的判断。

3. **进度对比与变化**：
   - 对比【事实图】与【基准图】，详细描述可见的工程进度变化。
   - 指出新增的建设内容。

4. **关键节点达成情况**：
   - 明确判断当前进度是否达到了关键放款节点。常见的关键节点包括：
     - 完成地基工程
     - 主体建设过半
     - 主体结构封顶
     - 完成建筑外立面
     - 竣工备案

### 输出格式：
请直接输出一份Markdown格式的报告，不需要JSON结构。报告应包含以下部分：

1.  **详细的进度分析与对比描述**：
    *   详细描述【事实图】中观察到的施工情况。
    *   对比【基准图】，指出具体的进度变化和新增建设内容。
    *   描述现场的**施工迹象**（如设备运行、工人作业等）和**建筑材料**（如钢筋、混凝土、脚手架等）的使用情况，作为判断依据。

2.  **建设阶段判断**：
    *   根据上述分析，明确判定当前建筑处于哪个具体的建设阶段。

3.  **关键节点达成情况**：
    *   明确说明是否达成了关键放款节点（如地基完成、主体过半、封顶等）。
    *   如果未达成，请说明目前距离下一节点还差哪些工作。

4.  **放款建议**：
    *   给出明确的结论：**建议放款** / **建议暂缓** / **需要进一步核查**。
    *   简要说明理由，支持你的建议。"""
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
    return response


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
