"""定时数据同步调度器"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from datetime import datetime

scheduler = AsyncIOScheduler()


async def startup_data_check():
    """启动时检查数据新鲜度，如需要则执行增量同步"""
    from app.core.database import get_job_db

    db, client = await get_job_db()
    try:
        # 检查最近一个交易日是否有数据
        latest = await db["daily_quotes"].find_one(
            {"adjust_flag": "none"},
            {"trade_date": 1},
            sort=[("trade_date", -1)],
        )

        today_str = datetime.now().strftime("%Y%m%d")
        need_sync = False

        if not latest:
            print("⚠️ 数据库中无行情数据，启动首次全量同步...")
            need_sync = True
        else:
            last_date = str(latest.get("trade_date", ""))
            # 检查最新日期的数据量是否完整（至少1000只股票才算有效同步）
            stock_count = await db["daily_quotes"].count_documents(
                {"adjust_flag": "none", "trade_date": last_date}
            )
            total_stocks = await db["stocks"].count_documents({})

            print(f"📊 最新数据日期：{last_date}（{stock_count}/{total_stocks}只），今天：{today_str}")

            # 数据落后或数据量不完整时触发同步
            if last_date < today_str:
                from datetime import datetime as dt
                weekday = dt.now().weekday()
                if weekday < 5:
                    print(f"⚠️ 数据落后（{last_date} → {today_str}），启动增量同步...")
                    need_sync = True
                else:
                    print(f"📅 今天是周末，最新数据 {last_date} 无需更新")
            elif stock_count < 1000:
                print(f"⚠️ 数据量不足（仅{stock_count}只），可能是部分同步，重新全量拉取...")
                need_sync = True
            else:
                print(f"✅ 数据已是最新且完整（{last_date}，{stock_count}只）")

        if need_sync:
            try:
                print("🔄 开始启动时数据同步...")
                await daily_data_pipeline()
                print("✅ 启动时数据同步完成")
            except Exception as e:
                print(f"❌ 启动时数据同步失败: {e}")
    finally:
        client.close()


async def daily_data_pipeline():
    """每日收盘后完整数据同步流水线（行情+基本面并行执行）"""
    print("🔄 ===== 每日数据同步流水线开始 =====")

    async def _sync_quotes():
        try:
            from app.jobs.sync_daily import sync_daily_quotes
            print("  [1/4] 同步日K线行情...")
            await sync_daily_quotes()
            print("  [1/4] ✅ 日K线同步完成")
        except Exception as e:
            print(f"  [1/4] ❌ 日K线同步失败: {e}")

    async def _sync_fundamentals():
        try:
            from app.jobs.sync_fundamentals import run as sync_fundamentals
            print("  [2/4] 同步基本面数据...")
            await sync_fundamentals()
            print("  [2/4] ✅ 基本面同步完成")
        except Exception as e:
            print(f"  [2/4] ❌ 基本面同步失败: {e}")

    # Step 1 & 2 可并行（行情 + 基本面）
    await asyncio.gather(_sync_quotes(), _sync_fundamentals())

    # Step 3 依赖 Step 1
    try:
        from app.jobs.compute_indicators import compute_and_save_indicators
        print("  [3/4] 计算技术指标...")
        await compute_and_save_indicators()
        print("  [3/4] ✅ 技术指标计算完成")
    except Exception as e:
        print(f"  [3/4] ❌ 技术指标计算失败: {e}")

    # Step 4 依赖 Step 3
    try:
        from app.jobs.compute_screener_signals import run as compute_signals
        print("  [4/4] 计算筛选信号...")
        await compute_signals()
        print("  [4/4] ✅ 筛选信号计算完成")
    except Exception as e:
        print(f"  [4/4] ❌ 筛选信号计算失败: {e}")

    print("🔄 ===== 每日数据同步流水线结束 =====")

    # 快照和缓存刷新
    try:
        from app.jobs.build_snapshot import build_snapshot, build_market_stats
        print("  [快照] 构建筛选快照...")
        await build_snapshot()
        print("  [快照] 构建市场统计缓存...")
        await build_market_stats()
        print("  [快照] ✅ 快照构建完成")
    except Exception as e:
        print(f"  [快照] ❌ 快照构建失败: {e}")

    # 选择性清除缓存（只清 cache: 前缀的 key，不清 ratelimit/session 等）
    try:
        import redis.asyncio as aioredis
        from app.core.config import settings
        from app.infrastructure.cache import CACHE_PREFIX
        r = aioredis.from_url(settings.REDIS_URL)
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await r.scan(cursor=cursor, match=f"{CACHE_PREFIX}*", count=500)
            if keys:
                await r.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        await r.close()
        print(f"  [缓存] 已清除 {deleted} 个缓存 key")
    except Exception as e:
        print(f"  [缓存] 清除缓存失败 (非致命): {e}")


async def daily_news_sync():
    """每天同步新闻"""
    try:
        from app.jobs.sync_news import sync_all_news
        await sync_all_news()
    except Exception as e:
        print(f"  新闻同步失败: {e}")


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


async def sync_stock_events_10d():
    """每10天同步一次风险事件"""
    try:
        from app.jobs.sync_stock_events import run as sync_events
        await sync_events()
    except Exception as e:
        print(f"  风险事件同步失败: {e}")


def start_scheduler():
    scheduler.add_job(
        daily_data_pipeline, "cron",
        day_of_week="mon-fri", hour=16, minute=0,
        id="daily_data_pipeline",
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        daily_news_sync, "cron",
        hour="8,12,18", minute=10,
        id="daily_news_sync",
        misfire_grace_time=1800,
    )
    scheduler.add_job(
        weekly_routine_check, "cron",
        day_of_week="fri", hour=17, minute=0,
        id="weekly_check",
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        sync_stock_events_10d, "interval", days=10,
        id="sync_stock_events_10d",
        misfire_grace_time=86400,
    )
    scheduler.start()
    print("✅ 定时调度器已启动:")
    print("   - 每日数据流水线: 周一至周五 16:00 (日K线→基本面→指标→信号)")
    print("   - 风险事件同步: 每10天一次")
    print("   - 新闻同步: 每天 8:10/12:10/18:10")
    print("   - 持仓巡检: 每周五 17:00")
