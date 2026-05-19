from motor.motor_asyncio import AsyncIOMotorDatabase


async def create_indexes(db: AsyncIOMotorDatabase):
    # stocks
    await db["stocks"].create_index("ts_code", unique=True, name="idx_ts_code")
    await db["stocks"].create_index([("industry", 1), ("market", 1)], name="idx_industry_market")
    await db["stocks"].create_index([("name", "text"), ("ts_code", "text")], name="idx_text_search")

    # daily_quotes
    await db["daily_quotes"].create_index(
        [("ts_code", 1), ("trade_date", -1)], unique=True, name="idx_code_date"
    )
    await db["daily_quotes"].create_index(
        [("trade_date", -1), ("pct_change", -1)], name="idx_date_pct"
    )
    await db["daily_quotes"].create_index(
        [("trade_date", -1), ("amount", -1)], name="idx_date_amount"
    )
    await db["daily_quotes"].create_index(
        [("adjust_flag", 1), ("trade_date", -1)], name="idx_adjust_date"
    )

    # screener_signals
    await db["screener_signals"].create_index(
        [("ts_code", 1), ("trade_date", -1)], name="idx_signal_code_date"
    )

    # fundamentals
    await db["fundamentals"].create_index(
        [("ts_code", 1), ("trade_date", -1)], name="idx_fund_code_date"
    )

    # indicators
    await db["indicators"].create_index(
        [("ts_code", 1), ("trade_date", -1)], unique=True, name="idx_ind_code_date"
    )

    # screener_snapshot
    await db["screener_snapshot"].create_index(
        [("ts_code", 1), ("snapshot_date", -1)], unique=True, name="idx_snapshot_code_date"
    )
    await db["screener_snapshot"].create_index(
        [("snapshot_date", -1)], name="idx_snapshot_date"
    )
    await db["screener_snapshot"].create_index(
        [("snapshot_date", -1), ("total_mv", -1)], name="idx_snapshot_date_mv"
    )

    # market_stats
    await db["market_stats"].create_index(
        [("trade_date", -1)], name="idx_stats_date"
    )

    # market_top
    await db["market_top"].create_index(
        [("type", 1), ("trade_date", -1)], name="idx_top_type_date"
    )

    # minute_quotes
    await db["minute_quotes"].create_index(
        [("ts_code", 1), ("period", 1), ("trade_time", -1)],
        unique=True, name="idx_minute_code_period_time"
    )
    await db["minute_quotes"].create_index(
        [("trade_date", 1)],
        expireAfterSeconds=5184000, name="idx_minute_ttl"
    )

    # news
    await db["news"].create_index("url", unique=True, name="idx_news_url")
    await db["news"].create_index([("pub_date", -1)], name="idx_news_pub_date")
    await db["news"].create_index([("heat_score", -1)], name="idx_news_heat")
    await db["news"].create_index("type", name="idx_news_type")
    await db["news"].create_index("related_codes", name="idx_news_related_codes")

    print("✅ MongoDB 索引创建完成")
