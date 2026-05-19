import asyncio
import re
import json
import time
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.repos.news_repo import NewsRepo


TYPE_KEYWORDS = {
    "financial": ["财报", "营收", "净利润", "一季报", "半年报", "三季报", "年报", "业绩", "盈利", "亏损", "营收增长"],
    "research": ["调研", "评级", "买入", "增持", "减持", "看多", "看空", "券商", "研报", "目标价"],
    "shareholder": ["减持", "增持", "回购", "股东", "套现", "质押", "解禁"],
    "business": ["收购", "合并", "战略合作", "产能", "订单", "中标", "签约"],
    "dividend": ["分红", "派息", "送股", "转增"],
    "product": ["新产品", "发布", "上市", "量产", "布局", "赛道"],
    "official": ["回应", "澄清", "公告", "声明", "传闻"],
    "regulatory": ["监管", "问询", "处罚", "立案", "警示", "整改"],
    "corporate": ["股权激励", "管理层", "换届", "重组", "分拆"],
}

SENTIMENT_KEYWORDS = {
    "positive": ["增长", "上涨", "利好", "突破", "创新高", "超预期", "买入", "增持", "看好", "获批", "中标", "签约", "合作"],
    "negative": ["下跌", "暴跌", "利空", "亏损", "减持", "处罚", "问询", "风险", "警示", "退市", "违规", "爆雷"],
}

AI_NEWS_PROMPT = """你是一位资深A股财经分析师。请分析以下新闻，判断对A股市场的影响价值。

新闻列表：
{news_list}

请返回JSON格式（不要markdown代码块）：
{{
  "analyses": [
    {{
      "index": 0,
      "value_score": 1-10,
      "ai_recommended": true/false,
      "ai_brief": "一句话核心点评(30字以内)",
      "affected_sectors": ["行业1", "行业2"],
      "action_hint": "利好/利空/中性"
    }}
  ]
}}

评分标准：
- value_score: 1-3=普通资讯, 4-6=值得关注, 7-8=重要影响, 9-10=重大事件
- ai_recommended: value_score>=6时为true
- action_hint: 对市场的整体影响方向

只返回JSON，不要其他文字。"""

_LLM_CACHE: dict = {}
_LLM_CACHE_TTL = 300


def _is_llm_available() -> bool:
    return bool(getattr(settings, "LLM_API_KEY", ""))


def _get_llm_client():
    from openai import OpenAI
    return OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=getattr(settings, "LLM_BASE_URL", ""),
    )


def _classify_type(title: str) -> str:
    for ntype, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in title:
                return ntype
    return "business"


def _classify_sentiment(title: str) -> str:
    pos_score = sum(1 for kw in SENTIMENT_KEYWORDS["positive"] if kw in title)
    neg_score = sum(1 for kw in SENTIMENT_KEYWORDS["negative"] if kw in title)
    if pos_score > neg_score:
        return "positive"
    elif neg_score > pos_score:
        return "negative"
    return "neutral"


def _extract_stock_codes(text: str) -> list:
    codes = re.findall(r'(\d{6})\.[SZ]', text)
    return list(set(codes))


def _calc_heat_score(item: dict) -> int:
    score = 50
    title = item.get("title", "")
    if any(kw in title for kw in ["突发", "重磅", "紧急", "重大"]):
        score += 20
    if any(kw in title for kw in ["暴跌", "暴涨", "涨停", "跌停"]):
        score += 15
    if any(kw in title for kw in ["央行", "国务院", "证监会", "美联储"]):
        score += 10
    return min(score, 100)


