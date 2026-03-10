# 大模型
from langchain_openai import ChatOpenAI
import os

qwen_model = ChatOpenAI(
    model="qwen3.5-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.7,
)

ds_model = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0.7,
)

# 工具


# 状态
from typing_extensions import Annotated, TypedDict
from pydantic import BaseModel, Field
class surveillance_state(TypedDict):
    """ surveillance state """
    messages: Annotated[list, Field(default_factory=list)]
    


from langgraph.graph.message import MessageState


# 节点
def qwen_llm_call(state: MessageState) -> MessageState:
    """调用千文模型"""
    # 从状态中获取消息
    messages = state["messages"]
    
    # 调用千文模型
    response = qwen_model.invoke(messages)
    
    return {'messages': [response]}


# 智能体构建
from langgraph.graph import StateGraph, START, END
agent_builder = StateGraph(MessageState)
