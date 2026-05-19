import json
import re
import hashlib
import asyncio
import time
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.screener import ScreenerCondition
from app.services.screener_service import ScreenerService
from app.core.config import settings

_LLM_CACHE_TTL = 300
_INDUSTRY_LIST_TTL = 3600
_CACHE_PREFIX_LLM = "llm:"
_CACHE_PREFIX_INDUSTRY = "industry_list"


def _get_cache() -> "RedisCache":
    """延迟获取 Redis 缓存实例，避免导入时 Redis 未初始化"""
    from app.core.database import redis_client
    from app.infrastructure.cache import RedisCache
    return RedisCache(redis_client)

FAST_KEYWORD_MAP = {
    "金叉": [ScreenerCondition(category="technical", field="macd_cross", op="eq", value=True)],
    "macd金叉": [ScreenerCondition(category="technical", field="macd_cross", op="eq", value=True)],
    "死叉": [ScreenerCondition(category="technical", field="macd_cross", op="eq", value=False)],
    "kdj金叉": [ScreenerCondition(category="technical", field="kdj_cross", op="eq", value=True)],
    "均线多头": [ScreenerCondition(category="technical", field="ma_bullish", op="eq", value=True)],
    "多头排列": [ScreenerCondition(category="technical", field="ma_bullish", op="eq", value=True)],
    "均线空头": [ScreenerCondition(category="technical", field="ma_bearish", op="eq", value=True)],
    "空头排列": [ScreenerCondition(category="technical", field="ma_bearish", op="eq", value=True)],
    "超卖": [ScreenerCondition(category="technical", field="rsi_oversold", op="eq", value=True)],
    "超买": [ScreenerCondition(category="technical", field="rsi_overbought", op="eq", value=True)],
    "超跌反弹": [ScreenerCondition(category="technical", field="rsi_oversold", op="eq", value=True)],
    "超跌": [ScreenerCondition(category="technical", field="rsi_oversold", op="eq", value=True)],
    "底部": [ScreenerCondition(category="technical", field="rsi_oversold", op="eq", value=True)],
    "抄底": [ScreenerCondition(category="technical", field="rsi_oversold", op="eq", value=True)],
    "见底": [ScreenerCondition(category="technical", field="rsi_oversold", op="eq", value=True)],
    "突破": [ScreenerCondition(category="pattern", field="breakout_20d_high", op="eq", value=True)],
    "新高": [ScreenerCondition(category="pattern", field="breakout_20d_high", op="eq", value=True)],
    "放量": [ScreenerCondition(category="technical", field="volume_surge", op="eq", value=True)],
    "缩量": [ScreenerCondition(category="technical", field="volume_shrink", op="eq", value=True)],
    "低估": [ScreenerCondition(category="fundamental", field="pe", op="range", min=0, max=20)],
    "低估值": [ScreenerCondition(category="fundamental", field="pe", op="range", min=0, max=25)],
    "低价": [ScreenerCondition(category="quote", field="price", op="range", min=0, max=20)],
    "低价股": [ScreenerCondition(category="quote", field="price", op="range", min=0, max=20)],
    "大盘股": [ScreenerCondition(category="fundamental", field="total_mv", op="gt", value=5000000)],
    "小盘股": [ScreenerCondition(category="fundamental", field="total_mv", op="range", min=0, max=1000000)],
    "中盘股": [ScreenerCondition(category="fundamental", field="total_mv", op="range", min=1000000, max=5000000)],
    "高股息": [ScreenerCondition(category="fundamental", field="dividend_yield", op="gt", value=3)],
    "上涨": [ScreenerCondition(category="quote", field="pct_change", op="gt", value=0)],
    "大涨": [ScreenerCondition(category="quote", field="pct_change", op="gt", value=3)],
    "破净": [ScreenerCondition(category="fundamental", field="pb", op="range", min=0, max=1)],
    "高ROE": [ScreenerCondition(category="fundamental", field="roe", op="gt", value=15)],
    "连涨": [ScreenerCondition(category="technical", field="continuous_up_3d", op="eq", value=True)],
    "连续上涨": [ScreenerCondition(category="technical", field="continuous_up_3d", op="eq", value=True)],
    "连续放量": [ScreenerCondition(category="technical", field="continuous_volume_3d", op="eq", value=True)],
    "V型反转": [ScreenerCondition(category="technical", field="v_shape_recovery", op="eq", value=True)],
    "盘整": [ScreenerCondition(category="technical", field="consolidation", op="eq", value=True)],
    "横盘": [ScreenerCondition(category="technical", field="consolidation", op="eq", value=True)],
    "布林突破": [ScreenerCondition(category="technical", field="boll_breakout_up", op="eq", value=True)],
    "布林破下": [ScreenerCondition(category="technical", field="boll_breakout_down", op="eq", value=True)],
    "60日新高": [ScreenerCondition(category="pattern", field="breakout_60d_high", op="eq", value=True)],
    "20日新高": [ScreenerCondition(category="pattern", field="breakout_20d_high", op="eq", value=True)],
    "创新低": [ScreenerCondition(category="pattern", field="drop_20d_low", op="eq", value=True)],
    "高换手": [ScreenerCondition(category="quote", field="turnover_rate", op="gt", value=8)],
    "换手率高": [ScreenerCondition(category="quote", field="turnover_rate", op="gt", value=8)],
    "活跃": [ScreenerCondition(category="quote", field="turnover_rate", op="gt", value=5)],
    "高成长": [ScreenerCondition(category="fundamental", field="profit_growth", op="gt", value=30)],
    "业绩增长": [ScreenerCondition(category="fundamental", field="profit_growth", op="gt", value=20)],
    "营收增长": [ScreenerCondition(category="fundamental", field="revenue_growth", op="gt", value=20)],
    "白马股": [ScreenerCondition(category="fundamental", field="roe", op="gt", value=15)],
    "蓝筹": [ScreenerCondition(category="fundamental", field="total_mv", op="gt", value=5000000)],
    "龙头": [ScreenerCondition(category="fundamental", field="total_mv", op="gt", value=3000000)],
    "强势": [ScreenerCondition(category="quote", field="pct_change", op="gt", value=2)],
    "弱势": [ScreenerCondition(category="quote", field="pct_change", op="lt", value=-2)],
    "涨停": [ScreenerCondition(category="quote", field="pct_change", op="gt", value=9)],
    "跌停": [ScreenerCondition(category="quote", field="pct_change", op="lt", value=-9)],
    "绩优": [ScreenerCondition(category="fundamental", field="roe", op="gt", value=10)],
    "绩优股": [ScreenerCondition(category="fundamental", field="roe", op="gt", value=10)],
    "价值股": [ScreenerCondition(category="fundamental", field="pe", op="range", min=0, max=20)],
    "成长股": [ScreenerCondition(category="fundamental", field="profit_growth", op="gt", value=20)],
    "抗跌": [ScreenerCondition(category="quote", field="pct_change", op="gt", value=-1)],
    "红盘": [ScreenerCondition(category="quote", field="pct_change", op="gt", value=0)],
}


