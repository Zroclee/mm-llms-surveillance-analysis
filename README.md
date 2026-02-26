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



