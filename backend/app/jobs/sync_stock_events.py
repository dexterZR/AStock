"""同步全市场股票真实风险事件（公告、减持、处罚等）"""
import asyncio
import re
from datetime import datetime, timedelta
from app.core.database import get_job_db

# 公告类型 → (event_type, severity) 映射
EVENT_TYPE_MAP = {
    "股份质押、冻结": ("冻结", "critical"),
    "诉讼仲裁": ("诉讼", "warning"),
    "年报问询函": ("问询", "warning"),
    "问询函": ("问询", "warning"),
    "深交所股票通报批评": ("处罚", "critical"),
    "通报批评": ("处罚", "warning"),
    "回购预案": ("回购", "info"),
    "分配方案决议公告": ("分红", "info"),
    "回复问询函公告": ("问询", "info"),
    # 个股公告特有类型
    "风险提示": ("风险提示", "warning"),
    "持股变动": ("持股变动", "warning"),
    "权益变动报告书": ("持股变动", "warning"),
    "减持": ("减持", "warning"),
    "增持": ("增持", "info"),
    "高管人员任职变动": ("人事", "info"),
    "提供/对外担保公告": ("担保", "warning"),
    "获得补贴（资助）": ("补贴", "info"),
    "投资设立公司": ("投资", "info"),
    "签订协议": ("协议", "info"),
    "关联交易": ("关联交易", "info"),
    "月度经营情况": ("业绩", "info"),
    "回购进展情况": ("回购", "info"),
    "回购完成公告": ("回购", "info"),
    "员工持股计划": ("股权激励", "info"),
    "资产重组": ("重组", "warning"),
    "监管警示": ("监管", "critical"),
}

# 标题关键词兜底 → (event_type, severity)
TITLE_RULES = [
    (r"留置|被查|立案|调查|违法违规|违规", "监管", "critical"),
    (r"冻结|查封|扣押", "冻结", "critical"),
    (r"减持|减持计划|套现", "减持", "warning"),
    (r"增持|增持计划", "增持", "info"),
    (r"亏损|净利润.*下降|净利润.*减少|业绩.*降|营收.*降|预亏", "业绩", "warning"),
    (r"处罚|罚款|警告|谴责", "处罚", "critical"),
    (r"退市|暂停上市|终止上市|摘牌", "退市", "critical"),
    (r"ST|退市风险", "退市", "critical"),
    (r"质押|质押比例|质押率", "质押", "warning"),
    (r"合同纠纷|仲裁|起诉", "诉讼", "warning"),
    (r"债务违约|逾期|兑付|违约", "债务", "critical"),
    (r"股份回购|回购计划", "回购", "info"),
    (r"中标|大订单|重大合同|战略合作|签署.*协议", "大订单", "info"),
    (r"重组|资产注入|借壳|并购", "重组", "warning"),
    (r"分红|派息|利润分配", "分红", "info"),
    (r"人事变动|辞职|聘任|解聘|换届", "人事", "info"),
    (r"异常波动|异动", "交易异动", "info"),
    (r"担保|提供担保|对外担保", "担保", "warning"),
    (r"关联交易", "关联交易", "info"),
    (r"投资设立|对外投资|增资|出资", "投资", "info"),
    (r"补贴|资助|政府补助", "补贴", "info"),
    (r"员工持股|股权激励|期权", "股权激励", "info"),
    (r"监管|警示函|关注函|监管措施", "监管", "warning"),
    (r"风险提示", "风险提示", "warning"),
    (r"逾期|违约|兑付|展期", "债务", "critical"),
    (r"停牌|复牌|停复牌", "停复牌", "warning"),
    (r"被查|滥用|违规", "监管", "critical"),
]


def classify_event(event_type_label: str, title: str) -> tuple:
    """先按公告类型映射，再按标题关键词兜底"""
    # 1. 按公告类型映射
    for key, (etype, severity) in EVENT_TYPE_MAP.items():
        if key in event_type_label:
            return etype, severity
    # 2. 按标题关键词兜底
    for pattern, etype, severity in TITLE_RULES:
        if re.search(pattern, title):
            return etype, severity
    return "公告", "info"


def _ensure_suffix(code: str) -> str:
    """补全交易所后缀"""
    if re.search(r'\.(SH|SZ|BJ|BK)$', code):
        return code
    if code.startswith("6") or code.startswith("9"):
        return f"{code}.SH"
    if code.startswith("0") or code.startswith("3") or code.startswith("2"):
        return f"{code}.SZ"
    if code.startswith("8") or code.startswith("4"):
        return f"{code}.BJ"
    return code


def _parse_date(d: str) -> str:
    d = d.replace("-", "").replace("/", "").strip()
    if len(d) == 8 and d.isdigit():
        return d
    return datetime.now().strftime("%Y%m%d")


