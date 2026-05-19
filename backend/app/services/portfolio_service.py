from typing import List, Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime


class PortfolioService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_holdings(self) -> List[Dict]:
        pipeline = [
            {"$group": {
                "_id": "$ts_code",
                "name": {"$first": "$name"},
                "total_shares": {
                    "$sum": {"$cond": [{"$eq": ["$action", "buy"]}, "$shares", {"$multiply": ["$shares", -1]}]}
                },
                "total_cost": {
                    "$sum": {"$cond": [{"$eq": ["$action", "buy"]}, {"$multiply": ["$price", "$shares"]}, 0]}
                },
                "buy_shares": {
                    "$sum": {"$cond": [{"$eq": ["$action", "buy"]}, "$shares", 0]}
                },
                "first_buy": {"$min": "$trade_date"},
                "last_trade": {"$max": "$trade_date"},
            }},
            {"$match": {"total_shares": {"$gt": 0}}},
        ]
        holdings = await self.db["trades"].aggregate(pipeline).to_list(None)

        if not holdings:
            return []

        ts_codes = [h["_id"] for h in holdings]

        # 批量查最新行情（N+1 → 1次）
        quote_pipeline = [
            {"$match": {"ts_code": {"$in": ts_codes}, "adjust_flag": "none"}},
            {"$sort": {"trade_date": -1}},
            {"$group": {"_id": "$ts_code", "latest": {"$first": "$$ROOT"}}},
        ]
        quote_results = await self.db["daily_quotes"].aggregate(quote_pipeline).to_list(None)
        quote_map = {r["_id"]: r["latest"] for r in quote_results}
        for v in quote_map.values():
            v.pop("_id", None)

        # 批量查未解决事件（N+1 → 1次）
        event_cursor = self.db["stock_events"].find(
            {"ts_code": {"$in": ts_codes}, "is_resolved": False, "severity": {"$in": ["warning", "critical"]}}
        )
        all_events = await event_cursor.to_list(None)
        event_map: dict = {}
        for e in all_events:
            event_map.setdefault(e["ts_code"], []).append(e)

        for h in holdings:
            ts_code = h["_id"]
            latest = quote_map.get(ts_code)
            events = event_map.get(ts_code, [])

            avg_cost = h["total_cost"] / h["buy_shares"] if h["buy_shares"] > 0 else 0
            latest_price = latest["close"] if latest else 0
            pct_change = latest.get("pct_change", 0) if latest else 0
            market_value = latest_price * h["total_shares"]
            remaining_cost = avg_cost * h["total_shares"]
            unrealized_pnl = market_value - remaining_cost
            unrealized_pct = (unrealized_pnl / remaining_cost * 100) if remaining_cost > 0 else 0

            risk_level = "normal"
            if events:
                has_critical = any(e["severity"] == "critical" for e in events)
                risk_level = "critical" if has_critical else "high"

            h.update({
                "ts_code": ts_code,
                "avg_cost": round(avg_cost, 3),
                "latest_price": latest_price,
                "pct_change": round(pct_change, 2) if pct_change else 0,
                "market_value": round(market_value, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "unrealized_pnl_pct": round(unrealized_pct, 2),
                "risk_level": risk_level,
                "warning_events": [e["title"] for e in events[:3]],
            })

        return holdings

    async def add_trade(self, trade: dict) -> str:
        trade["total_amount"] = trade["price"] * trade["shares"]
        result = await self.db["trades"].insert_one(trade)
        return str(result.inserted_id)

    async def get_trades(self, ts_code: Optional[str] = None) -> List[Dict]:
        query = {"ts_code": ts_code} if ts_code else {}
        cursor = self.db["trades"].find(query).sort("trade_date", -1)
        return await cursor.to_list(None)

    async def add_decision_log(self, log: dict) -> str:
        result = await self.db["decision_logs"].insert_one(log)
        return str(result.inserted_id)

    async def get_decision_logs(self, ts_code: Optional[str] = None) -> List[Dict]:
        query = {"ts_code": ts_code} if ts_code else {}
        cursor = self.db["decision_logs"].find(query).sort("created_at", -1)
        return await cursor.to_list(None)

    async def review_decision(self, log_id: str, result: dict):
        from bson import ObjectId
        await self.db["decision_logs"].update_one(
            {"_id": ObjectId(log_id)},
            {"$set": {
                "post_result_pnl": result.get("pnl"),
                "post_result_pct": result.get("pnl_pct"),
                "attribution": result.get("attribution"),
                "lessons": result.get("lessons"),
                "reviewed_at": datetime.now().isoformat(),
            }}
        )

    async def get_trade_stats(self) -> Dict:
        trades = await self.db["trades"].find().to_list(None)
        total_trades = len(trades)
        buy_trades = [t for t in trades if t["action"] == "buy"]
        sell_trades = [t for t in trades if t["action"] == "sell"]

        return {
            "total_trades": total_trades,
            "buy_count": len(buy_trades),
            "sell_count": len(sell_trades),
            "avg_buy_price": sum(t["price"] for t in buy_trades) / len(buy_trades) if buy_trades else 0,
        }

    async def get_realized_pnl(self, ts_code: Optional[str] = None) -> List[Dict]:
        """计算已实现盈亏（FIFO 成本匹配卖出）"""
        query = {}
        if ts_code:
            query["ts_code"] = ts_code

        # 分组计算每只股票的已实现盈亏
        pipeline = [
            {"$match": query},
            {"$sort": {"trade_date": 1}},
            {"$group": {
                "_id": "$ts_code",
                "name": {"$first": "$name"},
                "trades": {"$push": {
                    "action": "$action", "price": "$price",
                    "shares": "$shares", "trade_date": "$trade_date",
                }},
            }},
        ]
        results = await self.db["trades"].aggregate(pipeline).to_list(None)

        realized_list = []
        for r in results:
            ts = r["_id"]
            name = r.get("name", ts)
            trades = r["trades"]

            # 累计买入量和总成本
            total_buy_shares = 0
            total_buy_cost = 0.0
            realized_pnl = 0.0
            sell_count = 0

            for t in trades:
                if t["action"] == "buy":
                    total_buy_shares += t["shares"]
                    total_buy_cost += t["price"] * t["shares"]
                elif t["action"] == "sell":
                    sell_shares = t["shares"]
                    sell_price = t["price"]
                    sell_count += 1

                    if total_buy_shares >= sell_shares:
                        # 有足够的买入来匹配
                        avg_cost = total_buy_cost / total_buy_shares
                        pnl = (sell_price - avg_cost) * sell_shares
                        realized_pnl += pnl
                        # 按比例减少持仓
                        ratio = sell_shares / total_buy_shares
                        total_buy_cost -= total_buy_cost * ratio
                        total_buy_shares -= sell_shares
                    else:
                        # 卖超了（不太正常但兜底）
                        pnl = (sell_price - (total_buy_cost / max(total_buy_shares, 1))) * total_buy_shares
                        realized_pnl += pnl
                        total_buy_shares = 0
                        total_buy_cost = 0.0

            # 剩余持仓（未实现）
            remaining_shares = total_buy_shares
            remaining_avg_cost = total_buy_cost / remaining_shares if remaining_shares > 0 else 0

            realized_list.append({
                "ts_code": ts,
                "name": name,
                "realized_pnl": round(realized_pnl, 2),
                "sell_count": sell_count,
                "remaining_shares": remaining_shares,
                "remaining_avg_cost": round(remaining_avg_cost, 3),
            })

        return realized_list

    async def get_pnl_summary(self) -> Dict:
        """盈亏总览：未实现 + 已实现"""
        # 未实现盈亏（当前持仓）
        holdings = await self.get_holdings()
        total_unrealized = sum(h.get("unrealized_pnl", 0) for h in holdings)
        total_market_value = sum(h.get("market_value", 0) for h in holdings)
        total_cost = sum(
            (h.get("avg_cost", 0) * h.get("total_shares", 0))
            for h in holdings
        )

        # 已实现盈亏
        realized_list = await self.get_realized_pnl()
        total_realized = sum(r["realized_pnl"] for r in realized_list)

        # 按股票汇总
        holding_map = {h["ts_code"]: h for h in holdings}
        stock_summary = []
        all_codes = set(list(holding_map.keys()) + [r["ts_code"] for r in realized_list])

        for ts_code in sorted(all_codes):
            h = holding_map.get(ts_code, {})
            r = next((x for x in realized_list if x["ts_code"] == ts_code), None)

            stock_summary.append({
                "ts_code": ts_code,
                "name": h.get("name") or (r["name"] if r else ts_code),
                "unrealized_pnl": round(h.get("unrealized_pnl", 0), 2),
                "unrealized_pnl_pct": round(h.get("unrealized_pnl_pct", 0), 2),
                "realized_pnl": r["realized_pnl"] if r else 0,
                "total_pnl": round(
                    (h.get("unrealized_pnl", 0) or 0) + (r["realized_pnl"] if r else 0), 2
                ),
                "market_value": round(h.get("market_value", 0), 2),
                "remaining_shares": h.get("total_shares", 0) or (r["remaining_shares"] if r else 0),
            })

        return {
            "total_unrealized_pnl": round(total_unrealized, 2),
            "total_realized_pnl": round(total_realized, 2),
            "total_pnl": round(total_unrealized + total_realized, 2),
            "total_market_value": round(total_market_value, 2),
            "total_cost": round(total_cost, 2),
            "position_count": len(holdings),
            "stocks": stock_summary,
        }

    async def get_holding_detail(self, ts_code: str) -> Optional[Dict]:
        """获取单只股票的持仓详情（含已实现盈亏和交易记录）"""
        holdings = await self.get_holdings()
        holding = next((h for h in holdings if h["ts_code"] == ts_code), None)

        trades = await self.get_trades(ts_code)
        realized = await self.get_realized_pnl(ts_code)

        # 成本线
        cost_doc = await self.db["cost_lines"].find_one({"ts_code": ts_code}, {"_id": 0})
        if not cost_doc and trades:
            buy_trades = [t for t in trades if t["action"] == "buy"]
            if buy_trades:
                total_buy_cost = sum(t["price"] * t["shares"] for t in buy_trades)
                total_buy_shares = sum(t["shares"] for t in buy_trades)
                avg = round(total_buy_cost / total_buy_shares, 3) if total_buy_shares > 0 else 0
                cost_doc = {
                    "ts_code": ts_code,
                    "cost_price": avg,
                    "add_price": None,
                    "reduce_price": None,
                    "stop_loss_price": None,
                    "position_qty": total_buy_shares,
                }

        result = {
            "ts_code": ts_code,
            "holding": holding,
            "trades": trades,
            "cost_line": cost_doc,
            "realized_pnl": realized[0] if realized else None,
        }
        return result
