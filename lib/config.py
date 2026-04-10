"""
Runtime configuration helpers for Writers Room entrypoints.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Callable
from urllib import error as urllib_error
from urllib import request as urllib_request


class ConfigError(ValueError):
    """Raised when required runtime configuration is missing or invalid."""


@dataclass(frozen=True)
class RuntimeConfig:
    """Validated runtime settings shared across entrypoints and lib callers."""

    openrouter_api_key: str
    site_url: str = "http://localhost"
    site_name: str = "Writers Room"

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        return cls(
            openrouter_api_key=(os.getenv("OPENROUTER_API_KEY") or "").strip(),
            site_url=(os.getenv("YOUR_SITE_URL") or "http://localhost").strip()
            or "http://localhost",
            site_name=(os.getenv("YOUR_SITE_NAME") or "Writers Room").strip()
            or "Writers Room",
        )


def should_skip_api_validation() -> bool:
    """Return True when startup validation should be bypassed for this process."""
    value = (os.getenv("WRITERS_ROOM_SKIP_API_VALIDATION") or "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def validate_openrouter_api_key(
    api_key: str,
    *,
    urlopen: Callable = urllib_request.urlopen,
) -> tuple[bool, str]:
    """Validate an OpenRouter key against the provider's key endpoint."""
    if not api_key:
        return False, "OPENROUTER_API_KEY not found in environment"

    if not api_key.startswith("sk-or-"):
        return False, "API key format appears invalid (should start with 'sk-or-')"

    request = urllib_request.Request(
        "https://openrouter.ai/api/v1/key",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as exc:
        if exc.code == 401:
            return False, "API key is invalid or expired"
        if exc.code == 429:
            return False, "Rate limited - your API key may need credits"
        if exc.code == 404:
            return False, "OpenRouter key endpoint was not found"
        return False, f"OpenRouter validation failed ({exc.code})"
    except urllib_error.URLError as exc:
        reason = str(exc.reason)
        if "timed out" in reason.lower():
            return False, "Connection timeout - check your internet connection"
        return False, f"Network error - {reason}"
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"Validation failed: {str(exc)[:150]}"

    data = payload.get("data", {})
    if not data:
        return False, "Unexpected API response format"

    limit_remaining = data.get("limit_remaining")
    try:
        if limit_remaining is not None and float(limit_remaining) <= 0:
            return True, "Warning: API key is valid, but the current account limit is exhausted."
    except (TypeError, ValueError):
        pass

    return True, "API key validated successfully"


def build_runtime_config(
    *,
    validate_api_key: bool,
    urlopen: Callable = urllib_request.urlopen,
) -> tuple[RuntimeConfig, str]:
    """Load runtime config from the environment and validate it once."""
    config = RuntimeConfig.from_env()
    if not config.openrouter_api_key:
        raise ConfigError("OPENROUTER_API_KEY not found in environment")

    if not validate_api_key:
        return config, "API key present; validation skipped."

    is_valid, message = validate_openrouter_api_key(
        config.openrouter_api_key,
        urlopen=urlopen,
    )
    if not is_valid:
        raise ConfigError(message)
    return config, message
