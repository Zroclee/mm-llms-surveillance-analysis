import os
import time
import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/video",
    tags=["video"],
)

# 缓存 AccessToken
_access_token = None
_token_expire_time = 0

async def get_access_token():
    global _access_token, _token_expire_time
    
    current_time = time.time() * 1000
    if _access_token and current_time < _token_expire_time:
        return _access_token
        
    app_key = os.getenv("YS_APP_KEY")
    app_secret = os.getenv("YS_APP_SECRET")
    
    if not app_key or not app_secret:
        raise HTTPException(status_code=500, detail="缺少 YS_APP_KEY 或 YS_APP_SECRET 环境变量")
        
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://open.ys7.com/api/lapp/token/get",
            data={
                "appKey": app_key,
                "appSecret": app_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        data = response.json()
        if data.get("code") == "200":
            _access_token = data["data"]["accessToken"]
            expire_val = data["data"]["expireTime"]
            
            # 判断 expireTime 是绝对时间戳还是相对秒数
            # 1000000000000 毫秒对应的是 2001-09-09，目前的毫秒时间戳在 1700000000000 左右
            if expire_val > 1000000000000: # 绝对时间戳 (毫秒)
                _token_expire_time = expire_val - 300000 # 提前5分钟过期
            else: # 相对秒数
                _token_expire_time = current_time + (expire_val - 300) * 1000
            
            return _access_token
        else:
            raise HTTPException(status_code=500, detail=f"获取Token失败: {data.get('msg', data.get('message', '未知错误'))}")


async def get_video_url(token: str):
    
    device_serial = os.getenv("YS_DEVICE_SERIAL")
    channel_no = os.getenv("YS_CHANNEL_NO")
    device_code = os.getenv("YS_DEVICE_CODE")
    
    if not device_serial or not channel_no:
        raise HTTPException(status_code=500, detail="缺少设备序列号或通道号")
    
    protocols = [
        {"protocol": "1", "name": "ezopen"},
        {"protocol": "2", "name": "hls"}
    ]
    
    async with httpx.AsyncClient() as client:
        for p in protocols:
            try:
                response = await client.post(
                    "https://open.ys7.com/api/lapp/v2/live/address/get",
                    data={
                        "accessToken": token,
                        "deviceSerial": device_serial,
                        "channelNo": channel_no,
                        "protocol": p["protocol"],
                        "quality": "1",
                        "type": "1",
                        "expireTime": "86400",
                        "code": device_code or ""
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                data = response.json()
                if data.get("code") == "200":
                    return data["data"]["url"]
                elif data.get("code") == "60019":
                    # 协议加密错误，继续尝试下一个
                    continue
            except Exception as e:
                print(f"协议 {p['name']} 错误: {e}")
                
    raise HTTPException(status_code=500, detail="所有协议都无法获取视频地址，设备可能需要关闭视频加密")

@router.get("/")
async def get_video():
    try:
        token = await get_access_token()
        url = await get_video_url(token)
        return {"success": True, "url": url, "accessToken": token}
    except HTTPException as e:
        # FastAPI 会自动处理 HTTPException 并返回对应状态码
        raise e
    except Exception as e:
        return {"success": False, "message": str(e)}

        
