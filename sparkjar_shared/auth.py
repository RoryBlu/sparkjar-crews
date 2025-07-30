from datetime import timedelta


class InvalidTokenError(Exception):
    """Exception raised for invalid tokens."""


def create_token(
    subject: str, scopes=None, expires_delta: timedelta = timedelta(hours=1)
) -> str:
    """Return a dummy token string."""
    scopes = scopes or []
    return f"token-{subject}"


def verify_token(token: str) -> dict:
    """Very basic token verification for tests."""
    if token.startswith("invalid"):
        raise InvalidTokenError("Invalid token")
    return {"sub": "test-user", "scopes": ["sparkjar_internal", "crew_execute"]}
