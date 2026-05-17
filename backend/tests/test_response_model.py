import pytest
from app.models.response import BaseResponse


class TestBaseResponse:
    def test_defaults(self):
        resp = BaseResponse()
        assert resp.success is True
        assert resp.data is None
        assert resp.message == ""
        assert resp.request_id == ""
        assert resp.timestamp == ""

    def test_with_data(self):
        resp = BaseResponse(data={"key": "value"})
        assert resp.data == {"key": "value"}

    def test_error_response(self):
        resp = BaseResponse(success=False, message="参数错误")
        assert resp.success is False
        assert resp.message == "参数错误"

    def test_full_response(self):
        resp = BaseResponse(
            success=True,
            data=[1, 2, 3],
            message="ok",
            request_id="abc123",
            timestamp="2024-01-01T00:00:00",
        )
        assert resp.data == [1, 2, 3]
        assert resp.request_id == "abc123"
