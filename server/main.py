
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

from router import agent, files, video

app.include_router(agent.router)
app.include_router(video.router)
app.include_router(files.router)


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