def _build_system_prompt(industry_list: List[str]) -> str:
    industries_str = "、".join(industry_list)
    return f"""你是一个A股选股助手。用户会用自然语言描述想找什么样的股票，你需要将其解析为结构化的筛选条件。

可选的筛选条件类别和字段如下：

1. 技术信号(technical): macd_cross(MACD金叉), kdj_cross(KDJ金叉), ma_bullish(均线多头), ma_bearish(均线空头), rsi_oversold(RSI超卖), rsi_overbought(RSI超买), volume_surge(放量), volume_shrink(缩量), boll_breakout_up(布林突破上轨), boll_breakout_down(布林跌破下轨), v_shape_recovery(V型反转), consolidation(缩量盘整), continuous_up_3d(连涨3日), continuous_volume_3d(连续放量3日)

2. 形态信号(pattern): breakout_20d_high(突破20日新高), breakout_60d_high(突破60日新高), drop_20d_low(跌破20日新低)

3. 基本面(fundamental): pe(市盈率), pb(市净率), roe(净资产收益率%), dividend_yield(股息率%), total_mv(总市值,万元), revenue_growth(营收增长率%), profit_growth(净利润增长率%)

4. 行情(quote): price(股价,元), pct_change(涨跌幅%), turnover_rate(换手率%), volume(成交量), amount(成交额)

5. 行业(industry): 必须从以下行业列表中选择（可多选）：{industries_str}

请输出JSON格式，包含以下字段：
- "conditions": 条件数组，每个条件包含 category, field, op(eq/gt/lt/gte/lte/range), value(用于eq), min/max(用于range)
- "industries": 行业名称数组（必须从上面的行业列表中选择，不要自己编造行业名）
- "explanation": 简短解释你识别了哪些条件（一句话）

示例输入："PCB龙头，近期放量"
示例输出：
{{
  "conditions": [
    {{"category": "fundamental", "field": "total_mv", "op": "gt", "value": 3000000}},
    {{"category": "technical", "field": "volume_surge", "op": "eq", "value": true}}
  ],
  "industries": ["元器件", "电子制造"],
  "explanation": "筛选PCB行业（元器件、电子制造）的大市值龙头股，且近期放量"
}}

示例输入："AI算力概念"
示例输出：
{{
  "conditions": [],
  "industries": ["IT设备", "半导体", "软件服务"],
  "explanation": "筛选AI算力相关行业（IT设备、半导体、软件服务）"
}}

注意：
- 不要过度解读，只提取用户明确表达的条件
- 行业必须从上面的行业列表中选择，用户说的概念词（如PCB、CPO、AI等）需要你映射到列表中最接近的行业
- 一个概念可能对应多个行业，如"PCB"对应"元器件"和"电子制造"，"低空经济"对应"航空"和"专用机械"，"固态电池"对应"电气设备"
- 如果用户提到的概念没有直接对应的行业名，请选择最相关的1-3个行业
- 如果用户描述模糊，给出最合理的解读
- 只输出JSON，不要输出其他内容"""


