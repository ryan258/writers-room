from urllib import error as urllib_error

from lib.config import build_runtime_config, validate_openrouter_api_key


class DummyResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_validate_openrouter_api_key_reports_invalid_token():
    def fake_urlopen(request, timeout=0):
        raise urllib_error.HTTPError(
            request.full_url,
            401,
            "Unauthorized",
            hdrs=None,
            fp=None,
        )

    is_valid, message = validate_openrouter_api_key(
        "sk-or-v1-test-token",
        urlopen=fake_urlopen,
    )

    assert is_valid is False
    assert message == "API key is invalid or expired"


def test_validate_openrouter_api_key_reports_rate_limit():
    def fake_urlopen(request, timeout=0):
        raise urllib_error.HTTPError(
            request.full_url,
            429,
            "Too Many Requests",
            hdrs=None,
            fp=None,
        )

    is_valid, message = validate_openrouter_api_key(
        "sk-or-v1-test-token",
        urlopen=fake_urlopen,
    )

    assert is_valid is False
    assert message == "Rate limited - your API key may need credits"


def test_validate_openrouter_api_key_reports_missing_endpoint():
    def fake_urlopen(request, timeout=0):
        raise urllib_error.HTTPError(
            request.full_url,
            404,
            "Not Found",
            hdrs=None,
            fp=None,
        )

    is_valid, message = validate_openrouter_api_key(
        "sk-or-v1-test-token",
        urlopen=fake_urlopen,
    )

    assert is_valid is False
    assert message == "OpenRouter key endpoint was not found"


def test_validate_openrouter_api_key_reports_timeout():
    def fake_urlopen(request, timeout=0):
        raise urllib_error.URLError("timed out")

    is_valid, message = validate_openrouter_api_key(
        "sk-or-v1-test-token",
        urlopen=fake_urlopen,
    )

    assert is_valid is False
    assert message == "Connection timeout - check your internet connection"


def test_validate_openrouter_api_key_reports_empty_payload():
    def fake_urlopen(request, timeout=0):
        return DummyResponse(b"{}")

    is_valid, message = validate_openrouter_api_key(
        "sk-or-v1-test-token",
        urlopen=fake_urlopen,
    )

    assert is_valid is False
    assert message == "Unexpected API response format"


def test_build_runtime_config_can_skip_remote_validation(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-token")
    monkeypatch.setenv("YOUR_SITE_URL", "https://writers-room.local")
    monkeypatch.setenv("YOUR_SITE_NAME", "Writers Room")

    config, message = build_runtime_config(validate_api_key=False)

    assert config.openrouter_api_key == "sk-or-v1-test-token"
    assert config.site_url == "https://writers-room.local"
    assert config.site_name == "Writers Room"
    assert message == "API key present; validation skipped."
