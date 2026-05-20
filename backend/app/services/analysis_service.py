from typing import List, Dict, Optional
import asyncio
import re
import hashlib
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import json

from app.core.config import settings

# ============================================================
# 行业权重配置（可修改）
# ============================================================
INDUSTRY_WEIGHTS = {
    # 高关注行业 — 市场热度高，给予较高加分
    "high_attention": ["银行", "白酒", "电力", "医药", "通信", "新能源", "半导体", "人工智能"],
    "high_attention_score": 8,
    # 稳定行业 — 波动小、防御性强
    "stable": ["银行", "电力", "交通运输"],
    "stable_score": 5,
    # 高成长行业
    "growth": ["新能源", "半导体", "人工智能", "通信"],
    "growth_score": 10,
}


class MultiAgentAnalysisService:
    """选股多Agent分析服务（深度版）

    三维度分析：
    1. 技术面（Technical Agent）— 趋势 / 量价 / MACD / RSI / KDJ / 支撑压力
    2. 基本面（Fundamental Agent）— 行业 / 市值 / 成交额 / 价格位置 / 波动率
    3. 催化剂（Catalyst Agent）— 短期动量 / 量价突破 / 指标信号强化

    支持 LLM 生成自然语言深度分析报告（需配置 LLM_API_KEY）。
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def analyze_stock(self, ts_code: str, skip_llm: bool = False) -> Dict:
        """单股票三维度深度分析

        Args:
            ts_code: 股票代码
            skip_llm: 是否跳过LLM深度报告（批量/讨论场景建议跳过以加速响应）
        """
        # 获取最近120天数据（更丰富）
        quotes = await self.db["daily_quotes"].find(
            {"ts_code": ts_code, "adjust_flag": "none"},
            {"_id": 0}
        ).sort("trade_date", -1).limit(120).to_list(120)
        quotes.reverse()

        indicators = await self.db["indicators"].find(
            {"ts_code": ts_code},
            {"_id": 0}
        ).sort("trade_date", -1).limit(60).to_list(60)
        indicators.reverse()

        stock = await self.db["stocks"].find_one(
            {"ts_code": ts_code},
            {"_id": 0}
        )

        if not quotes or len(quotes) < 10:
            return {
                "ts_code": ts_code,
                "name": stock.get("name", "") if stock else "",
                "trade_date": quotes[-1]["trade_date"] if quotes else "",
                "close": quotes[-1]["close"] if quotes else 0,
                "total_score": 0,
                "technical": {"score": 0, "dimension": "技术面", "reasons": ["数据不足，无法进行技术分析"], "details": [f"当前仅有{len(quotes)}条K线数据，需要至少10条"]},
                "fundamental": {"score": 0, "dimension": "基本面", "reasons": ["数据不足"], "details": []},
                "catalyst": {"score": 0, "dimension": "催化剂", "reasons": ["数据不足"], "details": []},
                "bull_bear_analysis": {"bullish": [], "bearish": [], "neutral": ["数据不足，无法分析"], "bull_bear_balance": "中性"},
                "key_signals": [],
                "operation_suggestion": {"position_suggestion": "建议观望", "suggestions": ["数据不足，无法给出操作建议"]},
                "verdict": {"action": "数据不足", "color": "#9ca3af", "summary": f"当前仅有{len(quotes)}条K线数据，无法进行有效分析"},
                "data_insufficient": True,
            }

        tech = self._technical_agent(quotes, indicators)
        fund = self._fundamental_agent(stock, quotes)
        catalyst = self._catalyst_agent(quotes, indicators)

        # 综合评分
        total_score = round(
            tech["score"] * 0.4 + fund["score"] * 0.3 + catalyst["score"] * 0.3,
            1
        )

        latest = quotes[-1]

        # 调用 LLM 生成深度分析报告（批量场景可跳过以加速响应）
        llm_report = None
        if not skip_llm:
            llm_report = await self._generate_llm_deep_report(
                ts_code=ts_code,
                name=stock.get("name", "") if stock else "",
                latest=latest,
                technical=tech,
                fundamental=fund,
                catalyst=catalyst,
                total_score=total_score,
            )

        return {
            "ts_code": ts_code,
            "name": stock.get("name", "") if stock else "",
            "trade_date": latest["trade_date"],
            "close": latest["close"],
            "total_score": total_score,
            "technical": tech,
            "fundamental": fund,
            "catalyst": catalyst,
            "bull_bear_analysis": self._bull_bear_analysis(tech, fund, catalyst),
            "key_signals": self._extract_key_signals(quotes, indicators),
            "operation_suggestion": self._operation_suggestion(total_score, quotes, indicators),
            "verdict": self._verdict(total_score, tech, fund, catalyst),
            "llm_deep_report": llm_report,  # LLM 生成的深度分析报告（skip_llm 时为 None）
        }

    def _technical_agent(self, quotes: List[Dict], indicators: List[Dict]) -> Dict:
        """技术面深度分析Agent"""
        close = [q["close"] for q in quotes]
        vol = [q["volume"] for q in quotes]
        latest = quotes[-1]
        prev = quotes[-2] if len(quotes) > 1 else latest

        score = 50
        reasons = []
        details = []
        signals = []

        # 1. 趋势判断
        ma5 = sum(close[-5:]) / 5 if len(close) >= 5 else close[-1]
        ma10 = sum(close[-10:]) / 10 if len(close) >= 10 else close[-1]
        ma20 = sum(close[-20:]) / 20 if len(close) >= 20 else close[-1]
        ma60 = sum(close[-60:]) / 60 if len(close) >= 60 else close[-1]

        trend_strength = "震荡"
        if latest["close"] > ma5 > ma10 > ma20:
            score += 15
            trend_strength = "强势上升"
            reasons.append("均线多头排列（MA5>MA10>MA20），上升趋势确立")
            details.append(f"当前价格{latest['close']:.2f}位于MA5({ma5:.2f})上方，多头格局")
            signals.append({"type": "bullish", "name": "均线多头排列", "strength": "强"})
        elif ma20 > ma10 > ma5 > latest["close"]:
            score -= 15
            trend_strength = "弱势下降"
            reasons.append("均线空头排列，下降趋势明显")
            details.append(f"当前价格位于MA20({ma20:.2f})下方，空头格局")
            signals.append({"type": "bearish", "name": "均线空头排列", "strength": "强"})
        elif latest["close"] > ma20:
            score += 8
            trend_strength = "中性偏强"
            reasons.append("价格站上MA20，中短期趋势向好")
        elif latest["close"] < ma20:
            score -= 8
            trend_strength = "中性偏弱"
            reasons.append("价格跌破MA20，短线趋势转弱")

        details.append(f"当前趋势强度：{trend_strength}")

        # 2. 量价分析
        avg_vol = sum(vol[-20:]) / 20 if len(vol) >= 20 else vol[-1]
        vol_ratio = vol[-1] / avg_vol if avg_vol > 0 else 1
        
        if vol_ratio > 2 and latest["close"] > prev["close"]:
            score += 10
            reasons.append(f"放量上涨（量比{vol_ratio:.1f}），资金关注度大幅提升")
            details.append(f"今日成交量{vol[-1]:.0f}手，较20日均量放大{vol_ratio:.1f}倍")
            signals.append({"type": "bullish", "name": "放量突破", "strength": "中"})
        elif vol_ratio > 2 and latest["close"] < prev["close"]:
            score -= 8
            reasons.append(f"放量下跌，资金出逃迹象")
            signals.append({"type": "bearish", "name": "放量下跌", "strength": "中"})
        elif vol_ratio < 0.6 and abs(latest["pct_change"]) < 1:
            details.append(f"量能萎缩（量比{vol_ratio:.1f}），行情可能进入蛰伏期")

        # 3. 技术指标深度分析
        macd_status = "中性"
        rsi_status = "中性"
        kdj_status = "中性"
        
        if indicators and len(indicators) >= 5:
            ind = indicators[-1]
            ind_prev = indicators[-2]
            macd_bar = ind.get("macd_bar", 0)
            macd_bar_prev = ind_prev.get("macd_bar", 0)
            rsi_6 = ind.get("rsi_6", 50)
            rsi_12 = ind.get("rsi_12", 50)
            kdj_k = ind.get("kdj_k", 50)
            kdj_d = ind.get("kdj_d", 50)

            # MACD 分析
            if macd_bar is not None and macd_bar_prev is not None:
                if macd_bar_prev < 0 < macd_bar:
                    score += 10
                    macd_status = "金叉"
                    reasons.append(f"MACD金叉（柱于{latest['trade_date']}由负转正），明确买点信号")
                    signals.append({"type": "bullish", "name": "MACD金叉", "strength": "强"})
                elif macd_bar_prev > 0 > macd_bar:
                    score -= 10
                    macd_status = "死叉"
                    reasons.append("MACD死叉，注意回调风险")
                    signals.append({"type": "bearish", "name": "MACD死叉", "strength": "强"})
                elif macd_bar > 0 and macd_bar > macd_bar_prev:
                    score += 3
                    macd_status = "红柱放大"
                    details.append(f"MACD红柱放大（{macd_bar:.3f}），多头动能增强")
                elif macd_bar > 0 and macd_bar < macd_bar_prev:
                    macd_status = "红柱缩短"
                    details.append("MACD红柱缩短，注意动能衰减")

            # RSI 分析
            if rsi_6 is not None:
                if rsi_6 > 80:
                    score -= 8
                    rsi_status = "超买"
                    reasons.append(f"RSI6={rsi_6:.1f}，进入超买区域，注意回调风险")
                    signals.append({"type": "bearish", "name": "RSI超买", "strength": "中"})
                elif rsi_6 < 30:
                    score += 8
                    rsi_status = "超卖"
                    reasons.append(f"RSI6={rsi_6:.1f}，进入超卖区域，可能反弹")
                    signals.append({"type": "bullish", "name": "RSI超卖", "strength": "中"})
                elif 30 < rsi_6 < 70:
                    score += 2
                    rsi_status = "健康"
                    details.append(f"RSI6={rsi_6:.1f}，处于健康区间")

            # KDJ 分析
            if kdj_k is not None and kdj_d is not None:
                if kdj_k > 80 and kdj_d > 80:
                    kdj_status = "高位"
                    details.append(f"KDJ处于高位（K={kdj_k:.1f}, D={kdj_d:.1f}）")
                elif kdj_k < 20 and kdj_d < 20:
                    kdj_status = "低位"
                    details.append(f"KDJ处于低位（K={kdj_k:.1f}, D={kdj_d:.1f}）")
                elif kdj_k > kdj_d and kdj_k < 50:
                    score += 5
                    kdj_status = "低位金叉"
                    reasons.append("KDJ低位金叉，可能是反弹信号")

        # 4. 支撑压力位计算
        recent_low = min([q["low"] for q in quotes[-30:]])
        recent_high = max([q["high"] for q in quotes[-30:]])
        recent_20_low = min([q["low"] for q in quotes[-20:]])
        recent_20_high = max([q["high"] for q in quotes[-20:]])
        earlier_10_low = min([q["low"] for q in quotes[-30:-10]]) if len(quotes) >= 30 else recent_low
        earlier_10_high = max([q["high"] for q in quotes[-30:-10]]) if len(quotes) >= 30 else recent_high
        
        support_resistance = {
            "strong_support": round(min(recent_low, earlier_10_low), 2),
            "weak_support": round(recent_20_low, 2),
            "weak_resistance": round(recent_20_high, 2),
            "strong_resistance": round(max(recent_high, earlier_10_high), 2),
        }
        
        if support_resistance["strong_support"] == support_resistance["weak_support"]:
            support_resistance["strong_support"] = round(support_resistance["weak_support"] * 0.98, 2)
        if support_resistance["strong_resistance"] == support_resistance["weak_resistance"]:
            support_resistance["strong_resistance"] = round(support_resistance["weak_resistance"] * 1.02, 2)
        
        if latest["close"] > (recent_20_low + recent_20_high) / 2:
            score += 5
            reasons.append("价格处于近期区间中上部，相对强势")
        
        details.append(f"关键支撑位：{support_resistance['weak_support']:.2f}（20日）、{support_resistance['strong_support']:.2f}（30日）")
        details.append(f"关键压力位：{support_resistance['weak_resistance']:.2f}（20日）、{support_resistance['strong_resistance']:.2f}（30日）")

        # 5. 今日走势点评
        pct = latest.get("pct_change", 0)
        if pct > 5:
            score -= 5
            reasons.append(f"今日大涨{pct:.1f}%，注意追高风险，建议等待回调")
        elif pct < -5:
            score -= 3
            details.append(f"今日大跌{pct:.1f}%，谨慎观望，不建议急着抄底")
        elif 0 < pct <= 3:
            details.append(f"今日小涨{pct:.1f}%，走势平稳")

        return {
            "score": max(0, min(100, score)),
            "dimension": "技术面",
            "reasons": reasons[:5],
            "details": details,
            "signals": signals,
            "trend_strength": trend_strength,
            "indicators_status": {
                "macd": macd_status,
                "rsi": rsi_status,
                "kdj": kdj_status
            },
            "support_resistance": support_resistance,
        }

    def _fundamental_agent(self, stock: Dict, quotes: List[Dict]) -> Dict:
        """基本面深度分析Agent"""
        score = 50
        reasons = []
        details = []
        industry_analysis = ""

        # 行业分析（使用可配置权重）
        industry = stock.get("industry", "") if stock else ""
        if industry:
            hi_list = INDUSTRY_WEIGHTS.get("high_attention", [])
            hi_score = INDUSTRY_WEIGHTS.get("high_attention_score", 8)
            st_list = INDUSTRY_WEIGHTS.get("stable", [])
            st_score = INDUSTRY_WEIGHTS.get("stable_score", 5)
            gr_list = INDUSTRY_WEIGHTS.get("growth", [])
            gr_score = INDUSTRY_WEIGHTS.get("growth_score", 10)

            if industry in gr_list:
                score += gr_score
                reasons.append(f"属于{industry}，高成长赛道")
            elif industry in hi_list:
                score += hi_score
                reasons.append(f"属于{industry}板块，属于市场较关注行业")
            elif industry in st_list:
                score += st_score
                reasons.append(f"属于{industry}，行业稳定，波动较小")

            industry_analysis = f"所在行业：{industry}"

        # 市值与流动性分析
        cap_analysis = "未知"
        if stock and stock.get("total_cap", 0) > 0:
            cap = stock["total_cap"]
            if cap > 1000e8:
                cap_analysis = "大盘蓝筹，流动性极佳"
                score += 5
                details.append(f"市值{cap/1e8:.0f}亿，属于大盘股，机构偏好")
            elif 100e8 < cap <= 1000e8:
                cap_analysis = "中盘股，弹性较好"
                score += 8
                details.append(f"市值{cap/1e8:.0f}亿，中盘股，兼顾弹性与流动性")
            elif 50e8 < cap <= 100e8:
                cap_analysis = "小盘股，波动大"
                score += 3
                details.append(f"市值{cap/1e8:.0f}亿，小盘股，弹性大但风险也高")
            else:
                cap_analysis = "微盘股，注意风险"
                score -= 5
                details.append("市值较小，注意流动性风险")

        # 成交额活跃度分析
        avg_amount = sum([q.get("amount", 0) for q in quotes[-10:]]) / 10
        if avg_amount > 5e8:
            score += 10
            reasons.append("日均成交额超过5亿，交易活跃，大资金进出方便")
            details.append(f"近10日日均成交额{avg_amount/1e8:.1f}亿，流动性极佳")
        elif avg_amount > 1e8:
            score += 5
            reasons.append("日均成交额超过1亿，流动性良好")
        elif avg_amount < 1e7:
            score -= 8
            reasons.append("成交额偏低，注意流动性风险")
            details.append("日均成交额不足千万，流动性较差")

        # 价格位置分析（相对历史位置）
        latest = quotes[-1]
        prices = [q["close"] for q in quotes]
        price_max = max(prices)
        price_min = min(prices)
        price_pos = (latest["close"] - price_min) / (price_max - price_min) if price_max > price_min else 0.5

        if price_pos > 0.8:
            details.append(f"当前价格处于近{len(prices)}日高位（位置分位{price_pos:.1%}），注意回调风险")
        elif price_pos < 0.2:
            score += 5
            details.append(f"当前价格处于近{len(prices)}日低位（位置分位{price_pos:.1%}），安全边际较高")
        else:
            details.append(f"当前价格处于近{len(prices)}日中间位置")

        # 波动率分析
        pct_changes = [abs(q.get("pct_change", 0)) for q in quotes[-20:]]
        avg_volatility = sum(pct_changes) / len(pct_changes)
        if avg_volatility > 3:
            score -= 3
            details.append(f"近20日日均振幅{avg_volatility:.1f}%，波动率较高，适合短线但风险大")
        elif avg_volatility < 1.5:
            score += 3
            details.append(f"近20日日均振幅{avg_volatility:.1f}%，波动率较低，走势平稳")

        # 当日走势分析
        pct = latest.get("pct_change", 0)
        if pct < -5:
            score -= 5
            reasons.append("当日大跌，可能有未知利空，建议先观望")
            details.append(f"今日跌幅{pct:.1f}%，注意风险")

        return {
            "score": max(0, min(100, score)),
            "dimension": "基本面",
            "reasons": reasons[:5],
            "details": details,
            "industry_analysis": industry_analysis,
            "cap_analysis": cap_analysis,
            "price_position": round(price_pos * 100, 1),
        }

    def _catalyst_agent(self, quotes: List[Dict], indicators: List[Dict]) -> Dict:
        """催化剂深度分析Agent"""
        score = 50
        reasons = []
        details = []
        momentum_signals = []

        # 短期动量分析
        recent_pct = [q.get("pct_change", 0) for q in quotes[-5:]]
        recent_pct_filtered = [p for p in recent_pct if p is not None]
        
        if len(recent_pct_filtered) >= 3:
            if all(p > 0 for p in recent_pct_filtered[-3:]):
                score += 10
                reasons.append("连续3日上涨，短期强势确立")
                momentum_signals.append("连续上涨")
            elif all(p < 0 for p in recent_pct_filtered[-3:]):
                score -= 12
                reasons.append("连续3日下跌，短期趋势转弱")
                momentum_signals.append("连续下跌")

        # 5日涨跌幅
        if len(recent_pct_filtered) >= 5:
            five_day_return = sum(recent_pct_filtered)
            if five_day_return > 10:
                score -= 5
                details.append(f"近5日累计涨幅{five_day_return:.1f}%，注意短期回调风险")
            elif five_day_return < -10:
                score += 5
                details.append(f"近5日累计跌幅{five_day_return:.1f}%，可能存在超跌反弹机会")

        # 量价突破分析
        vol = [q["volume"] for q in quotes]
        if len(vol) >= 6:
            avg_vol_prev = sum(vol[-6:-1]) / 5
            if vol[-1] > avg_vol_prev * 2 and quotes[-1]["close"] > quotes[-2]["close"]:
                score += 15
                reasons.append("放量突破上涨，可能是行情起点，值得重点关注")
                momentum_signals.append("放量突破")
                details.append(f"今日成交量放大{vol[-1]/avg_vol_prev:.1f}倍，伴随价格上涨")
            elif vol[-1] > avg_vol_prev * 1.5 and quotes[-1]["close"] > quotes[-2]["close"]:
                score += 8
                reasons.append("量增价涨，趋势可能延续")
                momentum_signals.append("量增价涨")

        # 技术指标信号强化
        if indicators and len(indicators) >= 5:
            ind_now = indicators[-1]
            ind_prev = indicators[-2]
            macd_bar_now = ind_now.get("macd_bar", 0)
            macd_bar_prev = ind_prev.get("macd_bar", 0)
            rsi_6 = ind_now.get("rsi_6", 50)
            rsi_12 = ind_now.get("rsi_12", 50)

            # MACD 强化分析
            if macd_bar_now is not None and macd_bar_prev is not None:
                if macd_bar_prev < 0 < macd_bar_now:
                    score += 12
                    reasons.append("MACD金叉（柱由负转正），这是较为可靠的买点信号")
                    momentum_signals.append("MACD金叉")
                elif macd_bar_prev > 0 > macd_bar_now:
                    score -= 12
                    reasons.append("MACD死叉，注意回调风险")
                    momentum_signals.append("MACD死叉")

            # RSI 底背离/顶背离（简化）
            if rsi_6 is not None and rsi_12 is not None:
                if rsi_6 > rsi_12:
                    details.append("RSI6在RSI12上方，短期相对强势")
                elif rsi_6 < rsi_12:
                    details.append("RSI6在RSI12下方，短期相对弱势")

        return {
            "score": max(0, min(100, score)),
            "dimension": "催化剂",
            "reasons": reasons[:5],
            "details": details,
            "momentum_signals": momentum_signals,
        }

    def _bull_bear_analysis(self, tech: Dict, fund: Dict, catalyst: Dict) -> Dict:
        """多空对比分析"""
        bullish = []
        bearish = []
        neutral = []

        # 整理看多理由
        for reason in tech.get("reasons", []) + fund.get("reasons", []) + catalyst.get("reasons", []):
            if any(keyword in reason for keyword in ["上涨", "多头", "金叉", "放量", "强势", "站上", "健康", "机会", "突破"]):
                bullish.append(reason)

        # 整理看空理由
        for reason in tech.get("reasons", []) + fund.get("reasons", []) + catalyst.get("reasons", []):
            if any(keyword in reason for keyword in ["下跌", "空头", "死叉", "下跌", "弱势", "跌破", "风险", "注意"]):
                bearish.append(reason)

        # 信号
        for signal in tech.get("signals", []):
            if signal.get("type") == "bullish":
                bullish.append(f"{signal.get('name')}信号（{signal.get('strength')}）")
            elif signal.get("type") == "bearish":
                bearish.append(f"{signal.get('name')}信号（{signal.get('strength')}）")

        for signal in catalyst.get("momentum_signals", []):
            if "突破" in signal or "上涨" in signal:
                bullish.append(f"动量信号：{signal}")
            elif "下跌" in signal or "死叉" in signal:
                bearish.append(f"动量信号：{signal}")

        # 维度强弱
        scores = [tech.get("score", 50), fund.get("score", 50), catalyst.get("score", 50)]
        if tech.get("score", 50) > 70:
            bullish.append(f"技术面评分{tech.get('score')}，表现优秀")
        elif tech.get("score", 50) < 30:
            bearish.append(f"技术面评分{tech.get('score')}，表现较弱")

        # 去重
        bullish = list(set(bullish))[:5]
        bearish = list(set(bearish))[:5]

        return {
            "bullish": bullish,
            "bearish": bearish,
            "neutral": neutral,
            "bull_bear_balance": "偏多" if len(bullish) > len(bearish) + 1 else "偏空" if len(bearish) > len(bullish) + 1 else "中性",
        }

    def _extract_key_signals(self, quotes: List[Dict], indicators: List[Dict]) -> List[Dict]:
        """提取关键信号"""
        signals = []
        latest = quotes[-1] if quotes else {}
        prev = quotes[-2] if len(quotes) > 1 else latest

        # 趋势信号
        close = [q["close"] for q in quotes[-20:]] if len(quotes) >= 20 else []
        if len(close) >= 20:
            ma20 = sum(close) / 20
            if latest.get("close", 0) > ma20 * 1.02:
                signals.append({
                    "type": "bullish",
                    "name": "价格站上MA20",
                    "importance": "高",
                    "description": "价格站上20日均线，短期趋势可能转强",
                })
            elif latest.get("close", 0) < ma20 * 0.98:
                signals.append({
                    "type": "bearish",
                    "name": "价格跌破MA20",
                    "importance": "高",
                    "description": "价格跌破20日均线，注意短期风险",
                })

        # 成交量信号
        if len(quotes) >= 10:
            vol_list = [q.get("volume", 0) for q in quotes[-10:]]
            avg_vol = sum(vol_list[:-1]) / 9 if len(vol_list) > 1 else vol_list[0]
            latest_vol = vol_list[-1] if vol_list else 0
            if latest_vol > avg_vol * 2:
                direction = "向上" if latest.get("close", 0) > prev.get("close", 0) else "向下"
                signals.append({
                    "type": "important",
                    "name": "成交量异常放大",
                    "importance": "高",
                    "description": f"今日成交量较前9日均值放大{latest_vol/avg_vol:.1f}倍，方向{direction}，需要重点关注",
                })

        # 技术指标信号
        if indicators and len(indicators) >= 5:
            ind = indicators[-1]
            rsi = ind.get("rsi_6", 50)
            if rsi and rsi > 80:
                signals.append({
                    "type": "bearish",
                    "name": "RSI超买",
                    "importance": "中",
                    "description": f"RSI6={rsi:.1f}，进入超买区域，注意回调",
                })
            elif rsi and rsi < 30:
                signals.append({
                    "type": "bullish",
                    "name": "RSI超卖",
                    "importance": "中",
                    "description": f"RSI6={rsi:.1f}，进入超卖区域，可能反弹",
                })

        # 涨跌幅信号
        pct = latest.get("pct_change", 0)
        if pct and abs(pct) > 5:
            signals.append({
                "type": "important",
                "name": "大幅波动",
                "importance": "中",
                "description": f"今日涨跌幅{pct:.1f}%，波动较大，关注原因",
            })

        return signals[:5]

    def _operation_suggestion(self, total: float, quotes: List[Dict], indicators: List[Dict]) -> Dict:
        """操作建议"""
        latest = quotes[-1] if quotes else {}
        close = [q["close"] for q in quotes[-30:]] if len(quotes) >= 30 else []

        # 计算关键价位
        entry_point = None
        stop_loss = None
        target_price = None
        
        if close:
            recent_low = min(close[-20:])
            recent_high = max(close[-20:])
            current_price = close[-1]
            entry_point = round(current_price * 0.97, 2)  # 回踩3%建仓
            stop_loss = round(min(recent_low, current_price * 0.9), 2)  # 止损10%或新低
            target_price = round(current_price * 1.1, 2)  # 目标10%

        # 根据评分给出仓位建议
        position_suggestion = "空仓"
        if total >= 75:
            position_suggestion = "建议3-5成仓位"
        elif total >= 60:
            position_suggestion = "建议2-3成仓位"
        elif total >= 50:
            position_suggestion = "建议观望，1成以内仓位轻仓试盘"

        return {
            "position_suggestion": position_suggestion,
            "entry_point": entry_point,
            "stop_loss": stop_loss,
            "target_price": target_price,
            "risk_level": "高" if total < 50 else "中" if total < 70 else "低",
            "suggestions": [
                f"当前综合评分{total}分",
                "不建议重仓追高",
                "分批建仓，及时止损",
            ] if total >= 60 else [
                f"当前综合评分{total}分，以观望为主",
                "若参与，严格控制仓位，设置止损",
            ],
        }

    def _verdict(self, total: float, tech: Dict, fund: Dict, catalyst: Dict) -> Dict:
        if total >= 75:
            action = "值得关注"
            color = "#dc2626"
        elif total >= 55:
            action = "观望"
            color = "#d97706"
        else:
            action = "回避"
            color = "#16a34a"

        dims = [tech, fund, catalyst]
        best = max(dims, key=lambda x: x["score"])
        worst = min(dims, key=lambda x: x["score"])

        return {
            "action": action,
            "color": color,
            "summary": f"综合评分{total}分。{best['dimension']}最佳({best['score']}分)，{worst['dimension']}需注意({worst['score']}分)。",
        }

    # ——————————————————————————————————————————
    # LLM 深度分析报告
    # ——————————————————————————————————————————

    async def _get_llm_config(self) -> dict:
        """获取LLM配置（优先数据库自定义配置，回退环境变量）"""
        try:
            config = await self.db["llm_config"].find_one({"is_active": True})
            if config and config.get("api_key"):
                return {
                    "api_key": config["api_key"],
                    "base_url": config.get("base_url", ""),
                    "model": config.get("model", ""),
                }
        except Exception:
            pass
        return {
            "api_key": settings.LLM_API_KEY,
            "base_url": settings.LLM_BASE_URL,
            "model": settings.LLM_MODEL,
        }

    def _is_llm_available(self, llm_config: dict) -> bool:
        return bool(llm_config.get("api_key"))

    def _build_deep_report_prompt(
        self,
        ts_code: str,
        name: str,
        latest: dict,
        technical: dict,
        fundamental: dict,
        catalyst: dict,
        total_score: float,
    ) -> str:
        """构建LLM深度分析报告的system prompt"""
        tech_signals = json.dumps(technical.get("signals", []), ensure_ascii=False)
        tech_reasons = json.dumps(technical.get("reasons", []), ensure_ascii=False)
        fund_reasons = json.dumps(fundamental.get("reasons", []), ensure_ascii=False)
        cat_reasons = json.dumps(catalyst.get("reasons", []), ensure_ascii=False)

        return f"""你是一个专业的A股投资分析师。请基于以下数据，为股票撰写一份专业、精炼的中文投资分析报告。

