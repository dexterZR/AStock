from fastapi import APIRouter, Depends
from typing import List
from app.models.response import BaseResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_db

router = APIRouter(prefix="/api/watchlist", tags=["自选股"])


@router.get("")
async def get_watchlist(db: AsyncIOMotorDatabase = Depends(get_db)):
    data = await db["watchlists"].find_one({"user_id": "default"})
    if not data:
        return BaseResponse(data={"stocks": []})
    return BaseResponse(data={"stocks": data.get("stocks", [])})


@router.post("/{ts_code}")
async def add_stock(ts_code: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    await db["watchlists"].update_one(
        {"user_id": "default"},
        {"$addToSet": {"stocks": ts_code}},
        upsert=True,
    )
    return BaseResponse(data={"added": ts_code})


@router.delete("/{ts_code}")
async def remove_stock(ts_code: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    await db["watchlists"].update_one(
        {"user_id": "default"},
        {"$pull": {"stocks": ts_code}},
    )
    return BaseResponse(data={"removed": ts_code})
