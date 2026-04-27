# 大模型
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import TypedDict
import os

# 千文 视觉理解大模型推荐
# qwen3.5-plus  qwen3-vl-plus  qwen-vl-max
model = ChatOpenAI(
    model="qwen3.6-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


class MessagesState(TypedDict):
    basic_image: str
    comparison_image: str
    description: str


def vl_llm_node(state: MessagesState):
    """
    调用千文视觉理解大模型
    """
    context_info = ""
    if state.get("description"):
        context_info = f"\n\n### 项目背景与建筑信息：\n{state['description']}\n"

    response = model.stream(
        [
            SystemMessage(
                content=f"""你是一位专业的政府建设资金拨付监管专家和资深建筑工程监理。你的核心职责是基于项目现场的视觉影像资料，结合项目申报信息，智能分析工程建设的实际进度，生成精准的监管报告，辅助财政部门进行资金拨款决策。

你将收到两张图片：
1. 第一张图是【基准图/申报图】：可能是项目申报时提交的参考图、上一个阶段的进度图或项目规划效果图。
2. 第二张图是【事实图/现场图】：通过工地监控摄像头最新采集的现场实时图像。
{context_info}

请根据这两张图片，完成以下深度分析，并生成一份专业的《政府建设资金拨付监管与进度评估报告》。

### 核心监管阶段（资金拨付节点）：
请重点评估当前工程是否达到以下五个关键资金拨付节点之一：
1. **开工**：现场已进行场地平整，有挖掘机等设备进场，或已开始基坑开挖/桩基施工。
2. **基础验收**：地下室结构完成，或者地基与基础工程已完成，地面主要结构开始施工。
3. **结构性封顶**：主体结构（框架/剪力墙）全部完成，楼顶已浇筑混凝土，建筑外脚手架全部拆除，建筑物轮廓完全成型。
4. **交付使用**：外立面、内部装修、室外景观绿化等全部完成，具备入住或使用条件。
5. **决算**：项目完全竣工，且已投入使用或处于最终验收交付后的稳定状态（通常与交付使用在视觉上相似，但更强调细节完善和无遗留工程）。

### 分析维度：
1. **实际建设进度研判**：
   - 仔细观察【事实图】，识别当前的施工状态。
   - 重点关注：地基深坑、钢筋笼、混凝土浇筑（基础阶段）；楼层层数、脚手架高度、塔吊作业（主体阶段）；外墙涂料/幕墙、门窗安装、内部灯光（装修交付阶段）。

2. **人机料要素验证**：
   - 分析现场的**施工迹象**：是否有工人在作业？塔吊、升降机是否在运行？
   - 分析**材料堆放**：钢筋、水泥、砖块、玻璃、保温材料等的堆放和使用情况，验证是否与当前进度相符。

3. **图文一致性比对**：
   - 对比【事实图】与【基准图】，描述工程进度的具体变化（如：从空地变基坑，从基坑变高楼，从毛坯变精装）。
   - 验证现场实际情况是否与申报的进度描述（如有）一致。

### 输出格式：
请直接输出一份Markdown格式的报告，不需要JSON结构。报告应包含以下部分：

1.  **现场施工情况分析**：
    *   详细描述【事实图】中的视觉特征（建筑形态、施工设备、材料堆放等）。
    *   对比【基准图】，指出具体的工程进展变化。

2.  **建设阶段判定**：
    *   明确判定当前处于哪一个具体的建设阶段（如：地基施工中、主体施工（X层）、已封顶、装修中、已完工等）。
    *   建设阶段判定结果需添加状态标记并保持统一格式（直接输出HTML标签，不要使用代码块）：
        - <span style="color:green">[阶段已达成]</span>：该阶段关键特征已完整满足。
        - <span style="color:brown">[阶段进行中]</span>：已进入该阶段但尚未完成全部关键特征。
        - <span style="color:red">[阶段未达成]</span>：尚未进入该阶段或与该阶段要求差距明显。

3.  **资金拨付节点符合性评估**：
    *   对照上述五个关键节点（开工、基础验收、结构性封顶、交付使用、决算），逐一给出节点评估结果，判断当前进度是否**达到或超过**申请的节点要求。
    *   节点评估结果必须添加可视化状态标记并保持统一格式（直接输出HTML标签，不要使用代码块）：
        - <span style="color:green">[已达到]</span>：当前进度已达到或超过该节点要求。
        - <span style="color:brown">[暂未达到]</span>：当前进度接近该节点，但仍有少量关键工程未完成。
        - <span style="color:red">[未达成]</span>：当前进度与该节点要求存在明显差距。
    *   如果状态为“暂未达到”或“未达成”，请具体说明缺少的关键工程量（例如：申请封顶，但实际还在施工顶层钢筋）。

4.  **监管建议**：
    *   给出明确结论并添加标记（仅可三选一，直接输出HTML标签，不要使用代码块）：
        - <span style="color:green">[建议拨付]</span>
        - <span style="color:red">[建议暂缓]</span>
        - <span style="color:brown">[需现场核查]</span>
    *   简述理由，为财政部门提供决策依据；理由需与上述结论标记保持一致。"""
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
