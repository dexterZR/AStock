import json
import re
import asyncio
import time
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.screener import ScreenerCondition
from app.services.screener_service import ScreenerService
from app.core.config import settings

_LLM_CACHE: Dict[str, tuple] = {}
_LLM_CACHE_TTL = 300

SYSTEM_PROMPT = """你是一个A股选股助手。用户会用自然语言描述想找什么样的股票，你需要将其解析为结构化的筛选条件。

可选的筛选条件类别和字段如下：

1. 技术信号(technical): macd_cross(MACD金叉), kdj_cross(KDJ金叉), ma_bullish(均线多头), ma_bearish(均线空头), rsi_oversold(RSI超卖), rsi_overbought(RSI超买), volume_surge(放量), volume_shrink(缩量), boll_breakout_up(布林突破上轨), boll_breakout_down(布林跌破下轨), v_shape_recovery(V型反转), consolidation(缩量盘整), continuous_up_3d(连涨3日), continuous_volume_3d(连续放量3日)

2. 形态信号(pattern): breakout_20d_high(突破20日新高), breakout_60d_high(突破60日新高), drop_20d_low(跌破20日新低)

3. 基本面(fundamental): pe(市盈率), pb(市净率), roe(净资产收益率%), dividend_yield(股息率%), total_mv(总市值,万元), revenue_growth(营收增长率%), profit_growth(净利润增长率%)

4. 资金(capital): main_net_buy(主力净买入,万元), north_holding_change(北向资金变动%)

5. 行情(quote): price(股价,元), pct_change(涨跌幅%), turnover_rate(换手率%), volume(成交量), amount(成交额)

6. 行业(industry): 行业名称，如银行、地产、医药、白酒、半导体、新能源、汽车、军工、电力、通信、消费、食品、钢铁、煤炭、保险、证券等

请输出JSON格式，包含以下字段：
- "conditions": 条件数组，每个条件包含 category, field, op(eq/gt/lt/gte/lte/range), value(用于eq), min/max(用于range)
- "industries": 行业名称数组（如果用户提到了行业）
- "explanation": 简短解释你识别了哪些条件（一句话）

示例输入："低估值银行股，近期放量"
示例输出：
{
  "conditions": [
    {"category": "fundamental", "field": "pe", "op": "range", "min": 0, "max": 25},
    {"category": "technical", "field": "volume_surge", "op": "eq", "value": true}
  ],
  "industries": ["银行"],
  "explanation": "筛选低估值(PE<25)的银行股，且近期放量"
}

注意：
- 不要过度解读，只提取用户明确表达的条件
- 行业单独放在industries数组里，不要放在conditions里
- 如果用户描述模糊，给出最合理的解读
- 只输出JSON，不要输出其他内容"""

NLP_CONDITION_MAP = {
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
    "高股息": [ScreenerCondition(category="fundamental", field="dividend_yield", op="gt", value=3)],
    "北向": [ScreenerCondition(category="capital", field="north_holding_change", op="gt", value=0)],
    "北向加仓": [ScreenerCondition(category="capital", field="north_holding_change", op="gt", value=0)],
    "主力买入": [ScreenerCondition(category="capital", field="main_net_buy", op="gt", value=0)],
    "主力流入": [ScreenerCondition(category="capital", field="main_net_buy", op="gt", value=0)],
    "上涨": [ScreenerCondition(category="quote", field="pct_change", op="gt", value=0)],
    "大涨": [ScreenerCondition(category="quote", field="pct_change", op="gt", value=3)],
    "破净": [ScreenerCondition(category="fundamental", field="pb", op="range", min=0, max=1)],
    "高ROE": [ScreenerCondition(category="fundamental", field="roe", op="gt", value=15)],
}

