import asyncio
import json
from app.infrastructure.tushare_client import data_client
from app.infrastructure.sse_manager import SSEManager

async def sync_realtime_quotes(sse_manager: SSEManager):
    """盘中实时行情推送"""
    try:
        df = data_client.get_realtime_quotes()
        if df is None or len(df) == 0:
            return

        # 只取前 50 只推送，避免 SSE 爆炸
        for _, row in df.head(50).iterrows():
            code = str(row.get("代码", ""))
            if not code:
                continue
            suffix = ".SH" if code.startswith(("6", "5")) else ".SZ"
            ts_code = f"{code}{suffix}"

            quote = {
                "type": "quote_update",
                "ts_code": ts_code,
                "close": float(row.get("最新价", 0)),
                "pct_change": float(row.get("涨跌幅", 0)),
                "volume": int(float(row.get("成交量", 0))),
                "amount": float(row.get("成交额", 0)),
            }
            await sse_manager.publish(f"quote:{ts_code}", quote)

        # 广播数量
        await sse_manager.broadcast({
            "type": "batch_update",
            "count": min(len(df), 50),
            "ts": int(asyncio.get_event_loop().time()),
        })
    except Exception as e:
        print(f"实时同步异常: {e}")
