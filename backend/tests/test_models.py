import pytest
from pydantic import ValidationError as PydanticValidationError
from app.models.stock import StockBase, StockCreate, StockResponse, DailyQuote, Indicator


class TestStockModels:
    def test_stock_base_required_fields(self):
        stock = StockBase(ts_code="000001.SZ", symbol="000001", name="平安银行")
        assert stock.ts_code == "000001.SZ"
        assert stock.symbol == "000001"
        assert stock.name == "平安银行"
        assert stock.industry is None
        assert stock.market is None
        assert stock.list_date is None

    def test_stock_base_all_fields(self):
        stock = StockBase(
            ts_code="000001.SZ",
            symbol="000001",
            name="平安银行",
            industry="银行",
            market="SZSE",
            list_date="19910403",
        )
        assert stock.industry == "银行"
        assert stock.market == "SZSE"
        assert stock.list_date == "19910403"

    def test_stock_base_missing_required(self):
        with pytest.raises(PydanticValidationError):
            StockBase(ts_code="000001.SZ")

    def test_stock_create_inherits_base(self):
        sc = StockCreate(ts_code="600519.SH", symbol="600519", name="贵州茅台")
        assert sc.ts_code == "600519.SH"

    def test_daily_quote(self):
        dq = DailyQuote(
            ts_code="000001.SZ",
            trade_date="20240101",
            open=10.0,
            high=11.0,
            low=9.5,
            close=10.5,
            volume=1000000,
            amount=10500000.0,
        )
        assert dq.open == 10.0
        assert dq.close == 10.5
        assert dq.volume == 1000000
        assert dq.is_trading is True
        assert dq.adjust_flag == "none"
        assert dq.pct_change is None
        assert dq.turnover_rate is None

    def test_daily_quote_with_optional(self):
        dq = DailyQuote(
            ts_code="000001.SZ",
            trade_date="20240101",
            open=10.0,
            high=11.0,
            low=9.5,
            close=10.5,
            volume=1000000,
            amount=10500000.0,
            pct_change=5.0,
            turnover_rate=1.23,
            pre_close=10.0,
        )
        assert dq.pct_change == 5.0
        assert dq.turnover_rate == 1.23
        assert dq.pre_close == 10.0

    def test_indicator(self):
        ind = Indicator(ts_code="000001.SZ", trade_date="20240101")
        assert ind.ma_5 is None
        assert ind.macd_dif is None
        assert ind.rsi_6 is None
        assert ind.kdj_k is None
        assert ind.boll_upper is None

    def test_indicator_with_values(self):
        ind = Indicator(
            ts_code="000001.SZ",
            trade_date="20240101",
            ma_5=10.5,
            ma_10=10.2,
            ma_20=10.0,
            macd_dif=0.15,
            macd_dea=0.10,
            macd_bar=0.05,
            rsi_6=65.0,
            kdj_k=70.0,
            kdj_d=60.0,
            kdj_j=80.0,
            boll_upper=12.0,
            boll_mid=10.0,
            boll_lower=8.0,
        )
        assert ind.ma_5 == 10.5
        assert ind.macd_bar == 0.05
        assert ind.boll_mid == 10.0