async def _sync_individual_notices(db):
    """对全市场每只股票单独获取公告，确保覆盖所有股票"""
    import akshare as ak

    all_stocks = await db["stocks"].distinct("ts_code", {"delist_date": None})
    print(f"  个股公告同步: 共 {len(all_stocks)} 只股票需要检查")

    # 构建去重集合 (已有事件的跳过)
    existing = set()
    cursor = db["stock_events"].find(
        {"source": {"$in": ["akshare", "akshare_individual"]}},
        {"ts_code": 1, "title": 1, "event_date": 1, "_id": 0},
    )
    async for doc in cursor:
        if doc.get("title") and doc.get("event_date"):
            existing.add((doc["ts_code"], doc["title"].strip(), doc["event_date"]))

    print(f"  已有 {len(existing)} 条事件记录用于去重")

    sem = asyncio.Semaphore(5)  # 并发控制
    total_new = 0
    total_skip = 0
    stats = {"critical": 0, "warning": 0, "info": 0}
    ops = []
    cutoff = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")

    # 先处理没有事件覆盖的股票，再处理已有事件的股票
    stocks_with_events = set()
    for key in existing:
        stocks_with_events.add(key[0])
    priority_stocks = [s for s in all_stocks if s not in stocks_with_events]
    remaining = [s for s in all_stocks if s in stocks_with_events]
    ordered = priority_stocks + remaining
    print(f"  其中 {len(priority_stocks)} 只尚未有任何事件")

    async def fetch_notices(ts_code: str):
        nonlocal total_new, total_skip, ops
        symbol = ts_code.split(".")[0]
        try:
            async with sem:
                df = await asyncio.to_thread(
                    ak.stock_individual_notice_report,
                    security=symbol,
                    begin_date=cutoff,
                )
            if df is None or df.empty:
                return
        except Exception:
            return

        for _, row in df.iterrows():
            title = str(row.get("公告标题", "")).strip()
            event_type_label = str(row.get("公告类型", "")).strip()
            pub_date = str(row.get("公告日期", "")).strip()
            name = str(row.get("名称", "")).strip()

            if not title:
                continue

            trade_date = _parse_date(pub_date)
            event_type, severity = classify_event(event_type_label, title)

            key = (ts_code, title, trade_date)
            if key in existing:
                total_skip += 1
                continue

            ops.append({
                "ts_code": ts_code,
                "name": name,
                "event_type": event_type,
                "event_date": trade_date,
                "title": title,
                "content": f"[{event_type_label}] {title}",
                "severity": severity,
                "is_resolved": False,
                "source": "akshare_individual",
            })
            stats[severity] = stats.get(severity, 0) + 1
            total_new += 1
            existing.add(key)

            if len(ops) >= 500:
                try:
                    await db["stock_events"].insert_many(ops, ordered=False)
                except Exception:
                    pass
                ops = []

    # 分批处理，每批50只（5并发×10轮）
    batch_size = 50
    for i in range(0, len(ordered), batch_size):
        batch = ordered[i:i + batch_size]
        tasks = [fetch_notices(code) for code in batch]
        await asyncio.gather(*tasks)

        if (i + batch_size) % 500 == 0 or i >= len(ordered) - batch_size:
            progress = min(i + batch_size, len(ordered))
            print(f"  进度: {progress}/{len(ordered)}, 新增={total_new}, 跳过={total_skip}")

    if ops:
        try:
            await db["stock_events"].insert_many(ops, ordered=False)
        except Exception:
            pass

    print(f"  个股公告同步完成: 新增={total_new}, 跳过={total_skip}")
    print(f"  新增分布: critical={stats.get('critical',0)}, warning={stats.get('warning',0)}, info={stats.get('info',0)}")


async def run():
    db, client = await get_job_db()
    try:
        print("🔴 开始同步股票风险事件...")
        import akshare as ak

        # 第一步：批量获取（现有数据源）
        df = await asyncio.to_thread(ak.stock_notice_report)
        if df is None or df.empty:
            print("  stock_notice_report 无数据")
            return

        print(f"  获取到 {len(df)} 条公告")

        # 构建去重集合
        existing = set()
        cursor = db["stock_events"].find(
            {"source": {"$in": ["tushare", "akshare"]}},
            {"ts_code": 1, "title": 1, "event_date": 1, "_id": 0},
        )
        async for doc in cursor:
            existing.add((doc["ts_code"], doc["title"], doc.get("event_date", "")))

        total_new = 0
        total_skip = 0
        ops = []
        stats = {"critical": 0, "warning": 0, "info": 0}

        for _, row in df.iterrows():
            code = str(row.get("代码", "")).strip()
            name = str(row.get("名称", "")).strip()
            title = str(row.get("公告标题", "")).strip()
            event_type_label = str(row.get("公告类型", "")).strip()
            pub_date = str(row.get("公告日期", "")).strip()

            if not code or not title:
                continue

            ts_code = _ensure_suffix(code)
            trade_date = _parse_date(pub_date)
            event_type, severity = classify_event(event_type_label, title)

            key = (ts_code, title, trade_date)
            if key in existing:
                total_skip += 1
                continue

            ops.append({
                "ts_code": ts_code,
                "name": name,
                "event_type": event_type,
                "event_date": trade_date,
                "title": title,
                "content": f"[{event_type_label}] {title}",
                "severity": severity,
                "is_resolved": False,
                "source": "akshare",
            })
            stats[severity] = stats.get(severity, 0) + 1
            total_new += 1

            if len(ops) >= 500:
                await db["stock_events"].insert_many(ops, ordered=False)
                ops = []

        if ops:
            await db["stock_events"].insert_many(ops, ordered=False)

        print(f"  新增: {total_new}, 跳过(已存在): {total_skip}")
        print(f"  新增分布: critical={stats['critical']}, warning={stats['warning']}, info={stats['info']}")
        print("✅ 批量公告同步完成")

        # 第二步：对全市场每只股票逐个获取公告
        await _sync_individual_notices(db)

        # 最终统计
        db_critical = await db["stock_events"].count_documents({"severity": "critical"})
        db_warning = await db["stock_events"].count_documents({"severity": "warning"})
        db_info = await db["stock_events"].count_documents({"severity": "info"})
        distinct_stocks = len(await db["stock_events"].distinct("ts_code"))

        print(f"  库中总计: critical={db_critical}, warning={db_warning}, info={db_info}")
        print(f"  覆盖股票数: {distinct_stocks}")
        print("✅ 风险事件同步完成")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(run())