async def _get_llm_config(db) -> dict:
    try:
        config = await db["llm_config"].find_one({"is_active": True})
        if config and config.get("api_key"):
            return {
                "api_key": config["api_key"],
                "base_url": config.get("base_url", ""),
                "model": config.get("model", ""),
                "name": config.get("name", ""),
            }
    except Exception:
        pass
    return {
        "api_key": settings.LLM_API_KEY,
        "base_url": settings.LLM_BASE_URL,
        "model": settings.LLM_MODEL,
        "name": "",
    }


def _get_llm_client(config: dict):
    from openai import OpenAI
    return OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
    )


def _is_llm_available(config: dict) -> bool:
    return bool(config.get("api_key"))


async def _get_industry_list(db) -> List[str]:
    try:
        cache = _get_cache()
        cached = await cache.get(_CACHE_PREFIX_INDUSTRY)
        if cached is not None:
            return cached
    except Exception:
        pass
    try:
        cursor = db["stocks"].distinct("industry")
        industries = await cursor if hasattr(cursor, '__await__') else cursor
        industries = sorted([i for i in industries if i])
        try:
            await cache.set(_CACHE_PREFIX_INDUSTRY, industries, ttl=_INDUSTRY_LIST_TTL)
        except Exception:
            pass
        return industries
    except Exception:
        return []


async def _call_llm(query: str, industry_list: List[str], config: dict) -> Optional[Dict]:
    if not _is_llm_available(config):
        return None
    try:
        cache = _get_cache()
        cache_key = f"{_CACHE_PREFIX_LLM}{hashlib.md5(query.encode()).hexdigest()}"
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached
    except Exception:
        pass

    try:
        client = _get_llm_client(config)
        system_prompt = _build_system_prompt(industry_list)
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.chat.completions.create,
                model=config["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.1,
                max_tokens=1024,
            ),
            timeout=8.0,
        )
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            result = json.loads(json_match.group())
            try:
                await cache.set(cache_key, result, ttl=_LLM_CACHE_TTL)
            except Exception:
                pass
            return result
        return None
    except asyncio.TimeoutError:
        print("  [ai_pick] LLM调用超时(8s)")
        return None
    except Exception as e:
        print(f"  [ai_pick] LLM调用失败: {e}")
        return None


