"""持仓预警自动检测：基于行情异动、技术信号、资金流向自动生成预警"""
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.database import get_job_db


ALERT_DEDUPE_HOURS = 24


async def detect_holding_alerts():
    db, client = await get_job_db()
    try:
        holdings = await db["trades"].aggregate([
            {"$match": {"action": "buy"}},
            {"$group": {"_id": "$ts_code", "name": {"$first": "$name"}}},
        ]).to_list(None)
        if not holdings:
            print("  [预警检测] 无持仓，跳过")
            return

        ts_codes = [h["_id"] for h in holdings]
        name_map = {h["_id"]: h.get("name", "") for h in holdings}

        cutoff = (datetime.now() - timedelta(hours=ALERT_DEDUPE_HOURS)).isoformat()
        recent_titles = await db["risk_alerts"].distinct(
            "title",
            {"ts_code": {"$in": ts_codes}, "triggered_at": {"$gte": cutoff}},
        )

        new_count = 0

        quotes = await _get_latest_quotes(db, ts_codes)
        new_count += await _check_price_alerts(db, quotes, name_map, recent_titles)

        signals = await _get_latest_signals(db, ts_codes)
        new_count += await _check_signal_alerts(db, signals, name_map, recent_titles)

        print(f"  [预警检测] 检查 {len(ts_codes)} 只持仓，新增 {new_count} 条预警")
    finally:
        client.close()


async def _get_latest_quotes(db, ts_codes):
    pipeline = [
        {"$match": {"ts_code": {"$in": ts_codes}}},
        {"$sort": {"trade_date": -1}},
        {"$group": {"_id": "$ts_code", "latest": {"$first": "$$ROOT"}}},
    ]
    results = await db["daily_quotes"].aggregate(pipeline).to_list(None)
    return {r["_id"]: r["latest"] for r in results}


async def _get_latest_signals(db, ts_codes):
    pipeline = [
        {"$match": {"ts_code": {"$in": ts_codes}}},
        {"$sort": {"trade_date": -1}},
        {"$group": {"_id": "$ts_code", "latest": {"$first": "$$ROOT"}}},
    ]
    results = await db["screener_signals"].aggregate(pipeline).to_list(None)
    return {r["_id"]: r["latest"] for r in results}


async def _insert_alert(db, ts_code, name, alert_level, title, description, source, recent_titles):
    if title in recent_titles:
        return 0
    await db["risk_alerts"].insert_one({
        "ts_code": ts_code,
        "name": name,
        "alert_type": "auto",
        "alert_level": alert_level,
        "title": title,
        "description": description,
        "source": source,
        "triggered_at": datetime.now().isoformat(),
        "is_acknowledged": False,
        "related_event_id": "",
    })
    return 1


async def _check_price_alerts(db, quotes, name_map, recent_titles):
    count = 0
    for ts_code, q in quotes.items():
        name = name_map.get(ts_code, ts_code)
        pct = q.get("pct_change") or q.get("pct_chg") or 0

        if pct <= -7:
            title = f"[暴跌] {name}跌幅达{abs(pct):.1f}%"
            desc = f"{name}({ts_code})今日下跌{abs(pct):.1f}%，收盘价{q.get('close', 0):.2f}，可能存在重大利空或系统性风险。"
            count += await _insert_alert(db, ts_code, name, "high", title, desc, "行情数据", recent_titles)
        elif pct <= -5:
            title = f"[大跌] {name}跌幅达{abs(pct):.1f}%"
            desc = f"{name}({ts_code})今日下跌{abs(pct):.1f}%，收盘价{q.get('close', 0):.2f}，需关注是否有利空消息。"
            count += await _insert_alert(db, ts_code, name, "medium", title, desc, "行情数据", recent_titles)

        if pct >= 9.5:
            title = f"[涨停] {name}涨幅达{pct:.1f}%"
            desc = f"{name}({ts_code})今日涨停，涨幅{pct:.1f}%，收盘价{q.get('close', 0):.2f}。"
            count += await _insert_alert(db, ts_code, name, "medium", title, desc, "行情数据", recent_titles)

        vol = q.get("vol") or q.get("volume") or 0
        if vol > 0:
            pre_vol = q.get("pre_vol") or 0
            if pre_vol > 0 and vol / pre_vol >= 3:
                title = f"[放量] {name}成交量放大{vol/pre_vol:.1f}倍"
                desc = f"{name}({ts_code})今日成交量显著放大，为前一交易日的{vol/pre_vol:.1f}倍，需关注是否有重大消息或资金异动。"
                count += await _insert_alert(db, ts_code, name, "medium", title, desc, "行情数据", recent_titles)

    return count


async def _check_signal_alerts(db, signals, name_map, recent_titles):
    count = 0
    for ts_code, sig in signals.items():
        name = name_map.get(ts_code, ts_code)

        if sig.get("ma_bearish"):
            title = f"[均线空头] {name}均线呈空头排列"
            desc = f"{name}({ts_code})均线呈空头排列（MA5<MA10<MA20），短期趋势偏弱，注意下行风险。"
            count += await _insert_alert(db, ts_code, name, "medium", title, desc, "技术信号", recent_titles)

        if sig.get("rsi_oversold"):
            title = f"[超卖] {name}RSI进入超卖区"
            desc = f"{name}({ts_code})RSI指标进入超卖区域，短期可能存在反弹机会，但也可能继续下行。"
            count += await _insert_alert(db, ts_code, name, "medium", title, desc, "技术信号", recent_titles)

        if sig.get("drop_20d_low"):
            title = f"[破位] {name}跌破20日新低"
            desc = f"{name}({ts_code})跌破20日最低价，短期支撑失守，需关注是否进一步下探。"
            count += await _insert_alert(db, ts_code, name, "high", title, desc, "技术信号", recent_titles)

        if sig.get("boll_breakout_down"):
            title = f"[布林破位] {name}跌破布林下轨"
            desc = f"{name}({ts_code})跌破布林带下轨，短期波动率增大，注意风险。"
            count += await _insert_alert(db, ts_code, name, "medium", title, desc, "技术信号", recent_titles)

    return count

