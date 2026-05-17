import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def seed_portfolio():
    from app.core.config import settings
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client["stock_analysis"]

    await db["trades"].delete_many({})
    await db["stock_events"].delete_many({})
    await db["risk_alerts"].delete_many({})
    await db["decision_logs"].delete_many({})

    await db["trades"].insert_one({
        "ts_code": "600703.SH",
        "name": "三安光电",
        "action": "buy",
        "price": 14.0,
        "shares": 10000,
        "total_amount": 140000.0,
        "trade_date": "20260115",
        "decision_logic": "光模块/磷化铟赛道，成本14元附近建仓，看好化合物半导体长期逻辑。实控人事件导致超跌，认为风险已price in。",
        "emotion": "calm",
        "market_view": "市场处于震荡期，光通信板块有业绩支撑",
        "target_price": 20.0,
        "stop_loss": 12.5,
        "tags": ["光通信", "化合物半导体", "超跌反弹", "全仓"],
        "created_at": datetime.now().isoformat(),
    })

    events = [
        {"ts_code":"600703.SH","name":"三安光电","event_type":"留置","event_date":"20260315","title":"实控人林秀成被采取留置措施","content":"公司实控人、董事长林秀成因涉嫌违法被监察机关采取留置措施。","source":"公司公告","severity":"critical","is_resolved":False,"impact_assessment":"实控人被查对公司治理和融资能力构成重大不确定性"},
        {"ts_code":"600703.SH","name":"三安光电","event_type":"冻结","event_date":"20260320","title":"控股股东股份93.68%被轮候冻结","content":"控股股东三安集团及其一致行动人所持股份被轮候冻结，占其持股的93.68%。","source":"公司公告","severity":"critical","is_resolved":False,"impact_assessment":"股份冻结意味着控股股东无法减持或质押融资，流动性受限"},
        {"ts_code":"600703.SH","name":"三安光电","event_type":"减持","event_date":"20260501","title":"控股股东5月累计减持1.66%","content":"控股股东在5月通过大宗交易累计减持1.66%股份。","source":"交易所披露","severity":"warning","is_resolved":False,"impact_assessment":"连续减持显示控股股东资金需求紧张"},
        {"ts_code":"600703.SH","name":"三安光电","event_type":"业绩","event_date":"20260430","title":"Q1净利润同比下降68%","content":"一季度归母净利润同比下降68%，净利率降至2.48%。","source":"财报","severity":"warning","is_resolved":True,"impact_assessment":"业绩大幅下滑，LED芯片价格战持续"},
        {"ts_code":"600703.SH","name":"三安光电","event_type":"大订单","event_date":"20260510","title":"子公司获某车企SiC订单","content":"湖南三安获某头部新能源汽车客户SiC功率器件订单，金额未披露。","source":"行业消息","severity":"info","is_resolved":True,"impact_assessment":"SiC业务有突破，但订单金额不明，需观察"},
    ]

    for event in events:
        await db["stock_events"].insert_one(event)
        if event["severity"] in ["warning", "critical"] and not event["is_resolved"]:
            await db["risk_alerts"].insert_one({
                "ts_code": event["ts_code"], "name": event["name"],
                "alert_type": "event",
                "alert_level": "high" if event["severity"] == "critical" else "medium",
                "title": f"[{event['event_type']}] {event['title']}",
                "description": event["content"],
                "triggered_at": datetime.now().isoformat(),
                "is_acknowledged": False,
                "related_event_id": str(event.get("_id", "")),
            })

    print("✅ 持仓和事件数据初始化完成")
    print("  - 三安光电买入：成本14元，10000股")
    print("  - 风险事件：留置/冻结/减持/业绩")
    print("  - 3条未确认风险预警")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_portfolio())
