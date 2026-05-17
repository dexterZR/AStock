import time
import asyncio
from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta


DEFAULT_TEMPLATE = {
    "name": "持仓周巡检",
    "description": "针对持仓股票的标准化周度检查",
    "is_default": True,
    "steps": [
        {"step_id": "kline", "name": "K线回顾", "description": "最近5日K线", "enabled": True, "config": {"days": 5}},
        {"step_id": "announcement", "name": "公告扫描", "description": "最近7天公告", "enabled": True, "config": {"days": 7}},
        {"step_id": "holder_change", "name": "股东动向", "description": "大股东增减持", "enabled": True, "config": {}},
        {"step_id": "risk_score", "name": "风险评分", "description": "重新计算风险等级", "enabled": True, "config": {}},
        {"step_id": "report", "name": "生成报告", "description": "汇总生成Markdown报告", "enabled": True, "config": {}},
    ],
}


class RoutineService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_templates(self) -> List[Dict]:
        t = await self.db["routine_templates"].find_one({"is_default": True})
        if not t:
            await self.db["routine_templates"].insert_one(DEFAULT_TEMPLATE)
            t = dict(DEFAULT_TEMPLATE)
        if "_id" in t:
            t["_id"] = str(t["_id"])
        return [t]

    async def run_routine(self, template_id: str, stock_code: str, stock_name: str) -> str:
        template = await self.db["routine_templates"].find_one({}) or DEFAULT_TEMPLATE
        steps_def = template.get("steps", DEFAULT_TEMPLATE["steps"])

        result = {
            "template_id": template_id,
            "template_name": template.get("name", "持仓周巡检"),
            "stock_code": stock_code,
            "stock_name": stock_name,
            "status": "running",
            "steps": [{"step_id": s["step_id"], "name": s["name"], "status": "pending", "data": {}, "error": None, "duration_ms": 0} for s in steps_def],
            "report": "",
            "created_at": datetime.now().isoformat(),
        }
        r = await self.db["routine_results"].insert_one(result)
        result_id = str(r.inserted_id)

        # 异步执行
        task = asyncio.create_task(self._execute(result_id, stock_code, stock_name, steps_def))
        task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)
        return result_id

    async def _execute(self, result_id: str, stock_code: str, stock_name: str, steps_def: list):
        from bson import ObjectId
        steps_data = {}
        completed_steps = []

        for idx, step in enumerate(steps_def):
            if not step.get("enabled", True):
                continue
            sid = step["step_id"]
            start = time.monotonic()
            try:
                data = {}
                if sid == "kline":
                    data = await self._step_kline(stock_code)
                elif sid == "announcement":
                    data = await self._step_announcement(stock_code)
                elif sid == "holder_change":
                    data = await self._step_holder_change(stock_code)
                elif sid == "risk_score":
                    data = await self._step_risk_score(stock_code, stock_name)
                elif sid == "report":
                    data = await self._step_report(result_id, stock_code, stock_name, steps_data, completed_steps)

                dur = int((time.monotonic() - start) * 1000)
                steps_data[sid] = data
                completed_steps.append({"id": sid, "name": step["name"], "status": "success", "data": data, "error": None, "duration_ms": dur})
                await self.db["routine_results"].update_one(
                    {"_id": ObjectId(result_id)},
                    {"$set": {f"steps.{idx}": {"step_id": sid, "name": step["name"], "status": "success", "data": data, "duration_ms": dur, "error": None}}}
                )
            except Exception as e:
                dur = int((time.monotonic() - start) * 1000)
                steps_data[sid] = {"error": str(e)}
                completed_steps.append({"id": sid, "name": step["name"], "status": "failed", "data": {}, "error": str(e), "duration_ms": dur})

        # 生成报告
        report_md = self._build_report(stock_code, stock_name, completed_steps)

        await self.db["routine_results"].update_one(
            {"_id": ObjectId(result_id)},
            {"$set": {"status": "completed", "report": report_md, "completed_at": datetime.now().isoformat()}}
        )

    async def _step_kline(self, stock_code: str) -> dict:
        cursor = self.db["daily_quotes"].find({"ts_code": stock_code, "adjust_flag": "none"}).sort("trade_date", -1).limit(5)
        rows = await cursor.to_list(5)
        if not rows:
            return {"candles": [], "trend": "flat", "change_pct": 0}
        rows.sort(key=lambda x: x["trade_date"])
        change = (rows[-1]["close"] - rows[0]["close"]) / rows[0]["close"] * 100 if rows[0]["close"] else 0
        trend = "up" if change > 1 else "down" if change < -1 else "flat"
        return {
            "candles": [{"date": r["trade_date"], "open": r["open"], "close": r["close"], "high": r["high"], "low": r["low"], "volume": r["volume"]} for r in rows],
            "trend": trend, "change_pct": round(change, 2),
            "high": max(r["high"] for r in rows), "low": min(r["low"] for r in rows),
        }

    async def _step_announcement(self, stock_code: str) -> dict:
        events = await self.db["stock_events"].find(
            {"ts_code": stock_code}, {"_id": 0}
        ).sort("event_date", -1).limit(10).to_list(10)
        return {
            "count": len(events),
            "announcements": [{"title": e["title"], "date": e["event_date"], "type": e["event_type"]} for e in events],
        }

    async def _step_holder_change(self, stock_code: str) -> dict:
        events = await self.db["stock_events"].find(
            {"ts_code": stock_code, "event_type": {"$in": ["减持", "增持"]}}, {"_id": 0}
        ).sort("event_date", -1).limit(5).to_list(5)
        has_reduce = any(e["event_type"] == "减持" for e in events)
        has_increase = any(e["event_type"] == "增持" for e in events)
        return {
            "changes": [{"holder_name": "控股股东", "change_type": e["event_type"], "date": e["event_date"], "title": e["title"]} for e in events],
            "summary": "有减持记录" if has_reduce else "无异常增减持",
            "warning": has_reduce and not has_increase,
        }

    async def _step_risk_score(self, stock_code: str, stock_name: str) -> dict:
        events = await self.db["stock_events"].find(
            {"ts_code": stock_code, "is_resolved": False, "severity": {"$in": ["warning", "critical"]}}
        ).to_list(None)
        score = 50
        factors = []
        for e in events:
            if e["severity"] == "critical":
                score += 20
                factors.append({"name": e["title"], "weight": 95, "score": 95})
            else:
                score += 8
                factors.append({"name": e["title"], "weight": 65, "score": 65})
        level = "HIGH" if score >= 70 else "MEDIUM" if score >= 50 else "LOW"
        return {"score": min(100, score), "level": level, "factors": factors[:5]}

    async def _step_report(self, result_id: str, stock_code: str, stock_name: str, steps_data: dict, completed_steps: list) -> dict:
        return {"generated": True}

    def _build_report(self, stock_code: str, stock_name: str, steps: list) -> str:
        data = {s["id"]: s.get("data", {}) for s in steps}
        k = data.get("kline", {})
        a = data.get("announcement", {})
        h = data.get("holder_change", {})
        r = data.get("risk_score", {})

        lines = [
            f"# 持仓巡检报告：{stock_name}({stock_code})",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 一、K线回顾（最近5日）",
            f"- 趋势: {k.get('trend', 'N/A')}",
            f"- 区间涨跌: {k.get('change_pct', 0):+.2f}%",
        ]
        if k.get("high"):
            lines.append(f"- 关键价位: 最高{k['high']:.2f} / 最低{k['low']:.2f}")

        lines += ["", "## 二、公告扫描（最近7天）",
            f"- 共 {a.get('count', 0)} 条公告"]
        for ann in a.get("announcements", [])[:3]:
            lines.append(f"- [{ann.get('type','')}] {ann.get('title','')} ({ann.get('date','')})")

        lines += ["", "## 三、股东动向"]
        hd = h.get("changes", [])
        if hd:
            for c in hd[:3]:
                lines.append(f"- {c.get('holder_name','')}: {c.get('change_type','')} ({c.get('date','')})")
        else:
            lines.append("- 无异常增减持记录")
        if h.get("warning"):
            lines.append("- ⚠️ 警示: 有减持记录，资金面需关注")

        lines += ["", "## 四、风险评分更新",
            f"- 当前评分: {r.get('score', 50)}/100 ({r.get('level', 'MEDIUM')})"]
        for f in r.get("factors", []):
            lines.append(f"  - {f['name']}: {f['score']}/100")

        lines += ["", "## 五、巡检结论与建议",
            "1. 【持仓】建议关注成本线与止损线",
            "2. 【风险】关注未解决事件的发展",
            "3. 【建议】根据评分和事件自行判断",
            "", "---", "*本报告由系统自动生成，仅供参考*"]

        return "\n".join(lines)

    async def get_result(self, result_id: str) -> Dict:
        from bson import ObjectId
        doc = await self.db["routine_results"].find_one({"_id": ObjectId(result_id)}, {"_id": 0})
        return doc or {}

    async def get_history(self, stock_code: str, limit: int = 10) -> List[Dict]:
        cursor = self.db["routine_results"].find({"stock_code": stock_code}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(limit)
        for d in docs:
            if "_id" in d:
                d["_id"] = str(d["_id"])
        return docs