【股票信息】
代码：{ts_code}
名称：{name}
最新收盘价：{latest.get('close', 0):.2f}元
当日涨跌幅：{latest.get('pct_change', 0):.2f}%

【评分】
综合评分：{total_score}分（满分100）
技术面：{technical.get('score', 0)}分 — 趋势：{technical.get('trend_strength', '未知')}
基本面：{fundamental.get('score', 0)}分
催化剂：{catalyst.get('score', 0)}分

【技术面分析】
趋势强度：{technical.get('trend_strength', '未知')}
指标状态：MACD({technical.get('indicators_status', {}).get('macd', '未知')}) RSI({technical.get('indicators_status', {}).get('rsi', '未知')}) KDJ({technical.get('indicators_status', {}).get('kdj', '未知')})
支撑/压力：弱支撑{technical.get('support_resistance', {}).get('weak_support', 'N/A')} 强支撑{technical.get('support_resistance', {}).get('strong_support', 'N/A')} 弱压力{technical.get('support_resistance', {}).get('weak_resistance', 'N/A')} 强压力{technical.get('support_resistance', {}).get('strong_resistance', 'N/A')}
技术信号：{tech_signals}
判断理由：{tech_reasons}

【基本面分析】
行业：{fundamental.get('industry_analysis', '未知')}
市值特征：{fundamental.get('cap_analysis', '未知')}
价格位置分位：{fundamental.get('price_position', 50):.0f}%
判断理由：{fund_reasons}

