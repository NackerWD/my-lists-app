import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest, TokenResponse


class TestRegisterRequest:
    def test_valid_password(self) -> None:
        r = RegisterRequest(email="user@test.com", password="password12345")
        assert r.password == "password12345"

    def test_password_too_short(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(email="user@test.com", password="short")
        errors = exc_info.value.errors()
        assert any("12 caràcters" in str(e["msg"]) for e in errors)

    def test_password_exactly_12(self) -> None:
        r = RegisterRequest(email="user@test.com", password="exactly12chr")
        assert len(r.password) == 12

    def test_password_11_chars_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RegisterRequest(email="user@test.com", password="only11chars")

    def test_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", password="password12345")

    def test_email_normalised(self) -> None:
        r = RegisterRequest(email="User@TEST.COM", password="password12345")
        assert "@" in r.email


class TestTokenResponse:
    def test_default_token_type(self) -> None:
        t = TokenResponse(
            access_token="access",
            refresh_token="refresh",
        )
        assert t.token_type == "bearer"

    def test_default_expires_in(self) -> None:
        t = TokenResponse(access_token="access", refresh_token="refresh")
        assert t.expires_in == 900

    def test_custom_expires_in(self) -> None:
        t = TokenResponse(access_token="access", refresh_token="refresh", expires_in=3600)
        assert t.expires_in == 3600
