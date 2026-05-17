import pytest
from app.api.errors import AppError, NotFoundError, ValidationError, ExternalAPIError


class TestAppError:
    def test_app_error_defaults(self):
        err = AppError("something went wrong")
        assert err.message == "something went wrong"
        assert err.code == "INTERNAL_ERROR"
        assert err.status_code == 500
        assert err.details == {}

    def test_app_error_custom(self):
        err = AppError("custom", code="CUSTOM", status_code=400, details={"key": "val"})
        assert err.code == "CUSTOM"
        assert err.status_code == 400
        assert err.details == {"key": "val"}

    def test_not_found_error(self):
        err = NotFoundError()
        assert err.status_code == 404
        assert err.code == "NOT_FOUND"
        assert err.message == "资源不存在"

    def test_not_found_error_custom_message(self):
        err = NotFoundError("股票 000001.SZ 不存在")
        assert err.message == "股票 000001.SZ 不存在"
        assert err.status_code == 404

    def test_validation_error(self):
        err = ValidationError()
        assert err.status_code == 422
        assert err.code == "VALIDATION_ERROR"

    def test_validation_error_with_details(self):
        err = ValidationError(details={"field": "limit", "reason": "must be positive"})
        assert err.details == {"field": "limit", "reason": "must be positive"}

    def test_external_api_error(self):
        err = ExternalAPIError()
        assert err.status_code == 502
        assert err.code == "EXTERNAL_API_ERROR"

    def test_inheritance(self):
        assert issubclass(NotFoundError, AppError)
        assert issubclass(ValidationError, AppError)
        assert issubclass(ExternalAPIError, AppError)
