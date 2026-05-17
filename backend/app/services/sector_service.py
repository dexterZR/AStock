from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

_sector_cache: Dict = {"data": None, "ts": 0, "ttl": 120}
_overview_cache: Dict = {"data": None, "ts": 0, "ttl": 120}
_cons_cache: Dict = {"data": {}, "ts": 0, "ttl": 120}
_stocks_cache: Dict = {"data": None, "ts": 0, "ttl": 3600}
_daily_cache: Dict = {"data": None, "ts": 0, "ttl": 120, "trade_date": ""}


class SectorAnalysisService:
    """板块分析服务 - 使用 tushare 数据源确保行业名称一致"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def _get_tushare_daily_all(self, trade_date: str = None) -> tuple:
        global _daily_cache
        now = time.time()
        if _daily_cache["data"] is not None and now - _daily_cache["ts"] < _daily_cache["ttl"]:
            return _daily_cache["data"], _daily_cache["trade_date"]

        import tushare as ts
        from app.core.config import settings
        from datetime import datetime, timedelta

        if not trade_date:
            trade_date = datetime.now().strftime("%Y%m%d")

        ts.set_token(settings.TUSHARE_TOKEN)
        pro = ts.pro_api()

        df = await asyncio.to_thread(pro.daily, trade_date=trade_date)
        if df is None or len(df) == 0:
            for i in range(1, 5):
                prev = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
                df = await asyncio.to_thread(pro.daily, trade_date=prev)
                if df is not None and len(df) > 0:
                    trade_date = prev
                    break

        if df is None or len(df) == 0:
            return [], ""

        quotes = []
        for _, row in df.iterrows():
            quotes.append({
                "ts_code": row.get("ts_code", ""),
                "trade_date": str(row.get("trade_date", "")),
                "open": float(row.get("open", 0) or 0),
                "high": float(row.get("high", 0) or 0),
                "low": float(row.get("low", 0) or 0),
                "close": float(row.get("close", 0) or 0),
                "pre_close": float(row.get("pre_close", 0) or 0),
                "pct_chg": float(row.get("pct_chg", 0) or 0),
                "vol": float(row.get("vol", 0) or 0),
                "amount": float(row.get("amount", 0) or 0),
            })
        _daily_cache["data"] = quotes
        _daily_cache["ts"] = now
        _daily_cache["trade_date"] = trade_date
        return quotes, trade_date

    async def _get_stocks_with_industry(self) -> Dict[str, Dict]:
        global _stocks_cache
        now = time.time()
        if _stocks_cache["data"] is not None and now - _stocks_cache["ts"] < _stocks_cache["ttl"]:
            return _stocks_cache["data"]

        try:
            import tushare as ts
            from app.core.config import settings
            ts.set_token(settings.TUSHARE_TOKEN)
            pro = ts.pro_api()
            df = await asyncio.to_thread(
                pro.stock_basic, exchange='', list_status='L',
                fields='ts_code,name,industry,market'
            )
            stocks = {}
            for _, row in df.iterrows():
                stocks[row["ts_code"]] = {
                    "ts_code": row["ts_code"],
                    "name": row.get("name", ""),
                    "industry": row.get("industry", ""),
                    "market": row.get("market", ""),
                }
            _stocks_cache["data"] = stocks
            _stocks_cache["ts"] = now
            return stocks
        except Exception as e:
            logger.warning(f"tushare stock_basic 获取失败: {e}")
            return _stocks_cache.get("data") or {}

    async def get_sector_ranking(self, limit: int = 20) -> List[Dict]:
        """获取板块涨跌排行 - 使用 tushare 数据"""
        global _sector_cache
        now = time.time()
        if _sector_cache["data"] is not None and now - _sector_cache["ts"] < _sector_cache["ttl"]:
            return _sector_cache["data"][:limit]

        sectors = await self._build_tushare_sector_ranking()

        if not sectors:
            sectors = await self._fallback_sector_ranking(20)

        _sector_cache["data"] = sectors
        _sector_cache["ts"] = now
        return sectors[:limit]

    async def _build_tushare_sector_ranking(self) -> List[Dict]:
        """用 tushare 全量行情 + 行业分类计算板块排行"""
        try:
            quotes, trade_date = await self._get_tushare_daily_all()
            if not quotes:
                return []

            stocks_info = await self._get_stocks_with_industry()

            industry_data: Dict[str, Dict] = {}
            for q in quotes:
                info = stocks_info.get(q["ts_code"], {})
                industry = info.get("industry", "")
                if not industry:
                    continue
                if industry not in industry_data:
                    industry_data[industry] = {
                        "name": industry, "sector": industry,
                        "pcts": [], "amounts": [], "stocks": [],
                        "up": 0, "down": 0, "flat": 0,
                        "limit_up": 0, "limit_down": 0,
                    }
                d = industry_data[industry]
                pct = q["pct_chg"]
                d["pcts"].append(pct)
                d["amounts"].append(q["amount"])
                d["stocks"].append({
                    "ts_code": q["ts_code"],
                    "name": info.get("name", ""),
                    "pct_change": pct,
                    "close": q["close"],
                    "amount": q["amount"],
                    "vol": q["vol"],
                })
                if pct >= 9.9:
                    d["limit_up"] += 1
                elif pct <= -9.9:
                    d["limit_down"] += 1
                if pct > 0.05:
                    d["up"] += 1
                elif pct < -0.05:
                    d["down"] += 1
                else:
                    d["flat"] += 1

            sectors = []
            for industry, d in industry_data.items():
                avg_pct = sum(d["pcts"]) / len(d["pcts"]) if d["pcts"] else 0
                total_amount = sum(d["amounts"]) * 1000
                sorted_stocks = sorted(d["stocks"], key=lambda x: x["pct_change"], reverse=True)
                lead = sorted_stocks[0] if sorted_stocks else {}
                sectors.append({
                    "name": industry,
                    "sector": industry,
                    "stock_count": len(d["pcts"]),
                    "change_pct": round(avg_pct, 2),
                    "avg_pct_change": round(avg_pct, 2),
                    "total_amount": total_amount,
                    "up_count": d["up"],
                    "down_count": d["down"],
                    "flat_count": d["flat"],
                    "limit_up": d["limit_up"],
                    "limit_down": d["limit_down"],
                    "lead_stock": lead.get("name", ""),
                    "lead_stock_pct": lead.get("pct_change", 0),
                    "performance": "领涨" if avg_pct > 3 else "上涨" if avg_pct > 0 else "领跌" if avg_pct < -3 else "下跌",
                    "top_stocks": sorted_stocks[:5],
                    "bottom_stocks": sorted_stocks[-5:] if len(sorted_stocks) > 5 else [],
                    "all_stocks": sorted_stocks,
                    "source": "tushare",
                    "trade_date": trade_date,
                })

            sectors.sort(key=lambda x: x["change_pct"], reverse=True)
            return sectors
        except Exception as e:
            logger.warning(f"tushare 板块排行获取失败: {e}")
            return []

    async def get_concept_ranking(self, limit: int = 20) -> List[Dict]:
        """获取概念板块排行"""
        return await self.get_sector_ranking(limit)

    async def get_sector_constituents(self, sector_name: str, limit: int = 20) -> List[Dict]:
        """获取板块成分股 - 使用 tushare 行业分类"""
        global _cons_cache
        now = time.time()
        if sector_name in _cons_cache["data"] and now - _cons_cache["ts"] < _cons_cache["ttl"]:
            return _cons_cache["data"][sector_name][:limit]

        stocks = await self._tushare_sector_constituents(sector_name, limit)

        if not stocks:
            stocks = await self._fallback_sector_stocks(sector_name, "")

        _cons_cache["data"][sector_name] = stocks
        _cons_cache["ts"] = now
        return stocks[:limit]

    async def _tushare_sector_constituents(self, sector_name: str, limit: int = 20) -> List[Dict]:
        try:
            stocks_info = await self._get_stocks_with_industry()
            quotes, trade_date = await self._get_tushare_daily_all()
            if not quotes:
                return []

            quotes_map = {q["ts_code"]: q for q in quotes}
            result = []
            for ts_code, info in stocks_info.items():
                if info.get("industry") != sector_name:
                    continue
                q = quotes_map.get(ts_code, {})
                result.append({
                    "ts_code": ts_code,
                    "name": info.get("name", ""),
                    "industry": sector_name,
                    "close": q.get("close", 0),
                    "pct_change": q.get("pct_chg", 0),
                    "volume": q.get("vol", 0),
                    "amount": q.get("amount", 0) * 1000,
                })
            result.sort(key=lambda x: x.get("pct_change", -999) or -999, reverse=True)
            return result[:limit]
        except Exception as e:
            logger.warning(f"tushare 板块成分股获取失败: {e}")
            return []

    async def _fallback_sector_ranking(self, limit: int) -> List[Dict]:
        pipeline = [
            {"$match": {"industry": {"$nin": [None, ""]}}},
            {
                "$lookup": {
                    "from": "daily_quotes",
                    "let": {"ts_code": "$ts_code"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$ts_code", "$$ts_code"]}, "adjust_flag": "none"}},
                        {"$sort": {"trade_date": -1}},
                        {"$limit": 1}
                    ],
                    "as": "quotes"
                }
            },
            {"$unwind": {"path": "$quotes", "preserveNullAndEmptyArrays": True}},
            {
                "$group": {
                    "_id": "$industry",
                    "stock_count": {"$sum": 1},
                    "avg_pct_change": {"$avg": "$quotes.pct_change"},
                    "total_amount": {"$sum": "$quotes.amount"},
                    "stocks": {
                        "$push": {
                            "ts_code": "$ts_code",
                            "name": "$name",
                            "industry": "$industry",
                            "pct_change": "$quotes.pct_change"
                        }
                    }
                }
            },
            {"$sort": {"avg_pct_change": -1}},
            {"$limit": limit * 2}
        ]

        results = await self.db["stocks"].aggregate(pipeline).to_list(limit * 2)
        sectors = []

        for res in results:
            industry = res["_id"]
            if not industry:
                continue
            avg_pct = res.get("avg_pct_change", 0) or 0
            valid_stocks = sorted(
                [s for s in res.get("stocks", []) if s.get("pct_change") is not None],
                key=lambda x: x["pct_change"],
                reverse=True
            )
            sectors.append({
                "name": industry,
                "sector": industry,
                "stock_count": res.get("stock_count", 0),
                "change_pct": round(avg_pct, 2),
                "avg_pct_change": round(avg_pct, 2),
                "total_amount": res.get("total_amount", 0) or 0,
                "performance": "领涨" if avg_pct > 3 else "上涨" if avg_pct > 0 else "领跌" if avg_pct < -3 else "下跌",
                "top_stocks": valid_stocks[:5],
                "bottom_stocks": valid_stocks[-5:] if len(valid_stocks) > 5 else [],
                "all_stocks": valid_stocks,
                "lead_stock": valid_stocks[0]["name"] if valid_stocks else "",
                "lead_stock_pct": valid_stocks[0]["pct_change"] if valid_stocks else 0,
                "source": "db",
            })

        return sectors[:limit]

    async def get_stock_related_sectors(self, ts_code: str) -> Dict:
        """获取股票所属板块及同板块联动"""
        stocks_info = await self._get_stocks_with_industry()
        info = stocks_info.get(ts_code, {})

        if not info:
            stock = await self.db["stocks"].find_one({"ts_code": ts_code}, {"_id": 0})
            if stock:
                industry = stock.get("industry", "")
            else:
                industry = ""
        else:
            industry = info.get("industry", "")

        sector_stocks = []
        if industry:
            sector_stocks = await self.get_sector_constituents(industry, limit=20)
            for s in sector_stocks:
                s["is_focus"] = s.get("ts_code") == ts_code

        return {
            "current_sector": industry,
            "related_sectors": [{"sector": industry, "type": "行业"}] if industry else [],
            "sector_stocks": sector_stocks
        }

    async def _fallback_sector_stocks(self, industry: str, ts_code: str) -> List[Dict]:
        pipeline = [
            {"$match": {"industry": industry}},
            {"$limit": 50},
            {
                "$lookup": {
                    "from": "daily_quotes",
                    "let": {"ts_code": "$ts_code"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$ts_code", "$$ts_code"]}, "adjust_flag": "none"}},
                        {"$sort": {"trade_date": -1}},
                        {"$limit": 1}
                    ],
                    "as": "quotes"
                }
            },
            {"$unwind": {"path": "$quotes", "preserveNullAndEmptyArrays": True}}
        ]

        sector_stocks_raw = await self.db["stocks"].aggregate(pipeline).to_list(50)
        sector_stocks = []
        for s in sector_stocks_raw:
            quote = s.get("quotes", {})
            close_val = quote.get("close")
            sector_stocks.append({
                "ts_code": s.get("ts_code"),
                "name": s.get("name"),
                "industry": s.get("industry"),
                "close": close_val,
                "pct_change": quote.get("pct_change"),
                "is_focus": s.get("ts_code") == ts_code,
            })
        sector_stocks.sort(key=lambda x: (x.get("pct_change", -999) is None, x.get("pct_change", -999)), reverse=True)
        return sector_stocks

    async def get_market_overview_extended(self) -> Dict:
        """获取扩展市场概览 - 使用 tushare 全量数据"""
        global _overview_cache
        now = time.time()
        if _overview_cache["data"] is not None and now - _overview_cache["ts"] < _overview_cache["ttl"]:
            return _overview_cache["data"]

        try:
            quotes, trade_date = await self._get_tushare_daily_all()
            if quotes:
                up_count = 0
                down_count = 0
                flat_count = 0
                limit_up_count = 0
                limit_down_count = 0
                total_amount = 0

                for q in quotes:
                    pct = q.get("pct_chg", 0) or 0
                    total_amount += q.get("amount", 0) or 0
                    if pct >= 9.9:
                        limit_up_count += 1
                    elif pct <= -9.9:
                        limit_down_count += 1
                    if pct > 0.05:
                        up_count += 1
                    elif pct < -0.05:
                        down_count += 1
                    else:
                        flat_count += 1

                total = up_count + down_count + flat_count

                if total > 0:
                    up_ratio = up_count / total
                    if up_ratio > 0.7:
                        market_temp, temp_score = "火热", 85
                    elif up_ratio > 0.55:
                        market_temp, temp_score = "偏热", 70
                    elif up_ratio > 0.4:
                        market_temp, temp_score = "中性", 50
                    elif up_ratio > 0.25:
                        market_temp, temp_score = "偏冷", 30
                    else:
                        market_temp, temp_score = "寒冷", 15
                else:
                    market_temp, temp_score = "未知", 50

                result = {
                    "up_down_stats": {
                        "up": up_count,
                        "down": down_count,
                        "flat": flat_count,
                        "limit_up": limit_up_count,
                        "limit_down": limit_down_count,
                        "up_ratio": round(up_count / total * 100, 1) if total > 0 else 0,
                        "down_ratio": round(down_count / total * 100, 1) if total > 0 else 0,
                        "total_amount": total_amount * 1000,
                        "total_stocks": total,
                    },
                    "market_temperature": temp_score,
                    "market_temperature_level": market_temp,
                    "market_temperature_description": f"当前上涨{up_count}家，下跌{down_count}家，涨停{limit_up_count}家，跌停{limit_down_count}家，市场{market_temp}",
                    "trade_date": trade_date,
                }
                _overview_cache["data"] = result
                _overview_cache["ts"] = now
                return result
        except Exception as e:
            logger.warning(f"tushare 市场概览获取失败: {e}")

        return await self._fallback_market_overview()

    async def _fallback_market_overview(self) -> Dict:
        latest = await self.db["daily_quotes"].find_one(
            {"adjust_flag": "none"},
            {"trade_date": 1},
            sort=[("trade_date", -1)],
        )
        if not latest:
            return {
                "up_down_stats": {"up": 0, "down": 0, "flat": 0, "limit_up": 0, "limit_down": 0, "up_ratio": 0, "down_ratio": 0, "total_stocks": 0},
                "market_temperature": 50,
                "market_temperature_level": "未知",
                "market_temperature_description": "暂无数据",
            }

        trade_date = latest["trade_date"]
        latest_quotes = await self.db["daily_quotes"].find(
            {"adjust_flag": "none", "trade_date": trade_date},
            {"pct_change": 1},
        ).to_list(None)

        up_count = 0
        down_count = 0
        flat_count = 0
        limit_up_count = 0
        limit_down_count = 0

        for q in latest_quotes:
            pct = q.get("pct_change", 0) or 0
            if pct > 5:
                limit_up_count += 1
            elif pct < -5:
                limit_down_count += 1
            if pct > 0.05:
                up_count += 1
            elif pct < -0.05:
                down_count += 1
            else:
                flat_count += 1

        total = up_count + down_count + flat_count

        if total > 0:
            up_ratio = up_count / total
            if up_ratio > 0.7:
                market_temp, temp_score = "火热", 85
            elif up_ratio > 0.55:
                market_temp, temp_score = "偏热", 70
            elif up_ratio > 0.4:
                market_temp, temp_score = "中性", 50
            elif up_ratio > 0.25:
                market_temp, temp_score = "偏冷", 30
            else:
                market_temp, temp_score = "寒冷", 15
        else:
            market_temp, temp_score = "未知", 50

        return {
            "up_down_stats": {
                "up": up_count,
                "down": down_count,
                "flat": flat_count,
                "limit_up": limit_up_count,
                "limit_down": limit_down_count,
                "up_ratio": round(up_count / total * 100, 1) if total > 0 else 0,
                "down_ratio": round(down_count / total * 100, 1) if total > 0 else 0,
                "total_stocks": total,
            },
            "market_temperature": temp_score,
            "market_temperature_level": market_temp,
            "market_temperature_description": f"当前上涨家数占比{up_count/total:.1%}，市场{market_temp}" if total > 0 else "暂无数据",
        }
