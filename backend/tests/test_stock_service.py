import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.stock_service import StockService, INDEX_INFO
from app.api.errors import NotFoundError


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.find_all = AsyncMock(return_value=[])
    repo.find_by_code = AsyncMock(return_value=None)
    repo.search_by_name = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def service(mock_repo):
    return StockService(mock_repo)


class TestStockService:
    async def test_get_stock_list(self, service, mock_repo):
        expected = [{"ts_code": "000001.SZ", "name": "平安银行"}]
        mock_repo.find_all.return_value = expected
        result = await service.get_stock_list(skip=0, limit=10)
        mock_repo.find_all.assert_called_once_with(0, 10)
        assert result == expected

    async def test_get_stock_list_with_pagination(self, service, mock_repo):
        await service.get_stock_list(skip=20, limit=50)
        mock_repo.find_all.assert_called_once_with(20, 50)

    async def test_get_stock_detail_index(self, service, mock_repo):
        result = await service.get_stock_detail("000001.SH")
        mock_repo.find_by_code.assert_not_called()
        assert result == INDEX_INFO["000001.SH"]
        assert result["name"] == "上证指数"

    async def test_get_stock_detail_sz_index(self, service, mock_repo):
        result = await service.get_stock_detail("399001.SZ")
        assert result["name"] == "深证成指"

    async def test_get_stock_detail_cyb_index(self, service, mock_repo):
        result = await service.get_stock_detail("399006.SZ")
        assert result["name"] == "创业板指"

    async def test_get_stock_detail_found(self, service, mock_repo):
        stock = {"ts_code": "000001.SZ", "name": "平安银行"}
        mock_repo.find_by_code.return_value = stock
        result = await service.get_stock_detail("000001.SZ")
        mock_repo.find_by_code.assert_called_once_with("000001.SZ")
        assert result == stock

    async def test_get_stock_detail_not_found(self, service, mock_repo):
        mock_repo.find_by_code.return_value = None
        with pytest.raises(NotFoundError, match="股票 999999.SZ 不存在"):
            await service.get_stock_detail("999999.SZ")

    async def test_search_stocks_index_match(self, service, mock_repo):
        result = await service.search_stocks("上证")
        mock_repo.search_by_name.assert_not_called()
        assert len(result) == 1
        assert result[0]["name"] == "上证指数"

    async def test_search_stocks_index_code_match(self, service, mock_repo):
        result = await service.search_stocks("399001")
        assert len(result) == 1
        assert result[0]["ts_code"] == "399001.SZ"

    async def test_search_stocks_repo_fallback(self, service, mock_repo):
        repo_results = [{"ts_code": "000001.SZ", "name": "平安银行"}]
        mock_repo.search_by_name.return_value = repo_results
        result = await service.search_stocks("平安")
        mock_repo.search_by_name.assert_called_once_with("平安", 20)
        assert result == repo_results

    async def test_search_stocks_custom_limit(self, service, mock_repo):
        mock_repo.search_by_name.return_value = []
        await service.search_stocks("测试", limit=5)
        mock_repo.search_by_name.assert_called_once_with("测试", 5)
