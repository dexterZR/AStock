import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_db
from app.models.response import BaseResponse
from app.models.llm_config import LLMConfigRequest, LLMConfigResponse, LLMTestResponse, mask_api_key, is_masked_key

router = APIRouter(prefix="/api/llm-config", tags=["LLM配置"])


@router.get("")
async def get_llm_config(db: AsyncIOMotorDatabase = Depends(get_db)):
    config = await db["llm_config"].find_one({"is_active": True}, {"_id": 0})
    if not config:
        return BaseResponse(data=None)
    config["api_key"] = mask_api_key(config.get("api_key", ""))
    config["updated_at"] = config.get("updated_at", "").isoformat() if isinstance(config.get("updated_at"), datetime) else config.get("updated_at", "")
    return BaseResponse(data=config)


@router.put("")
async def save_llm_config(
    req: LLMConfigRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    update_doc = {
        "name": req.name,
        "base_url": req.base_url,
        "model": req.model,
        "is_active": True,
        "updated_at": datetime.now(),
    }
    if req.api_key and not is_masked_key(req.api_key):
        update_doc["api_key"] = req.api_key

    existing = await db["llm_config"].find_one({"is_active": True})
    if existing and is_masked_key(req.api_key):
        update_doc["api_key"] = existing.get("api_key", "")
    elif not existing and is_masked_key(req.api_key):
        return BaseResponse(success=False, message="首次配置请输入完整的 API Key")

    await db["llm_config"].update_one(
        {"is_active": True},
        {"$set": update_doc},
        upsert=True,
    )
    return BaseResponse(data={"name": req.name}, message="配置已保存")


@router.post("/test")
async def test_llm_connection(db: AsyncIOMotorDatabase = Depends(get_db)):
    config = await db["llm_config"].find_one({"is_active": True}, {"_id": 0})
    if not config or not config.get("api_key"):
        return BaseResponse(data=LLMTestResponse(success=False, message="未配置 LLM，请先保存配置"))

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=config["api_key"],
            base_url=config.get("base_url", ""),
        )
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.chat.completions.create,
                model=config.get("model", ""),
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
                temperature=0,
            ),
            timeout=10.0,
        )
        if response and response.choices:
            return BaseResponse(data=LLMTestResponse(success=True, message="连接成功"))
        return BaseResponse(data=LLMTestResponse(success=False, message="连接成功但未返回有效响应"))
    except asyncio.TimeoutError:
        return BaseResponse(data=LLMTestResponse(success=False, message="连接超时(10s)，请检查 Base URL 是否正确"))
    except Exception as e:
        err_msg = str(e)
        if "auth" in err_msg.lower() or "401" in err_msg or "api_key" in err_msg.lower():
            return BaseResponse(data=LLMTestResponse(success=False, message="认证失败：API Key 无效"))
        if "model" in err_msg.lower() or "not found" in err_msg.lower():
            return BaseResponse(data=LLMTestResponse(success=False, message=f"模型不存在：{config.get('model', '')}"))
        return BaseResponse(data=LLMTestResponse(success=False, message=f"连接失败：{err_msg[:100]}"))
