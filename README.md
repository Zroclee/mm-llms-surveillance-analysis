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

# 前端初始化
pnpm create vite@latest
cd web
pnpm install
pnpm run dev
```

## 后管服务

main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
load_dotenv()


app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中，应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

@app.get("/")
async def root():
    return "Hello, World!"

import uvicorn 
if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
```