async def _ai_analyze_news(news_list: list) -> list:
    if not _is_llm_available() or not news_list:
        return []

    news_text = ""
    for i, n in enumerate(news_list[:10]):
        title = n.get("title", "")
        news_text += f"\n{i}. {title}"

    cache_key = news_text[:200]
    now = time.time()
    cached = _LLM_CACHE.get(cache_key)
    if cached and now - cached[0] < _LLM_CACHE_TTL:
        return cached[1]

    try:
        client = _get_llm_client()
        prompt = AI_NEWS_PROMPT.format(news_list=news_text)
        response = await asyncio.wait_for(
            asyncio.to_thread(
                client.chat.completions.create,
                model=getattr(settings, "LLM_MODEL", ""),
                messages=[
                    {"role": "system", "content": "你是专业A股财经分析师，只返回JSON。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=2048,
            ),
            timeout=60.0,
        )
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            result = json.loads(json_match.group())
            analyses = result.get("analyses", [])
            _LLM_CACHE[cache_key] = (now, analyses)
            if len(_LLM_CACHE) > 100:
                oldest = min(_LLM_CACHE, key=lambda k: _LLM_CACHE[k][0])
                del _LLM_CACHE[oldest]
            return analyses
    except asyncio.TimeoutError:
        print("  AI新闻分析超时(60s)")
    except Exception as e:
        print(f"  AI新闻分析失败: {e}")
    return []


async def sync_global_news():
    print("📰 开始同步全球财经快讯...")
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    repo = NewsRepo(db)

    try:
        import akshare as ak
        df = await asyncio.to_thread(ak.stock_info_global_em)
        if df is None or len(df) == 0:
            print("  无数据")
            return

        records = []
        for _, row in df.iterrows():
            title = str(row.get("标题", ""))
            summary = str(row.get("摘要", ""))
            pub_date = str(row.get("发布时间", ""))
            url = str(row.get("链接", ""))

            if not title or not pub_date:
                continue

            full_text = f"{title} {summary}"
            records.append({
                "title": title,
                "summary": summary[:500] if summary else "",
                "type": _classify_type(full_text),
                "source": "东方财富",
                "pub_date": pub_date,
                "url": url,
                "related_codes": _extract_stock_codes(full_text),
                "related_stocks": [],
                "sentiment": _classify_sentiment(full_text),
                "heat_score": _calc_heat_score({"title": title}),
                "category": "global",
                "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

        count = await repo.bulk_upsert(records)
        total = await repo.count_documents({"category": "global"})
        print(f"  同步 {len(records)} 条, 更新 {count} 条, 库中共 {total} 条全球快讯")

    except Exception as e:
        print(f"  同步失败: {e}")
    finally:
        client.close()


async def sync_stock_news(symbols: list = None):
    if symbols is None:
        symbols = [
            "600519", "000858", "300750", "002594", "600036",
            "601318", "000001", "600745", "601939", "000651",
        ]

    print(f"📰 开始同步个股新闻 ({len(symbols)} 只)...")
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    repo = NewsRepo(db)

    try:
        import akshare as ak
        total_count = 0

        for symbol in symbols:
            try:
                df = await asyncio.to_thread(ak.stock_news_em, symbol=symbol)
                if df is None or len(df) == 0:
                    continue

                records = []
                for _, row in df.iterrows():
                    title = str(row.get("新闻标题", ""))
                    content = str(row.get("新闻内容", ""))
                    pub_date = str(row.get("发布时间", ""))
                    source = str(row.get("文章来源", ""))
                    url = str(row.get("新闻链接", ""))
                    keyword = str(row.get("关键词", ""))

                    if not title:
                        continue

                    full_text = f"{title} {content[:200]}"
                    records.append({
                        "title": title,
                        "summary": content[:500] if content else "",
                        "type": _classify_type(full_text),
                        "source": source,
                        "pub_date": pub_date,
                        "url": url,
                        "related_codes": [symbol] if symbol else [],
                        "related_stocks": [keyword] if keyword else [],
                        "sentiment": _classify_sentiment(full_text),
                        "heat_score": _calc_heat_score({"title": title}),
                        "category": "stock",
                        "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })

                if records:
                    count = await repo.bulk_upsert(records)
                    total_count += count

                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"  {symbol}: 失败 {e}")
                await asyncio.sleep(1)

        total = await repo.count_documents({"category": "stock"})
        print(f"  个股新闻更新 {total_count} 条, 库中共 {total} 条")

    except Exception as e:
        print(f"  同步失败: {e}")
    finally:
        client.close()


async def ai_analyze_today_news():
    print("🤖 开始AI分析今日新闻...")
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    repo = NewsRepo(db)

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        news = await repo.find_market_news(limit=20)
        today_news = [n for n in news if n.get("pub_date", "").startswith(today)]

        if not today_news:
            today_news = news[:20]

        if not today_news:
            print("  无新闻可分析")
            return

        analyses = await _ai_analyze_news(today_news)
        if not analyses:
            print("  AI分析未返回结果")
            return

        updated = 0
        for analysis in analyses:
            idx = analysis.get("index", -1)
            if idx < 0 or idx >= len(today_news):
                continue

            news_item = today_news[idx]
            url = news_item.get("url", "")
            if not url:
                continue

            update_fields = {
                "value_score": analysis.get("value_score", 5),
                "ai_recommended": analysis.get("ai_recommended", False),
                "ai_brief": analysis.get("ai_brief", ""),
                "affected_sectors": analysis.get("affected_sectors", []),
                "action_hint": analysis.get("action_hint", "中性"),
            }

            from pymongo import UpdateOne
            ops = [UpdateOne({"url": url}, {"$set": update_fields})]
            result = await repo.col.bulk_write(ops, ordered=False)
            updated += result.modified_count

        recommended = sum(1 for a in analyses if a.get("ai_recommended"))
        print(f"  AI分析 {len(analyses)} 条, 更新 {updated} 条, 推荐 {recommended} 条")

    except Exception as e:
        print(f"  AI分析失败: {e}")
    finally:
        client.close()


async def sync_all_news():
    print(f"{'='*50}")
    print(f"📰 新闻同步开始 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    await sync_global_news()
    await sync_stock_news()
    await ai_analyze_today_news()

    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    repo = NewsRepo(db)
    deleted = await repo.delete_old_news(days=30)
    total = await repo.count_documents()
    print(f"\n🗑️  清理 {deleted} 条过期新闻, 库中共 {total} 条")
    print(f"✅ 新闻同步完成")
    client.close()


if __name__ == "__main__":
    asyncio.run(sync_all_news())
