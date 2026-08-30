import re

SECRET_KEYS = {"api_key", "authorization", "openai_api_key", "token"}
_BEARER = re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+")
_OPENAI_KEY = re.compile(r"sk-[A-Za-z0-9_-]{12,}")


def redact(value):
    """Return a log-safe copy without mutating the caller's value."""
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if str(key).lower() in SECRET_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    if isinstance(value, str):
        return _OPENAI_KEY.sub("[REDACTED]", _BEARER.sub("Bearer [REDACTED]", value))
    return value
