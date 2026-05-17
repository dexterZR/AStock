from fastapi import APIRouter, Depends
from app.models.response import BaseResponse
from app.models.checklist import PreTradeChecklist
from app.api.deps import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

router = APIRouter(prefix="/api/checklist", tags=["交易检查"])


@router.post("/validate")
async def validate_checklist(body: PreTradeChecklist, db: AsyncIOMotorDatabase = Depends(get_db)):
    errors = []
    warnings = []

    # 校验
    if len(body.buy_reason or "") < 10:
        errors.append("买入理由至少10字")
    if body.stop_loss_price >= body.target_price and body.target_price:
        errors.append("止损价不能高于目标价")
    if body.position_ratio > 50:
        errors.append("单票仓位不能超过50%")
    if not body.contrarian_check:
        errors.append("请确认非冲动交易")

    ts_code = body.stock_code
    if ts_code:
        latest = await db["daily_quotes"].find_one(
            {"ts_code": ts_code, "adjust_flag": "none"}, sort=[("trade_date", -1)]
        )
        if latest and latest.get("turnover_rate", 0) > 20:
            warnings.append("换手率超过20%，注意异常波动风险")

    return BaseResponse(data={"valid": len(errors) == 0, "errors": errors, "warnings": warnings})


@router.post("/submit")
async def submit_checklist(body: PreTradeChecklist, db: AsyncIOMotorDatabase = Depends(get_db)):
    errors = []
    if len(body.buy_reason or "") < 10:
        errors.append("买入理由至少10字")
    if not body.contrarian_check:
        errors.append("请确认非冲动交易")
    if errors:
        return BaseResponse(data={"success": False, "errors": errors})

    doc = body.model_dump()
    doc["created_at"] = datetime.now().isoformat()
    result = await db["checklists"].insert_one(doc)

    decision = {
        "stock_code": body.stock_code, "stock_name": body.stock_name,
        "action": "CHECKLIST_PASSED",
        "content": f"买入前检查通过。理由: {body.buy_reason}。止损: {body.stop_loss_price}。仓位: {body.position_ratio}%",
        "created_at": datetime.now().isoformat(),
    }
    dec_result = await db["decisions"].insert_one(decision)
    return BaseResponse(data={"success": True, "checklist_id": str(result.inserted_id), "decision_id": str(dec_result.inserted_id)})


@router.get("/status/{stock_code}")
async def check_status(stock_code: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """检查24小时内是否已通过checklist"""
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    doc = await db["checklists"].find_one({
        "stock_code": stock_code,
        "created_at": {"$gte": cutoff},
    }, sort=[("created_at", -1)])
    return BaseResponse(data={"passed": doc is not None})
