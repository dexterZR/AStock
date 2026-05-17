from fastapi import APIRouter, Depends, Query
from app.models.response import BaseResponse
from app.services.routine_service import RoutineService
from app.api.deps import get_db
from app.models.routine import RoutineRunRequest
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api/routines", tags=["巡检"])


async def get_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> RoutineService:
    return RoutineService(db)


@router.get("/templates")
async def get_templates(service: RoutineService = Depends(get_service)):
    data = await service.get_templates()
    return BaseResponse(data=data)


@router.post("/run")
async def run_routine(body: RoutineRunRequest, service: RoutineService = Depends(get_service)):
    result_id = await service.run_routine(
        template_id=body.template_id,
        stock_code=body.stock_code,
        stock_name=body.stock_name,
    )
    return BaseResponse(data={"result_id": result_id, "status": "running"})


@router.get("/results/{result_id}")
async def get_result(result_id: str, service: RoutineService = Depends(get_service)):
    data = await service.get_result(result_id)
    return BaseResponse(data=data)


@router.get("/history")
async def get_history(stock_code: str = Query(...), limit: int = 10, service: RoutineService = Depends(get_service)):
    data = await service.get_history(stock_code, limit)
    return BaseResponse(data=data)