INDUSTRY_MAP = {
    "银行": ["银行"],
    "地产": ["房地产", "全国地产", "区域地产", "房产服务"],
    "房地产": ["房地产", "全国地产", "区域地产", "房产服务"],
    "保险": ["保险"],
    "证券": ["证券", "券商"],
    "券商": ["证券", "券商"],
    "医药": ["医药", "医药商业", "化学制药", "生物制药", "中成药", "中药", "医疗器械", "医疗服务", "医疗保健"],
    "医疗": ["医药", "医药商业", "化学制药", "生物制药", "中成药", "中药", "医疗器械", "医疗服务", "医疗保健"],
    "生物": ["生物制药"],
    "生物制药": ["生物制药"],
    "科技": ["半导体", "元器件", "软件", "软件服务", "电子制造", "IT设备", "人工智能", "通信设备"],
    "半导体": ["半导体"],
    "芯片": ["半导体"],
    "新能源": ["新能源", "电气设备"],
    "光伏": ["电气设备", "新型电力"],
    "锂电": ["电气设备"],
    "白酒": ["白酒"],
    "食品": ["食品", "食品饮料", "乳制品", "软饮料", "饲料"],
    "消费": ["白酒", "食品", "食品饮料", "乳制品", "软饮料", "家用电器", "家居用品", "服饰", "百货", "超市连锁", "消费电子", "啤酒", "红黄酒"],
    "家电": ["家用电器", "家居用品"],
    "汽车": ["汽车", "汽车整车", "汽车配件", "汽车零部件", "汽车服务"],
    "军工": ["航天军工", "航空", "船舶", "兵器"],
    "钢铁": ["钢铁", "普钢", "特种钢", "钢加工"],
    "煤炭": ["煤炭", "煤炭开采", "焦炭加工"],
    "电力": ["电力", "火力发电", "水力发电", "新型电力"],
    "通信": ["通信设备", "电信运营"],
    "电信": ["电信运营"],
    "互联网": ["互联网"],
    "软件": ["软件", "软件服务"],
    "游戏": ["互联网", "影视音像"],
    "纺织": ["纺织", "服饰", "纺织机械"],
    "服装": ["服饰", "纺织"],
    "建筑": ["建筑工程", "装修装饰", "建材", "其他建材", "水泥"],
    "建材": ["建材", "其他建材", "水泥", "玻璃", "陶瓷"],
    "机械": ["专用机械", "工程机械", "机械基件", "机床制造", "轻工机械", "化工机械", "纺织机械"],
    "化工": ["化工", "化工原料", "日用化工", "化纤", "塑料", "橡胶", "染料涂料"],
    "石油": ["石油", "石油加工", "石油化工", "石油开采", "石油贸易"],
    "有色": ["有色", "小金属", "铜", "铝", "铅锌", "黄金"],
    "有色金属": ["有色", "小金属", "铜", "铝", "铅锌", "黄金"],
    "铜": ["铜"],
    "铝": ["铝"],
    "农业": ["农业综合", "种植业", "渔业", "林业", "饲料", "农药化肥", "养殖"],
    "养殖": ["养殖", "农业综合", "饲料"],
    "传媒": ["影视音像", "广告包装", "出版业", "文教休闲"],
    "教育": ["文教休闲", "出版业"],
    "旅游": ["旅游", "旅游景点", "旅游服务", "酒店餐饮"],
    "酒店": ["酒店餐饮", "旅游"],
    "餐饮": ["酒店餐饮"],
    "交通运输": ["仓储物流", "物流", "水运", "空运", "航运", "港口", "机场", "公路", "铁路", "路桥", "轨道交通"],
    "航空": ["航空", "空运", "机场"],
    "环保": ["环保", "环境保护", "水务"],
    "电子": ["元器件", "电子制造", "消费电子", "面板", "电器仪表"],
    "商贸": ["商贸代理", "批发业", "百货", "超市连锁", "商品城"],
    "零售": ["百货", "超市连锁", "商贸代理"],
    "造纸": ["造纸", "包装"],
}


def _get_llm_client():
    from openai import OpenAI
    return OpenAI(
        api_key=settings.MINIMAX_API_KEY,
        base_url=settings.MINIMAX_BASE_URL,
    )


def _is_llm_available() -> bool:
    return bool(settings.MINIMAX_API_KEY)


async def _call_llm(query: str) -> Optional[Dict]:
    if not _is_llm_available():
        return None
    now = time.time()
    cached = _LLM_CACHE.get(query)
    if cached and now - cached[0] < _LLM_CACHE_TTL:
        return cached[1]
    try:
        client = _get_llm_client()
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.chat.completions.create,
                model=settings.MINIMAX_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.1,
                max_tokens=1024,
            ),
            timeout=10.0,
        )
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            result = json.loads(json_match.group())
            _LLM_CACHE[query] = (now, result)
            if len(_LLM_CACHE) > 200:
                oldest = min(_LLM_CACHE, key=lambda k: _LLM_CACHE[k][0])
                del _LLM_CACHE[oldest]
            return result
        return None
    except asyncio.TimeoutError:
        print("  MiniMax LLM调用超时(10s)")
        return None
    except Exception as e:
        print(f"  MiniMax LLM调用失败: {e}")
        return None