def _parse_llm_result(llm_result: Dict, valid_industries: List[str]) -> tuple[List[ScreenerCondition], List[str], str]:
    conditions = []
    for c in llm_result.get("conditions", []):
        try:
            cond = ScreenerCondition(
                category=c.get("category", "quote"),
                field=c.get("field", ""),
                op=c.get("op", "eq"),
                value=c.get("value"),
                min=c.get("min"),
                max=c.get("max"),
            )
            if cond.field:
                conditions.append(cond)
        except Exception:
            continue
    raw_industries = llm_result.get("industries", [])
    explanation = llm_result.get("explanation", "")
    if isinstance(raw_industries, str):
        raw_industries = [raw_industries]
    valid_set = set(valid_industries)
    industries = [ind for ind in raw_industries if ind in valid_set]
    return conditions, industries, explanation


def _build_chat_system_prompt(industry_list: List[str]) -> str:
    industries_str = "、".join(industry_list)
    return f"""你是一个A股智能选股助手，帮助用户通过对话筛选A股股票。

你可以做以下几件事：
1. 回答用户关于选股条件的问题
2. 根据用户描述解析出筛选条件
3. 判断用户是否想要筛选股票（should_search）
4. 提供选股建议和分析

可选筛选条件：
- 技术信号(technical): macd_cross(MACD金叉), kdj_cross(KDJ金叉), ma_bullish(均线多头), ma_bearish(均线空头), rsi_oversold(RSI超卖), rsi_overbought(RSI超买), volume_surge(放量), volume_shrink(缩量), boll_breakout_up(布林突破上轨), boll_breakout_down(布林跌破下轨), v_shape_recovery(V型反转), consolidation(缩量盘整), continuous_up_3d(连涨3日), continuous_volume_3d(连续放量3日)
- 形态(pattern): breakout_20d_high(突破20日新高), breakout_60d_high(突破60日新高), drop_20d_low(跌破20日新低)
- 基本面(fundamental): pe(市盈率), pb(市净率), roe(净资产收益率%), dividend_yield(股息率%), total_mv(总市值,万元), revenue_growth(营收增长率%), profit_growth(净利润增长率%)
- 行情(quote): price(股价,元), pct_change(涨跌幅%), turnover_rate(换手率%), volume(成交量)
- 行业: 从以下列表中选择（可多选）：{industries_str}

请输出JSON格式：
{{
  "text": "你对用户的自然语言回复（简短、专业、有温度）",
  "conditions": [
    {{"category": "technical", "field": "macd_cross", "op": "eq", "value": true}}
  ],
  "industries": ["行业名1", "行业名2"],
  "should_search": true
}}

规则：
- text 字段用中文回复，简短专业
- 如果用户在问选股相关、想要筛选股票，设置 should_search=true 并解析条件
- 如果用户只是闲聊或问问题（如"AI能做什么"、"今天行情怎么样"），设置 should_search=false，不给条件和行业
- 行业名必须从上面的行业列表中选择
- 只输出JSON，不要其他内容"""


async def _call_chat_llm(messages: List[Dict], config: dict) -> Optional[Dict]:
    if not _is_llm_available(config):
        return None
    try:
        client = _get_llm_client(config)
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.chat.completions.create,
                model=config["model"],
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            ),
            timeout=12.0,
        )
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
        return None
    except asyncio.TimeoutError:
        print("  [ai_chat] LLM调用超时(12s)")
        return None
    except Exception as e:
        print(f"  [ai_chat] LLM调用失败: {e}")
        return None


def _build_chat_messages(query: str, history: List[dict], industry_list: List[str]) -> List[Dict]:
    system_prompt = _build_chat_system_prompt(industry_list)
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        if msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": query})
    return messages


