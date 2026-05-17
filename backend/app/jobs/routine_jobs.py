"""定时巡检调度器"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

scheduler = AsyncIOScheduler()

async def weekly_routine_check():
    """每周五收盘后执行持仓巡检"""
    from app.core.database import get_job_db
    from app.services.routine_service import RoutineService
    db, client = await get_job_db()
    try:
        svc = RoutineService(db)
        holdings = await db["trades"].aggregate([
            {"$group": {"_id": "$ts_code", "name": {"$first": "$name"}}}
        ]).to_list(None)
        for h in holdings:
            try:
                rid = await svc.run_routine("default", h["_id"], h.get("name", ""))
                print(f"巡检: {h['_id']} → {rid[:8]}")
            except Exception as e:
                print(f"巡检失败 {h['_id']}: {e}")
    finally:
        client.close()


async def daily_news_sync():
    """每天同步新闻"""
    from app.jobs.sync_news import sync_all_news
    await sync_all_news()


def start_scheduler():
    scheduler.add_job(weekly_routine_check, "cron", day_of_week="fri", hour=17, minute=0, id="weekly_check")
    scheduler.add_job(daily_news_sync, "cron", hour="8,12,18", minute=10, id="daily_news_sync")
    scheduler.start()
    print("✅ 定时巡检调度器已启动 (含新闻同步: 8:10/12:10/18:10)")
