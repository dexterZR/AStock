from app.repos.stock_repo import StockRepo

INDEX_INFO = {
    "000001.SH": {"ts_code": "000001.SH", "name": "上证指数", "symbol": "000001", "industry": "指数", "market": "SSE"},
    "399001.SZ": {"ts_code": "399001.SZ", "name": "深证成指", "symbol": "399001", "industry": "指数", "market": "SZSE"},
    "399006.SZ": {"ts_code": "399006.SZ", "name": "创业板指", "symbol": "399006", "industry": "指数", "market": "SZSE"},
}


class StockService:
    def __init__(self, repo: StockRepo):
        self.repo = repo

    async def get_stock_list(self, skip: int = 0, limit: int = 100):
        return await self.repo.find_all(skip, limit)

    async def get_stock_detail(self, ts_code: str):
        if ts_code in INDEX_INFO:
            return INDEX_INFO[ts_code]
        stock = await self.repo.find_by_code(ts_code)
        if not stock:
            from app.api.errors import NotFoundError
            raise NotFoundError(f"股票 {ts_code} 不存在")
        return stock

    async def search_stocks(self, keyword: str, limit: int = 20):
        results = []
        for code, info in INDEX_INFO.items():
            if keyword in info["name"] or keyword in code:
                results.append(info)
        if results:
            return results
        return await self.repo.search_by_name(keyword, limit)
