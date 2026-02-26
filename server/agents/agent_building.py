from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
import os

# 千文 视觉理解大模型推荐
# qwen3.5-plus  qwen3-vl-plus  qwen-vl-max
model = ChatOpenAI(
    model="qwen3.5-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)



agent = create_agent(
    model,
    name="research_assistant",
    system_prompt="你是一个建筑进度查询智能体，用于查询建筑进度，包括已完成、未开始、进行中的项目",
)

response = agent.invoke(
    {"messages": [HumanMessage(content="查询已完成的项目")]},
)
print(response)
