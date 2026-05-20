"""共享测试工具"""


class FakeCursor:
    """模拟 Motor cursor — 支持链式调用 sort/limit + async to_list"""

    def __init__(self, data: list):
        self._data = list(data)

    def sort(self, field, direction=1):
        if field == "trade_date":
            reverse = direction < 0
            self._data.sort(key=lambda x: x.get("trade_date", ""), reverse=reverse)
        return self

    def limit(self, n):
        self._data = self._data[:n]
        return self

    async def to_list(self, length=None):
        result = list(self._data)
        if length is not None:
            result = result[:length]
        return result


class FakeCollection:
    """模拟 Motor collection"""

    def __init__(self, cursor_data=None):
        self._cursor_data = cursor_data or []

    def find(self, *args, **kwargs):
        return FakeCursor(self._cursor_data)


class FakeDB(dict):
    """模拟 AsyncIOMotorDatabase — dict 子类"""
    pass