def _parse_llm_result(llm_result: Dict) -> tuple[List[ScreenerCondition], List[str], str]:
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
    industries = llm_result.get("industries", [])
    explanation = llm_result.get("explanation", "")
    if isinstance(industries, str):
        industries = [industries]
    expanded = []
    for ind in industries:
        if ind in INDUSTRY_MAP:
            expanded.extend(INDUSTRY_MAP[ind])
        else:
            expanded.append(ind)
    industries = list(dict.fromkeys(expanded))
    return conditions, industries, explanation


def _extract_industry_groups(raw_industries: list) -> List[str]:
    groups = []
    for ind in raw_industries:
        if isinstance(ind, str):
            if ind in INDUSTRY_MAP:
                groups.append(ind)
            else:
                groups.append(ind)
    return groups


class ScreenerAIService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.screener_service = ScreenerService(db)

    async def parse_natural_language(self, query: str) -> Dict:
        conditions = []
        matched_keywords = []
        matched_industries = []
        matched_industry_groups = []
        seen_fields = set()

        sorted_keywords = sorted(NLP_CONDITION_MAP.keys(), key=len, reverse=True)
        for keyword in sorted_keywords:
            if keyword in query:
                keyword_conds = NLP_CONDITION_MAP[keyword]
                keyword_fields = tuple(c.field for c in keyword_conds)
                if keyword_fields in seen_fields:
                    matched_keywords.append(keyword)
                    continue
                seen_fields.add(keyword_fields)
                conditions.extend(keyword_conds)
                matched_keywords.append(keyword)

        for ind_keyword, ind_values in INDUSTRY_MAP.items():
            if ind_keyword in query:
                matched_industries.extend(ind_values)
                if ind_keyword not in matched_industry_groups:
                    matched_industry_groups.append(ind_keyword)

        matched_industries = list(dict.fromkeys(matched_industries))

        if conditions or matched_industries:
            return {
                "query": query,
                "matched_keywords": matched_keywords,
                "matched_industries": matched_industries,
                "matched_industry_groups": matched_industry_groups,
                "conditions": [c.model_dump() for c in conditions],
                "explanation": "",
                "source": "keyword",
            }

        llm_result = await _call_llm(query)
        if llm_result:
            conditions, industries, explanation = _parse_llm_result(llm_result)
            if conditions or industries:
                industry_groups = _extract_industry_groups(llm_result.get("industries", []))
                return {
                    "query": query,
                    "matched_keywords": [],
                    "matched_industries": industries,
                    "matched_industry_groups": industry_groups,
                    "conditions": [c.model_dump() for c in conditions],
                    "explanation": explanation,
                    "source": "llm",
                }

        if not conditions and not matched_industries:
            conditions.append(ScreenerCondition(category="quote", field="pct_change", op="gt", value=0))

        return {
            "query": query,
            "matched_keywords": matched_keywords,
            "matched_industries": matched_industries,
            "matched_industry_groups": matched_industry_groups,
            "conditions": [c.model_dump() for c in conditions],
            "explanation": "",
            "source": "keyword",
        }

    async def ai_pick(self, query: str) -> Dict:
        parse_result = await self.parse_natural_language(query)
        conditions = [ScreenerCondition(**c) for c in parse_result["conditions"]]
        matched_industries = parse_result.get("matched_industries", [])
        explanation = parse_result.get("explanation", "")
        source = parse_result.get("source", "keyword")

        if not conditions and not matched_industries:
            conditions.append(ScreenerCondition(category="quote", field="pct_change", op="gt", value=0))

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
            if stock.get("main_net_buy") and stock["main_net_buy"] > 0:
                reasons.append("主力资金流入")
            stock["ai_reason"] = "；".join(reasons) if reasons else "部分条件匹配"
            stock["match_score"] = score

        return {
            "query": query,
            "matched_keywords": parse_result["matched_keywords"],
            "matched_industries": matched_industries,
            "matched_industry_groups": parse_result.get("matched_industry_groups", []),
            "explanation": explanation,
            "source": source,
            "stocks": result_stocks,
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
            "north_holding_change": "北向加仓", "main_net_buy": "主力流入",
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