【催化剂分析】
动量信号：{json.dumps(catalyst.get('momentum_signals', []), ensure_ascii=False)}
判断理由：{cat_reasons}

请按照以下格式输出分析报告（用纯文本，不要JSON）：

## 核心观点
（1-2句话总结该股票的投资价值，明确态度：看多/看空/观望）

## 技术面研判
（对趋势、指标、量价的综合解读，2-3句话）

## 基本面评估
（行业地位、估值水平、流动性的评估，1-2句话）

## 催化剂与风险
（短期驱动因素和需要警惕的风险，2-3句话）

## 操作建议
（给出具体的操作思路：关注区间、止损参考、仓位建议）

注意：
- 语言专业但易懂，面向有一定经验的散户投资者
- 不给出绝对的买卖建议，强调风险提示
- 控制总字数在300字以内，精简有力"""

    async def _generate_llm_deep_report(
        self,
        ts_code: str,
        name: str,
        latest: dict,
        technical: dict,
        fundamental: dict,
        catalyst: dict,
        total_score: float,
    ) -> dict:
        """使用LLM生成深度分析报告。LLM不可用时返回结构化摘要。"""
        llm_config = await self._get_llm_config()

        # LLM不可用 → 返回结构化摘要作为降级方案
        if not self._is_llm_available(llm_config):
            return self._build_fallback_report(
                ts_code, name, latest, technical, fundamental, catalyst, total_score
            )

        prompt = self._build_deep_report_prompt(
            ts_code, name, latest, technical, fundamental, catalyst, total_score
        )

        # —— Redis 缓存（相同股票+日期 5分钟内不重复调用） ——
        cache_key = f"llm_report:{ts_code}:{latest.get('trade_date', '')}"
        try:
            from app.core.database import redis_client
            from app.infrastructure.cache import RedisCache
            cache = RedisCache(redis_client)
            cached = await cache.get(hashlib.md5(cache_key.encode()).hexdigest())
            if cached:
                return cached
        except Exception:
            pass

        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=llm_config["api_key"],
                base_url=llm_config["base_url"],
            )

            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.chat.completions.create,
                    model=llm_config["model"] or "gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": f"请分析{name}({ts_code})"},
                    ],
                    temperature=0.4,
                    max_tokens=800,
                ),
                timeout=12.0,
            )

            raw_text = response.choices[0].message.content.strip()
            report = {
                "source": "llm",
                "model": llm_config.get("model", ""),
                "raw": raw_text,
                "sections": self._parse_report_sections(raw_text),
            }

            # 写入缓存
            try:
                await cache.set(
                    hashlib.md5(cache_key.encode()).hexdigest(),
                    report,
                    ttl=300,
                )
            except Exception:
                pass

            return report

        except asyncio.TimeoutError:
            print(f"  [llm_report] LLM超时: {ts_code}")
        except Exception as e:
            print(f"  [llm_report] LLM调用失败: {ts_code} — {e}")

        return self._build_fallback_report(
            ts_code, name, latest, technical, fundamental, catalyst, total_score
        )

    def _build_fallback_report(
        self,
        ts_code: str,
        name: str,
        latest: dict,
        technical: dict,
        fundamental: dict,
        catalyst: dict,
        total_score: float,
    ) -> dict:
        """LLM不可用时，用结构化摘要作为降级方案"""
        action = "回避"
        if total_score >= 75:
            action = "值得关注"
        elif total_score >= 55:
            action = "观望"

        lines = [
            f"## 核心观点",
            f"综合评分{total_score}分，建议{action}。{technical.get('trend_strength', '震荡')}趋势。",
            "",
            f"## 技术面研判",
            f"趋势：{technical.get('trend_strength', '未知')}。"
            f"指标状态：MACD {technical.get('indicators_status', {}).get('macd', '中性')}、"
            f"RSI {technical.get('indicators_status', {}).get('rsi', '中性')}、"
            f"KDJ {technical.get('indicators_status', {}).get('kdj', '中性')}。",
            "；".join(technical.get("reasons", [])[:3]),
            "",
            f"## 基本面评估",
            f"行业：{fundamental.get('industry_analysis', '未知')}。{fundamental.get('cap_analysis', '未知')}。",
            "；".join(fundamental.get("reasons", [])[:2]),
            "",
            f"## 催化剂与风险",
            "；".join(catalyst.get("reasons", [])[:3]),
            "",
            f"## 操作建议",
            f"综合评分{total_score}分，注意控制仓位与风险。",
        ]

        raw_text = "\n".join([l for l in lines if l])

        return {
            "source": "fallback",
            "model": "",
            "raw": raw_text,
            "sections": self._parse_report_sections(raw_text),
        }

    def _parse_report_sections(self, raw_text: str) -> dict:
        """从LLM输出中解析各章节"""
        sections = {}
        current_key = None
        for line in raw_text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("## "):
                current_key = stripped[3:].strip()
                sections[current_key] = []
            elif current_key and stripped:
                sections[current_key].append(stripped)
        return {k: "\n".join(v) for k, v in sections.items()}

    async def analyze_batch(self, ts_codes: List[str], skip_llm: bool = True) -> List[Dict]:
        """批量分析（并行 + 信号量控制并发）

        Args:
            ts_codes: 股票代码列表
            skip_llm: 是否跳过LLM深度报告（默认True，讨论面板不需要LLM报告）
        """
        import asyncio
        sem = asyncio.Semaphore(5)

        async def _analyze(code: str) -> Dict:
            async with sem:
                try:
                    return await self.analyze_stock(code, skip_llm=skip_llm)
                except Exception as e:
                    return {"ts_code": code, "error": str(e)}

        tasks = [_analyze(code) for code in ts_codes]
        results = await asyncio.gather(*tasks)
        results = [r for r in results if r is not None]
        results.sort(key=lambda x: x.get("total_score", 0), reverse=True)
        return results