class ScreenerAIService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.screener_service = ScreenerService(db)

    async def parse_natural_language(self, query: str) -> Dict:
        llm_config = await _get_llm_config(self.db)
        conditions = []
        matched_keywords = []
        seen_fields = set()

        query_lower = query.lower()
        sorted_keywords = sorted(FAST_KEYWORD_MAP.keys(), key=len, reverse=True)
        for keyword in sorted_keywords:
            if keyword.lower() in query_lower:
                keyword_conds = FAST_KEYWORD_MAP[keyword]
                keyword_fields = tuple(c.field for c in keyword_conds)
                if keyword_fields in seen_fields:
                    matched_keywords.append(keyword)
                    continue
                seen_fields.add(keyword_fields)
                conditions.extend(keyword_conds)
                matched_keywords.append(keyword)

        industry_list = await _get_industry_list(self.db)

        llm_result = await _call_llm(query, industry_list, llm_config)
        if llm_result:
            llm_conditions, llm_industries, explanation = _parse_llm_result(llm_result, industry_list)
            if llm_conditions or llm_industries:
                merged_conditions = list(conditions)
                merged_fields = {c.field for c in merged_conditions}
                for c in llm_conditions:
                    if c.field not in merged_fields:
                        merged_conditions.append(c)
                        merged_fields.add(c.field)
                return {
                    "query": query,
                    "matched_keywords": matched_keywords,
                    "matched_industries": llm_industries,
                    "matched_industry_groups": llm_result.get("industries", []),
                    "conditions": [c.model_dump() for c in merged_conditions],
                    "explanation": explanation,
                    "source": "llm",
                }

        if not conditions:
            conditions.append(ScreenerCondition(category="quote", field="pct_change", op="gt", value=0))

        return {
            "query": query,
            "matched_keywords": matched_keywords,
            "matched_industries": [],
            "matched_industry_groups": [],
            "conditions": [c.model_dump() for c in conditions],
            "explanation": "",
            "source": "keyword",
        }

    async def ai_pick(self, query: str) -> Dict:
        t0 = time.time()
        parse_result = await self.parse_natural_language(query)
        t1 = time.time()
        conditions = [ScreenerCondition(**c) for c in parse_result["conditions"]]
        matched_industries = parse_result.get("matched_industries", [])
        explanation = parse_result.get("explanation", "")
        source = parse_result.get("source", "keyword")

        print(f"  [ai_pick] parse: {t1-t0:.3f}s, source={source}, "
              f"keywords={parse_result['matched_keywords']}, "
              f"industries={parse_result.get('matched_industry_groups', [])}")

        if not conditions and not matched_industries:
            conditions.append(ScreenerCondition(category="quote", field="pct_change", op="gt", value=0))

        all_conditions = []
        if matched_industries:
            all_conditions.append(
                ScreenerCondition(category="quote", field="industry", op="in_", values=matched_industries)
            )
        all_conditions.extend(conditions)

        try:
            result_stocks = await self.screener_service.screen(all_conditions, limit=20)
            t2 = time.time()
            print(f"  [ai_pick] AND query: {t2-t1:.3f}s, results={len(result_stocks)}")
        except Exception as e:
            print(f"  [ai_pick] AND query failed: {e}")
            result_stocks = []
            t2 = time.time()

        if len(result_stocks) < 10:
            condition_groups = []
            if matched_industries:
                condition_groups.append(("industry", [
                    ScreenerCondition(category="quote", field="industry", op="in_", values=matched_industries)
                ]))
            for cond in conditions:
                condition_groups.append((cond.field, [cond]))

            async def _query_group(group_name, group_conds):
                try:
                    return group_name, await self.screener_service.screen(group_conds, limit=200)
                except Exception:
                    return group_name, []

            group_results = await asyncio.gather(*[
                _query_group(name, conds) for name, conds in condition_groups
            ])
            t3 = time.time()
            print(f"  [ai_pick] OR fallback: {t3-t2:.3f}s, groups={len(condition_groups)}")

            all_stocks = {}
            for group_name, stocks in group_results:
                for stock in stocks:
                    ts_code = stock.get("ts_code")
                    if ts_code not in all_stocks:
                        all_stocks[ts_code] = stock
                        all_stocks[ts_code]["_match_score"] = 0
                        all_stocks[ts_code]["_match_tags"] = []
                    all_stocks[ts_code]["_match_score"] += 1
                    all_stocks[ts_code]["_match_tags"].append(group_name)

            sorted_stocks = sorted(
                all_stocks.values(),
                key=lambda x: (x.get("_match_score", 0), x.get("pct_change") or 0),
                reverse=True,
            )
            result_stocks = sorted_stocks[:20]
            for stock in result_stocks:
                tags = stock.pop("_match_tags", [])
                score = stock.pop("_match_score", 0)
                reasons = []
                if "industry" in tags:
                    reasons.append("所属行业匹配")
                for tag in tags:
                    if tag != "industry":
                        tag_label = self._get_tag_label(tag)
                        if tag_label:
                            reasons.append(tag_label)
                if stock.get("pct_change") and stock["pct_change"] > 3:
                    reasons.append("短期强势")
                if stock.get("pe") and 0 < stock["pe"] < 30:
                    reasons.append("估值合理")
                stock["ai_reason"] = "；".join(reasons) if reasons else "部分条件匹配"
                stock["match_score"] = score
        else:
            for stock in result_stocks:
                reasons = []
                if matched_industries:
                    reasons.append("所属行业匹配")
                for cond in conditions:
                    tag_label = self._get_tag_label(cond.field)
                    if tag_label:
                        reasons.append(tag_label)
                if stock.get("pct_change") and stock["pct_change"] > 3:
                    reasons.append("短期强势")
                if stock.get("pe") and 0 < stock["pe"] < 30:
                    reasons.append("估值合理")
                stock["ai_reason"] = "；".join(reasons) if reasons else "符合筛选条件"
                stock["match_score"] = len(reasons)

        t_end = time.time()
        print(f"  [ai_pick] total: {t_end-t0:.3f}s, stocks={len(result_stocks)}")

        return {
            "query": query,
            "matched_keywords": parse_result["matched_keywords"],
            "matched_industries": matched_industries,
            "matched_industry_groups": parse_result.get("matched_industry_groups", []),
            "explanation": explanation,
            "source": source,
            "stocks": result_stocks,
        }

    async def ai_chat(self, query: str, history: List[dict]) -> Dict:
        import traceback
        try:
            llm_config = await _get_llm_config(self.db)
            industry_list = await _get_industry_list(self.db)

            messages = _build_chat_messages(query, history, industry_list)
            llm_result = await _call_chat_llm(messages, llm_config)

            if not llm_result:
                return {
                    "text": "抱歉，我现在无法处理你的请求，请稍后再试。",
                    "conditions": [], "industries": [], "stocks": [], "stock_count": 0,
                }

            text = llm_result.get("text", "")
            conditions_data = llm_result.get("conditions", [])
            industries = llm_result.get("industries", [])
            should_search = llm_result.get("should_search", False)

            conditions = []
            for c in conditions_data:
                if c.get("field"):
                    try:
                        conditions.append(ScreenerCondition(**c))
                    except Exception as e:
                        print(f"  [ai_chat] 条件解析失败: {e}, data={c}")

            # 如果LLM没解析出条件，用关键词兜底
            if not conditions and not industries:
                query_lower = query.lower()
                seen_fields = set()
                sorted_keywords = sorted(FAST_KEYWORD_MAP.keys(), key=len, reverse=True)
                for keyword in sorted_keywords:
                    if keyword.lower() in query_lower:
                        kw_conds = FAST_KEYWORD_MAP[keyword]
                        kw_fields = tuple(c.field for c in kw_conds)
                        if kw_fields not in seen_fields:
                            seen_fields.add(kw_fields)
                            conditions.extend(kw_conds)
                if conditions:
                    should_search = True
                    text = text or f"好的，已识别到相关筛选条件，正在为你筛选..."

            stocks = []
            stock_count = 0

            if should_search and (conditions or industries):
                all_conditions = []
                if industries:
                    valid_set = set(industry_list)
                    valid_industries = [ind for ind in industries if ind in valid_set]
                    if valid_industries:
                        all_conditions.append(
                            ScreenerCondition(category="quote", field="industry", op="in_", values=valid_industries)
                        )
                all_conditions.extend(conditions)
                try:
                    stocks = await self.screener_service.screen(all_conditions, limit=20)
                    stock_count = len(stocks)
                except Exception as e:
                    print(f"  [ai_chat] 筛选失败: {e}")

            return {
                "text": text,
                "conditions": [c.model_dump() for c in conditions],
                "industries": industries,
                "stocks": stocks,
                "stock_count": stock_count,
            }
        except Exception as e:
            print(f"  [ai_chat] 未处理异常: {traceback.format_exc()}")
            return {
                "text": "抱歉，处理时出现内部错误，请稍后重试。",
                "conditions": [], "industries": [], "stocks": [], "stock_count": 0,
            }

    def _get_tag_label(self, field: str) -> str:
        labels = {
            "macd_cross": "MACD金叉", "kdj_cross": "KDJ金叉",
            "ma_bullish": "均线多头", "ma_bearish": "均线空头",
            "rsi_oversold": "RSI超卖", "rsi_overbought": "RSI超买",
            "boll_breakout_up": "布林突破", "boll_breakout_down": "布林破下",
            "volume_surge": "放量", "volume_shrink": "缩量",
            "breakout_20d_high": "突破新高", "breakout_60d_high": "60日新高",
            "drop_20d_low": "创新低", "v_shape_recovery": "V型反转",
            "consolidation": "缩量盘整", "continuous_up_3d": "连涨",
            "continuous_volume_3d": "连续放量",
            "pe": "低估值", "pb": "破净", "roe": "高ROE",
            "dividend_yield": "高股息", "total_mv": "市值匹配",
            "price": "价格匹配", "pct_change": "涨跌幅匹配",
            "turnover_rate": "换手率匹配",
        }
        return labels.get(field, "")

    async def ai_analyze(self, ts_codes: List[str]) -> Dict:
        from app.services.analysis_service import MultiAgentAnalysisService
        analysis_service = MultiAgentAnalysisService(self.db)
        results = await analysis_service.analyze_batch(ts_codes)
        overview = self._generate_overview(results)
        return {
            "overview": overview,
            "stocks": results,
        }

    def _generate_overview(self, results: List[Dict]) -> str:
        if not results:
            return "暂无分析结果"
        avg_score = sum(r.get("total_score", 0) for r in results) / len(results)
        bullish_count = sum(1 for r in results if r.get("total_score", 0) >= 60)
        return f"共分析{len(results)}只股票，平均评分{avg_score:.1f}分，{bullish_count}只评分≥60分。"

    async def get_daily_recommendation(self) -> Dict:
        col = self.db["ai_daily_recommendations"]
        latest = await col.find_one({}, {"_id": 0}, sort=[("date", -1)])
        if latest:
            return latest
        return await self._generate_daily_recommendation()

    async def _generate_daily_recommendation(self) -> Dict:
        from datetime import datetime
        strategies = [
            {
                "title": "均线多头+放量",
                "description": "关注均线多头排列且放量的股票",
                "conditions": [
                    ScreenerCondition(category="technical", field="ma_bullish", op="eq", value=True).model_dump(),
                    ScreenerCondition(category="technical", field="volume_surge", op="eq", value=True).model_dump(),
                ],
            },
            {
                "title": "低估值优质股",
                "description": "PE低于25的优质标的",
                "conditions": [
                    ScreenerCondition(category="fundamental", field="pe", op="range", min=0, max=25).model_dump(),
                ],
            },
        ]
        recommendations = []
        for s in strategies:
            conditions = [ScreenerCondition(**c) for c in s["conditions"]]
            stocks = await self.screener_service.screen(conditions, limit=10)
            recommendations.append({
                "title": s["title"],
                "description": s["description"],
                "conditions": s["conditions"],
                "stocks": stocks[:10],
                "reason": f"筛选出{len(stocks)}只符合条件的股票",
            })
        doc = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "recommendations": recommendations,
        }
        await self.db["ai_daily_recommendations"].replace_one(
            {"date": doc["date"]},
            doc,
            upsert=True,
        )
        return doc
