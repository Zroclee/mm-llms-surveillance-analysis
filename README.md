# mm-llms-surveillance-analysis
基于多模态大模型的实时监控视频异常分析和溯源系统


## 项目框架

- server - 后端服务，基于Python + FastApi + LangChain + OpenAI + Qwen VL
- web - 前端，Vue3 + Vite + TS


## 项目初始化

```bash
# 初始化步骤
mkdir server
python3 -m venv .venv
source .venv/bin/activate


# 直接安装 FastAPI 及所有可选依赖
pip install "fastapi[all]"
# LangChain
pip install -U langchain
pip install -U langchain-openai
pip install -U langgraph

# 将依赖库保存
pip freeze > requirements.txt

# 后续项目启动
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 前端初始化
pnpm create vite@latest
cd web
pnpm install
pnpm run dev
```

## 智能体设计

### 异常监控智能体
用于识别监控异常，并提供异常视频分析


### 建筑进度智能体
用于查询建筑进度，包括已完成、未开始、进行中的项目


### 卫星地图识别智能体
基于多模态大模型识别卫星地图上某个建筑工地的当前进展。

如果仅仅提供API的话怎么去通过API获取地图瓦片数据并提取成图片。

高德卫星地图是否提供时间

基于google地图的[水经注 GIS 地图](https://rivermap.cn/)

高德的[坐标拾取器](https://lbs.amap.com/tools/picker)可以根据地址获取经纬度


## 监控摄像头

内网搭建 GB28181 SIP服务
 
海康威视SDK

已经接入海康互联，直接使用海康威视云服务 如何视频流接入内网？